#!/usr/bin/env python3
"""Summarise a screen_arms.sh run: planned length per arm, no audio needed.

Reads <screen_dir>/<slug>_<seed>/semantic.json (a flat JSON array of semantic
codec indices, 25 frames/s) and prints one row per arm:

    arm              status     frames      sec  trunc    ar_s
    win_as-is        ok                812     32.5     no     232

`trunc` = the run stopped on semantic_max_tokens instead of the stop token
(meta field yue2.semantic.truncated in the CLI log); a longer plan than the
sheet warrants is the cheap proxy for an inserted section repeat.

`sec` alone is hard to judge, so compare against a reference the *sheet* warrants
rather than the cap (the cap is the truncation ceiling, so a delta against it is
degenerate). Best reference: the guidetrack's own rendered duration, which we
know matched the sheet.

    python3 INFERENCE/screen_summary.py <screen_dir> --expect-wav guide.wav
    python3 INFERENCE/screen_summary.py <screen_dir> --expect 262.0

Exit status: 0 if every arm produced a readable semantic.json, else 1.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import wave
from pathlib import Path

FPS = 25


def frames_of(p: Path) -> int | None:
    try:
        data = json.loads(p.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    if isinstance(data, dict):  # be tolerant of an envelope
        for key in ("semantic", "codes", "frames", "tokens"):
            if isinstance(data.get(key), list):
                data = data[key]
                break
    if not isinstance(data, list) or not all(isinstance(x, int) for x in data):
        return None
    return len(data)


def log_field(log: Path, name: str) -> str | None:
    """Last value of a `[TIMING ...] yue2.<name> <value>` line, or None."""
    try:
        text = log.read_text(errors="replace")
    except OSError:
        return None
    m = re.findall(rf"yue2\.{re.escape(name)}\s+([-\w.]+)", text)
    return m[-1] if m else None


def trunc_of(log: Path) -> str:
    """The MODEL's own flag (yue2.semantic.truncated 1|0), not the heuristic.

    generate.py also writes a `truncated` field into its sidecar, but sources it
    from `duration_heuristic` (WAV length near the cap) — the guide render is
    flagged `true` there while its model flag is `0`. The model flag is the one
    that means "stopped on semantic_max_tokens".
    """
    v = log_field(log, "semantic.truncated")
    if v is None:
        return "-"
    return {"1": "yes", "0": "no", "true": "yes", "false": "no"}.get(v.lower(), v)


def ar_seconds(log: Path) -> float | None:
    """AR semantic stage wall time (`yue2.semantic_ms`), the screen's real cost."""
    v = log_field(log, "semantic_ms")
    try:
        return float(v) / 1000.0
    except (TypeError, ValueError):
        return None


def expect_seconds(lyrics: Path) -> float:
    """The same 95th-percentile cap run_one.sh uses, in seconds.

    dur_cap = 111.1 + 0.3126*N_letters, rounded to 10 s
    (docs/text_to_duration_formula.md). Letters = alphabetic chars outside tags.
    NOTE: this is the truncation ceiling, not the song's length, so a delta
    against it is degenerate — prefer --expect-wav.
    """
    n = 0
    for line in lyrics.read_text().splitlines():
        s = line.strip()
        if not s or s.startswith("[") or s.startswith("///"):
            continue
        n += sum(ch.isalpha() for ch in s)
    return round((111.1 + 0.3126 * n) / 10.0) * 10.0


def wav_seconds(path: Path) -> float:
    """Duration of a PCM WAV via the stdlib (no deps)."""
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / float(w.getframerate())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("screen_dir", type=Path)
    ap.add_argument("--expect-wav", type=Path, default=None,
                    help="guide render's WAV; its duration is the reference")
    ap.add_argument("--expect", type=float, default=None,
                    help="explicit reference length in seconds")
    ap.add_argument("--expect-from", type=Path, default=None,
                    help="lyrics file; use the 95th-pct cap as the reference "
                         "(degenerate: that cap is also the truncation ceiling)")
    args = ap.parse_args()

    d = args.screen_dir
    if not d.is_dir():
        print(f"not a directory: {d}", file=sys.stderr)
        return 1

    ref = args.expect
    if ref is None and args.expect_wav is not None:
        try:
            ref = wav_seconds(args.expect_wav)
        except (OSError, wave.Error) as exc:
            print(f"cannot read {args.expect_wav}: {exc}", file=sys.stderr)
            return 1
    if ref is None and args.expect_from is not None:
        ref = expect_seconds(args.expect_from)

    rows = []
    for sub in sorted(d.iterdir()):
        if not sub.is_dir():
            continue
        sem = sub / "semantic.json"
        log = sub.parent / f"{sub.name}.log"
        if not log.exists():  # fall back to a log inside the artefact dir
            log = sub / "log.txt"
        n = frames_of(sem)
        if n is None:  # no artifact; recover the count from the CLI log
            tok = log_field(log, "semantic.tokens")
            n = int(tok) if tok and tok.isdigit() else None
        rows.append((sub.name, n, trunc_of(log), ar_seconds(log)))

    if not rows:
        print(f"no arm directories under {d}", file=sys.stderr)
        return 1

    head = f"{'arm':<26} {'status':<8} {'frames':>8} {'sec':>8} {'trunc':>6} {'ar_s':>7}"
    if ref is not None:
        head += f" {'vs ref':>8}"
    print(head)
    print("-" * len(head))
    ok = 0
    for name, n, trunc, ar_s in rows:
        if n is None:
            print(f"{name:<26} {'MISSING':<8} {'-':>8} {'-':>8} {trunc:>6} "
                  f"{'-' if ar_s is None else f'{ar_s:.0f}':>7}", end="")
            if ref is not None:
                print(f" {'-':>8}", end="")
            print()
            continue
        ok += 1
        sec = n / FPS
        line = (f"{name:<26} {'ok':<8} {n:>8} {sec:>8.1f} {trunc:>6} "
                f"{'-' if ar_s is None else f'{ar_s:.0f}':>7}")
        if ref is not None:
            line += f" {sec - ref:>+8.1f}"
        print(line)

    if ref is not None:
        print(f"\nref = {ref:.1f} s — a plan well over this is the cheap signal "
              f"of an inserted section repeat; a plan at the cap is truncated")
    print(f"\n{ok}/{len(rows)} arms produced a readable semantic.json")
    return 0 if ok == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
