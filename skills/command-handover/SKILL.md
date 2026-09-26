---
name: command-handover
description: Procedure for handing the user a command to run in their real terminal. Use before presenting any long-running, background/detached, or state-changing command, so terminal signals (Ctrl+C, closing the tab), output logging, stopping, and resuming are explicit. Trigger words - disown, setsid, nohup, background, foreground, Ctrl+C, long-running job, pkill, resume, run command.
---

# Command handover (real terminal, real user)

The user runs commands by hand in a terminal (vscode.dev on Colab). The agent's
shell tool is **not** that terminal: it has its own session, and facts obvious to
a human — Ctrl+C, closing the tab, where a detached process writes — are invisible
to the agent. This skill makes them explicit *before* a command is handed over.

## When this applies

Apply for any command the user will paste that is:

- long-running (more than ~a minute), or
- background / detached, or
- state-changing (writes files, starts/stops jobs, moves data).

Short read-only one-liners (`ls`, `cat`, `git status`, `pgrep`, `nvidia-smi`) are
exempt.

## Rule: annotate the command

Put one line immediately above the command block saying how it behaves:

```
terminal: foreground  — you watch it; Ctrl+C stops it.
terminal: detached    — survives Ctrl+C / closing the tab;
                        log: <path>; stop: <command>; resume: <command>.
```

For detached, **all three** of log / stop / resume are required. For a long
foreground job, also say how to check progress.

## Foreground vs detached — the decision

| Command | Mode | Why |
|---|---|---|
| Training run | **detached via `train_ctl.py`** | A stray Ctrl+C must not kill it. `train_ctl.py start` resets SIGINT so the clean `stop` still works; never launch `python run.py` bare. |
| Sidecars: `backup_to_gcp.py`, `gpu_logger.py` | **detached** | Must outlive the terminal tab / a stray Ctrl+C. |
| Inference batch (`generate.py`) and other long jobs | **detached** | Ctrl+C-proof; progress via log + `out/latest`. |

Launch training with `python train_ctl.py start` and stop it with
`train_ctl.py stop`; do not leave a long batch in the foreground where a stray
Ctrl+C kills it.

## Detached hygiene (all of it)

1. Redirect both streams to a log: `> /content/logs/<name>.log 2>&1`.
2. Launch with the repo convention: `setsid nohup <cmd> … & disown`.
3. Give the exact **stop** command (`pkill -f '<unique pattern>'`) and say whether
   partial work is safe and how to **resume**.
4. Note that Ctrl+C / closing the tab will *not* stop it.
5. Confirm nothing is already running first (`pgrep -af '<pattern>'`).

## After handing over

If the command produced a session step worth re-running, refresh
`agent_notes/current.md` (per `AGENTS.md`) so the copy-free handoff carries it.

## Record new gotchas

Every time a human-terminal reality is discovered or missed, append it to
`docs/COMMAND_HANDOVER_GOTCHAS.md` (date / fact / failure it prevents / correct
pattern). That list is the accumulation; this skill is the procedure.
