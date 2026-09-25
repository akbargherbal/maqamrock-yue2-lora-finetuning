# Source of truth

One authority per topic. When two documents disagree, the higher row wins.
History files are authoritative for what happened, never for what is true now.

| Topic | Authority | Notes |
|---|---|---|
| Run config / hyperparameters | `config/akbar_arabic_rock_lora.yml` | `DECISIONS.md` explains why; agents never edit either |
| Start / pause / resume training | `docs/START.md`, `docs/PAUSE_RESUME.md` | |
| Run metrics & liveness | `loss_log.db` via `monitor_loss.py` | files, not prose |
| Backup layout / restore | `docs/BACKUP_RESTORE.md` + `backup_to_gcp.py --help` | script flags beat prose |
| Inference procedure / provenance | `docs/INFERENCE.md` | repo `INFERENCE/` scripts are canonical |
| Pron LoRA training | `docs/PRON_LORA.md` | runbook; opt-in via `GCP_PRON_DATASET_PATH` |
| Pron LoRA source verification / offline eval | `docs/PRON_LORA_VERIFICATION.md` | A0–A7 + smoke + A100 run + AR-loss replay |
| v2 + pron merge (scaling, ranks) | `docs/PRON_LORA_MERGE.md` + `merge_pron_lora.py --help` | alpha convention is source-verified there |
| Alpha sweep / listening review | `docs/PRON_LORA_SWEEP.md` | procedure; numbers in `results/pron_sweep/` |
| Why a decision was made | `DECISIONS.md` | read-only; cite, don't rewrite |
| History / outcomes | `PROGRESS.md` | read-only |
| Known stale / open items | `docs/IMPROVEMENTS.md` | read-only snapshot |
| Doc index | `docs/README.md` | must list every live runbook |
| Repo knowledge graph (graphify) | `docs/GRAPHIFY.md` | generated map; refresh with `graphify update` |
| Agent contract | `AGENTS.md` | |
| Archived / superseded | `docs/investigation.md`, `docs/yue2-gguf-lora-findings.md`, `verification.md`, `docs/LIVE_STATUS.md` | banners are correct; don't "fix" |
