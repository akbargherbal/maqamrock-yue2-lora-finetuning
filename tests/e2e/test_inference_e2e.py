"""T2 e2e inference journeys (docs/E2E_TESTING_PLAN.md §5), GPU-free.

J1 -- happy path: multi-song, multi-take, explicit seeds -> one self-contained
run folder.
J2 -- re-run the same --out-dir: succeeded tracks skip (seeds reused), --force redoes.
J3 -- partial failure -> _failed_runs.log -> retry recovers only the failed track.
J4 -- per-song `loras:` registry routing + per-track provenance on the sidecar.
J6 -- `suno_to_songs.py` -> `generate.py` round trip.

All drive the real `generate.main` with only `gpu_info` and the `runner`
substituted (plan §5.1).
"""
from __future__ import annotations

import hashlib
import json
import wave
from pathlib import Path

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


STYLE_SABA = "arabmaqamrock saba, strings and oud, mournful rock"
LYRICS_SABA = "سَبا وَالدَّمعُ في العَينَينِ يَجرِي\nوَذِكرَاهُ الَّتي تَسكُنُ صَدرِي"


def _argv(input_path, out_dir, staged_inference, *extra, no_trigger=True):
    argv = [str(input_path), "--out-dir", str(out_dir)]
    if no_trigger:
        argv.append("--no-trigger")
    argv += ["--lora-ar", str(staged_inference.ar),
             "--lora-nar", str(staged_inference.nar)]
    return argv + list(extra)


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


def test_j2_rerun_skips_seeds_and_force(gen, tmp_path, staged_inference, run_generate,
                                        replay_mod):
    """Same --out-dir twice: skip + seed reuse; then `--force` redoes (plan §5 J2)."""
    data = {"songs": [
        {"name": "Hijaz", "style": STYLE_HIJAZ, "lyrics": LYRICS_HIJAZ, "repeat": 2},
        {"name": "Kurd", "style": STYLE_KURD, "lyrics": LYRICS_KURD, "seed": 20260924},
    ]}
    input_path = tmp_path / "j2.json"
    input_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    out_dir = tmp_path / "out" / "j2"
    argv = _argv(input_path, out_dir, staged_inference)

    calls: list = []

    def counting(base):
        def runner(cmd, env, log_fh):
            calls.append((cmd[2], cmd[3]))
            return base(cmd, env, log_fh)
        return runner

    passthrough = replay_mod.make_passthrough_runner()
    assert run_generate(argv, runner=counting(passthrough)) == 0
    first_tracks = json.loads((out_dir / "batch_manifest.json").read_text(
        encoding="utf-8"))["tracks"]
    seeds1 = [(t["name"], str(t["seed"])) for t in first_tracks]
    assert len(seeds1) == 3 and len(set(seeds1)) == 3   # 2 random Hijaz takes + 1 Kurd
    assert sorted(calls) == sorted(seeds1)
    assert (out_dir / "_runs_status.log").read_text(encoding="utf-8").count("=== START") == 3

    # second run: everything succeeded -> skipped, runner never invoked, seeds reused
    calls.clear()

    def boom(*_a, **_k):
        raise AssertionError("runner invoked for an already-succeeded track")

    assert run_generate(argv, runner=boom) == 0
    assert calls == []
    assert json.loads((out_dir / "batch_manifest.json").read_text(
        encoding="utf-8"))["tracks"] == first_tracks      # seed reuse via the manifest
    summary = (out_dir / "batch_summary.txt").read_text(encoding="utf-8")
    assert "ok: 0" in summary and "skipped: 3" in summary
    assert (out_dir / "_runs_status.log").read_text(encoding="utf-8").count("=== START") == 3

    # --force redoes every track, with the same manifest-reused random seeds
    assert run_generate([*argv, "--force"],
                        runner=counting(replay_mod.make_passthrough_runner())) == 0
    assert sorted(calls) == sorted(seeds1)
    assert (out_dir / "_runs_status.log").read_text(encoding="utf-8").count("=== START") == 6


