# current

_Updated 2026-09-30 (localhost). **Docs reconciliation + graphify cache-untrack — COMPLETE.**
`status.py` @ `9bc008f`. Mechanical 0 flagged; changes uncommitted._

## What changed (all uncommitted)

Docs reconciliation (6 semantic findings):
- `AGENTS.md`: §2 "build the inference binary" authority → in-repo
  (`docs/audiocpp_gpu_arch_builds.md` + `bootstrap/setup.sh`); `_Last revised_` 2026-09-30.
- `SOURCE_OF_TRUTH.md`: new build/stage row.
- `docs/PRON_LORA_LONG_PLAN.md`: dropped the "single source of truth" self-claim.
- `docs/README.md`: indexed `PRON_LORA_LONG_PLAN.md`; marked `L4_HANDOFF_TASK14C.md` historical.
- `docs/E2E_TESTING_PLAN.md` §8: "proposals" → "as landed"; phantom `tests/fixtures/gpu/` removed.
- `unverifiable.txt`: 4 dead E2E suppressions pruned.

Graphify tracking (user decision, multi-VM):
- **`graphify-out/cache/` untracked + gitignored** (`git rm -r --cached`; `.gitignore:20`).
  Outputs stay committed (8 files: `graph.json`, `GRAPH_REPORT.md`, `graph.html`,
  `manifest.json`, labels, `cost.json`, `.graphify_root`).
- Rationale: cache is keyed by graphify version; VMs differ (0.9.70 vs committed 0.9.71),
  so tracking it churned 189 files per refresh. AST rebuild is free (no LLM).
- Documented in `.gitignore`, `docs/GRAPHIFY.md`, `DECISIONS.md` ("Knowledge graph"
  section), `RECONCILIATION_LOG.md`.
- `graphify update .` ran: 1275 nodes / 2457 edges / 91 communities at `9bc008f`.

## State

- Re-verify: 2168 claims / 49 files, **0 flagged**.
- `graphify-out/` now tracks **8** files (was 189). Fresh VM rebuilds the cache
  locally on first `graphify update`; semantic edges ride in the committed outputs.
- `.opencode/`: opencode's own `.opencode/.gitignore` already excludes
  `node_modules`, `package.json`, `package-lock.json`; only the hand-authored
  `opencode.json` + `plugins/graphify.js` were untracked — now staged for tracking.
- No commit made (per policy) — the cache deletions and `.opencode` adds are staged;
  everything else unstaged.

## Ground truth reminders

- One GPU, shared, rented — `nvidia-smi` before any GPU work (idle; localhost).
- This file is a handoff surface, not authority — re-derive with `python status.py`.
