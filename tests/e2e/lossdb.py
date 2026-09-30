"""Build a real `loss_log.db` from a small spec (plan §4.2 synthesized fixtures).

The schema is the one Ostris AI Toolkit's `UILogger` writes and `monitor_loss.py`
reads (`monitor_loss.py` docstring; `toolkit/logging_aitk.py`):

    steps(step INTEGER PRIMARY KEY, wall_time REAL)
    metric_keys(key TEXT PRIMARY KEY, first_seen_step, last_seen_step)
    metrics(step, key, value_real, value_text)

Used by J10's `fake_run.py`-adjacent checks and J11; the spec file lives in
`tests/fixtures/loss_log.spec.json` (Tier A, text only). Kept tiny so a test can
assert an exact rate: with `step_seconds` the rate is `1 / step_seconds`.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE steps(step INTEGER PRIMARY KEY, wall_time REAL);
CREATE TABLE metric_keys(key TEXT PRIMARY KEY, first_seen_step INTEGER, last_seen_step INTEGER);
CREATE TABLE metrics(step INTEGER, key TEXT, value_real REAL, value_text TEXT);
"""


def load_spec(path: Path) -> dict:
    spec = json.loads(Path(path).read_text(encoding="utf-8"))
    if spec.get("schema") != 1:
        raise ValueError(f"{path}: unsupported loss_log spec schema {spec.get('schema')!r}")
    for key in ("steps", "keys"):
        if key not in spec:
            raise ValueError(f"{path}: spec missing {key!r}")
    return spec


def _value(kspec: dict, step: int, n: int) -> float:
    kind = kspec.get("kind", "const")
    if kind == "const":
        return float(kspec["value"])
    if kind == "decay":
        t = (step - 1) / max(n - 1, 1)
        return float(kspec["start"]) + (float(kspec["end"]) - float(kspec["start"])) * t
    raise ValueError(f"unknown metric kind {kind!r}")


def build_loss_db(path: Path, spec: dict) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.unlink(missing_ok=True)
    n = int(spec["steps"])
    step_seconds = float(spec.get("step_seconds", 1.0))
    con = sqlite3.connect(str(path))
    try:
        con.executescript(SCHEMA)
        for step in range(1, n + 1):
            con.execute("INSERT INTO steps VALUES(?, ?)", (step, step * step_seconds))
            for key, kspec in spec["keys"].items():
                con.execute("INSERT INTO metrics VALUES(?, ?, ?, NULL)",
                            (step, key, _value(kspec, step, n)))
                con.execute(
                    "INSERT OR REPLACE INTO metric_keys VALUES(?, ?, ?)", (key, 1, step))
        con.commit()
    finally:
        con.close()
    return path
