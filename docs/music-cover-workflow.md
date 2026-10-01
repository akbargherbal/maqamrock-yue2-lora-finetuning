# Music-cover workflow — design & end-to-end reference

How this project turns a **v2 maqamrock take** into a well-pronounced cover by conditioning
`qfinal_a0.3` on a **symbolic melody score (ABC)** of that take.

This is the **design reference** — what the workflow is and why. It is deliberately not the
runbook: exact commands, flags, and the safety gates live in
[`PRON_LORA_RESCUE.md`](PRON_LORA_RESCUE.md); the measured evidence and the cost model live in
[`music-cover-feasibility.md`](music-cover-feasibility.md) (§2.1, §4.2, §10). Where a number or
a claim appears here, it traces to one of those two.

_Last updated 2026-09-30._

## 1. The problem it solves

Two LoRAs in the same family, with opposite strengths:

| adapter | arrangement | pronunciation |
|---|---|---|
| **v2** (style only) | good arabmaqamrock band | struggles |
| **`qfinal_a0.3`** | drifts to sparse, percussion-led nasheed | good |

`qfinal_a0.3 = v2_style_Δ + 0.3·pron_Δ` merged into the **AR** branch, with the **NAR branch
copied verbatim from v2** (`docs/PRON_LORA_MERGE.md`). The drift is an **AR-plan** effect, so
lowering α shrinks it but never separates pronunciation from arrangement. The pronunciation
fix is **AR-only** (`config/pron_lora_ar_only.yml:38` ignores `transformer.nar`) — which is
exactly the stream a guide competes with.

**The idea:** give `qfinal_a0.3` the *plan* that v2 would have made, as a symbolic score. The
score carries arrangement; qfinal supplies the clean singing. Score-conditioned covers carry
song identity: SHS100K zero-shot **CLEWS Hit@1 71.3%** with a score vs **0.3%** without.

## 2. The three actors

| actor | role | artifact |
|---|---|---|
| **v2** | makes the maqamrock arrangement (pass-1) | take WAV |
| **SheetSage2** | turns that WAV into a melody **ABC** (the guide) | `score.abc` |
| **`qfinal_a0.3`** | re-renders the take, guided by the ABC, singing cleanly | rescue WAV |

YuE2 has no audio-to-audio input: the only "cover" handle is the symbolic score + lyrics
(`m-a-p/YuE2-3B`, Cover). Our runtime exposes `cot=melody|full` and `abc_file=`.

## 3. Two ways to get the guide

- **B1 — in-stack, exact (validated, n=1).** Run **v2** `cot=full --out-dir`; it writes its own
  `score.abc` (melody **+ chords**). Render qfinal `cot=full` + `abc_file=<that>`. No
  transcription loss — but it costs an extra v2 render, and it is a *different* v2 take than
  the liked `cot=off` one.
- **B2 — faithful, lossy (the designed default; guide unrun).** Transcribe the **liked
  `cot=off` v2 take** with **SheetSage2** (`melody_only=True`) → `melody.abc`; render qfinal
  `cot=melody` + `abc_file=`. Melody-only, but it reuses the exact take you chose and is
  **free to transcribe on CPU** (§6). **B2's guide quality has not been listened to yet** —
  a 1-track smoke gates it.

## 4. The workflow (end to end)

Keyed throughout by one string: **`<name>_<seed>`** (the pass-1 WAV stem).

| phase | box | in → out | notes |
|---|---|---|---|
| **0. Setup** | GPU VM | — → staged env | binary + models + **both** LoRAs; branch `music-cover`; backup sidecar up |
| **1. Pass-1** | GPU | manifest → 2 v2 takes/song | `cot=off` (trained regime); ~6.5 min/track |
| **2. Transcribe** | **free CPU** | takes → `score.abc` per take | SheetSage2 `melody_only=True`; ~4–6 min/track; 0 GPU units |
| **3. Listen** | human | takes → chosen take/song + `M` (fail list) | two axes: maqamrock-OK? pronunciation-OK? |
| **4. Rescue** | GPU | `M` takes + their ABC → rescue WAVs | `qfinal_a0.3` + `abc_file`; `cot` default `melody` (a run may use `full`); `seed` default = the take's own (`"random"` = fresh per take); cap/style/lyrics from pass-1 |
| **5. Re-listen** | human | pass-1 vs rescue, same seed | only the guide changed |

The **only difference at phase 4** is the guide: seed, cap, style, and lyrics are read from the
pass-1 `batch_manifest.json` and the flattened `prompts/`, never retyped.

### The spine (provenance)

`<name>_<seed>` is the pass-1 WAV stem, the ABC folder name, and the rescue WAV stem. "Which
ABC belongs to which take" is therefore structural, not hand-carried:

```
out/<run>/<name>_<seed>.wav          pass-1 (generate.py)
out/<abc>/<name>_<seed>/score.abc    transcription (sheetsage2_transcribe.py)
out/<rescue>/<name>_<seed>.wav       rescue (rescue_abc_batch.sh, separate dir)
```

## 5. Gates that keep it truthful

The workflow is safe because each step proves its inputs before spending GPU time. Full table
and rationale: `PRON_LORA_RESCUE.md`. In brief:

