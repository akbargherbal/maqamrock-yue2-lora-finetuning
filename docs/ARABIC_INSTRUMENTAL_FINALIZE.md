# Finalization checklist — `arabic_instrumental_lora`

_Run-specific completion checklist. The generic version is [FINAL_BACKUP.md](FINAL_BACKUP.md);
backup mechanics are in [BACKUP_RESTORE.md](BACKUP_RESTORE.md)._

Purpose: once training ends, get **every artifact to GCS** and **every doc to GitHub**, then stop
paying for the VM. Tick in order; each item names the check that proves it.

```
<base> = gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning
<run>  = arabic_instrumental_lora
<out>  = /content/ai-toolkit/output/arabic_instrumental_lora
```

Run shape: 5500/5500 steps · save_every 250 → **22 numbered checkpoints (250…5500)** ·
`max_step_saves_to_keep: 12` → only the newest 12 stay local, **all 22 must be in GCS** ·
plus the final adapter `<run>.safetensors` · 0 samples (`disable_sampling: true`).

---

## 0. Pre-finish (while the last steps run)

```bash
cd /content/maqamrock-yue2-lora-finetuning
pgrep -af 'backup_to_gcp.py|gpu_logger.py'      # expect our two pids (19244 / 19245)
df -h /content | tail -1                        # expect >100 GB free
gsutil ls "$GCP_BACKUP_BASE/" | head -3          # expect listing, no auth error
gh auth status                                   # expect: akbargherbal
```

- [ ] our backup daemon + gpu_logger alive (ignore the foreign `plumbing/backup_to_gcp.py`, pid 2667)
- [ ] disk ≥ 2 GB free (final save ~115 MB + optimizer)
- [ ] GCS + GitHub reachable

## 1. Confirm the run ended cleanly (not crashed)

```bash
pgrep -af 'run.py.*arabic_instrumental_lora'      # expect: nothing
tail -n 40 /content/logs/train.log                 # expect "Job stopped" / final save, no traceback
grep -nE '^Traceback|^[A-Za-z_.]*Error|CUDA error|OOM during training step 2/3|3/3' \
  /content/logs/train.log | tail -5                # expect: only "skipping batch 1/3" lines
nvidia-smi --query-gpu=memory.used --format=csv,noheader   # expect ~0 MiB
```

- [ ] `run.py` gone; `train.log` ends with the final save, not a traceback
- [ ] no `2/3` or `3/3` consecutive-OOM abort (expected: 129× `1/3`, all isolated)
- [ ] GPU freed

## 2. Verify the FINAL local artifacts

```bash
ls -lh <out>/ | tail -6
ls <out>/*_00000*.safetensors | wc -l      # expect 12 (rotation cap; 22 exist up to GCS)
ls -lh <out>/arabic_instrumental_lora.safetensors   # final adapter, ~115 MB
ls -lh <out>/optimizer.pt <out>/loss_log.db <out>/config.yaml
python monitor_loss.py <out>/loss_log.db --history 5 --total-steps 5500
ls <out>/tensorboard/*/events.out.tfevents.* | head -1
```

- [ ] final adapter `arabic_instrumental_lora.safetensors` exists
- [ ] 12 numbered checkpoints local (250…5000 rotated out as designed — they are in GCS)
- [ ] `optimizer.pt`, `loss_log.db` (+`-wal`/`-shm`), `config.yaml`, tensorboard event file
- [ ] `monitor_loss.py` reports the last step ≈ 5499/5500

## 3. Force the final sync (do not wait for the 5-min daemon)

```bash
cd /content/maqamrock-yue2-lora-finetuning
. /root/.secrets.env
python backup_to_gcp.py --run-name arabic_instrumental_lora --once
tail -n 8 /content/logs/gcp_backup_stdout.log
```

- [ ] exit 0 and `pass complete: 3/3 folders synced`
- [ ] (fallback if the daemon misbehaves: `gsutil -m rsync -r <out> "$GCP_BACKUP_BASE/<run>/output"`)

## 4. Verify remote == local — the check that actually matters

```bash
. /root/.secrets.env
B="$GCP_BACKUP_BASE/arabic_instrumental_lora"
gsutil ls "$B/output/"*_00000*.safetensors | wc -l      # expect 22
gsutil ls "$B/output/arabic_instrumental_lora.safetensors"   # expect present
gsutil ls -l "$B/output/optimizer.pt" "$B/output/loss_log.db" "$B/output/config.yaml"
gsutil -m rsync -r -n <out> "$B/output" | head          # expect NO transfers
```

