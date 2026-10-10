#!/usr/bin/env python3
"""status.py -- one deterministic read of this project's run state.

The AGENTS.md §4 "ground truth in one move" tool: a single read-only command
that prints training progress, inference batch progress, sidecar liveness, the
last-backup age, local-vs-GCS drift, disk free, the current run folder, and how
stale the knowledge graph is. It writes nothing, signals nothing, and never
touches the GPU.

Environment-aware: on Colab (`/content` exists) it reads the full picture; on a
local checkout it prints what is repo-local and says plainly what it cannot
check. Colab-only paths are never applied locally.

Usage:
    python status.py

Exit code is 0 unless an expected sidecar is missing while a run is active.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
ON_COLAB = Path("/content").is_dir()

RUN_NAME = "v3_arabmaqamrock_lora"
LOGS = Path("/content/logs")
JOB_ROOT = Path("/content/ai-toolkit/output") / RUN_NAME
LOSS_DB = JOB_ROOT / "loss_log.db"
TRAIN_PID = LOGS / "train.pid"
TRAIN_LOG = LOGS / "train.log"
GCP_LOG = LOGS / "gcp_backup.log"
INFER_OUT = Path("/content/audiocpp_inference") / "out"
GRAPH_JSON = REPO_ROOT / "graphify-out" / "graph.json"

ALERTS: list[str] = []


def _run(cmd: list[str], timeout: float = 15.0) -> tuple[int, str]:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.returncode, (result.stdout or "").strip()
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 127, f"{type(exc).__name__}: {exc}"


def _pgrep(pattern: str) -> list[str]:
    rc, out = _run(["pgrep", "-af", pattern])
    if rc != 0 or not out:
        return []
    return [ln for ln in out.splitlines() if ln.strip()]


def _pid_alive(pidfile: Path) -> int | None:
    try:
        pid = int(pidfile.read_text().strip())
    except (OSError, ValueError):
        return None
    try:
        stat = Path(f"/proc/{pid}/stat").read_text()
        after = stat.rfind(")")
        if stat[after + 2: after + 3] in ("Z", "", "X"):
            return None
        return pid
    except OSError:
        return None


def _age(seconds: float) -> str:
    if seconds < 0:
        return "negative"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    if d:
        return f"{d}d{h}h"
    if h:
        return f"{h}h{m}m"
    if m:
        return f"{m}m{s}s"
    return f"{s}s"


def _parse_ts(text: str) -> dt.datetime | None:
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return dt.datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def section_header(lines: list[str]) -> None:
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    env = "Colab (/content)" if ON_COLAB else "localhost (no /content)"
    _, head = _run(["git", "-C", str(REPO_ROOT), "rev-parse", "--short", "HEAD"])
    _, branch = _run(["git", "-C", str(REPO_ROOT), "rev-parse", "--abbrev-ref", "HEAD"])
    try:
        free = shutil.disk_usage(REPO_ROOT).free / 1e9
        disk = f"{free:.1f} GB free"
    except OSError:
        disk = "disk unknown"
    lines.append(
        f"status @ {now} · env: {env} · git {branch.strip() or '?'} @ "
        f"{head.strip() or '?'}"
    )
    lines.append(f"repo: {REPO_ROOT} · disk {disk}")


def section_training(lines: list[str]) -> bool:
    if not ON_COLAB:
        lines.append("training: n/a (no /content; local checkout)")
        return False
    pid = _pid_alive(TRAIN_PID)
    if pid:
        lines.append(f"training: RUNNING pid {pid} ({RUN_NAME})")
    else:
        lines.append(f"training: not running ({RUN_NAME})")
    if LOSS_DB.is_file():
        _, out = _run([sys.executable, str(REPO_ROOT / "monitor_loss.py"), str(LOSS_DB)])
        for ln in out.splitlines():
            lines.append("  " + ln)
    else:
        lines.append(f"  metrics db: not found ({LOSS_DB})")
    smi = shutil.which("nvidia-smi")
    if smi:
        _, gpu = _run([
            smi,
            "--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw",
            "--format=csv,noheader,nounits",
        ])
        if gpu:
            first = gpu.splitlines()[0].split(",")
            if len(first) == 5:
                lines.append(
                    f"  gpu: util {first[0].strip()}% · mem {first[1].strip()}/"
                    f"{first[2].strip()} MiB · {first[3].strip()}C · {first[4].strip()} W"
                )
    if TRAIN_LOG.is_file():
        tail = TRAIN_LOG.read_text(errors="replace").splitlines()[-3:]
        lines.append("  train.log tail:")
        for ln in tail:
            lines.append("    " + ln)
    return bool(pid)


def section_inference(lines: list[str]) -> bool:
    if not ON_COLAB:
        lines.append("inference: n/a (no /content; local checkout)")
        return False
    procs = _pgrep("generate.py") + _pgrep("run_one.sh")
    run_dir = None
    latest = INFER_OUT / "latest"
    if latest.is_file():
        candidate = Path(latest.read_text().strip())
        if candidate.is_dir():
            run_dir = candidate
    if run_dir is None and INFER_OUT.is_dir():
        subdirs = sorted(d for d in INFER_OUT.glob("*") if d.is_dir())
        run_dir = subdirs[-1] if subdirs else None
    if run_dir is None:
        lines.append("inference: no run folder yet (out/ empty)")
        return bool(procs)
    total = None
    manifest = run_dir / "batch_manifest.json"
    if manifest.is_file():
        try:
            total = len(json.loads(manifest.read_text(encoding="utf-8")).get("tracks", []))
        except (OSError, ValueError):
            total = None
    wavs = len(list(run_dir.glob("*.wav")))
    state = "RUNNING" if procs else "idle"
    lines.append(
        f"inference: {state} · {run_dir.name} · {wavs}/{total if total is not None else '?'} wavs"
    )
    failed = run_dir / "_failed_runs.log"
    if failed.is_file():
        n = len([ln for ln in failed.read_text(errors="replace").splitlines() if ln.strip()])
        lines.append(f"  failures: {n} (see {failed.name})")
    summary = run_dir / "batch_summary.txt"
    if summary.is_file():
        for ln in summary.read_text(errors="replace").splitlines():
            if ln.strip().startswith("ok:"):
                lines.append("  " + ln.strip())
    status = run_dir / "_runs_status.log"
    if status.is_file():
        for ln in status.read_text(errors="replace").splitlines()[-2:]:
            lines.append("  " + ln.strip())
    return bool(procs)


def section_sidecars(lines: list[str]) -> dict[str, str | None]:
    if not ON_COLAB:
        lines.append("sidecars: n/a (no /content; local checkout)")
        return {}
    state: dict[str, str | None] = {}
    for name in ("backup_to_gcp.py", "gpu_logger.py"):
        hits = _pgrep(name)
        state[name] = hits[0].split()[0] if hits else None
    rc, out = _run(["vm-continuity", "status"])
    state["vm-continuity"] = "healthy" if rc == 0 else (out or f"exit {rc}")
    shown = " · ".join(
        f"{k}={v if v else 'DOWN'}" for k, v in state.items()
    )
    lines.append("sidecars: " + shown)
    return state


def section_backup(lines: list[str]) -> float | None:
    if not ON_COLAB:
        lines.append("backup: n/a (no /content; local checkout)")
        return None
    last: tuple[dt.datetime, str] | None = None
    if GCP_LOG.is_file():
        for ln in GCP_LOG.read_text(errors="replace").splitlines():
            if "pass complete:" in ln:
                ts = _parse_ts(ln[:19])
                if ts:
                    last = (ts, ln.strip())
    if last is None:
        lines.append(f"backup: no completed pass in {GCP_LOG}")
        return None
    ts, raw = last
    secs = (dt.datetime.now() - ts).total_seconds()
    detail = raw.split("pass complete:", 1)[1].strip()
    lines.append(f"backup: last pass {ts} ({_age(secs)} ago) — {detail}")
    return secs


def section_drift(lines: list[str]) -> None:
    if not ON_COLAB:
        lines.append("drift: n/a (no /content; local checkout)")
        return
    base = os.environ.get("GCP_BACKUP_BASE")
    if not base:
        lines.append("drift: not checked (GCP_BACKUP_BASE unset)")
        return
    if not shutil.which("gsutil"):
        lines.append("drift: not checked (gsutil not on PATH)")
        return
    local_newest = 0.0
    if JOB_ROOT.is_dir():
        for path in JOB_ROOT.rglob("*"):
            try:
                if path.is_file():
                    local_newest = max(local_newest, path.stat().st_mtime)
            except OSError:
                continue
    rc, out = _run(["gsutil", "ls", "-l", f"{base}/{RUN_NAME}/output/"], timeout=45.0)
    if rc != 0:
        reason = out.splitlines()[-1][:80] if out else f"rc {rc}"
        lines.append(f"drift: GCS listing failed ({reason})")
        return
    remote_newest = 0.0
    for ln in out.splitlines():
        parts = ln.split()
        if len(parts) >= 2 and parts[1].isdigit():
            ts = _parse_ts(parts[0].replace("T", " ").rstrip("Z"))
            if ts:
                remote_newest = max(remote_newest, ts.timestamp())
    if not local_newest or not remote_newest:
        lines.append("drift: not checked (missing local or remote timestamp)")
        return
    delta = local_newest - remote_newest
    if abs(delta) < 120:
        verdict = "in sync"
    elif delta > 0:
        verdict = "local ahead"
    else:
        verdict = "backup ahead"
    local_h = dt.datetime.fromtimestamp(local_newest).strftime("%Y-%m-%d %H:%M")
    lines.append(
        f"drift: {verdict} by {_age(abs(delta))} "
        f"(local newest {local_h} vs GCS {dt.datetime.fromtimestamp(remote_newest):%Y-%m-%d %H:%M})"
    )


def section_graph(lines: list[str]) -> None:
    if not GRAPH_JSON.is_file():
        lines.append("graph: no graphify-out/graph.json")
        return
    try:
        built = json.loads(GRAPH_JSON.read_text(encoding="utf-8")).get("built_at_commit", "")
    except (OSError, ValueError):
        built = ""
    _, head = _run(["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"])
    head = head.strip()
    if built and head and built == head:
        lines.append(f"graph: fresh at HEAD {head[:7]}")
    elif built and head:
        _, count = _run(["git", "-C", str(REPO_ROOT), "rev-list", "--count", f"{built}..HEAD"])
        behind = f"{count} commit(s)" if count.isdigit() else "unknown distance"
        lines.append(
            f"graph: STALE — built at {built[:7]}, HEAD {head[:7]} ({behind} behind)"
        )
    else:
        lines.append("graph: built_at_commit unknown")


def main() -> int:
    lines: list[str] = []
    section_header(lines)
    training_active = section_training(lines)
    inference_active = section_inference(lines)
    sidecars = section_sidecars(lines)
    backup_age = section_backup(lines)
    section_drift(lines)
    section_graph(lines)
    lines.append("run folder: " + (str(JOB_ROOT) if ON_COLAB else "(none — local checkout)"))

    active = training_active or inference_active
    if ON_COLAB and active:
        if sidecars.get("backup_to_gcp.py") is None:
            ALERTS.append("backup_to_gcp.py is not running while a run is active")
        if training_active and sidecars.get("gpu_logger.py") is None:
            ALERTS.append("gpu_logger.py is not running (no hardware telemetry)")
        if backup_age is not None and backup_age > 1800:
            ALERTS.append(f"last backup was {_age(backup_age)} ago")

    lines.append("ALERTS: none" if not ALERTS else "ALERTS: " + "; ".join(ALERTS))
    print("\n".join(lines))
    return 1 if ALERTS else 0


if __name__ == "__main__":
    raise SystemExit(main())
