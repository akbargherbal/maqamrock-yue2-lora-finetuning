"""Unit tests for backup_to_gcp.py (GPU-free, no GCS).

The module is exercised **in-process** (via the `bak` fixture) with a fake
`subprocess.run`, so the repo's standard `coverage run -m pytest` traces every
line. Nothing touches /content, gsutil, or the network.
"""
import json
import logging
import os
import runpy
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "backup_to_gcp.py"


# --- fakes / helpers --------------------------------------------------------

class FakeGsutil:
    """Stands in for subprocess.run; dispatches on the gsutil subcommand."""

    def __init__(self, cat_rc=1, cat_out="", cp_rc=0, cp_err="", rsync_rc=0,
                 rsync_err="", interrupt_on_rsync=0):
        self.cat_rc, self.cat_out = cat_rc, cat_out
        self.cp_rc, self.cp_err = cp_rc, cp_err
        self.rsync_rc, self.rsync_err = rsync_rc, rsync_err
        self.interrupt_on_rsync = interrupt_on_rsync
        self.calls = []          # list of (argv, stdin)
        self.rsync_calls = 0

    def __call__(self, cmd, **kwargs):
        self.calls.append((list(cmd), kwargs.get("input")))
        if "rsync" in cmd:
            self.rsync_calls += 1
            if self.rsync_calls == self.interrupt_on_rsync:
                raise KeyboardInterrupt
            return subprocess.CompletedProcess(cmd, self.rsync_rc, "", self.rsync_err)
        sub = cmd[1] if len(cmd) > 1 else ""
        if sub == "cat":
            return subprocess.CompletedProcess(cmd, self.cat_rc, self.cat_out, "")
        if sub == "cp":
            return subprocess.CompletedProcess(cmd, self.cp_rc, "", self.cp_err)
        return subprocess.CompletedProcess(cmd, 0, "", "")

    def subcommands(self):
        return [c[0][1] for c in self.calls]


def _patch(bak, monkeypatch, fake, which="/fake/gsutil"):
    monkeypatch.setattr(bak, "shutil", SimpleNamespace(which=lambda name: which))
    monkeypatch.setattr(bak, "subprocess", SimpleNamespace(run=fake))


def _args(**over):
    base = {"gsutil": "/fake/gsutil", "exclude": [], "dry_run": False,
            "base": "gs://b/p"}
    base.update(over)
    return SimpleNamespace(**base)


@pytest.fixture
def lg():
    return logging.getLogger("gcp_backup")


@pytest.fixture(autouse=True)
def _close_log_handlers():
    yield
    logger = logging.getLogger("gcp_backup")
    for h in list(logger.handlers):
        h.close()
    logger.handlers.clear()


# --- pure helpers -----------------------------------------------------------

def test_parse_watch_specs(bak):
    got = bak.parse_watch_specs(["/a/b", "/c/d:wavs", "~/x/", "/e/f:/sub/"])
    assert got[0] == (Path("/a/b"), "")
    assert got[1] == (Path("/c/d"), "wavs")
    assert got[2] == (Path.home() / "x", "")
    assert got[3] == (Path("/e/f"), "sub")


def test_run_name_from_path(bak):
    assert bak.run_name_from_path(Path("/content/My Songs!")) == "My-Songs"
    assert bak.run_name_from_path(Path("/content/keep_me.2")) == "keep_me.2"
    assert bak.run_name_from_path(Path("/content/!!!")) == "watch"
    assert bak.run_name_from_path(Path("/")) == "watch"


def test_parse_extra_specs(bak):
    got = bak.parse_extra_specs(["/a/b", "/c/My Songs", "/d/e:wavs", "/f/g:"])
    assert got[0] == (Path("/a/b"), "b")                 # basename default
    assert got[1] == (Path("/c/My Songs"), "My-Songs")   # slugified basename
    assert got[2] == (Path("/d/e"), "wavs")              # explicit SUB
    assert got[3] == (Path("/f/g"), "")                  # explicit empty -> root


# --- setup_logging ----------------------------------------------------------

def test_setup_logging_writes_file_and_is_idempotent(bak, tmp_path):
    path = tmp_path / "deep" / "backup.log"
    logger = bak.setup_logging(str(path))
    assert path.parent.is_dir()
    logger.info("hello")
    assert "hello" in path.read_text(encoding="utf-8")
    n = len(logger.handlers)
    bak.setup_logging(str(path))          # replaces, does not accumulate
    assert len(logger.handlers) == n


