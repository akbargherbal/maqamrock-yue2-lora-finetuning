# Start training on a fresh Colab VM

Assumes: a Colab L4 runtime, and the launching notebook has staged
`/root/.secrets.env` (it exports `HF_TOKEN`, `GCP_DATASET_PATH`,
`GCP_BACKUP_BASE`). Nothing here is bucket- or account-specific in the repo.

> If `/content` survived (same VM), skip to step 4 — but check whether the run
> output still has checkpoints: relaunching will **auto-resume** from them. To
> start genuinely fresh, archive first ([BACKUP_RESTORE.md](BACKUP_RESTORE.md)).

## 1. Restore the repo

```bash
git clone https://github.com/akbargherbal/maqamrock-yue2-lora-finetuning.git \
  /content/maqamrock-yue2-lora-finetuning
cd /content/maqamrock-yue2-lora-finetuning
```

## 2. Bootstrap in the background

Does everything slow in parallel: clones ai-toolkit, installs its deps (pinned
torch 2.13 / cu130 — see `../DECISIONS.md`), pre-warms the HF cache, and pulls
the 267-track dataset from GCS.

```bash
bash bootstrap/setup.sh --training > /content/logs/setup.log 2>&1 &
```

(`--training` is the default; for inference instead, see `setup.sh --help`.)

While it runs, authenticate the `vscode.dev` tunnel in the foreground. Watch
for the verify block; it must end with all `[ok]` (including the torch/CUDA +
audio-decode check). Confirm with:

```bash
tail -n 25 /content/logs/setup.log
```

## 3. (Only if resuming) restore the run folder from GCS

See [PAUSE_RESUME.md](PAUSE_RESUME.md). Skip for a fresh start.

## 4. Start the two sidecars

Backup daemon (needs `GCP_BACKUP_BASE`, from the notebook) and GPU logger:

```bash
cd /content/maqamrock-yue2-lora-finetuning
setsid nohup python backup_to_gcp.py --run-name akbar_arabic_rock_lora \
  > /content/logs/gcp_backup_stdout.log 2>&1 & disown
setsid nohup python gpu_logger.py --out /content/logs/gpu_usage.csv \
  > /content/logs/gpu_logger_stdout.log 2>&1 & disown
pgrep -af 'backup_to_gcp.py|gpu_logger.py'
```

## 5. Launch training (you type this)

```bash
cd /content/ai-toolkit
python run.py /content/maqamrock-yue2-lora-finetuning/config/akbar_arabic_rock_lora.yml \
  -l /content/logs/train.log
```

Runs in the foreground; leave it. It reuses the latent cache if present
(else caches ~12 min first), then trains to `train.steps`. Note: the very first
thing after start is the **step-0 sample generation**, so `loss_log.db` stays at
0 steps for a few minutes — that is normal, not a stall.

Then monitor it: [MONITOR.md](MONITOR.md).
