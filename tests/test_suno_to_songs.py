"""Unit tests for INFERENCE/suno_to_songs.py (GPU-free)."""
import json

import pytest

ALLOWED_TAGS = {"[Intro]", "[Verse 1]", "[Verse 2]", "[Chorus]", "[Outro]"}


def _convert(sun, manifest_path, out, *extra):
    assert sun.main([str(manifest_path), "-o", str(out), *extra]) == 0
    doc = json.loads(out.read_text(encoding="utf-8"))
    report = json.loads(out.with_name(out.stem + ".report.json").read_text(encoding="utf-8"))
    return doc, report


# --- lyric cleaner ----------------------------------------------------------

def test_clean_lyrics_units(sun):
    raw = ("///***///\n"
           "[Intro | single clean guitar | close-mic'd, plate reverb]\n"
           "سَطْرٌ أَوَّلٌ...\n\n"
           "[Refrain | huge lift]\n"
           "سَطْرٌ ثَانٍ...\n\n"
           "[Instrumental Interlude | strings swell]\n\n"
           "[guitars surge — Ajam]\n\n"
           "[Chorus | soaring — Nahawand]\n"
           "سَطْرٌ ثَالِثٌ...")
    cleaned, dropped = sun.clean_lyrics(raw)
    assert "///***///" not in cleaned
    assert {"[Intro]", "[Refrain]", "[Chorus]"} <= set(cleaned.splitlines())
    assert "[Instrumental Interlude | strings swell]" in dropped
    assert "[guitars surge — Ajam]" in dropped
    assert "سَطْرٌ أَوَّلٌ..." in cleaned and "سَطْرٌ ثَالِثٌ..." in cleaned
    assert "\n\n\n" not in cleaned
    assert sun.canonical_tag("guitars surge — Ajam") is None
    assert sun.canonical_tag("verse 2 | x") == "[Verse 2]"
    assert sun.canonical_tag("REFRAIN") == "[Refrain]"


# --- real manifest conversion -----------------------------------------------

def test_real_manifest_dedup(sun, manifest_path, tmp_path):
    doc, report = _convert(sun, manifest_path, tmp_path / "songs.json")
    assert len(doc["songs"]) == 8
    assert "defaults" not in doc
    for song in doc["songs"]:
        assert set(song) == {"name", "style", "lyrics"}
        assert not song["style"].startswith("arabmaqamrock")
        assert "Maqam " in song["style"] and "Mood:" in song["style"]
        assert "|" not in song["lyrics"] and "///***///" not in song["lyrics"]
        tags = {ln.strip() for ln in song["lyrics"].splitlines() if ln.strip().startswith("[")}
        assert tags <= ALLOWED_TAGS, tags
    assert report["entries_total"] == 16
    assert report["songs_kept"] == 8
    assert report["duplicates_dropped"] == 8
    assert report["per_maqam"] == {"Nahawand": 4, "Kurd": 2, "Hijaz": 2}
    assert report["dropped_tags"] == {}
    assert len(report["provenance"]) == 8
    assert all(v["original_title"] for v in report["provenance"].values())


def test_round_trip_through_generate(gen, sun, manifest_path, tmp_path, capsys):
    out = tmp_path / "songs.json"
    assert sun.main([str(manifest_path), "-o", str(out)]) == 0
    capsys.readouterr()
    assert gen.main([str(out), "--dry-run"]) == 0
    captured = capsys.readouterr()
    assert "plan: 8 song(s), 8 track(s)" in captured.out
    # every style lacks the trigger, so generate.py prepends it — expected
    assert captured.err.count("trigger 'arabmaqamrock' prepended") == 8


# --- dedup modes ------------------------------------------------------------

@pytest.mark.parametrize("mode,suffix", [("a", "_SONG_A.mp3"), ("b", "_SONG_B.mp3")])
def test_keep_modes(sun, manifest_path, tmp_path, mode, suffix):
    _, report = _convert(sun, manifest_path, tmp_path / f"{mode}.json", "--keep", mode)
    assert all(v["assigned_filename"].endswith(suffix) for v in report["provenance"].values())


def test_keep_first(sun, manifest_path, tmp_path):
    # in this manifest SONG_B appears first
    _, report = _convert(sun, manifest_path, tmp_path / "first.json", "--keep", "first")
    assert all(v["assigned_filename"].endswith("_SONG_B.mp3")
               for v in report["provenance"].values())


