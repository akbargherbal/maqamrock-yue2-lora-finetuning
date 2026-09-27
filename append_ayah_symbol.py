#!/usr/bin/env python3
"""Append ' \u06dd' (space + ARABIC END OF AYAH) to the aya/lyrics line of
each caption .txt in the YuE2 quran dataset.

Template (expected, 4 non-empty lines, trailing newline):
    <style prompt>
    [Lyrics]
    [Verse]
    <aya text>

Only the aya text line is modified. Idempotent: skips lines already ending
with U+06DD. Fails safe: any file that does not match the template is reported
and left untouched (exit code stays 0; the report is what matters).

Usage:
    append_ayah_symbol.py [--apply] ROOT [ROOT ...]
Without --apply it is a dry run (no writes).
"""
import argparse
import sys
from pathlib import Path

SYMBOL = " \u06dd"  # ASCII space + ARABIC END OF AYAH


def process(path: Path, apply: bool):
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        return "bad-encoding", str(e)

    had_trailing_nl = text.endswith("\n")
    lines = text.split("\n")
    body_idx = [i for i, ln in enumerate(lines) if ln.strip() != ""]

    # Expected: exactly 4 non-empty lines, in order, last one the aya text.
    if len(body_idx) != 4:
        return "bad-structure", f"{len(body_idx)} non-empty lines"
    p, lyr, verse, aya_i = (body_idx[0], body_idx[1], body_idx[2], body_idx[3])
    if lines[lyr].strip() != "[Lyrics]":
        return "bad-structure", f"line2={lines[lyr]!r}"
    if lines[verse].strip() != "[Verse]":
        return "bad-structure", f"line3={lines[verse]!r}"
    if lines[aya_i].startswith("["):
        return "bad-structure", f"aya line starts with '[': {lines[aya_i]!r}"
    if "\u06dd" in lines[aya_i]:
        return "already", ""

    new_aya = lines[aya_i] + SYMBOL
    lines[aya_i] = new_aya
    new_text = "\n".join(lines)
    if not new_text.endswith("\n") and had_trailing_nl:
        new_text += "\n"
    if apply:
        path.write_bytes(new_text.encode("utf-8"))
    return "ok", ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("roots", nargs="+")
    args = ap.parse_args()

    counts = {}
    problems = []
    total = 0
    for root in args.roots:
        rootp = Path(root)
        for p in sorted(rootp.rglob("*.txt")):
            total += 1
            status, detail = process(p, args.apply)
            counts[status] = counts.get(status, 0) + 1
            if status not in ("ok", "already"):
                problems.append((str(p), status, detail))

    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"[{mode}] roots={args.roots} total_txt={total}")
    for k in sorted(counts):
        print(f"  {k}: {counts[k]}")
    if problems:
        print(f"  problems ({len(problems)}):")
        for p, s, d in problems[:50]:
            print(f"    {s}: {p} :: {d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
