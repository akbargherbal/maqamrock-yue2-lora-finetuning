# current

_Updated 2026-09-30 (local). E2E **Sessions 1–3 are complete** (Colab CPU,
GPU-free): `python -m pytest` -> **190 passed, 2 skipped**, all pushed
(`60368cc`). The next and only remaining step is **Session 4 — the budgeted T5
GPU gate** on a **Colab free T4** (plan §6). This VM is CPU; switching the
runtime wipes `/content` and ends it — see the pre-switch checklist (§7)._

## 0. Orientation — read these first, in order

1. `AGENTS.md` §2 (mode/environment) and §8 (the never list). **GPU rule:** no
   GPU work until `nvidia-smi` shows the T4 and nothing is running.
2. `docs/E2E_TESTING_PLAN.md` — §2 (boundary), §4 (record→replay + §4.4), §5
   (journeys), **§6 (the gate S1–S3)**, §8 (wiring), §9 (sequencing), §12.
3. `SOURCE_OF_TRUTH.md`, row "End-to-end test plan / tiers".

## 1. What landed in Sessions 1–3

- **T2** (`tests/e2e/test_inference_e2e.py`): J1–J4, J6 + provenance guard, on the
  real `generate.main` (only `gpu_info` + `runner` substituted).
- **T3** (`test_train_lifecycle_e2e.py`, `test_monitor_status_e2e.py`,
  `test_backup_restore_e2e.py`): J10 real detached process + SIGINT stop; J11
  `monitor_loss.py`/`status.py` on a spec-built db and a real run; J12 real
  `backup_to_gcp.py` mirror + manifest + byte-identical restore.
- Helpers: `tests/staging.py`, `tests/e2e/{replay,lossdb,fake_run,fake_gsutil}.py`.
- Tier A fixtures: `recorded_batch.json`, `loss_log.spec.json`, `manifest.json`,
  `README.md`, `fetch.sh`.
