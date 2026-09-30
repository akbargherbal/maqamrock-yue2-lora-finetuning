# Runbook — v2 pass-1 → SheetSage2 ABC → qfinal rescue (B2)

How to test the cover/rescue workflow on a batch: generate with **v2** (`cot=off`), transcribe
each take to a melody **ABC on free CPU**, listen, and re-render only the tracks that fail
pronunciation with `qfinal_a0.3` conditioned on that take's own ABC. Why this is cheap and
where the numbers come from: `music-cover-feasibility.md` §2.1 (CPU feasibility) and §10
(workflow + unit-cost split).

This is the **B2** route (§4.2): the guide is SheetSage2's melody-only transcription of the
liked v2 take — **B2's guide quality is still unrun (§8)**, so a 1-track smoke gates the batch.

## The alignment spine (read this first)

The whole workflow is keyed by one string: **`<name>_<seed>`** — the pass-1 WAV stem. It is
also the ABC folder name and the rescue WAV stem. "Which ABC belongs to which" is therefore
structural, never hand-carried:

| stage | artifact | produced by |
|---|---|---|
| pass-1 | `out/<run>/<name>_<seed>.wav` + `.json` sidecar | `generate.py` (`f"{name}_{seed}.wav"`) |
| transcribe | `out/abc_v2/<name>_<seed>/score.abc` | `sheetsage2_transcribe.py` (folder = WAV stem) |
| rescue | `out/<rescue>/<name>_<seed>.wav` | `rescue_abc_batch.sh` (same stem, **separate dir**) |

## Gates (what makes it truthful and cheap)

| # | Gate | Phase | Prevents |
|---|---|---|---|
| G0 | `generate.py --dry-run`; qfinal adapters staged; backup sidecar up | 0 | stalls, missing adapters, ephemeral-VM loss |
| G1 | always the same absolute `--out-dir` (resume, never the timestamped default) | 1 | scatted/duplicated take sets |
| G2 | fresh `--abc-dir` (or re-transcribe with `--force`); transcribe only the pass-1 dir | 2 | stale `score.abc` stapled to a fresh take |
| G3 | `rescue_abc_batch.sh --plan` builds `_rescue_index.json` (sha256 of wav + abc) and **aborts** on any missing piece | 2→4 | running a rescue with the wrong/absent guide |
| G4 | rescue driver **refuses** `--out-dir == pass-1 dir` | 4 | clobbering the liked take (identical filename) |
| G5 | `--smoke` renders 1 track, then stop and listen | 4 | an M-batch built on an unproven guide |
| G6 | seed/cap/style/lyrics read from the pass-1 `batch_manifest.json` + `prompts/` | 4 | conditioning drift → unattributable result |

## Phase 0 — setup (GPU VM)

- Stage the binary + models + **both** LoRAs. `bootstrap/setup.sh --inference` stages the v2
  pair only; pull qfinal explicitly:
  `gsutil -m cp -r gs://<base>/OSTRIS_Arabic_Suno_Finetuning/loras/audio_cpp/pron/qfinal_a0.3 /content/converter/out/`
- Start the backup sidecar and confirm continuity **before** the batch (`AGENTS.md` §10).
- Clone the right branch: `git clone --branch music-cover <url>` (a default clone lands on
  `main` and is missing these files).
- Pass-1 manifest: **`manifests/batch_12_rock_v2.json`** (generated from `batch_12_rock.json`
  with every `lora` set to `v2`; the original is kept). Validate with
  `python INFERENCE/generate.py manifests/batch_12_rock_v2.json --dry-run`.

## Phase 1 — pass-1 v2 batch (GPU)

`terminal: detached — survives Ctrl+C / closing the tab; log: /content/logs/batch_12_rock_v2.log; stop: pkill -f 'generate.py manifests/batch_12_rock_v2.json'; resume: same command (skips succeeded).`

```bash
python INFERENCE/generate.py manifests/batch_12_rock_v2.json \
  --out-dir /content/audiocpp_inference/out/batch_12_rock_v2
```

Wrap it: `setsid nohup <cmd> > /content/logs/batch_12_rock_v2.log 2>&1 & disown`.
~12 × ~6.5 min ≈ **~78 min** on a T4. The `--out-dir` is deliberate (G1); the manifest's
explicit per-song seeds mean a re-run reproduces the same tracks.

## Phase 2 — transcribe all (free CPU)

`terminal: detached; log: out/abc_v2_batch12/_driver.log; stop: pkill -f sheetsage2_transcribe.py; resume: same command (skips existing score.abc).`