def test_j3_partial_failure_then_retry_recovers(gen, tmp_path, staged_inference,
                                                run_generate, replay_mod, recorded_batch):
    """One track exits 1 -> _failed_runs.log; retry reruns only it and recovers (§5 J3)."""
    data = {"songs": [
        {"name": "Hijaz", "style": STYLE_HIJAZ, "lyrics": LYRICS_HIJAZ,
         "seed": 20260924, "cap": 6500},
        {"name": "Saba", "style": STYLE_SABA, "lyrics": LYRICS_SABA,
         "seed": 20260924, "cap": 6500},
    ]}
    input_path = tmp_path / "j3.json"
    input_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    out_dir = tmp_path / "out" / "j3"
    argv = _argv(input_path, out_dir, staged_inference)

    # first pass: Hijaz ok, Saba fails with no audio (the recorded exit=1 fixture)
    assert run_generate(argv, runner=replay_mod.make_replay_runner(recorded_batch)) == 1
    summary = (out_dir / "batch_summary.txt").read_text(encoding="utf-8")
    assert "ok: 1" in summary and "failed: 1" in summary
    failed = (out_dir / "_failed_runs.log").read_text(encoding="utf-8")
    assert "FAILED" in failed and "Saba" in failed
    sc = json.loads((out_dir / "Saba_20260924.json").read_text(encoding="utf-8"))
    assert sc["status"] == "failed" and sc["exit"] == 1
    assert sc["wav_sha256"] is None and sc["wav_duration_s"] is None
    assert not (out_dir / "Saba_20260924.wav").exists()
    assert (out_dir / "_runs_status.log").read_text(encoding="utf-8").count("=== START") == 2

    # retry: the succeeded track is skipped; only the failed one is re-invoked
    attempts: dict = {}

    def recovering(cmd, env, log_fh):
        key = (cmd[2], cmd[3])
        attempts[key] = attempts.get(key, 0) + 1
        assert key == ("Saba", "20260924"), f"runner called for {key}"
        replay_mod.write_track_outputs(out_dir, "Saba", "20260924", duration_s=201.2,
                                       exit_code=0, log_text="[TRACE] truncated=0\n")
        log_fh.write("[replay] recovered Saba\n")
        return 0

    assert run_generate(argv, runner=recovering) == 0
    assert attempts == {("Saba", "20260924"): 1}
    summary = (out_dir / "batch_summary.txt").read_text(encoding="utf-8")
    assert "ok: 1" in summary and "skipped: 1" in summary and "failed: 0" in summary
    sc = json.loads((out_dir / "Saba_20260924.json").read_text(encoding="utf-8"))
    assert sc["status"] == "ok" and sc["exit"] == 0 and sc["wav_sha256"]
    # the failure history is append-only, not cleared by a successful retry
    assert "FAILED" in (out_dir / "_failed_runs.log").read_text(encoding="utf-8")
    assert (out_dir / "_runs_status.log").read_text(encoding="utf-8").count("=== START") == 3


def test_j4_lora_registry_routing_and_provenance(gen, tmp_path, staged_inference,
                                                 run_generate, replay_mod, recorded_batch):
    """`loras:` registry picks the per-song adapter and stamps the sidecar (§5 J4)."""
    adapters = tmp_path / "adapters"
    pairs = {"v2": (b"v2-ar", b"v2-nar"), "qfinal": (b"qf-ar", b"qf-nar")}
    for alias, (ar_b, nar_b) in pairs.items():
        d = adapters / alias
        d.mkdir(parents=True)
        (d / gen.LORA_AR_NAME).write_bytes(ar_b)
        (d / gen.LORA_NAR_NAME).write_bytes(nar_b)

    data = {
        "loras": {"v2": {"dir": "adapters/v2"}, "qfinal": {"dir": "adapters/qfinal"}},
        "defaults": {"lora": "v2"},
        "songs": [
            {"name": "Hijaz", "style": STYLE_HIJAZ, "lyrics": LYRICS_HIJAZ,
             "seed": 20260924},
            {"name": "Kurd", "style": STYLE_KURD, "lyrics": LYRICS_KURD,
             "seed": 20260924, "lora": "qfinal"},
        ],
    }
    input_path = tmp_path / "j4.json"
    input_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    out_dir = tmp_path / "out" / "j4"

    seen: dict = {}

    def capture(base):
        def runner(cmd, env, log_fh):
            seen[(cmd[2], cmd[3])] = (env["LORA_AR"], env["LORA_NAR"])
            return base(cmd, env, log_fh)
        return runner

    assert run_generate(_argv(input_path, out_dir, staged_inference),
                        runner=capture(replay_mod.make_replay_runner(recorded_batch))) == 0
    for name, seed, alias in (("Hijaz", "20260924", "v2"), ("Kurd", "20260924", "qfinal")):
        ar_b, nar_b = pairs[alias]
        d = adapters / alias
        assert seen[(name, seed)] == (str(d / gen.LORA_AR_NAME), str(d / gen.LORA_NAR_NAME))
        sc = json.loads((out_dir / f"{name}_{seed}.json").read_text(encoding="utf-8"))
        assert sc["lora_alias"] == alias
        assert sc["lora_ar_sha256"] == hashlib.sha256(ar_b).hexdigest()
        assert sc["lora_nar_sha256"] == hashlib.sha256(nar_b).hexdigest()