def test_keep_both_and_filters(sun, manifest_path, tmp_path):
    doc, _ = _convert(sun, manifest_path, tmp_path / "both.json", "--keep-both")
    assert len(doc["songs"]) == 16

    doc, _ = _convert(sun, manifest_path, tmp_path / "nahawand.json", "--maqam", "nahawand")
    assert len(doc["songs"]) == 4
    assert all("Maqam Nahawand" in s["style"] for s in doc["songs"])

    doc, _ = _convert(sun, manifest_path, tmp_path / "dl.json", "--status", "downloaded")
    assert len(doc["songs"]) == 4

    doc, _ = _convert(sun, manifest_path, tmp_path / "skip.json", "--status", "skipped_existing")
    assert len(doc["songs"]) == 4


# --- defaults / file mode / determinism -------------------------------------

def test_defaults_and_file_mode(gen, sun, manifest_path, tmp_path, capsys):
    rep = tmp_path / "rep.json"
    doc, _ = _convert(sun, manifest_path, rep, "--repeat", "2", "--quantile", "0.975")
    assert doc["defaults"] == {"repeat": 2, "quantile": 0.975}
    capsys.readouterr()
    assert gen.main([str(rep), "--dry-run"]) == 0
    assert "plan: 8 song(s), 16 track(s)" in capsys.readouterr().out

    style_dir, lyrics_dir = tmp_path / "styles", tmp_path / "lyrics"
    out = tmp_path / "files.json"
    doc, _ = _convert(sun, manifest_path, out, "--style-dir", str(style_dir),
                      "--lyrics-dir", str(lyrics_dir))
    song = doc["songs"][0]
    assert set(song) == {"name", "style_file", "lyrics_file"}
    assert (out.parent / song["style_file"]).is_file()
    assert (out.parent / song["lyrics_file"]).is_file()
    capsys.readouterr()
    assert gen.main([str(out), "--dry-run"]) == 0
    assert "plan: 8 song(s), 8 track(s)" in capsys.readouterr().out


def test_dry_run_writes_nothing_and_determinism(sun, manifest_path, tmp_path):
    dry = tmp_path / "dry"
    dry.mkdir()
    assert sun.main([str(manifest_path), "-o", str(dry / "x.json"), "--dry-run"]) == 0
    assert list(dry.iterdir()) == []

    a, b = tmp_path / "a.json", tmp_path / "b.json"
    _convert(sun, manifest_path, a)
    _convert(sun, manifest_path, b)
    assert a.read_bytes() == b.read_bytes()


# --- bad manifests ----------------------------------------------------------

def _write(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
    return path


@pytest.mark.parametrize("obj,frag", [
    ({"tracks": [{"original_title": "t", "styles": "",
                  "lyrics": "///***///\nسطر", "clip_id": "c"}]}, "no usable style text"),
    ({"tracks": [{"original_title": "t", "styles": 'genre: "x"\nvocals: "Maqam Hijaz"',
                  "lyrics": "///***///", "clip_id": "c"}]}, "no usable lyrics"),
    ({"tracks": []}, "no usable tracks"),
])
def test_bad_manifests(sun, tmp_path, capsys, obj, frag):
    p = _write(tmp_path / "m.json", obj)
    assert sun.main([str(p), "--dry-run"]) == 1
    assert frag in capsys.readouterr().err


def test_invalid_json_and_missing_manifest(sun, tmp_path, capsys):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    assert sun.main([str(bad), "--dry-run"]) == 1
    assert "invalid JSON" in capsys.readouterr().err

    assert sun.main([str(tmp_path / "nope.json"), "--dry-run"]) == 1
    assert "manifest not found" in capsys.readouterr().err


# --- tracks with no maqam ---------------------------------------------------

def test_track_without_maqam_uses_raw_style(sun, tmp_path):
    # legacy stub: bare genre string, no key: "value" fields, no Maqam mention
    p = _write(tmp_path / "m.json", {"tracks": [
        {"original_title": "t", "styles": "Symphonic cinematic orchestral ballad, heavy rock",
         "lyrics": "///***///\n[Intro]\nسطر", "clip_id": "c123456789"}]})
    doc, report = _convert(sun, p, tmp_path / "songs.json")
    assert len(doc["songs"]) == 1
    assert doc["songs"][0]["style"] == "Symphonic cinematic orchestral ballad, heavy rock"
    assert report["per_maqam"] == {"unknown": 1}
    assert report["provenance"]["unknown_m_000_c1234567"]["maqam"] is None


def test_track_with_fields_but_no_maqam_omits_maqam_sentence(sun, tmp_path):
    p = _write(tmp_path / "m.json", {"tracks": [
        {"original_title": "t",
         "styles": 'genre: "Rock"\nvocals: "deep male vocals"\nmood: "dark"',
         "lyrics": "///***///\n[Verse 1]\nسطر", "clip_id": "c1"}]})
    doc, _ = _convert(sun, p, tmp_path / "songs.json")
    assert doc["songs"][0]["style"] == "Rock deep male vocals Mood: dark."
