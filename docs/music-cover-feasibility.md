# Music cover / guide-conditioned generation — feasibility

_Last revised: 2026-09-28. Investigation & discussion record — **not a runbook**.
No experiment described here has been run yet; hypotheses are marked as such.
Authority for procedures stays with `docs/INFERENCE.md`, `docs/PRON_LORA_MERGE.md`,
`docs/LORA_INVENTORY.md`, and `config/akbar_arabic_rock_lora.yml`._

## 1. Question

Is it feasible to use an existing track as a *guide* for generation — i.e. a
"song cover" — and would that help the current pronunciation-vs-style tradeoff?

## 2. What "cover" actually means in YuE2 (symbolic, not audio-to-audio)

YuE2 has a first-class cover workflow, but the guide enters as a **symbolic
melody score (ABC) + lyrics**, never as raw audio. There is no audio-to-audio or
voice-clone input. (`m-a-p/YuE2-3B` model card, "Cover" section.)

Upstream cover recipe:
1. Transcribe the source song with **SheetSage2** → `melody.abc` (melody, no chord symbols).
2. Get the lyrics (Qwen3-ASR / Gemini, or manual) → `cover_lyrics.txt`.
3. Generate with `cot="melody"` (recommended for covers) or `cot="full"`, passing
   `style` + `abc` + `lyrics`.

Quality signal: on SHS100K zero-shot cover, YuE2 (full score) reports **CLEWS
Hit@1 71.3%, mAP 0.647**; "without score" drops to **0.3% / 0.006** — the score is
what carries song identity.

`audio.cpp` (our runtime) already exposes the machinery: `cot=melody|full`,
`abc=` / `abc_file=`, `semantic_prefix[_file]`, and it **exports the generated
score** as `score.abc` under `--out-dir` (`docs/models/yue2.md`, audio.cpp).

Gaps in this repo (as of 2026-09-28):
- `INFERENCE/run_one.sh:79` hardcodes `--request-option cot=off`; `INFERENCE/generate.py`
  has no `abc`/`abc_file` field. Covers are not wired into the drivers.
- No transcription stage is staged. SheetSage2 is **not** ported to audio.cpp (no
  model doc); audio.cpp's **MuScriptor** (`--task midi --family muscriptor`) does
  audio→MIDI/note-JSON, not ABC.
- The fine-tuned adapters were trained `cot: "off"` (`config/akbar_arabic_rock_lora.yml:106`,
  "your captions carry no melodic/ABC info"), so ABC conditioning is **off-distribution**
  for them — a first-order unknown.

## 3. The tradeoff being worked around (α)

- **v2 style adapter (no pron):** gives the arabmaqamrock melody/arrangement wanted,
  but Arabic pronunciation struggles.
- **`qfinal_a0.3`:** good pronunciation, but perceived as drifting toward minimal
  Islamic-nasheed territory (sparse, percussion-led). α0.3 is held as the sweet spot;
  lowering α swings back to pronunciation problems.
- Mechanics: `qfinal_a0.3` is **not** a Quran adapter replacing style. It is
  `v2 = v2_style_Δ + 0.3·pron_Δ` merged in the **AR branch**; the **NAR branch is
  copied verbatim from v2** (`docs/LORA_INVENTORY.md:56-63`, `docs/PRON_LORA_MERGE.md`).
  So the drift is an **AR-plan effect** (sparser, more vocal-centric token plan) plus
  style-prompt adherence; the timbre/render machinery is identical to v2.
- Because pron and the arrangement live in the **same AR branch** and there is one
  LoRA slot per expert, pron cannot be applied without its AR perturbation. Lowering
  α only reduces the perturbation's magnitude — it does not separate the two.

## 4. Measure A — the style-text (prompt) lever — cheapest, in-distribution

The style text is the arrangement control, and the current caption **explicitly asks
for the drift**. Generation captions (e.g. `manifests/batch_36_songs.json`,
`defaults.style`) contain:
- `hymn-like grand concert hall acoustics`
- `forward vocals pulling instrumentation down on sustained phrases then band re-enters between lines`
- `stately groove, 110 BPM`
- `orchestral strings`

These are signed cues toward a solemn, voice-forward, sparse arrangement. They are
**in-distribution**: `prepare_yue2_dataset.py:86` `build_caption` trains on exactly the
`genre / vocals / production / instrumentation / mood` fields, so editing them is a
legitimate lever, not something that fights the adapter.

