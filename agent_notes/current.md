# current

_Updated 2026-09-30 (local). **Next session: Colab **CPU** runtime. Task: implement
`docs/E2E_TESTING_PLAN.md` Session 1 — GPU-free.** A CPU runtime is the faithful host:
it has `/content` and no `nvidia-smi`, exactly what the plan's T2/T3 tiers need. No GPU
work this session. Branch `music-cover` (plan + reconcile committed at `1513027`)._

## 0. Orientation — read these first, in order

1. `AGENTS.md` §2 (identify mode/environment) and §8 (the never list). This is **not** a
   §2 runbook mode; the authority is the plan doc below.
2. `docs/E2E_TESTING_PLAN.md` — §4 (record→replay), §5 (journey matrix), §8 (test wiring),
   §9 (sequencing = what Session 1 is), §12 (the 3 decisions to confirm with the user).
3. `SOURCE_OF_TRUTH.md`, row "End-to-end test plan / tiers".

## 1. Session 1 scope (plan §9)

- Build the `tests/e2e/` scaffold: `replay.py` (`make_replay_runner`), `conftest.py`
  (`fake_gpu`, staged fake assets), and pytest markers (`gpu`, `fixtures_heavy`, `live`).
- Harvest fixtures from **existing** artifacts — no GPU: `results/replay_l4_*.json`,
  `results/*/sidecars/`, `manifests/`, and GCS run dirs; write `tests/fixtures/recorded_batch.json`.
- Exit criterion: **J1** (inference happy path driven through `generate.main` with only
  `gpu_info` + `runner` substituted) passes on the CPU runtime with a hand-authored fixture.

## 2. Environment bring-up (you run these in a Colab terminal)

Fresh VM, clone the branch, then bootstrap CPU-side. Bootstrap backgrounds the heavy jobs;
watch `/content/logs/setup.log`.

```bash
git clone https://github.com/akbargherbal/maqamrock-yue2-lora-finetuning.git
cd maqamrock-yue2-lora-finetuning && git checkout music-cover
bash bootstrap/setup.sh --inference > /content/logs/setup.log 2>&1 &
# ...do vscode.dev tunnel auth in the foreground while it runs...
python -m pytest -q
```

`--inference` deliberately installs **no** torch. Colab's image usually ships one anyway;
if `tests/test_merge_pron_lora.py` fails to collect with `ModuleNotFoundError: torch`,
either `pip install torch --index-url https://download.pytorch.org/whl/cpu` or run
`python -m pytest -q --ignore=tests/test_merge_pron_lora.py` — and note which you chose.
(On the localhost box this module is the only one that does not collect.)

## 3. Guardrails for this session

- **CPU only.** Do not start GPU work, do not run `audiocpp_cli`, do not rely on
  `nvidia-smi`. `preflight`'s GPU refusal is itself a test (plan §7).
- Your terminal ≠ my shell: you type the commands; I do CPU-only repo work.
- `agent_notes/current.md` is a handoff surface, **not authority** (§6) — re-derive state
  with `python status.py`.
- Fixtures: Tier A (small text/json) in git; Tier B (wav / safetensors / db / binary) is
  GCS-backed and gitignored — never commit large binaries.
- Do not modify run configs or `/content` datasets (§8).

## 4. Confirm with the user before writing test code (plan §12)

1. Gate host for the single GPU smoke: **Kaggle T4** (proposed) / Colab free T4 / GH Actions GPU.
2. Fixture home: Tier A in git, Tier B in GCS — confirm.
3. T3 scope: fake `run.py` enough for the training-lifecycle e2e, or also a real 10-step
   smoke each recording cycle?

These are the user's call — do not pick silently.

## 5. Pointers

- Plan: `docs/E2E_TESTING_PLAN.md`. This pass: `RECONCILIATION_LOG.md` (2026-09-30 entry).
- Reconciler: `skills/docs-reconciler/SKILL.md`; suppressions
  `skills/docs-reconciler/references/unverifiable.txt`.
- Prior track (music-cover seed replication) is parked — its handover is in git history and
  `docs/music-cover-feasibility.md` §7 — **not** this session's work.
