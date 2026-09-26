# Reconciliation log

Dated records of docs changes: file, what-and-why, and the authority. One entry per pass.

## 2026-09-23 — `DECISIONS.md` / `PROGRESS.md` consolidation (frozen-doc exemption, user-approved)

- `DECISIONS.md`: 38 entries / 565 lines → 35 entries / 227 lines. Admission test applied (keep only what a fresh session would otherwise re-litigate or rediscover); merged the three L4/A100 entries into one and folded the two T4-attention entries; archived the v2-build-process and "Current plan (2026-09-21)" narratives to git. Baseline recorded in the header: `git show 50c8de8:DECISIONS.md`.
- `PROGRESS.md`: 740 → 582 lines. Condensed the 2026-09-19 listening/root-cause entry and the 2026-09-21 audio.cpp entry (both duplicated in `DECISIONS.md`); all other entries, including recent milestones and the 2026-09-23 agenda, untouched.
- Citation fix: `INFERENCE/suno_to_songs.py:18` re-pointed `DECISIONS.md:174-194` → `DECISIONS.md:111-119`.
- Authority: user-approved consolidation per `skills/docs-reconciler/SKILL.md` consolidation mode; compression only — no claim inverted, updated, or invented.
- Known stale-but-frozen: `docs/IMPROVEMENTS.md` lines 92/108/112/124 cite pre-consolidation `DECISIONS.md` line numbers; frozen, left as history.

## 2026-09-23 — drift reconciliation (live docs), 4 → 0 findings

