# Eval plan — did `arabic_instrumental_lora` learn the Arabic instrumental style?

_Status: **draft, 2026-11-12**. Nothing here has run. Blocked on (a) training reaching
"Job stopped", (b) a free GPU, (c) your go-ahead. This is an evaluation plan, not an
authority doc — it needs your approval, a `docs/README.md` index row and the
`docs-reconciler` pass before it becomes one._

Grounding: `docs/INFERENCE.md` (T4 benchmark, flags), `docs/AB_BLIND_EVAL.md` +
`skills/ab-blind-eval`, `docs/LISTENING_EVAL.md`, `docs/PRON_LORA_SWEEP.md` (sweep
conventions). Nothing below invents a flag that the repo's scripts do not have.

---

## 1. The questions, and what would falsify each

| # | Question | Falsified when |
|---|---|---|
| Q1 | Does the adapter change the sound **in the intended direction**? | blind listeners can't beat chance at LoRA-vs-base; or style score is not above base |
| Q2 | **Which checkpoint** is best: 3000 / 4000 / 5000 / 5500? | all four are indistinguishable on style and artifacts |
| Q3 | Does it follow **new prose**, or replay the training captions? | it only sounds right on the 8 holdout captions, but generic on new prose |
| Q4 | Does it **leak vocals** into an instrumental prompt? (283/482 training captions name vocals) | vocals appear on LoRA takes and not on base takes |
| Q5 | Does it **over-apply** the style to prompts that should be non-Arabic? | a piano-ballad probe comes back with oud/darbuka |

The verdict is **audio, never loss**. `loss/loss` plateaued around 4.0 from step 1000;
that says nothing about style fidelity.

---

## 2. Controls — three gotchas that would silently invalidate the test

1. **The trigger.** `INFERENCE/generate.py:316-318` prepends `arabmaqamrock ` to any style
   that lacks it. That string is correct for v3 and **wrong for this adapter** — our
   training captions all start `Middle Eastern fusion, instrumental.`. Always pass
   `--no-trigger` and put the prefix in the style text yourself.
2. **The `[Lyrics]` split.** A dataset `.txt` is
   `Middle Eastern fusion, instrumental. <caption>\n[Lyrics]\n[intro]…`. The generator takes
   **style and lyrics as separate fields** and the lyrics must be the tags **without** a
   `[Lyrics]` header (compare the staged `prompts/Hijaz_lyrics.txt`). Split on the exact
   separator `\n[Lyrics]\n`.
3. **The cap.** Pin `cap` to one integer per prompt and reuse it for **every arm**, otherwise
   duration differs across arms and the comparison is void. Never let `auto` recompute per arm.
   **`auto` is wrong here:** these lyrics are tag-only, so `duration_cap.py` counts
   `N_letters = 0` and returns `111.1 s → cap 2750` (verified:
   `[duration_cap] N_letters=0 q=0.950 dur=111.1s cap=2750`). That is a ~110 s render, too
   short to judge a style learned from 4–6 min tracks. **Pin `cap: 6500`** in `defaults`
   (benchmark: 6500 → ~424 s wall on a T4, ~240 s audio), which sits at the training p50.

Held constant across all arms: same GGUF (`yue2-3b-bf16.gguf`), same VAE, same
`attention=flash`, `cot=off`, default sampler (`guidance_scale=1.01`,
`semantic_temperature=1.0`, `semantic_repetition_penalty=1.2` — no `EXTRA_REQUEST_OPTS`),
same seed per prompt, LoRA scales 1.0/1.0 for adapter arms and **0/0 for the base arm**
(audio.cpp treats 0 as adapter-off), sequential generation only.

**Contamination check (must pass before rendering):** none of the 8 holdout names may
exist in `/content/yue2_dataset`; their prompts are the only contamination-free test set.

---

## 3. Arms

| arm | checkpoint | LoRA AR/NAR scale | role |
|---|---|---:|---|
| `base` | — | 0.0 / 0.0 | control: what the base model does with this prompt |
| `ck3000` | step 3000 | 1.0 / 1.0 | early ladder rung |
| `ck4000` | step 4000 | 1.0 / 1.0 | mid |
| `ck5000` | step 5000 | 1.0 / 1.0 | late |
| `ck5500` | step 5500 (final) | 1.0 / 1.0 | deliverable candidate |

