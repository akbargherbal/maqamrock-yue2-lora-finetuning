# AGENTS.md

## What you're for

- Get a training run ready: confirm the dataset, model assets, and config are actually in place before the user launches, and sanity-check the YAML against `DECISIONS.md` (fields that look real but are dead, paths that differ from what they appear to say).
- While a run is going, answer "how's it going" by reading `loss_log.db` (via `monitor_loss.py`) and the GPU CSV — not by guessing or recalling an earlier turn.
- When a run crashes, find the cause, and — per the policy below — either hand over the exact resume command or run it yourself, depending on whether anything changed.

Nothing else. Not a monitor running in a loop, not a companion — a problem solver, called in when needed, plus the one narrow standing exception below.

## Durable decisions & progress

Read `DECISIONS.md` and `PROGRESS.md` (repo root) at the start of any task involving training or tooling. `DECISIONS.md` records major, cross-session decisions and non-obvious insights verified against actual `ai-toolkit` source — the things a fresh session must not re-litigate or rediscover by reading a GitHub issue thread again. `PROGRESS.md` records the milestone trail: runs and their outcomes, and what's next. Keep both short and add an entry only when losing it would cost real work; neither is a log. Routine, per-session state goes in `agent_notes/current.md`.

**Maintain `agent_notes/current.md` yourself — don't wait to be asked.** The user drives this over `vscode.dev`, where selecting and copying text out of the chat is glitchy and laggy. So keep that file current as the copy-free handoff surface: after any session that changes run state, fixes tooling, or produces a command worth re-running, write/refresh it (date, what happened, exact commands, what's next). Put anything the user might otherwise have to copy from the conversation there. It's git-ignored, but `backup_to_gcp.py` mirrors it to GCS.

## The stack, so a fresh session isn't guessing

`ostris/ai-toolkit`, launched via its real CLI: `python run.py config/akbar_arabic_rock_lora.yml -l /content/logs/train.log` — not the Web UI (see `DECISIONS.md` for why that loses nothing on observability). `job: extension` / `process[].type: diffusion_trainer`, `arch: yue2`. Everything for this job lands under one folder: `training_folder/akbar_arabic_rock_lora/` — checkpoints, `loss_log.db`, `config.yaml` (auto-saved), samples, and the `tensorboard/` subfolder all together. One GPU, shared, rented.

## Observability — the three real surfaces

1. **`loss_log.db`** — the primary source. SQLite, WAL mode, safe to read while training writes to it. Use `monitor_loss.py`, don't hand-write SQL each time. Path: `<training_folder>/akbar_arabic_rock_lora/loss_log.db`.
2. **The `-l` log file** (`/content/logs/train.log`) — stdout/stderr, including the tqdm progress line (`lr:` + per-key loss) and any traceback. This is what you tail after a crash to find the cause.
3. **GPU CSV** (`/content/logs/gpu_usage.csv`, from `gpu_logger.py`) — utilization/memory/temp/power, sampled every 10s. AI Toolkit itself logs none of this (verified, see `DECISIONS.md`) — this script is the only source, so confirm it's actually running before trusting a "the GPU looks idle" read.

