"""T2 e2e inference journeys (docs/E2E_TESTING_PLAN.md §5), GPU-free.

J1 -- happy path: multi-song, multi-take, explicit seeds -> one self-contained
run folder. Drives the real `generate.main` with only `gpu_info` and the
`runner` substituted (plan §5.1).
"""
from __future__ import annotations

import hashlib
import json
import wave

import pytest

# Recorded prompt text, mirrored from the staged INFERENCE/prompts files. Kept
# inline so the test is self-contained and the exact bytes are asserted.
STYLE_HIJAZ = "arabmaqamrock hijaz, oud and qanun, driving rock band"
LYRICS_HIJAZ = "يا صَباحَ الوَطَنِ المَشدودِ بِالأَلَمِ\nنادِ الفَجْرَ وَخُذْ بِيَ إلى النَّدَى"
STYLE_KURD = "arabmaqamrock kurd, ney and darbuka, anthemic rock"
LYRICS_KURD = "قَلبي عَلى نارٍ وَدَمعي عَلى الخُدود\nأَنا في الغِيابِ وَأَنتِ في الوُجود"

INPUT = {
    "songs": [
        {"name": "Hijaz", "style": STYLE_HIJAZ, "lyrics": LYRICS_HIJAZ,
         "cap": 6500, "seeds": [20260924, 20260925]},
        {"name": "Kurd", "style": STYLE_KURD, "lyrics": LYRICS_KURD,
         "cap": 7250, "seed": 20260924},
    ],
}


def _recorded(recorded_batch, name, seed):
    for t in recorded_batch["tracks"]:
        if t["name"] == name and t["seed"] == seed:
            return t
    raise AssertionError(f"no recorded fixture for ({name}, {seed})")


def test_j1_happy_path(gen, tmp_path, staged_inference, run_generate,
                       replay_runner, recorded_batch):
    input_path = tmp_path / "j1_batch.json"
    input_path.write_text(json.dumps(INPUT, ensure_ascii=False), encoding="utf-8")
    out_dir = tmp_path / "out" / "j1"

    rc = run_generate(
        [str(input_path), "--out-dir", str(out_dir), "--no-trigger",
         "--lora-ar", str(staged_inference.ar),
         "--lora-nar", str(staged_inference.nar)],
        runner=replay_runner)
    assert rc == 0

    # input copied verbatim; prompts materialized at the exact conditioning bytes
    assert (out_dir / "input.json").read_bytes() == input_path.read_bytes()
    for name, style, lyrics in (("Hijaz", STYLE_HIJAZ, LYRICS_HIJAZ),
                                ("Kurd", STYLE_KURD, LYRICS_KURD)):
        assert (out_dir / "prompts" / f"{name}_style.txt").read_text(
            encoding="utf-8") == style
        assert (out_dir / "prompts" / f"{name}_lyrics.txt").read_text(
            encoding="utf-8") == lyrics

    manifest = json.loads((out_dir / "batch_manifest.json").read_text(encoding="utf-8"))
    assert manifest["gpu"] == {"name": "Tesla T4", "compute_cap": "7.5"}
    assets = manifest["assets"]
    assert assets["checkpoint_step"] == gen.CHECKPOINT_STEP
    assert assets["model_gguf_sha256"] == hashlib.sha256(b"m").hexdigest()
    assert assets["vae_gguf_sha256"] == hashlib.sha256(b"v").hexdigest()
    assert assets["lora_ar_sha256"] == hashlib.sha256(b"a").hexdigest()

    # seeds/caps/takes come from the real planner, matching the fixture contract
    assert [(t["name"], t["take"], t["seed"], t["cap"]) for t in manifest["tracks"]] == [
        ("Hijaz", 0, 20260924, 6500),
        ("Hijaz", 1, 20260925, 6500),
        ("Kurd", 0, 20260924, 7250),
    ]

    # per-track outputs + the sidecar the code under test writes itself
    for t in manifest["tracks"]:
        stem = f'{t["name"]}_{t["seed"]}'
        recorded = _recorded(recorded_batch, t["name"], t["seed"])
        wav = out_dir / f"{stem}.wav"
        assert wav.is_file()
        with wave.open(str(wav), "rb") as w:
            assert w.getnframes() / w.getframerate() == pytest.approx(
                recorded["duration_s"], abs=0.05)
        assert "Exit status: 0" in (out_dir / f"{stem}_time.txt").read_text(encoding="utf-8")
        assert (out_dir / f"{stem}_gpu.csv").read_text(encoding="utf-8").startswith(
            "gpu_util_pct,")

        sc = json.loads((out_dir / f"{stem}.json").read_text(encoding="utf-8"))
        assert sc["status"] == "ok" and sc["exit"] == 0
        assert sc["wav_sha256"] == hashlib.sha256(wav.read_bytes()).hexdigest()
        assert sc["wav_duration_s"] == pytest.approx(recorded["duration_s"], abs=0.05)
        assert sc["model_gguf_sha256"] == assets["model_gguf_sha256"]
        assert sc["lora_ar_sha256"] == assets["lora_ar_sha256"]
        assert sc["lora_nar_sha256"] == assets["lora_nar_sha256"]
        assert sc["audio_cpp_commit"] == assets["audio_cpp_commit"]
        assert sc["checkpoint_step"] == gen.CHECKPOINT_STEP
        assert sc["gpu"] == "Tesla T4"

    # _runs_status.log is written by the runner, one START/END per track
    status = (out_dir / "_runs_status.log").read_text(encoding="utf-8")
    assert status.count("=== START") == 3 and status.count("=== END") == 3

    # summary counts + out/latest pointer (the real main, not a stub)
    summary = (out_dir / "batch_summary.txt").read_text(encoding="utf-8")
    assert "ok: 3" in summary and "failed: 0" in summary
    assert (out_dir / "batch_manifest.json").is_file()
    latest = (staged_inference.root / "out" / "latest").read_text(encoding="utf-8")
    assert latest.strip() == str(out_dir)
