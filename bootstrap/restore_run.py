#!/usr/bin/env python3
"""Restore a training run's output from GCS and restore resume ctime order.

ai-toolkit resumes from ``max(glob("<run>*.safetensors"), key=os.path.getctime)``
-- **ctime, not the step number** (``BaseSDTrainProcess.get_latest_save_path``). A
GCS restore (``gcloud storage rsync``) recreates every file at ~the restore
instant, so the ctimes collapse and the "newest" pick is arbitrary. Observed: a
restore of ``_1500.._19500`` resumed from ``_000009000``, silently rewinding
~10,500 steps (and would overwrite newer saves).

This does the whole restore in the safe order: rsync
``<base>/<run-name>/output`` -> ``<output-root>/<run-name>``, then re-stamp the
checkpoints' ctime in ascending step order and VERIFY that ``getctime`` selects
the newest. Run it **before** ``train_ctl.py start``; never while ``run.py`` is
alive. Mirrors the ctime logic in ``bootstrap/rename_run.py``.

    python bootstrap/restore_run.py --run-name quran_ahh_r32             # dry-run
    python bootstrap/restore_run.py --run-name quran_ahh_r32 --apply
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CKPT_RE = re.compile(r"_(\d{9})\.safetensors$")


def step_of(path: Path) -> int:
    """Sort key: the step number; the un-suffixed final adapter sorts highest."""
    m = CKPT_RE.search(path.name)
    return int(m.group(1)) if m else 10**10


def restamp_ctime_order(dest: Path, run_name: str, sleep: float = 0.02) -> bool:
    """Re-stamp checkpoints in ascending step order so getctime picks the newest.

    ``os.utime`` (like ``touch``) bumps ctime on this filesystem -- verified. The
    sleep forces distinct, ascending ctimes. Returns True iff the newest-by-ctime
    is the expected (highest-step / final) checkpoint.
    """
    ckpts = sorted(dest.glob(f"{run_name}*.safetensors"), key=step_of)
    for f in ckpts:
        os.utime(f, None)
        time.sleep(sleep)
    if not ckpts:
        return True
    expected = max(ckpts, key=step_of)
    chosen = max(ckpts, key=os.path.getctime)
    print(f"  {len(ckpts)} checkpoints; resume will pick {chosen.name} "
          f"(want {expected.name})")
    return chosen == expected


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description=__doc__.split("\n\n")[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--run-name", required=True,
                    help="run name (config name + output folder + ckpt prefix)")
    ap.add_argument("--base", default=os.environ.get("GCP_BACKUP_BASE", "").rstrip("/"),
                    help="GCS base (default: $GCP_BACKUP_BASE)")
    ap.add_argument("--output-root", default="/content/ai-toolkit/output",
                    help="local training output root (default: /content/ai-toolkit/output)")
    ap.add_argument("--gsutil", default="gcloud",
                    help="'gcloud' (gcloud storage rsync) or 'gsutil'")
    ap.add_argument("--apply", action="store_true",
                    help="actually rsync + restamp (default: dry-run)")
    ap.add_argument("--force", action="store_true",
                    help="skip the run.py-alive guard")
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    if not args.base:
        sys.exit("no GCS base: set GCP_BACKUP_BASE or pass --base")
    dest = Path(args.output_root) / args.run_name
    src = f"{args.base}/{args.run_name}/output"

    # Match ai-toolkit's `run.py` but not this script (`restore_run.py`): require a
    # space or slash before `run.py`, which the literal string "restore_run.py" has not.
    alive = subprocess.run(["pgrep", "-af", "[ /]run\\.py"], capture_output=True,
                           text=True).stdout.strip()
    if alive and not args.force:
        sys.exit("refusing: run.py looks alive (restore only when stopped):\n" + alive)

    print(f"[restore] {src}\n       -> {dest}")
    if not args.apply:
        print("dry-run: add --apply to perform it")
        return 0

    dest.mkdir(parents=True, exist_ok=True)  # rsync needs the destination to exist
    if Path(args.gsutil).name == "gsutil":
        cmd = [args.gsutil, "-m", "rsync", "-r", src, str(dest)]
    else:
        cmd = [args.gsutil, "storage", "rsync", "-r", src, str(dest)]
    print("[restore] " + " ".join(cmd))
    subprocess.run(cmd, check=True)

    if not restamp_ctime_order(dest, args.run_name):
        sys.exit("ERROR: ctime order wrong after restore -- do NOT resume; re-run to fix")
    print("[restore] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
