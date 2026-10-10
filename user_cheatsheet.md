# User cheatsheet

Copy-paste commands for running this project on Colab, grouped by "what am I
trying to do". **This is an index, not an authority** — the runbooks in
[`docs/`](docs/README.md) (and `SOURCE_OF_TRUTH.md`) stay the source of truth.
When a command here and a runbook disagree, the runbook + `--help` win. Long jobs
are launched **detached** (`setsid nohup … & disown`): Ctrl+C / closing the tab
will **not** stop them; use the matching `stop`/`pkill`.

## Constants

```bash
cd /content/maqamrock-yue2-lora-finetuning
GCS_BASE=gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning
RUN=v3_arabmaqamrock_lora
OUT=/content/ai-toolkit/output/$RUN
```

| Thing | Path |
|---|---|
| Repo | `/content/maqamrock-yue2-lora-finetuning` |
| Training output | `/content/ai-toolkit/output/v3_arabmaqamrock_lora/` |
| Train log / GPU csv | `/content/logs/train.log`, `/content/logs/gpu_usage.csv` |
| Secrets/env | `/root/.secrets.env` (`HF_TOKEN`, `GCP_DATASET_PATH`, `GCP_BACKUP_BASE`) — staged by the notebook |
| Inference workspace | `/content/audiocpp_inference/` (out/, prompts/, bin/, models/) |
| Converted LoRAs | `/content/converter/out/` (style) + `qahh_a0p1/`, `qahh_a0p3/` |

## 0. Ground truth — always start here

One read-only call that prints training, inference, sidecars, backup age, drift,
disk, run folder, graph staleness:

```bash
python status.py
```

## 1. Sidecars (run these before a long job)

Terminal: detached. Logs under `/content/logs/`; stop with
`pkill -f 'backup_to_gcp.py|gpu_logger.py'`.

```bash
cd /content/maqamrock-yue2-lora-finetuning

# backup daemon — training targets (every 5 min by default)
setsid nohup python backup_to_gcp.py --run-name v3_arabmaqamrock_lora \
  > /content/logs/gcp_backup_stdout.log 2>&1 & disown

# backup daemon — inference workspace instead
setsid nohup python backup_to_gcp.py --inference --interval-minutes 5 \
  > /content/logs/gcp_backup_stdout.log 2>&1 & disown

# GPU logger (training only)
# inference doesn't need it: run_one.sh writes per-track <name>_<seed>_gpu.csv (1 Hz)
setsid nohup python gpu_logger.py --out /content/logs/gpu_usage.csv \
  > /content/logs/gpu_logger_stdout.log 2>&1 & disown

# are they alive? what's it doing?
pgrep -af 'backup_to_gcp.py|gpu_logger.py'
tail -f /content/logs/gcp_backup.log

# agent-session continuity across VM resets
vm-continuity status                       # exit 0 = healthy
vm-continuity watch --interval-minutes 5   # keep it healthy (detached)
```

## 2. Fresh VM: repo + setup + auth

```bash
git clone https://github.com/akbargherbal/maqamrock-yue2-lora-finetuning.git \
  /content/maqamrock-yue2-lora-finetuning
cd /content/maqamrock-yue2-lora-finetuning

# training stack (dataset + ai-toolkit + HF assets): detached, ~slow
mkdir -p /content/logs
setsid nohup bash bootstrap/setup.sh --training > /content/logs/setup.log 2>&1 & disown
tail -n 25 /content/logs/setup.log          # verify block must be all [ok]

# OR inference stack (audio.cpp + GGUFs, no dataset/ai-toolkit)
bash bootstrap/setup.sh --inference > /content/logs/setup.log 2>&1
grep -n "\[FAIL\]" /content/logs/setup.log || echo "no failures"

# authenticate git pushes (paste PAT at the hidden prompt; never in chat)
bash bootstrap/github_auth.sh
```

## 3. Training: start / status / stop

```bash
cd /content/maqamrock-yue2-lora-finetuning
python train_ctl.py start     # detached; step-0 sample first, loss_log stays 0 a few min
python train_ctl.py status    # running? pid? log tail
python train_ctl.py stop      # SIGINT; waits for "Job stopped" (checkpoint-safe)
```

## 4. Monitor training

```bash
# metrics (smoothed trend, not single steps)
python monitor_loss.py /content/ai-toolkit/output/v3_arabmaqamrock_lora/loss_log.db \
  --watch 30 --total-steps 3000
python monitor_loss.py /content/ai-toolkit/output/v3_arabmaqamrock_lora/loss_log.db \
  --key "loss/loss" --history 50

# liveness / errors
tail -f /content/logs/train.log
pgrep -af run.py

# hardware
tail -n 10 /content/logs/gpu_usage.csv
nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw --format=csv
```

## 5. Inference: stage LoRAs, then generate

Stage the adapter pairs a batch references (v2 is files directly in
`/content/converter/out/`; qahh are subdirs). Idempotent — re-run to resume.

```bash
export GCP_BACKUP_BASE=$GCS_BASE
mkdir -p /content/converter/out
gsutil -m rsync -r "$GCS_BASE/loras/audio_cpp/style" /content/converter/out
gcloud storage rsync -r "$GCS_BASE/quran_ahh_r32/maqamrock_merge/convert/qahh_a0p1" /content/converter/out/qahh_a0p1
gcloud storage rsync -r "$GCS_BASE/quran_ahh_r32/maqamrock_merge/convert/qahh_a0p3" /content/converter/out/qahh_a0p3
```

