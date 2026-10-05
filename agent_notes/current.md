# current

## State @ 2026-10-05 ~18:50 UTC (21:50 Bahrain) — training LIVE (56.8%); rename DEFERRED

Branch `pron-lora-long-aya`. Run config `config/quran_ahh_r8.yml` = **AR+NAR, rank 32/32,
`ar_kl_weight 0.0`, steps 28467 (3 epochs)** — authority; do not edit hyperparameters.
The `r8` in the name is a **misnomer (it is rank 32)** — see "Deferred rename" below.

- **Training running**: `run.py` pid **16301** (detached, started 12:35:11). Log
  `/content/logs/train_quran_ahh.log`. At ~18:46 UTC step ~**16,158 / 28,467 (56.8%)**;
  **10** checkpoints `_1500…_15000` + `optimizer.pt` (step 15000) + `loss_log.db`, all in GCS.
  Next save = **16,500** (~18:54 UTC / 21:54 Bahrain).
- ETA to 28,467 ~**02:26 Bahrain**; user stops ~23:00 Bahrain. Live snapshot:
  `TRAINING_ANALYSIS/quran_ahh_r8_rank32/ANALYSIS.md`.

## Resume next morning — fresh VM (name unchanged: `quran_ahh_r8`)

All resume inputs banked: checkpoints+optimizer+loss_log.db under `…/quran_ahh_r8/output/`;
dataset `quran_ahh_dataset.zip` + `_latent_cache.tar`. `ai-toolkit` auto-resumes from the newest
checkpoint (`training_info.step`).
```bash
git clone https://github.com/akbargherbal/maqamrock-yue2-lora-finetuning.git /content/maqamrock-yue2-lora-finetuning
cd /content/maqamrock-yue2-lora-finetuning && git checkout pron-lora-long-aya
bash bootstrap/setup.sh --training        # needs GCP_BACKUP_BASE, GCP_AHH_DATASET_ZIP, HF_TOKEN; wait for all-[ok]
mkdir -p /content/ai-toolkit/output/quran_ahh_r8
gcloud storage rsync -r "$GCP_BACKUP_BASE/quran_ahh_r8/output" /content/ai-toolkit/output/quran_ahh_r8
gcloud storage cp "$GCP_BACKUP_BASE/quran_ahh_dataset/_latent_cache.tar" /content/
tar -C /content/quran_ahh_dataset/train -xf /content/_latent_cache.tar
setsid nohup python backup_to_gcp.py --run-name quran_ahh_r8 > /content/logs/gcp_backup.log 2>&1 & disown
setsid nohup python gpu_logger.py --out /content/logs/gpu_usage.csv > /content/logs/gpu_logger.log 2>&1 & disown
python train_ctl.py start --config config/quran_ahh_r8.yml --run-name quran_ahh_r8 --log-name train_quran_ahh
grep -m1 'Found step' /content/logs/train_quran_ahh.log   # must NOT say step 0
```

## Pause tonight (you type) — NO rename
```bash
cd /content/maqamrock-yue2-lora-finetuning
python train_ctl.py stop --config config/quran_ahh_r8.yml --run-name quran_ahh_r8 --log-name train_quran_ahh
python backup_to_gcp.py --run-name quran_ahh_r8 --once    # confirm newest ckpt + optimizer.pt in GCS
```

## Deferred rename `quran_ahh_r8` -> `quran_ahh_r32` (do AFTER training completes)

**Marker beside the checkpoints** (so the misnomer can't be missed on a fresh VM):
`…/quran_ahh_r8/output/README.md` + `…/quran_ahh_r8/README.md` on GCS (also `docs/QURAN_AHH_RUN.md`).

Decision (user, 2026-10-05): leave the name until 28467 finishes. Post-completion there is no
resume, no live writer, no sidecar, so the two traps (the `{name}*` glob + ctime ordering) are
irrelevant and the rename is a plain offline move. Script is ready + tested:
`bootstrap/rename_run.py` (dry-run by default; refuses `--apply` while `run.py` alive). It
handles config `name`+`log_dir`, the config filename, local dir + checkpoint prefixes, ctime
ordering (still fine to have it), GCS copy→verify→delete, and merging `quran_ahh_r8_rank32/convert`
-> `quran_ahh_r32/convert`. Run it after the final save:
```bash
python bootstrap/rename_run.py --old quran_ahh_r8 --new quran_ahh_r32 --apply
setsid nohup python backup_to_gcp.py --run-name quran_ahh_r32 > /content/logs/gcp_backup.log 2>&1 & disown
```
Then a docs-reconciler pass over the ~10 files referencing `quran_ahh_r8` (`docs/QURAN_AHH_RUN.md`,
`docs/README.md`, `SOURCE_OF_TRUTH.md`, `bootstrap/setup.sh`, `INFERENCE/*`, the two
`TRAINING_ANALYSIS/` dirs) and rename `TRAINING_ANALYSIS/quran_ahh_r8_rank32/` -> `.../quran_ahh_r32/`.

## T4 probes

**Round 1 (done, 2026-10-05)** — c4500 + c7500 (real AR+NAR), held-out 2:255 both scripts:
`…/audiocpp_inference/out/20261005-154621_quran_pt_probe/`. All "sound like Alhusary"; **best =
c7500_simple** (one mistake); **simple > uthmani**; **hard letters (ح، ع) much improved vs
rank-8** but not solved.

**Round 2 (planned)** — **c10500 vs c16500** to test whether later training improves. `c10500` is
already converted + banked (`…/quran_ahh_r8_rank32/convert/c10500/`). Once the **16500**
checkpoint saves, convert + bank it (CPU, on the L4):
```bash
mkdir -p /content/converter/out && gcloud storage cp "$GCP_BACKUP_BASE/audiocpp_inference/converter/convert_aitoolkit_yue2_lora.py" /content/converter/out/
python /content/converter/out/convert_aitoolkit_yue2_lora.py \
  /content/ai-toolkit/output/quran_ahh_r8/quran_ahh_r8_000016500.safetensors \
  --out-dir /content/conversion/quran_ahh_r8_rank32/c16500 --stem quran_ahh_r8
gcloud storage rsync -r /content/conversion/quran_ahh_r8_rank32 "$GCP_BACKUP_BASE/quran_ahh_r8_rank32/convert"
```
Then, on a fresh T4 (`setup.sh --inference`), detached (~26 min for 4 tracks):
```bash
python INFERENCE/quran_pt_probe.py --prefix quran_ahh_r8_rank32/convert --arms c10500,c16500 --dry-run
setsid nohup python INFERENCE/quran_pt_probe.py --prefix quran_ahh_r8_rank32/convert --arms c10500,c16500 \
  > /content/logs/quran_pt_probe_r32.log 2>&1 & disown
```
Base (no-LoRA) reference: `…/out/20261005-072738_quran_pt_probe/base_*.wav`.

## Other open items
- Human blind gate (`ab-blind-eval`) before any merge; `docs/PAUSE_RESUME.md` still uses v2 names.
- `status.py` reports its default run name `akbar_arabic_rock_lora`; real run is `quran_ahh_r8`.
