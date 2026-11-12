# Start training on a fresh Colab VM

Assumes: a Colab GPU runtime (a 24 GB L4 or an A100), and the launching notebook has staged
`/root/.secrets.env` (it exports `HF_TOKEN`, `GCP_DATASET_ZIP`, `GCP_BACKUP_BASE`; add
`GCP_DATASET_COUNT` yourself whenever the zip is not the 438-track v3). Nothing here is
bucket- or account-specific in the repo.

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
the dataset named by `GCP_DATASET_ZIP` from GCS (the 438-track v3 zip by default; the
`arabic_instrumental_lora` run sets the 482-track instrumental zip **and**
`GCP_DATASET_COUNT=482`, otherwise the verify fails).

```bash
mkdir -p /content/logs
setsid nohup bash bootstrap/setup.sh --training > /content/logs/setup.log 2>&1 & disown
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

Backup daemon (needs `GCP_BACKUP_BASE`, from the notebook) and GPU logger. `--run-name` must equal
the config's `name:` key — `v3_arabmaqamrock_lora` is only the default/current example;
`arabic_instrumental_lora` is the next run.

```bash
cd /content/maqamrock-yue2-lora-finetuning
setsid nohup python backup_to_gcp.py --run-name v3_arabmaqamrock_lora \
  > /content/logs/gcp_backup_stdout.log 2>&1 & disown
setsid nohup python gpu_logger.py --out /content/logs/gpu_usage.csv \
  > /content/logs/gpu_logger_stdout.log 2>&1 & disown
pgrep -af 'backup_to_gcp.py|gpu_logger.py'
```

## 5. Launch training (you type this)

```bash
cd /content/maqamrock-yue2-lora-finetuning
python train_ctl.py start
```

Launches **detached** (its own session), so a stray Ctrl+C in this tab can't kill
it, and writes a pid/state file plus both logs. It reuses the latent cache if
present, else caches first — A2 estimates ~22 min for the 482-track set (v3's 438 was
quoted at ~20 min; older v2 notes say ~12 min, so treat it as tens of minutes). With
`sample`/`disable_sampling: true` (the current configs) there is **no**
step-0 sample, so `loss_log.db` sits at 0 steps for the whole cache pass — normal,
not a stall. A config with sampling enabled instead spends a few minutes generating
step 0 first.

```bash
python train_ctl.py status    # running? pid? log tail
python train_ctl.py stop      # SIGINT; waits for "Job stopped"
```

The bare verbs above are correct **only for the default v3 config**. Any other run
(`arabic_instrumental_lora`, the L4 variant, a pron run) must pass its config to all three:
`--config config/<run>.yml`. `start` otherwise launches v3, and `stop`/`status` otherwise
reject the live process with "not our training run" — see `docs/COMMAND_HANDOVER_GOTCHAS.md`
(2026-11-12).

Then monitor it: [MONITOR.md](MONITOR.md).
