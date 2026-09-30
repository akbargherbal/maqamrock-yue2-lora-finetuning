# current

_Copy surface, not authority. 2026-09-30 · Colab **T4**, branch `music-cover`._

## GIT — pushed ✓
`music-cover` is up to date with `origin` (tip `017a1d4`). Push flow if needed again: auth via
`bash bootstrap/github_auth.sh` (or an existing `gh` login), then `git push origin music-cover`.

## RUNNING — pass-1 v2 (`batch_12_rock_v2`)
Launched 10:13:12Z · track 1 **done** (`exit=0`, 48 kHz stereo, 242.0 s) · track 2 in progress.
Run dir `/content/audiocpp_inference/out/batch_12_rock_v2/`. ETA ≈ **12:50**.
Watch: `tail -f /content/logs/batch_12_rock_v2.log` · `python status.py`.
Stop: `pkill -f 'generate.py manifests/batch_12_rock_v2.json'` · resume: same launch (skips done).

## DONE while waiting (all inert, non-GPU)
- **P1 verified:** take 1 WAV `48 kHz / 2ch / 242.0 s`, sidecar `cot=off`, `_time.txt` `Exit status: 0`;
  backup daemon up and the run dir is on GCS (`workspace/out/batch_12_rock_v2/`, `5/5 folders synced`).
- **Runbook reconciled** (`docs/PRON_LORA_RESCUE.md`): Phase 0 now stages **every** manifest `loras`
  alias (v2 + qfinal_a0.3 + qfinal_a0.5; `_explicit` aliases into a0.5); Phase 2 now carries the env build.
- **New file `INFERENCE/ss2_venv.sh`** — build-only, idempotent; creates `/content/.venv-sheetsage2`
  (uv, py3.11, torch 2.8.0, transformers 4.45.2) at the path the runbook/transcriber name.
- Gotchas: a0.5 preflight requirement + the host-wide `_pgrep("generate.py")` test flake.
  Reconciler: 1511 checkable, **0 flagged**. Committed `2a13de1` (local only — push needs your PAT).

## DEFERRED until the render finishes (won't touch while it runs)
- **Build the env:** `bash INFERENCE/ss2_venv.sh` (pulls torch ~GB; do after the batch, or on the
  free CPU runtime that will transcribe).
- **Clean test run:** `python -m pytest tests/ -q -k 'not test_j11_status_inference_section_from_real_run'`
  (the full suite spawns a real `generate.py` that hashes the 3.9 GB GGUF — don't run it mid-batch).
- **graphify:** not installed (`graphify install --platform opencode` then `graphify update .`);
  graph is 7 commits stale. Low priority.

## NEXT — P2 transcribe (FREE CPU) → P3 listen → P4 rescue
```bash
bash INFERENCE/ss2_venv.sh                       # once
CUDA_VISIBLE_DEVICES="" /content/.venv-sheetsage2/bin/python INFERENCE/sheetsage2_transcribe.py \
  --input-dir /content/audiocpp_inference/out/batch_12_rock_v2 \
  --out-dir   /content/audiocpp_inference/out/abc_v2_batch12 --all
```
Key `<name>_<seed>`; best on a free CPU runtime with the WAVs via GCS. Then P3 listen → P4 rescue
(`rescue_abc_batch.sh --plan → --smoke → --songs-file`, `docs/PRON_LORA_RESCUE.md`).
