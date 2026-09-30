# current

_Updated 2026-09-30 (local). **Session 1 of `docs/E2E_TESTING_PLAN.md` is
complete** (Colab CPU, GPU-free): 181 passed, 1 skipped. Next session: **Session 2 —
T2 inference journeys J1–J4, J6 + the provenance guard test.** No GPU work until
the Session 4 gate (now decided: **Colab free T4**). Branch `music-cover`
(uncommitted Session 1 changes in the working tree — see `git status`)._

## 0. Orientation — read these first, in order

1. `AGENTS.md` §2 (identify mode/environment) and §8 (the never list). This is **not** a
   §2 runbook mode; the authority is the plan doc below.
2. `docs/E2E_TESTING_PLAN.md` — §4 (record→replay), §5 (journey matrix), §8 (test wiring),
   §9 (sequencing = what Session 2 is), §12 (decisions, now resolved).
3. `SOURCE_OF_TRUTH.md`, row "End-to-end test plan / tiers".

## 1. What landed in Session 1

- `tests/e2e/replay.py` — `make_replay_runner` (writes the `run_one.sh` file set from
  `recorded_batch.json`; synthesizes the WAV via stdlib `wave`), `load_recorded_batch`,
  `_synth_wav`.
- `tests/e2e/conftest.py` — `fake_gpu`, `staged_inference` (all preflight files in tmp),
  `run_generate` (drives the **real** `generate.main` with only `gpu_info` +
  `training_active` + `run_batch`'s `runner` substituted — plan §5.1).
- `tests/e2e/test_inference_e2e.py` — **J1** happy path (2 songs, 3 tracks, explicit seeds):
  prompts, `batch_manifest.json`, per-track sidecar provenance, WAV duration, summary,
  `out/latest`, `_runs_status.log`.
- `tests/fixtures/{recorded_batch.json,manifest.json,README.md,fetch.sh}` — Tier A
  hand-authored from `results/maqam_lyric_swap/sidecars/`; Tier B (GCS) declared empty.
- `pytest.ini` — markers `gpu` / `fixtures_heavy` / `live`; default
  `-m "not gpu and not fixtures_heavy and not live"`.
- Docs reconciled: plan banner/§3/§9/§12 updated; `SOURCE_OF_TRUTH.md` row note;
  suppression list narrowed; `RECONCILIATION_LOG.md` appended. Mechanical pass **0 flagged**.

## 2. Decisions (resolved 2026-09-30, plan §12)

1. **Gate host: Colab free T4.** Kaggle / GH Actions remain fallbacks.
2. **Fixtures: Tier A in git, Tier B in GCS** (`tests/fixtures/fetch.sh`, gitignored).
3. **T3 scope: fake `run.py` only**; the real 10-step smoke stays at the T5 gate.

## 3. Next — Session 2 (plan §9)

- T2 journeys **J1–J4, J6** in `tests/e2e/test_inference_e2e.py`:
  - J2 idempotent re-run skip + `--force`; J3 partial failure → `_failed_runs.log` → retry;
    J4 per-song `loras:` registry routing + provenance; J6 `suno_to_songs.py` → `generate.py`.
- **Provenance guard test** (plan §4.4): fixture `checkpoint_step` / `audio_cpp_commit`
  vs today's code; skip cleanly when `AUDIO_CPP` is absent (CPU VM).
- Keep the default suite GPU-free and green.

## 4. Reproduce / verify (CPU runtime)

```bash
cd /content/maqamrock-yue2-lora-finetuning
python -m pytest -q                     # 181 passed, 1 skipped
python -m pytest tests/e2e -q           # J1
python -m pytest -m gpu --collect-only  # T5 checks, deferred to the gate
```

## 5. Guardrails

- **CPU only.** No `audiocpp_cli`, no `nvidia-smi` dependency; `preflight`'s GPU refusal
  is itself a test (plan §7).
- Tier B binaries stay out of git (`tests/fixtures/**/*.wav|.safetensors|.db`,
  `audiocpp_cli`, `out/`).
- Do not modify run configs or `/content` datasets (§8).
- `agent_notes/current.md` is a handoff surface, **not authority** — re-derive state with
  `python status.py`.

## 6. Pointers

- Plan: `docs/E2E_TESTING_PLAN.md`. This pass: `RECONCILIATION_LOG.md` (2026-09-30 entries).
- Reconciler: `skills/docs-reconciler/SKILL.md`; suppressions
  `skills/docs-reconciler/references/unverifiable.txt`.