# --- wait_for_settle --------------------------------------------------------

def test_wait_for_settle_nonpositive_returns(bak, tmp_path, lg):
    bak.wait_for_settle(tmp_path, 0, lg)   # must not raise / sleep


def test_wait_for_settle_returns_once_quiet(bak, tmp_path, lg, monkeypatch):
    f = tmp_path / "a.wav"
    f.write_bytes(b"x")
    slept = []

    def fake_sleep(_):
        slept.append(1)
        old = time.time() - 1000
        os.utime(f, (old, old))            # age it so the next check settles
    monkeypatch.setattr(bak.time, "sleep", fake_sleep)
    bak.wait_for_settle(tmp_path, 50, lg)
    assert slept == [1]


def test_wait_for_settle_ignores_loss_log(bak, tmp_path, lg, monkeypatch):
    (tmp_path / "loss_log.db").write_bytes(b"x")
    monkeypatch.setattr(bak.time, "sleep",
                        lambda _: pytest.fail("must not wait on an ignored db"))
    bak.wait_for_settle(tmp_path, 50, lg)  # newest non-ignored file is absent -> 0.0


# --- sync -------------------------------------------------------------------

def test_sync_command_and_success(bak, lg, monkeypatch):
    fake = FakeGsutil(rsync_rc=0)
    _patch(bak, monkeypatch, fake)
    args = _args(exclude=[r"a\.b$"])
    assert bak.sync(Path("/src"), "gs://b/p/sub/", args, lg) is True
    cmd, _ = fake.calls[0]
    assert cmd[0] == "/fake/gsutil"
    assert cmd[1:6] == ["-m", "rsync", "-r", "-x", r"(.*\.tmp$|a\.b$)"]
    assert cmd[6] == "/src"
    assert cmd[7] == "gs://b/p/sub/"       # rstrip("/") + "/"


def test_sync_dry_run_uploads_nothing(bak, lg, monkeypatch, caplog):
    fake = FakeGsutil()
    _patch(bak, monkeypatch, fake)
    with caplog.at_level(logging.INFO, logger="gcp_backup"):
        assert bak.sync(Path("/src"), "gs://b/p/sub", _args(dry_run=True), lg) is True
    assert fake.calls == []
    assert "dry-run:" in caplog.text


def test_sync_failure_returns_false(bak, lg, monkeypatch, caplog):
    fake = FakeGsutil(rsync_rc=1, rsync_err="boom")
    _patch(bak, monkeypatch, fake)
    with caplog.at_level(logging.ERROR, logger="gcp_backup"):
        assert bak.sync(Path("/src"), "gs://b/p/sub", _args(), lg) is False
    assert "sync failed" in caplog.text


# --- read_remote_json -------------------------------------------------------

@pytest.mark.parametrize("rc,out,expected", [
    (1, "", None),
    (0, "   ", None),
    (0, '{"run_name": "x"}', {"run_name": "x"}),
])
def test_read_remote_json(bak, lg, monkeypatch, rc, out, expected):
    _patch(bak, monkeypatch, FakeGsutil(cat_rc=rc, cat_out=out))
    assert bak.read_remote_json("gs://b/p/run_manifest.json", _args(), lg) == expected


def test_read_remote_json_bad_json_warns(bak, lg, monkeypatch, caplog):
    _patch(bak, monkeypatch, FakeGsutil(cat_rc=0, cat_out="{not json"))
    with caplog.at_level(logging.WARNING, logger="gcp_backup"):
        assert bak.read_remote_json("gs://b/p/x.json", _args(), lg) is None
    assert "could not parse" in caplog.text


# --- ensure_manifest --------------------------------------------------------

def test_ensure_manifest_writes_new(bak, lg, monkeypatch):
    fake = FakeGsutil(cat_rc=1)
    _patch(bak, monkeypatch, fake)
    targets = [(Path("/src"), "sub", False)]
    assert bak.ensure_manifest("gs://b/p/run", "run", targets, _args(base="gs://b/p"), lg)
    cp, stdin = [c for c in fake.calls if c[0][1] == "cp"][0]
    assert cp[1:3] == ["cp", "-"]
    assert cp[3] == "gs://b/p/run/run_manifest.json"
    payload = json.loads(stdin)
    assert payload["run_name"] == "run"
    assert payload["prefix"] == "gs://b/p/run"
    assert payload["targets"] == [{"source": "/src", "subfolder": "sub"}]


