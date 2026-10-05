# current

## State @ 2026-10-05 12:39 UTC — `quran_ahh_r8` REVISED: TRAINING, cache hit, step ~88

Branch `pron-lora-long-aya` @ `7491211` (clean, 0/0 vs origin). Config
`config/quran_ahh_r8.yml` = **AR+NAR, rank 32/32, `ar_kl_weight 0.0`, steps 28467
(3 epochs)** — authority; do not edit. Old rank-8 AR-only checkpoints are NOT restored.

- **Training running**: `run.py` pid **16301** (detached). Log `/content/logs/train_quran_ahh.log`.
- **CACHE HIT confirmed**: the cache pass over 9,489 completed in `<1 s` (~10.4k it/s, lookup
  not encode); `Skipping first sample`; step 1 began immediately. **No full re-encode.**
- **Measurements** (from `loss_log.db` + `gpu_usage.csv`):
  - **~0.73 steps/s → ~1.37 s/step**
  - **VRAM peak ~7,896 MiB (7.71 GiB)** of 23,034 MiB; util avg 42 % / peak 100 %; 80 °C.
  - **1500-step save ≈ 34 min** (1500 × 1.37 s); ETA to 28,467 ≈ **10.8 h** (~648 min).
  - loss/loss 4.69 @ step 84 (bs=1; read the smoothed trend, not single steps).
- GPU L4, one process. Sidecars: `backup_to_gcp.py` (pid 13044) + `gpu_logger.py` (pid 13214).
- `vm-continuity status`: `state=OK` (pid 6120). `/content/quran_ahh_dataset` = 9489 train / 6 val;
  `_latent_cache` = 9489 files. `/content/ai-toolkit/output/quran_ahh_r8/` created by the run.

## Controls

terminal: detached (survives Ctrl+C / closing the tab).
log: `/content/logs/train_quran_ahh.log` (+ `_stdout.log`).
stop: `python train_ctl.py stop --config config/quran_ahh_r8.yml --run-name quran_ahh_r8 --log-name train_quran_ahh`
resume: re-run the same start line (local output prefix → auto-resumes newest checkpoint).

```bash
cd /content/maqamrock-yue2-lora-finetuning
python train_ctl.py start --config config/quran_ahh_r8.yml --run-name quran_ahh_r8 --log-name train_quran_ahh
```

Monitor: `python monitor_loss.py /content/ai-toolkit/output/quran_ahh_r8/loss_log.db --watch 30 --total-steps 28467`

## Evaluation (per checkpoint, after/between sessions)

Offline free-run on held-out 2:255 using the **TRAINED NAR** — never a lone-AR / NAR=0
render. Human blind gate (`ab-blind-eval`) before any merge.

## Close the session (you type these)

`train_ctl.py stop …` → `backup_to_gcp.py --run-name quran_ahh_r8 --once` → confirm newest
`*.safetensors` **and** `optimizer.pt` in GCS → `vm-continuity status` (`state=OK`) → update
this file + commit/push. No auto-resume; a pause is a user-typed `stop`.

## Open items
- `docs/QURAN_AHH_RUN.md` §1/§2/§5 note the revision; some snapshot rows (1 epoch/9489) stale.
- `results/quran_pt_gate/` untracked (`KEY.json` decoder) — not pushed.
- `status.py` reports its default run name `akbar_arabic_rock_lora`; actual run is `quran_ahh_r8`.