- **G0** dry-run + staged adapters + backup up, before phase 1.
- **G1** always the same absolute `--out-dir` (resume; never the timestamped default).
- **G2** fresh ABC dir (or `--force`) — `sheetsage2_transcribe.py` silently skips an existing
  `score.abc`, which can staple a stale ABC to a fresh take.
- **G3** `rescue_abc_batch.sh --plan` records sha256 of every WAV + its ABC and **aborts** on
  any missing piece; `--verify` re-checks later.
- **G4** the rescue driver **refuses** an `--out-dir` equal to the pass-1 dir — the rescue
  WAV has the *same filename*, so a slipped path would clobber the liked take.
- **G5** `--smoke` renders one track and stops — the B2 quality gate.
- **G6** conditioning values come from the pass-1 manifest, not the keyboard.

The rescue driver calls the binary **directly** with `cot=<cfg>` (`melody` default, `full` allowed) +
`abc_file`; it does not use `run_one.sh`, whose hardcoded `cot=off` and later override is unverified.

## 6. Economics

Currency is Colab compute units: a GPU runtime is billed (L4 `1.54 u/h`, A100 `6.7 u/h` —
`docs/GPU_L4_VS_A100.md`), a CPU runtime is not. Per-track GPU render ≈ **6.5 min on a T4**;
per-track CPU transcription ≈ **4–6 min**, ~4.3 GB RAM (`music-cover-feasibility.md` §2.1).

Two consequences of B2 being CPU-viable:

- **B2 is the GPU-cheap guide.** B1 burns a GPU render to export v2's plan; B2 transcribes the
  already-rendered take on CPU, so pass-1 stays `cot=off` and the guide is free.
- **Transcription must not run on a paid GPU VM.** Stop the GPU after pass-1; transcribe on a
  free CPU runtime (WAVs/ABCs over GCS). On the GPU box, force CPU with `CUDA_VISIBLE_DEVICES=""`.

Per chosen take/song (12-song batch) with M pronunciation-failures, GPU minutes — pass-1 itself
renders `repeat: 2` takes/song, so double the first row (24 takes ≈ 156 min):

| plan | renders | GPU-min |
|---|--:|--:|
| pass-1 only (accept drift) | 12 | 78 |
| **selective rescue on B2 (this workflow)** | 12 + M | **78 + 6.5·M** |
| selective rescue on B1 (+ plan export) | 12 + 2M | 78 + 13·M |
| guide every track (v2→ABC→qfinal) | 24 | 156 |

B2 saves **M** renders vs B1; selective rescue saves **N − M** vs guiding everything. The
selective saving shrinks as M grows.

## 7. What is proven, what is assumed

- **Proven:** B1 kept v2's arrangement *and* improved pronunciation on one blinded clip
  (`music-cover-feasibility.md` §7, n=1). ABC conditioning does not revert pronunciation.
- **Measured:** SheetSage2 audio→ABC is CPU-viable (~4.3 GB, ≤10-min track) — §2.1.
- **Assumed (the open risk):** that **B2's melody-only guide steers arrangement** as well as
  B1's full plan. Unrun — hence G5. If it fails, fall back to B1 (`INFERENCE/v2_abc_to_qfinal.sh`).
- **Not applicable (blocked):** `semantic_prefix` steering — staged binary < v0.8.2.

Also keep: adapters are `cot=off`, so all ABC conditioning is **off-distribution**; a guide and
its prompt must share the **maqam**; every round so far is n=1.

## 8. Where things live

- **Inputs:** pass-1 manifests `manifests/batch_12_rock_v2.json` (v2) and
  `manifests/batch_12_rock_v2_winning.json` (v2, "winning flat-prompt" style), each derived from
  `manifests/batch_12_rock.json` (source). Adapters under `/content/converter/out/`.
- **Drivers:** `INFERENCE/generate.py`, `INFERENCE/sheetsage2_transcribe.py`,
  `INFERENCE/ss2_venv.sh` (phase-2 env), `INFERENCE/rescue_abc_batch.sh`,
  `INFERENCE/v2_abc_to_qfinal.sh` (B1).
- **Outputs:** `out/<run>/` (pass-1 takes + sidecars), `out/<abc>/` (ABCs),
  `out/<rescue>/` (rescue takes + `_rescue_index.json`). Audio packages on GCS `listening/`.
- **Analysis:** `docs/music-cover-feasibility.md`; merge convention `docs/PRON_LORA_MERGE.md`.

## 9. Failure modes to expect

The "silently wrong" class, each with its guard (see §5): losing `/content` with no backup
(G0); a re-run scattering takes across dirs (G1); a stale ABC stapled to a fresh take (G2);
a rescue overwriting the liked take (G4); a "rescue" that silently ran `cot=off` (driver
bypasses `run_one.sh`); conditioning drift from hand-typed values (G6); mis-copied Arabic
stems (the spine).

## 10. References

- Runbook (commands, gates): `docs/PRON_LORA_RESCUE.md`.
- Evidence + cost model: `docs/music-cover-feasibility.md` §2.1, §4.2, §6, §7, §10.
- Unit rates / GPU choice: `docs/GPU_L4_VS_A100.md`.
- Batch generation + T4 timing: `docs/INFERENCE.md`.
- Merge convention: `docs/PRON_LORA_MERGE.md`; config `config/akbar_arabic_rock_lora.yml:106`
  (`cot: "off"`).
