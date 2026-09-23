---
name: crash-diagnose-and-resume
description: Diagnose why an ai-toolkit LoRA training run stopped and decide whether to auto-resume or hand the user the exact command. Use when run.py is no longer in pgrep, train.log ends in a traceback, or the user asks whether training died.
---

# Crash: diagnose and resume

Training only (`run.py` / `akbar_arabic_rock_lora`). For generation runs, use
`inference-batch-run`.

Sources of truth — read these, don't restate them:
- `docs/PAUSE_RESUME.md` — pause/resume mechanics, GCS restore, checkpoint cadence.
- `docs/BACKUP_RESTORE.md` — restore + archive commands.
- `AGENTS.md` ("Never") — the auto-resume policy. This skill only executes it.

## 1. Confirm the run is actually dead

```bash
pgrep -af run.py
tail -n 60 /content/logs/train.log
python monitor_loss.py /content/ai-toolkit/output/akbar_arabic_rock_lora/loss_log.db
```

The DB gives the last step reached; the log tail carries the cause — a traceback,
or `Job stopped` after a clean interrupt.

## 2. Classify the stop

| Evidence | Verdict |
|---|---|
| `Job stopped` after a kill/Ctrl-C, or `current.md` says a pause was planned | deliberate — never auto-resume |
| Traceback (OOM, CUDA, disk), VM reclaimed, log just ends mid-step | unplanned — candidate |
| You never saw this run going with human approval | hand it to the user |

## 3. Who resumes

Auto-resume yourself only if **all three** hold (AGENTS.md): it was already
running with human approval, the stop was unplanned, and the resume uses the
identical config and run name. Otherwise give the user the exact command in §5
and stop.

Never edit `config/akbar_arabic_rock_lora.yml` to "fix" a crash. A changed
config/hyperparameter is not a resume — archive and start fresh
(`docs/BACKUP_RESTORE.md`).

## 4. Fresh VM? Restore before relaunching

If `/content/ai-toolkit` or the run output folder is gone, the VM was lost:

```bash
bash bootstrap/setup.sh --training > /content/logs/setup.log 2>&1 &   # wait for [ok]
mkdir -p /content/ai-toolkit/output/akbar_arabic_rock_lora
gsutil -m rsync -r \
  gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/akbar_arabic_rock_lora/output \
  /content/ai-toolkit/output/akbar_arabic_rock_lora
```

Then restart both sidecars (`docs/START.md` §4). A ~12 min latent-cache rebuild
on first start is normal, not a stall.

## 5. Relaunch (identical config + run name)

```bash
cd /content/ai-toolkit
python run.py /content/maqamrock-yue2-lora-finetuning/config/akbar_arabic_rock_lora.yml \
  -l /content/logs/train.log
```

Confirm the log prints a "Found step N ... starting from there" line and does not
start at 0. If it starts at 0, stop it and re-check §4.

## 6. Record it

Update `agent_notes/current.md` (overwrite; keep it short): what stopped, cause,
who resumed, from which step.
