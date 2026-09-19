# Live status snapshot — 2026-09-19 11:05:15 UTC

Read-only observation. No config was changed and the training run was not
restarted or killed. Run: `akbar_arabic_rock_lora` (whole-song,
`train_window_frames: 0`), launched ~10:07 UTC.

## monitor_loss.py --history 5
```
step 225  (db: /content/ai-toolkit/output/akbar_arabic_rock_lora/loss_log.db)
  additional_model_loss: 4.863818
  learning_rate: 0.000100
  loss/ar_ce: 4.662021
  loss/ar_kl: 1.008985
  loss/loss: 5.638257
  ~0.075 steps/sec (last 50 recorded steps)
```

## monitor_loss.py --key "loss/loss" --history 20
```
step 225  (db: /content/ai-toolkit/output/akbar_arabic_rock_lora/loss_log.db)
  additional_model_loss: 4.863818
  learning_rate: 0.000100
  loss/ar_ce: 4.662021
  loss/ar_kl: 1.008985
  loss/loss: 5.638257
  ~0.075 steps/sec (last 50 recorded steps)

  last 20 recorded values for 'loss/loss':
    step 206: 5.711782
    step 207: 6.008478
    step 208: 5.493617
    step 209: 5.998558
    step 210: 5.836066
    step 211: 6.096294
    step 212: 5.733180
    step 213: 5.658139
    step 214: 5.807047
    step 215: 5.548685
    step 216: 5.686352
    step 217: 5.862387
    step 218: 6.062036
    step 219: 5.709780
    step 220: 5.879436
    step 221: 5.731359
    step 222: 6.160459
    step 223: 6.064662
    step 224: 5.809258
    step 225: 5.638257
```

## nvidia-smi
```
Sat Sep 19 11:05:04 2026       
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 580.82.07              Driver Version: 580.82.07      CUDA Version: 13.0     |
+-----------------------------------------+------------------------+----------------------+
| GPU  Name                 Persistence-M | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|                                         |                        |               MIG M. |
|=========================================+========================+======================|
|   0  NVIDIA L4                      Off |   00000000:00:03.0 Off |                    0 |
| N/A   76C    P0             76W /   72W |   15764MiB /  23034MiB |    100%      Default |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+

+-----------------------------------------------------------------------------------------+
| Processes:                                                                              |
|  GPU   GI   CI              PID   Type   Process name                        GPU Memory |
|        ID   ID                                                               Usage      |
|=========================================================================================|
|    0   N/A  N/A          160690      C   python3                               15756MiB |
+-----------------------------------------------------------------------------------------+
```

## gpu_usage.csv (tail -10)
```
2026-09-19 11:03:29,100,15764,23034,78,72.16
2026-09-19 11:03:39,100,15764,23034,75,72.53
2026-09-19 11:03:49,100,15764,23034,75,71.99
2026-09-19 11:03:59,100,15764,23034,76,70.50
2026-09-19 11:04:09,100,15764,23034,75,71.23
2026-09-19 11:04:19,100,15764,23034,75,73.74
2026-09-19 11:04:29,100,15764,23034,75,72.38
2026-09-19 11:04:39,100,15764,23034,76,69.80
2026-09-19 11:04:49,100,15764,23034,77,72.42
2026-09-19 11:04:59,100,15764,23034,76,72.55
```

## Colab A100 availability

**Not determinable from inside the running VM — this is not a yes/no that the
agent can answer here.** Colab exposes no API that lists the options in
Runtime > Change runtime type; it is a web-UI-only setting and depends on the
account's plan and current capacity. It must be checked by the human in the
Colab UI.

Evidence gathered from this runtime (for context only):
- `nvidia-smi -L` → `GPU 0: NVIDIA L4` (current accelerator is L4, not A100).
- The Colab tunnel identifier for this runtime contains `gpu-l4-...` (i.e. an L4
  backend was assigned).
- `COLAB_IMAGE_TYPE=gpu`, `COLAB_GPU=1`, `COLAB_RELEASE_TAG=release-colab-external-images_20260917-060051_RC00`.

Interpretation: this session is definitively on an L4. Whether an A100 option
is offered to this account right now cannot be inferred from within the VM; the
human should open **Runtime > Change runtime type** and look at the Hardware
accelerator dropdown (A100 is generally limited to certain plans/regions and is
subject to availability).

## Quick read (for the reviewer)

- Training healthy and progressing: step 225/3000 (~7.5%), `loss/loss` ~5.64
  and trending down versus the ~6.3 at step 1–100. Raw values are noisy
  (5.49–6.16 over the last 20) as expected at batch size 1.
- L4 is saturated: 100% util, **76 W on a 72 W cap**, 76–78 °C,
  15,764/23,034 MiB VRAM. The GPU, not the dataloader, is the bottleneck.
- First checkpoint is step 250 (`save_every: 250`); the run has not yet saved
  one, so it is not yet resumable. Snapshot taken at step 225.
- Relevant cost/time analysis: [GPU_L4_VS_A100.md](GPU_L4_VS_A100.md).
