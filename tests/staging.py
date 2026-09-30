"""Shared inference-workspace staging for the GPU-free tests (plan §5.1).

Both the T0 unit tests (`tests/test_generate.py`) and the T2 e2e conftest stage
the same minimal `INFERENCE` workspace: a `run_one.sh`, an executable
`audiocpp_cli`, a model dir with the GGUF stubs + `sidecars/`, and an AR/NAR
adapter pair. Keeping it in one place means the e2e layer provably exercises the
same preflight contract the unit layer already pins.
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace


def stage_inference_tree(gen, tmp_path: Path, monkeypatch, *, bin_exec: bool = True):
    """Stage the preflight-required files in `tmp_path` and point `gen` at them.

    Returns a namespace with `root`, `run_one`, `bin`, `model`, `ar`, `nar`.
    """
    run_one = tmp_path / "run_one.sh"
    run_one.write_text("#!/bin/sh\n", encoding="utf-8")
    binp = tmp_path / "bin" / "audiocpp_cli"
    binp.parent.mkdir()
    binp.write_text("x", encoding="utf-8")
    binp.chmod(0o755 if bin_exec else 0o644)
    model = tmp_path / "model"
    (model / "sidecars").mkdir(parents=True)
    (model / gen.MODEL_GGUF).write_bytes(b"m")
    (model / gen.VAE_GGUF).write_bytes(b"v")
    ar, nar = tmp_path / "ar", tmp_path / "nar"
    ar.write_bytes(b"a")
    nar.write_bytes(b"n")
    monkeypatch.setattr(gen, "RUN_ONE", run_one)
    monkeypatch.setattr(gen, "BIN", binp)
    monkeypatch.setattr(gen, "MODEL_DIR", model)
    monkeypatch.setattr(gen, "ROOT", tmp_path)
    return SimpleNamespace(root=tmp_path, run_one=run_one, bin=binp, model=model,
                           ar=ar, nar=nar)
