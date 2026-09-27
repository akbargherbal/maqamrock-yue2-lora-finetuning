# Session protocol — keeping context across VMs

This is for a **multi-day, multi-VM** run. `docs/PAUSE_RESUME.md` covers resuming
the *training run*; this doc covers resuming **the agent's context** — how a fresh
session on a fresh VM gets back into a known state without you re-explaining.

## Where state lives

| Store | Holds | Survives a VM stop? |
|---|---|---|
| **GitHub** (`pron-lora-long`) | code, configs, plan, docs, this protocol, `agent_notes/current.md` | yes |
| **GCS** (`…/OSTRIS_Arabic_Suno_Finetuning/`) | dataset, banked latent cache, checkpoints, `loss_log.db`, TensorBoard, `agent_notes/` mirror, **and the OpenCode session store** | yes |
| VM `/content` + `/root` | the live run, the conversation, HF cache | **no** |

Rule: nothing important lives *only* on the VM. Code/docs → push. Run artifacts →
the 5-min `backup_to_gcp.py` mirror. Conversation → `vm-continuity`.

## Two ways back into context

### A. Restore the actual conversation (richest, if it was captured)
`vm-continuity` ships the OpenCode session DB to
`<CONTINUITY_GCS>/opencode_sessions/by_host/<host>/` every 5 min **while its loop
runs**. `bootstrap/setup.sh` starts that loop early on every VM (both modes).
On a fresh VM:
```bash
vm-continuity hosts                                  # list VM namespaces
vm-continuity pull --host <H>                        # fetch one namespace
vm-continuity restore opencode -- --mode db          # exact restore
# or portable:  vm-continuity restore opencode -- --mode export --directory <repo>
```
Then reopen the session (`opencode -s <session-id>`). Notes:
- Only sessions captured **while the loop ran** come back. If the loop was off, they
  don't — that is exactly what happened to the 2026-09-26 session that wrote the plan.
- The per-session `sessions/<id>.json` export is the version-robust fallback; the DB
  snapshot is the exact one. Verify with `vm-continuity status` (exit 0 = healthy).

### B. Cold start with a pasted prompt (always works — the real guarantee)
Don't re-explain the project. The repo + GCS carry the state; a fresh agent reads it.
The agent's contract (`AGENTS.md`) already tells it to read `DECISIONS.md` and the
matching runbook; the project-specific entry points are:

1. `agent_notes/current.md` — the live state line + next step (tracked in git).
2. `docs/PRON_LORA_LONG_PLAN.md` — the run design and locked decisions.
3. `docs/GPU_OPENING_PROMPT.md` — the GPU-phase sequence.

Then the agent must **verify live state, never trust memory**: branch, `nvidia-smi`,
sidecars (`pgrep -af 'run\.py'`, `backup_to_gcp.py`, `gpu_logger.py`), and the newest
`quran_long_aya_r8` checkpoint in GCS versus local.

## The ritual

### Opening (you)
1. Restore the session (A) if it was captured; otherwise start fresh and paste the
   right prompt below (B).
2. Make sure the notebook exported the env: `HF_TOKEN`, `GCP_DATASET_PATH`,
   `GCP_BACKUP_BASE`.

### Closing (you + agent) — do this **before** you disconnect
1. Stop training cleanly:
   `python train_ctl.py stop --log-name train_quran_long` (waits for "Job stopped")
2. Force a mirror and confirm the newest checkpoint landed:
   `python backup_to_gcp.py --run-name quran_long_aya_r8 --once`, then check the
   `…/quran_long_aya_r8/output/` listing for the latest `*.safetensors` **and**
   `optimizer.pt`.
3. If the latent cache was just built and not yet banked, bank it now (§4.3 of the plan).
4. The agent updates `agent_notes/current.md` and commits + pushes.
5. Confirm `vm-continuity status` / the last ship time, then you can let the VM go.

## What "resume the run" means technically
Same run name + same config → `ai-toolkit` loads the newest checkpoint (the log prints
"Found step N … starting from there"). Restore = dataset + banked latent cache + run
output prefix, then relaunch the **identical** command (you type it). Never two VMs on
one run name. Full commands: `docs/PAUSE_RESUME.md` + plan §5.4.

## Loss window
Checkpoints every **1500 steps**; GCS mirror every **5 min**. A disconnect loses at
most the steps since the last 1500-multiple, plus ≤5 min of a completed checkpoint.
(The wall-clock minutes depend on s/step, measured in the first GPU session.)

## Copy-paste — first GPU launch
See the code block in `docs/GPU_OPENING_PROMPT.md`.

## Copy-paste — resume after a pause
```text
Resume the multi-day YuE2 run quran_long_aya_r8 (branch pron-lora-long); fresh VM.
Read agent_notes/current.md, docs/PRON_LORA_LONG_PLAN.md, docs/GPU_OPENING_PROMPT.md first.
Before anything else, report live state: nvidia-smi, disk, vm-continuity status, and the
newest quran_long_aya_r8 checkpoint in GCS with its step number. Then give me the exact
commands to restore the dataset + banked latent cache + run output prefix and start the
sidecars, followed by the identical launch command to type. Do not auto-resume; do not
edit the config.
```

## Copy-paste — status check while running
```text
Check quran_long_aya_r8 (branch pron-lora-long). Read agent_notes/current.md first.
Answer from live artifacts only: latest step + loss (monitor_loss.py on the run's
loss_log.db), GPU util/mem (gpu_usage.csv), newest checkpoint local vs GCS and the drift,
and whether backup_to_gcp.py + gpu_logger.py are running. Make no changes.
```
