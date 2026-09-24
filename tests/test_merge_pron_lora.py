"""Unit tests for merge_pron_lora.py (CPU-only, synthetic bf16 tensors).

The merge/convert end-to-end invariant (alpha=0 reproducing the live converted
v2 adapters byte-for-byte) needs the real files and the audio.cpp converter, so
it is verified out-of-band; these tests pin the merge logic itself.
"""
import importlib.util
import sys
from pathlib import Path

import pytest
import torch
from safetensors.torch import load_file, save_file

REPO_ROOT = Path(__file__).resolve().parents[1]

MODS = ["self_attn.qkv_proj", "mlp.down_proj"]
LAYERS = [0, 1]
IN_DIM, OUT_DIM = 5, 7
STYLE_RANK, PRON_RANK = 3, 2


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "merge_pron_lora", REPO_ROOT / "merge_pron_lora.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["merge_pron_lora"] = mod
    spec.loader.exec_module(mod)
    return mod


M = _load_module()


def build(rank, seed, groups=("text_encoders", "diffusion_model")):
    g = torch.Generator().manual_seed(seed)
    out = {}
    for group in groups:
        for layer in LAYERS:
            for mod in MODS:
                base = f"{group}.model.layers.{layer}.{mod}"
                out[f"{base}.lora_A.weight"] = torch.randn(
                    rank, IN_DIM, generator=g
                ).to(torch.bfloat16)
                out[f"{base}.lora_B.weight"] = torch.randn(
                    OUT_DIM, rank, generator=g
                ).to(torch.bfloat16)
    return out


@pytest.fixture
def v2():
    return build(STYLE_RANK, seed=1)


@pytest.fixture
def pron():
    return build(PRON_RANK, seed=2, groups=("text_encoders",))


def ar_keys(d):
    return sorted(k for k in d if k.startswith("text_encoders."))


def nar_keys(d):
    return sorted(k for k in d if k.startswith("diffusion_model."))


def test_alpha_zero_is_v2_verbatim(v2, pron):
    merged, stats = M.merge(v2, pron, 0.0)
    assert set(merged) == set(v2)
    assert all(torch.equal(merged[k], v2[k]) for k in v2)
    assert stats["ar_rank"] == STYLE_RANK
    assert stats["nar_rank"] == STYLE_RANK
    assert stats["nar_tensors_zero_padded"] == 0
    assert stats["ar_tensors_merged"] == len(ar_keys(v2))
    assert stats["nar_tensors_passed_through"] == len(nar_keys(v2))


def test_alpha_one_rank_concat_and_delta(v2, pron):
    merged, stats = M.merge(v2, pron, 1.0)
    assert stats["ar_rank"] == STYLE_RANK + PRON_RANK
    # NAR must be padded to the same rank so the converter's uniform-rank guard passes
    assert stats["nar_rank"] == STYLE_RANK + PRON_RANK
    assert stats["nar_tensors_zero_padded"] == len(nar_keys(v2))

    for base in [k.rsplit(".lora_", 1)[0] for k in ar_keys(v2) if k.endswith(".lora_A.weight")]:
        a_m, b_m = merged[base + ".lora_A.weight"], merged[base + ".lora_B.weight"]
        assert a_m.shape == (STYLE_RANK + PRON_RANK, IN_DIM)
        assert b_m.shape == (OUT_DIM, STYLE_RANK + PRON_RANK)
        delta = b_m.float() @ a_m.float()
        want = v2[base + ".lora_B.weight"].float() @ v2[base + ".lora_A.weight"].float()
        want = want + pron[base + ".lora_B.weight"].float() @ pron[base + ".lora_A.weight"].float()
        assert torch.allclose(delta, want, rtol=1e-2, atol=1e-2)

    for base in [k.rsplit(".lora_", 1)[0] for k in nar_keys(v2) if k.endswith(".lora_A.weight")]:
        a_m, b_m = merged[base + ".lora_A.weight"], merged[base + ".lora_B.weight"]
        assert a_m.shape == (STYLE_RANK + PRON_RANK, IN_DIM)
        assert b_m.shape == (OUT_DIM, STYLE_RANK + PRON_RANK)
        assert torch.equal(a_m[:STYLE_RANK], v2[base + ".lora_A.weight"])
        assert torch.equal(b_m[:, :STYLE_RANK], v2[base + ".lora_B.weight"])
        assert not a_m[STYLE_RANK:].any() and not b_m[:, STYLE_RANK:].any()


