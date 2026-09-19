# Operations docs

Task-oriented runbooks for running this project on Google Colab. These answer
"how do I actually do X". For *why* the config is the way it is, read
`../DECISIONS.md`; for project history, `../PROGRESS.md`. The coding agent's
operating contract is `../AGENTS.md`.

| Task | Doc |
|---|---|
| Get training running on a fresh Colab VM | [START.md](START.md) |
| Stop for the night and resume next session | [PAUSE_RESUME.md](PAUSE_RESUME.md) |
| GCS mirror layout, verify a backup, restore from it | [BACKUP_RESTORE.md](BACKUP_RESTORE.md) |
| Check how training is going | [MONITOR.md](MONITOR.md) |

## Constants (memorize / copy)

| | |
|---|---|
| Run name | `akbar_arabic_rock_lora` |
| Repo | `/content/maqamrock-yue2-lora-finetuning` |
| ai-toolkit | `/content/ai-toolkit` (cloned by bootstrap, tracks `main`) |
| Dataset | `/content/yue2_dataset` |
| Run output | `/content/ai-toolkit/output/akbar_arabic_rock_lora/` |
| Train log | `/content/logs/train.log` |
| Metrics db | `/content/ai-toolkit/output/akbar_arabic_rock_lora/loss_log.db` |
| GPU csv | `/content/logs/gpu_usage.csv` |
| GCS base | `gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning` |
| Secrets/env | `/root/.secrets.env` (exports `HF_TOKEN`, `GCP_DATASET_PATH`, `GCP_BACKUP_BASE`) |

Env vars are staged by the launching notebook before any terminal command; a
terminal that can't see them means the notebook cell hasn't run yet.

## The one rule that bites people

`ai-toolkit` **auto-resumes from the latest checkpoint in the run's output
folder**. That is what you want after a pause, and a trap when you meant to
start over: relaunching the same run name with old checkpoints present continues
from them instead of step 0. To genuinely start fresh, archive the old output
(see [BACKUP_RESTORE.md](BACKUP_RESTORE.md)). Details in `../DECISIONS.md`.