Proposed edit (keep `vocals` and `mood`; rewrite the rest):
- genre → `arabmaqamrock, driving symphonic rock, powerful modern production, 124 BPM.`
- production → `Punchy centered modern rock mix, full band arrangement throughout,
  distorted guitars and drums prominent beneath sustained vocals, wide dynamic range,
  minimal hall reverb.`
- instrumentation → `Distorted electric guitars, driving acoustic rock drums, prominent
  electric bass, orchestral strings as accent, tight rhythm section.`

Interaction with `guidance_scale`: CFG amplifies the *text prompt*, so raising it while
the text still says "hymn-like" makes the drift **worse**. Fix the text first, then try
`guidance_scale=1.3–1.5` (`EXTRA_REQUEST_OPTS`, forwarded verbatim by `run_one.sh`;
no duplicate-key collision). The knob probe tested `guidance_scale=1.5` only at α0.5
with the unchanged text — the combined test is new.

Verification: one variable (style text), same lyrics, same seed, same adapter, then a
blinded A/B against the α0.3 control (`INFERENCE/prepare_ab_eval.py`, skill
`ab-blind-eval`).

## 5. Measure B — ABC score-conditioning (new; targets the AR plan where the drift lives)

Two ways to obtain the score:
- **B1 (recommended, in-stack, exact):** run **v2** with `cot=full` and `--out-dir` →
  the binary writes `score.abc`; then render with `qfinal_a0.3` using
  `--request-option cot=full --request-option abc_file=<score.abc>` + same style/lyrics/seed.
  No SheetSage2, no transcription loss. Caveat: the guide is v2's *full-mode* plan, a
  different render from the `cot=off` v2 track that is liked.
- **B2 (faithful but fragile):** liked `cot=off` v2 wav → SheetSage2 → `melody.abc` →
  `qfinal_a0.3` with `cot=melody`. Requires SheetSage2 in a separate env (not staged);
  transcription is lossy.

Caveats: adapters trained `cot=off` (off-distribution ABC); α is unchanged (this does
not touch pronunciation, it tries to out-vote the arrangement drift with v2's plan);
two renders per song; `run_one.sh`/`generate.py` do not support `abc_file`/`cot`, so
this path calls the binary directly (the hardcoded `cot=off` at `run_one.sh:79` would
otherwise conflict).

Hypothesis: forcing the melody+chords of the richer v2 full-mode plan into the AR stage
should suppress the pron-induced sparsity. **Unverified.**

## 6. Note on Suno descriptors and lyrics (user observation, 2026-09-28)

Contrary to earlier agent advice to normalize the Suno lyric descriptors: **the
descriptors were helpful**, if anything, in making the output adhere to arabmaqamrock.
Normalizing them is **unnecessary** and is not the way forward.

Some anomalous behavior was observed — e.g. a verse line repeating where there is no
repetition in the source lyrics. But normalizing the lyrics is **not** the fix.

Implication: treat the inline `[Section | descriptors]` (and other raw Suno tags) as
intentional arrangement steering; do not strip them. If the repetition anomaly needs
investigating, look at decoding/sampling knobs (e.g. `semantic_repetition_penalty`,
`semantic_penalty_window`, `semantic_temperature`) rather than rewriting the lyrics.

## 7. Suggested order of tests

1. **Measure A** (minutes, no new deps): rock-forward style text, same seed/adapter;
   then optionally `guidance_scale=1.3–1.5`.
2. If the arrangement still collapses: **Measure B1** (score export + `abc_file`),
   1-track smoke first.
3. Blinded A/B each against the α0.3 control; keep α0.3 fixed throughout.

## 8. Provenance

- YuE2 model card, cover section + SHS100K benchmark: <https://huggingface.co/m-a-p/YuE2-3B>
- audio.cpp YuE2 options (`cot`, `abc`/`abc_file`, `score.abc`, `semantic_prefix`):
  `https://github.com/0xShug0/audio.cpp/blob/main/docs/models/yue2.md`
- audio.cpp MuScriptor (audio→MIDI/note-JSON):
  `https://github.com/0xShug0/audio.cpp/blob/main/docs/models/muscriptor.md`
- Repo: `docs/LORA_INVENTORY.md`, `docs/PRON_LORA_MERGE.md`,
  `config/akbar_arabic_rock_lora.yml:106`, `INFERENCE/run_one.sh:79`,
  `INFERENCE/generate.py`, `manifests/batch_36_songs.json`.
