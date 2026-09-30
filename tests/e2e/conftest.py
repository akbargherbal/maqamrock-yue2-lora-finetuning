"""e2e fixtures: fake device probe + recorded replay runner (plan §8).

The device boundary is two touchpoints (plan §2): the probe (`gpu_info`) and the
compute (`run_one.sh` via the `runner=` seam). This conftest substitutes exactly
those and leaves the rest of `generate.py` untouched; `run_generate` drives the
real `main` so preflight, fingerprint, materialize, run_batch, summary and
`out/latest` are all the production code path (plan §5.1).
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = REPO_ROOT / "tests" / "fixtures"

_FAKE_GPU = {"name": "Tesla T4", "memory_used": "100",
             "memory_total": "15360", "compute_cap": "7.5"}


def _load_replay():
    name = "e2e_replay"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(
        name, Path(__file__).resolve().parent / "replay.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def replay_mod():
    return _load_replay()


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return FIXTURES


@pytest.fixture(scope="session")
def recorded_batch_path(fixtures_dir) -> Path:
    return fixtures_dir / "recorded_batch.json"


@pytest.fixture(scope="session")
def recorded_batch(replay_mod, recorded_batch_path) -> dict:
    return replay_mod.load_recorded_batch(recorded_batch_path)


@pytest.fixture
def replay_runner(replay_mod, recorded_batch):
    return replay_mod.make_replay_runner(recorded_batch)


@pytest.fixture(scope="session")
def fake_gpu() -> dict:
    """The recorded T4 probe, the substitute for `generate.gpu_info` (plan §2)."""
    return dict(_FAKE_GPU)


@pytest.fixture
def staged_inference(gen, tmp_path, monkeypatch) -> SimpleNamespace:
    """Stage every file preflight demands in tmp and point `generate` at them."""
    run_one = tmp_path / "run_one.sh"
    run_one.write_text("#!/bin/sh\n", encoding="utf-8")
    binp = tmp_path / "bin" / "audiocpp_cli"
    binp.parent.mkdir()
    binp.write_text("x", encoding="utf-8")
    binp.chmod(0o755)
    model = tmp_path / "model"
    (model / "sidecars").mkdir(parents=True)
    (model / gen.MODEL_GGUF).write_bytes(b"m")
    (model / gen.VAE_GGUF).write_bytes(b"v")
    ar = tmp_path / "ar.safetensors"
    nar = tmp_path / "nar.safetensors"
    ar.write_bytes(b"a")
    nar.write_bytes(b"n")
    monkeypatch.setattr(gen, "RUN_ONE", run_one)
    monkeypatch.setattr(gen, "BIN", binp)
    monkeypatch.setattr(gen, "MODEL_DIR", model)
    monkeypatch.setattr(gen, "ROOT", tmp_path)
    return SimpleNamespace(root=tmp_path, run_one=run_one, bin=binp, model=model,
                           ar=ar, nar=nar)


@pytest.fixture
def run_generate(gen, fake_gpu, monkeypatch):
    """Invoke `generate.main` with only the probe and the compute runner replaced."""
    def invoke(argv, *, runner):
        monkeypatch.setattr(gen, "gpu_info", lambda: fake_gpu)
        monkeypatch.setattr(gen, "training_active", lambda: None)
        real_run_batch = gen.run_batch

        def with_runner(*a, **k):
            k["runner"] = runner
            return real_run_batch(*a, **k)

        monkeypatch.setattr(gen, "run_batch", with_runner)
        return gen.main(argv)

    return invoke