```bash
CUDA_VISIBLE_DEVICES="" /content/.venv-sheetsage2/bin/python INFERENCE/sheetsage2_transcribe.py \
  --input-dir /content/audiocpp_inference/out/batch_12_rock_v2 \
  --out-dir   /content/audiocpp_inference/out/abc_v2_batch12
```

`CUDA_VISIBLE_DEVICES=""` forces CPU even on the GPU box (the script auto-selects CUDA when
present). Best run on a **free CPU runtime** with the WAVs via GCS. ~12 × ~4.5 min ≈ **~54 min**.
Never point `--input-dir` at a dir that also holds rescue WAVs (G2).

## Phase 3 — listen / classify

Play the 12 pass-1 takes. Two axes each: **maqamrock-OK?** and **pronunciation-OK?**. The
rescue set `M` = the tracks that are maqamrock-OK but pronunciation-bad. List their whole
`name` strings (no hand-typing needed — see Phase 4's `--songs-file`).

## Phase 4 — rescue `M` (GPU)

`terminal: foreground for --plan/--smoke (seconds); detached for the batch; stop: pkill -f rescue_abc_batch.sh; resume: same command (skips succeeded).`

1. **Build + check the index (no GPU):**
   ```bash
   bash INFERENCE/rescue_abc_batch.sh \
     --pass1-dir /content/audiocpp_inference/out/batch_12_rock_v2 \
     --abc-dir   /content/audiocpp_inference/out/abc_v2_batch12 \
     --out-dir   /content/audiocpp_inference/out/rescue_v2abc_batch12 --plan
   ```
   This writes `_rescue_index.json` (sha256 of every pass-1 WAV and its ABC) and **stops** if
   any requested track is missing its WAV/ABC. Re-check later with the same command `--verify`.

2. **Smoke 1 track** (the B2 quality gate):
   ```bash
   bash INFERENCE/rescue_abc_batch.sh --pass1-dir ... --abc-dir ... --out-dir ... --smoke
   ```
   Listen: does the melody-only ABC steer the arrangement while qfinal keeps the pronunciation?
   If not, stop — B2 is unproven and the fallback is B1 (`INFERENCE/v2_abc_to_qfinal.sh`).

3. **Full rescue** (pass `--songs-file` of the M names):
   ```bash
   bash INFERENCE/rescue_abc_batch.sh --pass1-dir ... --abc-dir ... --out-dir ... \
     --songs-file /content/fails.txt
   ```

The driver calls the binary **directly** with `cot=melody abc_file=<abc>` (it does **not** use
`run_one.sh`, whose hardcoded `cot=off` + later override is unverified) and writes, per track,
`<stem>.wav`, `<stem>.log`, `<stem>_time.txt`, `<stem>_rescue.json` (binds the WAV to the exact
> abc sha256 + seed + cap), and `_rescue_status.log`.

## Phase 5 — re-listen

Compare `rescue_v2abc_batch12/<stem>.wav` against `batch_12_rock_v2/<stem>.wav` — same
`name`, same `seed`, the only difference is the guide. Package blinded with
`INFERENCE/prepare_ab_eval.py` (skill `ab-blind-eval`).

## Risk → guard, for the record

- **Ephemeral `/content` + no backup** → G0 (backup sidecar before the batch).
- **Re-run without `--out-dir`** → G1.
- **Stale `score.abc` skip** (`sheetsage2_transcribe.py` skips an existing file) → G2.
- **Rescue overwrites the liked take** (same `<name>_<seed>.wav`) → G4.
- **`cot` override silently a no-op** (`run_one.sh:85`) → driver bypasses `run_one.sh`.
- **Conditioning drift in hand-typed rescue** → G6 (values from the manifest).
- **Arabic stems mis-copied by hand** → the spine + `--songs-file`.
- **Transcription steals the GPU** → `CUDA_VISIBLE_DEVICES=""`.
- **Fresh-VM missing qfinal / wrong branch** → Phase 0.

## Sources

- Drivers: `INFERENCE/generate.py`, `INFERENCE/sheetsage2_transcribe.py`,
  `INFERENCE/rescue_abc_batch.sh` (this file's subject; `--help`).
- Manifests: `manifests/batch_12_rock_v2.json` (pass-1), `manifests/batch_12_rock.json` (source).
- Analysis: `docs/music-cover-feasibility.md` §2.1, §4.2, §10; `docs/GPU_L4_VS_A100.md` (unit
  rates); `docs/INFERENCE.md` (batch generation, T4 timing).
