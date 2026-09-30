# Source of truth

One authority per topic. When two documents disagree, the higher row wins.
History files are authoritative for what happened, never for what is true now.

| Topic | Authority | Notes |
|---|---|---|
| Run config / hyperparameters | `config/akbar_arabic_rock_lora.yml` | `DECISIONS.md` explains why; agents never edit either |
| Start / pause / resume training | `docs/START.md`, `docs/PAUSE_RESUME.md` | |
| Run metrics & liveness | `loss_log.db` via `monitor_loss.py` | files, not prose |
| Backup layout / restore | `docs/BACKUP_RESTORE.md` + `backup_to_gcp.py --help` | script flags beat prose |
| GCS prefix organisation (sections, frozen dataset, migration state) | `docs/GCP_ORGANIZATION_PLAN.md` + the on-bucket `<base>/LAYOUT.json` | the plan is authority for *intent*; the bucket is the fact. `quran_long_aya_dataset/` frozen 2026-09-29 |
| Inference procedure / provenance | `docs/INFERENCE.md` | repo `INFERENCE/` scripts are canonical |
| Pron LoRA training | `docs/PRON_LORA.md` | runbook; opt-in via `GCP_PRON_DATASET_PATH` |
| Long-aya Quran LoRA (run / resume) | `docs/PRON_LORA_LONG.md` | canonical hub; active run `quran_long_aya_r8_s10`, full set reserved |
| Long-aya run configs | `config/quran_long_aya_r8_s10.yml` (active) · `config/quran_long_aya_r8.yml` (full set, reserved) | never edit; dataset `_s10` = 8,100 pairs |
| Long-aya dataset + banked artifacts | GCS `<base>/quran_long_aya_dataset_s10.tar`, `<base>/…_s10/_latent_cache.tar`, `<base>/quran_long_aya_r8_s10/output/` | dataset tar · banked cache · checkpoints+optimizer |
| Pron LoRA source verification / offline eval | `docs/PRON_LORA_VERIFICATION.md` | A0–A7 + smoke + A100 run + AR-loss replay |
| End-to-end test plan / tiers | `docs/E2E_TESTING_PLAN.md` | proposed, not yet implemented; GPU only for the budgeted smoke gate |
| v2 + pron merge (scaling, ranks) | `docs/PRON_LORA_MERGE.md` + `merge_pron_lora.py --help` | alpha convention is source-verified there |
| LoRA library (what exists, how many, where) | `docs/LORA_INVENTORY.md` | canonical: `<base>/loras/` (current: style + qfinal; superseded pron_lora_ar_only_r8 under `<base>/archive/pron_lora_ar_only_legacy/`) |
| Alpha sweep / listening review | `docs/PRON_LORA_SWEEP.md` | procedure + Rounds 1–5; numbers in `results/{pron_sweep,pron_fine_sweep,pron_ckpt_sweep,maqam_lyric_swap,pron_knob_probe}/` |
| Blinded listening packages (audio) | GCS `<base>/listening/` | generated mp3 packages; **not repo content** (`.gitignore` `*_INPUT/`) |
| Blinded A/B listening package | `docs/AB_BLIND_EVAL.md` + `INFERENCE/prepare_ab_eval.py --help` | script flags beat prose; skill `ab-blind-eval` |
| Why a decision was made | `DECISIONS.md` | read-only; cite, don't rewrite |
| Milestones (outcomes) | `PROGRESS.md` | read-only; outcomes, not narrative |
| Full history | git | `git log`; pre-rewrite narrative `git show 39d1bbd:PROGRESS.md` |
| Known stale / open items | `docs/IMPROVEMENTS.md` | read-only snapshot |
| Doc index | `docs/README.md` | must list every live runbook |
| User cheat-sheet (copy-paste commands) | `user_cheatsheet.md` | index only; the runbooks above are authority |
| Repo knowledge graph (graphify) | `docs/GRAPHIFY.md` | generated map; refresh with `graphify update` |
| Agent contract | `AGENTS.md` | |
| v2 training-set facts (repeats, caption shape, lyric tags) | `docs/music-cover-feasibility.md` §5 | measured over the 267-song GCS dataset; sampler note in §5 |
| Verbatim / lyric-adherence blind round outcome | `manifests/evaluation_verbatim_hijaz/MY_EVALUATION.txt` (+ `manifests/evaluation_verbatim_hijaz/KEYS.txt`) | 5 arms, 1 track, seed 4148240095; narrated in `docs/music-cover-feasibility.md` §6 |
| Guide-conditioned round outcome (v2 `score.abc` → `qfinal_a0.3`) | `manifests/evaluation_v2_abc_to_qfinal/MY_EVALUATION.txt` (+ `manifests/evaluation_v2_abc_to_qfinal/KEYS.txt`) | 4 arms, 1 track, seed 4148240095, **blinding seed 20260932** (the GCS `listening/V2_ABC_TO_QFINAL_INPUT/` package is a different, unused 20260931 shuffle — see §7 provenance); guided `a2` wins; narrated in `docs/music-cover-feasibility.md` §7 |
| Archived / superseded | `docs/investigation.md`, `docs/yue2-gguf-lora-findings.md`, `verification.md`, `docs/LIVE_STATUS.md` | banners are correct; don't "fix" |
