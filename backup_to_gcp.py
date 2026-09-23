#!/usr/bin/env python3
"""Mirror the high-stake run artifacts to GCS on a timer.

Adapted from the arabic-suno-lora-finetuning (FL-YuE2) project's script of
the same name. The core loop, manifest logic, and CLI surface are unchanged;
what changed is WHERE things live, because Ostris AI Toolkit's output layout
is structurally different from FL-YuE2's:

- FL-YuE2 (ComfyUI): adapters, run state, and prep caches lived in three
  separate roots (ComfyUI/models/loras, ComfyUI/output/yue2_training, plus
  ComfyUI's own dataset-prep cache).
- Ostris (this project): everything for one job -- checkpoints, config.yaml,
  samples, and loss_log.db (the real metrics db, see DECISIONS.md) -- lands
  together under one `training_folder/<job_name>/` folder. That's a
  simplification: one TARGET entry covers what used to take three.

Run this in a second terminal next to training: it mirrors only the folders
needed to resume or debug the run up to a GCS prefix with `gsutil rsync`.

rsync is append/update-only here (no `-d`): nothing is ever deleted on the
remote side. If a pass catches a checkpoint mid-write, the next pass
re-uploads it once the local file stops changing, so a torn upload
self-heals.

Every run gets its own subfolder -- `<base>/<run-name>/` -- under one generic
root, so a new run can never overwrite a previous one and the bucket root
stays fixed. `--run-name` defaults per mode (see below) and a
`run_manifest.json` is written at the run folder's root so it identifies
itself. `dataset/` already lives under the root and is reserved.

Two modes, mirroring bootstrap/setup.sh's own --training/--inference split:

  training (default)  the run's training output + logs + agent_notes under
                      <base>/<run-name>/ (default run-name akbar_arabic_rock_lora).
  --inference         the audio.cpp inference workspace under
                      <base>/audiocpp_inference/ (out, prompts, scripts, the
                      converted LoRA) + logs + agent_notes. See INFERENCE_TARGETS.

`--watch LOCAL[:SUB]` (repeatable) replaces the mode's targets with exactly the
folders you name -- for mirroring an arbitrary location such as
`/content/my_songs`. Every watch lands under `<base>/<run-name>/`, with `SUB`
(or the prefix root for a single watch) as the remote subfolder.

`--extra LOCAL[:SUB]` (repeatable) ADDS folders on top of whatever the target
set already is (the mode's defaults, or the `--watch` list). Its remote
subfolder defaults to the folder's basename.

Usage:
    python backup_to_gcp.py --run-name akbar_arabic_rock_lora
    python backup_to_gcp.py --run-name akbar_arabic_rock_lora --interval-minutes 15
    python backup_to_gcp.py --run-name akbar_arabic_rock_lora --once
    python backup_to_gcp.py --run-name akbar_arabic_rock_lora --dry-run
    python backup_to_gcp.py --inference
    python backup_to_gcp.py --inference --once

    # watch a specific folder instead of the mode's default targets
    python backup_to_gcp.py --watch /content/my_songs --run-name my_songs
    python backup_to_gcp.py --watch /content/my_songs:wavs --watch /content/notes:misc

    # keep the default targets AND add one folder
    python backup_to_gcp.py --run-name akbar_arabic_rock_lora --extra /content/my_songs
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
# The GCS base is supplied at runtime, like the API keys: the launching
# notebook exports GCP_BACKUP_BASE, so no bucket- or account-specific value is
# stored in this repo. Override per invocation with --base. Format:
# gs://<bucket>/<project-prefix>.
DEFAULT_BASE = os.environ.get("GCP_BACKUP_BASE", "")
# Non-run folders that already live under the base; never use as a run name.
RESERVED_SUBFOLDERS = {"dataset"}
DEFAULT_LOG = Path("/content/logs/gcp_backup.log")

# Ostris AI Toolkit output layout (this project's config):
#   training_folder = /content/ai-toolkit/output  (config: training_folder)
#   everything for THIS job lives at training_folder/akbar_arabic_rock_lora/:
#     checkpoints (save.save_format/save_every), config.yaml (auto-saved),
#     sample previews, loss_log.db (metrics -- see DECISIONS.md), and the
#     tensorboard/<job>_<timestamp>/ subfolder if log_dir is set.
# This is a real structural difference from FL-YuE2's three-way split; one
# TARGET now covers what used to need LORA_ROOT + RUN_ROOT separately.
JOB_NAME = "akbar_arabic_rock_lora"
TRAINING_FOLDER = Path("/content/ai-toolkit/output")
JOB_ROOT = TRAINING_FOLDER / JOB_NAME

# Inference workspace (bootstrap/setup.sh --inference). Not a numbered run but a
# standing work area, and the one the agent actually drives audiocpp_cli from;
# it must survive the VM like a training run does. Local layout:
#   out/       generated wavs + per-run .log/_time.txt/_gpu.csv/_runs_status.log
#   prompts/   the Maqam <style,lyrics> pairs the runs are driven from
#   scripts/   duration_cap.py etc.
#   ../converter/out/  the converted step-3000 LoRA (.safetensors) + converter
#                      scripts -- expensive to regenerate, so mirrored too.
# Deliberately NOT backed up (reproducible, not precious):
#   models/    multi-GB GGUFs; setup.sh re-downloads them from HF
#   bin/       prebuilt audiocpp_cli; already GCS-resident under .../build/
INFERENCE_ROOT = Path("/content/audiocpp_inference")
INFERENCE_RUN_NAME = "audiocpp_inference"
LORA_LOCAL = Path("/content/converter/out")

# (source folder, remote subfolder, wait for writes to settle before syncing)
TRAINING_TARGETS = [
    (JOB_ROOT, "output", True),
    (Path("/content/logs"), "logs", False),
    (REPO_ROOT / "agent_notes", "agent_notes", False),
]
INFERENCE_TARGETS = [
    (INFERENCE_ROOT / "out", "out", False),
    (INFERENCE_ROOT / "prompts", "prompts", False),
    (INFERENCE_ROOT / "scripts", "scripts", False),
    (LORA_LOCAL, "converter", False),
    (Path("/content/logs"), "logs", False),
    (REPO_ROOT / "agent_notes", "agent_notes", False),
]
DEFAULT_EXCLUDES = [r".*\.tmp$"]
# loss_log.db (WAL mode) is ALWAYS being written to during an active run --
# same reasoning as FL-YuE2's old exclusion of its per-job jobs/*.log
# subtree, different filename. Real state (checkpoints, config.yaml,
# samples) is written atomically (temp + os.replace equivalents) and is safe
# to gate the settle wait on; the metrics db must not be allowed to starve
# every sync just because it's perpetually "recently touched."
SETTLE_IGNORE_NAMES = {"loss_log.db", "loss_log.db-wal", "loss_log.db-shm"}


def parse_watch_specs(specs: list[str]) -> list[tuple[Path, str]]:
    """`LOCAL` or `LOCAL:SUB` -> (expanded local path, remote subfolder).

    SUB defaults to "" (the run prefix root). A local path containing ':' is
    pathological on Linux, so a single split is unambiguous here.
    """
    out: list[tuple[Path, str]] = []
    for spec in specs:
        local, sub = spec.split(":", 1) if ":" in spec else (spec, "")
        out.append((Path(local).expanduser(), sub.strip("/")))
    return out


def run_name_from_path(path: Path) -> str:
    """A GCS-safe run name derived from a watched folder's basename."""
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", path.name).strip("-")
    return name or "watch"


