"""J12 -- backup mirror + manifest + restore diff (plan §5, T3).

Runs the **real** `backup_to_gcp.py` in a subprocess with a real `gsutil`
executable on `PATH` (`tests/e2e/fake_gsutil.py`, a local `gs://` mapper). Then
restores the mirrored folder with a reverse rsync and byte-compares it -- the
`gsutil` surface and the filesystem are real; only the network is faked.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BACKUP = REPO / "backup_to_gcp.py"


def _env(fake_gsutil) -> dict:
    env = dict(os.environ)
    env["PATH"] = str(fake_gsutil.bin_dir) + os.pathsep + env.get("PATH", "")
    env["FAKE_GCS_ROOT"] = str(fake_gsutil.root)
    return env


def _files(root: Path) -> set[str]:
    return {str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()}


def test_j12_mirror_manifest_and_restore(fake_gsutil, tmp_path):
    run = tmp_path / "run"
    out, logs, notes = run / "output", run / "logs", run / "agent_notes"
    for d in (out, logs, notes):
        d.mkdir(parents=True)
    (out / "checkpoint.safetensors").write_bytes(b"ckpt-bytes")
    (out / "config.yaml").write_text("name: demo\n", encoding="utf-8")
    (out / "loss_log.db").write_bytes(b"sqlite-fake")
    (out / "junk.tmp").write_bytes(b"must not be uploaded")   # default -x excludes *.tmp
    (logs / "train.log").write_text("step 1 loss 2.0\n", encoding="utf-8")
    (notes / "current.md").write_text("# notes\n", encoding="utf-8")

    env = _env(fake_gsutil)
    result = subprocess.run(
        [sys.executable, str(BACKUP), "--base", "gs://fakeb/proj", "--run-name", "myrun",
         "--watch", f"{out}:output", "--watch", f"{logs}:logs",
         "--watch", f"{notes}:agent_notes", "--once", "--settle-seconds", "0",
         "--gsutil", str(fake_gsutil.exe), "--log-file", str(tmp_path / "backup.log")],
        capture_output=True, text=True, env=env, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "pass complete: 3/3 folders synced" in result.stdout

    gcs = fake_gsutil.root / "fakeb" / "proj" / "myrun"
    manifest = json.loads((gcs / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["run_name"] == "myrun"
    assert manifest["prefix"] == "gs://fakeb/proj/myrun"
    assert [t["subfolder"] for t in manifest["targets"]] == ["output", "logs", "agent_notes"]
    assert (gcs / "output" / "checkpoint.safetensors").read_bytes() == b"ckpt-bytes"
    assert (gcs / "logs" / "train.log").is_file()
    assert (gcs / "agent_notes" / "current.md").is_file()
    assert not (gcs / "output" / "junk.tmp").exists()      # -x exclusion is real

    # restore: reverse rsync gs:// -> local, then byte-compare (diff clean)
    restore = tmp_path / "restore"
    reverse = subprocess.run(
        [sys.executable, str(fake_gsutil.exe), "-m", "rsync", "-r", "-x", r"(.*\.tmp$)",
         "gs://fakeb/proj/myrun/output/", str(restore)],
        capture_output=True, text=True, env=env, timeout=30)
    assert reverse.returncode == 0, reverse.stderr
    assert _files(restore) == {"checkpoint.safetensors", "config.yaml", "loss_log.db"}
    for name in ("checkpoint.safetensors", "config.yaml", "loss_log.db"):
        assert (restore / name).read_bytes() == (out / name).read_bytes()
    assert not (restore / "junk.tmp").exists()
