# Music cover / guide-conditioned generation — feasibility

_**Answer (2026-09-29):** conditioning `qfinal_a0.3` on **v2's own exported `score.abc`** at
`cot=full` kept v2's maqamrock arrangement **and** pronounced better than v2 — in one blind
listening round (§7). The guide is the fix; replication pending (§8)._

_Investigation record, **not a runbook**. Procedures stay with `docs/INFERENCE.md`,
`docs/PRON_LORA_MERGE.md`, `docs/LORA_INVENTORY.md`, and
`config/akbar_arabic_rock_lora.yml`. Round scores live in
`manifests/evaluation_*/MY_EVALUATION.txt`. Last updated 2026-09-29._

## 1. Question

Can an existing track be used as a *guide* for generation (a "song cover") — and does that
help the current **pronunciation-vs-arrangement** tradeoff?

## 2. What "cover" means in YuE2 (symbolic, not audio-to-audio)

YuE2 has no audio-to-audio or voice-clone input. The guide is a **symbolic melody score
(ABC) + lyrics** (`m-a-p/YuE2-3B`, "Cover" section). Upstream recipe: **(1)** transcribe the
source with **SheetSage2** → `melody.abc`; **(2)** supply lyrics; **(3)** generate
`cot="melody"|"full"` with `style` + `abc` + `lyrics`. The score is what carries song
identity: SHS100K zero-shot cover **CLEWS Hit@1 71.3% / mAP 0.647** with score vs
**0.3% / 0.006** without.

`audio.cpp` (our runtime) exposes `cot=melody|full`, `abc=`/`abc_file=`,
`semantic_prefix[_file]`, and **exports the generated score as `score.abc`** under `--out-dir`
(`docs/models/yue2.md`).

**Repo state (verified 2026-09-28):**

- **Generation is wired at the binary only.** `INFERENCE/run_one.sh:79` hardcodes `cot=off`
  and `generate.py` has no `abc`/`abc_file` field, so a cover render calls `audiocpp_cli`
  directly (see `INFERENCE/v2_abc_to_qfinal.sh`).
- **The staged binary already has the generation knobs** — `abc_file`×6, `cot`×18,
  `melody`×6 — so `cot=melody|full` + `abc_file` works today. It does **not** carry
  `semantic_prefix` (landed v0.8.2); the prefix route needs a newer binary.
- **SheetSage2 is not in the staged binary** (built `--model-set custom --models yue2`;
  0 `sheetsage` strings), and no prebuilt `audiocpp_cli` is published. The audio.cpp
  transcription rebuild was started and **abandoned as unnecessary**.
- **Chosen transcription route = the official Python `m-a-p/SheetSage2`**
  (`melody_only=True`; driver `INFERENCE/sheetsage2_transcribe.py`; own env — torch 2.8
  cu126 + MERT-v2-FullSong backbone). Its ABC drops straight into `abc_file=`.
  `INFERENCE/abc_transcribe.py` (audio.cpp path) is superseded.
- **The adapters trained `cot=off`** (`config/akbar_arabic_rock_lora.yml:106`), so ABC
  conditioning is **off-distribution** — hence a 1-track smoke before any batch.

## 3. The α tradeoff (why a guide is needed)

| adapter | arrangement | pronunciation |
|---|---|---|
| **v2** (style only) | good arabmaqamrock band | struggles |
| **`qfinal_a0.3`** | drifts to sparse, percussion-led nasheed | good |

Both live in the **same AR branch**: `qfinal_a0.3 = v2_style_Δ + 0.3·pron_Δ` merged into AR,
with the **NAR branch copied verbatim from v2** (`docs/PRON_LORA_MERGE.md`). The drift is
therefore an **AR-plan effect**, and lowering α only shrinks the perturbation — it does not
separate pronunciation from arrangement.

**Consequence for any token-level guide.** The pron fix is **AR-only**
(`config/pron_lora_ar_only.yml:38` ignores `transformer.nar`), so forcing an external AR
plan — ABC, or `semantic_prefix` — competes with exactly the stream pronunciation lives in.
A *partial* prefix may thread it; a full override would likely revert pronunciation.
**Result:** the full ABC guide did **not** revert pronunciation (§7) — the risk did not
materialise on this track.

## 4. Levers

### 4.1 Style text — cheapest, in-distribution (*combination untested*)

