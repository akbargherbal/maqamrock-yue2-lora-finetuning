# agent_notes / current

**Date:** 2026-09-27 · **State:** Phases 1 + 1.5 + DECISIONS condensation **done and pushed** (`a9112ef` on `origin/pron-lora-long`). Next: **Phase 3** — ff-merge to `main` + tag `v0.9.0-beta`. No run active. Local machine, not Colab.

**Next action (yours) — Phase 3 (fast-forward + tag):**
```bash
cd /home/akbar/Jupyter_Notebooks/OpenCode/ostris_prepare_dataset/maqamrock-yue2-lora-finetuning
git checkout main
git pull --ff-only origin main
git merge --ff-only origin/pron-lora-long
git tag -a v0.9.0-beta -m "BETA: v2 style LoRA + long-aya Quran pronunciation merges (unselected candidates) + audio.cpp inference pipeline"
git push origin main v0.9.0-beta
```
Then Phase 4 (below): branches stay frozen; verify.
(qfinal Suno/trigger sweep still awaiting your go-ahead — commands preserved at the bottom.)

---

# Merge-to-main plan (BETA) — decisions locked

## Locked decisions (this session)

| # | Decision |
|---|---|
| 1 | **Knobs doc stays on its branch.** `docs/investigation_generation_knobs.md` is NOT folded; `pron-lora-knobs-investigation` stays unmerged. |
| 2 | **α = candidates.** No winner named in README/PROGRESS; labels stay descriptors ("unlistened candidate"), per `docs/LORA_INVENTORY.md`. |
| 3 | **The `pron_lora_ar_only_r8` donor family is superseded by the long-aya Quran donor.** The current-line pronunciation candidates are the **qfinal** merges (v2 style + `quran_long_aya_r8_s10` final), α 0.3 / 0.5. The `c3050/c4575/cfinal` grid is legacy. |
| 4 | **Release mechanics** (my recommendation): annotated tag `v0.9.0-beta`, atomic with the merge. |
| 5 | **No branch deletion.** Keep all three branches as frozen archives (see rationale). |

## Ground truth (verified 2026-09-27, git + local gsutil)

- `origin/main` @ `91df00e` is an **ancestor** of `origin/pron-lora-long` @ `39d1bbd`
  → the merge is a **fast-forward: 76 commits, zero conflicts.**
- `pron-lora-ar-only` @ `d6bb283` is fully contained in `pron-lora-long` → nothing to carry.
- `pron-lora-knobs-investigation` @ `4ed26a9` is the only branch with unique commits
  (53 behind / 4 ahead); folded-in? **No** (decision 1).
- Local: `gsutil`/`gcloud` present, **`gh` absent** → no CLI PR; merge = local git + `git push`
  (PAT via `bootstrap/github_auth.sh`). No tags exist yet.

## Why keep the branches (decision 5)

Zero cost, and only one of them is actually unique:
- `main` will contain **every commit** of `pron-lora-long` and `pron-lora-ar-only` after the ff →
  deleting them loses nothing, but deleting them also gains nothing.
- `pron-lora-knobs-investigation` holds 4 commits `main` will never have (the knobs doc).
  Keeping it is the safe default.
- If you ever want them gone anyway, the tag makes recovery trivial: `git branch pron-lora-long <tag>`.
  No need to decide now.

## Supersede rename — repo ⇄ GCS in lockstep — **EXECUTED 2026-09-27 (verified)**

**GCS moves done (md5-verified, old prefixes empty):** 15 legacy merges + 3 source pins →
`archive/pron_lora_ar_only_legacy/…`; run prefix `pron_lora_ar_only_r8/` →
`pron_lora_ar_only_r8_obsolete/`. `loras/audio_cpp/pron/` now holds only the 2 `qfinal_a*`.
**Repo updated same pass:** `docs/LORA_INVENTORY.md` (library = style + qfinal; legacy table
moved under Superseded), `docs/INFERENCE.md`, `docs/PRON_LORA_MERGE.md` (+ banners on
`docs/PRON_LORA.md`, `docs/PRON_LORA_SWEEP.md`, `docs/PRON_LORA_VERIFICATION.md`,
`docs/L4_HANDOFF_TASK14C.md`), `bootstrap/setup.sh` comment, `SOURCE_OF_TRUTH.md`,
`DECISIONS.md` (new entry).

