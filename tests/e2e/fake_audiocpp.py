#!/usr/bin/env python3
"""Stub `audiocpp_cli` for tests/e2e/test_rescue_e2e.py.

Stands in for the real binary at the rescue driver's compute seam. Writes a fake
WAV to `--out` and records the request options (notably `cot` and `abc_file`)
beside it as `<out>.args.json`, so a test can assert the guide actually reached
the binary. Set FAKE_AUDIOCPP_FAIL to a comma list of substrings; a matching
`--out` basename exits 3 and writes nothing (to exercise the failure path).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    out = None
    opts: dict[str, str] = {}
    for i, a in enumerate(argv):
        if a == "--out" and i + 1 < len(argv):
            out = argv[i + 1]
        elif a == "--request-option" and i + 1 < len(argv):
            k, _, v = argv[i + 1].partition("=")
            opts[k] = v
    if not out:
        print("fake_audiocpp: missing --out", file=sys.stderr)
        return 2
    path = Path(out)
    fails = [s for s in os.environ.get("FAKE_AUDIOCPP_FAIL", "").split(",") if s]
    if any(s in path.name for s in fails):
        print(f"fake_audiocpp: simulated failure for {path.name}", file=sys.stderr)
        return 3
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"RIFF....WAVEfmt fake-audio")
    Path(str(path) + ".args.json").write_text(
        json.dumps({"argv": argv, "opts": opts}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    print(f"fake_audiocpp: wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