The current caption **asks for the drift**: `hymn-like grand concert hall acoustics`,
`forward vocals pulling instrumentation down…`, `stately groove, 110 BPM`,
`orchestral strings`. Editing it is legitimate — `prepare_yue2_dataset.py:86` trains on
exactly the `genre / vocals / production / instrumentation / mood` fields. Proposed
rock-forward rewrite: genre → `arabmaqamrock, driving symphonic rock, 124 BPM`; production
→ punchy centered rock mix, full band throughout, minimal hall reverb; instrumentation →
distorted guitars, driving rock drums, prominent bass, strings as accent. Raise
`guidance_scale` only *after* fixing the text (CFG amplifies the prompt; raising it while the
text says "hymn-like" makes the drift worse).

### 4.2 ABC score conditioning — *validated (§7)*

- **B1 (in-stack, exact):** run **v2** `cot=full --out-dir` → `score.abc`; render
  `qfinal_a0.3` with `cot=full` + `abc_file=<score.abc>`, same style/lyrics/seed. No
  transcription loss; the guide is v2's full-mode plan (melody **+ chords**). **This is the
  route that worked.** Caveat: it is a different v2 render from the liked `cot=off` track.
- **B2 (faithful, lossy; unrun):** liked `cot=off` v2 wav → **Python SheetSage2** →
  `melody.abc` → `qfinal_a0.3` `cot=melody` + `abc_file`. Melody-only.

### 4.3 Knobs for adherence / v2 fidelity

`semantic_penalty_window` (the section-repeat lever — the default window is only 2.0 s),
`guidance_scale` (default `1.01` for `cot=off`), `semantic_repetition_penalty`,
`semantic_temperature/top_p/top_k`. Keep the trained regime — `cot=off`, `temp 1.0`,
`top_p 0.95`, `top_k 100`. `export_semantic=true` + `stop_after=semantic` dumps the token
plan so adherence can be scored objectively.

## 5. Established: the v2 training set (measured over 267 pairs)

Read-only audit of `gs://…/OSTRIS_Arabic_Suno_Finetuning/dataset/`.

| property | value |
|---|---|
| Maqam balance | Nahawand 73, Ajam 72, Kurd 62, Hijaz 60 |
| Caption trigger `arabmaqamrock` | 267/267 (100%) |
| Caption `<n> BPM` | 267/267 — always `110` |
| Caption shape | 267/267 flat (no `genre:`/`vocals:` keys) — unlike the Suno block used at inference |
| Lyrics tags | 0/267 carry `[Section \| descriptors]`; all bare (`[Intro]`, `[Verse 1]`) |
| Sections per song | mean 5.6 |

**Repeats are intended, not a defect.** The sheet repeats by design (`suno-workflow`
buffer-in/out): `[Intro]` == `[Verse 1]` opening 98%, `[Outro]` reprise 99%, duplicate
chorus 48%, ≥1 repeated line in 100% (mean 23% of lines). **v2 sings the sheet verbatim,
repeats included** — the anomaly to chase is an *insertion beyond the sheet*
(3× / dropped / reordered), most likely an inference-side mismatch, not the data. **The
sampler is not the cause:** every render uses `repetition_penalty=1.2 / window=50` = 2.0 s,
far shorter than a section. Treat inline `[Section | descriptors]` tags as intentional
steering — do **not** strip them.

## 6. Round 1 — verbatim / lyric adherence (v2, `cot=off`)

5 arms, one Hijaz track (seed `4148240095`), blinded seed `20260929`; arms differed only in
style text / lyric sheet: A baseline raw Suno block; B winning prompt + `110 BPM`; C same
with repeats removed (injection test); D winning prompt; E bare tags.

Scale 1–5; **quality: B (4.75) ≥ A (4.67) > C (4.33) > D (4.17) > E (4.08)**.

- **No repeats in any arm** — the no-repeat sheet was not re-filled, so the adapter does
  **not** inject the prior's repeats.
- The "winning" prompt (D) placed **4th**; bare tags (E) **last**. Baseline / baseline+`110
  BPM` are the best here.
- Durations matched the predicted frame counts; the guide's natural plan (7743) sits 7 under
  the 7750 cap.
- Caveat: n=1, subjective; B − A = 0.08 is noise.

## 7. Round 2 — guide-conditioned (the answer)

Same track/seed; four arms, blinded seed **`20260932`**. A = `ref_v2_cotoff`,
B = `a0_cotoff` (qfinal control), C = `a1_cotfull_noabc`, D = `a2_cotfull_abc` (**v2's
`score.abc`**).

