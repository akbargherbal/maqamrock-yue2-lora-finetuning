# current.md — docs reconciliation: applied — 2026-10-13

Copy/read surface only, **not authority**. The 2026-10-13 reconciler pass is applied; the
durable record is the dated entry in `RECONCILIATION_LOG.md`.

## Applied this pass (11 edits)

`README.md` (v3 bullet + dataset line) · `docs/V3_SPICE_SWEEP.md`, `docs/V3_JARIR_SEED_PROBE.md`
(status) · `SOURCE_OF_TRUTH.md` (spice row) · `AGENTS.md` (skills list + revision line) ·
`docs/README.md` (env row + index row) · `docs/L4_HANDOFF_TASK14C.md` +
`skills/docs-reconciler/references/source_of_truth_template.md` (renamed configs).

Re-ran Steps 1–2 after: **22 → 19 flags (1.2%)**, all pre-existing false positives.

## Open — needs a call

- `README.md:24` spells the v2 GCS folder `v2_arabmaqrock_dataset/`; the canonical name is
  `v2_arabmaqamrock_dataset/` (`SOURCE_OF_TRUTH.md:9`, `DECISIONS.md:28`). The mechanical pass
  missed it.

## Deferred (user-approved)

- Curate `skills/docs-reconciler/references/unverifiable.txt` for the recurring bucket tokens
  (`README.txt`, `LAYOUT.json`, `GCP_ORGANIZATION_PLAN.md`).
- `skills/docs-reconciler/SKILL.md:15-19` — replace the editable-runbook enumeration (it
  predates the v3/probe docs) with a pointer to `docs/README.md`.
