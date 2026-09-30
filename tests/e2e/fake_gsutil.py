#!/usr/bin/env python3
"""A tiny fake `gsutil` on PATH for the T3 backup/restore e2e (plan §8).

`backup_to_gcp.py` shells out to `gsutil -m rsync`, `gsutil cat`, and
`gsutil cp -`. This stand-in maps every `gs://BUCKET/PATH` URI to
`$FAKE_GCS_ROOT/BUCKET/PATH` on the local disk, so a mirror + a reverse rsync
("restore") can be exercised end to end with no network and no credentials.

Supported: `[-m] rsync -r -x PATTERN SRC DST`, `cat REMOTE`, `cp - REMOTE`,
`cp LOCAL REMOTE`. The `-x` regex is honoured on the file *name* (so the default
`.*\\.tmp$` exclusion is real). Unknown subcommands exit non-zero.
"""
from __future__ import annotations

import os
import re
import shutil
import sys
from pathlib import Path

KNOWN = ("rsync", "cat", "cp")


def _map(uri: str) -> Path:
    if not uri.startswith("gs://"):
        raise ValueError(f"not a gs:// URI: {uri}")
    root = os.environ.get("FAKE_GCS_ROOT")
    if not root:
        print("fake_gsutil: FAKE_GCS_ROOT is not set", file=sys.stderr)
        raise SystemExit(2)
    return Path(root) / uri[len("gs://"):].strip("/")


def _copy_tree(src: Path, dst: Path, pattern: str | None) -> int:
    if not src.is_dir():
        print(f"fake_gsutil: rsync source is not a directory: {src}", file=sys.stderr)
        return 1
    for path in sorted(src.rglob("*")):
        if not path.is_file():
            continue
        if pattern and re.search(pattern, path.name):
            continue
        target = dst / path.relative_to(src)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    return 0


def _rsync(args: list[str]) -> int:
    pattern = None
    positional: list[str] = []
    i = 0
    while i < len(args):
        a = args[i]
        if a == "-x":
            pattern = args[i + 1]
            i += 2
        elif a.startswith("-"):
            i += 1
        else:
            positional.append(a)
            i += 1
    if len(positional) < 2:
        print("fake_gsutil: rsync needs SRC and DST", file=sys.stderr)
        return 2
    src, dst = positional[-2], positional[-1]
    if src.startswith("gs://"):
        return _copy_tree(_map(src), Path(dst), pattern)
    return _copy_tree(Path(src), _map(dst), pattern)


def main() -> int:
    args = [a for a in sys.argv[1:] if a != "-m"]
    sub = next((a for a in args if a in KNOWN), None)
    if sub is None:
        print(f"fake_gsutil: unsupported invocation: {' '.join(sys.argv[1:])}",
              file=sys.stderr)
        return 2
    rest = args[args.index(sub) + 1:]

    if sub == "rsync":
        return _rsync(rest)
    if sub == "cat":
        target = _map(rest[-1])
        if not target.is_file():
            print(f"fake_gsutil: no such object: {rest[-1]}", file=sys.stderr)
            return 1
        sys.stdout.write(target.read_text(encoding="utf-8"))
        return 0
    # cp
    src, dst = rest[0], rest[1]
    target = _map(dst)
    target.parent.mkdir(parents=True, exist_ok=True)
    if src == "-":
        target.write_text(sys.stdin.read(), encoding="utf-8")
    else:
        shutil.copy2(src, target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