- Reconciler run after the consolidation: 891 claims, 4 flagged (0.7%) → **0**.
- `docs/FINAL_BACKUP.md:142`: `` `ANALYSIS.md` `` → `` `TRAINING_ANALYSIS/ANALYSIS.md` `` (authority: the file's real location).
- `docs/FUTURE_PRONUNCIATION_LORA.md:58-59`: qualified the parenthetical as the external `vrgamegirl19/Yue2_Studio` doc, not this repo's `docs/`.
- `skills/docs-reconciler/references/unverifiable.txt`: added `prepare_yue2_dataset_v2.py` (local-only build script, deliberately uncommitted — `README.md`/heldout report already say so) and a doc-scoped `docs/FUTURE_PRONUNCIATION_LORA.md :: docs/lora.md` (external-repo doc).
- Frozen leftovers deliberately not touched: `docs/IMPROVEMENTS.md:92/108/112/124`.

## 2026-09-24 — new `PRON_LORA_SWEEP.md` + drift reconciliation (live docs), 10 → 0

- Added `docs/PRON_LORA_SWEEP.md` (Task 17 alpha-sweep runbook: the 5 configs, adapter build, the `INFERENCE/pron_alpha_sweep.sh` driver, the blinded review package; numbers deferred to `results/pron_sweep/`). The four pron docs (train / verify / merge / sweep) were absent from the index — added rows for all four to `docs/README.md`.
- Created `SOURCE_OF_TRUTH.md` (Step 0; it was missing) with rows for the pron topics and the new doc.
- Curated `skills/docs-reconciler/references/unverifiable.txt` for the 10 false-positive externals: ai-toolkit source `extensions_built_in/audio_models/yue2/yue2_model.py`; the converter script `converter/convert_aitoolkit_yue2_lora.py`; runtime `gcp_backup.log`; git flag `--porcelain`; doc-scoped historical quotes (`RECONCILIATION_LOG.md :: ANALYSIS.md`, `:: docs/lora.md`); and doc-scoped Task 17 artifacts (`sweep_manifest.json`, `KEY_open_after_listening.txt`, `KEY.json`, `results/pron_sweep/KEY.json` — the last is created by Task 17 step 6).
- Reconciler after: 1261 claims, 759 checkable, **0 flagged**.
- Authority: `skills/docs-reconciler/SKILL.md` (live docs only); no frozen doc touched. The `docs/INFERENCE.md` sm89/sm_75 stale lines are handled separately in the Task 17 step-6 commit.

## 2026-09-25 — drift reconciliation (live docs), 8 → 0

- Reconciler run after the graphify commit (e7077ec): 1361 claims, 831 checkable, 8 flagged (1.0%).
- Real drift (Batch A): the graphify refresh command was written as the assistant-skill flag inside a shell block, where it is not a valid command. Authority — the installed CLI: its usage lists `update <path>` as the subcommand, and an unrecognised leading-dash command exits 1. Corrected `docs/GRAPHIFY.md` (the bash refresh line and the two prose mentions) and the `AGENTS.md` Knowledge-graph paragraph to the runnable `graphify update .`.
- False positives (Batch B), curated in `skills/docs-reconciler/references/unverifiable.txt`: doc-scoped the external graphify `install` platform flag (`docs/GRAPHIFY.md`); doc-scoped two historical Task 17 artifact names quoted in this log; doc-scoped the generated graph edge-arrow token in `graphify-out/GRAPH_REPORT.md`.
- Step 0 (Batch C): added a `docs/GRAPHIFY.md` authority row to `SOURCE_OF_TRUTH.md` for the new knowledge-graph topic (`docs/README.md` already indexes it).
- No frozen doc touched; no config or hyperparameter changed.

## 2026-09-25 — drift reconciliation (live docs) after the swap + Round-3 arch fix, 11 → 0

- Reconciler run after the `maqam_lyric_swap` commit (`d3f4922`) and the Round-3 binary-arch correction (`73a92fb`): 1415 claims, 856 checkable, 11 flagged (1.3%) → **0**.
- Real drift (Batch A): `skills/inference-batch-run/SKILL.md` said the alternative to the staged sm_75 binary was to "build from source"; the documented L4 path is a **prebuilt per-arch `gsutil cp`** (`docs/INFERENCE.md:210,305`, `docs/audiocpp_gpu_arch_builds.md:132`). Corrected. `SOURCE_OF_TRUTH.md`'s sweep row named only `results/pron_sweep/`; broadened to Rounds 1–4 and the four records dirs.
- False positives (Batch B), curated in `skills/docs-reconciler/references/unverifiable.txt`: staged prompt files `*_style.txt` / `*_lyrics.txt` (the existing `_style.txt`/`_lyrics.txt` entries matched nothing — missing the leading `*`), and a doc-scoped `KEY_open_after_listening.txt` for the three `results/*/README.md` that cite the package-dir key.
- Outside the reconciler (Batch C): appended the `pkill -f '<pattern>'` self-match gotcha to `docs/COMMAND_HANDOVER_GOTCHAS.md` (the launching shell's own command line contains the pattern; anchor with `^python.*…`).
- Noted only, not touched: `DECISIONS.md:232` still says the sm89-l4 binary "has not been run on an L4" — **frozen**, history stays history.
- No config or hyperparameter changed.

## 2026-09-26 — drift reconciliation (live docs) after the LoRA reorg + graphify refresh, 35 → 0

- Reconciler run after the LoRA-library reorg/hedging, the α-grid build, and the graphify AST+semantic refresh (`a69cd1b`): 1628 claims, 1023 checkable, 35 flagged (3.4%) → **0**.
- Real drift (Batch A): none in the docs' facts. All 35 were mechanical scope/curation gaps, not contradictions.
- Scope fix (Batch B): `graphify-out/` is generated by `graphify update` (rebuilt wholesale) and must not be reconciled. Added `graphify-out` to `DEFAULT_EXCLUDES` + `SKIP_PARTS` in `skills/docs-reconciler/scripts/claims_common.py` (removes the `GRAPH_REPORT.md` and dated-snapshot flags).
- Small real fix (Batch C): `docs/GRAPHIFY.md` refresh comment cited bare `manifest.json`; qualified to `graphify-out/manifest.json` (authority: the file's real location, and the doc's own layout table).
- False positives (Batch D), curated in `skills/docs-reconciler/references/unverifiable.txt`: the `ab-blind-eval` package outputs `EVAL.txt` / `KEYS.txt` / `key.json` / `KEY_open_after_listening.txt` / `config/per-track` (written by `prepare_ab_eval.py` into GCS `listening/` packages; doc-scoped per file); sweep/runtime illustrations `_failed.log`, `__Kurd.json`, `json/log/gpu.csv/time.txt`; the external audio.cpp doc `docs/models/yue2.md` and the absolute runtime converter path `*/convert_aitoolkit_yue2_lora.py`; and external CLI flags `docs/GRAPHIFY.md :: --update` (graphify skill) and `:: --from` (uv).
- No frozen doc touched; no config or hyperparameter changed.
