"""Unit tests for INFERENCE/prepare_ab_eval.py (GPU-free, ffmpeg-free).

The audio files are dummy bytes: `--audio-format copy` is byte-preserving, so
the tests exercise the discovery/labeling/naming/key logic without any codec.
"""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load():
    path = REPO_ROOT / "INFERENCE" / "prepare_ab_eval.py"
    spec = importlib.util.spec_from_file_location("prepare_ab_eval", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["prepare_ab_eval"] = mod
    spec.loader.exec_module(mod)
    return mod


ab = _load()


def make(root: Path, rel: str, data: bytes | None = None) -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data if data is not None else rel.encode())
    return p


def rec_by_file(result: dict) -> dict:
    return {r["blind_file"]: r for r in result["records"]}


# --- flat layout ------------------------------------------------------------

def test_flat_two_variants_blind_and_key(tmp_path):
    root = tmp_path / "src"
    make(root, "variant_alpha/t1.wav", b"AAA")
    make(root, "variant_beta/t1.wav", b"BBB")
    out = tmp_path / "out"

    res = ab.setup_ab_evaluation(root, out, seed=1)
    recs = rec_by_file(res)
    assert set(recs) == {"t1_A.wav", "t1_B.wav"}
    assert {r["label"] for r in res["records"]} == {"A", "B"}
    assert {r["variant"] for r in res["records"]} == {"variant_alpha", "variant_beta"}
    # byte-preserving copy
    for r in res["records"]:
        assert (out / r["blind_file"]).read_bytes() == (root / r["source_path"]).read_bytes()

    # EVAL.txt is public: no variant names. KEYS.txt is secret: mapping present.
    eval_txt = (out / "EVAL.txt").read_text()
    keys_txt = (out / "KEYS.txt").read_text()
    assert "variant_alpha" not in eval_txt and "variant_beta" not in eval_txt
    assert "variant_alpha" in keys_txt and "variant_beta" in keys_txt


# --- categories + duplicate stems ------------------------------------------

def test_categories_and_duplicate_stems_get_prefix(tmp_path):
    root = tmp_path / "src"
    for cat in ("catA", "catB"):
        for var in ("treat", "control"):
            make(root, f"{cat}/{var}/track.wav")
    out = tmp_path / "out"

    res = ab.setup_ab_evaluation(root, out, seed=2)
    names = {r["blind_file"] for r in res["records"]}
    assert names == {
        "catA_track_A.wav", "catA_track_B.wav",
        "catB_track_A.wav", "catB_track_B.wav",
    }
    assert {r["category"] for r in res["records"]} == {"catA", "catB"}


def test_category_filter(tmp_path):
    root = tmp_path / "src"
    for cat in ("keep", "drop"):
        for var in ("x", "y"):
            make(root, f"{cat}/{var}/t.wav")
    res = ab.setup_ab_evaluation(root, tmp_path / "out",
                                 categories=["keep"], seed=3)
    assert {r["category"] for r in res["records"]} == {"keep"}


# --- labeling ---------------------------------------------------------------

def test_labels_consistent_within_category(tmp_path):
    root = tmp_path / "src"
    for cat in ("Hijaz", "Kurd"):
        for var in ("v1", "v2", "v3"):
            for stem in ("s1", "s2"):
                make(root, f"{cat}/{var}/{stem}.wav")
    res = ab.setup_ab_evaluation(root, tmp_path / "out", seed=7,
                                 shuffle_per="category")

    # same label -> same variant for every track inside a category
    per_cat: dict[str, dict[str, str]] = {}
    for r in res["records"]:
        per_cat.setdefault(r["category"], {})[r["label"]] = r["variant"]
    for cat, mapping in per_cat.items():
        assert len(mapping) == 3
        for r in res["records"]:
            if r["category"] == cat:
                assert mapping[r["label"]] == r["variant"]


def test_shuffle_per_pair_can_differ_across_tracks(tmp_path):
    root = tmp_path / "src"
    for var in ("v1", "v2"):
        for stem in ("s1", "s2", "s3"):
            make(root, f"{var}/{stem}.wav")
    res = ab.setup_ab_evaluation(root, tmp_path / "out", seed=11,
                                 shuffle_per="pair")
    per_stem = {}
    for r in res["records"]:
        stem = r["blind_file"].rsplit("_", 1)[0]
        per_stem.setdefault(stem, {})[r["label"]] = r["variant"]
    # with 3 pairs and a 2-way shuffle, at least one pair should differ
    assert len({tuple(sorted(m.items())) for m in per_stem.values()}) >= 1


