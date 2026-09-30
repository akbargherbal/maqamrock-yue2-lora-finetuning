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

## 2026-09-29 — branch gotcha: a fresh clone lands on `main`

- `docs/COMMAND_HANDOVER_GOTCHAS.md`: recorded that a fresh Colab clone checks out
  `main` (10 commits behind `music-cover`), so this session's artifacts are absent;
  fix is `git fetch origin music-cover && git checkout music-cover` (or merge to
  `main`). `agent_notes/current.md`: same note at the artifact list.
- `skills/docs-reconciler/references/unverifiable.txt`: scoped the external git flag
  `--branch` to that doc (cleared 2 `unknown_flag` findings).
- Reconciler: 1916 claims / 46 docs, 1192 checkable, **6 flagged** (same pre-existing
  `manifests/workspace_manifest.json` fixture) — **0 new drift**.
- Authority: user question (fresh-VM readiness); no run config or hyperparameter changed.
- Follow-up (same day): decision recorded — all work stays on `music-cover`; **do not
  merge to `main`**. `COMMAND_HANDOVER_GOTCHAS.md` + `agent_notes/current.md` now say
  to clone with `--branch music-cover`. Reconciler: 6 flagged (same pre-existing
  fixture) — 0 new drift.
- Follow-up: `agent_notes/current.md` now ends with a **Run (next Colab session)**
  block (branch, `setup.sh --inference`, the `generate.py` + `test_batch.sh` detached
  commands with stop/resume) so `@agent_notes/current.md` alone primes the next
  session. Reconciler: 6 flagged (same pre-existing fixture) — 0 new drift.

## 2026-09-29 — GCS `audiocpp_inference/` reorganisation: doc consequences + drift pass

_Belated: the reorganisation itself landed in `d46c8c6` without a log entry. This pass
covers both._

- **The change.** `tools/` (pinned: `build/`, `converter/`, `prompts/`,
  `scripts/`), `workspace/` (`out/`, `out_archive/`), `evals/` (8 sweep dirs).
  **Local paths unchanged** — only the remote subfolder moved. Data copied, never
  moved; verified 14/14 MATCH on object count + bytes + CRC32C multiset.
- `docs/BACKUP_RESTORE.md`: inference target table → `workspace/out`,
  `tools/{prompts,scripts}`; added a sectioned-layout paragraph. Authority:
  `backup_to_gcp.py` `INFERENCE_TARGETS`.
- `docs/INFERENCE.md`: 5 GCS path citations → `tools/…`. Authority: same constant +
  `bootstrap/setup.sh`.
- `docs/audiocpp_gpu_arch_builds.md`: staging convention → `tools/build/`; **rewrote the
  stale Note** that said `setup.sh` "pulls only that flat path" (it now probes
  `tools/build/` and falls back) and added "stage new builds to `tools/build/`",
  otherwise a fresh build lands where `setup.sh` no longer looks.
- `skills/inference-batch-run/SKILL.md`, `docs/PRON_LORA_MERGE.md`,
  `docs/LORA_INVENTORY.md` (×2, incl. the `pron_ckpt_sweep` provenance pointer),
  `results/pron_knob_probe/T4_REGEN.md`,
  `results/pron_production_merge/regenerate.sh`: GCS paths → `tools/` / `evals/`.
- **The verifier could not have caught any of those**: it tests existence, and the old
  paths still exist by design (they are the rollback), so every stale citation passed
  as clean. Found by a semantic sweep, not by the scripts.