No α variants, no merge with `quran_ahh_r32`, no v3 comparison in this round. Those are
separate decisions after the verdict (§10).

---

## 4. Prompt battery

`P0` is your representative prompt, verbatim. `H1..H8` are the held-out training captions.
`P1..P3` are probes **not** in any training caption.

| id | text | what it tests |
|---|---|---|
| **P0a** | `Middle Eastern fusion, instrumental. ` + your prompt | in-distribution prompt shape |
| **P0b** | your prompt alone, no prefix | robustness to prompt shape (still `--no-trigger`) |
| **H1–H8** | each held-out `.txt`, split per §2.2 | contamination-free recall of the dataset's own style |
| **P1** | new ensemble: `solo oud and cello, no percussion, slow taqsim-like introduction that opens into a 6/8 darbuka groove` | instruction-following: can it *remove* instruments? |
| **P2** | new combination: `qanun-led trio with ney and riq, fast 9/8, trading phrases, mostly mid-register, dry close mix` | generalization to an ensemble/feel absent from the prompt set |
| **P3** | **negative control**: `solo grand piano ballad, no Middle Eastern instruments, no percussion, no oud, no strings section` | over-application: does it force the style anyway? |

Your prompt and lyrics for **P0**, verbatim:

```
STYLE:
Arabic instrumental fusion, oriental ensemble, cinematic Arabic orchestral feel, Arabic instrumental cover, studio band session, musicians tracked together in one room, real acoustic oud with plucked pick attack and finger slides, violin and cello sections supporting the oud, played by hand with bow noise and vibrato, full ensemble swelling together like a small orchestra, fretted bass guitar, acoustic drum kit with natural ghost notes, darbuka, riq, daf with skin and jingle detail, expressive ornamented melody passed between oud, violin and cello in call and response, plucked oud answering the bowed strings, microtonal inflections, human timing with slight push and pull, breathing dynamics, dramatic dynamic builds and releases, spacious studio room, medium natural reverb, warm analog tape saturation, close-miked with room mics for ensemble width, clean and clear recording, polished studio mix, no audience, no applause, no crowd noise, no stage ambience, not a concert recording

LYRICS:
[intro]
[verse]
[chorus]
[bridge]
[verse]
[chorus]
[outro]
```

Use the same 7-tag lyrics for P1–P3 so cap and section count are comparable.

**Seeds:** `101` for every prompt in Stage A; in Stage B add `202` for P0a only, to measure
take-to-take variance. Same seed across arms is what makes the pair comparable.

---

## 5. Staging (fresh T4 VM, before any GPU work)

```bash
# GPU rule first — no overlap with training, ever
nvidia-smi
pgrep -af 'run.py|train_ctl|generate.py'

git clone https://github.com/akbargherbal/maqamrock-yue2-lora-finetuning.git
cd maqamrock-yue2-lora-finetuning
bash bootstrap/setup.sh --inference > /content/logs/setup_inf.log 2>&1   # foreground-ish, ~10 min
grep -n '\[FAIL\]' /content/logs/setup_inf.log || echo "no failures"
```

`--inference` stages the **sm_75 / T4** prebuilt binary, the two GGUF models from HF, the
converter, and the canonical v3 adapters (not ours). It needs `HF_TOKEN` +
`GCP_BACKUP_BASE` in `/root/.secrets.env`.

**Stage our checkpoints and convert them.** The ai-toolkit files are not loadable by
audio.cpp; each needs `convert_aitoolkit_yue2_lora.py` (in GCS
`audiocpp_inference/converter/`, staged to `/content/converter/`):

```bash
. /root/.secrets.env
RUN=arabic_instrumental_lora
for S in 3000 4000 5000 5500; do
  gsutil cp "$GCP_BACKUP_BASE/$RUN/output/${RUN}_00000${S}.safetensors" /content/ckpts/
  python /content/converter/convert_aitoolkit_yue2_lora.py \
    "/content/ckpts/${RUN}_00000${S}.safetensors" \
    --out-dir "/content/converter/out/ck${S}" --stem "${RUN}_ck${S}"
done
sha256sum /content/converter/out/ck*/*.safetensors | tee /content/logs/converted_sha256.txt
```

