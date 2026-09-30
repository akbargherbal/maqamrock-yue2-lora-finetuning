"""J10 -- training lifecycle: start -> status -> SIGINT stop (plan §5, T3).

Drives the **real** `train_ctl.py` in a subprocess against a **real detached
process** (`tests/e2e/fake_run.py` standing in for ai-toolkit's `run.py`) that
writes a real `loss_log.db` and answers SIGINT the way ai-toolkit does. No
torch, no GPU, no `/content`.
"""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CTL = REPO / "train_ctl.py"
MONITOR = REPO / "monitor_loss.py"


def _ctl(fake_env, *args):
    return subprocess.run(
        [sys.executable, str(CTL), *args,
         "--ai-toolkit", str(fake_env.ai),
         "--config", str(fake_env.cfg),
         "--logs-dir", str(fake_env.logs),
         "--run-name", fake_env.run_name],
        capture_output=True, text=True, timeout=40)


def _wait_for(pred, timeout=8.0):
    end = time.time() + timeout
    while time.time() < end:
        if pred():
            return True
        time.sleep(0.1)
    return False


def test_j10_start_status_sigint_stop(fake_training_env):
    env = fake_training_env
    assert _ctl(env, "start").returncode == 0

    pidfile = env.logs / "train.pid"
    assert _wait_for(pidfile.exists)
    pid = int(pidfile.read_text())
    try:
        # its own session: the terminal's Ctrl+C can never reach the child
        assert os.getsid(pid) == pid

        # the detached process is really training: it writes a real metrics db
        db = env.ai / "loss_log.db"
        assert _wait_for(db.exists)
        assert _wait_for(lambda: db.stat().st_size > 0)

        # status reads the same tree and reports it running
        st = _ctl(env, "status")
        assert st.returncode == 0
        assert "running" in st.stdout and str(pid) in st.stdout

        # a second copy of the same run is refused
        assert _ctl(env, "start").returncode == 1

        # clean, checkpoint-safe stop (SIGINT), waits for "Job stopped"
        assert _ctl(env, "stop", "--timeout", "15").returncode == 0
        assert _wait_for(lambda: not os.path.isdir(f"/proc/{pid}"))
        assert "Job stopped" in (env.logs / "train.log").read_text(encoding="utf-8")
        assert not pidfile.exists()

        # the db the fake wrote is readable by the real monitor
        mon = subprocess.run([sys.executable, str(MONITOR), str(db)],
                             capture_output=True, text=True, timeout=20)
        assert mon.returncode == 0, mon.stderr
        assert "step " in mon.stdout and "steps/sec" in mon.stdout
    finally:
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