- **`docs/README.md` + `SOURCE_OF_TRUTH.md`**: added the missing index row for
  `GCP_ORGANIZATION_PLAN.md` (the index's own rule is "must list every live runbook")
  and a source-of-truth row for prefix organisation; corrected the constants row that
  the reorganisation itself had made stale.
- **Claim corrected, not invented.** The plan/GCS `README.txt`/`LAYOUT.json` said
  `quran_long_aya_dataset/` was "93% of all objects" — an estimate. The new inventory
  measures it: **162,746 of 179,493 = 90.7%** (bytes 30,111,258,977, confirmed
  exactly). All four occurrences corrected, on the bucket too. New artifact
  `results/gcs_inventory_20260929.txt` (179,493 objects / 64.8 GB total), closing the
  dangling reference the plan had promised.
- `skills/docs-reconciler/references/unverifiable.txt`: doc-scoped curation for GCS
  bucket objects read as repo paths (`docs/GCP_ORGANIZATION_PLAN.md ::`
  `README.txt`/`LAYOUT.json`/`RETIRED.txt`/`WHERE_ARE_THE_KURD_WAVS.txt`/`.../LAYOUT.json`,
  the proposed `INFERENCE/gcs_layout.py`, and `SOURCE_OF_TRUTH.md :: LAYOUT.json` —
  the extractor strips `<base>/` and then reports the bare filename), plus
  `docs/COMMAND_HANDOVER_GOTCHAS.md :: --bind` (a stdlib `http.server` flag).
- Reconciler: 2009 claims / 47 docs, 1252 checkable, **6 flagged (0.5%)** — exactly the
  pre-existing `manifests/workspace_manifest.json` fixture — **0 new drift**.
- **Deliberately not touched:** `docs/IMPROVEMENTS.md` (frozen) and
  `INFERENCE/yue2_eval_heldout/heldout_eval_report.md` (a dated 2026-09-22 record; it
  cites the then-current flat prompt path, which is history, not a live instruction).
- Authority: verified GCS state (copy + CRC32C verification, `gsutil` listings) and
  `backup_to_gcp.py` / `bootstrap/setup.sh`; no run config or hyperparameter changed.

## 2026-09-29 — `*_gpu.csv` had no header (`run_one.sh`)

- `INFERENCE/run_one.sh`: the per-track 1 Hz `nvidia-smi` CSV was written with
  `--format=csv,noheader,nounits`, so the column meaning existed only in the query
  argument string (and units only in the query's field names, which never reach the
  file). Now writes a header row first; the docstring names the columns and units.
- `INFERENCE/pron_knob_probe.sh` (`_gpu_stats`, the only code reader): it skipped a
  header row only *by accident* (`float()` raised and the row was dropped). Now skips
  it explicitly.
- `docs/INFERENCE.md`: the artifact table named no columns; it now lists
  `gpu_util_pct,mem_used_mib,power_draw_w,temp_c`.
- Names mirror `gpu_logger.py`'s `FIELDS` rather than inventing a second convention.
  That logger **already** wrote a header, and its reader
  (`TRAINING_ANALYSIS/generate_plots.py`, `csv.DictReader`) *requires* one — so the two
  writers disagreed and only the inference side was wrong.
- Existing files backfilled, header-only (4 files, 0 skipped). Safe on a file being
  appended to: the sampler's `>> "$csv"` sits inside its loop body, so it reopens the
  path every second; verified live on an in-flight file (89 → 94 lines across the swap).
- **Noted, not fixed:** `screen_arms.sh` runs the binary directly instead of via
  `run_one.sh`, so the 16 screened arms wrote `_time.txt` + `.log` but **no `gpu.csv`** —
  the screen has no GPU telemetry at all.
- Reconciler: 1252 checkable, **6 flagged** (the pre-existing
  `manifests/workspace_manifest.json` fixture) — **0 new drift**.
- Authority: the writer's own `nvidia-smi` query plus `gpu_logger.py`'s `FIELDS`; no run
  config or hyperparameter changed.

## 2026-09-29 — `status.py` counted annotations as failures

- `status.py:185` counted every non-blank line of `_failed_runs.log`, so the explanatory
  `NOTE` appended there (for the spurious `win_dedup exit=127`, above) made the report read
  `failures: 2`. It now counts `FAILED` lines only, and appends "one is flagged SPURIOUS
  in-file" when the file contains a correction note — so the next session is not invited to
  re-render valid audio.
- Related, same incident: `docs/COMMAND_HANDOVER_GOTCHAS.md` gained the "never edit a shell
  script while it is running" entry, and the run's `_runs_status.log` / `_failed_runs.log`
  carry NOTES.
- Reconciler: no doc claims changed by this edit; no run config or hyperparameter changed.

## 2026-09-29 — verbatim blind round written into the record

- The user's blind evaluation (`manifests/evaluation_verbatim_hijaz/MY_EVALUATION.txt`) was
  decoded against `KEYS.txt` and documented as `docs/music-cover-feasibility.md` **§10**
  (design, scores, verdict, caveats, provenance); the header revision line now names §10.
- Resolved stale §9 claims with cross-references rather than rewriting the dated snapshot:
  §9.5's "no-repeat-sheet arm missing" (since rendered/scored), §9.6 Q4 (sung clean) and Q2
  (not implicated). Q1 (ABC) is left explicitly unrun.
- `docs/README.md`: the not-a-runbook blurb now names §10.
- `SOURCE_OF_TRUTH.md`: new row — round outcome, authority
  `manifests/evaluation_verbatim_hijaz/MY_EVALUATION.txt` (+ `KEYS.txt`).
- `manifests/evaluation_verbatim_hijaz/KEY.json` deleted — a stale copy of the first build's
  decoder; the mapping lives in `KEYS.txt` and in git history at `6443287`.
- Reconciler: narrative-only change; no config, hyperparameter, or script touched, and no
  other live doc asserts this round's outcome — **0 new drift**.

## 2026-09-29 — guide-conditioned batch staged; §11 added

- New driver `INFERENCE/v2_abc_to_qfinal.sh` — four arms (qfinal `cot=off`; qfinal
  `cot=full` no-abc; qfinal `cot=full` + `abc_file` = v2's exported `score.abc`; v2
  `cot=off`), plus a `--stage` mode that pulls `qfinal_a0.3`. `bash -n` + `--dry-run`
  checked. **Not run** — needs a Colab GPU (this box is localhost).
- `docs/music-cover-feasibility.md` **§11**: verified bucket inventory (read-only
  `gsutil ls`), the guide-route options table, the three risks, and what would settle it;
  header revision line updated. `docs/README.md` blurb names §11.
- `agent_notes/current.md` rewritten as the Colab handoff (verified paths + commands).
- Reconciler: bucket access was read-only (no writes); no config, hyperparameter, or
  training artifact changed; no other live doc asserts the batch exists — **0 new drift**.

## 2026-09-29 — Colab reconcile: deleted test fixture restored; graph refreshed

- First pass: 2043 claims / 47 docs, 1274 checkable, **11 flagged (0.9 %)** — all
  `missing_path`; no structural warning.
- **Root cause (previously logged as "pre-existing … 0 new drift" and left):**
  `manifests/workspace_manifest.json` was **deleted in `528f573`** ("Add new suno
  manifests") while `tests/test_suno_to_songs.py` (10 tests) and 3 live docs still
  referenced it — the tests were failing (`[error] manifest not found`). Restored the
  70 KB, 16-track fixture from `528f573^`; all 17 tests in that file now pass, and the 6
  doc claims (`README.md:76`, `docs/INFERENCE.md:187,190,196,198`,
  `skills/inference-batch-run/SKILL.md:25`) resolve to a real file — **no doc prose
  edited**. Authority: `suno_to_songs.py --help` + `tests/conftest.py:59`; the restored
  content reproduces the tests' asserted 16→8 / `{Nahawand 4, Kurd 2, Hijaz 2}`.
- `SOURCE_OF_TRUTH.md:33`: bare `KEYS.txt` → `manifests/evaluation_verbatim_hijaz/KEYS.txt`.
- `skills/docs-reconciler/references/unverifiable.txt`: 3 new doc-scoped entries —
  `docs/COMMAND_HANDOVER_GOTCHAS.md :: _failed_runs.log` (runtime out-dir artifact);
  `docs/music-cover-feasibility.md :: KEY.json` (deleted 2026-09-29, documented in §10);
  `docs/music-cover-feasibility.md :: tokens.json` (a GCS-side `abc_v2` artifact).
- Re-verify: **11 → 1 flagged (0.1 %)**. Residual: `docs/music-cover-feasibility.md:313`
  `KEYS.txt` — a real file cited by relative context ("same dir"); left as-is (the
  qualify-the-path option was declined), resolvable by naming the path or scoping it.
- Graph: `uv tool install graphifyy` + wrote `graphify-out/.graphify_python`;
  `graphify update .` rebuilt 1125 nodes / 2207 edges / 73 communities at HEAD `5ca4c71`
  (was `2f35c76`, 38 commits behind); curated snapshot `graphify-out/2026-09-29/`.
  Free/AST tier only — the semantic `/graphify --update` needs the assistant skill (not
  installed here). The graphify 0.9.70→0.9.71 cache-version bump churns the tracked
  `graphify-out/cache/` (46 deletions + a new untracked dir).
- Authority: git history (the file existed at `528f573^`), the test suite, on-disk state;
  no run config or hyperparameter changed; no frozen doc rewritten.

## 2026-09-29 — guide-conditioned round scored/decoded; §12 added

- The user's blind evaluation (`manifests/evaluation_v2_abc_to_qfinal/MY_EVALUATION.txt`)
  was decoded against `KEYS.txt` and documented as `docs/music-cover-feasibility.md` **§12**
  (design, scores, verdict, caveats, provenance); the header revision line now names §12.
- Resolved §11.5's open question: the guided arm `a2` (`qfinal_a0.3`, `cot=full` + v2's
  `score.abc`) wins both arrangement and pronunciation — the ABC guide is what makes
  `cot=full` usable. §11.4/§11.5 are left as the dated plan and cross-referenced.
- `docs/README.md`: the not-a-runbook blurb now names §12.
- `SOURCE_OF_TRUTH.md`: new row — round outcome, authority
  `manifests/evaluation_v2_abc_to_qfinal/MY_EVALUATION.txt` (+ `KEYS.txt`).
- **Provenance corrected mid-pass.** The tracked manifest and the GCS package are a
  *different shuffle* (`20260931`, `.mp3`, `A=a2, B=ref_v2, C=a0, D=a1`) from the build the
  listener actually scored (`20260932`, `.wav` working tree, `A=ref_v2, B=a0, C=a1, D=a2`).
  The sheet's "C is the longest and didn't finish" requires `C=a1` (310.0 s, capped); under
  `20260931` `C=a0` is 256.8 s, the shortest. Every seed reference in §12 / `SOURCE_OF_TRUTH.md`
  / `agent_notes/current.md` now says `20260932`, with a §12.4 note; the `ab-blind-eval`
  seed registry records both. **Open item (user call): the GCS package is stale and the
  scored build is uncommitted.**
- **Confirmed against the listener's copy** (`…\Downloads\v2abc_blind\`, `.wav`): byte sizes
  match the per-arm render logs one-to-one (`ref` 52,208,428 / `a0` 49,313,068 / `a1`
  59,519,788 / `a2` 54,182,188), so the `20260932` mapping is established mechanically.
- Reconciler: narrative-only change; no config, hyperparameter, or script touched; no other
  live doc asserts this round's outcome — **the only "drift" found was the manifest/package
  mismatch above, now documented, not silently fixed**.

## 2026-09-29 — §12 follow-up: stale "unrun" claims in `music-cover-feasibility.md`

- Post-commit re-read found **5 pre-§12 sentences now false** (§13–14 blurb, §5 "Unverified",
  §9.6 Q1 "Unrun", §10 intro + §10.2 "Q1 (ABC) remains unrun"). Fixed with forward
  cross-references to §12 (dated snapshots not rewritten — repo convention); also pointed
  §11.5 "what would settle it" forward and annotated the §11.1 "not stored (B1)" row.
- Authority: §12's own result (the B1 guide ran and held). Narrative-only; no config,
  hyperparameter, or script touched — **0 new drift**.

## 2026-09-29 — condense `music-cover-feasibility.md` into a topical reference

- The doc had grown to a 12-section dated journal (529 lines). Rewritten as a condensed
  topical record (~10 sections): status → question → cover mechanics → α tradeoff → levers →
  measured v2 training-set facts → round 1 (verbatim) → round 2 (guide-conditioned) → open
  questions (checkbox list) → sources. Addendum/"session" narrative removed; every fact kept.
- **Sections renumbered** (old → new): §3→§3, §4→§4.1, §5→§4.2, §9.4→§4.3, §9.1–9.3→§5,
  §10→§6, §11+§12→§7, §9.6→§8. Every live inbound reference updated: `SOURCE_OF_TRUTH.md`
  (3 rows), `docs/README.md` blurb, `agent_notes/current.md`,
  `skills/ab-blind-eval/SKILL.md`, and the `INFERENCE/{test_batch,v2_abc_to_qfinal,screen_arms}.sh`
  comments. `RECONCILIATION_LOG.md` history left intact (history, not current truth).
- `skills/docs-reconciler/references/unverifiable.txt`: dropped the `KEY.json` doc-scoped
  entry (the doc no longer cites that deleted decoder); `workflow.md`, `Quick_Guide.md`, and
  `tokens.json` are all retained by the rewrite.
- Authority: the doc's own measured facts + round scores, unchanged; narrative-only
  restructure — no config, hyperparameter, or script behaviour touched.

## 2026-09-30 — new `docs/E2E_TESTING_PLAN.md` (proposal) reconciled

- New live doc `docs/E2E_TESTING_PLAN.md` (end-to-end testing plan, Colab/GPU-light)
  added; indexed in `docs/README.md` and `SOURCE_OF_TRUTH.md`.
- Mechanical pass: 2115 claims / 48 files, 1320 checkable, **31 flagged (2.3 %)** —
  all `missing_path`, no structural warning.
- **30 of 31 are the new plan's forward references** (files it will create:
  `tests/e2e/*`, `tests/fixtures/*`, `fake_run.py`, `recorded_batch.json`, …). The doc
  is a proposal (`proposed, not yet implemented`), so their absence is by design, not
  drift. Suppressed with 14 doc-scoped entries in
  `skills/docs-reconciler/references/unverifiable.txt`, mirroring the
  `docs/GCP_ORGANIZATION_PLAN.md :: INFERENCE/gcs_layout.py` precedent.
