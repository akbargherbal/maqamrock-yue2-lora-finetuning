"""Unit tests for INFERENCE/duration_cap.py (GPU-free).

The CLI `main()` is exercised in-process via `runpy` (run as `__main__`), so
coverage sees it — the cap-parity test in test_generate.py runs it as a
subprocess, which coverage cannot trace.
"""
import runpy
import sys
from pathlib import Path

import pytest


# --- pure functions ---------------------------------------------------------

def test_arabic_letters_counts_only_arabic_letters(dur):
    assert dur.arabic_letters("كتاب") == 4
    # harakat are category Mn, not Lo -> not counted
    assert dur.arabic_letters("كِتَاب") == 4
    assert dur.arabic_letters("abc 123") == 0
    # Arabic-Indic digit is category Nd, not Lo
    assert dur.arabic_letters("٠١٢") == 0
    assert dur.arabic_letters("") == 0
    # Persian/Urdu letters inside the Arabic block still count
    assert dur.arabic_letters("پچژگ") == 4


@pytest.mark.parametrize("q", [0.90, 0.95, 0.975])
def test_duration_cap_matches_the_documented_fit(dur, q):
    a, b = dur.COEFFS[q]
    for n in (0, 10, 100, 300):
        dur_s, rounded, cap, quantile = dur.duration_cap(n, q)
        assert dur_s == a + b * n
        assert rounded == round(dur_s / 10.0) * 10
        assert cap == int(round(rounded * 25))
        assert quantile == q


def test_duration_cap_default_quantile_is_095(dur):
    assert dur.duration_cap(0) == dur.duration_cap(0, 0.95)


# --- CLI (in-process, so coverage traces it) --------------------------------

def _invoke_cli(dur_path: Path) -> int:
    with pytest.raises(SystemExit) as ei:
        runpy.run_path(str(dur_path), run_name="__main__")
    return ei.value.code


def test_cli_default_quantile(dur, tmp_path, monkeypatch, capsys):
    lyrics = tmp_path / "l.txt"
    lyrics.write_text("يا ليل يا عين", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["duration_cap.py", str(lyrics)])
    assert _invoke_cli(Path(dur.__file__)) == 0
    captured = capsys.readouterr()
    assert captured.out.strip() == str(dur.duration_cap(dur.arabic_letters("يا ليل يا عين"))[2])
    assert "N_letters=" in captured.err and "cap=" in captured.err


def test_cli_explicit_quantile(dur, tmp_path, monkeypatch, capsys):
    lyrics = tmp_path / "l.txt"
    lyrics.write_text("يا ليل يا عين", encoding="utf-8")
    monkeypatch.setattr(sys, "argv",
                        ["duration_cap.py", str(lyrics), "--quantile", "0.975"])
    assert _invoke_cli(Path(dur.__file__)) == 0
    captured = capsys.readouterr()
    n = dur.arabic_letters("يا ليل يا عين")
    assert captured.out.strip() == str(dur.duration_cap(n, 0.975)[2])
    assert "q=0.975" in captured.err


def test_cli_empty_lyrics_uses_floor(dur, tmp_path, monkeypatch, capsys):
    lyrics = tmp_path / "empty.txt"
    lyrics.write_text("", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["duration_cap.py", str(lyrics)])
    assert _invoke_cli(Path(dur.__file__)) == 0
    assert capsys.readouterr().out.strip() == str(dur.duration_cap(0)[2])
