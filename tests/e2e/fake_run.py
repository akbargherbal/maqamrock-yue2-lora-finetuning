#!/usr/bin/env python3
"""A stand-in for ai-toolkit's `run.py` (plan §2/§8), for the T3 lifecycle e2e.

`train_ctl.py` launches `python run.py <config> -l <log>` detached. Real
ai-toolkit needs torch + a GPU at import, so on the CPU tier this fake stands in:
it is a **real process** that

  * writes a real `loss_log.db` (the UILogger schema `monitor_loss.py` reads) as
    it "trains", in its cwd (the ai-toolkit checkout train_ctl was pointed at),
  * appends step lines to the `-l` train log,
  * reacts to SIGINT the way ai-toolkit does: writes `Job stopped` and exits 0,
    which is exactly what `train_ctl.py stop` waits for.

No GPU, no torch, no /content.
"""
from __future__ import annotations

import os
import signal
import sqlite3
import sys
import time

SCHEMA = """
CREATE TABLE IF NOT EXISTS steps(step INTEGER PRIMARY KEY, wall_time REAL);
CREATE TABLE IF NOT EXISTS metric_keys(key TEXT PRIMARY KEY,
    first_seen_step INTEGER, last_seen_step INTEGER);
CREATE TABLE IF NOT EXISTS metrics(step INTEGER, key TEXT, value_real REAL, value_text TEXT);
"""


def _arg(flag: str, default: str) -> str:
    return sys.argv[sys.argv.index(flag) + 1] if flag in sys.argv else default


def main() -> int:
    log = _arg("-l", "train.log")
    db = os.environ.get("FAKE_RUN_DB", os.path.join(os.getcwd(), "loss_log.db"))
    step_seconds = float(os.environ.get("FAKE_RUN_STEP_SECONDS", "0.05"))

    stop = {"requested": False}

    def handler(_sig, _frm):
        stop["requested"] = True

    signal.signal(signal.SIGINT, handler)

    con = sqlite3.connect(db, timeout=5.0)
    con.executescript(SCHEMA)
    con.commit()

    with open(log, "a", encoding="utf-8") as fh:
        fh.write(f"fake_run: started (db={db})\n")
        fh.flush()

    t0 = time.time()
    step = 0
    while not stop["requested"]:
        step += 1
        wall = time.time() - t0
        con.execute("INSERT OR REPLACE INTO steps VALUES(?, ?)", (step, wall))
        for key, value in (("loss", 1.0 / step), ("nar_flow", 0.42)):
            con.execute("INSERT OR REPLACE INTO metrics VALUES(?, ?, ?, NULL)",
                        (step, key, value))
            con.execute("INSERT OR REPLACE INTO metric_keys VALUES(?, ?, ?)",
                        (key, 1, step))
        con.commit()
        if step % 5 == 0:
            with open(log, "a", encoding="utf-8") as fh:
                fh.write(f"step {step} loss {1.0 / step:.4f}\n")
        time.sleep(step_seconds)

    with open(log, "a", encoding="utf-8") as fh:
        fh.write("Job stopped\n")
    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