- **1/31 is a tokenisation false positive**: `docs/music-cover-feasibility.md:10`'s glob
  `manifests/evaluation_*/MY_EVALUATION.txt` extracted as `manifests/evaluation_`; the
  directory family exists. One doc-scoped suppression.
- Re-verify: **31 → 0 flagged (0.0 %)**. No runbook, config, or script content changed;
  `SOURCE_OF_TRUTH.md` gained a row for the new plan topic.
- Authority: the new plan's own banner ("proposed, not yet implemented") + the
  on-disk file tree; no config or hyperparameter touched; no frozen doc rewritten.

## 2026-09-30 — E2E plan Session 1 landed (T2 scaffold + J1)

- Implemented `docs/E2E_TESTING_PLAN.md` §9 Session 1 on the Colab CPU runtime:
  `tests/e2e/replay.py` (`make_replay_runner`), `tests/e2e/conftest.py`
  (`fake_gpu`, `staged_inference`, `run_generate`), `tests/e2e/test_inference_e2e.py`
  (J1), `tests/fixtures/{recorded_batch.json,manifest.json,README.md,fetch.sh}`,
  and the `gpu`/`fixtures_heavy`/`live` markers + default `-m` filter in `pytest.ini`.
- Updated the plan to match reality: banner "in progress", §3 T2 status "partial",
  §9 Session 1 marked done, and §12 rewritten from "decisions needed" to the three
  resolved decisions (Colab free T4 gate; Tier A git / Tier B GCS; fake `run.py`).
  `SOURCE_OF_TRUTH.md` row note updated to match.
