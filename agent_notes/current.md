# current

_Copy surface, not authority. 2026-09-30 · Colab **T4**, branch `music-cover` @ `30682a2`._

## RUNNING — new batch `batch_12_rock_v2_winning` (launched 12:18:07Z)
`generate.py` pid 184762 · **track 1/24** · run dir `/content/audiocpp_inference/out/batch_12_rock_v2_winning/`.
Manifest `manifests/batch_12_rock_v2_winning.json` (12 songs × 2 = 24, `v2`, winning flat-prompt style).
ETA ≈ **15:30** (~24 × ~8 min). Watch: `tail -f /content/logs/batch_12_rock_v2_winning.log` · `python status.py`.
Stop: `pkill -f 'generate.py manifests/batch_12_rock_v2_winning.json'` · resume: same launch (skips done).

## Old batch `batch_12_rock_v2` — stopped early, 14/24 kept
Deliberate stop 12:11 (not a crash); 14 finished takes kept local + GCS; unfinished track-15 orphans
removed; `README.txt` in the GCS run path records it:
`gs://…/audiocpp_inference/workspace/out/batch_12_rock_v2/`

## Deferred until the render finishes (don't run mid-batch)
- `bash INFERENCE/ss2_venv.sh` — build the phase-2 env (`/content/.venv-sheetsage2`).
- Clean pytest: `python -m pytest tests/ -q -k 'not test_j11_status_inference_section_from_real_run'`.
- graphify install + `graphify update .` (graph 12 commits stale).

## Then — P2 transcribe (FREE CPU) → P3 listen → P4 rescue
`docs/PRON_LORA_RESCUE.md`; key `<name>_<seed>`; `--all`; `CUDA_VISIBLE_DEVICES=""`.
