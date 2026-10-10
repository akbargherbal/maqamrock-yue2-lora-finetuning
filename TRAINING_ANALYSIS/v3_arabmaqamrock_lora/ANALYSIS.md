# Training analysis — `v3_arabmaqamrock_lora` (438-track verbatim-lyric)

> **IN PROGRESS.** Snapshot at **2026-10-10 ~11:58 UTC, step 2589 / 5000 (51.8%)**.
> This is *not* a final analysis. Regenerate the charts + refresh these numbers when the
> run finishes:
> ```bash
> python TRAINING_ANALYSIS/generate_plots.py \
>   --db /content/ai-toolkit/output/v3_arabmaqamrock_lora/loss_log.db \
>   --gpu-csv /content/logs/gpu_usage.csv \
>   --total-steps 5000 --save-every 250 \
>   --outdir TRAINING_ANALYSIS/v3_arabmaqamrock_lora \
>   --title "v3_arabmaqamrock_lora" --event-label "checkpoint save"
> ```

## Run at a glance

| | |
|---|---|
| Config | `config/v3_arabmaqamrock_lora.yml` (A100 80 GB; rank 32 LoRA, EMA 0.999, `cot: off`, `train_window_frames: 0`, lr 1e-4, 5000 steps) |
| Model | YuE2 3B int8 `convrot8`, flowmatch, batch 1 |
| Dataset | **438** clips (Ajam 118 · Hijaz 107 · Kurd 101 · Nahawand 112), verbatim-lyric captions (`v3_arabmaqrock_dataset.zip`) |
| GPU | Colab **A100-SXM4-80GB** |
| Steps so far | **2589 / 5000 (51.8%)** — snapshot, still running |
| Step time | ~**2.4 s/step** (recent rate 0.4154 steps/s; avg 0.4161) |
| Wall span (logged) | 1.73 h |
| Sampling | **none** (`disable_sampling: true`, L93) — offline later |
| Checkpoints | every **250** steps (`save_every: 250`, L46); banked to GCS every ~5 min |
| Health | loss descending cleanly; **VRAM near cap — see callout** |

## Charts

- [`01_loss_curves.png`](01_loss_curves.png) — all loss terms, raw + 25-step mean
- [`02_loss_main.png`](02_loss_main.png) — primary `loss/loss` + linear trend
- [`03_learning_rate.png`](03_learning_rate.png) — LR schedule (constant 1e-4)
- [`04_throughput.png`](04_throughput.png) — seconds/step + progress vs wall-clock
- [`05_gpu_usage.png`](05_gpu_usage.png) — GPU util / memory / temp / power

## Loss trend (first-50 vs last-50 means)

| key | first50 | last50 | delta | min |
|---|---|---|---|---|
| `loss/loss` | 6.1719 | 4.7965 | **−1.3755** | 4.0784 @ step 2344 |
| `loss/ar_ce` | 5.2051 | 3.8893 | −1.3158 | 3.3596 @ step 2344 |
| `additional_model_loss` | 5.2051 | 3.8893 | −1.3158 | 3.3596 @ step 2344 |
| `learning_rate` | 1.0e-4 | 1.0e-4 | 0 | — |

`loss/ar_kl` is **absent** — `ar_kl_weight: 0.0` (L115) skips the KL term entirely.
Raw `loss/loss` is noisy at batch size 1; read the 25/50-step means, not single steps.

## ⚠️ VRAM is near capacity (~79.2 GB / 80 GB)

| metric | value |
|---|---|
| peak mem | **81144 MiB (79.2 GB, 99.05%)** |
| median / p90 | 78482 / 80834 MiB |
| headroom at peak | **~776 MiB** |

**Cause:** `gradient_checkpointing: false` (L78) — the only memory-relevant change vs v2
(`LEGACY…yml:72` had `true`; v2 peaked **17.0 GB**, `../ANALYSIS.md:37`). With
`train_window_frames: 0` (whole-song, L129) and batch 1, all activations are retained for the
backward pass. It bought ~30% speed (v2 median 3.42 s/step → here ~2.4). The config's own
justification ("~15-16 GB… skip activation recompute", L78) cites the figure that only holds
*with* checkpointing ON.

**Risk:** OOM is the one realistic failure mode. Mitigation **only if it OOMs** (not edited
mid-run): set `gradient_checkpointing: true` → ~17 GB, back to ~3.4 s/step. A crash is watched
by `train_watchdog.py` (auto-restart from checkpoint) with push alerts.

## ETA

`monitor_loss.py` ≈ **94.5 min** at the recent rate → finish ≈ **13:33 UTC ≈ 16:33 Bahrain**
(window ~16:00–16:35). Estimate only; it will firm up.

## What changed vs v2 (`LEGACY_akbar_arabic_rock_lora.yml`)

- dataset 267 → **438** (verbatim lyric tags)
- `steps` 3000 → **5000** (≈ same per-track exposure: 11.4 vs 11.2 epochs)
- `disable_sampling` false → **true** (sampling moved offline)
- `ar_kl_weight` 0.2 → **0.0** (the anchor never plateaued `ar_kl`; `DECISIONS.md`)
- `gradient_checkpointing` true → **false** (the VRAM cost above)

## Notes / honesty

- Loss is training loss only — no held-out split, so quality needs the (offline) samples too.
- Held-out/eval prompts are **stale vs the 438** and must be regenerated before any evaluation.
