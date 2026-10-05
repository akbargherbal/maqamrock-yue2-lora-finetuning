# current

## State @ 2026-10-05 13:40 UTC — `quran_ahh_r8` REVISED: TRAINING, step ~2638, 1 ckpt

Branch `pron-lora-long-aya` @ `f60bf80` (clean after this file; 0/0 vs origin). Config
`config/quran_ahh_r8.yml` = **AR+NAR, rank 32/32, `ar_kl_weight 0.0`, steps 28467
(3 epochs)** — authority; do not edit. Old rank-8 AR-only checkpoints are NOT restored.

- **Training running**: `run.py` pid **16301** (detached, started 12:35:11). Log
  `/content/logs/train_quran_ahh.log`.
- **CACHE HIT confirmed** at launch: the 9,489 cache pass took `<1 s` (lookup, not encode);
  `Skipping first sample`; step 1 started immediately. No full re-encode.
- **Measurements**: ~0.70–0.77 steps/s (**~1.3–1.4 s/step**); VRAM peak **9,144 MiB (8.93 GiB)**
  of 23,034; 80 °C, ~74 W; **1500-step save ≈ 34 min**. Step ~2638, loss/loss ~4.2–4.9 (bs=1).
- **Checkpoints (rank 32)**: `quran_ahh_r8_000001500.safetensors` (112 MiB, saved 13:11) +
  `optimizer.pt` (114 MiB), both in GCS @13:13:41. Next = step 3000.
- GPU L4, one process. Sidecars: `backup_to_gcp.py` (pid 13044) + `gpu_logger.py` (pid 13214).
- `vm-continuity status`: `state=OK` (pid 6120). `/content/quran_ahh_dataset` = 9489 train / 6 val;
  `_latent_cache` = 9489 files.

## GCS layout (2026-10-05, cleaned)

- **Live** `…/quran_ahh_r8/` now holds ONLY the revised run: `output/` (rank-32 ckpts +
  optimizer + loss_log.db), `logs/`, `agent_notes/`, `run_manifest.json`.
- **Archive** `…/archive/quran_ahh_r8_rank8_aronly/` holds the OLD rank-8 run's artifacts,
  moved out on 2026-10-05 UTC so the new run's same-named saves can't be confused/overwritten:
  `output/` (step saves 1500→9000 + final, 84 MiB) and `convert/` (base/quran_only/c*9000/final
  probe arms, 300 MiB). Do not use any rank-8 adapter with the revised config.

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
- `docs/QURAN_AHH_RUN.md` §2 updated for the archived convert/ path; some snapshot rows
  (1 epoch/9489) still stale.
- `results/quran_pt_gate/` untracked (`KEY.json` decoder) — not pushed.
- `status.py` reports its default run name `akbar_arabic_rock_lora`; actual run is `quran_ahh_r8`.
