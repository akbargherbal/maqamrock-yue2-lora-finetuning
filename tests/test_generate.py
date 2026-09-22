"""Unit tests for INFERENCE/generate.py (GPU-free)."""
import hashlib
import json
import os
import subprocess
import sys
import wave
from pathlib import Path

import pytest

FP = {
    "lora_ar_sha256": "aa", "lora_nar_sha256": "bb",
    "model_gguf": "yue2-3b-bf16.gguf", "vae_gguf": "yue2-vae-f16.gguf",
    "model_gguf_sha256": None, "vae_gguf_sha256": None,
    "audio_cpp_commit": "abc123", "checkpoint_step": 3000,
}
GPU = {"name": "Tesla T4", "compute_cap": "7.5"}
GPU_FULL = {"name": "Tesla T4", "memory_used": "100", "memory_total": "15360",
            "compute_cap": "7.5"}


# --- resolve / schema -------------------------------------------------------

def test_resolve_inline_defaults_trigger(gen, tmp_path, lyrics_ar):
    data = {
        "defaults": {"style": "symphonic rock", "repeat": 2},
        "songs": [
            {"name": "a_song", "lyrics": lyrics_ar},
            {"name": "b_song", "lyrics": "قلبي", "seed": 5},
            {"name": "c_song", "lyrics": "..."},
        ],
    }
    songs = gen.resolve_songs(data, tmp_path)
    assert [s.name for s in songs] == ["a_song", "b_song", "c_song"]
    assert songs[0].style_text.startswith(gen.TRIGGER)
    assert songs[0].seed_spec == ("random", 2)
    assert songs[1].seed_spec == ("single", 5)
    assert songs[2].seed_spec == ("random", 2)  # defaults.repeat also applies
    assert songs[0].cap > 0 and songs[0].n_letters > 0


def test_resolve_file_refs_and_no_trigger(gen, tmp_path, lyrics_ar):
    (tmp_path / "my_style.txt").write_text("dark rock ballad", encoding="utf-8")
    (tmp_path / "my_lyrics.txt").write_text(lyrics_ar, encoding="utf-8")
    songs = gen.resolve_songs({"songs": [{"name": "f_song", "style_file": "my_style.txt",
                                          "lyrics_file": "my_lyrics.txt"}]}, tmp_path)
    assert songs[0].style_text.startswith(gen.TRIGGER)
    assert songs[0].style_text.endswith("dark rock ballad")
    assert songs[0].lyrics_text == lyrics_ar

    songs = gen.resolve_songs({"songs": [{"name": "n_song", "style": "no trigger here",
                                          "lyrics": "..."}]}, tmp_path, trigger=False)
    assert songs[0].style_text == "no trigger here"