def test_alpha_half_scales_pron_only(v2, pron):
    merged, _ = M.merge(v2, pron, 0.5)
    base = "text_encoders.model.layers.0.self_attn.qkv_proj"
    a_m, b_m = merged[base + ".lora_A.weight"], merged[base + ".lora_B.weight"]
    assert torch.equal(a_m[:STYLE_RANK], v2[base + ".lora_A.weight"])
    assert torch.equal(a_m[STYLE_RANK:], pron[base + ".lora_A.weight"])
    scaled = (pron[base + ".lora_B.weight"].float() * 0.5).to(torch.bfloat16)
    assert torch.equal(b_m[:, STYLE_RANK:], scaled)


def test_pron_with_nar_key_fails(v2, pron):
    bad = dict(pron)
    bad["diffusion_model.model.layers.0.mlp.down_proj.lora_A.weight"] = torch.zeros(
        PRON_RANK, IN_DIM, dtype=torch.bfloat16
    )
    with pytest.raises(M.MergeError, match="not AR-only"):
        M.merge(v2, bad, 1.0)


def test_ar_key_set_mismatch_fails(v2, pron):
    missing = dict(pron)
    del missing["text_encoders.model.layers.1.mlp.down_proj.lora_B.weight"]
    with pytest.raises(M.MergeError, match="AR key sets differ"):
        M.merge(v2, missing, 1.0)


def test_extra_v2_ar_key_fails(v2, pron):
    extra = dict(v2)
    extra["text_encoders.model.layers.9.self_attn.qkv_proj.lora_A.weight"] = torch.zeros(
        STYLE_RANK, IN_DIM, dtype=torch.bfloat16
    )
    with pytest.raises(M.MergeError, match="AR key sets differ"):
        M.merge(extra, pron, 1.0)


def test_alpha_not_rank_refuses(v2, pron):
    bad = dict(v2)
    bad["text_encoders.model.layers.0.self_attn.qkv_proj.alpha"] = torch.tensor(99.0)
    with pytest.raises(M.MergeError, match="alpha key"):
        M.merge(bad, pron, 1.0)


def test_alpha_equal_rank_is_dropped(v2, pron):
    ok = dict(v2)
    ok["text_encoders.model.layers.0.self_attn.qkv_proj.alpha"] = torch.tensor(
        float(STYLE_RANK)
    )
    merged, _ = M.merge(ok, pron, 1.0)
    assert not any(k.endswith(".alpha") for k in merged)


def test_run_writes_metadata_and_roundtrips(tmp_path, v2, pron):
    v2p, prp = tmp_path / "v2.safetensors", tmp_path / "pron.safetensors"
    save_file(v2, str(v2p), metadata={"format": "pt", "name": "v2"})
    save_file(pron, str(prp), metadata={"format": "pt", "name": "pron"})
    out = tmp_path / "merged" / "merged.safetensors"
    stats, meta, digest, size, elapsed = M.run(v2p, prp, 0.5, out, prp.name)
    assert out.is_file() and size == out.stat().st_size
    assert meta["format"] == "pt" and meta["name"] == "v2"
    assert meta["merge_alpha"] == "0.5"
    assert meta["merge_pron_checkpoint"] == "pron.safetensors"
    assert meta["merge_ar_rank"] == str(STYLE_RANK + PRON_RANK)
    loaded = load_file(str(out))
    assert set(loaded) == set(v2)
    assert stats["nar_tensors_zero_padded"] > 0


def test_checkpoint_mapping():
    assert set(M.PRON_CHECKPOINTS) == {"1525", "3050", "4575", "final"}


def test_no_accelerator_calls_in_source():
    src = (REPO_ROOT / "merge_pron_lora.py").read_text()
    assert "torch.cuda" not in src
    assert ".cuda(" not in src