def test_j6_suno_to_generate_round_trip(gen, sun, manifest_path, tmp_path,
                                        staged_inference, run_generate, replay_mod):
    """`suno_to_songs.py` output runs end to end through the real `generate.main` (§5 J6)."""
    songs_json = tmp_path / "j6_songs.json"
    assert sun.main([str(manifest_path), "-o", str(songs_json)]) == 0
    doc = json.loads(songs_json.read_text(encoding="utf-8"))
    assert len(doc["songs"]) == 8
    by_name = {s["name"]: s for s in doc["songs"]}

    out_dir = tmp_path / "out" / "j6"
    assert run_generate(_argv(songs_json, out_dir, staged_inference, no_trigger=False),
                        runner=replay_mod.make_passthrough_runner()) == 0

    manifest = json.loads((out_dir / "batch_manifest.json").read_text(encoding="utf-8"))
    assert len(manifest["tracks"]) == 8
    assert {t["name"] for t in manifest["tracks"]} == set(by_name)
    for t in manifest["tracks"]:
        # suno emits no trigger; the real generate.py prepends it, byte-for-byte
        assert (out_dir / t["style_file"]).read_text(encoding="utf-8") == \
            gen.TRIGGER + by_name[t["name"]]["style"]
        assert (out_dir / t["lyrics_file"]).read_text(encoding="utf-8") == \
            by_name[t["name"]]["lyrics"]
    assert "ok: 8" in (out_dir / "batch_summary.txt").read_text(encoding="utf-8")
    assert (staged_inference.root / "out" / "latest").read_text(
        encoding="utf-8").strip() == str(out_dir)


def test_provenance_guard(gen, fixtures_dir):
    """Fixture rot check (plan §4.4): manifest integrity + `checkpoint_step`.

    The `audio_cpp_commit` equality is only meaningful where a Tier B binary was
    recorded from the same checkout (the T5 gate); on the CPU tier the audio.cpp
    tree is an arbitrary current clone, so that half is skipped until Tier B lands.
    """
    manifest = json.loads((fixtures_dir / "manifest.json").read_text(encoding="utf-8"))
    for name, meta in manifest["tier_a"].items():
        path = fixtures_dir / name
        assert path.is_file(), f"tier_a fixture missing: {name}"
        assert meta["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    recorded_path = fixtures_dir / "recorded_batch.json"
    spec = json.loads(recorded_path.read_text(encoding="utf-8"))

    prov = manifest["provenance"]
    for key in ("gpu", "compute_cap", "audio_cpp_commit", "checkpoint_step"):
        assert prov[key] == spec["provenance"][key]     # the two fixture files agree
    assert prov["checkpoint_step"] == gen.CHECKPOINT_STEP

    if not manifest.get("tier_b"):
        pytest.skip("Tier B binary not recorded yet; audio_cpp_commit re-checked at the T5 gate")
    code_commit = gen.git_commit(gen.AUDIO_CPP)
    assert prov["audio_cpp_commit"] == code_commit
