#!/usr/bin/env python3
"""Batch audio -> melody ABC with the official Python SheetSage2 (cover front end).

Runs under the isolated env `/content/.venv-sheetsage2` (uv, Python 3.11,
torch 2.8.0+cu126, transformers 4.45.2) — NOT the system python (which is
py3.13/transformers 5.x, incompatible with SheetSage2's custom code).

Loads the model once, transcribes each WAV with `melody_only=True`, and writes
`<out-dir>/<stem>/score.abc` (+ the model's side artifacts). Resumable: an
existing `score.abc` is skipped unless --force.

Default input is the batch_36_songs dir, excluding the `_2_`/`_3_` variant
markers — i.e. the **v2 / alpha-0** arm.

Usage:
    /content/.venv-sheetsage2/bin/python INFERENCE/sheetsage2_transcribe.py \\
        --out-dir /content/audiocpp_inference/out/abc_v2
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_INPUT = Path("/content/audiocpp_inference/out/batch_36_songs")
DEFAULT_OUT = Path("/content/audiocpp_inference/out/abc_v2")
VARIANT_MARKER = re.compile(r"_[23]_")


def now() -> str:
    return datetime.now(timezone.utc).strftime("%FT%TZ")


def collect(input_dir: Path, excl: re.Pattern | None) -> list[Path]:
    wavs = sorted(set(input_dir.glob("*.wav")) | set(input_dir.glob("*.WAV")))
    if excl is not None:
        wavs = [w for w in wavs if not excl.search(w.stem)]
    return wavs


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input-dir", default=str(DEFAULT_INPUT))
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT))
    ap.add_argument("--model", default="m-a-p/SheetSage2")
    ap.add_argument("--all", action="store_true",
                    help="include every WAV (disable the _2_/_3_ exclusion)")
    ap.add_argument("--exclude", default=None,
                    help="regex of stems to skip (default: the _2_/_3_ variant marker)")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--gcs", default="", help="gsutil rsync prefix for the out-dir")
    args = ap.parse_args(argv)

    if args.exclude is not None:
        excl = re.compile(args.exclude)
    elif args.all:
        excl = None
    else:
        excl = VARIANT_MARKER

    input_dir = Path(args.input_dir).expanduser()
    out_dir = Path(args.out_dir).expanduser()
    wavs = collect(input_dir, excl)
    if args.limit:
        wavs = wavs[: args.limit]
    if not wavs:
        print(f"[error] no WAVs under {input_dir} (excl={excl})", file=sys.stderr)
        return 1

    if args.dry_run:
        print(f"{len(wavs)} track(s) -> {out_dir}  (model={args.model})")
        for w in wavs:
            print("  ", w.name)
        return 0

    import torch
    from transformers import AutoModel

    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "_driver.log", "w", encoding="utf-8") as driver:

        def emit(line: str) -> None:
            print(line, flush=True)
            driver.write(line + "\n")
            driver.flush()

        emit(f"start {now()}  n={len(wavs)}  cuda={torch.cuda.is_available()}")
        t_load = time.monotonic()
        model = AutoModel.from_pretrained(args.model, trust_remote_code=True).eval()
        model = model.to("cuda" if torch.cuda.is_available() else "cpu")
        emit(f"model loaded in {time.monotonic() - t_load:.1f}s")

        rows, t0 = [], time.monotonic()
        for i, wav in enumerate(wavs, 1):
            tdir = out_dir / wav.stem
            abc = tdir / "score.abc"
            if abc.is_file() and abc.stat().st_size > 0 and not args.force:
                emit(f"[{i}/{len(wavs)}] {wav.stem}  skipped")
                rows.append((wav.stem, 0.0, "skipped", abc.stat().st_size))
                continue
            tdir.mkdir(parents=True, exist_ok=True)
            t = time.monotonic()
            try:
                model.transcribe(str(wav), output_dir=str(tdir), melody_only=True)
                status = "ok" if abc.is_file() else "no-abc"
            except Exception as e:  # noqa: BLE001 - one bad track must not kill the batch
                status = f"error: {type(e).__name__}"
            secs = time.monotonic() - t
            n = abc.stat().st_size if abc.is_file() else 0
            emit(f"[{i}/{len(wavs)}] {wav.stem}  {secs:.1f}s  {status}  abc={n}B")
            rows.append((wav.stem, secs, status, n))

        elapsed = time.monotonic() - t0
        with open(out_dir / "_timings.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["stem", "seconds", "status", "abc_bytes"])
            for r in rows:
                w.writerow([r[0], f"{r[1]:.1f}", r[2], r[3]])
        ok = [r for r in rows if r[2] in ("ok", "skipped") and r[3] > 0]
        (out_dir / "transcribe_manifest.json").write_text(json.dumps({
            "tool": "sheetsage2-python", "created_utc": now(), "model": args.model,
            "elapsed_s": round(elapsed, 1), "n": len(rows), "n_ok": len(ok),
            "tracks": [{"stem": r[0], "seconds": round(r[1], 1), "status": r[2],
                        "abc_bytes": r[3]} for r in rows],
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        emit(f"done {now()}  ok={len(ok)}/{len(rows)}  elapsed={elapsed:.1f}s "
             f"({elapsed / max(len(rows), 1):.1f}s/track)")
        if args.gcs:
            emit(f"uploading -> {args.gcs}")
            subprocess.run(["gsutil", "-m", "rsync", "-r", str(out_dir), args.gcs],
                           check=False)
    return 0 if len(ok) == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
