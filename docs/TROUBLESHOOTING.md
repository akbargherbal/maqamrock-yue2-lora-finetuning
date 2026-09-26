# Troubleshooting & evaluation checklist

When something looks wrong during **training, inference, fixing, or debugging**,
use this instead of a vibe. It produces one evidence file you can hand to the
agent, and a short scorecard for whether the *agent* behaved.

Not a runbook — for how-to, see `README.md` in this folder. Sources of truth, in
order: the live artifacts below → `DECISIONS.md` → the matching `docs/*` runbook
→ `AGENTS.md` policy.

## 0. Which lane? (pick one, then jump)

| Symptom | Lane | Section |
|---|---|---|
| Training stalled / died / loss looks wrong | Training | §2 |
| A generation came out wrong / batch failed | Inference | §3 |
| Progress might not be saved / VM died | Backup & continuity | §4 |
| "Did the agent do the right thing?" | Agent | §6 |
| Not sure it's even broken | Run §1 first | §1 |

## 1. Capture the evidence bundle first (always)

Paste this **once**, before changing anything. It writes one file; point the agent
at it. (Bracketed `pgrep` patterns avoid matching the shell running this script.)

```bash
cd /content/maqamrock-yue2-lora-finetuning 2>/dev/null
OUT=/content/logs/checkup_$(date -u +%Y%m%d-%H%M%S).txt
{
  echo "== when / host =="; date -u; hostname
  echo; echo "== git =="; git rev-parse --short HEAD 2>/dev/null; git status --short 2>/dev/null | head
  echo; echo "== processes =="; pgrep -af '[r]un\.py|[b]ackup_to_gcp\.py|[g]pu_logger\.py|[c]ontinuity\.py watch' || echo "(none)"
  echo; echo "== train_ctl status =="; python train_ctl.py status 2>&1
  echo; echo "== train.log tail =="; tail -n 60 /content/logs/train.log 2>&1
  echo; echo "== metrics =="; python monitor_loss.py /content/ai-toolkit/output/akbar_arabic_rock_lora/loss_log.db 2>&1 | tail -n 25
  echo; echo "== gpu =="; nvidia-smi 2>&1 | head -n 20
  echo; echo "== gpu csv freshness =="; stat -c '%y  %n' /content/logs/gpu_usage.csv 2>&1; tail -n 3 /content/logs/gpu_usage.csv 2>&1
  echo; echo "== run output =="; ls -lt /content/ai-toolkit/output/akbar_arabic_rock_lora/ 2>&1 | head -n 12
  echo; echo "== logs dir =="; ls -lt /content/logs 2>&1 | head -n 15
} | tee "$OUT"
echo; echo "evidence -> $OUT"
```

Then fill §7 and hand it over. Do **not** restart/stop anything before capturing.

## 2. Training checks

| # | Check | Command | Expected |
|---|---|---|---|
| T1 | Process alive | `pgrep -af '[r]un\.py'` | one `run.py` for this config |
| T2 | train_ctl agrees | `python train_ctl.py status` | "running — pid …" |
| T3 | Step is advancing | `monitor_loss.py …/loss_log.db` twice, ~60 s apart | step **increases**; not stuck |
| T4 | No traceback | `tail -n 60 /content/logs/train.log` | no `Traceback`; last line is newer than your last look |
| T5 | GPU actually working | `nvidia-smi` | the `run.py` pid shows memory + util > 0 |
| T6 | GPU logger fresh | `stat -c %y /content/logs/gpu_usage.csv` | mtime < ~30 s old |
| T7 | Checkpoints landing | `ls -lt /content/ai-toolkit/output/akbar_arabic_rock_lora/` | newest `.safetensors` step grows; `optimizer.pt` present |
| T8 | First-minutes expectation | — | step-0 **sample generation** runs first; `loss_log.db` sits at 0 for minutes. Normal. |
| T9 | Resume, not restart | `grep "starting from" /content/logs/train.log` | "Found step N … starting from there", **not** step 0 |

## 3. Inference checks

| # | Check | Command | Expected |
|---|---|---|---|
| I1 | Batch still alive | `pgrep -af 'generate\.py'` | the batch driver is running (if mid-batch) |
| I2 | Latest output dir | `ls -lt /content/audiocpp_inference/out/ \| head`; `cat /content/audiocpp_inference/out/latest` | a `latest` pointer + per-run dir |
| I3 | Per-run exit | per-run `.log` / `_runs_status.log` in `out/` | `exit=0` for each generated track |
| I4 | LoRA / GGUF staged | `ls /content/audiocpp_inference/models/ /content/converter/out/ 2>&1` | GGUF + converted adapter present |
| I5 | GPU not contended | `nvidia-smi` | nothing else on the GPU (one shared card) |

