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

## 2026-09-29 — `docs/music-cover-feasibility.md` §9 addendum (v2 dataset / repeat question)

- Added §9.1–9.7: characterised the v2 training set **read-only** from
  `gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/dataset/`
  (267 `.mp3`+`.txt` pairs) — maqam balance, 100% `arabmaqamrock`, 100% `110 BPM`,
  100% flat captions, **0%** descriptor lyric tags; repetition 98% buffer-in /
  99% buffer-out / 100% ≥1 repeat / 23% of lines.
- Resolved the outro-repeat: the adapter's **trained convention** (the training
  sheets repeat by design via the external `suno-workflow`); sampler exonerated
  (`repetition_penalty=1.2 penalty_window=50` = 2.0 s in every render).
- Corrected §6's "anomalous repetition" note to point at §9; bumped the header
  `_Last revised_`.
- Re-scoped the ABC/cover batch (§9.5): control arm, `abc_file`→`cot` confound,
  no-repeat-sheet control, Maqam clash Ajam-vs-Hijaz.
- Indexed in `docs/README.md`; added a `SOURCE_OF_TRUTH.md` row for the measured
  dataset facts.
- Reconciler: 1903 claims / 46 docs, 1179 checkable, **6 flagged** — all 6 the
  pre-existing missing `manifests/workspace_manifest.json` fixture; **0 new
  drift**. Two initial flags (`workflow.md`, `Quick_Guide.md` — external
  suno-workflow files) cleared by scoping them in
  `skills/docs-reconciler/references/unverifiable.txt`.
- Authority: user request (document the session); no run config or hyperparameter
  changed; no frozen doc rewritten. Knob tables + the proposed batch stay in
  `agent_notes/current.md` (handoff surface, **not** authority).

## 2026-09-29 — test-batch artifacts (`manifests/test_verbatim_hijaz/`, `INFERENCE/test_batch.sh`)

- Added `manifests/test_verbatim_hijaz/batch.json` (strict `generate.py` schema,
  **validated** with `--dry-run`: 5 songs → 15 tracks): guide-track arms with
  `lora=v2`, fixed seeds `4148240095/1029169725/1938238049`, cap auto q=0.95.
- Added `styles/` (hijaz_winning, hijaz_modified **placeholder to revise**,
  hijaz_sunoblk) and `lyrics/` (`01_nesib_as-is`, `_dedup`, `_bare`) — the last two
  generated programmatically from `batch_36_songs.json` (no hand transcription).
- Added `INFERENCE/test_batch.sh <knobs|abc|all>`: the B (knob, `EXTRA_REQUEST_OPTS`)
  and C (ABC, direct `audiocpp_cli` with `cot=melody[+abc_file]`) arms that
  `generate.py`/`run_one.sh` cannot express. Both B and C verified via `--dry-run`.
- Updated `agent_notes/current.md` with the artifact paths.
- Reconciler: 1903 claims / 46 docs, 1179 checkable, **6 flagged** — all the
  pre-existing `manifests/workspace_manifest.json` fixture; **0 new drift**.
- Authority: user request (write the test JSON + companion script); no run config or
  hyperparameter changed; no frozen doc rewritten.
- Follow-up: added the **raw Suno block** (`l0_raw` form — the prompt that scored 5/5
  MaqamRock), reusing `styles/hijaz_sunoblk.txt`, to **both** the B and C arms: C
  `c3_abc_raw` + `c0raw_cotonly`; B `b1raw_window` / `b2raw_guidance` / `b3raw_both`
  (vs the `ctl_sunoblk_as-is` baseline in `batch.json`). Reconciler: 1903 claims / 46
  docs, 1183 checkable, **6 flagged** (same pre-existing fixture) — **0 new drift**.
- Reconciliation pass (skill): `music-cover-feasibility.md` §9.5 updated to name the
  durable artifact paths (`manifests/test_verbatim_hijaz/batch.json`,
  `INFERENCE/test_batch.sh` arms) rather than only `agent_notes/current.md`. No other
  live doc contradicts the new artifacts (INFERENCE.md's scope is the standard
  procedure — left as-is; the ABC/cover work stays in the investigation record).
