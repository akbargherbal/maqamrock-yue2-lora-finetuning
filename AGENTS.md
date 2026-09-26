# AGENTS.md

_Last revised: 2026-09-26._

## What you're for

- Get a task ready before the user launches: confirm that task's prerequisites are in place — training (dataset, model assets, config), inference (GGUF assets, converted LoRA, prompts), a merge, a pron run — and sanity-check any YAML against `DECISIONS.md` (fields that look real but are dead, paths that differ from what they appear to say).
- While a task is running, answer "how's it going" from the active job's artifacts — training: `loss_log.db` (`monitor_loss.py`) + the GPU CSV; inference: the batch log and `out/latest` — never by recalling an earlier turn.
- When a run crashes, find the cause, and either auto-resume (conditions below) or hand over the exact resume command.

Nothing else. Not a monitor running in a loop, not a companion — a problem solver, called in when needed.

**Run readiness is mode-dependent.** Don't apply a generic checklist: identify the mode from the request and read its runbook — the `docs/README.md` table maps task → doc (training `docs/START.md`; inference `docs/INFERENCE.md`; merge `docs/PRON_LORA_MERGE.md`; pron training run `docs/PRON_LORA.md`). Confirm its prerequisites; if one is missing, say so and name the doc — never hand over a command that will fail.

## The essentials (why this file exists)

Two facts drive everything; missing them costs real compute:

1. **Colab is ephemeral; storage is far cheaper than GPU time.** Losing the VM wipes `/content`; only GitHub + GCS persist. Bias hard toward persisting anything expensive to regenerate, and keep the backup sidecar running.
2. **Don't block the session.** Anything slow runs in the background with a log so the user can keep interacting. **Training is detached too** — a stray Ctrl+C (the Linux copy-paste habit) then can't kill it; stop it deliberately with `train_ctl.py stop` (SIGINT).

**Canonical docs** — consult the one that matches the task, not all of them: `DECISIONS.md` (why), `README.md` (what / how), `docs/START.md` (fresh VM), `docs/MONITOR.md` (is it healthy), `docs/PAUSE_RESUME.md` (stop / resume). `PROGRESS.md` is the milestone trail: background reading, only when you need history — not a spec.

## Durable decisions & progress

For a training/tooling task, read `DECISIONS.md` first — it records cross-session decisions and non-obvious facts verified against actual `ai-toolkit` source, the things a fresh session must not re-litigate. Consult the one runbook that matches the task (index: `docs/README.md`); read `PROGRESS.md` only for history. Routine, per-session state goes in `agent_notes/current.md`.

**`agent_notes/current.md` is a copy/paste surface, not documentation.** The user drives OpenCode over `vscode.dev`, where selecting text out of the chat is glitchy; `current.md` exists so they can copy commands from a file — or read longer text in a browser / via TTS — instead of from the terminal.

- **Write it when** the reply is long or copy-hostile: commands to run, or more than a few lines to read. If it's ~5 lines of plain text with no commands, don't create a file.
- **Contents:** a one-line header (date, current run state, what changed) + the exact commands / payload. No narrative.
- **Overwrite it — never append.** Every write replaces it with the current state.
- **Write it in the same turn you claim it.** Never say it was written unless the write actually succeeded in that turn; running a shell command is not writing the file. This has recurred — treat it as a hard rule.

## The stack

