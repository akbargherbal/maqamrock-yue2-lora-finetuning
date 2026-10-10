# Next-session prompt — paste this to start the A100 session

_Created 2026-10-10. Task: LAUNCH the v3 maqamrock LoRA run (`v3_arabmaqamrock_lora`) on a fresh A100 VM._
_Copy from here (vscode.dev text selection is glitchy; this file is a copy surface, not authority)._

```text
Fresh Colab A100 VM. Repo akbargherbal/maqamrock-yue2-lora-finetuning, branch main.
Task: LAUNCH the v3 maqamrock style-LoRA run — `v3_arabmaqamrock_lora` (438-track verbatim-lyric
dataset, 5000 steps). It has NOT been started yet. No other run is active.

Read first, in order: AGENTS.md -> agent_notes/current.md (the live handoff/state) ->
docs/START.md -> docs/MONITOR.md. Then VERIFY live, never recall: `python status.py`,
`git log -1 --oneline`, `nvidia-smi`, and the GCS prefixes. Ground truth = artifacts.

Environment: fresh Colab A100 VM (ONE shared, rented GPU — run nvidia-smi FIRST; never overlap
GPU work). `/content` is ephemeral; only GitHub + GCS persist. Branch main is already pushed.

Before the run (the launching notebook already stages this):
- The notebook exports GCP_DATASET_ZIP (the v3 zip). `bash bootstrap/setup.sh --training` fetches
  it (~2.5 GB) + unzips to /content/yue2_dataset and builds the torch/HF stack, DETACHED
  (~5-7 min), so it overlaps the vscode.dev auth. Confirm it ends all `[ok]` including
  `dataset: 438 tracks in /content/yue2_dataset` (else read /content/logs/dataset_zip.log).
- Start the two sidecars (from the repo root):
    setsid nohup python backup_to_gcp.py --run-name v3_arabmaqamrock_lora > /content/logs/gcp_backup_stdout.log 2>&1 & disown
    setsid nohup python gpu_logger.py --out /content/logs/gpu_usage.csv > /content/logs/gpu_logger_stdout.log 2>&1 & disown

Launch (I TYPE this myself — do not start it for me):
    python train_ctl.py start --config config/v3_arabmaqamrock_lora.yml
- The FIRST thing after start is a mandatory GPU latent-cache build for the 438 (~7 min on A100)
  plus ~1-3 min model load, BEFORE step 1. `loss_log.db` stays at 0 steps for a few minutes —
  that is normal, not a stall. The cache is mandatory for YuE2 and is per-VM (rebuilt each fresh VM).
- `disable_sampling: true` => NO inference runs on the A100 (sampling happens later, offline, on a
  cheap GPU). Expect ~4.75 h for 5000 steps (measured ~3.42 s/step on A100).

Constraints: never start/resume a run with a changed config; do NOT edit configs or
hyperparameters (measure, report, recommend); ONE GPU — no overlapping GPU work, ever; stop with
`python train_ctl.py stop` (SIGINT), never bare kill/kill -9.

Known open items (see agent_notes/current.md): the held-out/eval prompts are STALE vs the 438
(3/4 contaminated) — regenerate before ANY evaluation; the config's `sample.samples` are inert.

Give me any state-changing/long command to run (command-handover skill). Report state from
artifacts only (status.py; monitor_loss.py <run>/loss_log.db; train.log; gpu_usage.csv),
citing file:line.
```