def parse_extra_specs(specs: list[str]) -> list[tuple[Path, str]]:
    """`LOCAL` or `LOCAL:SUB` -> (expanded path, subfolder) for targets ADDED
    on top of the current set. With no `:SUB` the folder's basename is used;
    `LOCAL:` (explicit empty SUB) mirrors at the prefix root."""
    out: list[tuple[Path, str]] = []
    for spec in specs:
        local, sub = spec.split(":", 1) if ":" in spec else (spec, None)
        path = Path(local).expanduser()
        out.append((path, run_name_from_path(path) if sub is None else sub.strip("/")))
    return out


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument(
        "--run-name",
        default=None,
        help="This run's subfolder under <base>. Defaults to "
             f"{JOB_NAME!r} in training mode and {INFERENCE_RUN_NAME!r} with "
             "--inference.",
    )
    p.add_argument(
        "--inference",
        action="store_true",
        help="Back up the audio.cpp inference workspace instead of the training "
             "run (targets INFERENCE_TARGETS).",
    )
    p.add_argument(
        "--watch",
        action="append",
        default=None,
        metavar="LOCAL[:SUB]",
        help="Mirror this local folder (repeatable) INSTEAD of the mode's default "
             "targets -- DROPS the defaults (checkpoints/logs/agent_notes); use "
             "--extra to keep them. LOCAL is ~-expanded; SUB is the remote "
             "subfolder under <base>/<run-name>/ and defaults to the prefix root "
             "for a single --watch (give an explicit :SUB for each when watching "
             "several). With no --run-name the run name is derived from the "
             "first folder.",
    )
    p.add_argument(
        "--extra",
        action="append",
        default=None,
        metavar="LOCAL[:SUB]",
        help="ADD this local folder (repeatable) on top of the current targets "
             "(the mode's defaults, or the --watch list) -- unlike --watch, the "
             "defaults are kept. SUB defaults to the folder's basename; LOCAL: "
             "(empty SUB) mirrors at the prefix root.",
    )
    p.add_argument(
        "--base",
        default=None,
        help="GCS root to mirror into (gs://<bucket>/<project-prefix>). Defaults "
             "to $GCP_BACKUP_BASE, which the launching notebook exports; it is "
             "required if that is unset.",
    )
    p.add_argument(
        "--interval-minutes",
        type=float,
        default=15.0,
        help="Minutes between passes (default: 15)",
    )
    p.add_argument(
        "--once", action="store_true", help="Run one pass and exit (for cron)."
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Log the sync commands but upload nothing.",
    )
    p.add_argument(
        "--settle-seconds",
        type=float,
        default=60.0,
        help="For checkpoint folders, wait until the newest file is this old before syncing (default: 60).",
    )
    p.add_argument("--gsutil", default="gsutil", help="gsutil executable to use.")
    p.add_argument(
        "--log-file",
        default=str(DEFAULT_LOG),
        help=f"Log file (default: {DEFAULT_LOG})",
    )
    p.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Extra gsutil -x regex to exclude (repeatable).",
    )
    return p.parse_args()


