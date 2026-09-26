# Final backup & push — run completion checklist

> **Status: COMPLETED for v2 on 2026-09-20.** v2 reached 3000/3000 and every
> step here was run and passed — artifacts on disk and in GCS (dry-run rsync
> showed no diffs), docs pushed, tree clean. Kept as the **reusable completion
> checklist for any future run**; the "expected end time" and sidecar pids below
> are v2-specific artifacts of when this was written and will differ next time.

Run: `akbar_arabic_rock_lora` (v2, lyric-conditioned captions).
Background/format: [BACKUP_RESTORE.md](BACKUP_RESTORE.md) and
[PAUSE_RESUME.md](PAUSE_RESUME.md).

`<base>` = `gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning`
`<run>`  = `akbar_arabic_rock_lora`
`<out>`  = `/content/ai-toolkit/output/akbar_arabic_rock_lora`

v2 forecast (written at 11:53 UTC, step 2750): **~12:08 UTC** for the final step,
then the step-3000 sample event and the final save. It actually finished
**~12:23 UTC** on 2026-09-20.

---

## 0. Pre-finish (while it's still running)

- [ ] Sidecars are running: `pgrep -af 'backup_to_gcp.py|gpu_logger.py'`
      (expected: `backup_to_gcp.py` pid 15941, `gpu_logger.py` pid 15942).
- [ ] Disk has room for the final save (~1 GB): `df -h /content`.
- [ ] GCS reachable and GH auth live:
      `gsutil ls <base>/ | head`, `gh auth status`.

## 1. Confirm the run ended cleanly

```bash
pgrep -af 'run.py.*akbar_arabic_rock_lora'          # expect: nothing
tail -n 40 /content/logs/train.log                   # expect no traceback
grep -nE '^Traceback|^[A-Za-z_.]*Error|CUDA error|out of memory' \
  /content/logs/train.log | tail                   # expect: empty
```
- [ ] `run.py` gone, GPU freed (`nvidia-smi` → ~0 MiB).
- [ ] No traceback. (Note: `grep -i error` false-matches the config's prompt
      text embedded in the log — anchor the pattern as above.)

## 2. Verify the FINAL local artifacts

