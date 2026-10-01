#!/usr/bin/env python3
"""SheetSage2 audio -> ABC transcription batch (audio.cpp path).

Feeds WAVs to the audio.cpp SheetSage2 runtime (`--task midi --family
sheetsage2`) and collects one ABC per input, for the cover experiment
(v2 melody -> qfinal_a0.3 with `cot=melody` + `abc_file`).

Strictly sequential (one GPU). Resumable: an existing ABC is skipped unless
--force. --limit and --time-budget make the smoke / stop-early runs cheap.

Outputs under --out-dir:
    <stem>.abc                 the score (primary output of this script)
    artifacts/<stem>/          whatever else the binary writes (midi, events)
    <stem>.log                 per-track CLI log
    _timings.csv               stem, seconds, exit, abc_bytes, started_utc
    transcribe_manifest.json   inputs, options, per-track results
    _driver.log                full console output

Exact sheetsage2 flags are UNVERIFIED upstream (no docs/models/sheetsage2.md;
the invocation mirrors the sibling `midi` family MuScriptor). The ABC is
located defensively: first --out <stem>.abc, else any *.abc under the track's
--out-dir. If a track yields no ABC, its log tail is printed and the run stops.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/content/audiocpp_inference")
DEFAULT_BIN = ROOT / "bin" / "audiocpp_cli"
DEFAULT_MODEL = ROOT / "models" / "SheetSage2-GGUF" / "sheetsage2-orig.gguf"
DEFAULT_INPUT = ROOT / "out" / "batch_36_songs"
DEFAULT_OUT = ROOT / "out" / "sheetsage2_abc"


class PlanError(RuntimeError):
    """Invalid input, bad CLI use, or a failed preflight."""


def slug(name: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in name)


def now() -> str:
    return datetime.now(timezone.utc).strftime("%FT%TZ")


@dataclass
class Track:
    src: Path
    stem: str
    abc: Path
    log: Path
    artifacts: Path
    exit: int = -1
    seconds: float = 0.0
    result_abc: Path | None = None
    status: str = "pending"


@dataclass
class Config:
    bin: Path
    model: Path
    inputs: list[Path]
    out_dir: Path
    backend: str
    threads: int
    request_opts: list[str] = field(default_factory=list)
    limit: int = 0
    time_budget: float = 0.0
    per_track_timeout: float = 0.0
    force: bool = False
    dry_run: bool = False
    gcs: str = ""


def collect_inputs(words: list[str], default_dir: Path) -> list[Path]:
    files: list[Path] = []
    for w in words:
        p = Path(w).expanduser()
        if p.is_dir():
            files.extend(sorted(p.glob("*.wav")) + sorted(p.glob("*.WAV")))
        elif p.is_file():
            files.append(p)
        else:
            raise PlanError(f"input not found: {p}")
    if not files:
        d = default_dir.expanduser()
        if not d.is_dir():
            raise PlanError(f"no inputs given and default dir missing: {d}")
        files = sorted(d.glob("*.wav"))
    seen: set[Path] = set()
    out: list[Path] = []
    for f in files:
        r = f.resolve()
        if r not in seen:
            seen.add(r)
            out.append(f)
    return out


def build_tracks(cfg: Config) -> list[Track]:
    tracks: list[Track] = []
    used: dict[str, int] = {}
    for src in cfg.inputs:
        stem = slug(src.stem)
        if stem in used:
            used[stem] += 1
            stem = f"{stem}_{used[stem]}"
        else:
            used[stem] = 1
        tracks.append(Track(src=src, stem=stem, abc=cfg.out_dir / f"{stem}.abc",
                            log=cfg.out_dir / f"{stem}.log",
                            artifacts=cfg.out_dir / "artifacts" / stem))
    if cfg.limit:
        tracks = tracks[: cfg.limit]
    return tracks


def command(cfg: Config, t: Track) -> list[str]:
    cmd = [
        str(cfg.bin),
        "--task", "midi",
        "--family", "sheetsage2",
        "--model", str(cfg.model),
        "--backend", cfg.backend,
        "--threads", str(cfg.threads),
        "--audio", str(t.src),
        "--out", str(t.abc),
        "--out-dir", str(t.artifacts),
        "--log",
    ]
    for kv in cfg.request_opts:
        cmd += ["--request-option", kv]
    return cmd


def find_abc(cfg: Config, t: Track) -> Path | None:
    if t.abc.is_file() and t.abc.stat().st_size > 0:
        return t.abc
    if t.artifacts.is_dir():
        hits = sorted(t.artifacts.rglob("*.abc"))
        if hits:
            return hits[0]
    return None


def run_track(cfg: Config, t: Track) -> None:
    if t.abc.is_file() and t.abc.stat().st_size > 0 and not cfg.force:
        t.status = "skipped"
        t.result_abc = t.abc
        return
    t.artifacts.mkdir(parents=True, exist_ok=True)
    cmd = command(cfg, t)
    started = time.monotonic()
    try:
        with open(t.log, "w", encoding="utf-8") as lf:
            lf.write("$ " + " ".join(cmd) + "\n")
            lf.flush()
            rc = subprocess.run(cmd, stdout=lf, stderr=subprocess.STDOUT,
                                timeout=cfg.per_track_timeout or None).returncode
    except subprocess.TimeoutExpired:
        t.exit, t.seconds, t.status = 124, time.monotonic() - started, "timeout"
        return
    t.exit = rc
    t.seconds = time.monotonic() - started
    found = find_abc(cfg, t)
    if found and rc == 0:
        if found != t.abc:
            shutil.copy2(found, t.abc)
        t.result_abc, t.status = t.abc, "ok"
    else:
        t.status = "failed"


def log_tail(path: Path, n: int = 20) -> str:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return ""
    return "\n".join(lines[-n:])


def print_plan(cfg: Config, tracks: list[Track]) -> None:
    print(f"binary : {cfg.bin}")
    print(f"model  : {cfg.model}")
    print(f"inputs : {len(tracks)} track(s) -> {cfg.out_dir}")
    if cfg.time_budget:
        print(f"budget : {cfg.time_budget:.0f}s total, "
              f"{cfg.per_track_timeout or 'no'}s/track timeout")
    for i, t in enumerate(tracks, 1):
        print(f"  {i:>3}  {t.stem}")


def write_csv(path: Path, rows: list[Track]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["stem", "seconds", "exit", "status", "abc_bytes", "abc_path"])
        for t in rows:
            n = t.abc.stat().st_size if t.abc.is_file() else 0
            w.writerow([t.stem, f"{t.seconds:.1f}", t.exit, t.status, n,
                        str(t.result_abc or "")])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="*",
                    help="WAV files or dirs (default: batch_36_songs)")
    ap.add_argument("--bin", default=str(DEFAULT_BIN))
    ap.add_argument("--model", default=str(DEFAULT_MODEL))
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT))
    ap.add_argument("--backend", default="cuda")
    ap.add_argument("--threads", type=int, default=8)
    ap.add_argument("--request-option", action="append", default=[],
                    dest="request_opts", metavar="K=V")
    ap.add_argument("--limit", type=int, default=0, help="0 = all")
    ap.add_argument("--time-budget", type=float, default=1200.0,
                    help="stop starting new tracks after this many seconds (0 = off)")
    ap.add_argument("--per-track-timeout", type=float, default=900.0,
                    help="hard timeout per track in seconds (0 = off)")
    ap.add_argument("--force", action="store_true", help="redo existing ABCs")
    ap.add_argument("--dry-run", action="store_true", help="plan only, write nothing")
    ap.add_argument("--gcs", default="", help="gsutil rsync prefix (e.g. gs://bucket/dir)")
    args = ap.parse_args(argv)

    try:
        if args.limit < 0:
            raise PlanError("--limit must be >= 0")
        out_dir = Path(args.out_dir).expanduser()
        inputs = collect_inputs(args.inputs, DEFAULT_INPUT)
        cfg = Config(bin=Path(args.bin).expanduser(), model=Path(args.model).expanduser(),
                     inputs=inputs, out_dir=out_dir, backend=args.backend,
                     threads=args.threads, request_opts=args.request_opts,
                     limit=args.limit, time_budget=args.time_budget,
                     per_track_timeout=args.per_track_timeout, force=args.force,
                     dry_run=args.dry_run, gcs=args.gcs)
        tracks = build_tracks(cfg)
        if not tracks:
            raise PlanError("no tracks to run")

        if cfg.dry_run:
            print_plan(cfg, tracks)
            print("\nfirst command:\n  " + " ".join(command(cfg, tracks[0])))
            return 0

        if not cfg.bin.is_file():
            raise PlanError(f"binary not found: {cfg.bin}")
        if not cfg.model.is_file():
            raise PlanError(f"model not found: {cfg.model}")

        out_dir.mkdir(parents=True, exist_ok=True)
        driver = open(out_dir / "_driver.log", "w", encoding="utf-8")

        def emit(line: str) -> None:
            print(line, flush=True)
            driver.write(line + "\n")
            driver.flush()

        print_plan(cfg, tracks)
        emit(f"start {now()}  n={len(tracks)}")
        t0 = time.monotonic()
        stopped_early = False
        for i, t in enumerate(tracks, 1):
            if cfg.time_budget and i > 1 and (time.monotonic() - t0) >= cfg.time_budget:
                stopped_early = True
                emit(f"budget {cfg.time_budget:.0f}s reached after {i - 1} track(s); "
                     f"stopping before {t.stem}")
                break
            run_track(cfg, t)
            abc_note = f"  abc={t.abc.stat().st_size}B" if t.abc.is_file() else ""
            emit(f"[{i}/{len(tracks)}] {t.stem}  {t.seconds:.1f}s  "
                 f"exit={t.exit}  {t.status}{abc_note}")
            if t.status in ("failed", "timeout"):
                emit(f"  aborted on first failure; log tail from {t.log}:\n"
                     + "\n".join("  " + ln for ln in log_tail(t.log).splitlines()))
                break

        elapsed = time.monotonic() - t0
        done = [t for t in tracks if t.status in ("ok", "skipped")]
        write_csv(out_dir / "_timings.csv", tracks)
        manifest = {
            "created_utc": now(), "binary": str(cfg.bin), "model": str(cfg.model),
            "backend": cfg.backend, "request_opts": cfg.request_opts,
            "elapsed_s": round(elapsed, 1), "stopped_early": stopped_early,
            "n_inputs": len(tracks), "n_ok": len(done),
            "tracks": [{"stem": t.stem, "src": str(t.src), "exit": t.exit,
                        "seconds": round(t.seconds, 1), "status": t.status,
                        "abc": str(t.result_abc or "")} for t in tracks],
        }
        (out_dir / "transcribe_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

        emit(f"done {now()}  ok={len(done)}/{len(tracks)}  elapsed={elapsed:.1f}s")
        if stopped_early and done:
            ran = [t for t in tracks if t.seconds > 0]
            if ran:
                per = sum(t.seconds for t in ran) / len(ran)
                print(f"  ~{per:.1f}s/track -> ~{per * len(tracks) / 60:.1f} min "
                      f"for all {len(tracks)}")
        if cfg.gcs:
            emit(f"uploading {out_dir} -> {cfg.gcs}")
            subprocess.run(["gsutil", "-m", "rsync", "-r", str(out_dir), cfg.gcs], check=False)
        driver.close()
        return 0 if done and all(t.status in ("ok", "skipped") for t in tracks) else 1
    except PlanError as e:
        print(f"[error] {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n[interrupted]", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