def test_three_variants_get_abc(tmp_path):
    root = tmp_path / "src"
    for var in ("one", "two", "three"):
        make(root, f"{var}/t.wav")
    res = ab.setup_ab_evaluation(root, tmp_path / "out", seed=4)
    assert {r["label"] for r in res["records"]} == {"A", "B", "C"}


def test_seed_is_reproducible(tmp_path):
    root = tmp_path / "src"
    for var in ("v1", "v2", "v3"):
        for stem in ("s1", "s2", "s3", "s4"):
            make(root, f"{var}/{stem}.wav")
    a = ab.setup_ab_evaluation(root, tmp_path / "a", seed=99)
    b = ab.setup_ab_evaluation(root, tmp_path / "b", seed=99)
    assert a["label_maps"] == b["label_maps"]


# --- selection / robustness -------------------------------------------------

def test_explicit_variants_selects_subset(tmp_path):
    root = tmp_path / "src"
    for var in ("keep1", "keep2", "ignore"):
        make(root, f"{var}/t.wav")
    res = ab.setup_ab_evaluation(root, tmp_path / "out",
                                 variants=["keep1", "keep2"], seed=5)
    assert {r["variant"] for r in res["records"]} == {"keep1", "keep2"}


def test_incomplete_pair_is_skipped(tmp_path):
    root = tmp_path / "src"
    make(root, "v1/t1.wav")
    make(root, "v2/t1.wav")
    make(root, "v1/t2.wav")  # no v2/t2 -> incomplete
    res = ab.setup_ab_evaluation(root, tmp_path / "out", seed=6)
    assert {r["blind_file"] for r in res["records"]} == {"t1_A.wav", "t1_B.wav"}


def test_bad_variant_name_errors(tmp_path):
    root = tmp_path / "src"
    make(root, "v1/t.wav")
    make(root, "v2/t.wav")
    with pytest.raises(ValueError):
        ab.setup_ab_evaluation(root, tmp_path / "out", variants=["v1", "nope"])


def test_missing_root_errors(tmp_path):
    with pytest.raises(FileNotFoundError):
        ab.setup_ab_evaluation(tmp_path / "nope", tmp_path / "out")


# --- dry run / json ---------------------------------------------------------

def test_dry_run_writes_nothing(tmp_path):
    root = tmp_path / "src"
    make(root, "v1/t.wav")
    make(root, "v2/t.wav")
    out = tmp_path / "out"
    res = ab.setup_ab_evaluation(root, out, seed=1, dry_run=True)
    assert len(res["records"]) == 2
    assert not out.exists()


def test_json_mapping_written(tmp_path):
    root = tmp_path / "src"
    make(root, "v1/t.wav")
    make(root, "v2/t.wav")
    out = tmp_path / "out"
    j = out / "key.json"
    ab.setup_ab_evaluation(root, out, seed=1, json_path=j)
    data = json.loads(j.read_text())
    assert data["seed"] == 1
    assert len(data["pairs"]) == 2
    assert set(data["variants"]) == {"v1", "v2"}


def test_note_legend_in_keys(tmp_path):
    root = tmp_path / "src"
    make(root, "g1.0/t.wav")
    make(root, "g1.5/t.wav")
    out = tmp_path / "out"
    ab.setup_ab_evaluation(root, out, seed=1,
                           notes={"g1.5": "guidance_scale=1.5"})
    keys = (out / "KEYS.txt").read_text()
    assert "VARIANT LEGEND" in keys
    assert "g1.5 = guidance_scale=1.5" in keys


def test_main_cli_end_to_end(tmp_path, capsys):
    root = tmp_path / "src"
    make(root, "v1/t.wav")
    make(root, "v2/t.wav")
    out = tmp_path / "out"
    rc = ab.main(["--root", str(root), "--output", str(out), "--seed", "1"])
    assert rc == 0
    assert (out / "EVAL.txt").is_file()
    assert (out / "KEYS.txt").is_file()


def test_cli_bad_args_returns_1(tmp_path):
    rc = ab.main(["--root", str(tmp_path / "nope"), "--output", str(tmp_path / "o")])
    assert rc == 1