- [ ] **22** numbered checkpoints in GCS (not 12) + the final adapter
- [ ] `optimizer.pt` / `loss_log.db` sizes match local
- [ ] dry-run rsync prints no files to copy
- [ ] last checkpoint's mtime is after the final save

**Record the deliverable hash** (goes in the run record and the future `loras/` row):

```bash
sha256sum <out>/arabic_instrumental_lora.safetensors | tee /content/logs/final_adapter_sha256.txt
gsutil cat "$B/output/arabic_instrumental_lora.safetensors" | sha256sum   # must match
```

- [ ] local and remote sha256 identical

## 5. Persist everything the daemon does NOT mirror

`backup_to_gcp.py` mirrors `output/`, `logs/`, `agent_notes/` only. These live outside it:

```bash
B="$GCP_BACKUP_BASE/arabic_instrumental_lora"
gsutil -m cp /content/eval_holdout/arabic_instrumental/HOLDOUT.json "$B/eval_holdout/"
gsutil -m cp /tmp/ai_manifest.json "$B/eval_holdout/dataset_manifest.json"
gsutil du -s "$B/eval_holdout"        # expect ~49,961,289 B + manifest
```

- [ ] eval holdout still complete on GCS: 17 objects (8 mp3 + 8 txt + HOLDOUT.json)
- [ ] dataset manifest archived next to it
- [ ] (after the eval renders exist) the eval prompts JSON, `batch_manifest.json`, converted
      adapters and 192k mp3 review copies are pushed under `<base>/<run>/eval/<stage>/`

## 6. Docs + repo

Update the files that are now factually stale:

| file | change |
|---|---|
| `docs/README.md:13` | "configs written, **not launched**" → finished, 5500/5500 |
| `docs/ARABIC_INSTRUMENTAL_LORA_PLAN.md` | status line: launched/finished; note the 13-track OOM coverage gap and the corrected VRAM figure (v3 was also ~79 GB — `TRAINING_ANALYSIS/ANALYSIS.md:71-79`) |
| `PROGRESS.md` | completion entry: steps, final losses, artifacts, GCS verified |
| `docs/ARABIC_INSTRUMENTAL_EVAL_PLAN.md` | no change (already pushed) |
| `agent_notes/current.md` | rewritten to "finished, eval pending" |
| `SOURCE_OF_TRUTH.md` / `RECONCILIATION_LOG.md` | run row + reconciler pass |

```bash
cd /content/maqamrock-yue2-lora-finetuning
git status --short
git add -A
git -c user.name='akbargherbal' -c user.email='akbargherbal@users.noreply.github.com' \
    commit -m "run: arabic_instrumental_lora finished 5500/5500 + GCS verified"
git push origin HEAD
git rev-list --left-right --count origin/main...HEAD   # expect: 0	0
```

- [ ] `docs-reconciler` pass run and logged (mechanical extraction first; edits proposed)
- [ ] tree clean, `HEAD == origin/main`
- [ ] `agent_notes/current.md` says "finished · eval pending" and carries the eval plan pointer

## 7. Housekeeping

```bash
pkill -f 'backup_to_gcp.py --run-name arabic_instrumental_lora'
pkill -f 'gpu_logger.py'
vm-continuity status        # leave running until the session truly ends
```

- [ ] sidecars stopped **only after** §4 passes
- [ ] local `<out>/` left in place (source of truth until verified; VM is ephemeral anyway)
- [ ] `vm-continuity` healthy; session notes shipped

---

## "Done" means all of these

- [ ] `run.py` exited with no traceback; GPU free
- [ ] local: 12 numbered + final adapter + optimizer.pt + loss_log.db + config + tensorboard
- [ ] GCS: **22 numbered + final adapter**, optimizer/db sizes match, dry-run rsync clean
- [ ] final adapter sha256 recorded and identical local↔GCS
- [ ] eval holdout + manifest + dataset manifest on GCS
- [ ] repo: docs updated, `HEAD == origin/main`, tree clean
- [ ] sidecars stopped; final sentence to the user states whether the last backup is current

## Do not

- [ ] don't delete the local run folder before §4 passes
- [ ] don't rebuild `audiocpp_cli` — check `gs://…/arabmaqrock/binaries/index.json` first
- [ ] don't start eval GPU work until `nvidia-smi` shows no `run.py`
- [ ] don't merge/convert/register anything before the listening verdict
