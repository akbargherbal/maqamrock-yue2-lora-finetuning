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

## 2026-09-27 — drift reconciliation (live docs) after the 10% subsample pivot

- Reconciler run after the s10 pivot: 1790 claims / 44 live docs, 1105 checkable, **10 flagged (0.9%), all benign** — runtime/example tokens (`selection_report.json`, `dataloader_mixins.py`, `<log-name>_state.json`), external vm-continuity flags (`--host`, `--mode`), and `EXPERIENCE_CHECKLIST.md` prose "config/data/course" misread as a path. No real contradiction; left uncurated.
- The real gap was **semantic** (the pivot), not mechanical: the authority/index docs still spoke v2/full-set. User-approved edits:
  - `docs/README.md`: hub row label `quran_long_aya_r8` → `quran_long_aya_r8_s10`; added a Constants note that the long-aya run's names/paths live in its Snapshot (the table is v2).
  - `docs/PRON_LORA_LONG.md`: added the resume check — after restoring the run output, the log must print `Found step N`, not step 0.
  - `docs/PAUSE_RESUME.md`: top note that the long-aya run uses `PRON_LORA_LONG.md`'s names/paths and its latent cache is banked (the "~12 min rebuild" line is v2).
  - `SOURCE_OF_TRUTH.md`: added rows for the long-aya runbook, its configs, and its GCS dataset/cache/checkpoint artifacts.
- Authority: `skills/docs-reconciler/SKILL.md` (live docs only); `DECISIONS.md` got a dated entry (frozen rule respected).
- No config or hyperparameter changed.

## 2026-09-27 — BETA merge: README/PROGRESS rewrite + pron-donor supersede rename

- `README.md` rewritten as the statement of record (BETA framing; current artifacts = v2 style LoRA +
  long-aya Quran pronunciation donor, `qfinal_a0.3/0.5` unselected candidates). Killed two false claims
  found via local `gsutil`: the v1 run/dataset "GCS archive" is absent from the project prefix (no
  surviving v1 adapter), and the pron LoRA is not "not scheduled" — it was built and superseded.
  Authority: the live GCS listing + `docs/LORA_INVENTORY.md`.
- `PROGRESS.md` compressed from 981 lines of narrative to **numbered milestones** (M1–M11 + open items)
  under the user-approved frozen-doc exemption; pre-rewrite baseline recorded in the header
  (`git show 39d1bbd:PROGRESS.md`). No claim inverted; outcomes preserved with evidence pointers.
  `SOURCE_OF_TRUTH.md` rows split: `PROGRESS.md` = milestones, history = git.
- Supersede rename applied **repo ⇄ GCS in lockstep**: the `pron_lora_ar_only_r8` family (15 merged
  `c3050/c4575/cfinal_a0.*` + 3 source pins) moved to GCS `archive/pron_lora_ar_only_legacy/`; run prefix
  renamed `pron_lora_ar_only_r8_obsolete/`. Repo refs updated: `docs/LORA_INVENTORY.md`, `docs/INFERENCE.md`,
  `docs/PRON_LORA_MERGE.md`, `docs/PRON_LORA.md`, `docs/PRON_LORA_VERIFICATION.md`, `docs/PRON_LORA_SWEEP.md`,
  `docs/L4_HANDOFF_TASK14C.md`, `bootstrap/setup.sh`, `SOURCE_OF_TRUTH.md`, `DECISIONS.md` (new entry).
- De-branched the fresh-VM docs + notebooks (`git checkout main`); `docs/FUTURE_PRONUNCIATION_LORA.md`
  got a "realized" banner. Reconciler after: 1828 claims / 45 docs, 1139 checkable, 18 flagged (1.6%),
  all pre-existing benign except one glob in the new README (fixed); `graphify update .` refreshed
  (956 nodes / 1726 edges).
- Authority: user-approved consolidation + rename; no config or hyperparameter changed.

## 2026-09-27 — `DECISIONS.md` condensed (second frozen-doc exemption pass)

