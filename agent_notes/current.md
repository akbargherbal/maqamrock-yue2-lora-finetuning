# current

_Copy surface, not authority. 2026-09-30 · **T4 Colab (GPU)**, branch `music-cover`. Run on the T4, not the CPU box._

## State
- **Pass-1 `batch_12_rock_v2`: 23/24 rendered** (`generate.py`, out-dir `/content/audiocpp_inference/out/batch_12_rock_v2`;
  manifest `manifests/batch_12_rock_v2.json` = 12 songs × 2 takes). One take may still be finishing — wait for the
  GPU to free before the rescue.
- **ABC: 14/24 transcribed** (songs 01–07) at `…/out/abc_v2_batch12` (GCS-mirrored). Songs 08–12 still need
  transcription (phase 2 top-up below — FREE CPU, GPU untouched).
- `--songs-json` (self-contained run config) just landed; `git pull` to get it + this file.

## Next step — P2 top-up ABC → P4 rescue (qfinal_a0.3 + `cot=melody` + `abc_file`)

### 0. Preflight
- **GPU free of GPU work** — the pass-1 batch must be done (`pgrep -af 'generate.py'`; rescue itself refuses if
  `run.py` training is active). One shared GPU: no overlap.
- Repo + ABCs onto the box:
  ```bash
  GCS=gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning
  B=/content/audiocpp_inference/out
  git pull                                             # gets --songs-json + this file
  gsutil -m cp -r "$GCS/audiocpp_inference/workspace/out/abc_v2_batch12" "$B/"   # the 14 already done
  ```
- Stage binary+models+v2, then the rescue adapters (`setup.sh` stages v2 only):
  ```bash
  bash bootstrap/setup.sh --inference
  for a in qfinal_a0.3 qfinal_a0.5; do gsutil -m cp -r "$GCS/loras/audio_cpp/pron/$a" /content/converter/out/; done
  ```
- Backup sidecar (free): `pgrep -af backup_to_gcp.py` — if down, start it (`bootstrap/setup.sh` starts it).

### 1. Phase 2 — transcribe the newly finished takes (FREE CPU; `CUDA_VISIBLE_DEVICES=""`)
```bash
bash INFERENCE/ss2_venv.sh     # once per VM (builds /content/.venv-sheetsage2)
CUDA_VISIBLE_DEVICES="" /content/.venv-sheetsage2/bin/python INFERENCE/sheetsage2_transcribe.py \
  --input-dir "$B/batch_12_rock_v2" --out-dir "$B/abc_v2_batch12" --all
```
Resumable (skips existing `score.abc`); `--all` is required (the default silently drops `_2_`/`_3_` stems).
Run detached with a log if you like. Stop: `pkill -f sheetsage2_transcribe.py`. Needs **all 24** transcribed before
a full rescue — the shield is the gate in step 3.

### 2. Selection config — one file drives the rescue
```bash
cp INFERENCE/rescue_selection.example.json /content/m_selection.json
# edit "songs": — each entry a song NAME (all takes) or a STEM <name>_<seed> (one take),
# or { "stem": "...", "note": "..." }. Dirs/knobs are already in the file; a CLI flag wins.
```
Omit `songs` to rescue every transcribed track.

### 3. Plan (no GPU) → smoke → full
```bash
bash INFERENCE/rescue_abc_batch.sh --songs-json /content/m_selection.json --plan   # validates, writes _rescue_index.json
bash INFERENCE/rescue_abc_batch.sh --songs-json /content/m_selection.json --smoke  # B2 quality gate: LISTEN before the batch
bash INFERENCE/rescue_abc_batch.sh --songs-json /content/m_selection.json          # full
```
Batch detached: `setsid nohup bash INFERENCE/rescue_abc_batch.sh --songs-json /content/m_selection.json > /content/logs/rescue_v2abc.log 2>&1 & disown`
Stop: `pkill -f rescue_abc_batch.sh` · resume: same command (skips succeeded). `--max` cap: `--limit N`.

### 4. After
- Per track: `$B/rescue_v2abc_batch12/<stem>.wav` + `<stem>_rescue.json` (binds the WAV to the ABC sha256 + seed).
- P5: blind-package pass-1 vs rescue with `INFERENCE/prepare_ab_eval.py` (skill `ab-blind-eval`).

## Caveats
- **B2 is unproven (§8)** — `--smoke` one track and listen before committing the batch; fallback is B1 (`INFERENCE/v2_abc_to_qfinal.sh`).
- `--plan` **aborts** if any selected track lacks its pass-1 WAV or ABC — that is the gate; only select tracks that have both.
- Rescue writes a **separate** `out_dir`; it refuses to write into the pass-1 dir.
Full runbook: `docs/PRON_LORA_RESCUE.md`.
