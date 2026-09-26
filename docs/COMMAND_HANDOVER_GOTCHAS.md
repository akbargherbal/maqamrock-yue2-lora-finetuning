# Human-terminal handover gotchas

Append-only. One entry per gotcha: the human-environment fact, the agent failure
it prevents, and the correct pattern. The procedure that uses this list is
`skills/command-handover/SKILL.md`; the always-on trigger is in `AGENTS.md`.

This list exists because the agent's shell tool is not the user's terminal.
Signals, session ownership, and where a detached process writes are obvious to a
human and invisible to the agent — so they get written down here.

## 2026-09-23 — The batch launch lacked `disown` (prompted this list)

- **Fact:** the user runs commands by hand; Ctrl+C in their terminal is a real
  risk, and a long job in the foreground dies with it.
- **Failure prevented:** the agent handed over
  `python INFERENCE/generate.py manifests/batch_songs_23092026.json` in the
  foreground, even though a ~2 h batch should be detached.
- **Correct pattern:** `setsid nohup … > /content/logs/<name>.log 2>&1 & disown`,
  with the stop command (`pkill -f …`) and the resume flag
  (`--out-dir "$(cat out/latest)"`) stated alongside.

## Detached output must be redirected to a log

- **Fact:** a detached process's stdout/stderr has no terminal; if not redirected
  it is lost.
- **Correct pattern:** `> /content/logs/<name>.log 2>&1` on every detached launch.

## A backgrounded job inherits `SIGINT=ignored` — Ctrl+C (and `kill -INT`) won't stop it

- **Fact:** a shell background job (`… &`) inherits `SIGINT=SIG_IGN`, and a
  non-interactive shell **cannot** reset it — so Ctrl+C doesn't reach it *and*
  `kill -INT <pid>` is a silent no-op. Training is launched **detached** now, so
  its clean stop has to reset SIGINT explicitly.
- **Correct pattern:** use `python train_ctl.py start` (it spawns via
  `Popen(start_new_session=True)` with a SIGINT reset) and `train_ctl.py stop`.
  For any other detached job, still state its exact stop command.

## No stop/resume line = a stuck job

- **Fact:** a detached job the user can't stop without hunting for a pid is a
  trap; a job that can't be resumed wastes the session.
- **Correct pattern:** always give `pkill -f '<pattern>'` and the exact resume
  command (e.g. `--out-dir "$(cat out/latest)"` for `generate.py`).

## vscode.dev clipboard is glitchy

- **Fact:** selecting/copying text out of the chat is slow and unreliable for the
  user.
- **Correct pattern:** put anything long the user must copy into
  `agent_notes/current.md`, not the chat.

## Env vars are staged by the launching notebook

- **Fact:** `HF_TOKEN`, `GCP_DATASET_PATH`, `GCP_BACKUP_BASE` are exported by the
  notebook, not the shell. A terminal that can't see them means the cell hasn't
  run yet (`docs/README.md`, constants).
- **Correct pattern:** check/mention this before a command that needs them.

## One shared GPU

- **Fact:** training and inference share one rented GPU; two GPU jobs at once can
  OOM the NAR graph.
- **Correct pattern:** `nvidia-smi` first; never run GPU work while training is
  active (`generate.py` refuses unless `--allow-concurrent`).

## 2026-09-25 — `pkill -f '<pattern>'` matches the launching shell too

- **Fact:** the agent's shell tool runs each command as `/bin/bash -c "<script>"`,
  so that shell's own command line contains any pattern written literally in the
  script. `pkill -f backup_to_gcp.py` therefore matches and kills the very shell
  running it, before the restart line executes.
- **Failure prevented:** two daemon-restart attempts died mid-script (empty
  output), leaving **no** backup running while the agent believed it had
  restarted one. The bracketed `[b]ackup…` trick does not help here, because the
  same command also contains the literal `backup_to_gcp.py` it is launching.
- **Correct pattern:** anchor to the real process — `pkill -f '^python.*backup_to_gcp'`
  (`^` cannot match a `/bin/bash -c …` command line). Reserve the bracket trick
  for the case where the bracketed literal is the pattern's **only** occurrence
  in the command.

## 2026-09-26 — `trap - INT` cannot un-ignore an inherited signal

- **Fact:** to keep `kill -INT` working on a detached run we first wrapped the
  launch as `setsid nohup bash -c 'trap - INT; exec …'`. It does **not** work:
  POSIX says a non-interactive shell cannot reset a signal that was ignored on
  entry, so the child keeps `SIGINT=SIG_IGN` and `kill -INT` is a silent no-op
  (verified via `/proc/<pid>/status` `SigIgn` bit `0x2` and a signal round-trip).
- **Failure prevented:** a detached training run that *looks* stoppable but
  ignores the clean stop, forcing `kill -9` and losing up to `save_every` steps.
- **Correct pattern:** reset in Python before `exec` —
  `signal.signal(signal.SIGINT, signal.SIG_DFL)` — which *can* override an
  inherited ignored signal. `train_ctl.py start` does exactly this.

## Related traps (not terminal-specific)

- The auto-resume trap: relaunching a run name with checkpoints present resumes
  instead of starting fresh — `docs/README.md`, "The one rule that bites people".