@pytest.mark.parametrize("quantile", [0.90, 0.95, 0.975])
def test_cap_parity_with_duration_cap_cli(gen, tmp_path, lyrics_ar, quantile):
    lyrics = "\n".join([lyrics_ar] * 3)
    f = tmp_path / "cap_lyrics.txt"
    f.write_text(lyrics, encoding="utf-8")
    songs = gen.resolve_songs({"songs": [{"name": "x", "style": "s", "lyrics": lyrics}]},
                              tmp_path, cli_quantile=quantile)
    dur_cap = Path(gen.__file__).parent / "duration_cap.py"
    r = subprocess.run([sys.executable, str(dur_cap), str(f), "--quantile", str(quantile)],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert int(r.stdout.strip()) == songs[0].cap


def test_cap_override_and_conflict(gen, tmp_path, lyrics_ar):
    songs = gen.resolve_songs({"songs": [{"name": "x", "style": "s", "lyrics": lyrics_ar,
                                          "cap": 750}]}, tmp_path)
    assert songs[0].cap == 750
    with pytest.raises(gen.PlanError) as ei:
        gen.resolve_songs({"songs": [{"name": "x", "style": "s", "lyrics": lyrics_ar,
                                      "cap": 750, "quantile": 0.975}]}, tmp_path)
    assert "mutually exclusive" in str(ei.value)


VALID = {"name": "x", "style": "s", "lyrics": "y"}


@pytest.mark.parametrize("data,frag", [
    ({"foo": 1, "songs": [VALID]}, "unknown key(s): foo"),
    ({"songs": [{"name": "x", "style": "s", "lyric": "y"}]}, "unknown key(s): lyric"),
    ([1, 2], "top level must be"),
    ({"songs": []}, "non-empty array"),
    ({"songs": [{"name": "has space", "style": "s", "lyrics": "y"}]}, "ASCII slug"),
    ({"songs": [{"style": "s", "lyrics": "y"}]}, "ASCII slug"),
    ({"songs": [VALID, VALID]}, "duplicate name"),
    ({"songs": [{"name": "x", "style": "s", "style_file": "f", "lyrics": "y"}]},
     "mutually exclusive"),
    ({"songs": [{"name": "x", "lyrics": "y"}]}, "needs 'style'"),
    ({"songs": [{"name": "x", "style": "s"}]}, "needs 'lyrics' or 'lyrics_file'"),
    ({"songs": [{"name": "x", "style_file": "nope.txt", "lyrics": "y"}]}, "file not found"),
    ({"songs": [{"name": "x", "style": "s", "lyrics": "y", "seeds": [1], "repeat": 2}]},
     "mutually exclusive"),
    ({"songs": [{"name": "x", "style": "s", "lyrics": "y", "seed": 1, "repeat": 2}]},
     "ambiguous"),
    ({"songs": [{"name": "x", "style": "s", "lyrics": "y", "seed": 2 ** 32}]},
     "[0, 4294967296)"),
    ({"songs": [{"name": "x", "style": "s", "lyrics": "y", "seeds": [4, 4]}]},
     "duplicate seeds"),
    ({"songs": [{"name": "x", "style": "s", "lyrics": "y", "quantile": 0.5}]},
     "quantile must be one of"),
    ({"songs": [{"name": "x", "style": "s", "lyrics": "y", "repeat": 0}]}, "integer >= 1"),
    ({"songs": [{"name": "x", "style": "s", "lyrics": "y", "seed": True}]}, "integer in [0"),
])
def test_validation_errors(gen, tmp_path, data, frag):
    with pytest.raises(gen.PlanError) as ei:
        gen.resolve_songs(data, tmp_path)
    assert frag in str(ei.value)


# --- planning ---------------------------------------------------------------

def test_build_tracks(gen, tmp_path, lyrics_ar):
    songs = gen.resolve_songs({"defaults": {"style": "s", "repeat": 4},
                               "songs": [{"name": "rand_song", "lyrics": lyrics_ar}]}, tmp_path)
    tracks = gen.build_tracks(songs)
    seeds = [t.seed for t in tracks]
    assert len(seeds) == 4 and len(set(seeds)) == 4
    assert all(0 <= s < 2 ** 32 for s in seeds)
    assert [t.take for t in tracks] == [0, 1, 2, 3]
    assert [t.idx for t in tracks] == [1, 2, 3, 4]
    assert all(t.seed is None for t in gen.build_tracks(songs, draw=False))

    songs2 = gen.resolve_songs({"songs": [
        {"name": "s1", "style": "s", "lyrics": "y", "seeds": [11, 12]},
        {"name": "s2", "style": "s", "lyrics": "y", "seed": 99}]}, tmp_path)
    assert [t.seed for t in gen.build_tracks(songs2)] == [11, 12, 99]
    assert [t.seed for t in gen.build_tracks(songs2, limit=2)] == [11, 12]
    assert [t.seed for t in gen.build_tracks(songs2, seed_lookup={("s1", 0): 777})] == [777, 12, 99]


# --- materialize + execution ------------------------------------------------

def _make_run(gen, tmp_path, lyrics_ar):
    run = tmp_path / "run"
    run.mkdir()
    songs = gen.resolve_songs({"songs": [{"name": "s1", "style": "style text",
                                          "lyrics": lyrics_ar, "seeds": [11, 12]}]}, tmp_path)
    tracks = gen.build_tracks(songs)
    info = gen.materialize(run, songs, b'{"songs": []}', tmp_path / "in.json", tracks, FP, GPU)
    return run, tracks, info


def test_materialize_writes_prompts_manifest_input(gen, tmp_path, lyrics_ar):
    run, tracks, _ = _make_run(gen, tmp_path, lyrics_ar)
    assert (run / "prompts/s1_style.txt").read_text(encoding="utf-8").startswith(gen.TRIGGER)
    assert (run / "input.json").read_bytes() == b'{"songs": []}'
    manifest = json.loads((run / "batch_manifest.json").read_text(encoding="utf-8"))
    assert [t["seed"] for t in manifest["tracks"]] == [11, 12]


def test_run_batch_ok_then_skip_then_force_fail(gen, tmp_path, lyrics_ar):
    run, tracks, info = _make_run(gen, tmp_path, lyrics_ar)

    def fake_ok(cmd, env, log):
        name, seed = cmd[2], cmd[3]
        out = Path(env["OUT_DIR"])
        sc = json.loads((out / f"{name}_{seed}.json").read_text(encoding="utf-8"))
        assert sc["status"] == "started"  # sidecar written before generation
        assert env["STYLE_FILE"].endswith(f"{name}_style.txt")
        assert env["LYRICS_FILE"].endswith(f"{name}_lyrics.txt")
        (out / f"{name}_{seed}.wav").write_bytes(b"RIFF0000WAVEfmt ")
        (out / f"{name}_{seed}_time.txt").write_text("\tExit status: 0\n", encoding="utf-8")
        (out / f"{name}_{seed}.log").write_text("... truncated=1 ...", encoding="utf-8")
        return 0

    results = gen.run_batch(run, tracks, info, FP, GPU, runner=fake_ok)
    assert [r.status for r in results] == ["ok", "ok"]
    assert all(r.truncated and r.truncated_source == "log" for r in results)
    sc = json.loads((run / "s1_11.json").read_text(encoding="utf-8"))
    assert sc["exit"] == 0 and sc["status"] == "ok" and sc["wav_sha256"]
    assert sc["lora_ar_sha256"] == "aa" and sc["attention"] == "flash" and sc["gpu"] == "Tesla T4"

    def boom(*_a):
        raise AssertionError("runner called for an already-succeeded track")

    assert [r.status for r in gen.run_batch(run, tracks, info, FP, GPU, runner=boom)] == \
        ["skipped", "skipped"]

    def fake_fail(cmd, env, log):
        name, seed = cmd[2], cmd[3]
        out = Path(env["OUT_DIR"])
        (out / f"{name}_{seed}.log").write_text("model load failed\n", encoding="utf-8")
        (out / f"{name}_{seed}_time.txt").write_text("\tExit status: 1\n", encoding="utf-8")
        return 1

    results = gen.run_batch(run, tracks, info, FP, GPU, force=True, runner=fake_fail)
    assert [r.status for r in results] == ["failed", "failed"]
    assert (run / "_failed_runs.log").read_text(encoding="utf-8").count("FAILED") == 2
    sc = json.loads((run / "s1_11.json").read_text(encoding="utf-8"))
    assert sc["exit"] == 1 and sc["status"] == "failed"
    summary = gen.render_summary(run, results)
    assert "failed: 2" in summary and "possibly truncated" not in summary


def test_truncation_info(gen, tmp_path):
    log = tmp_path / "x.log"
    log.write_text("truncated=1\n", encoding="utf-8")
    assert gen.truncation_info(log, None, 2500) == (True, "log")
    missing = tmp_path / "none.log"
    assert gen.truncation_info(missing, 100.0, 2500) == (True, "duration_heuristic")
    assert gen.truncation_info(missing, 10.0, 2500) == (False, "duration_heuristic")
    assert gen.truncation_info(missing, None, 2500) == (None, None)


# --- CLI / preflight --------------------------------------------------------

def test_cli_dry_run_example(gen, repo_root, capsys):
    example = repo_root / "INFERENCE" / "songs.example.json"
    assert gen.main([str(example), "--dry-run"]) == 0
    out = capsys.readouterr()
    assert "plan: 2 song(s), 3 track(s)" in out.out
    assert "<random>" in out.out and "750" in out.out


def test_cli_malformed_json(gen, tmp_path, capsys):
    bad = tmp_path / "bad.json"
    bad.write_text('{"songs":[{"name":"x","style":"s"}]}', encoding="utf-8")
    assert gen.main([str(bad), "--dry-run"]) == 1
    assert "needs 'lyrics' or 'lyrics_file'" in capsys.readouterr().err


def test_preflight_missing_assets(gen, tmp_path, monkeypatch):
    monkeypatch.setattr(gen, "RUN_ONE", tmp_path / "run_one.sh")
    monkeypatch.setattr(gen, "BIN", tmp_path / "bin")
    monkeypatch.setattr(gen, "MODEL_DIR", tmp_path / "model")
    monkeypatch.setattr(gen, "LORA_AR", tmp_path / "ar.safetensors")
    monkeypatch.setattr(gen, "LORA_NAR", tmp_path / "nar.safetensors")
    monkeypatch.setattr(gen, "training_active", lambda: None)
    with pytest.raises(gen.PlanError) as ei:
        gen.preflight(False)
    assert "preflight failed" in str(ei.value)


def test_main_refuses_and_writes_nothing_when_preflight_fails(gen, tmp_path, monkeypatch, capsys,
                                                             lyrics_ar):
    songs = tmp_path / "songs.json"
    songs.write_text(json.dumps({"songs": [{"name": "x", "style": "s", "lyrics": lyrics_ar}]},
                                ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(gen, "preflight", lambda allow: gen.fail("preflight failed: test"))
    assert gen.main([str(songs)]) == 1
    assert "preflight failed" in capsys.readouterr().err
    assert [p.name for p in tmp_path.iterdir()] == ["songs.json"]


# --- internals, error paths, GPU-free seams ---------------------------------

def _songs_json(tmp_path, lyrics_ar, **song_extra):
    song = {"name": "x", "style": "s", "lyrics": lyrics_ar}
    song.update(song_extra)
    p = tmp_path / "songs.json"
    p.write_text(json.dumps({"songs": [song]}, ensure_ascii=False), encoding="utf-8")
    return p


class _Run:
    """Minimal stand-in for subprocess.CompletedProcess."""

    def __init__(self, returncode=0, stdout=""):
        self.returncode = returncode
        self.stdout = stdout


def test_sha256_file(gen, tmp_path):
    p = tmp_path / "a.bin"
    p.write_bytes(b"abc")
    assert gen.sha256_file(p) == hashlib.sha256(b"abc").hexdigest()
    assert gen.sha256_file(tmp_path / "nope.bin") is None


def test_load_input_errors(gen, tmp_path):
    bad_json = tmp_path / "bad.json"
    bad_json.write_text("{not json", encoding="utf-8")
    with pytest.raises(gen.PlanError) as ei:
        gen.load_input(bad_json)
    assert "invalid JSON" in str(ei.value)

    non_utf8 = tmp_path / "nonutf8.json"
    non_utf8.write_bytes(b"\xff\xfe\x00")
    with pytest.raises(gen.PlanError) as ei:
        gen.load_input(non_utf8)
    assert "not valid UTF-8" in str(ei.value)

    top_list = tmp_path / "top.json"
    top_list.write_text("[1, 2]", encoding="utf-8")
    with pytest.raises(gen.PlanError) as ei:
        gen.load_input(top_list)
    assert "top level must be" in str(ei.value)

    with pytest.raises(gen.PlanError):
        gen.load_input(tmp_path / "nope.json")


def test_style_file_invalid_utf8(gen, tmp_path, lyrics_ar):
    (tmp_path / "s.txt").write_bytes(b"\xff\xfe")
    with pytest.raises(gen.PlanError) as ei:
        gen.resolve_songs({"songs": [{"name": "x", "style_file": "s.txt",
                                      "lyrics": lyrics_ar}]}, tmp_path)
    assert "not valid UTF-8" in str(ei.value)


def test_load_manifest_seeds(gen, tmp_path):
    run = tmp_path / "run"
    run.mkdir()
    assert gen.load_manifest_seeds(run) == {}
    (run / "batch_manifest.json").write_text(
        '{"tracks": [{"name": "a", "take": 0, "seed": 7}]}', encoding="utf-8")
    assert gen.load_manifest_seeds(run) == {("a", 0): 7}
    (run / "batch_manifest.json").write_text("{bad", encoding="utf-8")
    assert gen.load_manifest_seeds(run) == {}


def test_succeeded(gen, tmp_path):
    wav, time_file = tmp_path / "x.wav", tmp_path / "x_time.txt"
    assert not gen._succeeded(wav, time_file)      # nothing exists
    wav.write_bytes(b"RIFF")
    assert not gen._succeeded(wav, time_file)      # time file missing
    time_file.write_text("Exit status: 0", encoding="utf-8")
    assert gen._succeeded(wav, time_file)
    time_file.write_text("Exit status: 1", encoding="utf-8")
    assert not gen._succeeded(wav, time_file)


def test_wav_duration(gen, tmp_path, monkeypatch):
    wav = tmp_path / "t.wav"
    with wave.open(str(wav), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(8000)
        w.writeframes(b"\x00\x00" * 8000)
    assert abs(gen.wav_duration(wav) - 1.0) < 0.01
    assert gen.wav_duration(tmp_path / "nope.wav") is None

    junk = tmp_path / "junk.wav"
    junk.write_bytes(b"not a wav")
    monkeypatch.setattr(gen.shutil, "which", lambda _n: None)
    assert gen.wav_duration(junk) is None                    # wave fails, no ffprobe
    monkeypatch.setattr(gen.shutil, "which", lambda _n: "/usr/bin/ffprobe")
    monkeypatch.setattr(gen.subprocess, "run", lambda *a, **k: _Run(0, "12.5\n"))
    assert gen.wav_duration(junk) == 12.5                    # ffprobe fallback


def test_subprocess_runner_streams_to_log(gen, tmp_path):
    log = (tmp_path / "d.log").open("w", encoding="utf-8")
    try:
        rc = gen.subprocess_runner(
            ["bash", "-c", "echo out-line; echo err-line >&2"], dict(os.environ), log)
    finally:
        log.close()
    assert rc == 0
    text = (tmp_path / "d.log").read_text(encoding="utf-8")
    assert "out-line" in text and "err-line" in text


def test_gpu_info(gen, monkeypatch):
    monkeypatch.setattr(gen.shutil, "which", lambda _n: None)
    assert gen.gpu_info() is None
    monkeypatch.setattr(gen.shutil, "which", lambda _n: "/usr/bin/nvidia-smi")
    monkeypatch.setattr(gen.subprocess, "run",
                        lambda *a, **k: _Run(0, "Tesla T4, 100, 15360, 7.5\n"))
    assert gen.gpu_info() == {"name": "Tesla T4", "memory_used": "100",
                              "memory_total": "15360", "compute_cap": "7.5"}
    monkeypatch.setattr(gen.subprocess, "run", lambda *a, **k: _Run(1, ""))
    assert gen.gpu_info() is None


def test_git_commit(gen, repo_root, tmp_path):
    assert gen.git_commit(tmp_path) is None          # not a repo
    assert gen.git_commit(repo_root) is not None     # real repo


def test_asset_fingerprint(gen, tmp_path, monkeypatch):
    model = tmp_path / "model"
    model.mkdir()
    (model / gen.MODEL_GGUF).write_bytes(b"m")
    (model / gen.VAE_GGUF).write_bytes(b"v")
    ar, nar = tmp_path / "ar", tmp_path / "nar"
    ar.write_bytes(b"a")
    nar.write_bytes(b"n")
    monkeypatch.setattr(gen, "MODEL_DIR", model)
    monkeypatch.setattr(gen, "LORA_AR", ar)
    monkeypatch.setattr(gen, "LORA_NAR", nar)
    monkeypatch.setattr(gen, "git_commit", lambda _p: "deadbeef")

    fp = gen.asset_fingerprint(hash_big=True)
    assert fp["model_gguf_sha256"] and fp["vae_gguf_sha256"]
    assert fp["lora_ar_sha256"] and fp["audio_cpp_commit"] == "deadbeef"
    assert gen.asset_fingerprint(hash_big=False)["model_gguf_sha256"] is None


def _stub_assets(gen, tmp_path, monkeypatch, bin_exec=True):
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
    monkeypatch.setattr(gen, "LORA_AR", ar)
    monkeypatch.setattr(gen, "LORA_NAR", nar)
    monkeypatch.setattr(gen, "ROOT", tmp_path)
    return binp


def test_preflight_success(gen, tmp_path, monkeypatch):
    _stub_assets(gen, tmp_path, monkeypatch)
    monkeypatch.setattr(gen, "training_active", lambda: None)
    monkeypatch.setattr(gen, "gpu_info", lambda: GPU_FULL)
    assert gen.preflight(False) == GPU_FULL


def test_preflight_not_executable_binary(gen, tmp_path, monkeypatch):
    _stub_assets(gen, tmp_path, monkeypatch, bin_exec=False)
    with pytest.raises(gen.PlanError) as ei:
        gen.preflight(False)
    assert "not executable" in str(ei.value)


def test_preflight_refuses_active_training_and_gpu_check(gen, tmp_path, monkeypatch):
    _stub_assets(gen, tmp_path, monkeypatch)
    monkeypatch.setattr(gen, "training_active", lambda: "python run.py akbar_arabic_rock_lora")
    with pytest.raises(gen.PlanError) as ei:
        gen.preflight(False)
    assert "training" in str(ei.value)

    monkeypatch.setattr(gen, "gpu_info", lambda: GPU_FULL)
    assert gen.preflight(True) == GPU_FULL

    monkeypatch.setattr(gen, "gpu_info", lambda: None)
    with pytest.raises(gen.PlanError):
        gen.preflight(True)


def test_pick_run_dir_collision(gen, tmp_path, monkeypatch):
    fixed = gen.datetime(2026, 9, 22, 12, 0, 0)

    class FakeDatetime:
        @staticmethod
        def now():
            return fixed

    monkeypatch.setattr(gen, "ROOT", tmp_path)
    monkeypatch.setattr(gen, "datetime", FakeDatetime)
    first = gen.pick_run_dir("lbl")
    first.mkdir(parents=True)
    second = gen.pick_run_dir("lbl")
    assert second == first.with_name(first.name + "-2")


def test_trunc_label_and_summary_truncations(gen, tmp_path):
    t = gen.Track(1, "n", 0, 1, 2500, 0.95, 10)
    assert gen._trunc_label(gen.Result(t, "ok")) == "-"
    assert gen._trunc_label(gen.Result(t, "ok", 0, 1.0, 1.0, False, "duration_heuristic")) == "no"
    assert gen._trunc_label(gen.Result(t, "ok", 0, 1.0, 1.0, True, "log")) == "yes"
    assert gen._trunc_label(gen.Result(t, "ok", 0, 1.0, 1.0, True, "duration_heuristic")) == "maybe"
    summary = gen.render_summary(
        tmp_path, [gen.Result(t, "ok", 0, 1.0, 1.0, True, "duration_heuristic")])
    assert "possibly truncated" in summary


def test_wait_vram_free_paths(gen, monkeypatch, real_wait_vram_free):
    monkeypatch.setattr(gen.shutil, "which", lambda _n: None)
    real_wait_vram_free()                                   # no nvidia-smi -> return

    monkeypatch.setattr(gen.shutil, "which", lambda _n: "/usr/bin/nvidia-smi")
    monkeypatch.setattr(gen.subprocess, "run", lambda *a, **k: _Run(1, ""))
    real_wait_vram_free()                                   # query failed -> return

    monkeypatch.setattr(gen.subprocess, "run", lambda *a, **k: _Run(0, "500\n"))
    real_wait_vram_free()                                   # free -> return

    replies = iter([_Run(0, "5000\n"), _Run(0, "0\n")])
    monkeypatch.setattr(gen.subprocess, "run", lambda *a, **k: next(replies))
    monkeypatch.setattr(gen.time, "sleep", lambda _s: None)
    real_wait_vram_free()                                   # busy then free

    monkeypatch.setattr(gen.subprocess, "run", lambda *a, **k: _Run(0, ""))
    real_wait_vram_free()                                   # empty stdout -> return
    monkeypatch.setattr(gen.subprocess, "run", lambda *a, **k: _Run(0, "abc\n"))
    real_wait_vram_free()                                   # unparsable -> return


def test_main_full_path_with_out_dir(gen, tmp_path, monkeypatch, capsys, lyrics_ar):
    monkeypatch.setattr(gen, "ROOT", tmp_path)
    monkeypatch.setattr(gen, "preflight", lambda allow: GPU)
    monkeypatch.setattr(gen, "asset_fingerprint", lambda *a, **k: FP)
    songs = _songs_json(tmp_path, lyrics_ar, seed=1)
    track = gen.Track(1, "x", 0, 1, 3000, 0.95, 10)
    monkeypatch.setattr(gen, "run_batch", lambda *a, **k: [
        gen.Result(track, "ok", 0, 1.0, 10.0, False, "duration_heuristic")])
    run_dir = tmp_path / "run"
    assert gen.main([str(songs), "--out-dir", str(run_dir)]) == 0
    captured = capsys.readouterr()
    assert "ok: 1" in captured.out
    assert (run_dir / "batch_summary.txt").is_file()
    assert (tmp_path / "out" / "latest").read_text(encoding="utf-8").strip() == str(run_dir)


def test_main_keyboard_interrupt(gen, tmp_path, monkeypatch, capsys, lyrics_ar):
    songs = _songs_json(tmp_path, lyrics_ar)

    def boom(_allow):
        raise KeyboardInterrupt

    monkeypatch.setattr(gen, "preflight", boom)
    assert gen.main([str(songs)]) == 130
    assert "interrupted" in capsys.readouterr().err


def test_main_invalid_limit(gen, tmp_path, capsys, lyrics_ar):
    songs = _songs_json(tmp_path, lyrics_ar)
    assert gen.main([str(songs), "--dry-run", "--limit", "0"]) == 1
    assert "--limit must be" in capsys.readouterr().err