Final GCS state (verified by md5 multiset before/after):
- Library: `loras/audio_cpp/pron/` = {`qfinal_a0.3`, `qfinal_a0.5`}; `loras/audio_cpp/style/` untouched; `loras/source/` = v2 style only.
- Archive: `archive/pron_lora_ar_only_legacy/loras/audio_cpp/pron/` (15 dirs / 30 files) + `.../loras/source/` (3 pins).
- Run: `pron_lora_ar_only_r8_obsolete/` (40 objects / 80.0 MiB).
- Not moved (run records, not the deployable set): `pron_dataset/`, `pron_alpha_sweep/`, `pron_fine_sweep/`, `pron_production_merge/`, `listening/PRON_*`.

## Corrections the rewrite MUST make (found 2026-09-27 via local `gsutil`)

- README claims the v1 run + dataset are archived in GCS (`…_v1_nolyrics_archived`, 185 objects;
  `dataset_v1_style_only_obsolete/`). **Verified ABSENT** from the project prefix — `archive/`
  holds only `alpha_gt_0.5/`. There is **no surviving v1 adapter**. Stop claiming it.
- README says the pron LoRA is "researched but **not scheduled**" — it was built (6100/6100),
  replayed (720 AR-loss passes), merged, swept; then the donor moved to long-aya Quran (qfinal).