Validate a JSON batch (no GPU, writes nothing), then run it detached:

```bash
cd /content/maqamrock-yue2-lora-finetuning
python INFERENCE/generate.py manifests/batch_36_songs.json --dry-run

mkdir -p /content/logs
setsid nohup python INFERENCE/generate.py manifests/batch_36_songs.json \
  --out-dir /content/audiocpp_inference/out/batch_36_songs \
  > /content/logs/batch_36_songs.log 2>&1 & disown
```

Progress / resume / stop (resume skips tracks whose WAV succeeded; `--force`
regenerates; `--limit N` for a smoke test):

```bash
tail -f /content/audiocpp_inference/out/batch_36_songs/_driver.log
tail -f /content/audiocpp_inference/out/latest/_driver.log   # newest run
pkill -f 'generate.py manifests/batch_36_songs.json'         # stop
# resume = re-run the same command, same --out-dir
```

Single maqam/seed (staged prompts), for a one-off:

```bash
INFERENCE/run_one.sh <Maqam> <seed> [cap|auto]     # Maqam ∈ Ajam Hijaz Kurd Nahawand
```

## 6. Listening evaluation — rate the renders (on your own PC)

Score rendered variants in the external rating app. Full runbook: `docs/LISTENING_EVAL.md`.
The app is **not** in this repo; it replaces the earlier in-repo single-file listening app.

```bash
# once, on your machine
git clone https://github.com/akbargherbal/ai_music_rating_app.git
cd ai_music_rating_app && py -m pip install -r requirements.txt
```

Pull the rendered audio from GCS, then launch with scorecard + label (**one command**;
add `--blind` for the unbiased pass):

```powershell
gsutil -m rsync -r gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/audiocpp_inference/out/<run> .\<run>\

# copy the scorecard into scorecards/ OR pass its path, then:
python app.py --audio "C:\path\to\<run>" --label <run_id> --scorecard "<card.json | name>"
# report: open /report.md   (also /report.csv, /report.json)
```

The startup line `rating_app: ready for '<run_id>' [scorecard: …]` confirms the card was
picked up (a bare `[scorecard: default]` means it was **not**). Change scorecards with a
**new `--label`** — an existing run's scorecard is frozen.

## 7. Backup now / verify / restore

```bash
# one forced pass (don't wait for the 5-min daemon)
python backup_to_gcp.py --run-name v3_arabmaqamrock_lora --once
python backup_to_gcp.py --inference --once

# verify remote vs local
gsutil ls -l $GCS_BASE/v3_arabmaqamrock_lora/output/ | tail
ls -la $OUT/
tail -n 20 /content/logs/gcp_backup.log

# force a full sync of a finished run (training)
gsutil -m rsync -r $OUT $GCS_BASE/v3_arabmaqamrock_lora/output

# restore a run folder (parent dir MUST exist first)
mkdir -p $OUT
gsutil -m rsync -r $GCS_BASE/v3_arabmaqamrock_lora/output $OUT
```

## 8. Pause for the night / resume next session

```bash
# PAUSE
python train_ctl.py stop
python backup_to_gcp.py --run-name v3_arabmaqamrock_lora --once
gsutil ls -l $GCS_BASE/v3_arabmaqamrock_lora/output/ | tail   # newest ckpt + optimizer.pt

# RESUME (fresh VM): setup (step 2) then restore (step 6) then:
setsid nohup python backup_to_gcp.py --run-name v3_arabmaqamrock_lora \
  > /content/logs/gcp_backup_stdout.log 2>&1 & disown
python train_ctl.py start        # same run name + config → auto-resumes from newest ckpt
```

## 9. Finish a run + push

```bash
gsutil -m rsync -r $OUT $GCS_BASE/v3_arabmaqamrock_lora/output
gsutil -m rsync -r -n $OUT $GCS_BASE/v3_arabmaqamrock_lora/output   # expect no output
python TRAINING_ANALYSIS/generate_plots.py

git add -A
git -c user.name='akbargherbal' -c user.email='akbar.gherbal@gmail.com' \
    commit -m "<message>"
git push origin HEAD
git status --short

# then stop the sidecars
pkill -f 'backup_to_gcp.py|gpu_logger.py'
```

## 10. Gotchas that bite

- **`ai-toolkit` auto-resumes** from the newest checkpoint in the output folder.
  Same run name + same config = resume. To genuinely start over, **archive first**
  (`mv` locally + `gsutil -m mv` in GCS — see `docs/BACKUP_RESTORE.md`) or it
  silently continues the old run.
- **`/content` is ephemeral.** Only GitHub + GCS persist. Don't let a long job run
  without the backup daemon up.
- **Detached vs foreground.** Anything launched with `setsid nohup … & disown`
  outlives the tab; Ctrl+C won't touch it — stop it by name (`pkill -f '<pattern>'`)
  or its `train_ctl.py stop`.
- **Env vars** (`HF_TOKEN`, `GCP_*`) come from `/root/.secrets.env`, staged by the
  launching notebook. A terminal that can't see them means the notebook cell
  hasn't run.
- **`generate.py` runs tracks strictly sequentially** — never start a second
  concurrent inference run (two can OOM the NAR graph); it refuses if training is
  detected (`--allow-concurrent` overrides).
- **`gsutil rsync` is append/update-only (no `-d`)** — remote files are never
  deleted; a local wipe leaves stale remote copies.
- **Don't trust a single `nvidia-smi` "idle"** — confirm `gpu_logger.py` is running
  and check `status.py`.
