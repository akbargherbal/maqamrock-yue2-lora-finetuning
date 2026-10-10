#!/usr/bin/env python3
"""Agent-side sanity monitor (the second layer on top of train_watchdog.py).

Reads the training + watchdog logs every --interval seconds and logs a
heartbeat. It EXITS (so the launching agent is notified and can act) as soon as
it sees something that needs a human/agent:

  * the process watchdog gave up ("ALERT:" in train_watchdog.log),
  * the process watchdog is no longer running (supervisor died),
  * a deliberate stop ("Job stopped" in train.log),
  * run completion (reached --total-steps).

It does NOT restart anything — train_watchdog.py owns that. This only watches
the watcher and reports.

Usage:
    python agent_watch.py [--interval 600] [--max-checks 21] [--total-steps 5000]

Log: /content/logs/agent_watch.log
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
from pathlib import Path

LOGS = Path("/content/logs")
WATCHDOG_LOG = LOGS / "train_watchdog.log"
TRAIN_LOG = LOGS / "train.log"
OUT = LOGS / "agent_watch.log"


def log(msg: str) -> None:
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}"
    print(line, flush=True)
    try:
        LOGS.mkdir(parents=True, exist_ok=True)
        with open(OUT, "a") as fh:
            fh.write(line + "\n")
    except OSError:
        pass


def watchdog_pid() -> int | None:
    """PID of a running train_watchdog.py (via /proc; excludes this script)."""
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        try:
            raw = Path(f"/proc/{entry}/cmdline").read_bytes().decode(errors="replace")
        except OSError:
            continue
        if "train_watchdog.py" in raw and "agent_watch.py" not in raw:
            return int(entry)
    return None


def tail(path: Path, n: int) -> str:
    try:
        return "\n".join(path.read_text(errors="replace").splitlines()[-n:])
    except OSError:
        return ""


def step(total: int) -> int:
    try:
        text = TRAIN_LOG.read_text(errors="replace")
    except OSError:
        return 0
    hits = re.findall(rf"(\d+)/{total}\b", text)
    return max((int(h) for h in hits), default=0)


def crash_count() -> int:
    """How many crash events the process watchdog has logged so far."""
    try:
        return WATCHDOG_LOG.read_text(errors="replace").count("detected: CRASH")
    except OSError:
        return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Agent-side sanity monitor.")
    ap.add_argument("--interval", type=float, default=600.0)
    ap.add_argument("--max-checks", type=int, default=21)
    ap.add_argument("--total-steps", type=int, default=5000)
    args = ap.parse_args(argv)

    log(f"agent_watch up: interval={args.interval}s max-checks={args.max_checks} "
        f"total-steps={args.total_steps}")
    crashes0 = crash_count()
    log(f"baseline crash-count={crashes0}")
    for i in range(1, args.max_checks + 1):
        time.sleep(args.interval)
        wd = watchdog_pid()
        st = step(args.total_steps)
        crashes = crash_count()
        alert = "ALERT:" in tail(WATCHDOG_LOG, 6)
        stopped = "Job stopped" in tail(TRAIN_LOG, 40)
        log(f"[{i}] step={st}/{args.total_steps} watchdog_pid={wd} crashes={crashes} "
            f"alert={alert} job_stopped={stopped}")

        reason = None
        if st >= args.total_steps:
            reason = f"COMPLETE: reached step {st}/{args.total_steps}"
        elif alert:
            reason = "WATCHDOG ALERT: it gave up (unrecoverable crash). See train_watchdog.log."
        elif wd is None:
            reason = "WATCHDOG GONE: no train_watchdog.py running (supervisor died)."
        elif stopped:
            reason = "DELIBERATE STOP detected in train.log."
        elif crashes > crashes0:
            reason = (f"CRASH: watchdog logged {crashes - crashes0} new crash(es); "
                      f"now at step {st}/{args.total_steps}. Inspect train.log.")
        if reason:
            log(f"EXIT -> {reason}")
            print(f"AGENT MONITOR EXIT: {reason}")
            return 0

    log(f"reached max-checks={args.max_checks} window; exiting (run still in progress).")
    print("AGENT MONITOR EXIT: check window elapsed; run still in progress.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
