# current — 2026-10-07 16:47Z

**D-test render: DONE.** 20/20 takes, **0 failed**. Driver `INFERENCE/jarir_lever_probe.sh`
(exited rc_total=0 at 16:34:24Z). Backed up and verified.

## Ground truth (`python status.py`, 16:46Z)

- training: not running · GPU **free** (0% / 0 MiB).
- inference: **complete** — 20 WAVs in `out/jarir_dtest/`:
  `v2_1.0_1.0` 4/4 · `qa_1.0_1.0` 4/4 · `qa_0.5_1.0` 4/4 · `qa_1.0_0.5` 4/4 · `qa_0.0_1.0` 4/4.
  `_failed.log` empty. Wall 37:30.
  (`status.py`'s `inference:` line reports a stale single-arm count — trust the folder.)
- backup: last pass **16:44:45Z**, 5/5 folders synced. GCS `…/out/jarir_dtest/` = **20/20**,
  newest upload 16:39:28Z (after the last take). Local 20 = GCS 20. ✅
- sidecars: `backup_to_gcp.py`=11254 · `gpu_logger.py`=DOWN (not needed for inference) ·
  `vm-continuity`=healthy. disk 64.2 GB free. graph STALE (HEAD `3690f98`).

## Next: listen to the D-test

1. Re-sync the audio to your PC:
   ```powershell
   gsutil -m rsync -r gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/audiocpp_inference/out/jarir_dtest .\jarir_dtest\
   ```
2. Launch the rating app (one command, add `--blind` for the unbiased pass):
   ```powershell
   python app.py --audio "C:\Users\DELL\Downloads\jarir_dtest" --label dtest_diction --scorecard "C:\path\to\dtest_diction.json"
   ```
   Scorecard source: `INFERENCE/scorecards/dtest_diction.json`. Confirm the startup line
   `rating_app: ready for 'dtest_diction' [scorecard: …]` (not `[scorecard: default]`).
3. Rate; export `/report.md`. Resume is safe: every save writes `runs/dtest_diction/results.json`.
   Runbook: `docs/LISTENING_EVAL.md`.

## Also

- **Uncommitted doc change set**: evaluation documented on the external app
  (`docs/LISTENING_EVAL.md` + `skills/listening-eval/`, plus DECISIONS/PROGRESS/README/
  SOURCE_OF_TRUTH/user_cheatsheet/AB_BLIND_EVAL edits, reconciler pass log). Not committed.
