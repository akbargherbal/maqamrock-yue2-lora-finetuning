# GCS organization plan — OSTRIS project (non-breaking)

_Status: **decisions taken; Phase 0 + part of Phase 1/2 implemented 2026-09-29** — §11 lists
exactly what changed. **Nothing has been deleted**: every old path is still present and is still
the source. Authority for how the backup works today stays with `docs/BACKUP_RESTORE.md`; this
document changes the layout, not the mechanism._

**Scope: strictly `gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/` and nothing
above it.** This plan reorganizes only what is *inside* that prefix. The prefix name itself is
fixed — renaming it would touch the level above, which is out of scope by decision (2026-09-29).

## 1. Why this document exists

Each session re-derives where things are. The prefix root is a flat pile in which datasets,
training runs, the curated LoRA library, tooling, evaluation output and dead weight are all
siblings, and the same concept often lives in two or three places. There is already a symptom
artifact: `audiocpp_inference/WHERE_ARE_THE_KURD_WAVS.txt` — somebody had to leave a breadcrumb
because the files could not be found. The goal is a layout with **named sections**, where the
location of a thing follows from what kind of thing it is — without breaking any reader.

## 2. What is actually there (evidence)

Read-only, run 2026-09-29, all paths inside the project prefix:

```bash
P=gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning
gsutil ls "$P/"                       # the prefix root: 22 entries
gsutil ls "$P/audiocpp_inference/"
gsutil ls "$P/audiocpp_inference/out/"
```

### 2.1 Everything is a sibling of everything

The prefix root has no grouping: 18 directories and 4 loose files, distinguished from one
another only by name. Datasets (`dataset/`, `pron_dataset/`, `quran_long_aya_dataset/`,
`quran_long_aya_dataset_s10/`), training runs (`akbar_arabic_rock_lora/`, `pron_alpha_sweep/`,
`pron_fine_sweep/`, `pron_production_merge/`, `quran_long_aya_r8/`, `quran_long_aya_r8_s10/`),
the curated library (`loras/`), evaluation packages (`listening/`,
`PRON_FINE_SWEEP_EVAL_INPUT/`), tooling (`audiocpp_inference/`) and dead weight (`archive/`,
`repo_bundles/`, `*_obsolete/`, `*_archived/`) all sit at the same level.

### 2.2 Our prefix root — 22 entries, no taxonomy

```
PRON_FINE_SWEEP_EVAL_INPUT.zip          quran_long_aya_dataset_s10.tar
quran_long_aya_dataset_s10.tar.sha256   quran_long_aya_s10_manifest.json
PRON_FINE_SWEEP_EVAL_INPUT/  akbar_arabic_rock_lora/
akbar_arabic_rock_lora_smoketest_archived/  archive/  audiocpp_inference/
dataset/  listening/  loras/
pron_alpha_sweep/  pron_dataset/  pron_fine_sweep/
pron_lora_ar_only_r8_obsolete/  pron_production_merge/
quran_long_aya_dataset/  quran_long_aya_dataset_s10/
quran_long_aya_r8/  quran_long_aya_r8_s10/  repo_bundles/
```

### 2.3 `audiocpp_inference/` — a workspace acting as a run dir

```
WHERE_ARE_THE_KURD_WAVS.txt  run_manifest.json
agent_notes/  build/  converter/  logs/  prompts/  scripts/     ← pinned tooling (setup.sh pulls these)
maqam_lyric_swap/  pron_ckpt_sweep/  pron_fine_sweep/  pron_grid_kurd/
pron_knob_probe/  pron_t08_alpha/  pron_t10_alpha/  quran_eval/  ← evaluation output
out/  out_archive/                                              ← every run ever, plus a second archive
```

`out/` itself: `latest`, `20260922-1337_random16/`, `20260923-071255_batch_songs_23092026/`,
`abc_v2/`, `batch_36_songs/`, `qfinal_suno_sweep/`, `screen_semantic/`, `sheetsage2_abc/`,
`ss2_smoke/`, `ss2_smoke2/`, `style_ablation_ajam/`.

### 2.4 Sizes and object counts — the migration currency

Read-only (`gsutil -m du -s`, `gsutil ls -r`), taken 2026-09-29T08:42Z:

| prefix | size | objects | note |
|---|---:|---:|---|
| `quran_long_aya_dataset/` | **30.1 GB** | **162,746** | **93% of all objects** |
| `audiocpp_inference/` | 9.41 GB | 1,561 | workspace + pinned tooling, mixed |
| `archive/` | 4.26 GB | 117 | legacy |
| `akbar_arabic_rock_lora/` | 1.75 GB | 150 | the v2 training run |
| `dataset/` | 1.54 GB | 534 | 267 mp3 + 267 txt |
| `pron_alpha_sweep/` | 1.34 GB | 66 | |
| `pron_dataset/` | 1.07 GB | 12,592 | 6,296 mp3 + pairs |
| `loras/` | 606 MB | 7 | curated library |
| `quran_long_aya_dataset_s10/` | 568 MB | 1 | a single tar |
| `pron_fine_sweep/` | 508 MB | 39 | |
| `pron_production_merge/` | 441 MB | 3 | |
| `quran_long_aya_r8_s10/` | 165 MB | 36 | |
| `listening/` | 126 MB | 28 | eval packages |
| `repo_bundles/` | 84 MB | 1 | |
| `pron_lora_ar_only_r8_obsolete/` | 84 MB | 40 | legacy |
| `quran_long_aya_r8/` | 51 MB | 23 | |
| `PRON_FINE_SWEEP_EVAL_INPUT/` | 41 MB | 10 | |
| `akbar_arabic_rock_lora_smoketest_archived/` | 17 MB | 13 | legacy |
| **total** | **≈52 GB** | **≈178,000** | |

**The decisive number:** `quran_long_aya_dataset/` alone is 93% of the objects. Migrating it means
a 30 GB copy *plus* a 162,746-object integrity check — a long listing on both sides, a real
interruption risk, and non-trivial GCS operation cost — all to buy a path rename. **Excluding it,
everything else is ≈22 GB / ≈15,000 objects**, which migrates in minutes. That is the whole basis
of the §9.2 recommendation: freeze that one dataset in place, document it, and migrate the rest.


## 3. Diagnosis — five concrete problems

1. **No taxonomy.** Datasets, training runs, the LoRA library, tooling, evals and dead weight
   are all siblings under one prefix, distinguished only by name.
2. **The same concept lives in 2–3 places.** `pron_fine_sweep/` exists at the root *and* under
   `audiocpp_inference/`; `logs/` and `agent_notes/` exist under both `<run>/` and
   `audiocpp_inference/`; there are four ways to say "old": `archive/`,
   `audiocpp_inference/out_archive/`, `*_obsolete/`, `*_archived/`.
3. **Colliding naming conventions.** `snake_case` for most things, `SCREAMING_CASE` for
   `PRON_FINE_SWEEP_EVAL_INPUT`/`.zip`, and loose `.tar`/`.zip` blobs sitting beside directories.
4. **A workspace prefix doubles as a run.** `audiocpp_inference/` mixes *pinned, re-staged*
   tooling with *accumulating* run output, so `out/` has no lifecycle and never gets pruned.
5. **Not machine-readable.** The layout exists only as prose in docs and literals in scripts, so
   every session re-derives it — and drifts.

## 4. The hard constraint that shapes everything

**GCS has no rename and no symlinks.** "Moving" a prefix means copy + delete. Therefore:

- there is no atomic cutover — for the duration of a move, readers of the old path and the new
  path see different things;
- `gsutil rsync` **without `-d` never deletes**, so a half-finished migration leaves silent
  duplicates rather than an error;
- any deletion is irreversible except by restoring from the other copy.

**Design rule: additive first. Add the new layout, switch the writers, copy with verification,
and delete only in a separate gated phase.** Nothing is ever deleted in the same step that
creates its replacement.

## 5. Reader map — the thing that makes this non-breaking

Every path that a non-document reader depends on. This is the complete blast radius; if a
change is not in this table, it cannot break a reader.