(Step 5000/5500 may still be local-only if the 5-min daemon hasn't run; pull from GCS or
copy from `/content/ai-toolkit/output/` while the VM is alive — whichever exists.)

**Build the prompts JSON** (one file, validated before any GPU work):

```json
{
  "loras": {
    "ck3000": { "dir": "/content/converter/out/ck3000" },
    "ck4000": { "dir": "/content/converter/out/ck4000" },
    "ck5000": { "dir": "/content/converter/out/ck5000" },
    "ck5500": { "dir": "/content/converter/out/ck5500" }
  },
  "defaults": { "seed": 101, "lora": "ck5500", "cap": 6500 },
  "songs": [
    { "name": "p0a_rep_prefix", "style": "Middle Eastern fusion, instrumental. <P0 text>", "lyrics": "[intro]\n[verse]\n[chorus]\n[bridge]\n[verse]\n[chorus]\n[outro]" },
    { "name": "p0b_rep_noprefix", "style": "<P0 text>", "lyrics": "<same tags>" },
    { "name": "p1_no_perc", "style": "Middle Eastern fusion, instrumental. solo oud and cello, no percussion, slow taqsim-like introduction that opens into a 6/8 darbuka groove", "lyrics": "<same tags>" },
    { "name": "p2_qanun9", "style": "Middle Eastern fusion, instrumental. qanun-led trio with ney and riq, fast 9/8, trading phrases, mostly mid-register, dry close mix", "lyrics": "<same tags>" },
    { "name": "p3_piano_control", "style": "solo grand piano ballad, no Middle Eastern instruments, no percussion, no oud, no strings section", "lyrics": "<same tags>" }
  ]
}
```

(`H1..H8` get one entry each from `eval_holdout/*.txt`, split as in §2.2; write them with a
small script and keep `HOLDOUT.json` next to the JSON for provenance.)

```bash
python INFERENCE/generate.py /content/eval/input_stageA.json --dry-run --no-trigger
# prints the projected wall time and existence-checks every adapter pair — no GPU work
```

Note: `generate.py` **refuses** to run while an ai-toolkit training run is detected
(`--allow-concurrent` overrides; don't use it).

---

## 6. Budget on a T4 (~6.5 min/track measured at auto cap; **~7.1 min at cap 6500**,
`INFERENCE.md:300` — Hijaz at 6500 took 424 s)

| stage | arms | prompts | tracks | wall |
|---|---|---|---:|---:|
| **A — checkpoint screen** | base, 3000, 4000, 5000, 5500 | P0a + H1,H2 (vocal) + H3,H4 (clean) | 25 | **≈ 3.0 h** |
| **B — depth on the winner** | winner + base | P0a×2 seeds, P0b, H1–H8, P1–P3 | 28 | **≈ 3.3 h** |
| total | | | 53 | **≈ 6.3 h** |

Run **sequentially, detached**, one stage at a time:

```bash
cd /content/maqamrock-yue2-lora-finetuning
setsid nohup python INFERENCE/generate.py /content/eval/input_stageA.json \
  --no-trigger --label evalA > /content/logs/evalA_stdout.log 2>&1 & disown
pgrep -af 'generate.py'
```

Stage A first: it answers Q2 for ~half the cost. If Stage A already shows base == LoRA,
stop and report — don't spend Stage B.

Base arm = the same JSON with `LORA_AR_SCALE=0 LORA_NAR_SCALE=0` exported (scales are read
by `run_one.sh`), same seeds, same caps, separate `--label evalA_base`.

---

## 7. Objective side-checks (cheap, secondary)

These support the ears; they never override them.

