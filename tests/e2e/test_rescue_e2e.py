"""e2e: `rescue_abc_batch.sh` against a stub binary and a staged pass-1/ABC tree.

The device boundary is two seams: the preflight GPU probe (bypassed with
`--skip-preflight`) and the binary (`$BIN`). Everything else — arg parsing,
selector resolution, the sha256 index, render loop, resume, and the sidecar — is
the production shell code path. No GPU, no `/content`.

Covers: plan (all / by stem / by name / unknown), missing ABC, out-dir refusals,
`--verify` clean + tamper, render + sidecar + status log, resume + `--force`,
`--smoke`, `--limit`, `--songs-file` (CRLF/comments), a simulated render failure,
and Arabic stems.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO = Path(__file__).resolve().parents[2]
DRIVER = REPO / "INFERENCE" / "rescue_abc_batch.sh"
STUB = Path(__file__).resolve().parent / "fake_audiocpp.py"

ARABIC = "الحر"
SONG_A = f"07-{ARABIC}-rock"     # 2 takes
SONG_B = "06-night_rock"          # 1 take
SEEDS_A = [11, 22]
SEED_B = 33
STEMS_A = [f"{SONG_A}_{s}" for s in SEEDS_A]
STEM_B = f"{SONG_B}_{SEED_B}"


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


@pytest.fixture
def ws(tmp_path) -> SimpleNamespace:
    pass1 = tmp_path / "pass1"
    (pass1 / "prompts").mkdir(parents=True)
    tracks = []
    for name, seeds in ((SONG_A, SEEDS_A), (SONG_B, [SEED_B])):
        (pass1 / "prompts" / f"{name}_style.txt").write_text("arabmaqamrock style", encoding="utf-8")
        (pass1 / "prompts" / f"{name}_lyrics.txt").write_text("[Verse 1]\nكلمات", encoding="utf-8")
        for take, seed in enumerate(seeds):
            stem = f"{name}_{seed}"
            (pass1 / f"{stem}.wav").write_bytes(b"RIFFpass1")
            (pass1 / f"{stem}_time.txt").write_text("...\nExit status: 0\n", encoding="utf-8")
            tracks.append({"idx": len(tracks), "name": name, "take": take, "seed": seed, "cap": 7000,
                           "style_file": f"prompts/{name}_style.txt",
                           "lyrics_file": f"prompts/{name}_lyrics.txt"})
    (pass1 / "batch_manifest.json").write_text(
        json.dumps({"songs": 2, "tracks": tracks}, ensure_ascii=False), encoding="utf-8")

    abc = tmp_path / "abc"
    for t in tracks:
        d = abc / f"{t['name']}_{t['seed']}"
        d.mkdir(parents=True)
        (d / "score.abc").write_text("X:1\nK:C\nCDEF|", encoding="utf-8")

    out = tmp_path / "rescue"
    out.mkdir()
    bindir = tmp_path / "bin"
    bindir.mkdir()
    exe = bindir / "audiocpp_cli"
    shutil.copy2(STUB, exe)
    exe.chmod(0o755)
    return SimpleNamespace(root=tmp_path, pass1=pass1, abc=abc, out=out, bin=exe, tracks=tracks)


def run(ws: SimpleNamespace, *args: str, fail: str | None = None,
        out_dir: Path | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env.update({"BIN": str(ws.bin), "MODEL": str(ws.root / "model"), "THREADS": "1",
                "QF_AR": str(ws.root / "ar"), "QF_NAR": str(ws.root / "nar")})
    if fail:
        env["FAKE_AUDIOCPP_FAIL"] = fail
    cmd = ["bash", str(DRIVER),
           "--pass1-dir", str(ws.pass1), "--abc-dir", str(ws.abc),
           "--out-dir", str(out_dir or ws.out), "--skip-preflight", *args]
    return subprocess.run(cmd, capture_output=True, text=True, env=env)


def _index(ws) -> dict:
    return json.loads((ws.out / "_rescue_index.json").read_text(encoding="utf-8"))


def _wavs(ws) -> list[str]:
    return sorted(p.name for p in ws.out.glob("*.wav"))


# --- plan / selection --------------------------------------------------------

def test_plan_all(ws):
    r = run(ws, "--plan")
    assert r.returncode == 0, r.stderr
    assert _index(ws)["n"] == 3
    assert "n     : 3" in r.stdout


def test_plan_by_stem_selects_one(ws):
    r = run(ws, "--plan", "--songs", STEMS_A[1])
    assert r.returncode == 0, r.stderr
    assert _index(ws)["n"] == 1
    assert _index(ws)["tracks"][0]["stem"] == STEMS_A[1]


def test_plan_by_name_selects_every_take(ws):
    r = run(ws, "--plan", "--songs", SONG_A)
    assert r.returncode == 0, r.stderr
    assert _index(ws)["n"] == 2


def test_plan_unknown_selector_aborts(ws):
    r = run(ws, "--plan", "--songs", "does-not-exist")
    assert r.returncode == 3
    assert "requested selector not in manifest" in r.stderr


def test_plan_missing_abc_aborts(ws):
    (ws.abc / STEM_B / "score.abc").unlink()
    r = run(ws, "--plan")
    assert r.returncode == 3
    assert "missing/empty abc" in r.stderr


def test_plan_missing_style_aborts(ws):
    (ws.pass1 / "prompts" / f"{SONG_B}_style.txt").unlink()
    r = run(ws, "--plan", "--songs", STEM_B)
    assert r.returncode == 3
    assert "missing style" in r.stderr


def test_plan_missing_cap_aborts(ws):
    man = json.loads((ws.pass1 / "batch_manifest.json").read_text(encoding="utf-8"))
    for t in man["tracks"]:
        if t["name"] == SONG_B:
            del t["cap"]
    (ws.pass1 / "batch_manifest.json").write_text(json.dumps(man, ensure_ascii=False), encoding="utf-8")
    r = run(ws, "--plan", "--songs", STEM_B)
    assert r.returncode == 3
    assert "manifest has no cap" in r.stderr


# --- out-dir refusals --------------------------------------------------------

def test_refuse_out_equals_pass1(ws):
    r = run(ws, "--plan", out_dir=ws.pass1)
    assert r.returncode == 2
    assert "== --pass1-dir" in r.stderr


def test_refuse_out_under_pass1(ws):
    r = run(ws, "--plan", out_dir=ws.pass1 / "sub")
    assert r.returncode == 2
    assert "is under --pass1-dir" in r.stderr


def test_refuse_out_is_generate_dir(ws):
    (ws.out / "batch_manifest.json").write_text("{}", encoding="utf-8")
    r = run(ws, "--plan")
    assert r.returncode == 2
    assert "looks like a generate.py run dir" in r.stderr


def test_refuse_out_equals_abc(ws):
    r = run(ws, "--plan", out_dir=ws.abc)
    assert r.returncode == 2
    assert "== --abc-dir" in r.stderr


# --- verify ------------------------------------------------------------------

def test_verify_clean_then_tamper(ws):
    assert run(ws, "--plan").returncode == 0
    ok = run(ws, "--verify")
    assert ok.returncode == 0, ok.stdout
    assert "verify: OK" in ok.stdout
    (ws.abc / STEM_B / "score.abc").write_text("X:1\nK:C\nGABc|", encoding="utf-8")
    bad = run(ws, "--verify")
    assert bad.returncode == 1
    assert "MISMATCH" in bad.stdout


# --- render / sidecar / resume ----------------------------------------------

def test_render_sidecar_status_and_resume(ws):
    r = run(ws)
    assert r.returncode == 0, r.stderr
    assert _wavs(ws) == sorted(f"{s}.wav" for s in STEMS_A + [STEM_B])
    assert "ok=3 fail=0" in r.stdout

    side = json.loads((ws.out / f"{STEM_B}_rescue.json").read_text(encoding="utf-8"))
    assert side["cot"] == "melody" and side["adapter"] == "qfinal_a0.3"
    assert side["name"] == SONG_B and side["seed"] == SEED_B
    assert side["abc_sha256"] == _sha(ws.abc / STEM_B / "score.abc")

    args = json.loads((ws.out / f"{STEM_B}.wav.args.json").read_text(encoding="utf-8"))
    assert args["opts"]["cot"] == "melody"
    assert args["opts"]["abc_file"] == str(ws.abc / STEM_B / "score.abc")

    status = (ws.out / "_rescue_status.log").read_text(encoding="utf-8")
    assert f"START rescue {STEM_B}" in status and f"END rescue {STEM_B}" in status

    again = run(ws)
    assert again.returncode == 0 and "skip" in again.stdout

    forced = run(ws, "--force")
    assert forced.returncode == 0 and "skip" not in forced.stdout


def test_smoke_renders_one(ws):
    r = run(ws, "--smoke")
    assert r.returncode == 0 and "[smoke]" in r.stdout
    assert len(_wavs(ws)) == 1


def test_limit(ws):
    r = run(ws, "--limit", "2")
    assert r.returncode == 0
    assert len(_wavs(ws)) == 2


def test_songs_file_crlf_comments_and_blank(ws):
    f = ws.root / "fails.txt"
    f.write_bytes(f"# a comment\r\n\r\n{STEMS_A[0]}\r\n".encode())
    r = run(ws, "--plan", "--songs-file", str(f))
    assert r.returncode == 0, r.stderr
    assert _index(ws)["n"] == 1


def test_empty_songs_file_errors_not_select_all(ws):
    f = ws.root / "empty.txt"
    f.write_bytes(b"# only a comment\r\n\r\n")
    r = run(ws, "--plan", "--songs-file", str(f))
    assert r.returncode == 2
    assert "no selectors" in r.stderr


# --- --songs-json ------------------------------------------------------------

def test_songs_json_strings_and_objects(ws):
    f = ws.root / "pick.json"
    f.write_text(json.dumps({
        "_comment": "ignored",
        "songs": [STEMS_A[1], {"stem": STEMS_A[0], "note": "why not"}],
    }, ensure_ascii=False), encoding="utf-8")
    r = run(ws, "--plan", "--songs-json", str(f))
    assert r.returncode == 0, r.stderr
    assert _index(ws)["n"] == 2


def test_songs_json_name_selects_every_take(ws):
    f = ws.root / "pick.json"
    f.write_text(json.dumps({"songs": [SONG_A]}), encoding="utf-8")
    r = run(ws, "--plan", "--songs-json", str(f))
    assert r.returncode == 0, r.stderr
    assert _index(ws)["n"] == 2


def test_songs_json_render_one(ws):
    f = ws.root / "pick.json"
    f.write_text(json.dumps({"songs": [STEMS_A[1]]}), encoding="utf-8")
    r = run(ws, "--songs-json", str(f))
    assert r.returncode == 0, r.stderr
    assert _wavs(ws) == [f"{STEMS_A[1]}.wav"]


def test_songs_json_empty_list_errors_not_select_all(ws):
    f = ws.root / "pick.json"
    f.write_text(json.dumps({"songs": []}), encoding="utf-8")
    r = run(ws, "--plan", "--songs-json", str(f))
    assert r.returncode == 2
    assert "no selectors" in r.stderr


def test_songs_json_invalid_json_errors(ws):
    f = ws.root / "pick.json"
    f.write_text("{not json", encoding="utf-8")
    r = run(ws, "--plan", "--songs-json", str(f))
    assert r.returncode == 2
    assert "not readable/valid JSON" in r.stderr


def test_songs_json_songs_must_be_list(ws):
    f = ws.root / "pick.json"
    f.write_text(json.dumps({"songs": "not-a-list"}), encoding="utf-8")
    r = run(ws, "--plan", "--songs-json", str(f))
    assert r.returncode == 2
    assert "must be a list" in r.stderr


def test_songs_json_entry_needs_stem_or_name(ws):
    f = ws.root / "pick.json"
    f.write_text(json.dumps({"songs": [{"note": "no selector"}]}), encoding="utf-8")
    r = run(ws, "--plan", "--songs-json", str(f))
    assert r.returncode == 2
    assert "needs 'stem' or 'name'" in r.stderr


def test_songs_json_mutually_exclusive_with_songs_file(ws):
    js = ws.root / "pick.json"
    js.write_text(json.dumps({"songs": [STEMS_A[0]]}), encoding="utf-8")
    txt = ws.root / "pick.txt"
    txt.write_text(STEMS_A[1], encoding="utf-8")
    r = run(ws, "--plan", "--songs-json", str(js), "--songs-file", str(txt))
    assert r.returncode == 2
    assert "only one of" in r.stderr


def run_cfg(ws: SimpleNamespace, cfg: Path, *args: str) -> subprocess.CompletedProcess:
    """Like run() but with no --dir flags: the config file must supply them."""
    env = dict(os.environ)
    env.update({"BIN": str(ws.bin), "MODEL": str(ws.root / "model"), "THREADS": "1",
                "QF_AR": str(ws.root / "ar"), "QF_NAR": str(ws.root / "nar")})
    cmd = ["bash", str(DRIVER), "--skip-preflight", "--songs-json", str(cfg), *args]
    return subprocess.run(cmd, capture_output=True, text=True, env=env)


def _cfg(ws, **over) -> Path:
    doc = {"pass1_dir": str(ws.pass1), "abc_dir": str(ws.abc), "out_dir": str(ws.out)}
    doc.update(over)
    p = ws.root / "cfg.json"
    p.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    return p


def test_songs_json_supplies_run_dirs(ws):
    r = run_cfg(ws, _cfg(ws, songs=[STEMS_A[1]]), "--plan")
    assert r.returncode == 0, r.stderr
    assert _index(ws)["n"] == 1


def test_songs_json_cli_dir_overrides(ws):
    other = ws.root / "cli-out"
    r = run_cfg(ws, _cfg(ws, songs=[STEMS_A[1]]), "--out-dir", str(other), "--plan")
    assert r.returncode == 0, r.stderr
    assert (other / "_rescue_index.json").is_file()
    assert not (ws.out / "_rescue_index.json").exists()


def test_songs_json_config_only_no_songs_rescues_all(ws):
    r = run_cfg(ws, _cfg(ws), "--plan")
    assert r.returncode == 0, r.stderr
    assert _index(ws)["n"] == 3


def test_songs_json_cot_and_adapter_override(ws):
    r = run_cfg(ws, _cfg(ws, defaults={"cot": "full", "adapter": "custom_adapter"},
                        songs=[STEM_B]))
    assert r.returncode == 0, r.stderr
    side = json.loads((ws.out / f"{STEM_B}_rescue.json").read_text(encoding="utf-8"))
    assert side["cot"] == "full" and side["adapter"] == "custom_adapter"


def test_songs_json_loras_registry_and_per_song_override(ws):
    cfg = _cfg(ws,
               loras={"q3": {"dir": "/opt/q3"}, "q5": {"dir": "/opt/q5"}},
               defaults={"lora": "q3"},
               songs=[STEMS_A[0], {"stem": STEMS_A[1], "lora": "q5"}])
    r = run_cfg(ws, cfg, "--plan")
    assert r.returncode == 0, r.stderr
    tracks = {t["stem"]: t for t in _index(ws)["tracks"]}
    assert tracks[STEMS_A[0]]["adapter"] == "q3"
    assert tracks[STEMS_A[0]]["ar"] == "/opt/q3/akbar_arabic_rock_lora_ar.safetensors"
    assert tracks[STEMS_A[1]]["adapter"] == "q5"
    assert tracks[STEMS_A[1]]["nar"] == "/opt/q5/akbar_arabic_rock_lora_nar.safetensors"


def test_songs_json_per_song_cot_override(ws):
    cfg = _cfg(ws, defaults={"cot": "melody"},
               songs=[STEMS_A[0], {"stem": STEMS_A[1], "cot": "full"}])
    r = run_cfg(ws, cfg, "--plan")
    assert r.returncode == 0, r.stderr
    tracks = {t["stem"]: t for t in _index(ws)["tracks"]}
    assert tracks[STEMS_A[0]]["cot"] == "melody"
    assert tracks[STEMS_A[1]]["cot"] == "full"


def test_songs_json_unknown_lora_alias_errors(ws):
    r = run_cfg(ws, _cfg(ws, defaults={"lora": "ghost"}, songs=[STEMS_A[0]]), "--plan")
    assert r.returncode == 2
    assert "not in 'loras'" in r.stderr


def test_songs_json_legacy_qf_keys_warn(ws):
    # qf_ar/qf_nar were replaced by 'loras' + per-song/defaults 'lora'
    r = run_cfg(ws, _cfg(ws, qf_ar="/x", qf_nar="/y", songs=[STEMS_A[0]]), "--plan")
    assert r.returncode == 0, r.stderr
    assert "unknown --songs-json key: qf_ar" in r.stderr


def test_songs_json_missing_dirs_usage_error(ws):
    cfg = ws.root / "cfg.json"
    cfg.write_text(json.dumps({"songs": [STEMS_A[0]]}), encoding="utf-8")
    r = run_cfg(ws, cfg, "--plan")
    assert r.returncode == 2
    assert "missing --pass1-dir" in r.stderr


def test_songs_json_unknown_key_warns(ws):
    r = run_cfg(ws, _cfg(ws, bogus=1, songs=[STEMS_A[0]]), "--plan")
    assert r.returncode == 0, r.stderr
    assert "unknown --songs-json key: bogus" in r.stderr


def test_songs_json_bad_threads_type_errors(ws):
    r = run_cfg(ws, _cfg(ws, defaults={"threads": "eight"}, songs=[STEMS_A[0]]), "--plan")
    assert r.returncode == 2
    assert "defaults.threads must be a non-negative integer" in r.stderr


def test_render_failure_exits_nonzero(ws):
    r = run(ws, fail=STEM_B)
    assert r.returncode == 1
    assert "fail=1" in r.stdout
    assert f"{STEM_B}.wav" not in _wavs(ws)
    assert len(_wavs(ws)) == 2


def test_arabic_stem_roundtrip(ws):
    r = run(ws, "--songs", STEMS_A[0])
    assert r.returncode == 0, r.stderr
    assert (ws.out / f"{STEMS_A[0]}.wav").exists()
    assert (ws.out / f"{STEMS_A[0]}_rescue.json").exists()
    # only the selected stem rendered
    assert _wavs(ws) == [f"{STEMS_A[0]}.wav"]


# --- seed override: fresh seed per take, ABC stays keyed to the source stem -----

def test_songs_json_seed_random_rerolls_but_keeps_abc_source(ws):
    r = run_cfg(ws, _cfg(ws, defaults={"seed": "random"}), "--plan")
    assert r.returncode == 0, r.stderr
    idx = _index(ws)
    assert idx["n"] == 3
    for t in idx["tracks"]:
        assert t["stem"] == f"{t['name']}_{t['seed']}"
        assert t["abc_source_stem"] == t["src_stem"]
        assert t["stem"] != t["src_stem"]              # fresh seed (collision ~2**-32)
    a = [t for t in idx["tracks"] if t["name"] == SONG_A]
    assert a[0]["stem"] != a[1]["stem"]                # independent draw per take
    assert {t["src_stem"] for t in idx["tracks"]} == set(STEMS_A + [STEM_B])


def test_songs_json_seed_pinned_int(ws):
    r = run_cfg(ws, _cfg(ws, defaults={"seed": 424242}, songs=[STEMS_A[0]]), "--plan")
    assert r.returncode == 0, r.stderr
    t = _index(ws)["tracks"][0]
    assert t["seed"] == 424242
    assert t["stem"] == f"{SONG_A}_424242"
    assert t["src_stem"] == STEMS_A[0]


def test_songs_json_per_song_seed_beats_defaults(ws):
    cfg = _cfg(ws, defaults={"seed": 1}, songs=[{"stem": STEMS_A[1], "seed": 999}])
    r = run_cfg(ws, cfg, "--plan")
    assert r.returncode == 0, r.stderr
    t = _index(ws)["tracks"][0]
    assert t["seed"] == 999 and t["stem"] == f"{SONG_A}_999"
    assert t["src_stem"] == STEMS_A[1]


def test_songs_json_bad_seed_errors(ws):
    r = run_cfg(ws, _cfg(ws, defaults={"seed": "soon"}, songs=[STEMS_A[0]]), "--plan")
    assert r.returncode == 2
    assert "seed must be an integer" in r.stderr


def test_songs_json_no_seed_override_is_back_compatible(ws):
    r = run_cfg(ws, _cfg(ws, songs=[STEM_B]), "--plan")
    assert r.returncode == 0, r.stderr
    t = _index(ws)["tracks"][0]
    assert t["stem"] == STEM_B and t["src_stem"] == STEM_B


def test_songs_json_random_seed_render_uses_original_abc(ws):
    r = run_cfg(ws, _cfg(ws, defaults={"seed": "random"}, songs=[STEM_B]))
    assert r.returncode == 0, r.stderr
    t = _index(ws)["tracks"][0]
    out_stem = t["stem"]
    assert t["src_stem"] == STEM_B
    assert (ws.out / f"{out_stem}.wav").is_file()
    side = json.loads((ws.out / f"{out_stem}_rescue.json").read_text(encoding="utf-8"))
    assert side["abc_source_stem"] == STEM_B
    assert side["seed"] == t["seed"]
    args = json.loads((ws.out / f"{out_stem}.wav.args.json").read_text(encoding="utf-8"))
    assert args["opts"]["abc_file"] == str(ws.abc / STEM_B / "score.abc")
    assert str(t["seed"]) in args["argv"]


def test_songs_json_random_seed_is_stable_across_replan(ws):
    cfg = _cfg(ws, defaults={"seed": "random"}, songs=[STEM_B])
    assert run_cfg(ws, cfg, "--plan").returncode == 0
    first = _index(ws)["tracks"][0]["stem"]
    assert run_cfg(ws, cfg, "--plan").returncode == 0
    # the drawn seed is reused from the index, not re-rolled (resume-stable)
    assert _index(ws)["tracks"][0]["stem"] == first
    assert _index(ws)["tracks"][0]["seed_mode"] == "random"