| reader | reads/writes | path (relative to `<base>`) | how it gets there |
|---|---|---|---|
| `backup_to_gcp.py` (`--inference`) | **writes** | `audiocpp_inference/{out,prompts,scripts,logs,agent_notes}` | `INFERENCE_TARGETS` constant (lines ~152-158) |
| `backup_to_gcp.py` (training) | **writes** | `<run-name>/{output,logs,agent_notes}` | `TRAINING_TARGETS`; run name from `--run-name`/config |
| `backup_to_gcp.py` | root | — | `DEFAULT_BASE = os.environ["GCP_BACKUP_BASE"]` (line 84); `--base` overrides |
| `bootstrap/setup.sh` | **reads** | `loras/audio_cpp/style` | literal (line 120) |
| `bootstrap/setup.sh` | **reads** | `audiocpp_inference/converter` | literal (line 121) |
| `bootstrap/setup.sh` | **reads** | `audiocpp_inference/build/audiocpp_cli` | literal (line 122) |
| `bootstrap/setup.sh` | **reads** | `audiocpp_inference/prompts`, `.../scripts` | literals (lines 123-124) |
| `bootstrap/setup.sh` | **reads** | `$GCP_DATASET_PATH`, `$GCP_PRON_DATASET_PATH`, `$GCP_QURAN_LONG_DATASET_PATH` | env, not literals (lines 99, 249, 270) |
| `status.py` | **reads** | base for drift | `GCP_BACKUP_BASE` (line 241) |
| launching notebook | sets | the three dataset env vars + `GCP_BACKUP_BASE` | `notebooks/L4_QPRON_ArabicSuno_vscode_anywhere.ipynb` |
| `prepare_pron_dataset.py` | references | `quran_long_aya_dataset/` | docstring only |
| docs / `user_cheatsheet.md` / `skills/` / `results/*.json` | prose+literals | ~25 occurrences | see §2 commands' grep |
| `generate.py` | writes | `out/latest` pointer + `out/<ts>_<label>/` | inside the workspace |

**The good news:** the base is env-driven and the sub-layout is 5 literals in `setup.sh` plus 1
constant in `backup_to_gcp.py`. The dataset paths are already indirection (`$GCP_*`), so moving
those is a notebook + docs edit, not a logic change.

## 6. Target layout

Seven named sections, one per *kind* of thing. Names are lowercase `snake_case`; every section
has one job and one lifecycle.

```
OSTRIS_Arabic_Suno_Finetuning/
  README.txt                 # what this prefix is; points at LAYOUT.json
  LAYOUT.json                # machine-readable: logical name -> path, state, owner
  datasets/                  # IMMUTABLE inputs
    v2_style_267/            <- dataset/                     (267 mp3+txt; the LoRA's training data)
    pron/                    <- pron_dataset/                (6,296 mp3)
    quran_long_aya/          <- quran_long_aya_dataset/      (81,372 mp3)  [decision pending, §9]
    quran_long_aya_s10/      <- quran_long_aya_dataset_s10/ + the .tar, .sha256, manifest
  runs/                      # APPEND-ONLY training runs
    style_v2/                <- akbar_arabic_rock_lora/
    pron_alpha_sweep/        <- pron_alpha_sweep/
    pron_fine_sweep/         <- pron_fine_sweep/            (root copy; the audiocpp one is eval output)
    pron_production_merge/   <- pron_production_merge/
    quran_long_aya_r8/       <- quran_long_aya_r8/
    quran_long_aya_r8_s10/   <- quran_long_aya_r8_s10/
  loras/                     # CURATED adapter library (name unchanged - already canonical)
    audio_cpp/{style,pron}/...
  tools/                     # PINNED, re-staged by setup.sh; never accumulates
    audiocpp/{build,converter,prompts,scripts,run_manifest.json}   <- audiocpp_inference/*
  evals/                     # LISTENING packages + eval output
    listening/               <- listening/
    audiocpp/                <- audiocpp_inference/{pron_ckpt_sweep,pron_fine_sweep,
                                                  pron_grid_kurd,pron_knob_probe,
                                                  pron_t08_alpha,pron_t10_alpha,
                                                  maqam_lyric_swap,quran_eval}
    packs/                   <- PRON_FINE_SWEEP_EVAL_INPUT/ (+ .zip)
  workspace/                 # EPHEMERAL working output: prunable, regenerable
    audiocpp/out/            <- audiocpp_inference/out/
    audiocpp/out_archive/    <- audiocpp_inference/out_archive/
    audiocpp/logs/           <- audiocpp_inference/logs/
    audiocpp/agent_notes/    <- audiocpp_inference/agent_notes/
  _legacy/                   # FROZEN: pointers + RETIRED.txt; nothing reads from here
    archive/                 <- archive/
    repo_bundles/            <- repo_bundles/
    smoketest_archived/      <- akbar_arabic_rock_lora_smoketest_archived/
    ar_only_r8_obsolete/     <- pron_lora_ar_only_r8_obsolete/
```

