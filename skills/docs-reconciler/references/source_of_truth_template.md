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
| Why a decision was made | `DECISIONS.md` | read-only; cite, don't rewrite |
| History / outcomes | `PROGRESS.md` | read-only |
| Known stale / open items | `docs/IMPROVEMENTS.md` | read-only snapshot |
| Doc index | `docs/README.md` | must list every live runbook |
| Agent contract | `AGENTS.md` | |
| Archived / superseded | `docs/investigation.md`, `docs/yue2-gguf-lora-findings.md`, `verification.md`, `docs/LIVE_STATUS.md` | banners are correct; don't "fix" |
