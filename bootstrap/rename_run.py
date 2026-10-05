#!/usr/bin/env python3
"""Rename an ai-toolkit run end-to-end: config, local output, GCS prefix.

Why a script (the parts that bite): ai-toolkit derives everything from `config.name` --
  save_root      = training_folder / name                 `BaseTrainProcess.py:45`
  ckpt filename  = f"{name}_{step:09d}.safetensors"       `BaseSDTrainProcess.py:524`
  resume         = newest-by-CTIME file matching "{name}*.safetensors" in save_root
                   (`BaseSDTrainProcess.py:826-865`) -- NOT by step number.
So a rename must change the config, move the output dir, rename every checkpoint
prefix, AND restore ctime order (touch in ascending step) or resume picks the wrong
file. `optimizer.pt` is name-independent; `training_info` stores only step/epoch.

Safe by default: DRY-RUN unless `--apply`, and it refuses to `--apply` while a
`run.py` for `--old` is alive (override with `--force`). GCS is copy-then-verify-then
-delete (server-side). Run it with training STOPPED.

    python bootstrap/rename_run.py --old quran_ahh_r8 --new quran_ahh_r32                 # dry-run
    python bootstrap/rename_run.py --old quran_ahh_r8 --new quran_ahh_r32 --apply         # do it
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


def run(cmd: list[str], dry: bool) -> None:
    print(("  DRY " if dry else "  RUN ") + " ".join(str(c) for c in cmd))
    if not dry:
        subprocess.run([str(c) for c in cmd], check=True)


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--old", required=True, help="current run name (config name + dir + ckpt prefix)")
    ap.add_argument("--new", required=True, help="new run name")
    ap.add_argument("--config-dir", default=str(REPO / "config"), help="where <name>.yml lives")
    ap.add_argument("--output-root", default="/content/ai-toolkit/output",
                    help="ai-toolkit training_folder")
    ap.add_argument("--gcs-base", default=os.environ.get("GCP_BACKUP_BASE", "").rstrip("/"),
                    help="GCS base prefix (default $GCP_BACKUP_BASE); blank = skip GCS")
    ap.add_argument("--adapters-prefix", default=None,
                    help="extra GCS prefix whose convert/ should merge into <new>/convert "
                         "(default: <old>_rank32)")
    ap.add_argument("--apply", action="store_true", help="actually do it (default: dry-run)")
    ap.add_argument("--force", action="store_true", help="skip the run.py-alive guard")
    return ap.parse_args()


def main() -> int:
    a = parse_args()
    dry = not a.apply
    old, new = a.old, a.new
    if old == new:
        sys.exit("old and new are identical")
    config_dir = Path(a.config_dir)
    out_root = Path(a.output_root)
    old_dir, new_dir = out_root / old, out_root / new
    old_cfg, new_cfg = config_dir / f"{old}.yml", config_dir / f"{new}.yml"
    gcs = a.gcs_base
    adapters = a.adapters_prefix if a.adapters_prefix is not None else f"{old}_rank32"

    print(f"rename {old!r} -> {new!r}   ({'APPLY' if not dry else 'DRY-RUN'})\n")

    # 0. guard -- never touch a live run (match the config path, not our own argv)
    alive = subprocess.run(["pgrep", "-af", rf"run\.py\s+\S*/config/{re.escape(old)}\.yml"],
                           capture_output=True, text=True)
    if alive.stdout.strip():
        if a.apply and not a.force:
            sys.exit("refusing: a run.py for %s is alive:\n%s" % (old, alive.stdout.strip()))
        print(f"WARNING: run.py for {old} looks alive (ok for dry-run; --apply needs --force):")
        print(alive.stdout.rstrip() + "\n")
    side = subprocess.run(["pgrep", "-af", f"backup_to_gcp.py --run-name {old}"],
                          capture_output=True, text=True)
    if side.stdout.strip():
        print("NOTE: backup sidecar still on the OLD name -- stop it before --apply:")
        print(side.stdout.rstrip() + "\n")

    # 1. local output dir: move dir, rename ckpt prefixes, restore ctime order
    if old_dir.exists():
        if new_dir.exists():
            sys.exit(f"refusing: {new_dir} already exists")
        print(f"[local] {old_dir} -> {new_dir}")
        run(["mv", str(old_dir), str(new_dir)], dry)
        scan = old_dir if dry else new_dir  # dry-run: files are still in the old dir
        ckpts = []
        for f in scan.glob(f"{old}*.safetensors"):
            m = re.search(r"_(\d{9})\.safetensors$", f.name)
            ckpts.append((int(m.group(1)) if m else 10**10, f))  # un-suffixed final last
        for _, f in sorted(ckpts):
            nf = f.with_name(new + f.name[len(old):])
            run(["mv", str(f), str(nf)], dry)
            if not dry:
                time.sleep(0.05)  # ctime granularity is ~1 ms; force distinct, ascending
            run(["touch", str(nf)], dry)
        print(f"  ({len(ckpts)} checkpoint(s) renamed)")
        if not dry and ckpts:
            # the whole rename hinges on resume picking the newest-by-CTIME file; verify it
            def step_of(p: Path) -> int:
                m = re.search(r"_(\d{9})\.safetensors$", p.name)
                return int(m.group(1)) if m else 10**10
            cands = list(new_dir.glob(f"{new}*.safetensors"))
            expected = max(cands, key=step_of)
            chosen = max(cands, key=os.path.getctime)
            print(f"  ctime check: resume will pick {chosen.name} (want {expected.name})")
            if chosen != expected:
                sys.exit("ERROR: ctime ordering wrong after rename -- do NOT resume; re-run to fix")
    else:
        print(f"[local] {old_dir} absent -- nothing to move (fine on a fresh VM)")

    # 2. config file: new name + log_dir, then drop the old file
    if old_cfg.exists():
        text = old_cfg.read_text()
        text = re.sub(r'(name:\s*")' + re.escape(old) + r'(")', r"\g<1>" + new + r"\g<2>", text)
        text = text.replace(f"output/{old}/", f"output/{new}/")
        print(f"[config] {old_cfg.name} -> {new_cfg.name} (name + log_dir)")
        if dry:
            run(["write", str(new_cfg)], dry)
        else:
            new_cfg.write_text(text)
            print(f"  wrote {new_cfg}")
        run(["rm", str(old_cfg)], dry)
    else:
        print(f"[config] {old_cfg} absent -- nothing to rename")

    # 3. GCS: copy prefix, verify object sets, then delete old
    if gcs:
        def rel_objects(prefix: str) -> set[str]:
            r = subprocess.run(["gcloud", "storage", "ls", "-r", prefix],
                               capture_output=True, text=True)
            out = set()
            for line in r.stdout.splitlines():
                line = line.strip()
                if line.startswith("gs://") and not line.endswith(":"):
                    out.add(line[len(prefix):].lstrip("/"))
            return out

        existing = subprocess.run(["gcloud", "storage", "ls", f"{gcs}/{new}/"],
                                  capture_output=True, text=True)
        if existing.returncode == 0 and existing.stdout.strip():
            sys.exit(f"refusing: GCS prefix {gcs}/{new}/ already has objects")
        run(["gcloud", "storage", "rsync", "-r", f"{gcs}/{old}", f"{gcs}/{new}"], dry)
        if adapters:
            ada = subprocess.run(["gcloud", "storage", "ls", f"{gcs}/{adapters}/"],
                                 capture_output=True, text=True)
            if ada.returncode == 0 and ada.stdout.strip():
                run(["gcloud", "storage", "rsync", "-r",
                     f"{gcs}/{adapters}/convert", f"{gcs}/{new}/convert"], dry)
                run(["gcloud", "storage", "rm", "-r", f"{gcs}/{adapters}"], dry)
            else:
                print(f"[gcs] adapters prefix {gcs}/{adapters}/ absent -- skipped")
        if not dry:
            old_set, new_set = rel_objects(f"{gcs}/{old}/"), rel_objects(f"{gcs}/{new}/")
            missing = old_set - new_set
            print(f"  GCS objects: old={len(old_set)} new={len(new_set)} missing={len(missing)}")
            if missing:
                sys.exit(f"ERROR: GCS copy incomplete ({sorted(missing)[:5]}) -- old prefix NOT deleted")
        run(["gcloud", "storage", "rm", "-r", f"{gcs}/{old}"], dry)
    else:
        print("[gcs] GCP_BACKUP_BASE unset -- skipped")

    print("\nEpilogue (do these after a successful --apply):")
    print(f"  # restart the backup sidecar on the new name")
    print(f"  setsid nohup python backup_to_gcp.py --run-name {new} "
          f"> /content/logs/gcp_backup.log 2>&1 & disown")
    print(f"  # resume (same config body, new name) and confirm a 'Found step' line:")
    print(f"  python train_ctl.py start --config {new_cfg} --run-name {new} --log-name train_quran_ahh")
    print(f"  grep -m1 'Found step' /content/logs/train_quran_ahh.log")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
