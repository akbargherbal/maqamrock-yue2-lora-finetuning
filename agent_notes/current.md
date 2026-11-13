# Current — `arabic_instrumental_lora` · 2026-11-12 · **ck5500 LOCKED**, depth round pending

**Nothing is running. The VM is off. Checkpoint decision: `ck5500` (your listening verdict,
2026-11-12) — recorded in `docs/ARABIC_INSTRUMENTAL_EVAL_PLAN.md` §9 rule 3.** The staged depth
inputs are already pinned to it, so the depth round needs no regeneration. What remains is
(1) the 13-track depth round on a GPU (Q3/Q4/Q5) and (2) the separate promotion/publish
decisions.

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

## Mix with v3 (`arabic_instrumental_lora` × `arabmaqamrock`) — supported, verified

No new tool: `merge_quran_lora.py` is branch-generic (AR+NAR rank-concat, α into donor B).
v3 = carrier (`--v2`), instrument = donor (`--quran`) → **α=0 is bit-identical to v3**.

**Grid built 2026-11-13 (CPU, this box), converted, uploaded to
`<base>/arabic_instrumental_lora/mix_v3/a<α>/` with `MANIFEST.json`:**

| α | effective share of the AR style delta | AR sha256 |
|---:|---:|---|
| 0.1 | 8.9 % | `d48109b3…64a0` |
| 0.2 | **16.5 %** (primary) | `820f1ce9…dd6` |

**a0.3 and a0.5 were built, then deleted from GCS 2026-11-13 — high α rejected by the user.**
Only 0.1 / 0.2 exist; do not rebuild them without a new decision. The render spec
(`INFERENCE/input_mix_v3instr.json`) now carries 3 arms: `v3` + `a0p1` + `a0p2` (default `a0p2`).

Control = v3 itself (α=0 is tensor-identical). Merge input identity proven: the GCS fused file
`37dba84a…` is the MANIFEST source of the HF pair, and local conversion reproduced it exactly
(AR `3531bb91…`, NAR `a7eabcad…`).

Render: `loras.<arm>.dir` → `/content/converter/out/v3instr_a<α>` after pulling each arm, one
prompt / seed / pinned cap across arms. Full recipe: `docs/PRON_LORA_MERGE.md` § "style × style".

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
(same, LoRA scale 0). Both are pinned to `ck5500` — the locked pick — so neither JSON needs
regenerating and nothing needs reconverting. Provenance of the pair: GCS
`<base>/arabic_instrumental_lora/converted/ck5500/`, AR `69517eea…97edb`, NAR
`f84fdd4e…6ea2f`, source adapter `cf6d44bb…3584`.

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

**Render JSON ready (dry-run validated):** `INFERENCE/input_mix_v3instr.json` — 5 arms
(`v3`, `a0.1`, `a0.2`, `a0.3`, `a0.5`), Hijaz prompt from the staged
`/content/audiocpp_inference/prompts/Hijaz_{style,lyrics}.txt`, seed 101, q=0.95 → cap **7250**
for every arm (same lyrics ⇒ same cap). **No `--no-trigger`**: the stage style file already
starts with `arabmaqamrock`, and the mix's conditioning side is v3, so v3's prompt shape wins.

```bash
B=gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning
gsutil -m rsync -r "$B/arabic_instrumental_lora/mix_v3" /content/mix
mkdir -p /content/mix/v3
gsutil -m cp "$B/v3_arabmaqamrock_lora/convert/v3_arabmaqamrock_lora_"*.safetensors /content/mix/v3/
python INFERENCE/generate.py INFERENCE/input_mix_v3instr.json --dry-run
setsid nohup python INFERENCE/generate.py INFERENCE/input_mix_v3instr.json \
  --label mix_v3instr > /content/logs/mix_v3instr.log 2>&1 & disown
```
