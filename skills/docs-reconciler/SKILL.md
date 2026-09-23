---
name: docs-reconciler
description: Reconcile live project docs against actual code/config and resolve contradictions between them, without an unscoped rewrite. Use when asked to clean up docs, fix stale or outdated documentation, audit the docs, or make the docs match the code. Mechanical extraction and verification run first; proposed edits are surgical and each needs human approval before being written.
---

# Docs reconciliation

"Clean up the docs" is unbounded. This splits it: scripts find *candidate*
problems cheaply, model judgment is spent only on flagged items, and the user
approves every edit. Do not skip to "just fix everything" — that is the failure
mode this exists to prevent.

## Scope: live vs frozen (this repo)

Reconcile (editable): `README.md`, `AGENTS.md`, `skills/*/SKILL.md`, the live
runbooks in `docs/` (`START.md`, `MONITOR.md`, `PAUSE_RESUME.md`,
`BACKUP_RESTORE.md`, `INFERENCE.md`, `docs/README.md`,
`text_to_duration_formula.md`, `audiocpp_gpu_arch_builds.md`, `FINAL_BACKUP.md`,
`GPU_L4_VS_A100.md`), and `INFERENCE/` help text.

Frozen (read-only; never "corrected"): `DECISIONS.md`, `PROGRESS.md`,
`docs/IMPROVEMENTS.md`, `docs/LIVE_STATUS.md`, `verification.md`,
`docs/investigation.md`, `docs/yue2-gguf-lora-findings.md`,
`TRAINING_ANALYSIS/v1_nolyrics_archived/`, `agent_notes/`. History stays history:
add a dated entry, don't rewrite it. The scripts exclude these by default.
Exception: a deliberate, user-approved consolidation pass may *compress* them
(conclusions kept, narrative dropped, git as the archive) — never silently.

Authority when two docs disagree: config YAML + code (`--help`, argparse)
outrank `docs/` runbooks, which outrank `README.md`. `DECISIONS.md` is the
authority for *why* — cite it, never re-litigate it.

## Step 0 — Source-of-truth map

If `SOURCE_OF_TRUTH.md` is missing at the repo root, create it from
`references/source_of_truth_template.md` (topic → the one authoritative file).
Every future pass reuses it.

## Step 1 — Extract claims (scripted)

```bash
python skills/docs-reconciler/scripts/extract_claims.py --root .
```

Writes `.reconcile/claims.json`: repo paths, `file:line` citations, CLI flags,
dotted config keys, runtime/GCS paths, date stamps. No model judgment here.

## Step 2 — Verify mechanically

```bash
python skills/docs-reconciler/scripts/verify_claims.py --root .
```

Writes `.reconcile/drift_report.md` with only the failures: missing paths,
out-of-range citations, flags defined nowhere in repo code, config keys not in
the run config. If it prints the **structural warning** (>30% of checkable
claims flagged), stop and tell the user the corpus needs a scoped rewrite, not a
reconciliation pass.

## Step 3 — Batch

Group flagged items by file or topic; never send more than ~10–15 to judgment in
one batch.

## Step 4 — Propose minimal diffs

Per item: quote the contradiction, state what the authority says is correct, and
give the smallest edit — never rewrite surrounding prose. Check freshness with
`git log -1 --format=%cs -- <file>` against the source file the doc describes
(this repo has no `Last verified:` stamps; stamps are recognized if adopted).

## Step 5 — Human checkpoint

Present diffs per file/topic; apply only what the user approves. Config and
hyperparameters are the user's call (`AGENTS.md`).

## Step 6 — Apply and log

Targeted replacements only. Append date / file / one-line what-and-why /
authority to `RECONCILIATION_LOG.md` (root; create on first run).

## Guardrails

- Steps 1–2 are script-only; never pull whole documents into context for them.
- Suppress missing-path noise only by curating `references/unverifiable.txt` with
  review — a broad glob there hides real drift.
- Never rewrite a frozen doc to match today's code.
- Never accept "clean up all the docs" as one pass; scope it first.
- Nothing is written before the Step 5 checkpoint.

## Bundled resources

- `scripts/extract_claims.py`, `scripts/verify_claims.py` — run directly, don't reimplement.
- `references/example_drift_report.md` — expected report shape.
- `references/source_of_truth_template.md` — Step 0 starting map.
- `references/unverifiable.txt` — curated tokens that legitimately live outside the repo (runtime artifacts, ai-toolkit/audio.cpp files, example inputs, external flags). Scope a token to one doc with `path/to/doc.md :: glob`.