`ostris/ai-toolkit`, launched via its real CLI — not the Web UI (see `DECISIONS.md`). Run-control goes through **`train_ctl.py`**: `start` launches training **detached** (its own session, so a stray Ctrl+C can't kill it; it resets SIGINT in the child so the clean stop works even when a script or the agent launches it), and `stop` sends a checkpoint-safe SIGINT. `docs/START.md` carries the full fresh-VM sequence.

```bash
python train_ctl.py start     # detached, Ctrl+C-proof; writes a pid + state file
python train_ctl.py status    # running? pid? log tail
python train_ctl.py stop      # SIGINT; waits for "Job stopped"
```

`start` refuses a second copy of the same run; `stop` verifies the PID is our `run.py` before signalling. Plain `kill` (SIGTERM) and `kill -9` skip the clean `Job stopped` path and lose progress since the last checkpoint — last resort only.

## Handing over a command / running things yourself

The user runs commands by hand in a real terminal (vscode.dev). For any long-running, background/detached, or state-changing command, load the `command-handover` skill first:

- Say whether it runs **foreground** (Ctrl+C stops it) or **detached** (survives Ctrl+C / closing the tab).
- Detached: give the output-log path and the exact stop command; for long jobs, the progress check and resume command.
- **Training is detached on purpose** — launch and stop it via `train_ctl.py`; plain `kill` / `kill -9` are not the clean stop.
- New terminal gotchas are appended to `docs/COMMAND_HANDOVER_GOTCHAS.md`. A short read-only one-liner needs no annotation.

**When *you* run something slow** (tests, smoke checks, debugging): background it with a log, don't block the session or poll in a tight loop, and report when it finishes so the user can keep interacting. You don't need permission to run tests or debugging in your own shell — that freedom catches problems before a real run — **but check `nvidia-smi` before anything GPU-heavy**.

## Observability & where to look

Everything for the run lives under `/content/ai-toolkit/output/akbar_arabic_rock_lora/` (the config's `training_folder`): checkpoints, `loss_log.db`, `config.yaml`, samples, `tensorboard/`.

1. **`loss_log.db`** — the primary source. SQLite/WAL, safe to read while training writes. Use `monitor_loss.py <path>`; don't hand-write SQL.
2. **`/content/logs/train.log`** (the `-l` file) — the training log and tracebacks. **`/content/logs/train_stdout.log`** holds stdout/stderr from before that file is set up (e.g. an import-time crash) — check it if `train.log` looks truncated.
3. **`/content/logs/gpu_usage.csv`** — util/memory/temp/power from `gpu_logger.py` (every 10s). AI Toolkit logs no GPU stats, so confirm `gpu_logger.py` is running before believing "the GPU looks idle."

**Not a source:** `aitk_db.db` (the config's `sqlite_db_path`) — only populated under the Web UI, and only a status string.

Also: `pgrep -af 'run\.py'` for liveness; checkpoints per `save.*` in the config; TensorBoard under `<log_dir>/akbar_arabic_rock_lora_<timestamp>/` (glob the timestamped subfolder; `<log_dir>` is the config's `log_dir`, `output/akbar_arabic_rock_lora/tensorboard`); base assets in the HF cache (`~/.cache/huggingface/hub`).

## Never

- Start a new run, or resume with a **changed** config/hyperparameter, without the user typing the command. Give the exact command every time.
- **Auto-resume is the one exception — with evidence.** Resume it yourself only when the run name and config are unchanged, it looks crashed (traceback / OOM / VM reclaimed), and nothing signals a deliberate stop (no `Job stopped` at the end of `train.log`, no "stopped on purpose" note). Log what you did in `current.md`. **If you can't tell a crash from a deliberate stop, ask the user — don't guess.**
- Modify `/content/yue2_dataset` or re-run a dataset build script. If a data change is genuinely needed (e.g. the dataset silently lacks something the run depends on), **stop and explain the necessity** — don't silently proceed, and don't silently accept degraded training.
- Edit a run config on your own initiative. Config/hyperparameters are the user's: measure, report, recommend.
- **Never** run GPU-heavy work while a run might be active — check `nvidia-smi` first. One GPU, shared, rented.
- Claim to have written `agent_notes/current.md` without writing it that turn.

## Runtime reality — Colab is ephemeral, storage is cheap

Colab wipes `/content` when the VM dies; only GitHub + GCS persist. Bias hard toward persisting anything expensive to regenerate (checkpoints, `loss_log.db`, prepared dataset, logs, notes). Layout and restore: `docs/BACKUP_RESTORE.md`.

**Restore the repo on a fresh VM** (details: `docs/START.md`):

```bash
git clone https://github.com/akbargherbal/maqamrock-yue2-lora-finetuning.git \
  /content/maqamrock-yue2-lora-finetuning
cd /content/maqamrock-yue2-lora-finetuning
mkdir -p /content/logs
setsid nohup bash bootstrap/setup.sh --training > /content/logs/setup.log 2>&1 & disown
# then authenticate vscode.dev in the foreground while setup.sh runs.
```

`setup.sh` is idempotent and does **not** restore checkpoints or `loss_log.db` — pull those from the run's GCS prefix (`<base>/<run-name>/output/`; `<base>` = `$GCP_BACKUP_BASE`, e.g. `gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning`) before resuming (`docs/PAUSE_RESUME.md`).

## Backup responsibility

`backup_to_gcp.py` mirrors the run output, `/content/logs`, and `agent_notes/` to GCS in training mode, and the audio.cpp inference workspace with `--inference`. Commands, layout, verification, and restore: `docs/BACKUP_RESTORE.md`.

- Before the user starts a run, confirm the sidecars are up: `pgrep -af backup_to_gcp.py`, `pgrep -af gpu_logger.py` (or freshness of `/content/logs/gcp_backup.log`), and the session-backup loop via `vm-continuity status` (one line; exit 0 = healthy). If one is down, give the exact start command — but do not let backup repair become the session's work; if it can't be fixed cheaply, note it and continue.
- "Is my progress backed up?" → compare GCS object timestamps under the run's prefix with local ones and report the actual drift.
- **OpenCode sessions** are backed up separately by `vm-continuity` (installed and loop-started by `setup.sh` — now started early and independent of setup success; one namespace per host). Check health with `vm-continuity status`; restart with `vm-continuity watch --interval-minutes 15` (log `/content/logs/vm_continuity.log`). Recover a past session: `vm-continuity hosts` → `vm-continuity pull [--host H]` → `vm-continuity restore opencode -- --mode db|export`. A global reminder lives at `~/.config/opencode/AGENTS.md`.
- **At session end**, before handing off, re-check `vm-continuity status` (and `/content/logs/gcp_backup.log` freshness if a run was active) and state plainly whether the last successful backup is current — the user must not have to ask whether their work was saved. Report it; don't silently proceed and don't turn it into a repair project.
- **Continuity is idle-time work:** never spend GPU-paid session time on it (Milestone 1, restore tests, polish) while the project has training/inference to run. Pick it up on a busy GPU or a CPU VM.

## GitHub pushes

Pushing needs auth the user supplies, never the agent. Ask them to run `bash bootstrap/github_auth.sh` in their own terminal and paste a PAT at the hidden prompt; it validates the token and runs `gh auth setup-git`. Never ask for the token in chat. `/content` is ephemeral — re-run on every fresh VM.

## Repo docs & checks

- **Canonical docs:** `DECISIONS.md`, `README.md`, `docs/START.md`, `docs/MONITOR.md`, `docs/PAUSE_RESUME.md`.
- Dataset build + independent verification: `README.md`'s Dataset section and `verification.md`. Build/promotion history and open items: `DECISIONS.md` / `PROGRESS.md`.
- Config: `config/akbar_arabic_rock_lora.yml` — read the inline comments before "fixing" anything; several apparent issues are already resolved in `DECISIONS.md`.
- Metrics: `monitor_loss.py <loss_log.db>`; GPU: `gpu_logger.py`. Runbooks: `docs/` (`docs/README.md` is the index).
- **Skills** (reusable procedures; canonical in `skills/<name>/SKILL.md`, symlinked under `.claude/skills/`): `crash-diagnose-and-resume`, `inference-batch-run`, `command-handover`, `docs-reconciler`, `ab-blind-eval`. Load with the skill tool when a task matches; the runbooks stay the source of truth.

## Knowledge graph (graphify)

`graphify-out/` is a prebuilt, committed map of this repo — prefer `GRAPH_REPORT.md` or `graphify query "<q>"` for architecture / "what's load-bearing" questions over grepping the tree, but open the real files before editing. Refresh with `graphify update .` after meaningful changes and before merging. On a fresh VM, install the CLI (`uv tool install graphifyy`); setup and portability are in `docs/GRAPHIFY.md`.