| check | how | reads as |
|---|---|---|
| **Timbre/style distance** | MERT embeddings (`hf_mert` is already cached) of each render vs the 474 training tracks: cosine to the training centroid, and to the nearest training track | LoRA takes should sit closer to the dataset manifold than base takes |
| **Duration / truncation** | `batch_summary.txt` + per-track JSON: did the take hit the cap? | truncation is a structure failure, not a style one |
| **Vocal leakage** | scorecard field `vocals` (none / non-lexical / words) on every take | Q4 |
| **Spectral sanity** | optional: low/high-band balance, clipping count | catches a broken render, not quality |

MERT numbers are a **proxy** (`style` is not in the embedding by construction). Report them
as “consistent with” / “inconsistent with”, never as the verdict.

---

## 8. Blind the package

Two stages, two packages. New blinding seed per round (prior rounds used 20260925/26/27;
take **20261113**), per-category labels, mp3 review copies:

```bash
python INFERENCE/prepare_ab_eval.py \
  --root /content/audiocpp_inference/out/<stageA_run> \
  --output /content/ab_eval/A_ckpt \
  --variants base ck3000 ck4000 ck5000 ck5500 \
  --audio-format mp3 --bitrate 192k --seed 20261113 \
  --json /content/ab_eval/A_ckpt_key.json \
  --title "arabic_instrumental_lora — checkpoint screen"
```

Hand the evaluator `EVAL.txt` + audio only; `KEYS.txt` opens after listening. Then rate with
`ai_music_rating_app` (`--blind`), not an in-repo app (`docs/LISTENING_EVAL.md`).

**Scorecard** — draft for `INFERENCE/scorecards/arabic_instrumental_style.json`:

```json
{
  "schema_version": 1,
  "name": "arabic_instrumental_lora — style fidelity (base vs LoRA, ckpt ladder)",
  "summary_metric": "style_fidelity",
  "criteria": [
    {"key":"style_fidelity","label":"Arabic instrumental ensemble character","type":"rating","max":5,"required":true,
     "scale_labels":{"1":"wrong genre","3":"some Arabic colour","5":"convincingly Arabic instrumental"},
     "help":"Ignore mix and performance; judge whether this sounds like the intended Arabic acoustic ensemble."},
    {"key":"instruments","label":"Instrument realism (oud / violin / cello / darbuka / riq)","type":"rating","max":5,"required":true,
     "help":"Are the named instruments actually present and physically plausible (attack, bow noise, skin/jingle detail)?"},
    {"key":"ornamentation","label":"Ornamentation / microtonality","type":"rating","max":5,"required":true,
     "help":"Slides, vibrato, maqam inflections, call-and-response between oud and strings."},
    {"key":"coherence","label":"Structure / section flow","type":"rating","max":5,"required":true,
     "help":"Do the tagged sections arrive, build and release — or does it loop or wander?"},
    {"key":"production","label":"Mix / production","type":"rating","max":5,"required":true,
     "help":"Warm acoustic room, natural reverb, no mud, no digital harshness."},
    {"key":"vocals","label":"Vocals present","type":"choice","required":true,
     "options":[{"v":"none","t":"None (correct for this prompt)"},{"v":"nonlex","t":"Non-lexical vocalisations"},{"v":"words","t":"Sung words"}]},
    {"key":"artifacts","label":"Artifacts","type":"choice","required":true,
     "options":[{"v":"none","t":"None"},{"v":"minor","t":"Minor"},{"v":"major","t":"Major"},{"v":"broken","t":"Broken"}]},
    {"key":"arm_guess","label":"Which arm is this?","type":"choice","required":true,
     "options":[{"v":"base","t":"Base model"},{"v":"lora","t":"LoRA"},{"v":"unsure","t":"Can't tell"}],
     "help":"Forced guess on every take — this is the discrimination test."},
    {"key":"overall","label":"Overall","type":"rating","max":5,"required":true},
    {"key":"notes","label":"Notes","type":"notes","required":false,
     "help":"Timecodes for artifacts, the instrument that gave it away, anything structurally broken."}
  ]
}
```

---

## 9. Decision rules (written before listening, so the result can't be rationalised)

1. **Did it learn anything?** Discrimination: of the paired P0a/H1–H4 takes in Stage A,
   ≥ 10/13 correct `arm_guess` = audible difference (binomial p < 0.05). Fewer = the adapter
   is inaudible on this test; report that, don't pick a checkpoint.
