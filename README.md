# maqamrock-yue2-lora-finetuning

A LoRA fine-tune of [YuE2](https://github.com/ostris/ai-toolkit) (3B, int8 `convrot`) on Arabic maqam rock, trained with [`ostris/ai-toolkit`](https://github.com/ostris/ai-toolkit). The goal is a style/timbre adapter, not a melodic one: 267 clips across four maqams sharing one fixed genre, production, and instrumentation, with a trigger word `arabmaqamrock`.

Training runs on a rented single GPU in Google Colab, driven over the CLI rather than the Web UI, and is monitored through an agent-readable SQLite metrics db. Colab is ephemeral, so all expensive artifacts are mirrored to GCS as the run proceeds.

## Status

Nothing has been trained yet (as of the `PROGRESS.md` 2026-09-19 entry). The dataset is built and independently verified, the config is final, and `bootstrap/setup.sh` is written but not yet validated end-to-end on a fresh Colab L4. The next step is to stand up that VM, run the bootstrap, confirm `loss_log.db` is created and updating, then launch the real run.

## Repo layout

```
config/akbar_arabic_rock_lora.yml   # the training config (rank 32, EMA, cot: off)
prepare_yue2_dataset.py             # build audio + .txt caption pairs from manifests
monitor_loss.py                     # read-only loss_log.db inspector (step, metrics, ETA)
gpu_logger.py                       # nvidia-smi poller -> CSV (AI Toolkit logs no GPU stats)
backup_to_gcp.py                    # periodic GCS mirror of run artifacts
bootstrap/setup.sh                  # idempotent Colab bootstrap (ai-toolkit, HF cache, dataset)
bootstrap/github_auth.sh            # token-based git push auth, never exposed to the agent
DECISIONS.md                        # source-verified decisions and non-obvious findings
PROGRESS.md                         # milestone trail across sessions
verification.md                     # independent dataset audit
AGENTS.md                           # operating instructions for the coding agent
```

## Dataset

Built by `prepare_yue2_dataset.py` from a `min_4stars_ai_music/` tree and its per-workspace `workspace_manifest.json` files:

```bash
python prepare_yue2_dataset.py --root ./min_4stars_ai_music --out ./yue2_dataset
```

Result: **267 audio/caption pairs**, all native `mp3, 48000 Hz, stereo` — exactly what YuE2's loader expects, so no conversion is needed. Captions are style-only (genre, maqam, vocals, production, instrumentation, mood); the Suno control headers and all lyrics are stripped. The shortlist is the filesystem plus the manifest: a take is used only if it is both listed and physically present. Do not use `--convert-wav`; it hardcodes 44.1 kHz and would force a needless lossy round-trip. The full audit is in `verification.md`.

## Training config

`config/akbar_arabic_rock_lora.yml` runs `process[].type: diffusion_trainer` with `arch: yue2` on `Comfy-Org/YuE2/checkpoints/yue2_3b_int8_convrot.safetensors` (`quantize: true`, `qtype: convrot8`). Key choices: rank 32 combined LoRA, `ema_config.use_ema: true` with `ema_decay: 0.999`, `model_kwargs.cot: "off"` (captions carry no melodic information, so SheetSage2 is never loaded), `cache_latents_to_disk: true` (mandatory for YuE2), `noise_scheduler: flowmatch`, and `max_step_saves_to_keep: 12` so the background GCS sync has a buffer before local rotation deletes older checkpoints.

`log_config` at the process root is a dead key left in with a comment, and `aitk_db.db` is not a metrics source — see `DECISIONS.md` for both.

## Running on Colab

On a fresh VM, restore the repo and start the bootstrap in the background while you authenticate the vscode.dev tunnel in the foreground:

```bash
git clone <this repo's URL>
cd maqamrock-yue2-lora-finetuning
bash bootstrap/setup.sh > /content/logs/setup.log 2>&1 &
```

The notebook cell must export `HF_TOKEN` (staged into `/root/.secrets.env`), `GCP_DATASET_PATH`, and `GCP_BACKUP_BASE` first; nothing bucket- or account-specific is hardcoded in the repo. `setup.sh` is idempotent: it skips the dataset download when the completion marker is present and skips any HF asset already cached. It clones ai-toolkit (tracking `main`, deliberately not pinned) and pre-warms only the assets this config actually loads.

Then start the two sidecar processes and launch training from ai-toolkit's directory:

```bash
cd /content/maqamrock-yue2-lora-finetuning
setsid nohup python backup_to_gcp.py --run-name akbar_arabic_rock_lora \
  > /content/logs/gcp_backup_stdout.log 2>&1 & disown
setsid nohup python gpu_logger.py --out /content/logs/gpu_usage.csv \
  > /content/logs/gpu_logger_stdout.log 2>&1 & disown

cd /content/ai-toolkit
python run.py /content/maqamrock-yue2-lora-finetuning/config/akbar_arabic_rock_lora.yml \
  -l /content/logs/train.log
```

Everything for the job lands under `/content/ai-toolkit/output/akbar_arabic_rock_lora/`: checkpoints, the auto-saved `config.yaml`, samples, `loss_log.db`, and the timestamped `tensorboard/` subfolder.

## Observability

Three real surfaces, in priority order:

1. **`loss_log.db`** — the per-step metrics source, written by `UILogger` because `logging.use_ui_logger: true`. Read it with `python monitor_loss.py /content/ai-toolkit/output/akbar_arabic_rock_lora/loss_log.db` (add `--key nar_flow --history 50`, or `--watch 30 --total-steps 3000` for a live ETA). It is WAL-mode, so read-only inspection during training is safe.
2. **`/content/logs/train.log`** — the `-l` stdout/stderr log; the tqdm progress line and any traceback live here.
3. **`/content/logs/gpu_usage.csv`** — utilization/memory/temp/power, sampled every 10s by `gpu_logger.py`. AI Toolkit logs none of this itself.

`aitk_db.db` (the config's `sqlite_db_path`) holds at most a job-status string and only when the Web UI launched the run; a CLI run leaves it untouched entirely. Do not point monitoring at it.

## Backup to GCS

`backup_to_gcp.py` mirrors the run's artifacts to `gs://<base>/<run-name>/` every 15 minutes: `training_folder/akbar_arabic_rock_lora/` → `output/`, `/content/logs/` → `logs/`, and `agent_notes/` → `agent_notes/`. It uses `gsutil rsync` without `-d` (append/update only, never deletes remote), writes a `run_manifest.json` that refuses to mix two runs in one prefix, and gates each sync on the newest file being untouched (`--settle-seconds`) except for `loss_log.db` and its WAL sidecars, which are perpetually fresh during a run. To confirm progress is actually backed up, compare GCS object timestamps against local ones rather than assuming.

## Docs

`DECISIONS.md` records source-verified decisions and the reasoning behind non-obvious config fields; read it before changing anything that looks wrong. `PROGRESS.md` is the milestone trail. `verification.md` is the dataset audit. `AGENTS.md` is the operating contract for the coding agent, including the run-control policy (no new or changed run without the user typing the command; auto-resume only an unchanged, already-approved run after an unplanned interruption).
