#!/usr/bin/env python3
"""Verify claims.json against the repo and write a drift report (no LLM involved)."""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

from claims_common import iter_code, relpath

FLAG_LITERAL_RE = re.compile(r"--[a-z][a-z0-9-]{1,}")
DEFAULT_IGNORE_FILE = "skills/docs-reconciler/references/unverifiable.txt"


def load_ignore_patterns(path: Path) -> tuple[str, ...]:
    if not path.is_file():
        return ()
    patterns = []
    for line in path.read_text().splitlines():
        entry = line.split("#", 1)[0].strip()
        if entry:
            patterns.append(entry)
    return tuple(patterns)


def is_ignored(token: str, claim_file: str, patterns: tuple[str, ...]) -> bool:
    for pattern in patterns:
        if "::" in pattern:
            doc, token_pattern = (part.strip() for part in pattern.split("::", 1))
            if claim_file == doc and fnmatch.fnmatch(token, token_pattern):
                return True
        elif fnmatch.fnmatch(token, pattern):
            return True
    return False


def repo_index(root: Path):
    by_basename: dict[str, list[Path]] = defaultdict(list)
    for path in root.rglob("*"):
        if path.is_file() and ".git" not in path.parts:
            by_basename[path.name].append(path)
    flags: set[str] = set()
    for path in iter_code(root):
        try:
            text = path.read_text(errors="ignore")
        except OSError:
            continue
        flags.update(match.group(0) for match in FLAG_LITERAL_RE.finditer(text))
    return by_basename, flags


def config_index(config_path: Path):
    if not config_path.is_file():
        return None, None
    try:
        import yaml
    except ImportError:
        return None, None
    doc = yaml.safe_load(config_path.read_text())
    if not isinstance(doc, dict):
        return set(), set()
    top = {str(key) for key in doc}
    flat: set[str] = set()

    def walk(node, prefix: str) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                dotted = f"{prefix}.{key}" if prefix else str(key)
                flat.add(dotted)
                walk(value, dotted)

    walk(doc, "")
    return top, flat


def resolve_candidates(root: Path, doc_rel: str, token: str, by_basename):
    doc_dir = (root / doc_rel).parent
    candidates: list[Path] = []
    for base in (doc_dir, root):
        candidate = Path(os.path.normpath(base / token))
        if candidate not in candidates:
            candidates.append(candidate)
    if "/" not in token:
        matches = by_basename.get(Path(token).name, [])
        if len(matches) == 1 and matches[0] not in candidates:
            candidates.append(matches[0])
    return candidates


def verify(
    payload: dict,
    root: Path,
    config_path: Path,
    ignore_patterns: tuple[str, ...] = (),
) -> dict:
    by_basename, flags = repo_index(root)
    top, flat = config_index(config_path)
    flagged: dict[str, list[dict]] = {
        "missing_path": [],
        "citation_out_of_range": [],
        "unknown_flag": [],
        "unknown_config_key": [],
    }
    unchecked: Counter = Counter()
    skipped_config = 0
    ignored_claims = 0
    checkable = 0

    for claim in payload["claims"]:
        kind = claim["kind"]
        if kind in ("path", "citation", "flag") and is_ignored(
            claim["raw"], claim["file"], ignore_patterns
        ):
            ignored_claims += 1
            continue
        if kind in ("path", "citation"):
            checkable += 1
            candidates = resolve_candidates(root, claim["file"], claim["raw"], by_basename)
            found = next((c for c in candidates if c.exists()), None)
            if found is None:
                flagged["missing_path"].append(
                    {
                        "file": claim["file"],
                        "line": claim["line"],
                        "raw": claim["raw"],
                        "tried": [relpath(root, c) for c in candidates],
                    }
                )
                continue
            if kind == "citation" and found.is_file():
                total = len(found.read_text(errors="ignore").splitlines())
                if claim["start_line"] > total or claim["end_line"] > total:
                    if claim["end_line"] != claim["start_line"]:
                        ref = f"{claim['start_line']}-{claim['end_line']}"
                    else:
                        ref = str(claim["start_line"])
                    flagged["citation_out_of_range"].append(
                        {
                            "file": claim["file"],
                            "line": claim["line"],
                            "raw": f"{claim['raw']}:{ref}",
                            "resolved": relpath(root, found),
                            "file_lines": total,
                        }
                    )
        elif kind == "flag":
            checkable += 1
            if claim["raw"] not in flags:
                flagged["unknown_flag"].append(
                    {"file": claim["file"], "line": claim["line"], "raw": claim["raw"]}
                )
        elif kind == "config_key":
            root_key = claim["raw"].split(".")[0]
            if top is None or root_key not in top:
                skipped_config += 1
                continue
            checkable += 1
            if claim["raw"] not in flat:
                flagged["unknown_config_key"].append(
                    {"file": claim["file"], "line": claim["line"], "raw": claim["raw"]}
                )
        else:
            unchecked[kind] += 1

    total_flagged = sum(len(items) for items in flagged.values())
    ratio = total_flagged / checkable if checkable else 0.0
    return {
        "claims": len(payload["claims"]),
        "files": len(payload["files_scanned"]),
        "checkable": checkable,
        "flagged": total_flagged,
        "ratio": ratio,
        "structural_warning": checkable >= 20 and ratio > 0.30,
        "details": flagged,
        "unchecked": dict(unchecked),
        "skipped_config_keys": skipped_config,
        "ignored": ignored_claims,
        "ignore_file": None,
    }


