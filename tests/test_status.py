"""GPU-free tests for `status.py` (the §4 ground-truth read).

No `/content`, no GPU: the local path is asserted end to end via subprocess, and
the Colab-only branches plus the graph-freshness logic are unit-tested against
faked module state. The property that matters most is honesty: on a local
checkout the `/content` surfaces must be reported as `n/a`, not as "not running".
"""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "status.py"


def _load():
    spec = importlib.util.spec_from_file_location("status_script", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["status_script"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def status():
    return _load()


def test_age_format(status):
    assert status._age(0) == "0s"
    assert status._age(45) == "45s"
    assert status._age(90) == "1m30s"
    assert status._age(3600) == "1h0m"
    assert status._age(90000) == "1d1h"


def test_parse_ts(status):
    assert status._parse_ts("2026-09-28 09:00:00").hour == 9
    assert status._parse_ts("2026-09-28T09:00:00").minute == 0
    assert status._parse_ts("not a timestamp") is None


def test_local_run_reports_sections(status):
    result = subprocess.run(
        [sys.executable, str(SCRIPT)], capture_output=True, text=True, cwd=str(REPO_ROOT)
    )
    assert result.returncode == 0, result.stderr
    out = result.stdout
    assert "status @" in out
    assert "graph:" in out
    assert "run folder:" in out
    assert "ALERTS:" in out


def test_missing_content_is_n_a_not_down(status, tmp_path, monkeypatch):
    monkeypatch.setattr(status, "ON_COLAB", False)
    lines = []
    active = status.section_training(lines)
    assert active is False
    assert "n/a" in "\n".join(lines)
    assert "not running" not in "\n".join(lines)


def test_graph_stale_is_flagged(status, tmp_path, monkeypatch):
    graph = tmp_path / "graph.json"
    graph.write_text(json.dumps({"built_at_commit": "0" * 40}), encoding="utf-8")
    monkeypatch.setattr(status, "GRAPH_JSON", graph)
    lines = []
    status.section_graph(lines)
    assert "STALE" in "\n".join(lines)


def test_graph_fresh_matches_head(status, tmp_path, monkeypatch):
    head = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
        capture_output=True, text=True,
    )
    if head.returncode != 0:
        pytest.skip("not a git checkout")
    graph = tmp_path / "graph.json"
    graph.write_text(json.dumps({"built_at_commit": head.stdout.strip()}), encoding="utf-8")
    monkeypatch.setattr(status, "GRAPH_JSON", graph)
    lines = []
    status.section_graph(lines)
    assert "fresh at HEAD" in "\n".join(lines)
