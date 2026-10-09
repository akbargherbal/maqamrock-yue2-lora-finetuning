# current — 2026-10-09 (merged: `pron-lora-long-aya` → `main`)

## State
`main` now carries the **curated** merge of this branch — tooling + docs + the lean lessons;
the heavy run data did not come across. The Quran donor is **shelved**; evaluation runs in the
external **rating app**.

## What landed on `main`
- **Docs:** `PROGRESS.md` (M12–M15 → one lean **M12** block), `DECISIONS.md` (shelving decision
  + "score the axis you care about"), `README.md` + `SOURCE_OF_TRUTH.md` (donor shelved; rating
  app = the way forward), `docs/LISTENING_EVAL.md` (`gh repo clone akbargherbal/ai_music_rating_app`),
  new `docs/QURAN_*.md`, runbooks/tests updated.
- **Tooling/config:** `config/{A100,L4,LEGACY}_*.yml` + `config/quran_ahh_r32.yml`; `merge_quran_lora.py`,
  `build_pron_only_fused.py`, `prepare_ahh_quran_dataset.py`, `train_ctl.py`, `backup_to_gcp.py`;
  `INFERENCE/` tooling + `scorecards/` + `songs.*.json`; `bootstrap/{rename_run,restore_run,setup}.sh`;
  `skills/`; `opencode.json` (dev config, tracked for fresh VMs).
- **Small referenced records kept:** `INFERENCE/{rating_app,eval_app}`,
  `results/{jarir_qahh,quran_ahh_epochs,dtest_diction}`, `TRAINING_ANALYSIS/quran_ahh_*/ANALYSIS.md`.

## Stayed on the branch (not on `main`)
- `quran_text/` (3 MB dataset text), `TRAINING_ANALYSIS/quran_ahh_*/0*.png` (generated plots).

## Health
- Reconciler Steps 1–2 after merge+trim: **0 flagged / 1483 checkable**.
- Merge conflict resolved in `docs/COMMAND_HANDOVER_GOTCHAS.md` (took the branch's version — a
  superset that keeps origin/main's cuDNN entry plus the `LEGACY_` config rename).
- `.reconcile/` is a local scratch dir (untracked; safe to ignore).

## Next (when resumed)
- New arabmaqamrock round (~400–450 songs) — `config/A100_akbar_arabic_rock_lora.yml` is the template.
- Dialect project (long-term): lyric-free style + separate diction adapter.
