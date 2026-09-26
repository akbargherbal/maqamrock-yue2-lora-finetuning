#!/usr/bin/env python3
"""Run-control for an ai-toolkit training job.

`start` launches training **detached** (its own session) so the terminal's
accidental Ctrl+C cannot kill it, while keeping it cleanly stoppable with
SIGINT (`stop`). It writes a PID + state file so liveness is observable, and it
refuses to start a second copy of the same run.

Why this exists (see AGENTS.md): a plain shell background job inherits
``SIGINT=SIG_IGN``, which makes the checkpoint-safe stop (``kill -INT``) a
silent no-op. Spawning through ``Popen(..., start_new_session=True)`` from a
foreground launcher avoids that, and a ``preexec_fn`` reset makes it robust even
when a script or the agent launches it.

Run-control policy: the user types the launch; the agent may auto-resume an
unchanged crashed run. This tool only launches/stops/inspects — it never edits
the config or the dataset.

Usage:
    python train_ctl.py start [--dry-run]
    python train_ctl.py status
    python train_ctl.py stop [--timeout 180]

The log basename defaults to ``train`` (so ``train.log``, ``train.pid`` …);
override with ``--log-name`` for a side run (e.g. a pron smoke test).
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
DEFAULT_CONFIG = REPO_ROOT / "config" / "akbar_arabic_rock_lora.yml"
DEFAULT_AI_TOOLKIT = Path("/content/ai-toolkit")
DEFAULT_LOGS = Path("/content/logs")
DEFAULT_LOG_NAME = "train"


# --- paths / small process helpers -----------------------------------------

def _pid_path(logs: Path, log_name: str) -> Path:
    return logs / f"{log_name}.pid"


def _state_path(logs: Path, log_name: str) -> Path:
    return logs / f"{log_name}_state.json"


def _train_log(logs: Path, log_name: str) -> Path:
    return logs / f"{log_name}.log"


def _stdout_log(logs: Path, log_name: str) -> Path:
    return logs / f"{log_name}_stdout.log"


def _proc_state(pid: int) -> str | None:
    """Return the /proc state char ('R', 'S', 'Z', ...) or None if gone."""
    try:
        stat = Path(f"/proc/{pid}/stat").read_text()
    except OSError:
        return None
    after = stat.rfind(")")
    if after == -1:
        return None
    return stat[after + 2: after + 3] or None


def _alive(pid: int) -> bool:
    """True if the pid exists and is not a zombie."""
    return _proc_state(pid) not in (None, "Z")


def _cmdline(pid: int) -> str:
    try:
        raw = Path(f"/proc/{pid}/cmdline").read_text()
    except OSError:
        return ""
    return " ".join(part for part in raw.split("\0") if part)


def _cmdline_matches(cmdline: str, config: Path, run_name: str) -> bool:
    if not cmdline or "run.py" not in cmdline:
        return False
    return str(config) in cmdline or run_name in cmdline


def _read_pid(pidfile: Path) -> int | None:
    try:
        return int(pidfile.read_text().strip())
    except (OSError, ValueError):
        return None


def _tail(path: Path, n: int = 10) -> str:
    try:
        lines = path.read_text(errors="replace").splitlines()
    except OSError:
        return ""
    return "\n".join(lines[-n:])


# --- subcommands -----------------------------------------------------------

def cmd_start(args: argparse.Namespace) -> int:
    # The user may Ctrl+C out of habit while reading the output; don't let that
    # kill the launcher mid-flight. The child gets SIGINT reset in _preexec.
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    config = Path(args.config).expanduser().resolve()
    ai_toolkit = Path(args.ai_toolkit)
    logs = Path(args.logs_dir)
    log_name = args.log_name
    run_name = args.run_name or config.stem
    pidfile = _pid_path(logs, log_name)
    train_log = _train_log(logs, log_name)
    stdout_log = _stdout_log(logs, log_name)

    problems = []
    if not config.is_file():
        problems.append(f"config not found: {config}")
    if not (ai_toolkit / "run.py").is_file():
        problems.append(f"run.py not found under: {ai_toolkit}")
    if problems:
        for problem in problems:
            print(f"error: {problem}", file=sys.stderr)
        return 2

    existing = _read_pid(pidfile)
    if existing and _alive(existing) and _cmdline_matches(
            _cmdline(existing), config, run_name):
        print(f"error: already running (pid {existing})", file=sys.stderr)
        print(f"       stop it first: python {Path(__file__).name} stop "
              f"--log-name {log_name}", file=sys.stderr)
        return 1

    argv = [sys.executable, "run.py", str(config), "-l", str(train_log)]
    print(f"launch (detached), cwd={ai_toolkit}:")
    print("  " + " ".join(argv))
    if args.dry_run:
        print("(dry-run: nothing launched)")
        return 0

    logs.mkdir(parents=True, exist_ok=True)
    with open(stdout_log, "ab") as out:
        proc = subprocess.Popen(
            argv, cwd=str(ai_toolkit), stdin=subprocess.DEVNULL,
            stdout=out, stderr=subprocess.STDOUT,
            start_new_session=True, preexec_fn=_preexec, close_fds=True)

    pidfile.write_text(f"{proc.pid}\n")
    _state_path(logs, log_name).write_text(json.dumps({
        "pid": proc.pid,
        "run_name": run_name,
        "config": str(config),
        "started": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "train_log": str(train_log),
        "stdout_log": str(stdout_log),
    }, indent=2) + "\n")

    stop_hint = f"python {Path(__file__).name} stop"
    if log_name != DEFAULT_LOG_NAME:
        stop_hint += f" --log-name {log_name}"
    print(f"\ntraining started — pid {proc.pid}, detached (survives Ctrl+C)")
    print(f"logs:   {train_log}")
    print(f"        {stdout_log}  (pre-log / import-time output)")
    print(f"stop:   {stop_hint}     (SIGINT, checkpoint-safe)")
    print(f"resume: rerun this same start command (auto-resumes newest checkpoint)")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    config = Path(args.config).expanduser().resolve()
    logs = Path(args.logs_dir)
    log_name = args.log_name
    run_name = args.run_name or config.stem
    pid = _read_pid(_pid_path(logs, log_name))

    running = bool(pid and _alive(pid)
                   and _cmdline_matches(_cmdline(pid), config, run_name))
    if not running:
        print(f"not running (stale pid {pid})" if pid else "not running")
        return 1

    state = {}
    try:
        state = json.loads(_state_path(logs, log_name).read_text())
    except (OSError, ValueError):
        pass
    started = state.get("started", "?")
    print(f"running — pid {pid}, run '{run_name}', started {started}")
    tail = _tail(_train_log(logs, log_name))
    if tail:
        print(f"--- {log_name}.log (tail) ---")
        print(tail)
    return 0


def cmd_stop(args: argparse.Namespace) -> int:
    config = Path(args.config).expanduser().resolve()
    logs = Path(args.logs_dir)
    log_name = args.log_name
    run_name = args.run_name or config.stem
    pidfile = _pid_path(logs, log_name)
    pid = _read_pid(pidfile)

    if not pid or not _alive(pid):
        print("not running")
        pidfile.unlink(missing_ok=True)
        return 0

    cmdline = _cmdline(pid)
    if not _cmdline_matches(cmdline, config, run_name):
        print(f"refusing to signal pid {pid}: not our training run", file=sys.stderr)
        print(f"  cmdline: {cmdline}", file=sys.stderr)
        return 1

    print(f"sending SIGINT to pid {pid} (clean, checkpoint-safe stop)…")
    os.kill(pid, signal.SIGINT)
    train_log = _train_log(logs, log_name)
    deadline = time.time() + args.timeout
    while time.time() < deadline:
        if not _alive(pid):
            break
        if "Job stopped" in _tail(train_log, 40):
            break
        time.sleep(1.0)

    if _alive(pid):
        print(f"warning: still running after {args.timeout}s — check {train_log}",
              file=sys.stderr)
        return 1
    if "Job stopped" in _tail(train_log, 40):
        print("stopped cleanly (log shows 'Job stopped')")
    else:
        print("process exited")
    pidfile.unlink(missing_ok=True)
    return 0


def _preexec() -> None:  # runs in the child, after fork, before exec
    # Guarantee a default SIGINT so the SIGINT stop reaches run.py. A shell
    # background job would otherwise enter with SIGINT ignored and stay ignored.
    signal.signal(signal.SIGINT, signal.SIG_DFL)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Launch/stop/inspect the detached ai-toolkit training run.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    def common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--config", default=str(DEFAULT_CONFIG),
                       help="training config YAML (default: %(default)s)")
        p.add_argument("--ai-toolkit", default=str(DEFAULT_AI_TOOLKIT),
                       help="ai-toolkit checkout (default: %(default)s)")
        p.add_argument("--logs-dir", default=str(DEFAULT_LOGS),
                       help="log/pid directory (default: %(default)s)")
        p.add_argument("--log-name", default=DEFAULT_LOG_NAME,
                       help="log/pid basename (default: %(default)s)")
        p.add_argument("--run-name", default=None,
                       help="run name (default: the config file's stem)")

    p_start = sub.add_parser("start", help="launch training detached")
    common(p_start)
    p_start.add_argument("--dry-run", action="store_true",
                         help="print what would run; launch nothing")
    p_start.set_defaults(func=cmd_start)

    p_status = sub.add_parser("status", help="is it running, and the log tail")
    common(p_status)
    p_status.set_defaults(func=cmd_status)

    p_stop = sub.add_parser("stop", help="SIGINT the run and wait for it to stop")
    common(p_stop)
    p_stop.add_argument("--timeout", type=float, default=180.0,
                        help="seconds to wait for the stop (default: %(default)s)")
    p_stop.set_defaults(func=cmd_stop)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
