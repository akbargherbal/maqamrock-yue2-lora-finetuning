from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "skills" / "docs-reconciler" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import extract_claims  # noqa: E402
import verify_claims  # noqa: E402


def _repo(tmp_path: Path) -> Path:
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "c.yml").write_text(
        "config:\n  name: run\ntrain:\n  steps: 3000\n"
    )
    (tmp_path / "INFERENCE").mkdir()
    (tmp_path / "INFERENCE" / "duration_cap.py").write_text("x = 1\n")
    (tmp_path / "backup_to_gcp.py").write_text(
        'p.add_argument("--inference")\np.add_argument("--extra")\n'
    )
    (tmp_path / "PROGRESS.md").write_text("See `also/missing.py`.\n")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "START.md").write_text("Run `README.md` for the overview.\n")
    (tmp_path / "README.md").write_text(
        "\n".join(
            [
                "Run `python backup_to_gcp.py --inference`.",
                "Flag `--bogus-flag` is fake.",
                "See `missing/dir/file.py`.",
                "Citation `backup_to_gcp.py:9999` is wrong.",
                "Key `train.wrong_key` is wrong and `train.steps` is right.",
                "Cap comes from `duration_cap.py`.",
                "Workspace `/content/audiocpp_inference/out`.",
                "The `INFERENCE/` directory exists.",
                "The file `config.yaml` is not a key.",
                "```json",
                '{ "lyrics_file": "../my_lyrics/kurd_night.txt" }',
                "```",
            ]
        )
        + "\n"
    )
    return tmp_path


def test_extract_scope_and_kinds(tmp_path):
    payload = extract_claims.extract(_repo(tmp_path), extract_claims.DEFAULT_EXCLUDES)
    assert "PROGRESS.md" not in payload["files_scanned"]
    kinds = {claim["kind"] for claim in payload["claims"]}
    assert {"path", "citation", "flag", "config_key", "runtime_path"} <= kinds
    raws = {claim["raw"] for claim in payload["claims"]}
    assert "kurd_night.txt" not in raws


def test_verify_findings(tmp_path):
    root = _repo(tmp_path)
    payload = extract_claims.extract(root, extract_claims.DEFAULT_EXCLUDES)
    summary = verify_claims.verify(payload, root, root / "config" / "c.yml")

    missing = {item["raw"] for item in summary["details"]["missing_path"]}
    assert "missing/dir/file.py" in missing
    assert "duration_cap.py" not in missing
    assert "README.md" not in missing
    assert "INFERENCE/" not in missing

    ranges = {item["raw"] for item in summary["details"]["citation_out_of_range"]}
    assert "backup_to_gcp.py:9999" in ranges

    flags = {item["raw"] for item in summary["details"]["unknown_flag"]}
    assert "--bogus-flag" in flags
    assert "--inference" not in flags

    keys = {item["raw"] for item in summary["details"]["unknown_config_key"]}
    assert keys == {"train.wrong_key"}


def test_ignore_file_suppresses_missing(tmp_path):
    root = _repo(tmp_path)
    payload = extract_claims.extract(root, extract_claims.DEFAULT_EXCLUDES)
    summary = verify_claims.verify(
        payload, root, root / "config" / "c.yml", ("missing/dir/file.py", "config.yaml")
    )
    assert summary["details"]["missing_path"] == []
    assert summary["ignored"] == 2


def test_load_ignore_patterns(tmp_path):
    ignore = tmp_path / "unverifiable.txt"
    ignore.write_text(
        "# comment\n\nrun.py   # inline comment\n*.gguf\nreport.md :: *.txt\n"
    )
    assert verify_claims.load_ignore_patterns(ignore) == ("run.py", "*.gguf", "report.md :: *.txt")
    patterns = verify_claims.load_ignore_patterns(ignore)
    assert verify_claims.is_ignored("yue2-3b.gguf", "docs/x.md", patterns)
    assert verify_claims.is_ignored("a.txt", "report.md", patterns)
    assert not verify_claims.is_ignored("a.txt", "other.md", patterns)
    assert not verify_claims.is_ignored("run.py", "docs/x.md", ("*.gguf",))


def test_include_all_scans_frozen(tmp_path):
    payload = extract_claims.extract(_repo(tmp_path), (), include_all=True)
    assert "PROGRESS.md" in payload["files_scanned"]


def test_report_render(tmp_path):
    root = _repo(tmp_path)
    payload = extract_claims.extract(root, extract_claims.DEFAULT_EXCLUDES)
    summary = verify_claims.verify(payload, root, root / "config" / "c.yml")
    report = verify_claims.render_report(summary, ".reconcile/claims.json", "config/c.yml")
    assert "Missing paths" in report
    assert "missing/dir/file.py" in report
    assert "Not verified" in report
