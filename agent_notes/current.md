# current

## State @ 2026-10-05 ~17:35 UTC (20:35 Bahrain) — training LIVE; RENAME quran_ahh_r8 -> quran_ahh_r32 tonight

Branch `pron-lora-long-aya`. Run config `config/quran_ahh_r8.yml` = **AR+NAR, rank 32/32,
`ar_kl_weight 0.0`, steps 28467 (3 epochs)** — authority; do not edit hyperparameters.

- **Training running**: `run.py` pid **16301** (detached, started 12:35:11). Log
  `/content/logs/train_quran_ahh.log`. At ~17:20 UTC step ~**12,311 / 28,467 (~43%)**;
  8 checkpoints `_1500…_12000` + `optimizer.pt` + `loss_log.db`, all in GCS.
- User runs until **~23:00 Bahrain (20:00 UTC)**; training won't finish tonight (~02:30 Bahrain).

## TONIGHT: rename `quran_ahh_r8` -> `quran_ahh_r32` (name is misleading: it is rank 32)

The full rename is scripted + tested: `bootstrap/rename_run.py` (dry-run by default; refuses
`--apply` while `run.py` is alive; verified on temp dirs and throwaway GCS prefixes). It:
changes config `name`+`log_dir`, renames `config/quran_ahh_r8.yml` -> `config/quran_ahh_r32.yml`,
moves the local output dir + every checkpoint prefix, **restores ctime order** (resume picks
newest-by-ctime), copies GCS `quran_ahh_r8/` -> `quran_ahh_r32/` (verify, then delete old), and
merges `quran_ahh_r8_rank32/convert` -> `quran_ahh_r32/convert`.

**Do this when you stop (~23:00):**
```bash
cd /content/maqamrock-yue2-lora-finetuning
# 1. stop training cleanly (so the newest save is in GCS):
python train_ctl.py stop --config config/quran_ahh_r8.yml --run-name quran_ahh_r8 --log-name train_quran_ahh
pgrep -af 'run.py.*quran_ahh_r8'        # must be empty
# 2. stop the backup sidecar (it holds the old prefix):
pkill -f 'backup_to_gcp.py --run-name quran_ahh_r8'
# 3. rename (dry-run first if you like; --apply does it):
python bootstrap/rename_run.py --old quran_ahh_r8 --new quran_ahh_r32
python bootstrap/rename_run.py --old quran_ahh_r8 --new quran_ahh_r32 --apply
# 4. restart the backup sidecar on the new name:
setsid nohup python backup_to_gcp.py --run-name quran_ahh_r32 > /content/logs/gcp_backup.log 2>&1 & disown
```
The script ends with a **`ctime check`** line — it must say "resume will pick quran_ahh_r32_<newest>".
If it exits with `ERROR`, do **not** resume; re-run the script.

## Resume next morning — fresh VM (now under the NEW name)

All resume inputs are banked: checkpoints+optimizer+loss_log.db under `…/quran_ahh_r32/output/`;
dataset `quran_ahh_dataset.zip` + `_latent_cache.tar`. `ai-toolkit` auto-resumes from the newest
checkpoint (`training_info.step`).
```bash
git clone https://github.com/akbargherbal/maqamrock-yue2-lora-finetuning.git /content/maqamrock-yue2-lora-finetuning
cd /content/maqamrock-yue2-lora-finetuning && git checkout pron-lora-long-aya
bash bootstrap/setup.sh --training        # needs GCP_BACKUP_BASE, GCP_AHH_DATASET_ZIP, HF_TOKEN; wait for all-[ok]
mkdir -p /content/ai-toolkit/output/quran_ahh_r32
gcloud storage rsync -r "$GCP_BACKUP_BASE/quran_ahh_r32/output" /content/ai-toolkit/output/quran_ahh_r32
gcloud storage cp "$GCP_BACKUP_BASE/quran_ahh_dataset/_latent_cache.tar" /content/
tar -C /content/quran_ahh_dataset/train -xf /content/_latent_cache.tar
setsid nohup python backup_to_gcp.py --run-name quran_ahh_r32 > /content/logs/gcp_backup.log 2>&1 & disown
setsid nohup python gpu_logger.py --out /content/logs/gpu_usage.csv > /content/logs/gpu_logger.log 2>&1 & disown
python train_ctl.py start --config config/quran_ahh_r32.yml --run-name quran_ahh_r32 --log-name train_quran_ahh
grep -m1 'Found step' /content/logs/train_quran_ahh.log   # must NOT say step 0
```

## T4 probe round 1 verdict (2026-10-05, user)

c4500 + c7500 (real AR+NAR), held-out 2:255 both scripts:
`…/audiocpp_inference/out/20261005-154621_quran_pt_probe/`. All "sound like Alhusary";
**best = c7500_simple** (one mistake); **simple > uthmani**; **hard letters (ح، ع) much improved
vs rank-8** but not solved. Not a plateau -> **next try ~step 18000** (convert on the L4 -> bank
to `quran_ahh_r32/convert/` after the rename -> `INFERENCE/quran_pt_probe.py --arms c18000`).

## Remaining after the rename
- Docs-reconciler pass: update the ~10 files referencing `quran_ahh_r8` (`docs/QURAN_AHH_RUN.md`,
  `docs/README.md`, `SOURCE_OF_TRUTH.md`, `bootstrap/setup.sh`, `INFERENCE/*`, the two
  `TRAINING_ANALYSIS/` dirs). Rename `TRAINING_ANALYSIS/quran_ahh_r8_rank32/` -> `.../quran_ahh_r32/`.
- Human blind gate (`ab-blind-eval`) before any merge; `docs/PAUSE_RESUME.md` still uses v2 names.
- `status.py` reports its default run name `akbar_arabic_rock_lora`; real run is now `quran_ahh_r32`.