- **Production fix**: `train_ctl.py::cmd_stop` log-write/exit race (false "still
  running"); now waits a 5 s grace. `PAUSE_RESUME.md` still holds.

## 2. Decisions (resolved 2026-09-30, plan §12)

1. **Gate host: Colab free T4.** Kaggle / GH Actions GPU are fallbacks.
2. **Fixtures: Tier A in git, Tier B in GCS** (`tests/fixtures/fetch.sh`).
3. **T3 scope: fake `run.py` only**; the real 10-step smoke stays at the T5 gate.

## 3. Pre-switch checklist (do on THIS CPU VM, before changing the runtime)

The runtime switch **restarts the VM and wipes `/content`**; only GitHub + GCS
persist. Confirm before switching:

- Work is pushed: `git status --short` is clean and
  `git log origin/music-cover..HEAD --oneline` is empty.
- Continuity is healthy: `vm-continuity status` exits 0. To recover this OpenCode
  session on the fresh VM afterwards: `vm-continuity hosts`, `vm-continuity pull`,
  then `vm-continuity restore opencode -- --mode db|export`.
- You can re-create `/root/.secrets.env` (HF_TOKEN + GCP_*) from the notebook cell.

Then: **Runtime -> Change runtime type -> T4 GPU** (this is a Colab-UI action;
the agent cannot do it). It disconnects and ends this VM.

## 4. Bring-up on the T4 VM

```bash
# 0. secrets: run the notebook cell that exports HF_TOKEN + GCP_* to /root/.secrets.env
git clone git@github.com:akbargherbal/maqamrock-yue2-lora-finetuning.git \
  /content/maqamrock-yue2-lora-finetuning
cd /content/maqamrock-yue2-lora-finetuning
nvidia-smi                 # read-only: confirm a T4 and that it is idle
```
```
terminal: detached  — long, multi-GB; log: /content/logs/setup_inference.log;
  stop: pkill -f 'bootstrap/setup.sh'; resume: rerun the same command.
```
```bash
setsid nohup bash bootstrap/setup.sh --inference \
  > /content/logs/setup_inference.log 2>&1 & disown
# watch: tail -f /content/logs/setup_inference.log   (wait for all "[ok]")
```
```
terminal: detached  — installs ai-toolkit + torch/cu130 + dataset; log:
  /content/logs/setup_training.log; stop: pkill -f 'bootstrap/setup.sh';
  resume: rerun the same command.  Run AFTER --inference completes.
```
```bash
setsid nohup bash bootstrap/setup.sh --training \
  > /content/logs/setup_training.log 2>&1 & disown
# watch: tail -f /content/logs/setup_training.log
```

## 5. The gate: S1–S3 (plan §6) — records the fixtures AND proves the kernels

**S1 — binary loads, CUDA present** (short, foreground):
```bash
/content/audiocpp_inference/bin/audiocpp_cli --version
```

**S2 — one real generation** (`<Maqam>` in Ajam/Hijaz/Kurd/Nahawand; ~7 min):
```
terminal: detached  — GPU; log: /content/smoke/Hijaz_1.log (+ _runs_status.log);
  stop: pkill -f audiocpp_cli; resume: rerun (the WAV is rewritten).
```
```bash
OUT_DIR=/content/smoke setsid nohup bash INFERENCE/run_one.sh Hijaz 1 auto \
  > /content/logs/smoke_run_one.log 2>&1 & disown
# progress: tail -f /content/smoke/Hijaz_1.log ; ls -l /content/smoke
# check:    grep -h 'Exit status' /content/smoke/Hijaz_1_time.txt   # expect 0
#           ls -l /content/smoke/Hijaz_1.wav
```

**S3 — 10-step training smoke** (uses `train_ctl.py`, so a stray Ctrl+C can't kill it):
```
terminal: detached  — GPU; log: /content/logs/train_smoke.log;
  stop: python train_ctl.py stop --log-name train_smoke;
  resume: rerun the start command (auto-resumes newest checkpoint).
```
```bash
python train_ctl.py start --config config/pron_lora_ar_only_smoke.yml \
  --log-name train_smoke
# status: python train_ctl.py status --config config/pron_lora_ar_only_smoke.yml --log-name train_smoke
# success: 10/10 steps, finite loss, checkpoint under
#   /content/ai-toolkit/output/pron_lora_ar_only_smoke/
```

**Optional S2b:** re-run S2 with a nonexistent `LORA_AR=...` to capture a real
`exit=1` `.log`.

## 6. After the gate

1. Start the backup sidecars so the smoke artifacts are mirrored (they were DOWN
   on the CPU VM): `pgrep -af 'backup_to_gcp.py|gpu_logger.py'`; if absent, launch
   each detached (`setsid nohup ...`, per `docs/BACKUP_RESTORE.md`).
2. Copy the smoke artifacts into `tests/fixtures/` — Tier A (`.log`, `_time.txt`,
   sidecar, `recorded_batch` provenance) and Tier B (`.wav`) — set `tier_b` in
   `tests/fixtures/manifest.json`, then **switch back to the CPU runtime** and
   re-run `python -m pytest` (the guards now check `audio_cpp_commit` too).

## 7. Guardrails

- One GPU, shared, rented — never overlap; `nvidia-smi` before any GPU work.
- Tier B binaries stay out of git (`tests/fixtures/**/*.wav|.safetensors|.db`,
  `audiocpp_cli`, `out/`).
- Do not modify run configs or `/content` datasets (AGENTS.md §8).
- `agent_notes/current.md` is a handoff surface, **not authority** — re-derive
  state with `python status.py`.

## 8. Pointers

- Plan: `docs/E2E_TESTING_PLAN.md`. Passes: `RECONCILIATION_LOG.md` (2026-09-30).
- Reconciler: `skills/docs-reconciler/SKILL.md`; suppressions
  `skills/docs-reconciler/references/unverifiable.txt`.
