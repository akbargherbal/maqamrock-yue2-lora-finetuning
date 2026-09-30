# current

_Updated 2026-09-30 (local). **E2E Sessions 1–2 are complete** (Colab CPU,
GPU-free): `python -m pytest` -> **185 passed, 2 skipped**. Next: **Session 3 —
T3 process/lifecycle e2e J10–J12** (`fake_run.py`, fake `gsutil`, monitor/status
from a spec-built db). No GPU work until Session 4 (the T5 gate; host decided:
**Colab free T4**). Branch `music-cover`; Session 2 changes uncommitted (see
`git status`)._

## 0. Orientation — read these first, in order

1. `AGENTS.md` §2 (mode/environment) and §8 (the never list). This is **not** a
   §2 runbook mode; the authority is the plan doc below.
2. `docs/E2E_TESTING_PLAN.md` — §2 (device boundary), §4 (record→replay + §4.4
   provenance), §5 (journey matrix), §8 (wiring), §9 (sequencing = Session 3),
   §11 (risks), §12 (resolved decisions).
3. `SOURCE_OF_TRUTH.md`, row "End-to-end test plan / tiers".

## 1. What landed in Sessions 1–2

- `tests/e2e/replay.py` — `write_track_outputs` (the single `run_one.sh` file-set
  writer), `make_replay_runner`, `make_passthrough_runner`.
- `tests/e2e/conftest.py` — `fake_gpu`, `staged_inference`, `run_generate`
  (re-invocable; drives the real `generate.main` with only `gpu_info` +
  `training_active` + the `runner` substituted).
- `tests/e2e/test_inference_e2e.py` — **J1** happy path, **J2** re-run/`--force`,
  **J3** failure→retry, **J4** LoRA registry routing, **J6** suno→generate round
  trip, **provenance guard** (`checkpoint_step` + manifest integrity; the
  `audio_cpp_commit` half is gated on Tier B).
- `tests/staging.py` — `stage_inference_tree`, shared by the unit tests
  (`tests/test_generate.py::_stub_assets`) and the e2e `staged_inference` fixture.
- `tests/fixtures/` — Tier A `recorded_batch.json` (incl. a synthetic `Saba`
  `exit=1` track for J3), `manifest.json` (refreshed sha), `README.md`, `fetch.sh`.
- `pytest.ini` — `gpu` / `fixtures_heavy` / `live` markers + default filter.

## 2. Decisions (resolved 2026-09-30, plan §12)

1. **Gate host: Colab free T4.** Kaggle / GH Actions GPU are fallbacks.
2. **Fixtures: Tier A in git, Tier B in GCS** (`tests/fixtures/fetch.sh`, gitignored).
3. **T3 scope: fake `run.py` only**; the real 10-step smoke stays at the T5 gate.

## 3. Next — Session 3 (plan §9)

- **J10** training lifecycle with `tests/e2e/fake_run.py`: a real process that
  writes a `loss_log.db` and answers SIGINT; prove `train_ctl.py` start →
  `status` (detached, PID file) → `stop` (SIGINT reaches the child, "Job stopped").
- **J11** monitor + status from a spec-built db: `monitor_loss.py` step/rate and
  `status.py` drift/staleness, built from `tests/fixtures/loss_log.spec.json`.
- **J12** backup mirror + restore diff with a fake `gsutil`/`gcloud` shim on
  `PATH`: targets, manifest, byte-identical restore.
- Keep the default suite GPU-free and green; `pytest -m live` is never automatic.

## 4. Reproduce / verify (CPU runtime)

```bash
cd /content/maqamrock-yue2-lora-finetuning
python -m pytest -q                     # 185 passed, 2 skipped
python -m pytest tests/e2e -q           # J1–J4, J6
python -m pytest -m gpu --collect-only  # T5 checks, deferred to the gate
```

## 5. Guardrails

- **CPU only.** No `audiocpp_cli`, no real `run.py`; `preflight`'s GPU refusal is
  itself a test (plan §7). T3 uses a real *process* for `fake_run.py`, still no GPU.
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
  `gpu_logger.py` sidecars DOWN (no run active; vm-continuity healthy). Not this
  session's work — re-check before the Session 4 gate.