| section | A v2 | B a0 | C a1 no-abc | D a2 +abc |
|---|---:|---:|---:|---:|
| arrangement fidelity | 4.5 | 3.5 | 3 | **5** |
| overall pronunciation | 4 | 4.5 | 5\* | 4.5 |
| pace | 4.5 | 4 | 2 | **5** |
| overall vocal | 4 | 4 | 3.5 | **4.5** |
| duration | 271.9 s | 256.8 s | 310.0 s (cap) | 282.2 s |

\*C's 5 is **reciter / Quranic cadence** (the leak), so it is pyrrhic — D is the best *sung*
pronunciation.

- **The guide wins both axes on one clip: D (`a2`).** Arrangement fidelity 5 ≥ v2's 4.5;
  pronunciation 4.5 > v2's 4.0. **The AR-conflict risk (§3) did not materialise here.**
- **D vs C is the proof:** identical except D got `score.abc`. Adding the guide took
  arrangement `3 → 5`, pace `2 → 5`, and turned a **non-finishing** take into a complete
  one — C's 310.0 s is the `7750`-token cap; v2's plan fits under it.
- **`cot=full` with no plan (C) is the failure mode:** sparse, percussion-only
  nasheed/recitation ("like poem recitation"), 28 s intro, did not finish.
- Caveats: n=1; D is still not "wow" (wants crisper pronunciation); D's intro is 3 s
  (shortest); **no objective arrangement metric** — this is a listening call.

**Provenance caveat.** The scored build is the seed-`20260932` `.wav` manifest
(`manifests/evaluation_v2_abc_to_qfinal/`). The GCS `listening/V2_ABC_TO_QFINAL_INPUT/`
package is a *different, unused* seed-`20260931` shuffle (`A=a2, B=ref_v2, C=a0, D=a1`) and
must not be mistaken for the record. The decode is mechanical: the listener's files match
the per-arm render logs byte-for-byte (`ref` 52,208,428 / `a0` 49,313,068 / `a1` 59,519,788 /
`a2` 54,182,188 B).

## 8. Open questions

- [ ] **Replicate round 2** on the other two seeds (`1029169725`, `1938238049`) — the sheet
  asks for it. *(next)*
- [ ] **B1 vs B2 guide.** Does the melody-only SheetSage2 ABC (B2) steer arrangement as well
  as v2's full plan (B1)? B2 unrun.
- [ ] **Style-text lever (§4.1).** Does a rock-forward caption close the gap without a
  guide, and does `guidance_scale` 1.3–1.5 help once the text is fixed? Unrun.
- [ ] **Partial prefix.** Can `semantic_prefix` steer arrangement *without* reverting
  pronunciation? **Blocked** — staged binary < v0.8.2.
- [ ] **Objective arrangement metric.** None exists; the verdict is listening-only. Worth a
  proxy (stem energy / drum presence)?
- [ ] **Stale GCS package.** Refresh or delete `listening/V2_ABC_TO_QFINAL_INPUT/`.

## 9. Guardrails / caveats

- Every round here is **n = 1 track, 1 seed, 1 listener** — a signal, not a verdict.
- The adapters are `cot=off`; all ABC results are **off-distribution**.
- A guide and its prompt must share the **maqam** (Hijaz ABC + Hijaz prompt).
- Scores are subjective 1–5 with no confidence captured.

## 10. Sources & artifacts

- **Upstream:** YuE2 cover + SHS100K — <https://huggingface.co/m-a-p/YuE2-3B>; SheetSage2 —
  <https://huggingface.co/m-a-p/SheetSage2>; audio.cpp YuE2 options —
  `https://github.com/0xShug0/audio.cpp/blob/main/docs/models/yue2.md`; SheetSage2 merge
  (PR #553) — <https://github.com/0xShug0/audio.cpp/pull/553>.
- **Drivers:** `INFERENCE/v2_abc_to_qfinal.sh` (the batch),
  `INFERENCE/sheetsage2_transcribe.py` (Python transcription; `abc_transcribe.py`
  superseded), `INFERENCE/prepare_ab_eval.py` (blinding; skill `ab-blind-eval`).
- **Rounds:** `manifests/evaluation_verbatim_hijaz/` (round 1),
  `manifests/evaluation_v2_abc_to_qfinal/` (round 2); audio packages under GCS `listening/`.
  Guide ABC (B2) `abc_v2/<track>/score.abc` + `tokens.json` sidecar on GCS.
- **Training set / repeats:** `dataset/` on GCS;
  `github.com/akbargherbal/suno-workflow` (`workflow.md`, `Quick_Guide.md`).
- **Related:** `docs/LORA_INVENTORY.md`, `docs/PRON_LORA_MERGE.md`,
  `config/akbar_arabic_rock_lora.yml:106`. Live state: `agent_notes/current.md`.