Expected in `<out>/` (this is exactly what a finished run looks like — matches
v1's archive):

| artifact | expected |
|---|---|
| numbered checkpoints | `_000000250` … `_000002750` (11 files, ~112 MB each) |
| **final adapter** | `akbar_arabic_rock_lora.safetensors` |
| optimizer state | `optimizer.pt` (~114 MB) |
| metrics | `loss_log.db` (+ `-wal`/`-shm`) |
| config | `config.yaml` (auto-saved, v2 hyperparams) |
| samples | `samples/*.mp3` = **52** (13 events × 4: steps 0,250,…,3000) |
| tensorboard | `tensorboard/<ts>/events.out.tfevents.*` |

```bash
ls -la <out>/
ls <out>/*.safetensors | wc -l          # expect 12 (11 numbered + final)
ls <out>/samples/*.mp3 | wc -l          # expect 52
python monitor_loss.py <out>/loss_log.db # expect latest step ~2999, 4 metrics
```
- [ ] 12 `.safetensors`, `optimizer.pt`, `config.yaml`, `loss_log.db`, 52 samples.
- [ ] `max_step_saves_to_keep: 12`: if a numbered `_000003000` appears and
      `_000000250` gets rotated out locally, that's fine — 250 is already in GCS
      (append-only) and local≠remote supersets are okay.

## 3. Force a final GCS sync (do NOT wait for the 5-min daemon)

```bash
gsutil -m rsync -r <out> <base>/<run>/output
```
- [ ] Sync exit 0. (Files are closed after the run exits, so no mid-write torn
      uploads; the daemon's settle logic only matters *during* a run.)

## 4. Verify remote == local (the one that actually matters)

```bash
gsutil ls <base>/<run>/output/*.safetensors | wc -l        # >= 12
gsutil ls <base>/<run>/output/samples/*.mp3 | wc -l        # 52
gsutil ls -l <base>/<run>/output/optimizer.pt <base>/<run>/output/loss_log.db \
             <base>/<run>/output/config.yaml
# dry-run rsync: any output/transfer = NOT fully synced
gsutil -m rsync -r -n <out> <base>/<run>/output
tail -n 20 /content/logs/gcp_backup.log
```
- [ ] Checkpoint count ≥ 12 and the **final** `akbar_arabic_rock_lora.safetensors`
      is present.
- [ ] 52 samples remote.
- [ ] Dry-run rsync prints **no** files to copy.
- [ ] `optimizer.pt` / `loss_log.db` sizes match local.
- [ ] `run_manifest.json` present at `<base>/<run>/`, no errors in the daemon log.

> **If the VM dies before this step:** the last 5-min daemon pass is the
> fallback — resume from the newest checkpoint in GCS (see PAUSE_RESUME.md), or
> just accept the ~≤5 min of steps lost. Once the run is *done*, there is no
> "next checkpoint", so a final manual sync is not optional.

## 5. Finalize docs and push to GitHub

```bash
cd /content/maqamrock-yue2-lora-finetuning
python TRAINING_ANALYSIS/generate_plots.py     # final plots
# edit the docs, then:
git add -A
git -c user.name='akbargherbal' -c user.email='akbar.gherbal@gmail.com' \
    commit -m "<final analysis + progress>"
git push origin HEAD
git status --short
git rev-list --left-right --count origin/main...HEAD   # expect: 0	0
```
- [ ] `TRAINING_ANALYSIS/ANALYSIS.md` finalized: drop the **IN PROGRESS** banner,
      full table to 3000, final charts, observations, next steps.
- [ ] `PROGRESS.md`: completion entry (3000/3000, final losses incl. `ar_kl`,
      artifacts + GCS verified).
- [ ] `DECISIONS.md`: add only if a genuinely new durable insight (e.g. v2's
      `ar_kl` trajectory vs v1).
- [ ] `agent_notes/current.md` refreshed (git-ignored; GCS-mirrored — no GitHub).
- [ ] `git push` exit 0; working tree clean; `HEAD == origin/main`.
- [ ] (Local git identity is unset on a fresh VM — pass `-c user.name/-c
      user.email` per commit, matching the repo author.)

## 6. Post-run housekeeping

- [ ] **Only after §4 and §5 pass:** stop the sidecars:
      `kill 15941 15942` (or `pkill -f 'backup_to_gcp.py|gpu_logger.py'`).
- [ ] Leave local `<out>/` in place — it's the source of truth until the sync is
      verified, and the VM is ephemeral anyway.
- [ ] Optional (separate task, not required): inference/eval comparing base vs
      final LoRA, e.g. against `INFERENCE/evaluation_alharith.json` and the
      held-out set. v1 kept this under `output/eval_alharith/`.

---

## "Done" means all of these

- [ ] `run.py` exited, no traceback
- [ ] local: 12 checkpoints + final + optimizer.pt + config + loss_log.db + 52 samples
- [ ] GCS: dry-run rsync shows no diffs; counts/sizes match
- [ ] GitHub: `HEAD == origin/main`, clean tree
- [ ] `TRAINING_ANALYSIS/ANALYSIS.md` finalized + `PROGRESS.md` completion entry pushed
- [ ] sidecars stopped

## Known gotchas (from this session)

- `gsutil rsync` is **append-only (no `-d`)** → a local wipe/supersede leaves
  remote files behind; delete remote explicitly if needed (bit us with 4 stale
  smoke-test samples).
- Daemon lag: a *just-finished* sample/checkpoint may miss the current 5-min
  pass → **force a sync** rather than assume.
- `generate_plots.py`'s "recent rate"/ETA line can read too pessimistic if a
  sample pause sits in its last-100 window; use the median in this doc.
- Training is launched detached via `train_ctl.py`, which resets SIGINT in the
  child so `train_ctl.py stop` (SIGINT) is the clean, checkpoint-safe stop.
