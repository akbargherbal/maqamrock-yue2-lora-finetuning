# current

> **Tomorrow's session plan:** [`docs/QURAN_AHH_RESUME_PLAN.md`](../docs/QURAN_AHH_RESUME_PLAN.md)
> — point the agent there first; it resumes training, runs the c10500/c16500 T4 probe, finishes the
> run, then renames.

## State @ 2026-10-05 20:08 UTC (23:08 Bahrain) — **PAUSED** at step 19,500/28,467; rename DEFERRED

Branch `pron-lora-long-aya`. Run config `config/quran_ahh_r8.yml` = **AR+NAR, rank 32/32,
`ar_kl_weight 0.0`, steps 28467 (3 epochs)** — authority; do not edit hyperparameters.
The `r8` in the name is a **misnomer (it is rank 32)** — see "Deferred rename" below.

- **Training STOPPED cleanly** (SIGINT, `Job stopped` in the log; `run.py` gone) with the last save
  at **step 19,500** (13 checkpoints `_1500…_19500` + `optimizer.pt` **step 19500** + `loss_log.db`).
  Reached step 19,738 before stopping — resume re-runs ≤ ~238 steps.
- **Backup current**: forced `--once`, **3/3 synced** (20:08:37 UTC); GCS has 19,500 + optimizer.pt
  + loss_log.db. Sidecars left running (will die with the VM; fine).
- **Resume point = step 19,500.** Live snapshot: `TRAINING_ANALYSIS/quran_ahh_r8_rank32/ANALYSIS.md`.
- Round-2 T4 adapters `c10500` + `c16500` banked and ready.

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

## Pause — DONE (2026-10-05 20:08 UTC)
Stopped cleanly at checkpoint **19,500**; backup forced current. Nothing further tonight. If the VM
survives and you want it paused, leave it stopped; if the VM is reclaimed, resume tomorrow as below.

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

**Round 2 (planned)** — **c10500 vs c16500** to test whether later training improves. Both arms
are converted + banked (`…/quran_ahh_r8_rank32/convert/{c10500,c16500}/`). On a fresh T4
(`setup.sh --inference`), detached (~26 min for 4 tracks):
```bash
python INFERENCE/quran_pt_probe.py --prefix quran_ahh_r8_rank32/convert --arms c10500,c16500 --dry-run
setsid nohup python INFERENCE/quran_pt_probe.py --prefix quran_ahh_r8_rank32/convert --arms c10500,c16500 \
  > /content/logs/quran_pt_probe_r32.log 2>&1 & disown
```
Base (no-LoRA) reference: `…/out/20261005-072738_quran_pt_probe/base_*.wav`.

## Other open items
- Human blind gate (`ab-blind-eval`) before any merge; `docs/PAUSE_RESUME.md` still uses v2 names.
- `status.py` reports its default run name `akbar_arabic_rock_lora`; real run is `quran_ahh_r8`.
