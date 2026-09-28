# current

## Stage the LoRAs for `batch_36_songs.json` (2026-09-28)

The manifest uses three adapter aliases: `v2` (style pair), `qfinal_a0.3`,
`qfinal_a0.5`. GCS has all three under `loras/audio_cpp/`. Local check just now:
the `v2` style pair is **already present** in `/content/converter/out/`; the two
`qfinal_a0.*/` subdirs are **missing** and must be pulled. The `style` rsync is
idempotent (no-op if current), so the block below stages all three.

terminal: foreground — you watch it; Ctrl+C stops it. Idempotent: re-run the
same block to finish/resume (gsutil skips objects already matching). ~280 MiB
(4 files), no GPU.

```bash
export GCP_BACKUP_BASE=gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning
mkdir -p /content/converter/out
gsutil -m rsync -r "$GCP_BACKUP_BASE/loras/audio_cpp/style" /content/converter/out
gsutil -m cp -r "$GCP_BACKUP_BASE/loras/audio_cpp/pron/qfinal_a0.3" /content/converter/out/
gsutil -m cp -r "$GCP_BACKUP_BASE/loras/audio_cpp/pron/qfinal_a0.5" /content/converter/out/
```

Verify (6 files must all list):

```bash
ls /content/converter/out/akbar_arabic_rock_lora_{ar,nar}.safetensors \
   /content/converter/out/qfinal_a0.3/akbar_arabic_rock_lora_{ar,nar}.safetensors \
   /content/converter/out/qfinal_a0.5/akbar_arabic_rock_lora_{ar,nar}.safetensors
```

`generate.py` preflight existence-checks every referenced pair before any GPU
work, so a missing file fails fast (before the batch starts).

## Run the batch (after the LoRAs are staged)

terminal: detached — survives Ctrl+C / closing the tab.
log: the run's own `_driver.log`, mirrored to `/content/logs/batch_36_songs.log`.
Full output dir: `/content/audiocpp_inference/out/batch_36_songs`.
stop: `pkill -f 'generate.py manifests/batch_36_songs.json'`
resume: re-run the exact same command (completed tracks are skipped).
Ctrl+C / closing the tab will NOT stop it.

```bash
mkdir -p /content/logs
setsid nohup python INFERENCE/generate.py manifests/batch_36_songs.json \
  --out-dir /content/audiocpp_inference/out/batch_36_songs \
  > /content/logs/batch_36_songs.log 2>&1 & disown
```

Progress: `tail -f /content/audiocpp_inference/out/batch_36_songs/_driver.log`
(or `tail -f /content/audiocpp_inference/out/latest/_driver.log`).

## Back up to GCS every 5 minutes (detached daemon)

terminal: detached — survives Ctrl+C / closing the tab.
log: `/content/logs/gcp_backup_stdout.log` (stdout) + `/content/logs/gcp_backup.log`
(daemon's own pass log).
stop: `pkill -f backup_to_gcp.py`
resume: re-run the exact same command (rsync is append/update-only, nothing is
ever deleted remotely).
Ctrl+C / closing the tab will NOT stop it.

`--inference` mirrors `/content/audiocpp_inference/{out,prompts,scripts}` +
`/content/logs` + `agent_notes/` to
`gs://…/OSTRIS_Arabic_Suno_Finetuning/audiocpp_inference/`. Interval default is
already 5; passed explicitly for clarity.

```bash
export GCP_BACKUP_BASE=gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning
cd /content/maqamrock-yue2-lora-finetuning
setsid nohup python backup_to_gcp.py --inference --interval-minutes 5 \
  > /content/logs/gcp_backup_stdout.log 2>&1 & disown
```

Confirm alive / watch progress:

```bash
pgrep -af backup_to_gcp.py
tail -f /content/logs/gcp_backup.log
```

## Earlier fix (2026-09-28)

`generate.py` had an ASCII-only `name` regex; now `^[^\W_][\w-]*$` accepts
Unicode/Arabic names (spaces/dots/slashes still rejected). `batch_36_songs.json`
unchanged; dry-run validates 36 songs / 36 tracks. Tests + `docs/INFERENCE.md`
updated; reconciler pass = 0 new drift.
