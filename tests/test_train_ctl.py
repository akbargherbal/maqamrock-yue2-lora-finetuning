"""GPU-free tests for `train_ctl.py` (detached launch / clean SIGINT stop).

No ai-toolkit, no GPU, no `/content`: a fake `run.py` stands in, and the CLI is
driven end to end via subprocess. The key safety properties asserted here are
the ones that bit us in review:
  * the training child runs in its **own session** (a terminal Ctrl+C can't reach it);
  * `stop` delivers a SIGINT that the run handles (clean, checkpoint-safe);
  * `start` refuses a second copy of the same run;
  * `stop` refuses to signal a PID that isn't our run.
"""
import importlib.util
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "train_ctl.py"

DUMMY_RUN = '''
import os, signal, sys, time
log = sys.argv[sys.argv.index("-l") + 1]
def handler(sig, frm):
    with open(log, "a") as fh:
        fh.write("Job stopped\\n")
    sys.exit(0)
signal.signal(signal.SIGINT, handler)
print("dummy running", flush=True)
time.sleep(300)
'''

# give `_proc_state` a moment to observe a friendly-exit vs a zombie
_SETTLE = 0.1


def _load():
    spec = importlib.util.spec_from_file_location("train_ctl", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["train_ctl"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def tctl():
    return _load()


@pytest.fixture
def fake_env(tmp_path):
    ai = tmp_path / "ai-toolkit"
    ai.mkdir()
    (ai / "run.py").write_text(DUMMY_RUN)
    cfg = tmp_path / "fake_cfg.yml"
    cfg.write_text("name: demo\n")
    return {"ai": ai, "cfg": cfg, "logs": tmp_path / "logs", "run_name": "demo"}


def _cli(fake_env, *args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args,
         "--ai-toolkit", str(fake_env["ai"]),
         "--config", str(fake_env["cfg"]),
         "--logs-dir", str(fake_env["logs"]),
         "--run-name", fake_env["run_name"]],
        capture_output=True, text=True, timeout=40)


def _wait_for(pred, timeout=6.0):
    end = time.time() + timeout
    while time.time() < end:
        if pred():
            return True
        time.sleep(_SETTLE)
    return False


def test_dry_run_launches_nothing(fake_env):
    result = _cli(fake_env, "start", "--dry-run")
    assert result.returncode == 0
    assert "run.py" in result.stdout
    assert not (fake_env["logs"] / "train.pid").exists()


def test_start_detaches_then_stop_is_clean(fake_env):
    assert _cli(fake_env, "start").returncode == 0
    pidfile = fake_env["logs"] / "train.pid"
    assert _wait_for(pidfile.exists)
    pid = int(pidfile.read_text())
    try:
        # own session: the terminal's Ctrl+C can never reach this process
        assert os.getsid(pid) == pid
        assert _cli(fake_env, "status").returncode == 0
        # a second copy of the same run must be refused
        assert _cli(fake_env, "start").returncode == 1
        # clean, checkpoint-safe stop
        assert _cli(fake_env, "stop", "--timeout", "15").returncode == 0
        assert _wait_for(lambda: not os.path.isdir(f"/proc/{pid}"))
        assert "Job stopped" in (fake_env["logs"] / "train.log").read_text()
        assert not pidfile.exists()
    finally:
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def test_stop_refuses_foreign_pid(fake_env):
    fake_env["logs"].mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen(["sleep", "60"])
    try:
        (fake_env["logs"] / "train.pid").write_text(str(proc.pid))
        result = _cli(fake_env, "stop")
        assert result.returncode == 1
        assert "refus" in (result.stderr + result.stdout).lower()
        assert proc.poll() is None  # the foreign process is untouched
    finally:
        proc.terminate()
        proc.wait(timeout=5)


def test_cmdline_matches(tctl, tmp_path):
    cfg = tmp_path / "x.yml"
    assert tctl._cmdline_matches("python run.py /a/x.yml -l /log", cfg, "x")
    assert not tctl._cmdline_matches("/bin/sleep 60", cfg, "x")
    assert not tctl._cmdline_matches("", cfg, "x")
