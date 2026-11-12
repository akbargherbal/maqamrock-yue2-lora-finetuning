# Current — `arabic_instrumental_lora` · 2026-11-12 · training done, eval = NOW

**Nothing is running. The VM is off. What's left is the listening evaluation, and the only
two things you can do locally today are (1) score the 4-checkpoint screen and (2) judge the
base take. Everything that tests generalization (Q3/Q4/Q5) needs a GPU round that is staged
but not rendered.** Authority: `docs/ARABIC_INSTRUMENTAL_EVAL_PLAN.md` (every claim below is
from it or from the GCS artifacts it names).

## What is on your Windows box (verified against GCS, 2026-11-12)

```
mp3/screen_loRA/   p0a_ck3000|ck4000|ck5000|ck5500_101.mp3   4 takes, all 260.0 s, cap 6500
mp3/screen_base/   p0a_base_101.mp3                          1 take, 114.7 s, ended naturally
audio/...          the authoritative WAVs (mp3 = listening copy)
inputs/            HOLDOUT.json, input_depth_ck5500_{loRA,base}.json, converted_sha256.txt
```

Consequence: **the checkpoint ladder is a fair blind comparison** (same prompt, seed 101, cap
6500, same 260 s duration). **base-vs-LoRA is not blind** — 114.7 s vs 260 s gives it away, and
that length gap is itself a finding (the adapter changes structure, not only timbre).

## Step 1 (local, no GPU) — rate the 4 checkpoints in the app → Q1 + Q2

The app groups by **parent folder**, so one folder per arm is all it needs (no renaming, no
`prepare_ab_eval`; that tool is only for handing a package to a *different* person):

```powershell
$src = "C:\Users\DELL\Downloads\ai_eval\mp3\screen_loRA"
$dst = "C:\Users\DELL\Downloads\ai_eval\app_src"
foreach ($ck in "3000","4000","5000","5500") {
  New-Item -ItemType Directory -Force "$dst\ck$ck" | Out-Null
  Copy-Item "$src\p0a_ck${ck}_101.mp3" "$dst\ck$ck\p0a_101.mp3"
}
```

Copy the card into the app, then launch blind:

```powershell
Copy-Item "<repo>\INFERENCE\scorecards\arabic_instrumental_quick.json" .\ai_music_rating_app\scorecards\
cd ai_music_rating_app
py app.py --audio "C:\Users\DELL\Downloads\ai_eval\app_src" `
  --label ainst_screen --scorecard arabic_instrumental_quick --blind
```

Card: `INFERENCE/scorecards/arabic_instrumental_quick.json` — 6 نعم/لا + `arm_guess` +
`overall` (1–5, the summary metric) + notes; validated with the app's own loader.
Full card (`…_style.json`) if you want the 1–5 breakdown instead.

Base take: separate run against its own folder, **without** `--blind` — 1:54 vs 4:20 gives it
away, so mixing it in only breaks the blind for that one track.

**نسخة ورقية (بدون تطبيق):** `agent_notes/quick_score.md` — نفس الأسئلة.

## Step 2 (local) — judge the base take, openly

`mp3/screen_base/p0a_base_101.mp3`, arms known. The only question is **does base even sound
like an Arabic acoustic ensemble on this prompt** (style_fidelity), and what it did in 114.7 s
that the LoRA stretched to 260 s. This is the reference line for decision rule 2.

## Step 3 (needs a GPU VM) — the 13-track depth round → Q3/Q4/Q5

Rendered inputs are already staged in GCS at `…/eval/inputs/`:
`input_depth_ck5500_loRA.json` (7 songs: `p0b_noprefix`, `h1_0153_vocal`, `h2_0032_vocal`,
`h3_0211_clean`, `p1_noperc`, `p3_piano_control`, `p0a_rep_prefix_s202`) + the `_base` twin
(same, LoRA scale 0). Both are pinned to `ck5500`; if the screen winner is another checkpoint,
regenerate the two JSONs — the converted pairs already exist, nothing to reconvert.

Cost: ~26 min on A100, ~1.5 h on T4. GPU rule: `nvidia-smi` first; no overlap with anything.

What each track answers:

| prompt | question |
|---|---|
| `h1/h2/h3` | Q3 contamination-free recall (only 3 of the 8 holdouts are in this round) |
| `p1_noperc` | Q3b instruction-following: can it *remove* percussion? |
| `p3_piano_control` | Q5 over-application — must be style_fidelity ≤ 2 on both arms |
| `p0b_noprefix` | Q1b robustness to prompt shape |
| `p0a_rep_prefix_s202` | variance: is the screen ranking stable across seeds? |

## Decision rules (plan §9, fixed before listening)

1. Discrimination ≥ 10/13 correct `arm_guess` = audible (p < 0.05); fewer = don't pick a ckpt.
2. Style win: LoRA median `style_fidelity` ≥ 4 **and** ≥ 1 point over base, artifacts no worse.
3. Checkpoint: highest `style_fidelity`; tie-break `coherence`, then `artifacts`; still tied →
   later checkpoint.
4. H-caption scores must not exceed P1 by > 1 point (else it's prompt replay, not style).
5. Any `words` vocals on LoRA that base doesn't produce = flag (283/482 captions named vocals).
6. P3 must be ≤ 2 on both arms.

Only after 1–6: convert/register the winner in `<base>/loras/audio_cpp/style/`, then the
`quran_ahh_r32` α-merge test. Publishing stays a separate decision.

## Not to do

- Don't judge on `loss/loss` (plateaued ~4.0 from step 1000 by design).
- Don't pass the `arabmaqamrock` trigger — the LoRA was trained on `Middle Eastern fusion, instrumental.`
  (`generate.py` prepends the v3 trigger unless `--no-trigger`).
- Don't let `cap` be `auto` (tag-only lyrics → 2750 ≈ 110 s).
- Don't rebuild the binary; check `gs://…/arabmaqrock/binaries/index.json` first.