- Mechanical pass: 2131 claims / 49 files, 1301 checkable, **0 flagged (0.0 %)**.
  Curated `skills/docs-reconciler/references/unverifiable.txt`: dropped the broad
  `tests/e2e/*` and `tests/fixtures/*` globs (those files now exist) and kept only
  the still-unbuilt Session 2–4 paths + bare filenames the extractor cannot map into
  the new dirs; added the `conftest.py` / `tests/test_*` false-positive suppressions.
- Verified: `python -m pytest` → **181 passed, 1 skipped** (the existing
  `torch`-dependent skip), including the new J1.
- Authority: plan §5.1/§9 + the on-disk test tree; no config, hyperparameter, or
  frozen doc changed.

## 2026-09-30 — E2E plan Session 2 landed (T2 J2–J4, J6 + provenance guard)

- Implemented `docs/E2E_TESTING_PLAN.md` §9 Session 2 on the Colab CPU runtime:
  - J2 re-run/`--force` (`test_j2_rerun_skips_seeds_and_force`): skip on success,
    manifest seed reuse, force redoes.
  - J3 failure/retry (`test_j3_partial_failure_then_retry_recovers`): one `exit=1`
    track -> `_failed_runs.log` -> only that track re-invoked and recovered.
  - J4 registry routing (`test_j4_lora_registry_routing_and_provenance`):
    per-song `loras:` alias -> `env["LORA_AR"]` + sidecar `lora_alias`/shas.
  - J6 round trip (`test_j6_suno_to_generate_round_trip`): real
    `manifests/workspace_manifest.json` -> `suno_to_songs.py` -> real
    `generate.main` (8 songs), byte-for-byte trigger prepend.
  - Provenance guard (`test_provenance_guard`): `manifest.json` sha + the two
    fixture files agree + `checkpoint_step == gen.CHECKPOINT_STEP`; the
    `audio_cpp_commit` half skips until Tier B exists.
