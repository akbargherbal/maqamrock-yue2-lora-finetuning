# current

_Updated 2026-09-30 (local). **E2E Sessions 1–3 are complete** (Colab CPU,
GPU-free): `python -m pytest` -> **190 passed, 2 skipped**. Only **Session 4 —
the budgeted T5 GPU gate** remains (host: **Colab free T4**). Nothing in
Sessions 1–3 needs a GPU. Branch `music-cover`; Session 3 changes uncommitted
(see `git status`)._

## 0. Orientation — read these first, in order

1. `AGENTS.md` §2 (mode/environment) and §8 (the never list). Not a §2 runbook
   mode; the authority is the plan below. **GPU work needs the §8 rule**: check
   `nvidia-smi`, never overlap a run.
2. `docs/E2E_TESTING_PLAN.md` — §2 (boundary), §4 (record→replay + §4.4), §5
   (journeys), §6 (the T5 gate S1–S3), §8 (wiring), §9 (sequencing), §12.
3. `SOURCE_OF_TRUTH.md`, row "End-to-end test plan / tiers".

## 1. What landed in Sessions 1–3

- **T2** (`tests/e2e/test_inference_e2e.py`): J1–J4, J6 + provenance guard, on the
  real `generate.main` (only `gpu_info` + `runner` substituted).
- **T3** (`test_train_lifecycle_e2e.py`, `test_monitor_status_e2e.py`,
  `test_backup_restore_e2e.py`): J10 real detached process + SIGINT stop; J11
  `monitor_loss.py`/`status.py` on a spec-built db and a real run; J12 real
  `backup_to_gcp.py` mirror + manifest + byte-identical restore.
- Helpers: `tests/staging.py`, `tests/e2e/replay.py`, `tests/e2e/lossdb.py`,
  `tests/e2e/fake_run.py`, `tests/e2e/fake_gsutil.py`.
- Fixtures (Tier A): `recorded_batch.json`, `loss_log.spec.json`, `manifest.json`,
  `README.md`, `fetch.sh`.
- **Production fix**: `train_ctl.py::cmd_stop` had a log-write/process-exit race
  (false "still running"); it now waits a 5 s grace after seeing `Job stopped`
  and reports true elapsed. Surfaced by J10 under load. `PAUSE_RESUME.md` still
  holds.

## 2. Decisions (resolved 2026-09-30, plan §12)

1. **Gate host: Colab free T4.** Kaggle / GH Actions GPU are fallbacks.
2. **Fixtures: Tier A in git, Tier B in GCS** (`tests/fixtures/fetch.sh`, gitignored).
3. **T3 scope: fake `run.py` only**; the real 10-step smoke stays at the T5 gate.

## 3. Next — Session 4 (plan §6/§9), the only GPU session

Attach a **Colab T4** runtime, then (this is the gate AND the recording run):

| Step | Command shape | Proves |
|---|---|---|
| S1 | `<bin>/audiocpp_cli --version` | binary loads, CUDA device present |
| S2 | `bash INFERENCE/run_one.sh <Maqam> 1 auto` with `OUT_DIR=/content/smoke` | one real WAV + `_time.txt`/`.log`/`_gpu.csv` -> the J1–J3 Tier B fixtures |
| S3 | `python run.py config/pron_lora_ar_only_smoke.yml -l /content/logs/train_smoke.log` | 10/10 steps, finite loss, checkpoint written |

Then copy the smoke artifacts into `tests/fixtures/` (Tier A/B), set `tier_b` in
`manifest.json`, and **switch back to the CPU runtime**. Optional S2b: a missing
LoRA for a real `exit=1` log. Before starting: confirm the backup sidecars are up
(see below) and `nvidia-smi` is idle; `train_ctl.py`/`generate.py` must not be
running.

## 4. Reproduce / verify (CPU runtime)

```bash
cd /content/maqamrock-yue2-lora-finetuning
python -m pytest -q                     # 190 passed, 2 skipped
python -m pytest tests/e2e -q           # J1–J4, J6, J10–J12
python -m pytest -m gpu --collect-only  # T5 checks, deferred to the gate
```

## 5. Guardrails

- **CPU only until Session 4.** `pytest -m "not gpu"` is the default and must stay
  green; `pytest -m live` is never automatic.
- Tier B binaries stay out of git (`tests/fixtures/**/*.wav|.safetensors|.db`,
  `audiocpp_cli`, `out/`).
- Do not modify run configs or `/content` datasets (AGENTS.md §8).
- `agent_notes/current.md` is a handoff surface, **not authority** — re-derive
  state with `python status.py`.

## 6. Pointers

- Plan: `docs/E2E_TESTING_PLAN.md`. Passes: `RECONCILIATION_LOG.md` (2026-09-30).
- Reconciler: `skills/docs-reconciler/SKILL.md`; suppressions
  `skills/docs-reconciler/references/unverifiable.txt`.
- Note (audit, 2026-09-30): `status.py` reports `backup_to_gcp.py` and
  `gpu_logger.py` sidecars **DOWN** (no run active; vm-continuity healthy). Start
  them before the Session 4 gate so the smoke artifacts are mirrored.
