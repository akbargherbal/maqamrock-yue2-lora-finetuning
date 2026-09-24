"""Unit tests for offline_ar_loss_replay.py (CPU-only, no model load).

The replay itself needs the YuE2 base checkpoint + semantic head and is verified
out-of-band by the benchmark run; these tests pin the pure helpers (checkpoint
mapping, val-pair discovery, averaging, config parsing, CLI defaults) so they are
usable without ai-toolkit or torch.
"""
import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "offline_ar_loss_replay", REPO_ROOT / "offline_ar_loss_replay.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["offline_ar_loss_replay"] = mod
    spec.loader.exec_module(mod)
    return mod


M = _load_module()


def test_checkpoint_map_has_four_trainable_artifacts():
    assert set(M.CHECKPOINT_FILES) == {"1525", "3050", "4575", "final"}
    # no _000006100 numbered file: the post-loop no-step save IS the step-6100 file
    assert M.CHECKPOINT_FILES["final"] == "pron_lora_ar_only_r8.safetensors"


def test_resolve_checkpoint_found_and_missing(tmp_path):
    name = "pron_lora_ar_only_r8_000001525.safetensors"
    (tmp_path / name).write_bytes(b"x")
    assert M.resolve_checkpoint(tmp_path, "1525") == tmp_path / name
    with pytest.raises(M.ReplayError, match="adapter not staged"):
        M.resolve_checkpoint(tmp_path, "final")


def test_resolve_checkpoint_rejects_unknown_name(tmp_path):
    with pytest.raises(M.ReplayError, match="unknown checkpoint"):
        M.resolve_checkpoint(tmp_path, "9999")


def test_list_val_pairs_skips_unpaired(tmp_path):
    (tmp_path / "a.mp3").write_bytes(b"x")
    (tmp_path / "a.txt").write_text("cap", encoding="utf-8")
    (tmp_path / "b.mp3").write_bytes(b"x")  # mp3 with no txt -> skipped
    pairs = M.list_val_pairs(tmp_path)
    assert [p[0] for p in pairs] == ["a"]


def test_list_val_pairs_empty_raises(tmp_path):
    with pytest.raises(M.ReplayError, match=r"no .*pairs found"):
        M.list_val_pairs(tmp_path)


def test_mean_losses_ignores_missing_kl():
    rs = [
        M.ItemResult(0, "a", 10, 100, 4.0, 1.0, 1.0, 2.0),
        M.ItemResult(1, "b", 10, 100, 6.0, None, 1.0, 4.0),
    ]
    ce, kl = M.mean_losses(rs)
    assert ce == pytest.approx(5.0)
    assert kl == pytest.approx(1.0)


def test_load_config_sections_reads_real_config():
    model, network = M.load_config_sections(M.DEFAULT_CONFIG)
    assert model["arch"] == "yue2"
    assert model["model_kwargs"]["cot"] == "off"
    assert model["model_kwargs"]["ar_kl_weight"] == 0.2
    assert network["linear"] == 8 and network["linear_alpha"] == 8
    assert network["network_kwargs"]["ignore_if_contains"] == ["transformer.nar"]


def test_arg_parser_defaults():
    args = M.build_arg_parser().parse_args([])
    assert args.checkpoint == "final"
    assert args.limit is None
    assert args.device == "cpu"
    assert args.val_dir == Path("/content/pron_dataset/val")


def test_no_hardcoded_cuda_in_source():
    src = (REPO_ROOT / "offline_ar_loss_replay.py").read_text()
    assert "torch.cuda" not in src