def setup_logging(log_file: str) -> logging.Logger:
    logger = logging.getLogger("gcp_backup")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    fmt = logging.Formatter(
        "%(asctime)s %(levelname)s %(message)s", "%Y-%m-%d %H:%M:%S"
    )
    stream = logging.StreamHandler(sys.stdout)
    stream.setFormatter(fmt)
    logger.addHandler(stream)
    path = Path(log_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(path, encoding="utf-8")
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)
    return logger


def wait_for_settle(folder: Path, seconds: float, logger: logging.Logger) -> None:
    """Block until the newest file in `folder` (ignoring loss_log.db and its
    WAL sidecars, which are perpetually fresh during an active run) has been
    untouched for `seconds`."""
    if seconds <= 0:
        return
    while True:
        newest = max(
            (p.stat().st_mtime for p in folder.rglob("*")
             if p.is_file() and p.name not in SETTLE_IGNORE_NAMES),
            default=0.0,
        )
        age = time.time() - newest
        if age >= seconds:
            return
        wait = min(seconds - age, 5.0)
        logger.info(
            "%s: newest file is %.0fs old, waiting %.0fs for the write to finish",
            folder.name,
            age,
            wait,
        )
        time.sleep(wait)


def sync(src: Path, dst: str, args: argparse.Namespace, logger: logging.Logger) -> bool:
    # gsutil honours only the last -x flag, so combine every pattern into one alternation.
    patterns = DEFAULT_EXCLUDES + args.exclude
    cmd = [
        args.gsutil,
        "-m",
        "rsync",
        "-r",
        "-x",
        "(" + "|".join(patterns) + ")",
        str(src),
        dst.rstrip("/") + "/",
    ]
    logger.info("syncing %s -> %s", src, dst)
    if args.dry_run:
        logger.info("dry-run: %s", " ".join(cmd))
        return True
    started = time.perf_counter()
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(
            "sync failed (exit %d): %s",
            result.returncode,
            (result.stderr or result.stdout).strip()[-2000:],
        )
        return False
    logger.info("ok: %s in %.1fs", src, time.perf_counter() - started)
    return True


def read_remote_json(
    remote: str, args: argparse.Namespace, logger: logging.Logger
) -> dict | None:
    """Return the parsed JSON at `remote`, or None if it isn't there / isn't JSON."""
    result = subprocess.run(
        [args.gsutil, "cat", remote], capture_output=True, text=True
    )
    if result.returncode != 0 or not result.stdout.strip():
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        logger.warning("could not parse %s; treating it as absent", remote)
        return None