2. **Style win:** LoRA median `style_fidelity` ≥ 4 **and** ≥ 1 point above base, with
   `artifacts` no worse than base. A style gain bought with major artifacts is a loss.
3. **Checkpoint:** highest `style_fidelity`; tie-break on `coherence` then `artifacts`; if
   still tied, take the **later** checkpoint (more exposure, same risk). Report the full
   ladder, not just the winner.
4. **Generalization (Q3):** H-caption scores must not be more than 1 point above P1/P2
   scores; a large gap means prompt replay, not style learning.
5. **Vocal leakage (Q4):** any `words` on LoRA takes that base doesn't produce = flag. It is
   an expected risk (283/482 captions name vocals), not a surprise — but it changes what the
   adapter is good for.
6. **Over-application (Q5):** P3 must be `style_fidelity` ≤ 2 on both arms. Higher on LoRA
   means the adapter imposes the style regardless of the prompt.
7. **No decision** if Stage A's pairs are confounded (e.g. duration differs, a take
   truncated, a missing file) — fix and re-render that cell rather than interpret it.

Only after 1–7: convert the chosen checkpoint (or reuse the converted pair), record its
sha256, register the `loras/audio_cpp/style/` row, and *then* consider the `quran_ahh_r32`
α-merge (§1.1 of the training plan). Publishing stays a separate decision.

---

## 10. Deliverables

```
results/arabic_instrumental_eval/
  README.md              config table, T4 timings, per-track table
  KEY.json               label -> variant (mirror of KEYS.txt)
  KEY_open_after_listening.txt
  scorecard.json         frozen copy of the card used
  report.md / .csv       from ai_music_rating_app
  mert_similarity.csv    objective side-check
audio                     192k mp3 review copies (committed); raw WAVs stay in GCS
GCS                       …/arabic_instrumental_lora/eval/<stage>/  (backup_to_gcp.py --inference)
```

Provenance to record next to the key: the four converted adapters' sha256, GGUF names,
binary sha256, `input.json` + `batch_manifest.json`, blinding seed, and the 8 holdout names
from `HOLDOUT.json`.

---

## 11. Risks / failure modes

| risk | effect | mitigation |
|---|---|---|
| `arabmaqamrock` trigger left on | every prompt is out-of-distribution; LoRA looks broken | `--no-trigger` + prefix in style (§2.1); assert in `batch_manifest.json` |
| `[Lyrics]` header passed to `--lyrics` | double header, mangled conditioning | split on `\n[Lyrics]\n` (§2.2) |
| cap recomputed per arm | different durations, unfair A/B | pin one integer per prompt (§2.3) |
| `auto` cap on tag-only lyrics | 2750 tokens ≈ 110 s — too short to judge style | pin `cap: 6500` (§2.3) |
| two concurrent renders | NAR OOM, corrupt batch | sequential only (§6) |
| T4 16 GB + long cap | slow or OOM on very long prompts | cap ~6500 for 7 tags; `--limit 1` smoke test first |
| judging on loss | plateau misread as failure | audio-only verdict (§1) |
| base arm forgotten | no control, no claim possible | `LORA_*_SCALE=0` batch, same seeds |
| comparing to v3 numbers | meaningless cross-run loss | not done (§1) |

---

## 12. Checklist

- [ ] training "Job stopped"; `nvidia-smi` clean; no `run.py`
- [ ] `bootstrap/setup.sh --inference` all `[ok]`; `grep '\[FAIL\]'` empty
- [ ] 4 checkpoints pulled + converted; `converted_sha256.txt` written
- [ ] holdout contamination check: 8 names absent from `/content/yue2_dataset`
- [ ] prompts JSON validates (`--dry-run`) and prints a sane projected time
- [ ] Stage A rendered detached, log `/content/logs/evalA_stdout.log`
- [ ] package blinded (seed 20261113), `EVAL.txt` carries no variant names
- [ ] ratings exported; decision rules applied as written
- [ ] winner sha256 recorded; only then conversion/registration/merge talk
