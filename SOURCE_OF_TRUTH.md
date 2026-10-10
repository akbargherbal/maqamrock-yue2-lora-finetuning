# Source of truth

One authority per topic. When two documents disagree, the higher row wins.
History files are authoritative for what happened, never for what is true now.

| Topic | Authority | Notes |
|---|---|---|
| Run config / hyperparameters | `config/v3_arabmaqamrock_lora.yml` (A100) · `config/v3_arabmaqamrock_lora_l4.yml` (L4); `config/LEGACY_akbar_arabic_rock_lora.yml` = v1/v2 | `DECISIONS.md` explains why; agents never edit either |
| Maqamrock training dataset (v2 folder / v3 zip) | GCS `<base>/v2_arabmaqamrock_dataset/` (267) · `<base>/v3_arabmaqamrock_dataset.zip` (438, verbatim) | renamed + v3 added 2026-10-10; `GCP_DATASET_ZIP` selects v3, else `GCP_DATASET_PATH` |
| Start / pause / resume training | `docs/START.md`, `docs/PAUSE_RESUME.md` | |
| Run metrics & liveness | `loss_log.db` via `monitor_loss.py` | files, not prose |
| Backup layout / restore | `docs/BACKUP_RESTORE.md` + `backup_to_gcp.py --help` | script flags beat prose |
| Inference procedure / provenance | `docs/INFERENCE.md` | repo `INFERENCE/` scripts are canonical |
| v3 output-quality "spice" sweep (sampler / scale / checkpoint) | `docs/V3_SPICE_SWEEP.md` | Pass-1 arm table + rollout; implement on Colab |
| Pron LoRA training | `docs/PRON_LORA.md` | runbook; opt-in via `GCP_PRON_DATASET_PATH` |
| Long-aya Quran LoRA (run / resume) — **RETIRED 2026-10-07** | `docs/PRON_LORA_LONG.md` | the 9-reciter `quran_long_aya_r8_s10` is retired → `<base>/archive/quran_long_aya_legacy/`; superseded by `quran_ahh_r32` |
| Long-aya run configs — **RETIRED** | `config/quran_long_aya_r8_s10.yml` · `config/quran_long_aya_r8.yml` | never edit (kept for the record); both runs retired |
| Long-aya dataset + banked artifacts | GCS `<base>/quran_long_aya_dataset_s10.tar`, `<base>/…_s10/_latent_cache.tar` | dataset tars kept; the `quran_long_aya_r8_s10` **run** is retired (archived) |
| Pron LoRA source verification / offline eval | `docs/PRON_LORA_VERIFICATION.md` | A0–A7 + smoke + A100 run + AR-loss replay |
| v2 + pron merge (scaling, ranks) | `docs/PRON_LORA_MERGE.md` + `merge_pron_lora.py --help` | alpha convention is source-verified there |
| Quran pron **alone** (α=1) on base model | `docs/QURAN_ONLY_EXPERIMENT.md` + `build_pron_only_fused.py` | the AR-only→fused workaround and the first-sample result |
| Quran adapter format/caption probe | `docs/QURAN_FORMAT_PROBE.md` + `INFERENCE/songs.quran_format_probe.json` | 6-arm GPU test; run 2026-10-04, listening verdict recorded |
| Quran-pron objective / criteria / next-run plan | `docs/QURAN_PRON_REVIEW.md` | post-verdict audit; acceptance criteria proposal (pending user) |
| AHH Quran LoRA run (`quran_ahh_r32`) — hub / config audit / GPU checklist | `docs/QURAN_AHH_RUN.md` | gated by Phase 1 base-model ceiling probe |
| High-quality Quran recitation dataset (AHH filtered) | `github.com/akbargherbal/quran_recitation_training_dataset` + GCS `AHH_Quran_Long_Aya_Filtered_DATASET.zip` | 3 reciters; 9,492/13,501 kept; audio-only (pair with Tanzil text) |
| LoRA library (what exists, how many, where) | `docs/LORA_INVENTORY.md` | canonical `<base>/loras/`: **style** + `source/`; pron donor `quran_ahh_r32` — **shelved, not adopted for arabmaqamrock** (`PROGRESS.md` M12); merges `qahh_a0*` under `<base>/quran_ahh_r32/maqamrock_merge/`; superseded donors under `<base>/archive/` |
| Alpha sweep / listening review | `docs/PRON_LORA_SWEEP.md` | procedure + Rounds 1–5; numbers in `results/{pron_sweep,pron_fine_sweep,pron_ckpt_sweep,maqam_lyric_swap,pron_knob_probe}/` |
| Blinded listening packages (audio) | GCS `<base>/listening/` | generated mp3 packages; **not repo content** (`.gitignore` `*_INPUT/`) |
| Blinded A/B listening package | `docs/AB_BLIND_EVAL.md` + `INFERENCE/prepare_ab_eval.py --help` | script flags beat prose; skill `ab-blind-eval`; hands a package to a different person |
| Listening evaluation / rating (score rendered variants) | `docs/LISTENING_EVAL.md` | external app `github.com/akbargherbal/ai_music_rating_app`; supersedes the earlier in-repo listening app; skill `listening-eval` |
| Why a decision was made | `DECISIONS.md` | read-only; cite, don't rewrite |
| Milestones (outcomes) | `PROGRESS.md` | read-only; outcomes, not narrative |
| Full history | git | `git log`; pre-rewrite narrative `git show 39d1bbd:PROGRESS.md` |
| Known stale / open items | `docs/IMPROVEMENTS.md` | read-only snapshot |
| Doc index | `docs/README.md` | must list every live runbook |
| User cheat-sheet (copy-paste commands) | `user_cheatsheet.md` | index only; the runbooks above are authority |
| Repo knowledge graph (graphify) | `docs/GRAPHIFY.md` | generated map; refresh with `graphify update` |
| Agent contract | `AGENTS.md` | |
| Archived / superseded | `docs/investigation.md`, `docs/yue2-gguf-lora-findings.md`, `verification.md`, `docs/LIVE_STATUS.md` | banners are correct; don't "fix" |
