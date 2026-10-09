# current — 2026-10-09 (merge prep: curated `pron-lora-long-aya` → `main`)

Goal: land the **lessons + key tooling** from this branch on `main`, **without** the heavy run
artifacts, and keep `PROGRESS.md` / `DECISIONS.md` lean. Docs reconciled for the donor decision.

## Headline decision
The Quran pronunciation donor (`quran_ahh_r32` + `qahh_a0*` merges) is **shelved for
arabmaqamrock** — no demonstrated diction advantage over v2 (M13 + the D-test; the rubric
saturated at 5). Reserved for a future **dialect** project: *take the song's melody, the
Quran's diction.* Evaluation now runs in the external **rating app**
(`gh repo clone akbargherbal/ai_music_rating_app`).

## Done this turn (on `pron-lora-long-aya`)
- `PROGRESS.md` — M12–M15 → one lean **M12** block (108 → 127 lines).
- `DECISIONS.md` — shelving decision + "score the axis you care about" lesson (88 → 103).
- `README.md` — donor section → **shelved**; status line; evaluation points at the rating app.
- `SOURCE_OF_TRUTH.md` — LoRA row → donor "shelved".
- `docs/LISTENING_EVAL.md` — setup uses `gh repo clone akbargherbal/ai_music_rating_app`.
- `skills/docs-reconciler/references/unverifiable.txt` — benign run-record tokens curated.
- `RECONCILIATION_LOG.md` — 2026-10-09 entry appended.
- `results/jarir_qahh/OPEN_DECISIONS.md` — donor marked Resolved.
- `results/dtest_diction/rating_20261009-2208.md` — report filed; junk deleted.
- **`opencode.json` — staged** (`git add` done) so a fresh VM is preconfigured.
- Reconciler Steps 1–2 after edits: **0 flagged / 1483 checkable**.

## Merge scope
**A — bring to main:** tooling/config (`config/{A100,L4,LEGACY}_*.yml`,
`config/quran_ahh_r32.yml`, root scripts, `INFERENCE/` tooling + `scorecards/` + `songs.*.json`,
`bootstrap/{rename_run,restore_run,setup}.sh`, `tests/test_generate.py`, `.gitignore`,
`manifests/manifest.example`, `skills/`, **`opencode.json`**) and the docs set (new
`docs/LISTENING_EVAL.md` + `docs/QURAN_*.md`; modified `README.md`, `SOURCE_OF_TRUTH.md`,
`PROGRESS.md`, `DECISIONS.md`, `RECONCILIATION_LOG.md`, `user_cheatsheet.md`, `docs/*`,
`TRAINING_ANALYSIS/ANALYSIS.md`).

**C — keep on the branch (do NOT land on main):** `quran_text/` (3.0 MB),
`TRAINING_ANALYSIS/quran_ahh_r32/` + `quran_ahh_r8_rank8_aronly/` (PNG snapshots), `results/`,
`INFERENCE/rating_app/` (superseded), `INFERENCE/eval_app/`.

## Commands

terminal: foreground (state-changing, fast git ops — not a long job).

```bash
# 1. freeze everything on the branch (explicit — do NOT `git add -A`:
#    it would sweep in the 39 untracked graphify-out/cache/ files)
git checkout pron-lora-long-aya
git add PROGRESS.md DECISIONS.md README.md SOURCE_OF_TRUTH.md RECONCILIATION_LOG.md \
  docs/LISTENING_EVAL.md skills/docs-reconciler/references/unverifiable.txt \
  agent_notes/current.md results/jarir_qahh/OPEN_DECISIONS.md results/dtest_diction opencode.json
git commit -m "docs: donor shelved; lean M12; rating app for eval; track opencode.json"

# 2. build the curated release branch off the real main
git fetch origin
git checkout -b release/lean origin/main
git merge --no-ff pron-lora-long-aya -m "merge pron-lora-long-aya (curated into main)"
#    (if it stops: only bootstrap/setup.sh or docs/COMMAND_HANDOVER_GOTCHAS.md can conflict)

# 3. drop the heavy set from the release tree
git rm -r quran_text TRAINING_ANALYSIS/quran_ahh_r32 TRAINING_ANALYSIS/quran_ahh_r8_rank8_aronly \
  results INFERENCE/rating_app INFERENCE/eval_app
git commit -m "main: drop heavy run artifacts (kept on pron-lora-long-aya)"

# 4. review before landing
git diff --stat origin/main..HEAD

# 5. land it
git checkout main && git merge --ff-only origin/main
git merge --ff-only release/lean
git push origin main        # needs your auth (bootstrap/github_auth.sh)
```

Alternative (no merge history, cleanest tree): skip step 2–3 and instead
`git checkout -b release/lean origin/main && git checkout pron-lora-long-aya -- <A-paths>`.
Trade-off: loses the 66-commit provenance; the branch keeps it anyway.

## After landing
- Bucket-C paths are gone from main; the brought docs cite them only in bucket-C files, so the
  post-merge reconciler should stay at **0** (re-run to confirm).
- Optional: `git rm` `INFERENCE/rating_app/` even from the branch if you want it gone entirely.