def ensure_manifest(
    prefix: str,
    run_name: str,
    targets,
    args: argparse.Namespace,
    logger: logging.Logger,
) -> bool:
    """Write the run marker, refusing to write into a prefix owned by another run."""
    remote = f"{prefix.rstrip('/')}/run_manifest.json"
    existing = read_remote_json(remote, args, logger)
    if existing is not None and existing.get("run_name") != run_name:
        # A manifest whose own recorded `prefix` does not match the prefix it
        # sits at is not the authoritative owner of this prefix -- it was
        # written elsewhere and relocated. Adopt it (rewrite below) instead of
        # refusing; only a manifest that both names another run AND claims this
        # exact prefix is a real collision.
        if existing.get("prefix", "").rstrip("/") == prefix.rstrip("/"):
            logger.error(
                "run prefix %s already belongs to run %r; refusing to mix.",
                prefix,
                existing.get("run_name"),
            )
            return False
        logger.warning(
            "adopting prefix %s: manifest here names run %r but records prefix "
            "%r; rewriting it for run %r",
            prefix,
            existing.get("run_name"),
            existing.get("prefix"),
            run_name,
        )
    stamp = dt.datetime.now().isoformat(timespec="seconds")
    manifest = {
        "run_name": run_name,
        "created": (existing or {}).get("created", stamp),
        "updated": stamp,
        "base": args.base,
        "prefix": prefix,
        "targets": [{"source": str(src), "subfolder": sub} for src, sub, _ in targets],
    }
    payload = json.dumps(manifest, indent=2) + "\n"
    if args.dry_run:
        logger.info("dry-run: would write manifest %s", remote)
        return True
    result = subprocess.run(
        [args.gsutil, "cp", "-", remote], input=payload, capture_output=True, text=True
    )
    if result.returncode != 0:
        logger.error(
            "could not write manifest %s: %s",
            remote,
            (result.stderr or result.stdout).strip()[-2000:],
        )
        return False
    logger.info("run manifest: %s", remote)
    return True


def main() -> int:
    args = parse_args()
    logger = setup_logging(args.log_file)

    gsutil = shutil.which(args.gsutil)
    if not gsutil:
        logger.error("could not find '%s' on PATH", args.gsutil)
        return 2
    args.gsutil = gsutil

    args.base = (args.base or DEFAULT_BASE).rstrip("/")
    if not args.base:
        logger.error(
            "no GCS base: pass --base or set GCP_BACKUP_BASE "
            "(the launching notebook exports it)"
        )
        return 3

    watch = parse_watch_specs(args.watch) if args.watch else None
    extra = parse_extra_specs(args.extra) if args.extra else None
    missing = [str(path) for path, _ in (watch or []) + (extra or [])
               if not path.is_dir()]
    if missing:
        logger.error("target path is not a directory: %s", ", ".join(missing))
        return 3
    if watch and sum(1 for _, sub in watch if not sub) > 1:
        logger.error(
            "multiple --watch targets need an explicit :SUB "
            "(only one may sync to the prefix root)"
        )
        return 3

    if not args.run_name:
        if watch and not args.inference:
            args.run_name = run_name_from_path(watch[0][0])
        else:
            args.run_name = INFERENCE_RUN_NAME if args.inference else JOB_NAME

    if args.run_name in RESERVED_SUBFOLDERS:
        logger.error(
            "%r is a reserved non-run folder under %s; pick another run name.",
            args.run_name,
            args.base,
        )
        return 3

    prefix = f"{args.base}/{args.run_name}"

    base_targets = ([(path, sub, False) for path, sub in watch] if watch
                    else list(INFERENCE_TARGETS if args.inference else TRAINING_TARGETS))
    targets = base_targets + [(path, sub, False) for path, sub in (extra or [])]

    subs = [sub for _, sub, _ in targets]
    collisions = sorted({s for s in subs if subs.count(s) > 1})
    if collisions:
        logger.error(
            "duplicate remote subfolder(s) among targets: %s; give a distinct "
            ":SUB for the extra/watch target(s)",
            ", ".join(repr(s) for s in collisions),
        )
        return 3

    logger.info(
        "backup run %r (%s) to %s/%s every %.0f min (once=%s, dry-run=%s)",
        args.run_name,
        "watch" if watch else ("inference" if args.inference else "training"),
        args.base,
        args.run_name,
        args.interval_minutes,
        args.once,
        args.dry_run,
    )
    for src, sub, _ in targets:
        logger.info("  watching %s -> %s/%s", src, prefix, sub)

    if not ensure_manifest(prefix, args.run_name, targets, args, logger):
        return 3

    try:
        while True:
            synced = 0
            for src, sub, settle in targets:
                if not src.is_dir():
                    logger.warning("skipping missing folder %s", src)
                    continue
                if settle:
                    wait_for_settle(src, args.settle_seconds, logger)
                if sync(src, f"{prefix}/{sub}", args, logger):
                    synced += 1
            logger.info(
                "pass complete: %d/%d folders synced", synced, len(targets)
            )
            if args.once:
                break
            time.sleep(max(1.0, args.interval_minutes * 60.0))
    except KeyboardInterrupt:
        logger.info("interrupted; last completed pass is what is in GCS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