Two rules the layout encodes: **`tools/` never grows** (re-staged each VM), and **`workspace/`
is safe to prune** (nothing there is precious — if it were, it belongs in `runs/` or `evals/`).

## 7. Migration procedure — phased, reversible, gated

### Phase 0 — inventory and freeze (safe, no writes to the layout)
1. Re-run the inventory (§2) on this VM; save it to the repo, not `/tmp`:
   `python3 -c ...` / the script → `results/gcs_inventory_20260929.txt`.
2. Write `<base>/README.txt` and `<base>/LAYOUT.json` describing **current** state and this plan.
   Pure additions; nothing reads them yet, so they cannot break anything.
3. **Stop the writer**: `pkill -f 'backup_to_gcp[.]py'` (it refuses to run without a base, but it
   is currently mirroring old paths — do not let it write mid-migration).
4. Confirm nothing else is writing: no training run, no inference batch.

### Phase 1 — add new layout, switch writers (no moves yet)
5. `mkdir` the new sections (empty prefixes are free).
6. Update the **writers** to the new paths, with a one-cycle **read fallback**:
   `backup_to_gcp.py` → `workspace/audiocpp/{...}` and `runs/<run>/…`; `setup.sh` → `tools/audiocpp/…`
   and `loras/…`. Fallback = "if the new path is empty, use the old one", so either layout works
   during the transition.
7. Rehearse end-to-end **against a throwaway base**, never the real one:
   `python3 backup_to_gcp.py --inference --base gs://akbar-december-2024-backup/OSTRIS_layouttest --once`
   then `bash bootstrap/setup.sh --inference` with the test base. Delete the test prefix after.

### Phase 2 — copy, then verify
8. Per prefix, copy only (never `-d`): `gsutil -m rsync -r <old> <new>`.
9. Verify, and require **all three** before proceeding:
   - object count: `gsutil ls -r <old>/** | grep -vc '/$'` == same for `<new>`
   - integrity: `gsutil ls -L -r <old>/**` vs `<new>` — compare the `crc32c` values as sets
   - spot size: `gsutil -m du -s <old>/**` vs `<new>`
10. Do **one prefix at a time**, cheapest first (`listening/`, `pron_fine_sweep/`, `tools/`), and
    leave the 81k-object dataset last (§9).

### Phase 3 — retire (separately gated)
11. Delete the old prefix **only after the new path has served at least one real session**
    (setup + a generation + a backup pass). `gsutil -m rm -r <old>`.
12. Record it in `<base>/_legacy/RETIRED.txt`: what was deleted, when, the new path, and how to
    restore (copy back from the new path). Keep the old path documented in `LAYOUT.json` as
    `"state": "moved"` with its former name.

### Phase 4 — guardrails so it cannot drift again
13. `INFERENCE/gcs_layout.py` (or repo root): a resolver — `resolve("datasets.pron")` → the path —
    read from `LAYOUT.json`. Scripts ask it instead of hardcoding.
14. A CPU test that fails if a non-doc file contains a literal
    `gs://…/OSTRIS_Arabic_Suno_Finetuning/` outside the resolver/whitelist. This is the mechanism
    that makes the organization stick; without it the pile regrows.
15. `docs/README.md` gains the section map; run `docs-reconciler` and log it in
    `RECONCILIATION_LOG.md` (§12 of `AGENTS.md`).

## 8. What must NOT be touched (inside the prefix)

- **Nothing outside `OSTRIS_Arabic_Suno_Finetuning/`** — by decision, out of scope entirely.
- **`loras/` internals** — the documented canonical library, curated by hand
  (`docs/LORA_INVENTORY.md`). Renaming the *section* would be fine; reorganising its contents is a
  separate decision.
- **Anything a live process is writing to.** At the time of writing that was
  `audiocpp_inference/out/screen_semantic/` (the semantic screen) and the backup daemon.
- **Self-referential pointers** — `audiocpp_inference/out/latest` and
  `<base>/audiocpp_inference/run_manifest.json` point *at* other paths. If their targets move, the
  pointer must be rewritten in the same step, or it silently points at nothing.