## 4. Backup & continuity checks

| # | Check | Command | Expected |
|---|---|---|---|
| B1 | Backup daemon up | `pgrep -af '[b]ackup_to_gcp\.py'` | running |
| B2 | Recent GCS object | `gsutil ls -l gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/akbar_arabic_rock_lora/output/ \| tail` | newest mtime within ~15 min of local |
| B3 | Checkpoint is in GCS | same as B2 | newest `.safetensors` **and** `optimizer.pt` present, sizes match local |
| B4 | GPU logger up | `pgrep -af '[g]pu_logger\.py'` | running (skip on a CPU-only VM) |
| B5 | Session backup loop | `pgrep -af '[c]ontinuity\.py watch'` | running; else `vm-continuity watch --interval-minutes 15` |
| B6 | Env staged | `env \| grep -E 'GCP_BACKUP_BASE\|GCP_DATASET_PATH\|HF_TOKEN'` | set (from the notebook) |

## 5. Environment checks (fresh / reclaimed VM)

| # | Check | Command | Expected |
|---|---|---|---|
| E1 | GPU present | `nvidia-smi` | shows a GPU (a CPU-only VM can't train/infer) |
| E2 | Dataset present | `ls /content/yue2_dataset/.bootstrap_complete` | marker exists |
| E3 | ai-toolkit present | `ls /content/ai-toolkit/run.py` | exists |
| E4 | Run output restored | `ls /content/ai-toolkit/output/akbar_arabic_rock_lora/` | newest checkpoint restored from GCS before relaunch |

## 6. Agent-behavior scorecard

Answer **Yes / No / N/A** with the evidence (a command or a quote). This is the
part that turns "the agent seemed off" into something specific.

| # | Question | Evidence (paste) | Y/N |
|---|---|---|---|
| A1 | Did it read `DECISIONS.md` / the matching runbook before acting? | | |
| A2 | Training launched via `train_ctl.py` (not a bare `python run.py`)? | | |
| A3 | Did it run `nvidia-smi` before any GPU-heavy work? | | |
| A4 | Did it distinguish a **deliberate** stop (`Job stopped`) from a **crash**? | | |
| A5 | If it auto-resumed: same config **and** run name, with crash evidence — or did it ask? | | |
| A6 | Did it claim a `current.md` write **and** actually write+verify it? (`grep` the file) | | |
| A7 | Did it edit a run config or the dataset without stopping to ask? | | |
| A8 | Were handed-over commands given with mode + log path + stop command? | | |
| A9 | Did it **verify** paths/commands against the repo, or assert from memory? | | |
| A10 | Did it avoid blocking the session (slow work backgrounded with a log)? | | |
| A11 | For "is it backed up?", did it compare real timestamps rather than assume? | | |
| A12 | Did it change the config/run-name and still call it a resume? | | |

## 7. Classify → decide

Fill the row that matches; each points at the next action.

| Expected vs actual | Likely cause | Next |
|---|---|---|
| T1/T2 fail, log ends `Job stopped` | deliberate stop / clean end | nothing to fix; restart only if intended |
| T1/T2 fail, log ends in `Traceback` | crash (OOM/CUDA/disk) | §2 T4 for the cause; resume per `skills/crash-diagnose-and-resume` |
| T3 stuck, T2 alive | stalled step / sample gen / deadlock | capture T4 + T5; check the GPU; don't kill blindly |
| T5 low/zero, T2 alive | not using the GPU | check the log for device errors; confirm nothing else holds the GPU |
| T6 stale | `gpu_logger.py` dead | restart it (`docs/START.md` §4) |
| T7 missing while step > 250 | save issue | check `save.*` in config; check disk |
| B2/B3 stale | backup daemon dead | restart it (`docs/BACKUP_RESTORE.md`) |
| A-row = No | process/agent issue | note it here; it's evidence for the next session |

## 8. Hand-off block (copy this, fill it, give it to the agent)

```
Symptom (one line):
Lane:                # training | inference | backup | env | agent
Started when / last known good:
Evidence file:       /content/logs/checkup_<...>.txt
What I already tried:
What I expect should happen:
Agent scorecard:     # paste the §6 rows that are "No"
```