def test_ensure_manifest_refuses_collision(bak, lg, monkeypatch, caplog):
    existing = json.dumps({"run_name": "other", "prefix": "gs://b/p/run"})
    fake = FakeGsutil(cat_rc=0, cat_out=existing)
    _patch(bak, monkeypatch, fake)
    with caplog.at_level(logging.ERROR, logger="gcp_backup"):
        assert bak.ensure_manifest("gs://b/p/run", "run", [], _args(), lg) is False
    assert "already belongs" in caplog.text
    assert fake.subcommands() == ["cat"]      # refused before any write


def test_ensure_manifest_adopts_relocated(bak, lg, monkeypatch, caplog):
    existing = json.dumps({"run_name": "other", "prefix": "gs://elsewhere",
                           "created": "2020-01-01T00:00:00"})
    fake = FakeGsutil(cat_rc=0, cat_out=existing)
    _patch(bak, monkeypatch, fake)
    with caplog.at_level(logging.WARNING, logger="gcp_backup"):
        assert bak.ensure_manifest("gs://b/p/run", "run", [], _args(), lg) is True
    assert "adopting prefix" in caplog.text
    payload = json.loads(fake.calls[-1][1])
    assert payload["run_name"] == "run"
    assert payload["created"] == "2020-01-01T00:00:00"    # preserved


def test_ensure_manifest_dry_run(bak, lg, monkeypatch, caplog):
    fake = FakeGsutil(cat_rc=1)
    _patch(bak, monkeypatch, fake)
    with caplog.at_level(logging.INFO, logger="gcp_backup"):
        assert bak.ensure_manifest("gs://b/p/run", "run", [], _args(dry_run=True), lg) is True
    assert "would write manifest" in caplog.text
    assert all(c[0][1] == "cat" for c in fake.calls)


def test_ensure_manifest_write_failure(bak, lg, monkeypatch, caplog):
    fake = FakeGsutil(cat_rc=1, cp_rc=1, cp_err="nope")
    _patch(bak, monkeypatch, fake)
    with caplog.at_level(logging.ERROR, logger="gcp_backup"):
        assert bak.ensure_manifest("gs://b/p/run", "run", [], _args(), lg) is False
    assert "could not write manifest" in caplog.text


# --- main() (in-process) ----------------------------------------------------

def _invoke(bak, monkeypatch, argv):
    monkeypatch.setattr(bak, "DEFAULT_BASE", "")
    monkeypatch.setattr(sys, "argv", ["backup_to_gcp.py", *argv])
    return bak.main()


def _dirs(tmp_path, names, settle=None):
    out = []
    for i, name in enumerate(names):
        d = tmp_path / name
        d.mkdir()
        out.append((d, name, i == settle))
    return out


