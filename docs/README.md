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
| Decide L4 vs A100 (cost/time) | [GPU_L4_VS_A100.md](GPU_L4_VS_A100.md) |
| Finish a run: final backup + push checklist | [FINAL_BACKUP.md](FINAL_BACKUP.md) |
| Build `audiocpp_cli` for a target GPU on a CPU-only runtime | [audiocpp_gpu_arch_builds.md](audiocpp_gpu_arch_builds.md) |
| Run inference (YuE2 GGUF + LoRA) on a fresh VM | [INFERENCE.md](INFERENCE.md) |
| Train the AR-only pronunciation LoRA | [PRON_LORA.md](PRON_LORA.md) |
| Verify / offline-eval the pronunciation LoRA (source + AR-loss replay) | [PRON_LORA_VERIFICATION.md](PRON_LORA_VERIFICATION.md) |
| Merge v2 + pron at a chosen alpha | [PRON_LORA_MERGE.md](PRON_LORA_MERGE.md) |
| Alpha sweep + blinded listening review | [PRON_LORA_SWEEP.md](PRON_LORA_SWEEP.md) |
| Hand the user a command to run (terminal reality check) | [COMMAND_HANDOVER_GOTCHAS.md](COMMAND_HANDOVER_GOTCHAS.md) |
| How the text→duration cap is derived | [text_to_duration_formula.md](text_to_duration_formula.md) |
| Repo audit: stale docs, drift & workflow backlog | [IMPROVEMENTS.md](IMPROVEMENTS.md) |

Future ideas (not runbooks, not scheduled): [FUTURE_PRONUNCIATION_LORA.md](FUTURE_PRONUNCIATION_LORA.md)
— fixing Arabic pronunciation with a second, AR-only LoRA.

Not runbooks — kept for the record. `LIVE_STATUS.md` is a point-in-time snapshot.
`investigation.md` and `yue2-gguf-lora-findings.md` are **superseded/retracted**
(see the banners at their tops); do not follow them.

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
| Inference workspace | `/content/audiocpp_inference/` (GCS `<base>/audiocpp_inference/`) |
| Inference output | `/content/audiocpp_inference/out/` (`_runs_status.log`, `*_time.txt`, `*.json`) |
| Inference prompts | `/content/audiocpp_inference/prompts/<Maqam>_{style,lyrics}.txt` |
| Converted LoRA | `/content/converter/out/akbar_arabic_rock_lora_{ar,nar}.safetensors` |
| Handoff notes | `agent_notes/current.md` (git-ignored; GCS-mirrored, no pull command yet) |

Env vars are staged by the launching notebook before any terminal command; a
terminal that can't see them means the notebook cell hasn't run yet.

## The one rule that bites people

`ai-toolkit` **auto-resumes from the latest checkpoint in the run's output
folder**. That is what you want after a pause, and a trap when you meant to
start over: relaunching the same run name with old checkpoints present continues
from them instead of step 0. To genuinely start fresh, archive the old output
(see [BACKUP_RESTORE.md](BACKUP_RESTORE.md)). Details in `../DECISIONS.md`.
