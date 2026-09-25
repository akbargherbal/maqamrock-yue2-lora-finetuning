---
name: inference-batch-run
description: Plan and run YuE2 GGUF + LoRA generation on the audiocpp inference workspace. Use when asked to generate tracks or songs, run inference, smoke-test generate.py, or work in /content/audiocpp_inference.
---

# Inference batch run (YuE2 GGUF + LoRA)

Read `docs/INFERENCE.md` first — it is the canonical runbook (setup, provenance,
flags, cap math, benchmark). This skill only adds the cross-cutting traps.

## Pre-flight

- `nvidia-smi` — one shared GPU. Never start while ai-toolkit training may be
  running; `generate.py` refuses concurrent runs unless `--allow-concurrent`.
- Never run two generations in parallel — the NAR graph can OOM. `generate.py`
  is sequential by design.

## Entry points

```bash
bash bootstrap/setup.sh --inference > /content/logs/setup.log 2>&1  # fresh VM; wait for "done"
INFERENCE/run_one.sh <Maqam> <seed> [cap|auto]                      # one track
python INFERENCE/generate.py my_songs.json --dry-run                # validate a batch, no GPU
python INFERENCE/generate.py my_songs.json                          # real batch run
python INFERENCE/suno_to_songs.py manifests/workspace_manifest.json -o songs.json
```

`<Maqam>` ∈ {`Ajam`, `Hijaz`, `Kurd`, `Nahawand`}. Cap defaults to `auto`
(95th-percentile `INFERENCE/duration_cap.py` — an upper cap, not a mean); pass an
integer to override. `generate.py` batches accept `--out-dir` to resume a run and
`--limit N` for smoke tests.

## Traps

- **The GGUF is never in GCS** — it comes from HF (`audio-cpp/Yue2-3B-GGUF`) and
  `setup.sh` re-fetches it; `models/` and `bin/` are deliberately not mirrored.
- Repo `INFERENCE/` scripts are canonical; the GCS `scripts/` copy is a legacy
  mirror. The repo copy is what runs.
- The bootstrap stages the sm_75 / T4 build. On an L4 (or another arch) stage the
  prebuilt per-arch object from GCS (e.g.
  `$GCP_BACKUP_BASE/audiocpp_inference/build/sm89-l4/audiocpp_cli`) — a source
  build is not required (`docs/audiocpp_gpu_arch_builds.md`).
- `run_one.sh` needs GNU `time` (`/usr/bin/time`); bootstrap installs it.
- Outputs land per-run under `out/`; `out/latest` points at the newest batch.

## Verify and back up

```bash
python -m pytest tests/test_generate.py tests/test_duration_cap.py tests/test_suno_to_songs.py
python backup_to_gcp.py --inference          # daemon; mirrors out/, prompts/, converter/
```

Planning rule of thumb: ~6.5 min/track on a T4 (~9 tracks/hour).