**Not a source:** `aitk_db.db` (the config's `sqlite_db_path`). It only populates when the Web UI launches the job, and only ever holds a status string, never metrics. If a fresh session inherits a config pointing at it expecting run history, that expectation is wrong — check `DECISIONS.md`.

## Never

- **Start a new run, or resume with any changed config/hyperparameter, without the user typing the command themselves.** Give the exact command every time — vague hand-waving forces them to reconstruct settings you already know.
- **Auto-resume is the one exception**, and only when *all* of these hold: the run was already running with human approval, it stopped from an unplanned interruption (not a deliberate stop), and the resume uses the identical config and run name. In that case, resume it yourself rather than waiting for the user to come back and retype a command — that's the whole point of the exception. Log what you did in `agent_notes/current.md` either way.
- Modify the dataset (`/content/yue2_dataset`) or re-run `prepare_yue2_dataset.py` — it's already built and verified (`verification.md`); don't regenerate it "to be sure."
- Run anything GPU-heavy while a run might be active — check `nvidia-smi` first. One GPU, shared.

## Runtime reality — Colab is ephemeral, storage is cheap

Google Colab: strong GPUs, stateless. Losing the VM or switching runtime wipes `/content` — the repo working tree, the HF cache, everything. Only GitHub + GCS persist. Storage costs far less than compute, so bias hard toward persisting anything expensive to regenerate (the LoRA checkpoints, `loss_log.db`, the prepared dataset, logs, this repo's own notes).

**Restore on a fresh VM:**

```bash
git clone <this repo's URL>
cd maqamrock-yue2-lora-finetuning
bash bootstrap/setup.sh > /content/logs/setup.log 2>&1 &
# then authenticate vscode.dev in the foreground while setup.sh runs —
# it clones ai-toolkit, installs its (heavier) deps, pre-warms the HF
# cache for the yue2 assets, and pulls the dataset from GCS, all in parallel
```

`bootstrap/setup.sh` is idempotent: it skips the dataset download if the completion marker is present, and skips any HF asset already in the local cache. It does **not** restore checkpoints or `loss_log.db` — pull those from the run's GCS prefix (`<base>/<run-name>/output/`) before resuming.

## Backup responsibility

- `backup_to_gcp.py` mirrors `training_folder` (checkpoints, `loss_log.db`, config, samples, tensorboard), `/content/logs` (train log + GPU CSV), and `agent_notes/`. Before a run that writes a new output folder, confirm `TARGETS` actually covers it — if not, fix the script, don't work around it by hand.
- Before the user starts a run, confirm the backup daemon is actually running (`pgrep -af backup_to_gcp.py`, or freshness of `/content/logs/gcp_backup.log`) and that `gpu_logger.py` is too (`pgrep -af gpu_logger.py`). If either isn't, give the exact command — `--run-name` is required for the backup script, and the GCS base comes from `GCP_BACKUP_BASE`, exported by the launching notebook:

  ```bash
  cd /content/maqamrock-yue2-lora-finetuning
  setsid nohup python backup_to_gcp.py --run-name akbar_arabic_rock_lora \
    > /content/logs/gcp_backup_stdout.log 2>&1 & disown
  setsid nohup python gpu_logger.py --out /content/logs/gpu_usage.csv \
    > /content/logs/gpu_logger_stdout.log 2>&1 & disown
  ```

- "Is my progress backed up?" → compare GCS object timestamps under the run's configured prefix with local timestamps and report the actual drift — don't assume the last known-good state is still current.

## GitHub pushes

- Pushing needs auth the user supplies, never the agent. Ask them to run `bash bootstrap/github_auth.sh` in their own terminal and paste a PAT at the hidden prompt; it validates the token, runs `gh auth setup-git`, and prints the authenticated account. After that, `git push` works for the rest of the session. Never ask for the token in chat.
- `/content` is ephemeral — re-run it on every fresh VM.

## Repo docs & checks

- Dataset build + independent verification: `prepare_yue2_dataset.py` (already run, don't re-run) and `verification.md` (the audit record — read it before assuming anything about dataset format is unverified).
- Config: `config/akbar_arabic_rock_lora.yml`. Read the inline comments before "fixing" anything that looks off — several apparent issues (`log_config`, `type: diffusion_trainer`) are already resolved in `DECISIONS.md`.
- Metrics: `monitor_loss.py <path to loss_log.db>` — latest step, latest metric values, step-rate/ETA. GPU: `gpu_logger.py`.

## Where to look before answering "what's going on"

- **Training progress:** `<training_folder>/akbar_arabic_rock_lora/loss_log.db` via `monitor_loss.py`. Don't trust `aitk_db.db` for this (see above).
- **Is it still alive:** `pgrep -af run.py`, and the tail of `/content/logs/train.log` for the most recent line / any traceback.
- **Checkpoints:** inside `<training_folder>/akbar_arabic_rock_lora/` per `save.save_format`/`save_every`/`max_step_saves_to_keep` in the config.
- **TensorBoard (secondary, redundant with loss_log.db):** `<log_dir>/akbar_arabic_rock_lora_<timestamp>/` — glob for the timestamped subfolder, don't assume `log_dir` itself holds the event file.
- **GPU:** `/content/logs/gpu_usage.csv`, if `gpu_logger.py` is running.
- **Base model / assets:** standard HF cache (`~/.cache/huggingface/hub`), not a bespoke local directory — see `DECISIONS.md`'s asset-download entry before assuming a file is missing just because it's not under the repo.
