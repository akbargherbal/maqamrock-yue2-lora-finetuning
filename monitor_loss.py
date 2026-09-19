#!/usr/bin/env python3
"""
monitor_loss.py
----------------
Read-only inspector for the SQLite metrics db that Ostris AI Toolkit's
`UILogger` writes when a config has `logging.use_ui_logger: true`
(toolkit/logging_aitk.py). This is the ONLY surface with real per-step
metrics -- `aitk_db.db` (the config's `sqlite_db_path`) only ever holds a
job status string and only populates when the Web UI launched the run. See
this repo's DECISIONS.md for why.

The db is opened WAL-mode by the writer, so reading it while training is
actively writing is safe -- this script opens its own read-only connection
and never writes.

Schema (fixed, verified against toolkit/logging_aitk.py):
    steps(step INTEGER PRIMARY KEY, wall_time REAL)
    metric_keys(key TEXT PRIMARY KEY, first_seen_step, last_seen_step)
    metrics(step, key, value_real, value_text)

Usage:
    python monitor_loss.py output/akbar_arabic_rock_lora/loss_log.db
    python monitor_loss.py output/akbar_arabic_rock_lora/loss_log.db --history 50
    python monitor_loss.py output/akbar_arabic_rock_lora/loss_log.db --key nar_flow --history 200
    python monitor_loss.py output/akbar_arabic_rock_lora/loss_log.db --watch 30
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
import time
from pathlib import Path


def connect_readonly(db_path: Path) -> sqlite3.Connection:
    # uri=True + mode=ro: never blocks/competes with the writer's WAL locks,
    # and can never accidentally corrupt the live db.
    return sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=5.0)


def latest_step(con: sqlite3.Connection) -> tuple[int, float] | None:
    row = con.execute(
        "SELECT step, wall_time FROM steps ORDER BY step DESC LIMIT 1"
    ).fetchone()
    return tuple(row) if row else None


def metrics_at_step(con: sqlite3.Connection, step: int) -> dict[str, float | str]:
    rows = con.execute(
        "SELECT key, value_real, value_text FROM metrics WHERE step = ?", (step,)
    ).fetchall()
    out = {}
    for key, vr, vt in rows:
        out[key] = vr if vr is not None else vt
    return out


def rate_estimate(con: sqlite3.Connection, window: int = 50) -> float | None:
    """Steps/second over the last `window` recorded steps (not necessarily
    contiguous -- steps only get a row when logging.log_every fires)."""
    rows = con.execute(
        "SELECT step, wall_time FROM steps ORDER BY step DESC LIMIT ?", (window,)
    ).fetchall()
    if len(rows) < 2:
        return None
    (newest_step, newest_t) = rows[0]
    (oldest_step, oldest_t) = rows[-1]
    dt = newest_t - oldest_t
    dstep = newest_step - oldest_step
    if dt <= 0 or dstep <= 0:
        return None
    return dstep / dt


def history(con: sqlite3.Connection, key: str, n: int) -> list[tuple[int, float]]:
    rows = con.execute(
        "SELECT step, value_real FROM metrics WHERE key = ? "
        "AND value_real IS NOT NULL ORDER BY step DESC LIMIT ?",
        (key, n),
    ).fetchall()
    return list(reversed(rows))


def list_keys(con: sqlite3.Connection) -> list[str]:
    rows = con.execute(
        "SELECT key FROM metric_keys ORDER BY key"
    ).fetchall()
    return [r[0] for r in rows]


def report(db_path: Path, args: argparse.Namespace) -> bool:
    if not db_path.exists():
        print(f"[not found] {db_path} -- has the run started yet? "
              f"(only created once logging.use_ui_logger fires its first commit)")
        return False

    con = connect_readonly(db_path)
    try:
        latest = latest_step(con)
        if latest is None:
            print(f"[empty] {db_path} exists but has no steps committed yet.")
            return False

        step, wall_time = latest
        keys = list_keys(con)
        vals = metrics_at_step(con, step)
        rate = rate_estimate(con, window=args.rate_window)

        print(f"step {step}  (db: {db_path})")
        for k in keys:
            if k in vals:
                v = vals[k]
                print(f"  {k}: {v:.6f}" if isinstance(v, float) else f"  {k}: {v}")
        if rate:
            print(f"  ~{rate:.3f} steps/sec (last {args.rate_window} recorded steps)")
            if args.total_steps:
                remaining = max(args.total_steps - step, 0)
                eta_sec = remaining / rate if rate > 0 else float("inf")
                print(f"  ETA to step {args.total_steps}: ~{eta_sec / 60:.1f} min")

        if args.key:
            hist = history(con, args.key, args.history)
            if hist:
                print(f"\n  last {len(hist)} recorded values for '{args.key}':")
                for s, v in hist:
                    print(f"    step {s}: {v:.6f}")
            else:
                print(f"\n  no numeric history for key '{args.key}' "
                      f"(known keys: {', '.join(keys)})")
        return True
    finally:
        con.close()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("db_path", type=Path, help="Path to loss_log.db")
    ap.add_argument("--key", default=None, help="Show recent history for one metric key")
    ap.add_argument("--history", type=int, default=20, help="How many recent values to show for --key")
    ap.add_argument("--rate-window", type=int, default=50, help="Steps to average the rate/ETA over")
    ap.add_argument("--total-steps", type=int, default=None, help="train.steps from the config, for an ETA")
    ap.add_argument("--watch", type=float, default=None, help="Re-poll every N seconds instead of running once")
    args = ap.parse_args()

    if args.watch:
        try:
            while True:
                print(f"--- {time.strftime('%Y-%m-%d %H:%M:%S')} ---")
                report(args.db_path, args)
                print()
                time.sleep(args.watch)
        except KeyboardInterrupt:
            return 0
    else:
        return 0 if report(args.db_path, args) else 1


if __name__ == "__main__":
    sys.exit(main())
