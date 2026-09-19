#!/usr/bin/env python3
"""
gpu_logger.py
--------------
AI Toolkit logs no GPU utilization/memory/temperature/power anywhere
(verified against extensions_built_in/sd_trainer/DiffusionTrainer.py and the
base trainer -- see DECISIONS.md). `performance_log_every` only times named
code sections, not hardware. This script is the actual source of that data:
polls `nvidia-smi` on a fixed interval and appends plain CSV rows an agent
(or pandas) can read directly, correlated against loss_log.db's wall_time.

Usage:
    python gpu_logger.py --out /content/logs/gpu_usage.csv
    python gpu_logger.py --out /content/logs/gpu_usage.csv --interval-seconds 10
"""

from __future__ import annotations

import argparse
import csv
import shutil
import subprocess
import sys
import time
from pathlib import Path

FIELDS = [
    "timestamp",
    "gpu_util_pct",
    "mem_used_mib",
    "mem_total_mib",
    "temp_c",
    "power_draw_w",
]

QUERY = "utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw"


def poll(nvidia_smi: str) -> list[str] | None:
    result = subprocess.run(
        [nvidia_smi, f"--query-gpu={QUERY}", "--format=csv,noheader,nounits"],
        capture_output=True, text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return None
    # First GPU only; multi-GPU Colab instances aren't in scope here.
    first_line = result.stdout.strip().splitlines()[0]
    parts = [p.strip() for p in first_line.split(",")]
    if len(parts) != 5:
        return None
    return parts


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True, type=Path, help="CSV file to append to")
    ap.add_argument("--interval-seconds", type=float, default=10.0)
    ap.add_argument("--nvidia-smi", default="nvidia-smi")
    args = ap.parse_args()

    nvidia_smi = shutil.which(args.nvidia_smi)
    if not nvidia_smi:
        print(f"[FAIL] '{args.nvidia_smi}' not found on PATH", file=sys.stderr)
        return 2

    args.out.parent.mkdir(parents=True, exist_ok=True)
    write_header = not args.out.exists() or args.out.stat().st_size == 0

    with open(args.out, "a", newline="") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(FIELDS)
            f.flush()

        print(f"logging GPU stats to {args.out} every {args.interval_seconds}s "
              f"(ctrl-c to stop)")
        try:
            while True:
                parts = poll(nvidia_smi)
                if parts is None:
                    print("[warn] nvidia-smi query failed or returned nothing this poll")
                else:
                    row = [time.strftime("%Y-%m-%d %H:%M:%S"), *parts]
                    writer.writerow(row)
                    f.flush()
                time.sleep(args.interval_seconds)
        except KeyboardInterrupt:
            return 0


if __name__ == "__main__":
    sys.exit(main())