def test_main_gsutil_missing(bak, monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(bak, "shutil", SimpleNamespace(which=lambda name: None))
    rc = _invoke(bak, monkeypatch,
                 ["--base", "gs://b/p", "--once", "--gsutil", "nope",
                  "--log-file", str(tmp_path / "m.log")])
    assert rc == 2
    assert "could not find" in capsys.readouterr().out


def test_main_requires_base(bak, monkeypatch, tmp_path, capsys):
    _patch(bak, monkeypatch, FakeGsutil())
    rc = _invoke(bak, monkeypatch,
                 ["--once", "--log-file", str(tmp_path / "m.log")])
    assert rc == 3
    assert "no GCS base" in capsys.readouterr().out


def test_main_training_once(bak, monkeypatch, tmp_path, capsys):
    targets = _dirs(tmp_path, ["out", "logs"], settle=0)
    targets.append((tmp_path / "missing", "agent_notes", False))
    monkeypatch.setattr(bak, "TRAINING_TARGETS", targets)
    fake = FakeGsutil()
    _patch(bak, monkeypatch, fake)
    rc = _invoke(bak, monkeypatch,
                 ["--base", "gs://b/p", "--once", "--settle-seconds", "0",
                  "--log-file", str(tmp_path / "m.log")])
    out = capsys.readouterr().out
    assert rc == 0
    assert "backup run 'akbar_arabic_rock_lora' (training)" in out
    assert "skipping missing folder" in out
    assert "pass complete: 2/3 folders synced" in out
    # two rsync calls, no manifest collision (cat absent)
    assert fake.rsync_calls == 2
    # settle target (out/) was synced via the settle path; logs is not settle
    assert len(fake.calls) >= 2


def test_main_run_name_selects_local_output_folder(bak, monkeypatch, tmp_path, capsys):
    # A non-default --run-name must mirror training_folder/<run-name>/, not the
    # default JOB_ROOT, while still writing to <base>/<run-name>/.
    monkeypatch.setattr(bak, "TRAINING_FOLDER", tmp_path)
    (tmp_path / "pron_lora_ar_only_r8").mkdir()
    fake = FakeGsutil()
    _patch(bak, monkeypatch, fake)
    rc = _invoke(bak, monkeypatch,
                 ["--run-name", "pron_lora_ar_only_r8", "--base", "gs://b/p",
                  "--once", "--settle-seconds", "0",
                  "--log-file", str(tmp_path / "m.log")])
    assert rc == 0
    srcs = [c[0][-2] for c in fake.calls if "rsync" in c[0]]
    dsts = [c[0][-1] for c in fake.calls if "rsync" in c[0]]
    assert str(tmp_path / "pron_lora_ar_only_r8") in srcs
    assert "gs://b/p/pron_lora_ar_only_r8/output/" in dsts


def test_main_inference_defaults(bak, monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(bak, "INFERENCE_TARGETS",
                        _dirs(tmp_path, ["out", "prompts"]))
    fake = FakeGsutil()
    _patch(bak, monkeypatch, fake)
    rc = _invoke(bak, monkeypatch,
                 ["--inference", "--base", "gs://b/p", "--once",
                  "--log-file", str(tmp_path / "m.log")])
    out = capsys.readouterr().out
    assert rc == 0
    assert "backup run 'audiocpp_inference' (inference)" in out


def test_main_watch_derives_run_name_and_prefix_root(bak, monkeypatch, tmp_path, capsys):
    d = tmp_path / "my_songs"
    d.mkdir()
    fake = FakeGsutil()
    _patch(bak, monkeypatch, fake)
    rc = _invoke(bak, monkeypatch,
                 ["--watch", str(d), "--base", "gs://b/p", "--once",
                  "--log-file", str(tmp_path / "m.log")])
    out = capsys.readouterr().out
    assert rc == 0
    assert "backup run 'my_songs' (watch)" in out
    rsync, _ = [c for c in fake.calls if "rsync" in c[0]][0]
    assert rsync[-1] == "gs://b/p/my_songs/"


def test_main_watch_subfolders(bak, monkeypatch, tmp_path, capsys):
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir()
    b.mkdir()
    fake = FakeGsutil()
    _patch(bak, monkeypatch, fake)
    rc = _invoke(bak, monkeypatch,
                 ["--watch", f"{a}:one", "--watch", f"{b}:two", "--run-name", "run1",
                  "--base", "gs://b/p", "--once", "--log-file", str(tmp_path / "m.log")])
    assert rc == 0
    dsts = [c[0][-1].rstrip("/") for c in fake.calls if "rsync" in c[0]]
    assert "gs://b/p/run1/one" in dsts
    assert "gs://b/p/run1/two" in dsts


def test_main_watch_missing_dir(bak, monkeypatch, tmp_path, capsys):
    _patch(bak, monkeypatch, FakeGsutil())
    rc = _invoke(bak, monkeypatch,
                 ["--watch", str(tmp_path / "nope"), "--base", "gs://b/p", "--once",
                  "--log-file", str(tmp_path / "m.log")])
    assert rc == 3
    assert "not a directory" in capsys.readouterr().out


def test_main_watch_multiple_without_sub(bak, monkeypatch, tmp_path, capsys):
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir()
    b.mkdir()
    _patch(bak, monkeypatch, FakeGsutil())
    rc = _invoke(bak, monkeypatch,
                 ["--watch", str(a), "--watch", str(b), "--base", "gs://b/p",
                  "--once", "--log-file", str(tmp_path / "m.log")])
    assert rc == 3
    assert ":SUB" in capsys.readouterr().out


def test_main_reserved_run_name(bak, monkeypatch, tmp_path, capsys):
    _patch(bak, monkeypatch, FakeGsutil())
    rc = _invoke(bak, monkeypatch,
                 ["--run-name", "dataset", "--base", "gs://b/p", "--once",
                  "--log-file", str(tmp_path / "m.log")])
    assert rc == 3
    assert "reserved non-run folder" in capsys.readouterr().out


def test_main_extra_keeps_defaults_and_adds(bak, monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(bak, "TRAINING_TARGETS", _dirs(tmp_path, ["out", "logs"]))
    extra = tmp_path / "My Songs"
    extra.mkdir()
    fake = FakeGsutil()
    _patch(bak, monkeypatch, fake)
    rc = _invoke(bak, monkeypatch,
                 ["--base", "gs://b/p", "--once", "--extra", str(extra),
                  "--log-file", str(tmp_path / "m.log")])
    assert rc == 0
    dsts = [c[0][-1].rstrip("/") for c in fake.calls if "rsync" in c[0]]
    # defaults are KEPT and the extra is ADDED (basename slugified)
    assert "gs://b/p/akbar_arabic_rock_lora/out" in dsts
    assert "gs://b/p/akbar_arabic_rock_lora/logs" in dsts
    assert "gs://b/p/akbar_arabic_rock_lora/My-Songs" in dsts
    assert len(dsts) == 3


def test_main_extra_with_explicit_sub(bak, monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(bak, "TRAINING_TARGETS", _dirs(tmp_path, ["out"]))
    extra = tmp_path / "songs"
    extra.mkdir()
    fake = FakeGsutil()
    _patch(bak, monkeypatch, fake)
    rc = _invoke(bak, monkeypatch,
                 ["--base", "gs://b/p", "--once", "--extra", f"{extra}:wavs",
                  "--log-file", str(tmp_path / "m.log")])
    assert rc == 0
    dsts = [c[0][-1].rstrip("/") for c in fake.calls if "rsync" in c[0]]
    assert "gs://b/p/akbar_arabic_rock_lora/wavs" in dsts


def test_main_extra_with_inference(bak, monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(bak, "INFERENCE_TARGETS", _dirs(tmp_path, ["out", "prompts"]))
    extra = tmp_path / "notes"
    extra.mkdir()
    fake = FakeGsutil()
    _patch(bak, monkeypatch, fake)
    rc = _invoke(bak, monkeypatch,
                 ["--inference", "--base", "gs://b/p", "--once",
                  "--extra", str(extra), "--log-file", str(tmp_path / "m.log")])
    assert rc == 0
    dsts = [c[0][-1].rstrip("/") for c in fake.calls if "rsync" in c[0]]
    assert "gs://b/p/audiocpp_inference/out" in dsts
    assert "gs://b/p/audiocpp_inference/notes" in dsts


def test_main_watch_plus_extra_still_replaces_defaults(bak, monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(bak, "TRAINING_TARGETS", _dirs(tmp_path, ["out"]))
    watched, added = tmp_path / "watched", tmp_path / "added"
    watched.mkdir()
    added.mkdir()
    fake = FakeGsutil()
    _patch(bak, monkeypatch, fake)
    rc = _invoke(bak, monkeypatch,
                 ["--watch", str(watched), "--extra", str(added), "--base", "gs://b/p",
                  "--once", "--log-file", str(tmp_path / "m.log")])
    assert rc == 0
    dsts = [c[0][-1].rstrip("/") for c in fake.calls if "rsync" in c[0]]
    assert "gs://b/p/watched" in dsts          # watch maps to the prefix root
    assert "gs://b/p/watched/added" in dsts    # extra added on top
    assert "gs://b/p/watched/out" not in dsts  # default still dropped by --watch


def test_main_extra_missing_dir(bak, monkeypatch, tmp_path, capsys):
    _patch(bak, monkeypatch, FakeGsutil())
    rc = _invoke(bak, monkeypatch,
                 ["--base", "gs://b/p", "--once", "--extra", str(tmp_path / "nope"),
                  "--log-file", str(tmp_path / "m.log")])
    assert rc == 3
    assert "not a directory" in capsys.readouterr().out


def test_main_extra_sub_collides_with_default(bak, monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(bak, "TRAINING_TARGETS", _dirs(tmp_path, ["out", "logs"]))
    extra = tmp_path / "x"
    extra.mkdir()
    _patch(bak, monkeypatch, FakeGsutil())
    rc = _invoke(bak, monkeypatch,
                 ["--base", "gs://b/p", "--once", "--extra", f"{extra}:logs",
                  "--log-file", str(tmp_path / "m.log")])
    assert rc == 3
    assert "duplicate remote subfolder" in capsys.readouterr().out


def test_main_extra_same_basename_collides(bak, monkeypatch, tmp_path, capsys):
    (tmp_path / "a" / "songs").mkdir(parents=True)
    (tmp_path / "b" / "songs").mkdir(parents=True)
    _patch(bak, monkeypatch, FakeGsutil())
    rc = _invoke(bak, monkeypatch,
                 ["--base", "gs://b/p", "--once",
                  "--extra", str(tmp_path / "a" / "songs"),
                  "--extra", str(tmp_path / "b" / "songs"),
                  "--log-file", str(tmp_path / "m.log")])
    assert rc == 3
    assert "duplicate remote subfolder" in capsys.readouterr().out


def test_main_dry_run_uploads_nothing(bak, monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(bak, "TRAINING_TARGETS", _dirs(tmp_path, ["out"]))
    fake = FakeGsutil()
    _patch(bak, monkeypatch, fake)
    rc = _invoke(bak, monkeypatch,
                 ["--base", "gs://b/p", "--once", "--dry-run",
                  "--log-file", str(tmp_path / "m.log")])
    out = capsys.readouterr().out
    assert rc == 0
    assert "dry-run: would write manifest" in out
    assert fake.rsync_calls == 0
    assert "cp" not in fake.subcommands()


def test_main_sync_failure_is_counted_not_fatal(bak, monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(bak, "TRAINING_TARGETS", _dirs(tmp_path, ["out", "logs"]))
    fake = FakeGsutil(rsync_rc=1, rsync_err="x")
    _patch(bak, monkeypatch, fake)
    rc = _invoke(bak, monkeypatch,
                 ["--base", "gs://b/p", "--once", "--log-file", str(tmp_path / "m.log")])
    out = capsys.readouterr().out
    assert rc == 0
    assert "pass complete: 0/2 folders synced" in out


def test_main_manifest_failure_aborts(bak, monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(bak, "TRAINING_TARGETS", _dirs(tmp_path, ["out"]))
    existing = json.dumps({"run_name": "other", "prefix": "gs://b/p/akbar_arabic_rock_lora"})
    _patch(bak, monkeypatch, FakeGsutil(cat_rc=0, cat_out=existing))
    rc = _invoke(bak, monkeypatch,
                 ["--base", "gs://b/p", "--once", "--log-file", str(tmp_path / "m.log")])
    assert rc == 3
    assert "already belongs" in capsys.readouterr().out


def test_main_interrupt_stops_cleanly(bak, monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(bak, "TRAINING_TARGETS", _dirs(tmp_path, ["out"]))
    fake = FakeGsutil(interrupt_on_rsync=2)
    _patch(bak, monkeypatch, fake)
    slept = []
    monkeypatch.setattr(bak.time, "sleep", lambda s: slept.append(s))
    rc = _invoke(bak, monkeypatch,
                 ["--base", "gs://b/p", "--interval-minutes", "1",
                  "--log-file", str(tmp_path / "m.log")])
    out = capsys.readouterr().out
    assert rc == 0
    assert fake.rsync_calls == 2          # second pass raised KeyboardInterrupt
    assert slept                          # interval sleep happened between passes
    assert "interrupted; last completed pass" in out


def test_module_main_guard(tmp_path, monkeypatch):
    # covers `if __name__ == "__main__": sys.exit(main())` via runpy
    monkeypatch.setattr(sys, "argv",
                        ["backup_to_gcp.py", "--gsutil", "/nonexistent/gsutil",
                         "--log-file", str(tmp_path / "m.log")])
    with pytest.raises(SystemExit) as ei:
        runpy.run_path(str(SCRIPT), run_name="__main__")
    assert ei.value.code == 2
