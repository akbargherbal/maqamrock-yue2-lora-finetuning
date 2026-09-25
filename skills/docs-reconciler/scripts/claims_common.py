"""Shared scope rules for the docs-reconciler claim extractor/verifier."""

from __future__ import annotations

from pathlib import Path

KNOWN_DIRS = (
    "docs",
    "config",
    "skills",
    "tests",
    "bootstrap",
    "INFERENCE",
    "manifests",
    "TRAINING_ANALYSIS",
    "agent_notes",
)

KNOWN_EXTS = (
    "md",
    "py",
    "sh",
    "yml",
    "yaml",
    "json",
    "txt",
    "csv",
    "log",
    "db",
    "safetensors",
    "gguf",
)

# Frozen by design: history (PROGRESS/DECISIONS), archived audits/research,
# machine-local notes. Reconciling these would rewrite the record, not fix drift.
DEFAULT_EXCLUDES = (
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    ".reconcile",
    "__pycache__",
    "node_modules",
    "agent_notes",
    "TRAINING_ANALYSIS/v1_nolyrics_archived",
    "DECISIONS.md",
    "PROGRESS.md",
    "verification.md",
    "docs/IMPROVEMENTS.md",
    "docs/LIVE_STATUS.md",
    "docs/investigation.md",
    "docs/investigation_generation_knobs.md",
    "docs/yue2-gguf-lora-findings.md",
    "skills/docs-reconciler/references/example_drift_report.md",
)

CODE_SUFFIXES = (".py", ".sh")

SKIP_PARTS = {
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    ".reconcile",
    "__pycache__",
    "node_modules",
    ".claude",
}


def is_excluded(rel: Path, excludes: tuple[str, ...] = DEFAULT_EXCLUDES) -> bool:
    posix = rel.as_posix()
    for raw in excludes:
        ex = raw.rstrip("/")
        if not ex:
            continue
        if "/" in ex:
            if posix == ex or posix.startswith(ex + "/"):
                return True
        elif ex in rel.parts:
            return True
    return False


def iter_markdown(root: Path, excludes: tuple[str, ...] = DEFAULT_EXCLUDES):
    for path in sorted(root.rglob("*.md")):
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        rel = path.relative_to(root)
        if is_excluded(rel, excludes):
            continue
        yield path, rel


def iter_code(root: Path):
    for path in sorted(root.rglob("*")):
        if path.suffix not in CODE_SUFFIXES or path.is_symlink():
            continue
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        yield path


def relpath(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)
