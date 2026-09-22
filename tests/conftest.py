"""Shared fixtures for the GPU-free test suite.

The generator/converter are plain scripts, not installed packages, so they are
loaded by path and registered in `sys.modules` (dataclasses resolve
`cls.__module__` through it). No test touches the GPU or /content.
"""
import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
INFERENCE_DIR = REPO_ROOT / "INFERENCE"

# captured before the autouse fixture replaces it, so it can be tested directly
_ORIGINAL_WAIT_VRAM_FREE: dict = {}


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def gen():
    module = _load_module("generate", INFERENCE_DIR / "generate.py")
    _ORIGINAL_WAIT_VRAM_FREE["fn"] = module.wait_vram_free
    return module


@pytest.fixture(scope="session")
def dur(gen):
    # generate.py imports duration_cap, so it is already loaded under this name
    return sys.modules["duration_cap"]


@pytest.fixture(scope="session")
def sun(gen):
    # sun imports `generate` itself; loading it here keeps one module identity
    return _load_module("suno_to_songs", INFERENCE_DIR / "suno_to_songs.py")


@pytest.fixture
def manifest_path() -> Path:
    return REPO_ROOT / "manifests" / "workspace_manifest.json"


@pytest.fixture
def lyrics_ar() -> str:
    return ("يا صَباحَ الوَطَنِ المَشدودِ بِالأَلَمِ\n"
            "نادِ الفَجْرَ وَخُذْ بِيَ إلى النَّدَى...")


@pytest.fixture(autouse=True)
def _no_vram_sleep(gen, monkeypatch):
    """Never actually poll/sleep on a GPU-capable host during unit tests."""
    monkeypatch.setattr(gen, "wait_vram_free", lambda *a, **k: None)


@pytest.fixture
def real_wait_vram_free(gen):
    """The unpatched `wait_vram_free`, for tests that exercise it directly."""
    return _ORIGINAL_WAIT_VRAM_FREE["fn"]
