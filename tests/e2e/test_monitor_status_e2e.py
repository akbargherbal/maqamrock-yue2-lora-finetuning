"""J11 -- monitor + status on recorded artifacts (plan §5, T3).

Two real reads:
  * `monitor_loss.py` as a subprocess against a `loss_log.db` built from
    `tests/fixtures/loss_log.spec.json` (exact step/rate/ETA).
  * `status.py`'s training and inference sections pointed at a spec-built db and
    at a run produced by the real `generate.main` (+ replay runner).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
MONITOR = REPO / "monitor_loss.py"


def test_j11_monitor_reads_spec_db(loss_log_spec, build_loss_db, tmp_path):
    db = build_loss_db(tmp_path / "job" / "loss_log.db", loss_log_spec)
    result = subprocess.run(
        [sys.executable, str(MONITOR), str(db),
         "--key", "loss", "--history", "3", "--total-steps", "40"],
        capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    out = result.stdout
    assert "step 40" in out
    assert "loss:" in out and "nar_flow:" in out
    assert "~2.000 steps/sec" in out              # 40 steps at 0.5 s each
    assert "ETA to step 40" in out
    assert "step 38:" in out and "step 40:" in out  # the 3-value history


def test_j11_status_training_section(status_mod, loss_log_spec, build_loss_db,
                                     tmp_path, monkeypatch):
    job = tmp_path / "job"
    db = build_loss_db(job / "loss_log.db", loss_log_spec)
    log = tmp_path / "train.log"
    log.write_text("step 38 loss 0.8\nstep 40 loss 0.7\n", encoding="utf-8")
    pidfile = tmp_path / "train.pid"
    proc = subprocess.Popen(["sleep", "60"])
    pidfile.write_text(str(proc.pid), encoding="utf-8")
    try:
        monkeypatch.setattr(status_mod, "ON_COLAB", True)
        monkeypatch.setattr(status_mod, "JOB_ROOT", job)
        monkeypatch.setattr(status_mod, "LOSS_DB", db)
        monkeypatch.setattr(status_mod, "TRAIN_PID", pidfile)
        monkeypatch.setattr(status_mod, "TRAIN_LOG", log)
        lines: list[str] = []
        active = status_mod.section_training(lines)
        text = "\n".join(lines)
        assert active is True
        assert f"RUNNING pid {proc.pid}" in text
        assert "step 40" in text
        assert "train.log tail:" in text and "loss 0.7" in text
    finally:
        proc.terminate()
        proc.wait(timeout=5)


def test_j11_status_inference_section_from_real_run(status_mod, gen, tmp_path,
                                                    staged_inference, run_generate,
                                                    replay_runner, monkeypatch):
    data = {"songs": [{"name": "Hijaz", "style": "arabmaqamrock hijaz",
                       "lyrics": "يا صَباحَ", "seed": 20260924, "cap": 6500}]}
    input_path = tmp_path / "j11.json"
    input_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    out_root = staged_inference.root / "out"
    assert run_generate(
        [str(input_path), "--out-dir", str(out_root / "j11"), "--no-trigger",
         "--lora-ar", str(staged_inference.ar), "--lora-nar", str(staged_inference.nar)],
        runner=replay_runner) == 0

    monkeypatch.setattr(status_mod, "ON_COLAB", True)
    monkeypatch.setattr(status_mod, "INFER_OUT", out_root)
    lines: list[str] = []
    status_mod.section_inference(lines)
    text = "\n".join(lines)
    assert "inference: idle" in text
    assert "1/1 wavs" in text
    assert "ok: 1" in text
