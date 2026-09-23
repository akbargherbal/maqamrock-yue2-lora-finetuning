# Drift report — 2026-09-23

> Trimmed example from the first run on this repo; the real report is written to
> `.reconcile/drift_report.md`. Two of the five missing paths are shown, and the
> ignore-list / unverifiable counts appear as counts only — that is the shape to
> expect, not a guarantee of item count.

Source: `.reconcile/claims.json` — 856 claims across 19 live docs. Checkable: 554; flagged: 5 (0.9%).

## Missing paths (5; 2 shown)

- `INFERENCE/yue2_eval_heldout/heldout_eval_report.md:3` — `prepare_yue2_dataset_v2.py` — tried: `INFERENCE/yue2_eval_heldout/prepare_yue2_dataset_v2.py`, `prepare_yue2_dataset_v2.py`
- `README.md:57` — `prepare_yue2_dataset_v2.py` — tried: `prepare_yue2_dataset_v2.py`

## Not verified (counts only)

- gs_uri: 10
- runtime_path: 143
- dotted tokens whose root is not a config section: 25
- matched `skills/docs-reconciler/references/unverifiable.txt` (known external/runtime/example tokens): 124
