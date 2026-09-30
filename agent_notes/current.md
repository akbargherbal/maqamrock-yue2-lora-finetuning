# current

_Copy surface, not authority. 2026-09-30 · Colab **T4**, branch `music-cover` @ `83cb14d`._

## RUNNING — pass-1 v2 (`batch_12_rock_v2`)
Launched 10:13:12Z · `generate.py` pid 18475, `audiocpp_cli` on **track 1/24**.
Run dir `/content/audiocpp_inference/out/batch_12_rock_v2/` (`batch_manifest.json` = 24 tracks + seeds).
ETA ≈ **12:49**. Watch: `tail -f /content/logs/batch_12_rock_v2.log` · `python status.py`.
Stop: `pkill -f 'generate.py manifests/batch_12_rock_v2.json'` · resume: same launch (skips done).

## WHILE WAITING — housekeeping plan (all non-GPU)

**P1 · protect the 156 GPU-min**
- [x] backup daemon up (`--inference`, 5/5 folders); confirm the run dir reaches GCS after the next pass
- [ ] **take-1 sanity check** when it lands (~10:19): WAV 48 kHz/stereo, sane duration; sidecar `cot=off`; `_time.txt` `Exit status: 0`

**P2 · make phase 2 turnkey** (the one real blocker)
- [ ] **`/content/.venv-sheetsage2` has no builder.** The runbook + `sheetsage2_transcribe.py` name it,
      but only `INFERENCE/ss2_probe.sh` builds a venv — and it makes `/content/.ss2` and then runs a probe
      (its header: "Scratch artifact, not authority"). Fix: a tiny build-only, idempotent
      `INFERENCE/ss2_venv.sh` at the runbook's path, pins copied from `ss2_probe.sh:30-36`
      (torch 2.8.0 / torchaudio 2.8.0, transformers 4.45.2, hf-hub 0.36.0, safetensors 0.5.3,
      numpy 1.24.3, scipy 1.13.1, mir_eval 0.8.2, pretty_midi 0.2.10, mido 1.3.3, setuptools 78.1.1) + ffmpeg.
- [ ] **decide phase-2 venue:** free CPU runtime (recommended — WAVs come from GCS, GPU stays free) vs.
      here with `CUDA_VISIBLE_DEVICES=""`. This decides *where* the venv gets built.
- [ ] pre-stage `/content/fails.txt` (stem-per-line format) + re-read `rescue_abc_batch.sh --help`

**P3 · repo hygiene / truth**
- [ ] reconcile `docs/PRON_LORA_RESCUE.md`: Phase 0 must stage **qfinal_a0.5** (done as a gotcha, not yet in the runbook);
      Phase 2 must carry the venv build
- [ ] record the test flake: `tests/e2e/test_monitor_status_e2e.py::test_j11_status_inference_section_from_real_run`
      **fails while any `generate.py` runs** — `status.py:158` `_pgrep("generate.py")` is host-wide, so a live
      render makes status say RUNNING. Not a regression.
- [ ] commit the pending doc changes (`COMMAND_HANDOVER_GOTCHAS.md`, runbook, this file) so they survive VM loss
- [ ] graph refresh: `graphify` not on PATH (7 commits stale) — investigate; low priority

## AFTER — P2 transcribe (FREE CPU) → P3 listen → P4 rescue
`docs/PRON_LORA_RESCUE.md`. Key `<name>_<seed>`; `--all`; `CUDA_VISIBLE_DEVICES=""`.
