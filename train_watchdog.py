#!/usr/bin/env python3
"""Unattended crash-watchdog + supervisor for a single ai-toolkit training run.

When the run is healthy it does nothing. When the parent ``run.py`` dies
WITHOUT a deliberate-stop marker ("Job stopped" in train.log) it:
  1. pushes an alert (if WATCHDOG_ALERT_URL is set),
  2. makes sure the backup + gpu-logger sidecars are alive,
  3. relaunches the *identical* config/run via ``train_ctl.py start``
     (auto-resumes the newest checkpoint).

It never edits the config, run name, or any hyperparameter.

Stops itself when it sees:
  * a deliberate stop ("Job stopped" in the log),
  * run completion (reached --total-steps),
  * a restart loop with no step progress (e.g. OOM on the same long track),
  * more than --max-restarts total relaunches.
On the last two it sends an ALERT (log + push) so a human knows.

Policy: AGENTS.md §8 "auto-resume on crash" exception, pre-authorised by the
user for this run.

Usage:
    python train_watchdog.py [--config config/v3_arabmaqamrock_lora.yml]
                             [--interval 30] [--max-restarts 6]
                             [--total-steps 5000] [--once] [--dry-run] [--no-sidecars]

Env:
    WATCHDOG_ALERT_URL   optional. If set, POSTs the alert text to it. Works with
                         ntfy.sh (e.g. https://ntfy.sh/<your-topic>) or any webhook.
                         Never required — without it, alerts go to the log only.

Log:  /content/logs/train_watchdog.log
Stop: pkill -f train_watchdog.py
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
LOGS = Path("/content/logs")
PY = sys.executable


def _log(msg: str) -> None:
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}"
    print(line, flush=True)
    try:
        LOGS.mkdir(parents=True, exist_ok=True)
        with open(LOGS / "train_watchdog.log", "a") as fh:
            fh.write(line + "\n")
    except OSError:
        pass


def notify(msg: str) -> None:
    """Best-effort push alert; never raises. No-op if WATCHDOG_ALERT_URL unset."""
    url = os.environ.get("WATCHDOG_ALERT_URL", "").strip()
    if not url:
        _log("(no WATCHDOG_ALERT_URL set; alert is log-only)")
        return
    try:
        req = urllib.request.Request(url, data=msg.encode("utf-8"), method="POST",
                                     headers={"Title": "v3 training watchdog",
                                              "Tags": "warning"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            _log(f"alert pushed ({resp.status})")
    except Exception as exc:  # noqa: BLE001 - alerting must never kill the watchdog
        _log(f"alert push FAILED: {exc!r}")


def run_pid(config: Path, run_name: str) -> int | None:
    """The live parent run.py PID from train.pid, or None.

    Keyed off ``train.pid`` (the exact parent train_ctl launched), NOT a /proc
    scan: run.py forks worker children that share its cmdline, so a scan could
    report "alive" from an orphaned child after the parent dies.
    """
    try:
        pid = int((LOGS / "train.pid").read_text().strip())
    except (OSError, ValueError):
        return None
    try:
        state = Path(f"/proc/{pid}/stat").read_text()
    except OSError:
        return None
    after = state.rfind(")")
    if after == -1 or state[after + 2:after + 3] in ("", "Z"):
        return None
    try:
        raw = Path(f"/proc/{pid}/cmdline").read_bytes().decode(errors="replace")
    except OSError:
        return None
    if "run.py" in raw and (str(config) in raw or run_name in raw):
        return pid
    return None


def _proc_has(fragment: str) -> bool:
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        try:
            raw = Path(f"/proc/{entry}/cmdline").read_bytes().decode(errors="replace")
        except OSError:
            continue
        if fragment in raw:
            return True
    return False


def ensure_sidecars(run_name: str) -> None:
    """Restart backup_to_gcp.py / gpu_logger.py if either died. Idempotent."""
    import time as _t
    specs = [
        ("backup_to_gcp.py", ["backup_to_gcp.py", "--run-name", run_name],
         "gcp_backup_stdout.log"),
        ("gpu_logger.py", ["gpu_logger.py", "--out", str(LOGS / "gpu_usage.csv")],
         "gpu_logger_stdout.log"),
    ]
    for script, argv, out in specs:
        if _proc_has(script):
            continue
        _log(f"sidecar {script} is DOWN -> restarting")
        try:
            with open(LOGS / out, "ab") as fh:
                subprocess.Popen([PY, *argv], cwd=str(REPO_ROOT),
                                 stdin=subprocess.DEVNULL, stdout=fh,
                                 stderr=subprocess.STDOUT,
                                 start_new_session=True, close_fds=True)
        except Exception as exc:  # noqa: BLE001
            _log(f"sidecar {script} restart FAILED: {exc!r}")
        _t.sleep(1)


def last_step(train_log: Path, total_steps: int) -> int:
    try:
        text = train_log.read_text(errors="replace")
    except OSError:
        return 0
    hits = re.findall(rf"(\d+)/{total_steps}\b", text)
    return max((int(h) for h in hits), default=0)


def log_tail(train_log: Path, n: int = 120) -> str:
    try:
        return "\n".join(train_log.read_text(errors="replace").splitlines()[-n:])
    except OSError:
        return ""


def deliberate_stop(train_log: Path) -> bool:
    return "Job stopped" in log_tail(train_log, 40)


def relaunch(config: Path) -> None:
    cmd = [PY, str(REPO_ROOT / "train_ctl.py"), "start", "--config", str(config)]
    _log(f"relaunch: {' '.join(cmd)}")
    res = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
    for ln in (res.stdout + res.stderr).strip().splitlines():
        _log(f"  train_ctl: {ln}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Crash-watchdog for a training run.")
    ap.add_argument("--config", default=str(REPO_ROOT / "config" / "v3_arabmaqamrock_lora.yml"))
    ap.add_argument("--interval", type=float, default=30.0)
    ap.add_argument("--max-restarts", type=int, default=6)
    ap.add_argument("--total-steps", type=int, default=5000)
    ap.add_argument("--once", action="store_true", help="run a single poll then exit")
    ap.add_argument("--dry-run", action="store_true", help="log decisions; never relaunch")
    ap.add_argument("--no-sidecars", action="store_true", help="don't touch the sidecars")
    args = ap.parse_args(argv)

    config = Path(args.config).expanduser().resolve()
    run_name = config.stem
    train_log = LOGS / "train.log"

    restarts = 0
    prev_step = last_step(train_log, args.total_steps)
    stall = 0
    _log(f"watchdog up: run='{run_name}' interval={args.interval}s "
         f"max-restarts={args.max_restarts} alert_url={'set' if os.environ.get('WATCHDOG_ALERT_URL') else 'unset'}")

    while True:
        if run_pid(config, run_name):
            step = last_step(train_log, args.total_steps)
            if step > prev_step:
                prev_step, stall = step, 0
            if args.once:
                _log(f"alive; step {step}/{args.total_steps}")
                return 0
            time.sleep(args.interval)
            continue

        step = last_step(train_log, args.total_steps)
        if deliberate_stop(train_log):
            _log(f"not running and 'Job stopped' present -> deliberate stop; exiting (step {step})")
            return 0
        if step >= args.total_steps:
            _log(f"not running; step {step}/{args.total_steps} reached -> complete; exiting")
            return 0

        tail = log_tail(train_log, 60)
        if "out of memory" in tail.lower() or "OutOfMemoryError" in tail:
            cause = f"CRASH: CUDA out of memory at step {step}"
        elif "Traceback" in tail:
            cause = f"CRASH: Python traceback at step {step}"
        else:
            cause = f"CRASH: run.py gone, no 'Job stopped', no completion at step {step}"

        if step <= prev_step:
            stall += 1
        else:
            stall = 0
        prev_step = max(prev_step, step)

        _log(f"detected: {cause}; stall={stall} restarts={restarts}")

        if stall >= 2:
            msg = (f"v3 training UNRECOVERABLE: 2 crashes with no progress at step {step} "
                   f"(likely a track that OOMs every draw). Watchdog stopping. "
                   f"See /content/logs/train_watchdog.log + train.log.")
            _log("ALERT: " + msg)
            notify(msg)
            return 2
        if restarts >= args.max_restarts:
            msg = (f"v3 training: reached max-restarts={args.max_restarts} at step {step}. "
                   f"Watchdog stopping. See /content/logs/train_watchdog.log.")
            _log("ALERT: " + msg)
            notify(msg)
            return 2

        if args.dry_run:
            _log("dry-run: would alert + relaunch now.")
            return 0

        restarts += 1
        notify(f"v3 training crashed at step {step} (attempt {restarts}). "
               f"Auto-restarting from the last checkpoint.")
        if not args.no_sidecars:
            ensure_sidecars(run_name)
        relaunch(config)
        if args.once:
            return 0
        time.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
