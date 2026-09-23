# Backup to GCS, verify, and restore

`backup_to_gcp.py` is the only thing that persists run state — Colab's
`/content` does not survive a VM loss. It runs as a **sidecar** next to training
or generation and mirrors a fixed set of folders to GCS every 15 minutes with
`gsutil rsync` **without `-d`** (append/update only — it never deletes anything
remote). If a pass catches a file mid-write, the next pass re-uploads it once it
stops changing, so a torn upload self-heals.

Every run gets its own prefix, `<base>/<run-name>/`, and a `run_manifest.json`
is written there that refuses to let two different runs share a prefix.
`<base>` = `$GCP_BACKUP_BASE` (exported by the launching notebook) =
`gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning`; override with
`--base gs://…`.

## What gets mirrored

| Mode | Local | GCS (`<base>/<run-name>/`) |
|---|---|---|
| **training** (default) `--run-name akbar_arabic_rock_lora` | `/content/ai-toolkit/output/akbar_arabic_rock_lora/` | `output/` |
| | `/content/logs/` | `logs/` |
| | `agent_notes/` | `agent_notes/` |
| **inference** `--inference` (`--run-name audiocpp_inference`) | `/content/audiocpp_inference/out/` | `out/` |
| | `/content/audiocpp_inference/{prompts,scripts}/` | `prompts/`, `scripts/` |
| | `/content/converter/out/` (the converted LoRA) | `converter/` |
| | `/content/logs/`, `agent_notes/` | `logs/`, `agent_notes/` |
| **watch** `--watch LOCAL[:SUB]` | exactly the folders you name | prefix root, or the given `SUB` |

In training mode the `output/` target waits until its newest file has been
untouched for `--settle-seconds` (default 60) before syncing — except
`loss_log.db` and its `-wal`/`-shm` sidecars, which are perpetually fresh during
a run and would otherwise starve every pass. Inference/watch targets sync
immediately.

## Run it in the background (non-blocking)

`setsid nohup … & disown` detaches the daemon from your terminal so it keeps
running after you close the tab (and Ctrl-C in the tab won't kill it):

- `&` — run in the background, prompt returns immediately.
- `nohup` — ignore `SIGHUP` (sent when a terminal closes).
- `setsid` — start it in its own session, decoupled from the controlling terminal.
- `disown` — drop it from the shell's job table so the shell won't signal it on exit.

```bash
# training
cd /content/maqamrock-yue2-lora-finetuning
setsid nohup python backup_to_gcp.py --run-name akbar_arabic_rock_lora \
  > /content/logs/gcp_backup_stdout.log 2>&1 & disown

# inference workspace
setsid nohup python backup_to_gcp.py --inference \
  > /content/logs/gcp_backup_stdout.log 2>&1 & disown

# an arbitrary folder (see below)
setsid nohup python backup_to_gcp.py --watch /content/my_songs \
  > /content/logs/gcp_backup_stdout.log 2>&1 & disown
```

Confirm it's alive and see its progress:

```bash
pgrep -af backup_to_gcp.py
tail -f /content/logs/gcp_backup.log          # the daemon's own log
```

One pass and exit (handy for cron or a one-off check) — no `& disown` needed:

```bash
python backup_to_gcp.py --run-name akbar_arabic_rock_lora --once
python backup_to_gcp.py --inference --once
```

Preview what it would sync without uploading anything (still needs a base):

```bash
python backup_to_gcp.py --run-name akbar_arabic_rock_lora --dry-run --once
```

## Watching a specific folder (`--watch`)

`--watch LOCAL[:SUB]` (repeatable) **replaces** the mode's default targets with
exactly the folders you name — for mirroring a location the script doesn't know
about. `LOCAL` is `~`-expanded; `SUB` is the remote subfolder under
`<base>/<run-name>/` and defaults to the prefix root for a single `--watch`.
With more than one `--watch`, give each an explicit `:SUB`. With no
`--run-name`, the run name is derived from the first folder's basename:

```bash
# /content/my_songs/*  ->  gs://<base>/my_songs/
python backup_to_gcp.py --watch /content/my_songs

# -> gs://<base>/my_songs/wavs/
python backup_to_gcp.py --watch /content/my_songs:wavs --run-name my_songs

# two targets, each needs its own :SUB
python backup_to_gcp.py --watch /content/a:wavs --watch /content/b:notes --once
```

## Flags

| Flag | Meaning |
|---|---|
| `--run-name NAME` | This run's prefix under `<base>`. Defaults to `akbar_arabic_rock_lora` (training) / `audiocpp_inference` (`--inference`) / the first watched folder (`--watch`). `dataset` is reserved. |
| `--inference` | Use the inference target set instead of training. |
| `--watch LOCAL[:SUB]` | Mirror these folders instead of the mode's targets (repeatable). |
| `--base gs://…` | GCS root; defaults to `$GCP_BACKUP_BASE`. |
| `--interval-minutes N` | Minutes between passes (default 15). |
| `--once` | Run one pass and exit. |
| `--dry-run` | Log the commands, upload nothing. |
| `--settle-seconds N` | Wait for the newest file in the training `output/` target to be this old (default 60). |
| `--exclude REGEX` | Extra `gsutil -x` pattern to skip (repeatable). |
| `--gsutil PATH` | `gsutil` executable (default: from `PATH`). |
| `--log-file PATH` | Log file (default `/content/logs/gcp_backup.log`). |

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
