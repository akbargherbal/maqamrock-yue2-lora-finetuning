# Backup to GCS, verify, and restore

`backup_to_gcp.py` is the only thing that persists run state — Colab's
`/content` does not survive. It runs as a sidecar and mirrors, every 15 minutes:

| Local | GCS (`<base>/akbar_arabic_rock_lora/`) |
|---|---|
| `/content/ai-toolkit/output/akbar_arabic_rock_lora/` | `output/` |
| `/content/logs/` | `logs/` |
| `/content/maqamrock-yue2-lora-finetuning/agent_notes/` | `agent_notes/` |

where `<base>` = `$GCP_BACKUP_BASE` =
`gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning`.

It uses `gsutil rsync` **without `-d`** (append/update only, never deletes
remote) and waits for writes to settle before syncing, except for `loss_log.db`
and its `-wal`/`-shm` sidecars (perpetually fresh during a run).

## Verify a backup

Don't assume — compare what's remote against local:

```bash
gsutil ls -l gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/akbar_arabic_rock_lora/output/ | tail
ls -la /content/ai-toolkit/output/akbar_arabic_rock_lora/
tail -n 20 /content/logs/gcp_backup.log
```

## Restore

The destination's parent directory must exist first — `gsutil rsync` aborts with
*"does not name a directory"* if it doesn't:

```bash
mkdir -p /content/ai-toolkit/output/akbar_arabic_rock_lora
gsutil -m rsync -r \
  gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/akbar_arabic_rock_lora/output \
  /content/ai-toolkit/output/akbar_arabic_rock_lora
```

## Starting a genuinely new run (archive the old one)

`ai-toolkit` auto-resumes from any checkpoints in the output folder, and the
backup manifest only refuses to mix **different** run names — so a same-name
relaunch would silently continue the old run. To actually start over, archive
the old output under a new suffix, locally **and** in GCS:

```bash
# local
mv /content/ai-toolkit/output/akbar_arabic_rock_lora \
   /content/ai-toolkit/output/akbar_arabic_rock_lora_<suffix>

# GCS (gsutil mv renames the prefix)
gsutil -m mv \
  gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/akbar_arabic_rock_lora \
  gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/akbar_arabic_rock_lora_<suffix>
```

Then restart the backup daemon so it writes a **fresh** `run_manifest.json` at
the now-clean `akbar_arabic_rock_lora/` prefix:

```bash
pkill -f 'backup_to_gcp.py' ; sleep 2
cd /content/maqamrock-yue2-lora-finetuning
setsid nohup python backup_to_gcp.py --run-name akbar_arabic_rock_lora \
  > /content/logs/gcp_backup_stdout.log 2>&1 & disown
```

Precedent: the killed 60s-window run is archived as
`akbar_arabic_rock_lora_crop60_killed`.