- **`quran_long_aya_dataset/`** — freeze, do not move, unless §9.2 is explicitly answered
  "migrate". 162,746 objects is the single largest regression risk in this plan.

## 9. Decisions — settled 2026-09-29 (no longer open)

1. **`quran_long_aya_dataset/` — FROZEN, not migrated.** 162,746 objects / 30.1 GB = 93% of the
   prefix. It is *documented* instead (`<prefix>/README.txt`, `LAYOUT.json`), which fixes
   "I can't find it" without a 30 GB copy and a 162,746-object verification.
2. **`backup_to_gcp.py` — MAY change its write paths.** Done: `INFERENCE_TARGETS` now writes
   `workspace/out` + `tools/prompts` + `tools/scripts` (with `logs` and `agent_notes`
   unchanged). **Local sources are untouched**, so no local tool changes.
3. **`audiocpp_inference/` — sectioned *in place*** (`tools/`, `workspace/`, `evals/`) rather
   than split out to the prefix root: zero doc churn, and it keeps the workspace self-contained.
4. **Prefix name — fixed.** Not a decision: renaming it would touch the level above, which is
   out of scope.


## 10. Recommended immediate step (safe, today, additive only)

Do Phase 0 only: write `<base>/README.txt` + `<base>/LAYOUT.json` recording the current state and
this plan, and commit the inventory into `results/`. That is three additive operations, breaks
nothing, and converts the layout from tribal knowledge into a machine-readable fact — which is
the precondition for every later phase. The actual moving can then happen in a session where no
GPU work is in flight.

## 11. Implementation log — 2026-09-29

Done in one session, on branch `music-cover`, GPU free, backup daemon stopped for the duration.

**Phase 0 — documentation (additive, nothing read them before)**
- Uploaded `<base>/README.txt` and `<base>/LAYOUT.json` (project map; records the `datasets/`,
  `runs/`, `evals/`, `_legacy/` plan and the **frozen** `quran_long_aya_dataset/`).
- Uploaded `<base>/audiocpp_inference/README.txt` and `.../LAYOUT.json` (the sections, the
  lifecycle of each, and the list of legacy flat paths still present).

**Phase 1 — the whole `audiocpp_inference/` reorganisation (code)**
- `backup_to_gcp.py` — `INFERENCE_TARGETS` now writes `workspace/out`, `tools/prompts`,
  `tools/scripts` (`logs`, `agent_notes` unchanged); docstring updated. **Local sources
  unchanged.**
- `bootstrap/setup.sh` — the four pull paths now probe `audiocpp_inference/tools/` and **fall
  back** to the flat layout when it is absent, so a VM boots during the transition.
- `INFERENCE/pron_knob_probe.sh` — the staging hint now points at `evals/maqam_lyric_swap/`.
- `tests/test_backup_to_gcp.py` — **added** `test_inference_targets_are_sectioned`, which pins the
  real `INFERENCE_TARGETS` subfolders *and* asserts the local sources are unchanged. Every other
  inference test monkeypatches the constant, so without this the layout could drift unnoticed.
- `docs/BACKUP_RESTORE.md`, `docs/INFERENCE.md` — paths corrected.
- `python3 -m pytest tests/test_backup_to_gcp.py` → **42 passed**.

**Phase 2 — copy + verify (data)**
- Copied (never moved) the 14 pieces: `prompts`, `scripts`, `build`, `converter` → `tools/`;
  `out`, `out_archive` → `workspace/`; the 8 sweep dirs → `evals/`.
- Verification, all three axes, **14/14 MATCH / 0 mismatches** — object count, total bytes, and a
  CRC32C multiset comparison per pair (log: `/content/logs/verify_sections.log`).
- Daemon restarted and confirmed writing the new paths (its log now shows
  `out -> …/audiocpp_inference/workspace/out` etc., and it rewrote `run_manifest.json`).

**Still to do**
1. **Phase 3 — retire the flat paths.** Not done, deliberately: they are the rollback. Delete only
   after the sectioned paths have served a real session.
2. The prefix-level sections (`datasets/`, `runs/`, `evals/`, `_legacy/`) are still *planned* —
   only `audiocpp_inference/` was reorganised.
3. `docs-reconciler` + a `RECONCILIATION_LOG.md` entry for the doc edits above (§12 of
   `AGENTS.md`) — **not yet run**.