def render_report(summary: dict, claims_path: str, config_path: str) -> str:
    lines = [
        f"# Drift report — {date.today().isoformat()}",
        "",
        f"Source: `{claims_path}` — {summary['claims']} claims across {summary['files']} live docs. "
        f"Checkable: {summary['checkable']}; flagged: {summary['flagged']} "
        f"({summary['ratio'] * 100:.1f}%).",
        "",
    ]
    if summary["structural_warning"]:
        lines += [
            "> **Structural warning:** more than 30% of checkable claims failed. This corpus "
            "needs a scoped rewrite, not a reconciliation pass — stop and tell the user.",
            "",
        ]
    details = summary["details"]
    sections = (
        ("missing_path", "Missing paths"),
        ("citation_out_of_range", "File:line citations out of range"),
        ("unknown_flag", "Flags not found anywhere in repo code"),
        ("unknown_config_key", f"Keys not in `{config_path}`"),
    )
    for key, title in sections:
        items = details[key]
        if not items:
            continue
        lines.append(f"## {title} ({len(items)})")
        lines.append("")
        for item in items:
            loc = f"{item['file']}:{item['line']}"
            if key == "missing_path":
                tried = ", ".join(f"`{t}`" for t in item["tried"])
                lines.append(f"- `{loc}` — `{item['raw']}` — tried: {tried}")
            elif key == "citation_out_of_range":
                lines.append(
                    f"- `{loc}` — `{item['raw']}` — `{item['resolved']}` has {item['file_lines']} lines"
                )
            else:
                lines.append(f"- `{loc}` — `{item['raw']}`")
        lines.append("")
    if not summary["flagged"]:
        lines += ["No drift found among checkable claims.", ""]
    counts = summary["unchecked"]
    if counts or summary["skipped_config_keys"] or summary["ignored"]:
        lines.append("## Not verified (counts only)")
        lines.append("")
        for kind, count in sorted(counts.items()):
            lines.append(f"- {kind}: {count}")
        if summary["skipped_config_keys"]:
            lines.append(f"- dotted tokens whose root is not a config section: {summary['skipped_config_keys']}")
        if summary["ignored"]:
            source = summary.get("ignore_file") or "ignore list"
            lines.append(f"- matched `{source}` (known external/runtime/example tokens): {summary['ignored']}")
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="repo root (default: .)")
    parser.add_argument("--claims", default=".reconcile/claims.json", help="claims JSON from extract_claims.py")
    parser.add_argument("--report", default=".reconcile/drift_report.md", help="output report path")
    parser.add_argument("--config", default="config/akbar_arabic_rock_lora.yml", help="run config to verify keys against")
    parser.add_argument("--ignore-file", default=DEFAULT_IGNORE_FILE, help="tokens that legitimately live outside the repo")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    claims_path = Path(args.claims)
    if not claims_path.is_absolute():
        claims_path = root / claims_path
    report_path = Path(args.report)
    if not report_path.is_absolute():
        report_path = root / report_path
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = root / config_path
    ignore_path = Path(args.ignore_file)
    if not ignore_path.is_absolute():
        ignore_path = root / ignore_path

    if not claims_path.is_file():
        print(f"no claims file at {claims_path} — run extract_claims.py first")
        return 2

    payload = json.loads(claims_path.read_text())
    summary = verify(payload, root, config_path, load_ignore_patterns(ignore_path))
    if ignore_path.is_file():
        summary["ignore_file"] = relpath(root, ignore_path)
    report = render_report(summary, relpath(root, claims_path), relpath(root, config_path))
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report + "\n")

    print(f"checkable={summary['checkable']} flagged={summary['flagged']} "
          f"({summary['ratio'] * 100:.1f}%) ignored={summary['ignored']} -> {report_path}")
    for key, items in summary["details"].items():
        if items:
            print(f"  {key}: {len(items)}")
    if summary["structural_warning"]:
        print("STRUCTURAL: >30% of checkable claims flagged — see report header")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
