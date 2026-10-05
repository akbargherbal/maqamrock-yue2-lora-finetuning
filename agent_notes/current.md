# current

## State @ 2026-10-05 ~17:20 UTC (20:20 Bahrain) — `quran_ahh_r8` REVISED training LIVE; resume READY

Branch `pron-lora-long-aya` @ `91716a9`. Config `config/quran_ahh_r8.yml` = **AR+NAR, rank
32/32, `ar_kl_weight 0.0`, steps 28467 (3 epochs)** — authority; do not edit.

- **Training running**: `run.py` pid **16301** (detached, started 12:35:11). Log
  `/content/logs/train_quran_ahh.log`.
- **Progress**: ~**12,311 / 28,467 (~43%)** at 17:18 UTC; ~0.73 steps/s → **won't finish
  tonight** (ETA ~23:30 UTC = 02:30 Bahrain). By bedtime (20:00 UTC) ≈ step ~19,400; c18000
  save lands ~19:00 UTC.
- **Checkpoints (rank 32)**: `_1500 … _12000` (**8**) + `optimizer.pt` (**step 12000**, matches)
  + `loss_log.db` — local + GCS. Next save = 13500.
- Sidecars: `backup_to_gcp.py` (pid 13044, **5-min passes**, last 17:17:52Z 3/3 synced) +
  `gpu_logger.py` (pid 13214). `vm-continuity status`: `state=OK` (pid 6120).

## Resume next morning — VERIFIED 2026-10-05 17:18 UTC

In place: **8 checkpoints (1500–12000) + `optimizer.pt` + `loss_log.db` + `config.yaml`** in
GCS `…/quran_ahh_r8/output/`; dataset `quran_ahh_dataset.zip` (3.97 GB) and latent cache
`quran_ahh_dataset/_latent_cache.tar` (737 MB) banked. `ai-toolkit` auto-resumes from the newest
checkpoint (reads `training_info.step`), so a fresh VM + restored output prefix + same config
continues. **Stop cleanly first** so the newest save is in GCS (or it dies mid-run — last
backed-up checkpoint, ≤5 min old, is still fine).

**Pause tonight (you type):**
```bash
cd /content/maqamrock-yue2-lora-finetuning
python train_ctl.py stop --config config/quran_ahh_r8.yml --run-name quran_ahh_r8 --log-name train_quran_ahh
python backup_to_gcp.py --run-name quran_ahh_r8 --once     # confirm newest ckpt + optimizer.pt in GCS
```

**Resume (fresh VM, next morning):**
```bash
# env must carry GCP_BACKUP_BASE, GCP_AHH_DATASET_ZIP, HF_TOKEN (notebook cell / /root/.secrets.env)
git clone https://github.com/akbargherbal/maqamrock-yue2-lora-finetuning.git /content/maqamrock-yue2-lora-finetuning
cd /content/maqamrock-yue2-lora-finetuning && git checkout pron-lora-long-aya
bash bootstrap/setup.sh --training        # restores env + AHH dataset; wait for the all-[ok] verify (9489 train pairs)

# restore the run output into the exact path (mkdir parent first):
mkdir -p /content/ai-toolkit/output/quran_ahh_r8
gcloud storage rsync -r "$GCP_BACKUP_BASE/quran_ahh_r8/output" /content/ai-toolkit/output/quran_ahh_r8

# skip the ~50 min re-encode — untar the banked cache over the dataset:
gcloud storage cp "$GCP_BACKUP_BASE/quran_ahh_dataset/_latent_cache.tar" /content/
tar -C /content/quran_ahh_dataset/train -xf /content/_latent_cache.tar

# sidecars (detached):
setsid nohup python backup_to_gcp.py --run-name quran_ahh_r8      > /content/logs/gcp_backup.log 2>&1 & disown
setsid nohup python gpu_logger.py     --out /content/logs/gpu_usage.csv > /content/logs/gpu_logger.log 2>&1 & disown

# launch (SAME config + run name = resume):
python train_ctl.py start --config config/quran_ahh_r8.yml --run-name quran_ahh_r8 --log-name train_quran_ahh
```
Watch `train_quran_ahh.log` for a **`Found step 12000`-style line, not step 0**. Do not restore
the old rank-8 output prefix; do not change any hyperparameter.

## T4 probe — round 1 verdict (2026-10-05, user)

Rendered **c4500 + c7500** (real AR+NAR), held-out 2:255 both scripts: `…/audiocpp_inference/
out/20261005-154621_quran_pt_probe/` (GCS 16:05Z). All tracks "sound like Alhusary"; **best =
`c7500_simple`** (one mistake); **simple > uthmani**; **hard letters (ح، ع) much improved vs
rank-8** but not solved. Not a plateau → **next try ~step 18000** (recipe below). T4 disconnected.

```bash
# convert on the L4 (CPU), then bank; repeat per checkpoint step S:
mkdir -p /content/converter/out
gcloud storage cp "$GCP_BACKUP_BASE/audiocpp_inference/converter/convert_aitoolkit_yue2_lora.py" /content/converter/out/
python /content/converter/out/convert_aitoolkit_yue2_lora.py \
  /content/ai-toolkit/output/quran_ahh_r8/quran_ahh_r8_00000<S>.safetensors \
  --out-dir /content/conversion/quran_ahh_r8_rank32/c<S> --stem quran_ahh_r8
gcloud storage rsync -r /content/conversion/quran_ahh_r8_rank32 "$GCP_BACKUP_BASE/quran_ahh_r8_rank32/convert"
```
```bash
# on a fresh T4: setup.sh --inference, then (detached; ~26 min for 4 tracks):
python INFERENCE/quran_pt_probe.py --prefix quran_ahh_r8_rank32/convert --arms c18000 --dry-run
setsid nohup python INFERENCE/quran_pt_probe.py --prefix quran_ahh_r8_rank32/convert --arms c18000 \
  > /content/logs/quran_pt_probe_r32.log 2>&1 & disown
```
Base (no-LoRA) reference already exists: `…/out/20261005-072738_quran_pt_probe/base_*.wav`.

## GCS layout (2026-10-05)

- **Live revised run** `…/quran_ahh_r8/` = `output/`, `logs/`, `agent_notes/`, `run_manifest.json`.
- **Revised adapters** `…/quran_ahh_r8_rank32/convert/{c4500,c7500}/` (rank 32, AR+NAR).
- **Archive** `…/archive/quran_ahh_r8_rank8_aronly/` = OLD rank-8 `output/` + `convert/`. Do not
  use any rank-8 adapter or output prefix with the revised config.

## Open items
- Human blind gate (`ab-blind-eval`) before any merge.
- Only 4 metric keys; `additional_model_loss` == `loss/ar_ce` (duplicate), so the NAR term shows
  only as the `loss/loss − ar_ce` residual — see `TRAINING_ANALYSIS/quran_ahh_r8_rank32/ANALYSIS.md`.
- `docs/PAUSE_RESUME.md` still uses v2 example names; `docs/QURAN_AHH_RUN.md` still points at the
  old rank-8 `TRAINING_ANALYSIS/quran_ahh_r8/`.
- `status.py` reports its default run name `akbar_arabic_rock_lora`; actual run is `quran_ahh_r8`.
