# Live status snapshot — 2026-09-19 12:01 UTC (A100, post-resume)

> **Later update (14:55 UTC):** the run went on to **complete 3000/3000**
> cleanly on the A100. This file is preserved as the 12:01 mid-run observation;
> see `TRAINING_ANALYSIS/ANALYSIS.md` and `PROGRESS.md` for the final numbers.

Read-only observation. No config was changed and the training run was not
restarted or killed. Run: `akbar_arabic_rock_lora` (whole-song,
`train_window_frames: 0`), resumed on an **A100-SXM4-80GB** from the step-250
checkpoint; captured at ~step 461/3000. L4 run for comparison: ~13.4 s/step,
15.8 GB peak.

## Resume confirmation (not a restart at step 0)

`/content/logs/train.log`:
```
Loading from /content/ai-toolkit/output/akbar_arabic_rock_lora/akbar_arabic_rock_lora_000000250.safetensors
Found step 250 in metadata, starting from there
Loading optimizer state from /content/ai-toolkit/output/akbar_arabic_rock_lora/optimizer.pt
```
Also confirmed independently: the checkpoint's embedded `training_info.step` is
`250`, and it is the only `*.safetensors` in the run folder. The latent cache
was absent on the fresh VM, so first launch rebuilt it before the first step.

## monitor_loss.py --history 30
```
step 461  (db: /content/ai-toolkit/output/akbar_arabic_rock_lora/loss_log.db)
  additional_model_loss: 4.898764
  learning_rate: 0.000100
  loss/ar_ce: 4.664380
  loss/ar_kl: 1.171918
  loss/loss: 5.727722
  ~0.318 steps/sec (last 50 recorded steps)
  ETA to step 3000: ~133.1 min
```

## monitor_loss.py --key "loss/loss" --history 30
```
  last 30 recorded values for 'loss/loss':
    step 432: 5.891504
    step 433: 6.164943
    step 434: 5.831566
    step 435: 5.781652
    step 436: 6.066602
    step 437: 5.928311
    step 438: 5.829404
    step 439: 5.851487
    step 440: 6.004880
    step 441: 5.825076
    step 442: 5.836835
    step 443: 6.107095
    step 444: 5.979740
    step 445: 5.551672
    step 446: 5.843320
    step 447: 6.013007
    step 448: 5.479530
    step 449: 5.588436
    step 450: 5.692197
    step 451: 5.891844
    step 452: 5.850797
    step 453: 5.848957
    step 454: 5.789231
    step 455: 5.732360
    step 456: 5.888706
    step 457: 5.599371
    step 458: 5.890467
    step 459: 5.789252
    step 460: 5.685486
    step 461: 5.727722
```

## nvidia-smi
```
Sat Sep 19 12:00:40 2026
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 580.82.07              Driver Version: 580.82.07      CUDA Version: 13.0     |
+-----------------------------------------+------------------------+----------------------+
| GPU  Name                 Persistence-M | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|                                         |                        |               MIG M. |
|=========================================+========================+======================|
|   0  NVIDIA A100-SXM4-80GB          Off |   00000000:00:05.0 Off |                    0 |
| N/A   65C    P0            392W /  400W |   15254MiB /  81920MiB |     85%      Default |
|                                         |                        |             Disabled |
+-----------------------------------------+------------------------+----------------------+
| Processes:                                                                            |
|  GPU   GI   CI              PID   Type   Process name                        GPU Memory |
|        ID   ID                                                               Usage |
|=======================================================================================|
|    0   N/A  N/A           80090      C   python3                               15242MiB |
+-----------------------------------------------------------------------------------------+
```

## gpu_usage.csv (tail -15)
```
2026-09-19 11:58:18,100,15254,81920,66,364.22
2026-09-19 11:58:28,100,15254,81920,65,391.79
2026-09-19 11:58:38,100,15254,81920,64,391.46
2026-09-19 11:58:48,100,15254,81920,65,404.26
2026-09-19 11:58:58,100,15254,81920,65,397.91
2026-09-19 11:59:08,0,15254,81920,55,96.85
2026-09-19 11:59:18,100,15254,81920,64,402.88
2026-09-19 11:59:28,96,15254,81920,66,400.07
2026-09-19 11:59:38,100,15254,81920,65,400.67
2026-09-19 11:59:48,96,15254,81920,66,404.39
2026-09-19 11:59:58,100,15254,81920,67,424.10
2026-09-19 12:00:08,100,15254,81920,64,355.05
2026-09-19 12:00:18,100,15254,81920,65,403.34
2026-09-19 12:00:28,100,15254,81920,66,404.54
2026-09-19 12:00:38,100,15254,81920,67,410.47
```

## Sidecars
```
38310 python3 backup_to_gcp.py --run-name akbar_arabic_rock_lora
38313 python3 gpu_logger.py --out /content/logs/gpu_usage.csv
```
Backup daemon healthy: passes at 11:35 and 11:50, all three targets synced
(`output/`, `logs/`, `agent_notes/`). GPU logger sampling every 10 s.

## Quick read (for the reviewer)

- **Resume is correct:** step-250 checkpoint + `optimizer.pt` loaded, loop
  started at 250, currently ~step 461/3000 (~15%). No restart at 0.
- **Step time ~3.1 s/step** (0.318 steps/sec over the last 50 recorded), versus
  ~13.4 s/step on the L4 — about **4.3× faster**, above the 2–2.6× estimate in
  `docs/GPU_L4_VS_A100.md`. Treat with mild caution: this window may not yet
  include the longest (~370 s) clips; re-check the median once a broader mix of
  songs has been seen.
- **Throughput-bound, as on L4:** ~100% util (one 0% CSV sample is a polling
  blip), power mean 334 W / max 424 W against a 400 W cap, 64–67 °C. 15.25 GB
  of 80 GB VRAM is used — the extra capacity is untouched (batch is still 1;
  config unchanged). The three `run.py` PIDs are one parent (80090) plus two
  multiprocessing children; only 80090 holds GPU memory.
- **Loss:** `loss/loss` ~5.7 at step 461, still noisy (5.48–6.16 over the last
  30) as expected at batch 1 — read the trend, not single steps.
- **ETA:** ~2.2 h to step 3000 at the current rate, excluding ~1.2 h of
  sampling every 250 steps (next checkpoint at 500).
