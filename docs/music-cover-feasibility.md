# Music cover / guide-conditioned generation — feasibility

_Last revised: 2026-09-29 (**§11 addendum**: guide-conditioned batch staged for Colab,
with the verified bucket inventory; **§10 addendum**: the verbatim/lyric-adherence blind
round is scored and decoded — no repeats, baseline / baseline+`110 BPM` win; **§9
addendum**: v2 training set characterised, outro-repeat resolved, ABC/cover batch
re-scoped). Earlier,
2026-09-28: route corrected to transcribe with the **official Python SheetSage2** (no
audio.cpp rebuild; binary capability verified). Investigation & discussion record — **not a
runbook**.
The transcription front end (route B2) has been smoke-tested and works; the **ABC**
generation experiments remain unrun — hypotheses are marked as such.
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

Gaps in this repo (as of 2026-09-28; SheetSage2 status re-verified 2026-09-28):
- `INFERENCE/run_one.sh:79` hardcodes `--request-option cot=off`; `INFERENCE/generate.py`
  has no `abc`/`abc_file` field. Covers are not wired into the *generation* drivers —
  a cover render must call the binary directly.
- SheetSage2 **is** in audio.cpp (v0.8.0, PR #553, 2026-09-15), but **our staged
  `bin/audiocpp_cli` does not contain it**: it was built `--model-set custom
  --models yue2` (`DECISIONS.md` build entry) and its strings show **0** `sheetsage`
  (verified 2026-09-28). Upstream releases ship **only `audiocpp_server`** (HTTP, no
  CLI mode) — **no prebuilt `audiocpp_cli`** exists. So the audio.cpp transcription
  route requires a rebuild (`docs/audiocpp_gpu_arch_builds.md`; add `sheetsage2` to
  `--models`). We started that rebuild and **abandoned it as unnecessary**.
- **The generation side needs no rebuild** (verified 2026-09-28): the existing binary
  already carries the cover knobs `abc_file` (×6), `cot` (×18), `melody` (×6), so a
  `cot=melody` + `abc_file` render works today. It does **not** carry `semantic_prefix`
  (×0; landed v0.8.2) — Form ② would need a newer binary; Form ① does not.
- **Chosen transcription route: the *official Python* model** `m-a-p/SheetSage2`
  (`transformers` + `trust_remote_code`, `melody_only=True`) — no audio.cpp, no GGUF,
  no build. It is the reference the audio.cpp GGUF was validated against (ABC parity),
  so its `score.abc` drops straight into `--request-option abc_file=`. Needs its own
  env (torch 2.8/torchaudio 2.8 cu126, transformers 4.45.2, ffmpeg 6.1 + shared libs)
  and the MERT-v2-FullSong backbone (632 M, downloaded separately). The Python-route
  driver is `INFERENCE/sheetsage2_transcribe.py`; the audio.cpp-path
  `INFERENCE/abc_transcribe.py` is superseded for this route.
- The fine-tuned adapters were trained `cot: "off"` (`config/akbar_arabic_rock_lora.yml:106`,
  "your captions carry no melodic/ABC info"), so ABC conditioning is **off-distribution**
  for them — a first-order unknown, hence a 1-track smoke before any batch.

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
- **Consequence for any token-level guide:** the pron fix is **AR-only**
  (`config/pron_lora_ar_only.yml:38` `ignore_if_contains: ["transformer.nar"]`;
  `merge_pron_lora.py:20` copies v2 through every NAR key). So forcing an external
  AR plan — ABC, or the newer `semantic_prefix[_file]` (audio.cpp v0.8.2, 2026-09-24)
  — trades arrangement control against exactly the stream the pronunciation fix lives
  in. A *partial* prefix may thread it; a full override likely reverts pronunciation.

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
- **B2 (faithful; now the chosen transcription route):** liked `cot=off` v2 wav →
  **official Python SheetSage2** (`transcribe(wav, output_dir=…, melody_only=True)`) →
  `melody.abc` → `qfinal_a0.3` with `cot=melody` + `abc_file`. No audio.cpp for this
  step; runs on GPU or CPU; needs its own env. Transcription is lossy vs an exact
  exported plan.

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

**Resolved 2026-09-29 — see §9.** The "verse line repeating" is the adapter's *learned
convention*: the v2 training sheets repeat by design (§9.2) and the training audio
matches them. The sampler is **not** the cause (identical `repetition_penalty=1.2 /
window=50` in every render; the window is only 2.0 s). `semantic_penalty_window` is the
knob aimed at section-length repeats.

## 7. Suggested order of tests

1. **Measure A** (minutes, no new deps): rock-forward style text, same seed/adapter;
   then optionally `guidance_scale=1.3–1.5`.
2. If the arrangement still collapses: **Measure B**, 1-track smoke first.
   - Transcribe the liked `cot=off` v2 wav with the **official Python SheetSage2**
     (`melody_only=True`) → `melody.abc` — route B2, no audio.cpp build.
   - Cover render on the **existing** `audiocpp_cli`: `qfinal_a0.3`, `cot=melody` +
     `abc_file`, same lyrics/seed.
   - (B1 — export v2's own `score.abc` via `cot=full --out-dir` — stays exact but is a
     different v2 render.)
3. Blinded A/B each against the α0.3 control; keep α0.3 fixed throughout.

## 8. Provenance

- YuE2 model card, cover section + SHS100K benchmark: <https://huggingface.co/m-a-p/YuE2-3B>
- SheetSage2 (upstream) + GGUF: <https://huggingface.co/m-a-p/SheetSage2>,
  <https://huggingface.co/audio-cpp/SheetSage2-GGUF>
- audio.cpp SheetSage2 merge (v0.8.0): <https://github.com/0xShug0/audio.cpp/pull/553>
- audio.cpp releases ship `audiocpp_server` only (no prebuilt `audiocpp_cli`):
  <https://github.com/0xShug0/audio.cpp/releases/tag/v0.8.2-audio8-perf-hotfix>
- Python SheetSage2 cover mode (`melody_only=True`): <https://huggingface.co/m-a-p/SheetSage2>
- audio.cpp YuE2 options (`cot`, `abc`/`abc_file`, `score.abc`, `semantic_prefix`):
  `https://github.com/0xShug0/audio.cpp/blob/main/docs/models/yue2.md`
- audio.cpp MuScriptor (audio→MIDI/note-JSON):
  `https://github.com/0xShug0/audio.cpp/blob/main/docs/models/muscriptor.md`
- Repo drivers: `INFERENCE/sheetsage2_transcribe.py` (Python route, used) and
  `INFERENCE/abc_transcribe.py` (audio.cpp path, superseded); handoff:
  `agent_notes/current.md`.
- Repo: `docs/LORA_INVENTORY.md`, `docs/PRON_LORA_MERGE.md`,
  `config/akbar_arabic_rock_lora.yml:106`, `INFERENCE/run_one.sh:79`,
  `INFERENCE/generate.py`, `manifests/batch_36_songs.json`.

---

## 9. Addendum — 2026-09-29: the v2 training set, the repeat question, lyric adherence

_Session outcome: the "outro repeats itself" anomaly is resolved (a trained
convention, not the sampler); the training set is characterised from GCS; the
ABC/cover batch is re-scoped. Read with §6 (descriptors) and §4–5 (the levers).
Full knob tables + the proposed batch live in `agent_notes/current.md`._

### 9.1 Where the training data is, and what it is

`gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/dataset/` — **267**
`.mp3` + `.txt` pairs. Each `.txt` is one training example: the caption (style)
first, then `[Lyrics]`, then the lyrics with section tags. Measured over all 267
(read-only; no generation):

| property | value |
|---|---|
| Maqam balance | Nahawand 73, Ajam 72, Kurd 62, Hijaz 60 |
| Caption trigger `arabmaqamrock` | **267/267 (100%)** |
| Caption `<n> BPM` | **267/267** — always `110` |
| Caption shape | **267/267 flat** (no `genre:`/`vocals:` keys) — unlike the Suno block (§6) used at inference |
| Caption tail `Mood:` | 233/267 (87%) |
| Lyrics tags | **0/267** carry `[Section \| descriptors]`; all **bare** (`[Intro]`, `[Verse 1]`, …) |
| Sections per song | mean 5.6 |

### 9.2 The repeats are the target — the dataset is self-consistent

Repetition is built into the training lyrics by the `suno-workflow`
(`github.com/akbargherbal/suno-workflow`; Phase 5 rule 8 "buffer-in/out"; Phase 3
rules 1, 2, 10):

| pattern | prevalence |
|---|---|
| `[Intro]` content == opening of `[Verse 1]` (buffer-in) | 261/267 (98%) |
| `[Outro]` content already appears earlier (buffer-out) | 263/267 (99%) |
| duplicate `[Chorus]` block | 127/267 (48%) |
| ≥1 repeated lyric line anywhere | **267/267 (100%)** |
| fraction of lines that are repeats | mean **23%** |

**Correction to §6's "anomalous repetition":** the sheet repeats and the audio
matches — a couplet is sung 2× (once in its verse, once in the `[Outro]`), never 3×.
So v2 was trained to sing the sheet **verbatim, repeats included**; "verbatim" means
*reproduce the sheet exactly*. The anomaly to chase is an **insertion beyond the
sheet** (3× / dropped / reordered), not the sheet's own repeats. Because training
adhered, an extra repeat at inference is more likely an **inference-side mismatch**
(descriptor tags / format / prompt) than the data.

### 9.3 The sampler is not the cause

Every render (all 5 ablation variants; all 36-batch takes) logs the same
`yue2 … repetition_penalty=1.2 penalty_window=50`. Source (`ar_runtime.cpp`,
`sample_semantic_token`) penalises only the last `penalty_window` emitted frames, so
the window is **50 / 25 = 2.0 s** — far shorter than a section, hence it cannot
suppress a section-level repeat. **`semantic_penalty_window` is the knob pointed at
this symptom** (200–1000 frames = 8–40 s, with a modest penalty).

### 9.4 Knobs for lyric adherence / v2 fidelity (summary; tables in `current.md`)

- **Settings:** `semantic_penalty_window` (the section-repeat lever), `guidance_scale`
  (CFG on the text; default `1.01` for `cot=off`), `semantic_repetition_penalty`,
  `semantic_temperature`/`top_p`/`top_k`. Keep `cot=off` + `temp 1.0` + `top_p 0.95` +
  `top_k 100` = the adapter's trained regime (protects v2 likeness).
- **Prompt:** `style` (flat caption; **restore `110 BPM`** — 100% of training captions
  carry it) and `--lyrics` (bare tags = trained; descriptor tags = off-distribution).
- **ABC:** `abc`/`abc_file` steer the **melody, not the words**; they require
  `cot=melody|full`, itself off-distribution for a `cot=off` adapter.
- **Measurement:** `export_semantic=true` + `stop_after=semantic` dumps the token plan
  so adherence can be scored objectively at no NAR cost.

### 9.5 The ABC/cover batch — re-scoped

Proposed guide = `01-نسيب-وظعن-الحي-ونخيل-يامن-وعرائس-النعمة_4148240095.wav`
(`batch_36_songs.json`: Hijaz, `lora: v2`; two further seeds on GCS). Review:

- **Maqam clash:** the "winning prompt" is **Ajam** (`current.md` §1); this track is
  **Hijaz**. ABC (Hijaz) + Ajam text will fight — use a Hijaz copy.
- **ABC confounds `cot`:** `abc_file` forces `cot=melody|full`; the adapter trained
  `cot=off`. Any ABC arm needs a `cot=melody`-no-`abc` control.
- **Missing:** a control arm; a **no-repeat-sheet** arm (the only one that separates
  "followed the sheet" from "injected the prior"); n=1 seed; an objective metric.
  *Update §10: the control and no-repeat-sheet arms were subsequently rendered and scored.*
- Built at `manifests/test_verbatim_hijaz/batch.json` (`generate.py` arms:
  `ctl_sunoblk_as-is`, `win_as-is`, `mod_as-is`, `win_dedup`, `win_bare`) plus
  `INFERENCE/test_batch.sh <knobs|abc|all>` (the arms `generate.py` can't express —
  B: `b1_window`…`b3raw_both`; C: `c0_cotonly`…`c3_abc_raw`; `c3_abc_raw` = the raw
  Suno block that scored 5/5 MaqamRock). Working details + the revise-placeholder in
  `agent_notes/current.md`.

### 9.6 Open questions for the next session

1. Does ABC (`cot=melody|full`) help or hurt (a) lyric adherence, (b) v2 arrangement
   fidelity? **Unrun.**
2. Does the **descriptor-tag** mismatch (bare tags in training vs descriptor tags at
   inference) explain the extra repeat? Test: same track, bare-tag vs descriptor sheet.
   **§10: no extra repeat was observed in any arm — not implicated on this track.**
3. Which adapter for the batch — `v2` or `qfinal_a0.3`? (§3's tradeoff decides.)
4. Does a **no-repeat sheet** get echoed (adapter injection) or sung clean?
   **Answered §10: sung clean — no injection.**

### 9.7 Provenance additions (2026-09-29)

- Training dataset: `gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/dataset/`
  (267 pairs; the LoRA's actual training text).
- Workflow that built the repeats: `github.com/akbargherbal/suno-workflow`
  (`workflow.md`, `Quick_Guide.md`).
- Session handoff + knob tables + proposed batch: `agent_notes/current.md`.

---

## 10. Addendum — 2026-09-29: the verbatim / lyric-adherence blind round (scored)

_The §9.6 repeat questions (Q2, Q4) are answered here by listening; Q1 (ABC) stays unrun.
Scores: `manifests/evaluation_verbatim_hijaz/MY_EVALUATION.txt`; decoder: same dir
`KEYS.txt` (the earlier build's `KEY.json` was deleted 2026-09-29). The audio package
lives on GCS (`listening/VERBATIM_HIJAZ_LYRIC_ADHERENCE_INPUT/`). One track, one seed, one
listener — a signal, not proof._

### 10.1 Design

One track (`01-نسيب…_4148240095`, **Hijaz**), adapter **v2** (step 3000), render seed
`4148240095`, all `cot=off`. Five arms differ **only** in the style text and/or the lyric
sheet, so a difference is attributable to that change. Blinded + shuffled with
`INFERENCE/prepare_ab_eval.py` (blinding seed `20260929`); scored blind, then decoded:

| label | arm | the one variable isolated |
|---|---|---|
| A | `ctl_sunoblk_as-is` | baseline — the track's own raw Suno block + its sheet |
| B | `mod_as-is` | the "winning" prompt + `110 BPM` restored |
| C | `win_dedup` | the "winning" prompt + a sheet with the built-in repeats **removed** (injection test) |
| D | `win_as-is` | the "winning" `l2_target_off` prompt alone |
| E | `win_bare` | the "winning" prompt + bare `[Verse 1]` tags (the trained format) |

### 10.2 Result

| section | A | B | C | D | E |
|---|---:|---:|---:|---:|---:|
| intro-verse vocal | 4.5 | **5** | 4 | 4 | 4 |
| maqam rock (v2) | 4.5 | 4.5 | 4 | 4 | 4 |
| overall vocal | 4.5 | **5** | 4.5 | 4 | 4 |
| pronunciation | 4.5 | 4.5 | **5** | 4 | 4 |
| lyrics adherence | 5 | 5 | 5 | 5 | 5 |
| pace | **5** | 4.5 | 3.5 | 4 | 3.5 |
| **mean** | 4.67 | **4.75** | 4.33 | 4.17 | 4.08 |
| vocal start | 22 s | 21 s | 30 s | 19 s | 6 s |

- **Repeats — none, in any arm.** The no-repeat sheet (C) was **not** re-filled with the
  removed repeats; every clip scored 5/5 for singing its own sheet. **§9.6 Q4 answered:**
  the adapter did **not** inject the prior's repeats on this track.
- **Quality: B ≥ A > C > D > E.** The baseline (A) and baseline+`110 BPM` (B) lead; the
  "winning" prompt (D) came **4th** ("generic / meh"), bare tags (E) **last**. The
  listener's own summary: *"best-sounding: A OR B"*.
- **Objective corroboration:** rendered durations equal the §9 screen's predicted frame
  counts (5/5) and none truncated — an injected repeat lengthens the plan, and the guide's
  natural plan (7743) sits 7 frames under the 7750 cap. Ears and length agree.
- **§9.6 Q2** (descriptor-tag mismatch → extra repeat): no extra repeat anywhere, so it is
  not implicated here. **Q1 (ABC) remains unrun** — every arm in this round was `cot=off`.

### 10.3 Caveats

n=1 track, 1 seed, 1 listener, subjective 1–5 with no confidence recorded; B over A is
`0.08` (noise-level). This is evidence the defect did not reproduce on this track, and that
the "winning" prompt / bare-tag format are unsupported here — not a general verdict on the
adapter.

### 10.4 Provenance

- Scores + blank sheet: `manifests/evaluation_verbatim_hijaz/MY_EVALUATION.txt`; decoder
  `manifests/evaluation_verbatim_hijaz/KEYS.txt`.
- Packaging tool: `INFERENCE/prepare_ab_eval.py` (skill `ab-blind-eval`); blinding seed
  `20260929`.
- Render run dir: `out/verbatim_hijaz_seed4148240095` (5/5 durations matched the screen);
  round uploaded in commit `6443287`.
- Session notes + knob tables: `agent_notes/current.md`.

---

## 11. Addendum — 2026-09-29: guide-conditioned batch, staged for Colab

_The feasibility question — "can v2's plan guide `qfinal_a0.3` into v2's maqamrock
arrangement while keeping its pronunciation?" — is now a runnable batch. This is the
durable state: what exists, the guide choices, the risks, and what the run would settle.
Commands + verified paths: `agent_notes/current.md`; driver:
`INFERENCE/v2_abc_to_qfinal.sh`._

### 11.1 Verified inventory (bucket read-only, `gsutil ls`, 2026-09-29)

| asset | bucket path (under `…/OSTRIS_Arabic_Suno_Finetuning/`) | note |
|---|---|---|
| candidate adapter | `loras/audio_cpp/pron/qfinal_a0.3/akbar_arabic_rock_lora_{ar,nar}.safetensors` | AR rank 40 |
| v2 style pair | `loras/audio_cpp/style/…` | staged by `setup.sh` |
| guide ABC (B2) | `audiocpp_inference/workspace/out/abc_v2/01-نسيب…_4148240095/score.abc` | + `chords.mid`, `melody_vocal.mid`, `tokens.json` |
| 11 more v2 ABCs | `…/workspace/out/abc_v2/` | 12 dirs total |
| guide WAV | `…/workspace/out/batch_36_songs/01-نسيب…_4148240095.wav` | B2 source / reference |
| today's 5 arms | `…/workspace/out/verbatim_hijaz_seed4148240095/*.wav` | re-listenable |
| pinned tooling | `audiocpp_inference/tools/{build,converter,prompts,scripts}` | |
| **not stored** | v2's own `cot=full` `score.abc` (B1) | phase 1 generates it on Colab |

### 11.2 Guide options

| guide | route | what it carries | availability |
|---|---|---|---|
| SheetSage2 ABC | B2 (`abc_v2/…/score.abc`) | melody (+ `chords.mid` sidecar); `melody_only=True` | present now |
| v2's own `score.abc` | B1 (`cot=full --out-dir`) | v2's *full-mode* plan, melody + chords | generate on Colab |
| v2 `cot=off` semantic plan | `semantic_prefix[_file]` | the **exact** plan of the liked render | **blocked** — binary < v0.8.2 |

### 11.3 The three risks (unchanged from §3)

1. **AR conflict** — the pron fix lives in the AR stream; any guide overrides it.
2. **Off-distribution** — adapters trained `cot=off`; `abc_file` forces `cot=melody|full`
   (a `cot`-only arm is required to separate the effects).
3. **Melody ≠ arrangement** — the stored ABCs are melody-only; only B1 (`score.abc`) or
   `semantic_prefix` carry chords/plan.

Plus two practicals: the guide must match the prompt's maqam (Hijaz ABC + Hijaz prompt, not
the Ajam "winning" prompt); and there is **no objective arrangement metric** — the verdict
is listening/blind.

### 11.4 The batch (four arms, one track/seed)

`INFERENCE/v2_abc_to_qfinal.sh` — phase 1 exports v2's `score.abc`; phase 2 renders
`a0_cotoff` (qfinal control), `a1_cotfull_noabc` (cot-only), `a2_cotfull_abc` (the idea),
`ref_v2_cotoff` (v2 reference), all at the same style/lyrics/seed. Set
`ABC_SCORE=<abc_v2 score.abc>` to use B2 and skip phase 1. ~35 min on a T4.

### 11.5 What would settle it

Listen `a0` vs `a2`: if `a2` keeps v2's arrangement but pronounces like v2, the AR-override
conflict is real and only the prefix route (blocked) can thread it; if `a2` ≈ `a0`, the
guide did nothing. Blind the arms for a fair call.

### 11.6 Provenance

- Bucket listing: read-only `gsutil ls`, 2026-09-29.
- Driver: `INFERENCE/v2_abc_to_qfinal.sh` (`bash -n` + `--dry-run` checked; `--stage` pulls
  `qfinal_a0.3`).
- Handoff: `agent_notes/current.md`.