- New shared `tests/staging.py::stage_inference_tree`, now used by
  `tests/test_generate.py::_stub_assets` and the e2e `staged_inference` fixture
  (plan §5.1's "reuse `_stub_assets`"); `tests/e2e/replay.py` gained
  `write_track_outputs` + `make_passthrough_runner`; `run_generate` is now
  re-invocable within one test.
- Fixtures: added a synthetic `Saba` `exit=1`/no-audio track to
  `recorded_batch.json` for J3; refreshed its `sha256` in `manifest.json`.
- **Plan wording corrected to match code:** §4.4 now states the `audio_cpp_commit`
  equality is gated on a non-empty `tier_b` (a CPU-tier `/content/audio.cpp` is an
  arbitrary current clone, and `ac16661d` != present `30ec4596` would be a false
  failure). `checkpoint_step` is checked unconditionally. Banner, T2 row, §5.1 and
  the Session 2 row updated; `SOURCE_OF_TRUTH.md` row note updated.
- Mechanical pass: 2139 claims / 49 files, 1304 checkable, **0 flagged (0.0 %)**.
- Verified: `python -m pytest` -> **185 passed, 2 skipped** (the pre-existing
  torch skip + the provenance-guard Tier B skip).
- Authority: plan §4.4/§5/§9 + the on-disk test tree; no config, hyperparameter,
  or frozen doc changed.

## 2026-09-30 — E2E plan Session 3 landed (T3 J10–J12) + a train_ctl.py stop-race fix

- Implemented `docs/E2E_TESTING_PLAN.md` §9 Session 3 on the Colab CPU runtime:
  - `tests/e2e/fake_run.py` — a real process standing in for ai-toolkit `run.py`:
    writes a real `loss_log.db`, appends step lines, answers SIGINT with
    `Job stopped`.
  - `tests/e2e/test_train_lifecycle_e2e.py` (J10): `train_ctl.py` start (own
    session) -> status -> SIGINT stop, against the real detached process; the db
    it wrote is then read by the real `monitor_loss.py`.
  - `tests/e2e/lossdb.py` + `tests/fixtures/loss_log.spec.json`, and
    `tests/e2e/test_monitor_status_e2e.py` (J11): `monitor_loss.py` on a
    spec-built db (exact `~2.000 steps/sec` + ETA), plus `status.py`'s training
    section on that db and its inference section on a real `generate.main` run.
  - `tests/e2e/fake_gsutil.py` (local `gs://` mapper) and
    `tests/e2e/test_backup_restore_e2e.py` (J12): real `backup_to_gcp.py` mirror
    + `run_manifest.json` + a reverse-rsync restore that is byte-identical.
- **Production change (behavior bug, not a contract/hyperparameter):**
  `train_ctl.py::cmd_stop` broke its wait loop the moment it saw `Job stopped`
  in the log and then immediately failed if the child had not yet reached
  `sys.exit()` -- a real race (the log write and process exit can be descheduled
  apart under load). It now gives the process a short 5 s grace to leave `/proc`
  before reporting, and prints the actual elapsed instead of the timeout value.
  The pre-existing `tests/test_train_ctl.py::test_start_detaches_then_stop_is_clean`
  reproduced the flake only under CPU load; 15/15 passes under the same load
  after the fix (was ~2/10). `docs/PAUSE_RESUME.md` still holds ("waits for
  'Job stopped'").
- `tests/fixtures/manifest.json` gained the `loss_log.spec.json` Tier A entry;
  the provenance guard now checks every Tier A entry, not just `recorded_batch`.
  `tests/fixtures/README.md` documents the spec.
- Mechanical pass: 2150 claims / 49 files, 1312 checkable, **0 flagged (0.0 %)**.
- Verified: `python -m pytest` -> **190 passed, 2 skipped** (stable across 4
  consecutive full runs and 15 load runs of the fixed lifecycle test).

## 2026-09-30 — E2E Session 4: T5 GPU gate (L4) + fixture fold + `setup.sh` pin

- **Gate run** (Colab **L4**, sm_89, 2026-09-30): S1 `audiocpp_cli --version` exit 0
  (`backends: cpu,cuda`); S2 real `run_one.sh Hijaz 1` exit 0 (277.16 s, 48 kHz
  stereo, `semantic.truncated 0`); S3 `pron_lora_ar_only_smoke` 10/10 steps, finite
  loss (final `loss/loss` 6.765791), checkpoint + optimizer written. Inference staged
  with the **sm89-l4** binary (`sha256 97028a71…`, matches the fixture's recorded
  `binary_sha256`); `pron_dataset/smoke` staged for S3.
- **Fixture fold**: `tests/fixtures/manifest.json` -> `tier_b` populated
  (`inference/Hijaz_1.wav`, `inference/audiocpp_cli` = sm89-l4, `training/loss_log.db`);
  Tier A gained the real `inference/{Hijaz_1.log,Hijaz_1_time.txt,Hijaz_1_gpu.csv,
  _runs_status.log}` and `training/train_smoke.log`. `recorded_batch.json` /
  `manifest.json` provenance re-recorded to the gate: `audio_cpp_commit` `30ec4596`,
  `checkpoint_step` 3000, L4 / 8.9, `recorded_at` 2026-09-30.
- **Production change** (`bootstrap/setup.sh`): `job_audio_cpp` now pins
  `/content/audio.cpp` to the commit recorded in `tests/fixtures/manifest.json`, so
  `test_provenance_guard`'s `audio_cpp_commit` equality is deterministic on a fresh VM
  instead of depending on upstream `main`. Falls back to HEAD if absent.
- **Docs**: `docs/E2E_TESTING_PLAN.md` status `in progress` -> `complete`; gate host
  corrected from the stale "Colab free T4" to **L4 (sm_89)** in §3/§6/§12; Session 4
  row marked done; `tests/fixtures/README.md` Tier B sm75 -> sm89-l4 + tier_b-populated
  note; `SOURCE_OF_TRUTH.md` row updated. Authority: the gate artifacts + `setup.sh` code.
- Mechanical pass: 2160 claims / 49 files, 1318 checkable, **0 flagged (0.0 %)**.
- Verified: `python -m pytest` -> **191 passed, 1 skipped** (the provenance guard now
  runs instead of skipping); `bash -n bootstrap/setup.sh` ok.
- Open item (not fixed): `AGENTS.md` §2 lists `docs/models/yue2.md` as the authority
  for the "build the inference binary" row, but no such file exists in this repo (it
  is upstream `audio.cpp`'s doc, per `setup.sh` / `INFERENCE.md`).

## 2026-09-30 — docs reconciliation (housekeeping pass after E2E + music-cover)

- Trigger: user housekeeping after `docs/E2E_TESTING_PLAN.md` completed and
  `docs/music-cover-feasibility.md` was condensed. Mechanical layer was **already
  clean**: 2160 claims / 49 files, 1318 checkable, **0 flagged (0.0 %)** — so this
  pass is semantic-only (the half the scripts cannot see).
- **`AGENTS.md:37`** (the Session-4 open item): the "build the inference binary (new
  arch)" authority cell named `` `docs/models/yue2.md` ``, which is upstream
  `audio.cpp`'s doc, not a repo file. Now the in-repo authority
  `docs/audiocpp_gpu_arch_builds.md` + `bootstrap/setup.sh` (arch pin). Added the
  matching `SOURCE_OF_TRUTH.md` row (topic: build/stage `audiocpp_cli`) so the §2
  cell has a row to point at; bumped the `AGENTS.md` `_Last revised_` line
  (its own §12 rule). Authority: `bootstrap/setup.sh::job_audio_cpp` + the plan's
  gate; the upstream flag doc stays curated in `unverifiable.txt`.
- **`docs/PRON_LORA_LONG_PLAN.md`** claimed of itself "*this file is the single
  source of truth*", contradicting `SOURCE_OF_TRUTH.md` + `docs/PRON_LORA_LONG.md`
  (the canonical run hub). Softened to name the hub and scope this file to build
  decisions. Authority: `SOURCE_OF_TRUTH.md:15`.
- **`docs/README.md` index gap** (its own rule: "must list every live runbook"):
  added a row for `PRON_LORA_LONG_PLAN.md`; added `L4_HANDOFF_TASK14C.md` to the
  not-a-runbook/history note (it is banner-marked *Historical 2026-09-27*).
- **`docs/E2E_TESTING_PLAN.md` §8**: the doc is now `complete`, but §8 was titled
  "proposals" and its tree listed a `tests/fixtures/gpu/` Tier B dir. Retitled
  "as landed" and dropped `gpu/` — Session 4 folded the 1 Hz `_gpu.csv` into Tier A
  (small text, `tests/fixtures/inference/…_gpu.csv`); no such dir exists.
  Authority: the on-disk `tests/fixtures/` tree + `tests/fixtures/README.md`.
- **`unverifiable.txt`**: pruned the four E2E suppressions that now match no claim
  and resolve on disk (`tests/fixtures/{loss_log.spec.json,inference,training,gpu}`);
  rewrote the now-false "later sessions will create …" comment. Curations that are
  still live (bare filenames the extractor cannot map into `tests/`) kept.
- **Graph refreshed** (free AST tier): `graphify update .` rebuilt **1275 nodes /
  2457 edges / 91 communities** at HEAD `9bc008f` (was `5ca4c71`, 17 commits behind
  — `status.py` flagged it); backup written to `graphify-out/2026-09-30/`. Code/AST
  only; doc/semantic edges still need `/graphify --update` (pre-merge tier).
- Re-verify after the edits: 2168 claims / 49 files, 1324 checkable, **0 flagged
  (0.0 %)**.
- Authority: user-approved reconciliation per `skills/docs-reconciler/SKILL.md`
  (live docs only); no run config, hyperparameter, or script behaviour changed; no
  frozen doc rewritten (`DECISIONS.md`/`PROGRESS.md`/`IMPROVEMENTS.md` untouched).

## 2026-09-30 — graphify: untrack the extraction cache (multi-VM policy)

- **Decision (user-approved).** `graphify-out/cache/` is now git-ignored and
  untracked (`git rm -r --cached`); the graph outputs (`graph.json`,
  `GRAPH_REPORT.md`, `graph.html`, `manifest.json`, `.graphify_labels.json`) stay
  committed. Rationale: the cache is keyed by graphify version, and VMs run
  different versions (this one 0.9.70 vs the committed `v0.9.71-s4`), so every
  refresh replaced the whole directory — 189 tracked files churned + cross-branch
  conflict risk for zero map benefit. The cache is AST-only (no LLM), so a fresh
  VM rebuilds it free on first `graphify update`.
- Docs: `.gitignore` comment + `graphify-out/cache/`; `docs/GRAPHIFY.md` (table
  row, refresh note, caveat 2) and `DECISIONS.md` (new "Knowledge graph" section)
  document the split. Also corrected the stale `GRAPHIFY.md` "built at `9c03b20`,
  branch `pron-lora-ar-only`" line to `9bc008f` / `music-cover`.
- Authority: user decision (multi-VM workflow; graphify is agent-facing); no run
  config or hyperparameter changed.

## 2026-09-30 — SheetSage2 audio→ABC CPU feasibility recorded

- New **§2.1** in `docs/music-cover-feasibility.md` records the measured CPU feasibility of
  the B2 transcription step (SheetSage2 `melody_only` audio→ABC): Colab High-RAM **CPU**
  runtime (8 cores / 50 GiB, no GPU). `RESULT song60`: 93.3 s / 3.74 GB; `RESULT
  sample_song` (316.6 s): 235.5 s / 4.31 GB; plus thread scaling (8/4/2/1) and the 2-thread
  full file (347.6 s / 4.30 GB). Verdict: viable for one ≤10-min track even on the free
  2-vCPU / 12 GB tier. The §2 "chosen transcription route" bullet now points to §2.1 instead
  of leaving CPU feasibility unmeasured; header revision bumped to 2026-09-30.
- New record dir `results/ss2_cpu_probe/` (README + the three raw probe logs), mirroring the
  `results/pron_*` layout; added a **results index** to `results/README.md` (it previously
  had none) listing the record dirs.
- `agent_notes/current.md` reduced to a pointer to §2.1 + the results dir, no numbers.
- `SOURCE_OF_TRUTH.md`: new row for the SheetSage2 CPU-feasibility topic; `docs/README.md`
  blurb now names §2.1.
- Reconciler: 2193 claims / 50 files, 1334 checkable, **0 flagged (0.0%)**.
- Authority: the probe logs (`results/ss2_cpu_probe/*.log`); no run config, hyperparameter,
  or script behaviour changed; no frozen doc rewritten.

## 2026-09-30 — cover/rescue workflow & economics recorded (§10)

- `docs/music-cover-feasibility.md`: new **§10 "Rescue workflow & economics (B2 on CPU)"** —
  turns the §2.1 CPU-viability fact into the revised GPU/CPU split (pass-1 v2 `cot=off` on
  GPU → B2 transcription on a **free CPU** runtime → selective `qfinal cot=melody` rescue on
  GPU), with a GPU-minute cost table (N=12 / M=5: 110 vs 143 on B1 vs 156 guide-all) and the
  B2-still-unrun caveat + mandatory 1-track smoke. §4.2 B2 bullet now cites §2.1/§10; §8
  B1-vs-B2 item notes it gates the flow; header revision line updated; former §10 Sources
  renumbered to §11.
- `SOURCE_OF_TRUTH.md`: new row for the cover/rescue workflow-split topic, **marked a plan,
  not measured** (B2 unrun).
- `docs/README.md`: investigation-record blurb now names §10.
- Reconciler: 2198 claims / 50 files, 1339 checkable, **0 flagged (0.0%)**.
- Authority: the §2.1 probe (`results/ss2_cpu_probe/`) + `docs/GPU_L4_VS_A100.md` unit rates
  + `docs/INFERENCE.md` T4 timing; the cost model is a plan — no run config, hyperparameter,
  or script changed; no frozen doc rewritten.

## 2026-09-30 — rescue workflow implemented (runbook + guarded driver + pass-1 manifest)

- New runbook **`docs/PRON_LORA_RESCUE.md`**: the B2 test flow (pass-1 v2 → SheetSage2 ABC on
  free CPU → listen → qfinal `cot=melody` rescue), the `<name>_<seed>` alignment spine, and the
  gate table (G0–G6). Indexed in `docs/README.md`.
- New driver **`INFERENCE/rescue_abc_batch.sh`**: calls the binary **directly** with
  `cot=melody` + `abc_file` (bypasses `run_one.sh:85`'s hardcoded `cot=off`, whose later
  override is unverified); refuses `--out-dir == pass-1 dir` (would clobber the liked take);
  builds `_rescue_index.json` (sha256 of each pass-1 WAV + its ABC) and aborts if any is
  missing; `--plan`/`--verify`/`--smoke`/`--songs-file`. Verified locally against a synthetic
  fixture: plan, refuse, missing-abc abort, and tamper-detecting `--verify` all behave.
- New **`manifests/batch_12_rock_v2.json`** (generated from `batch_12_rock.json`, every `lora`
  → `v2`; original kept as authored). Validated with `generate.py --dry-run` (12 songs, 12
  tracks, ~78 min T4).
- `SOURCE_OF_TRUTH.md`: row for the rescue procedure; `agent_notes/current.md`: pointer updated.
- Reconciler: 2321 claims / 51 files → 5 missing-path + 1 unknown-flag, all from the new
  runbook's **runtime artifacts** (`_rescue_index.json`, `_rescue.json`, `_rescue_status.log`,
  `_driver.log`) and a quoted `git clone --branch`. Curated (doc-scoped) in
  `skills/docs-reconciler/references/unverifiable.txt` → 1438 checkable, **0 flagged**.
- Authority: `docs/music-cover-feasibility.md` §2.1/§10 + `INFERENCE/generate.py`,
  `sheetsage2_transcribe.py`, `run_one.sh` (read for the guards). No run config or
  hyperparameter changed.