- `docs/FUTURE_PRONUNCIATION_LORA.md` is a realized idea → superseded banner.
- Docs that tell a fresh VM to `git checkout <branch>` to get files now on `main` must be
  de-branched (else they're false after the merge): `docs/PRON_LORA.md:46`,
  `docs/L4_HANDOFF_TASK14C.md:5,29,73`, `docs/PRON_LORA_LONG.md` (several),
  `docs/PRON_LORA_LONG_PLAN.md`, `notebooks/L4_QPRON_*.ipynb` (`pron-lora-long` / `pron-lora-ar-only`).
  Historical mentions (`docs/GRAPHIFY.md:22`, `DECISIONS.md:267,339`, `.gitignore:15`) can stay.

## Phase 1 — doc rewrite ON `pron-lora-long` — **DONE (uncommitted)**

> **`DECISIONS.md` also condensed this pass:** 46 headings / 370 lines → **11 sections / 88 lines**, grouped
> by topic; every binding rule/trap kept, narrative folded to outcomes. Baseline in its header
> (`git show 39d1bbd:DECISIONS.md`); citation `INFERENCE/suno_to_songs.py:18` re-pointed to `DECISIONS.md:25`.
> Recorded in `RECONCILIATION_LOG.md`.

- `PROGRESS.md` → restructure (don't delete): **numbered milestones**, one block each
  (what / when / evidence pointer). History stays in git — record the pre-rewrite baseline
  in the header (`git show 39d1bbd:PROGRESS.md`). Spine:
  1. v1 dataset built + independently verified (267 pairs); bootstrap validated on a fresh L4
  2. v1 run 3000/3000 (A100) — style strong, pronunciation degraded → root cause: captions had no lyrics
  3. v2 dataset (lyric-conditioned) built, verified, promoted; held-out eval set; lyric training samples
  4. v2 run 3000/3000 — pronunciation ~9/10
  5. audio.cpp GGUF+LoRA inference harness (`run_one.sh`, `generate.py`), T4/L4 benchmarks
  6. AR-only pron LoRA (6100/6100) + offline AR-loss replay — **now a legacy donor (decision 3)**
  7. merge tool (`merge_pron_lora.py`) + α/ckpt sweeps + blinded listening packages + LoRA library
  8. long-aya Quran LoRA (`quran_long_aya_r8_s10`, 8100/8100) → **current pron donor**; qfinal merges
  9. operability: `train_ctl.py`, 5-min backups, vm-continuity session recovery, docs reconciliation
  10. BETA: repo consolidated onto `main`
- `README.md` → statement of record: what the project is; BETA; deliverables = v2 style LoRA +
  long-aya Quran pronunciation donors merged as **unselected candidates** (α 0.3/0.5); layout;
  quickstart; docs map. Kill both false claims above.
- `docs/LORA_INVENTORY.md`: mark the `pron_lora_ar_only_r8` family as **legacy donor** (superseded by
  long-aya), current candidates = `qfinal_a0.3`/`qfinal_a0.5`. Keep the hash table as history.
- `SOURCE_OF_TRUTH.md`: split the "History / outcomes" row → `PROGRESS.md` = milestones; history = git.
- `docs/README.md` index wording; `AGENTS.md` "milestone trail" line aligns.
- `RECONCILIATION_LOG.md`: one entry (authority = user-approved consolidation; frozen-doc exemption
  for PROGRESS, as in the 2026-09-23 pass).
- De-branch the fresh-VM docs + notebooks (list above).
- Then: `graphify update .` → `docs-reconciler` pass → `python -m pytest -q` (must stay green).

## Phase 1.5 — the supersede rename, repo + GCS in lockstep — **DONE**

```bash
B=gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning
# 1) library: legacy 15 dirs -> archive (original paths preserved)
gsutil -m mv -r "$B/loras/audio_cpp/pron/c3050_a0.1" ... "$B/archive/pron_lora_ar_only_legacy/loras/audio_cpp/pron/"
# 2) source pins
gsutil -m mv "$B/loras/source/pron_lora_ar_only_r8.safetensors" \
             "$B/loras/source/pron_lora_ar_only_r8_000003050.safetensors" \
             "$B/loras/source/pron_lora_ar_only_r8_000004575.safetensors" \
             "$B/archive/pron_lora_ar_only_legacy/loras/source/"
# 3) run prefix
gsutil -m mv -r "$B/pron_lora_ar_only_r8/" "$B/pron_lora_ar_only_r8_obsolete/"
# 4) verify: 0 objects left at the old paths; counts + md5 match the pre-move listing
```
Then the repo refs in the same commit; `pytest` green.

## Phase 2 — skipped (knobs stays on its branch)

## Phase 3 — the merge (fast-forward) + tag

```bash
cd /home/akbar/Jupyter_Notebooks/OpenCode/ostris_prepare_dataset/maqamrock-yue2-lora-finetuning
git push origin pron-lora-long                      # Phase 1 commits

git checkout main
git pull --ff-only origin main
git merge --ff-only origin/pron-lora-long           # no conflicts possible (ancestor)
git tag -a v0.9.0-beta -m "BETA: v2 style LoRA + long-aya Quran pronunciation merges (unselected candidates) + audio.cpp inference pipeline"
git push origin main v0.9.0-beta                    # PAT: bash bootstrap/github_auth.sh first
```

## Phase 4 — freeze branches (do NOT delete)

```bash
# nothing to do — all three branches stay as-is. main now supersedes long/ar-only;
# knobs stays the only place with unique commits. Retrieval if ever needed:
#   git branch <name> v0.9.0-beta
```

## Phase 5 — post-merge verify

- `git log --oneline -1 origin/main` == the tag commit; GitHub tree == `pron-lora-long`'s.
- Fresh-clone smoke: `git clone … && bash bootstrap/setup.sh --inference` verify block.
  (Still an **open item** from 2026-09-22 — warm-VM only so far.)
- Confirm default branch is `main`; verify no live doc still says "checkout <branch> to get X".

---

# Still pending from last session — qfinal sweep (do not lose)

Smoke passed; awaiting your go-ahead for 16 tracks (8 songs × α 0.3 / 0.5). Two commands are in
`git show 39d1bbd:agent_notes/current.md` (bottom) — or just ask and I'll re-emit them.
Adapters: `<base>/loras/audio_cpp/pron/qfinal_a{0.3,0.5}/`, NAR `7d9324bf…`.