- `DECISIONS.md`: 46 headings / 370 lines → **11 sections / 88 lines**, grouped by topic instead of
  chronology. Admission test per the file's charter: keep only what a fresh session would otherwise
  re-litigate or rediscover (binding rules, verified source quirks, costly traps) — process narrative
  and incident chronology were folded into their outcomes. Baseline recorded in the header:
  `git show 39d1bbd:DECISIONS.md`. Compression only: no claim inverted, and the one now-false claim
  (v1's "185-object GCS archive") was corrected against the live GCS listing.
- Superseded/updated in place where live state overrode the old text: the LoRA library counts (now
  style + qfinal; legacy archived), the notebooks' branch (`main`, since the BETA merge), and the donor
  family (archived — see this session's rename entry above).
- Citation re-point: `INFERENCE/suno_to_songs.py:18` `DECISIONS.md:111-119` → `DECISIONS.md:25`.
- Reconciler exposed two `citation_out_of_range` hits — both pre-consolidation `DECISIONS.md:NN`
  quotes inside this log (history). Doc-scoped them in `references/unverifiable.txt`
  (`RECONCILIATION_LOG.md :: DECISIONS.md:*`), matching the existing history-quote curations.
- Authority: user-approved consolidation per `skills/docs-reconciler/SKILL.md`; no config or
  hyperparameter changed.

## 2026-09-28 — drift reconciliation (live docs) after the graphify refresh

- Reconciler run: 1866 claims / 45 docs, 1157 checkable, **18 flagged (1.6%)** — no structural
  warning, and on inspection **no real contradiction**: 12 missing paths + 6 unknown flags, all
  either runtime artifacts, external-tool flags, or the log's own quotes of past runs.
- Judgment calls (user-approved, `AGENTS.md:120` aside, no live doc text changed):
  - `AGENTS.md:120`: bare `GRAPH_REPORT.md` → `graphify-out/GRAPH_REPORT.md` (made resolvable).
  - `RECONCILIATION_LOG.md` is now **excluded from extraction outright** (`claims_common.py`
    `DEFAULT_EXCLUDES` + `SKILL.md` scope): an append-only log that quotes past drift reports
    verbatim re-flags every old finding forever. Its former per-token curations in
    `references/unverifiable.txt` were removed with it.
  - Curated in `references/unverifiable.txt` (doc-scoped, nothing global hid real drift):
    `--host`/`--mode` as external `vm-continuity` flags (`setup.sh:87-88` clones it to
    `/content/vm-continuity`); `*_state.json` (`train_ctl.py:53` runtime file);
    `docs/EXPERIENCE_CHECKLIST.md` prose "config / data / course"; the pron build's
    `selection_report.json` / `dataloader_mixins.py` (live in `/content`, not the repo).
- Semantic spot-check against source (the half scripts can't do): `docs/INFERENCE.md` (09-28)
  matches `INFERENCE/generate.py` (09-28); LoRA library path agrees across `setup.sh:120`,
  `docs/LORA_INVENTORY.md:17`, `docs/INFERENCE.md:27`; the `<dir>/akbar_arabic_rock_lora_{ar,nar}
  .safetensors` registry convention matches the inventory; the two docs missing from
  `docs/README.md`'s index are linked from their hubs (intentional).
- Re-run after the edits: 1750 claims / 44 docs, 1080 checkable, **0 flagged (0.0%)**.
- Authority: user-approved reconciliation per `skills/docs-reconciler/SKILL.md`; no config or
  hyperparameter changed; no frozen doc rewritten.

## 2026-09-28 — `AGENTS.md` rewritten (agent-contract revision, user-approved)

- Rewrote `AGENTS.md` from a critique of the prior contract; user approved the draft and it
  replaced the live file. Structural changes, not fact changes:
  - **§0** authority now via `SOURCE_OF_TRUTH.md` + `docs/README.md` (one row per topic),
    replacing the three duplicated canonical-docs lists.
  - **§2** adds an explicit mode→runbook→authority table and an **environment check**
    (Colab vs local; never assume the main run — constants live in `docs/README.md`).
  - **§4** "Ground truth in one move": `status.py` named as the target (not built;
    `docs/IMPROVEMENTS.md` #11) with an interim one-block read.
  - **§6** redefines `agent_notes/current.md` as a copy/read surface only — explicitly not
    documentation and not a source of truth (removes the prior "routine per-session state"
    framing).
  - **§8** reconciles the GPU rule with the permission to run (non-GPU) tests; **§9** adds
    the verified-vs-assumed + definition-of-done norm; **§12** adds the self-maintenance loop
    (`docs-reconciler` → this log → `SOURCE_OF_TRUTH.md` / `docs/README.md`).
  - Dropped the repo-restore and backup-layout prose (delegated to `docs/START.md` /
    `docs/BACKUP_RESTORE.md`); removed the "Nothing else" scope line.
- Proposal file `AGENTS.proposed.md` deleted after approval.
- Authority: user-approved contract revision; no config or hyperparameter changed; no frozen
  doc (DECISIONS/PROGRESS) touched. `status.py` is a named gap, not yet created.

## 2026-09-28 — drift reconciliation (live docs) after the `AGENTS.md` rewrite

- Reconciler run after the contract revision: 1723 claims / 44 docs, 1064 checkable,
  **2 flagged (0.2%), both benign** — `AGENTS.md:58` and `AGENTS.md:61` name `status.py`,
  which is a deliberate forward reference (§4 marks it "proposed, not built"). No real
  contradiction; **no live doc edited.**
- Judgment call: `status.py` is **not** curated into `references/unverifiable.txt`. It is a
  planned repo file, not an external/runtime token — hiding it would mask real drift if it
  lands (or keeps failing to). The flag should disappear when the script is built; if it
  isn't, the flag is a correct reminder.
- Semantic spot-check (the half scripts can't do), since `AGENTS.md` was just rewritten:
  every runbook in the §2 mode table resolves (`docs/{START,PAUSE_RESUME,MONITOR,INFERENCE,
  audiocpp_gpu_arch_builds,PRON_LORA_MERGE,PRON_LORA,PRON_LORA_LONG,PRON_LORA_VERIFICATION,
  PRON_LORA_SWEEP,AB_BLIND_EVAL,BACKUP_RESTORE}.md`); all five named skills exist under
  `skills/`; `SOURCE_OF_TRUTH.md`, `RECONCILIATION_LOG.md`, `graphify-out/GRAPH_REPORT.md`,
  `docs/GRAPHIFY.md` all resolve. The authority map's "one row per topic" matches the file's
  existing rows.
- Authority: `skills/docs-reconciler/SKILL.md` (live docs only); no config or hyperparameter
  changed; no frozen doc rewritten.

## 2026-09-28 — `status.py` built + `AGENTS.md` graphify corrections

- Added `status.py` (the §4 "ground truth in one move" tool) and `tests/test_status.py`
  (6 GPU-free tests; suite 165 green, the torch module excluded locally, as usual).
  Read-only and environment-aware: Colab reads the full picture; a local checkout reports the
  `/content` surfaces as `n/a` rather than "not running". Reports training step/rate + pid,
  inference batch `n/N` + failures, sidecar pids, last-backup age, local-vs-GCS drift, disk
  free, the run folder, and graph staleness (`built_at_commit` vs HEAD). §4's
  `docs/IMPROVEMENTS.md` #11 "proposed, not built" note was removed; `IMPROVEMENTS.md` itself
  left frozen.
- `AGENTS.md` corrections — the graphify shortcomings traced back to the file:
  - §0: added "a `graphify query` is a locator, not a read", resolving the tension between
    §12 recommending the graph and §0 declaring "everything else is not in scope".
  - §1: "Three jobs" → "Four jobs", adding "Stay oriented" — the missing job that left any
    orientation tool without a purpose in the contract.
  - §12: fixed the refresh instruction. `graphify update .` is code/AST-only; doc/semantic
    edges need `/graphify --update`. The old line ("refresh with `graphify update .`") was
    what *caused* the semantic staleness the earlier review flagged. Also added the authority
    rule (orientation only, never authority; quote `built_at_commit`).
- Reconciler after the changes: 1723 claims / 44 docs, 1061 checkable, **0 flagged**.
  Reworded `config/code/docs` → "the config, code, or docs" (a false missing-path token) and
  curated two external graphify flags (`AGENTS.md :: --budget`, `AGENTS.md :: --update`)
  beside the existing `docs/GRAPHIFY.md` entries.
- Authority: user-directed implementation of the reviewed plan; no run config or
  hyperparameter changed; no frozen doc rewritten.

## 2026-09-28 — `generate.py` names: ASCII-only slug → Unicode slug

- `generate.NAME_RE` widened from `^[A-Za-z0-9][A-Za-z0-9_-]*$` to
  `^[^\W_][\w-]*$` (Unicode letters/digits + `-`/`_`; still rejects spaces, dots,
  slashes and leading punctuation). Hand-authored Arabic names in
  `manifests/batch_36_songs.json` now validate; repeats still dedup to `_2`/`_3`.
  Names reach `run_one.sh` as quoted argv and are used as path components, so
  Unicode is safe end-to-end.
- Docs: `docs/INFERENCE.md` `name` row and the `generate.py` module docstring
  updated to match; `tests/test_generate.py` gained a Unicode-accept test and
  `../evil` / `.hidden` reject cases (fragment `ASCII slug` → `required name slug`).
- Reconciler after the change: 1722 claims / 44 docs, 1061 checkable, **6 flagged**;
  all 6 are the pre-existing missing `manifests/workspace_manifest.json` fixture
  (same cause as the `test_suno_to_songs` failures) — **0 new drift**.
- Authority: user-directed ("fix the script, not the batch; Arabic names should
  work"); no run config or hyperparameter changed; no frozen doc rewritten.

## 2026-09-28 — `user_cheatsheet.md` (user-facing copy-paste index)

- Added `user_cheatsheet.md` at the repo root: copy-paste commands grouped by task
  (ground-truth `status.py`, sidecars, fresh-VM setup + GH auth, train
  start/status/stop, monitoring, inference LoRA staging + `generate.py`, backup /
  verify / restore, pause-resume, finish + push, gotchas). Explicitly marked
  **index, not authority**; every command is sourced from a runbook
  (`START.md`, `PAUSE_RESUME.md`, `MONITOR.md`, `INFERENCE.md`,
  `BACKUP_RESTORE.md`, `FINAL_BACKUP.md`) and the scripts' `--help`.
- Indexed it in `docs/README.md` (task table) and `SOURCE_OF_TRUTH.md`
  (row: index only; the runbooks above are authority).
- Two script/tool false positives fixed during the pass (`$OUT/loss_log.db` and
  `*_ctl.py` tokens → literal path / `train_ctl.py`).
- Reconciler after the change: 1835 claims / 45 docs, 1129 checkable, **6 flagged**;
  all 6 are the pre-existing missing `manifests/workspace_manifest.json` fixture —
  **0 new drift**.
- Authority: user request (avoid re-asking the agent for recurring commands); no
  run config or hyperparameter changed; no frozen doc rewritten.
- Follow-up: clarified in `user_cheatsheet.md` that `gpu_logger.py` is a
  **training-only** sidecar — inference needs no global logger because
  `run_one.sh` writes a per-track `<name>_<seed>_gpu.csv` at 1 Hz. Reconciler:
  1837 claims / 45 docs, 1130 checkable, **6 flagged** (same pre-existing
  fixture) — 0 new drift.

## 2026-10-04 — `run_one.sh`: per-expert adapter scales are env-overridable

- `INFERENCE/run_one.sh` now reads `LORA_AR_SCALE` / `LORA_NAR_SCALE` (default
  `1.0`), forwarded as `yue2.ar_lora_scale` / `yue2.nar_lora_scale`. Unset behavior
  is byte-identical to before (both were the hardcoded literal `1.0`). This enables
  the "Quran pron LoRA alone / base model" arms from `agent_notes/current.md`:
  audio.cpp treats a scale of `0` as adapter-off (base weights), verified in
  `docs/yue2-gguf-lora-findings.md:2.3` / PR #586.
- `docs/INFERENCE.md` "Fixed session options" bullet updated to state the scales
  default to 1.0 and are overridable by those env vars; no other doc claimed a
  hardcoded scale for `run_one.sh`.
- Tests: `tests/test_generate.py` + `tests/test_merge_pron_lora.py` pass
  (73 passed, 1 skipped — the end-to-end converter invariant, artifacts not
  staged). `tests/test_suno_to_songs.py` failures are the pre-existing missing
  `manifests/workspace_manifest.json` fixture, unrelated.
- Reconciler after the change: 1838 claims / 45 docs, 1131 checkable, **6 flagged**;
  all 6 are that same pre-existing fixture — **0 new drift**.
- Authority: user-directed experiment prep; no run config or hyperparameter
  changed; no frozen doc rewritten.

## 2026-10-04 — gotcha: CUDA-13 image needs CUDA-12 libs on `LD_LIBRARY_PATH`

- Added a `docs/COMMAND_HANDOVER_GOTCHAS.md` entry: the prebuilt sm_75
  `audiocpp_cli` links CUDA 12 (`libcublas.so.12`, `libcudart.so.12`); on this
  CUDA-13 Colab image those ship only in the pip `nvidia-*-cu12` packages, so the
  binary dies with `exit=127` unless every `nvidia/*/lib` dir is on
  `LD_LIBRARY_PATH`. The `.so.12` files are present (verified with `ldd`); this is
  a loader-path fix, not a missing toolkit. Prevented a second wasted launch.
- Reconciler after the change: 1845 → 1845 claims / 45 docs, 1131 checkable,
  **6 flagged** — all 6 the pre-existing missing `manifests/workspace_manifest.json`
  fixture — **0 new drift**.
- Authority: user-directed (generation failed; fix the env, report it); no run
  config or hyperparameter changed; no frozen doc rewritten.

## 2026-10-04 — Quran-only (α=1) experiment recorded; `build_pron_only_fused.py`

- Added `docs/QURAN_ONLY_EXPERIMENT.md` (the AR-only→fused workaround, the first-sample
  result, and the early-self-termination finding) + repo-root `build_pron_only_fused.py`.
  Indexed in `docs/README.md` and `SOURCE_OF_TRUTH.md` (row: Quran pron alone on base).
- Reconciler after the change: **1885 claims / 46 docs, 1155 checkable, 6 flagged** — all 6
  the pre-existing missing `manifests/workspace_manifest.json` fixture — **0 new drift**.
- Authority: user request ("document everything"); no run config or hyperparameter changed;
  no frozen doc rewritten.

## 2026-10-04 — session recorded in the durable trail (`PROGRESS.md`, `DECISIONS.md`)

- Added **`PROGRESS.md` M12** (Quran pron alone, α=1 — first sample rendered; self-terminates
  at ~one aya) + an Open-item for the comparison arms.
- Added **`DECISIONS.md`** bullets (LoRA-merge section): a pron adapter "alone" is not a merge
  and the raw file already is α=1; the converter requires both branches →
  `build_pron_only_fused.py`; an AR-only adapter also governs sequence length (cap can't
  extend it).
- Reconciler: 1885 claims / 46 docs, 1155 checkable, **6 flagged** (pre-existing
  `workspace_manifest.json` fixture) — **0 new drift** (`PROGRESS.md`/`DECISIONS.md` are
  excluded from the scan).
- Authority: user request ("so the next session knows exactly what we did"); no run config or
  hyperparameter changed.

## 2026-10-04 — Quran format/caption probe documented (GPU test, pending)

- Added `docs/QURAN_FORMAT_PROBE.md` (background + 6-arm design for the
  `INFERENCE/songs.quran_format_probe.json` manifest) and indexed it in `docs/README.md`;
  added a `SOURCE_OF_TRUTH.md` row (Quran adapter format/caption probe).
- Reconciler after the change: **1917 claims / 47 docs, 1178 checkable, 6 flagged (0.5%)** —
  all 6 the pre-existing `manifests/workspace_manifest.json` fixture — **0 new drift**.
- Authority: user request ("write background about the test we're doing on the GPU VM"); no
  run config or hyperparameter changed; no frozen doc rewritten.

## 2026-10-04 — Quran format/caption probe run recorded (6/6)

- `docs/QURAN_FORMAT_PROBE.md`: status "prepared, not yet run" → "run 2026-10-04, 6/6
  rendered; listening verdict pending"; added a "Run result" section (per-arm durations +
  `truncated=no`, objective duration reads only — no quality verdict).
- `agent_notes/current.md`: rewritten with the live run status + result table.
- Reconciler: **not run this pass** — deliberately deferred to the CPU VM to avoid
  GPU-paid time; the edit is additive (a result section + a status flip), no claim inverted.
- Authority: user request ("push to gh; discuss findings on cpu vm"); no run config or
  hyperparameter changed.

## 2026-10-04 — Quran format/caption probe listening verdict recorded

- `docs/QURAN_FORMAT_PROBE.md`: status "listening verdict pending" → "received"; added a
  "Listening verdict (user)" section: prosody (madd/waqf) present in all arms, but
  pronunciation unusable in all six (~1 makhraj error every 2–3 words, incl. in-domain T6);
  caption-sensitive looping on a specific half-line (T1/QURAN ×3, T2 ×2, T3/NASHEED ×7,
  T4/KHALIJI ×3, T5/QASIDA ×4, T6 none); T6 stops cleanly. Added a per-track
  `semantic.tokens` table, and a "Bearing on the ceiling risk" note tying the makhārij
  failure to the MERT-token representational limit (`FUTURE_PRONUNCIATION_LORA.md:143-148`).
- `agent_notes/current.md`: rewritten with the verdict + open items.
- Reconciler: not run this pass (still pending from the GPU commit, which deferred it to
  the CPU VM). The edit is additive — a listening result + tokens, no claim inverted.
- Authority: user's listening report (2026-10-04); no run config or hyperparameter changed.

## 2026-10-04 — Quran-pron objective/criteria/next-run review

- Added `docs/QURAN_PRON_REVIEW.md` (post-verdict audit: the reframed objective;
  acceptance-criteria proposal; the teacher-forced-eval criteria error; the AHH
  filtered dataset; config/ceiling/sampler hypotheses; an ordered cheap-first plan).
  Indexed in `docs/README.md`; two `SOURCE_OF_TRUTH.md` rows added (the review, and
  the AHH dataset repo/zip); the stale probe row note ("prepared not yet run") fixed.
- Second revision (same day, after user clarification): added the corrected symptom
  framing (prosody gained, words degraded), a "catastrophic-forgetting hypothesis"
  subsection (§2.7, marked unverified), and an "assumptions & hypotheses — re-opened"
  table. User's explicit direction: success ≠ "hear ح/ع"; the training method must be
  re-examined.
- Findings verified from artifacts: eval used `ar_ce`/`ar_kl` only (teacher-forced)
  and `disable_sampling: true`; AHH = 13,501 mp3 / 4,650 ayat / 3 reciters.
- Correction (same day, per user): the old dataset's 67,505 pairs vs the 81,006
  planned is **by design** — the three AHH reciters (Abdul_Basit, Hudhaify, Husary)
  were carved out, leaving them `_uthmani`-only (verified per reciter in GCS). The
  trained set was the **8,100-pair `s10` subsample**, not 81k/67.5k.
- Reconciler: not run this pass (still outstanding from the GPU commit). Changes are
  additive (new review doc + index rows); no claim inverted; no config or
  hyperparameter edited.
- Authority: user request ("comprehensive review … stop repeating training without
  benefit") + the clarifications on dataset quality/reciters and Tanzil text.

## 2026-10-06 — config rename fallout + drift reconciliation (live docs/code), 36 → 0

- Renamed `config/akbar_arabic_rock_lora.yml` → `config/LEGACY_akbar_arabic_rock_lora.yml`
  and added per-GPU `config/L4_…` / `config/A100_…` variants (session config split).
  Reconciler then re-pointed every live reference to the old path:
  - `SOURCE_OF_TRUTH.md:8` + `skills/docs-reconciler/references/source_of_truth_template.md:8`
    (authority row) → both new configs (+ LEGACY = v1/v2).
  - `README.md:53` (tree) / `:108` (prose) → both variants + LEGACY.
  - `skills/crash-diagnose-and-resume/SKILL.md:44`, `docs/L4_HANDOFF_TASK14C.md:95` → `config/A100_…`.
  - `docs/COMMAND_HANDOVER_GOTCHAS.md:104` → new `train_ctl.py` default (`LEGACY_…`).
  - `train_ctl.py:40` `DEFAULT_CONFIG` → `config/LEGACY_…` (behavior-preserving);
    `skills/docs-reconciler/scripts/verify_claims.py:250` default likewise.
  - `bootstrap/setup.sh:648` echoed launch hint → `config/A100_…`.
- Historical records (`TRAINING_ANALYSIS/ANALYSIS.md:28`,
  `INFERENCE/yue2_eval_heldout/heldout_eval_report.md:6,253`) → `LEGACY_…` (same artifact, renamed).
- Fixed a pre-existing self-reference: `docs/QURAN_AHH_RESUME_PLAN.md:4` cited
  `agent_notes/RESUME_PLAN.md` → `docs/QURAN_AHH_RESUME_PLAN.md`.
- Curated `unverifiable.txt`: this session's placeholders/externals (`bad.db`, `clean.db`,
  `BaseSDTrainProcess.py`, `--force-reinstall`) plus `workspace_manifest.json` (user-supplied
  legacy input), `docs/investigation_generation_knobs.md` (other branch), `config/hyperparameters.`
  (prose), `agent_notes/T4_listening_checklist.md` and the eval_app/`convert/` runtime files.
- Reconciler after: 2237 claims, 1384 checkable, **0 flagged** (was 36 / 2.6%).
- Deliberately untouched (frozen): `PROGRESS.md:11`,
  `TRAINING_ANALYSIS/v1_nolyrics_archived/ANALYSIS.md:34` (still name the old path as history),
  `graphify-out/GRAPH_REPORT.md` (generated snapshot).
- Authority: `skills/docs-reconciler/SKILL.md`; user-approved scope ("scope agreed").
  Config values unchanged except the pre-agreed split; no hyperparameter edited.

## 2026-10-06 — encode the CUDA-12 loader path (recurring `audiocpp_cli` `exit=127`), code + docs

- Fix: the prebuilt sm_75/sm89 `audiocpp_cli` links CUDA 12
  (`libcublas.so.12`/`libcudart.so.12`); a CUDA-13 image exposes those only via the pip
  `nvidia-*-cu12` wheels, and **nothing set the loader path** — so every fresh VM redied
  `exit=127` and the requirement lived only as prose (gotcha 2026-10-04). Added
  `INFERENCE/cuda_loader_path.sh` (self-healing resolver), sourced it in
  `INFERENCE/run_one.sh` — the choke point for `generate.py` / `pron_*_sweep.sh` /
  `maqam_lyric_swap.py` — and made `bootstrap/setup.sh --inference` resolve + `pip install`
  the `-cu12` wheels and **fail the verify** if `ldd` still shows `not found`; it also
  persists the path in `~/.bashrc` for interactive shells.
- Docs: `docs/COMMAND_HANDOVER_GOTCHAS.md` (2026-10-04 entry marked "Encoded 2026-10-06");
  `docs/INFERENCE.md` (setup section notes the automatic loader path).
- Verified: bare shell (`env -u LD_LIBRARY_PATH`) resolves the binary; `--check` exits 0;
  sourcing twice is idempotent; an interactive shell resolves via `~/.bashrc`; `bash -n`
  clean on both scripts. No config or hyperparameter touched.
- Authority: user directive ("fix things once and for all … while the root cause exists")
  + the 2026-10-04 gotcha's own "Correct pattern".

## 2026-10-06 — encode the other two "documented but not enforced" gotchas (ctime restore, WAL checkpoint)

- `bootstrap/restore_run.py` (new): rsyncs `<base>/<run-name>/output` → the local output
  root, re-stamps checkpoint ctime in ascending step order, verifies the resume pick, and
  refuses while `run.py` is alive. Replaces the bare-rsync + hand-`chmod` restore in
  `docs/PAUSE_RESUME.md` and `docs/BACKUP_RESTORE.md` (both updated).
- `backup_to_gcp.py`: `checkpoint_sqlite_dbs()` runs `PRAGMA wal_checkpoint(TRUNCATE)` on
  every `*.db` under each synced folder (called in the pass loop before `sync`), so the main
  `loss_log.db` alone is a consistent snapshot.
- Corrected a wrong gotcha claim: `touch` **does** bump ctime on this filesystem (verified
  2026-10-06: `…014` → `…015`); the earlier "chmod updates ctime; `touch` does not" was
  wrong. The ctime gotcha's pattern now reads "re-stamp in ascending step order".
- Both gotcha entries marked **Encoded 2026-10-06**.
- Verified: WAL test (61832 → 0 bytes, `PRAGMA integrity_check=ok`, rows intact); a
  simulated collapsed restore reproduced the original failure (arbitrary pick
  `_000009000`) and the helper corrected it (picks `quran_ahh_r32.safetensors`); dry-run and
  the `run.py`-alive guard exercised. No config or hyperparameter touched.
- Authority: user directive (2026-10-06: "fix those issues … before we do another
  inference") + the two gotchas' own "Durable fix belongs in …" notes.
