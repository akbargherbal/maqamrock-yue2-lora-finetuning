# Training analysis — `akbar_arabic_rock_lora`

Snapshot taken **2026-09-19 14:09 UTC** (17:09 Bahrain) at **step ~2346 / 3000 (~78%)**.
Charts are regenerated from the live `loss_log.db` and `gpu_usage.csv` with:

```bash
python TRAINING_ANALYSIS/generate_plots.py
```

> This is **training loss only**. There is no held-out validation split, so quality
> has to be judged from the generated samples as well — loss alone can't tell you
> the LoRA learned the maqam.

> **Cross-VM note.** This run began on an L4 (steps 1–250, whole-song) and was
> resumed on an A100-SXM4-80GB at step 250 (now to ~2346). The loss history is
> continuous across the switch; the throughput/GPU panels are A100-only
> (`gpu_usage.csv` started fresh on this VM). Steps 251–295 were re-processed on
> the A100 after resume (they existed locally but never reached a saved
> checkpoint on the L4).

## Run at a glance

| | |
|---|---|
| Config | `config/akbar_arabic_rock_lora.yml` (rank 32 LoRA, EMA 0.999, `cot: off`, `train_window_frames: 0`, lr 1e-4) |
| Model | YuE2 3B int8 `convrot8`, flowmatch, batch 1 |
| Dataset | 267 clips, 267 captions, one combined LoRA across four maqams |
| GPU | Colab **A100-SXM4-80GB** (steps 1–250 were L4 24 GB) |
| Steps done | **~2346 / 3000 (78.2%)** |
| Median step time | **3.10 s/step** on A100 (p10/p90 = 2.59 / 3.69), over 2079 steps; L4 was 13.4 s/step |
| Sample tax | ~226 s (~3.8 min) per sample event, every 250 steps (L4 was ~388 s) |
| Effective rate incl. samples | ~0.25 steps/s (~4.0 s/step amortised) |
| ETA | **~45 min from snapshot → ~14:55 UTC / ~17:55 Bahrain** (incl. sample pauses at 2500/2750/3000) |
| Checkpoints | `..._000000250` … `..._000002250.safetensors` (9) — all on disk **and in GCS** (every 250, keep 12) |
| Samples | 40 mp3s (4 prompts at steps 0, 250, 500, 750, 1000, 1250, 1500, 1750, 2000, 2250) |

## Charts

- [`01_loss_curves.png`](01_loss_curves.png) — all four loss terms, raw + 25-step mean
- [`02_loss_main.png`](02_loss_main.png) — primary `loss/loss` with linear trend
- [`03_learning_rate.png`](03_learning_rate.png) — LR schedule (constant 1e-4)
- [`04_throughput.png`](04_throughput.png) — seconds/step and progress vs wall-clock
- [`05_gpu_usage.png`](05_gpu_usage.png) — A100 util / memory / temp / power

## Loss trend (per-100-step means)

| steps | `loss/loss` | `loss/ar_ce` | `loss/ar_kl` | `additional_model_loss` |
|---|---|---|---|---|
| 1–100 | 6.287 | 5.227 | 0.579 | 5.343 |
| 101–200 | 5.904 | 4.805 | 0.891 | 4.983 |
| 201–300 | 6.072 | 5.000 | 0.723 | 5.144 |
| 301–400 | 5.953 | 4.853 | 0.857 | 5.024 |
| 401–500 | 5.818 | 4.706 | 0.986 | 4.903 |
| 501–600 | 5.751 | 4.627 | 1.047 | 4.837 |
| 601–700 | 5.726 | 4.604 | 1.050 | 4.814 |
| 701–800 | 5.699 | 4.563 | 1.090 | 4.781 |
| 801–900 | 5.661 | 4.512 | 1.111 | 4.734 |
| 901–1000 | 5.644 | 4.519 | 1.122 | 4.744 |
| 1001–1100 | 5.614 | 4.473 | 1.157 | 4.704 |
| 1101–1200 | 5.574 | 4.442 | 1.180 | 4.678 |
| 1201–1300 | 5.576 | 4.443 | 1.160 | 4.675 |
| 1301–1400 | 5.503 | 4.366 | 1.208 | 4.608 |
| 1401–1500 | 5.536 | 4.409 | 1.194 | 4.648 |
| 1501–1600 | 5.509 | 4.372 | 1.215 | 4.615 |
| 1601–1700 | 5.491 | 4.340 | 1.241 | 4.588 |
| 1701–1800 | 5.460 | 4.313 | 1.252 | 4.563 |
| 1801–1900 | 5.446 | 4.291 | 1.278 | 4.547 |
| 1901–2000 | 5.409 | 4.252 | 1.280 | 4.508 |
| 2001–2100 | 5.426 | 4.272 | 1.273 | 4.526 |
| 2101–2200 | 5.369 | 4.198 | 1.325 | 4.463 |
| 2201–2300 | 5.352 | 4.197 | 1.321 | 4.461 |
| 2301–2400 | 5.388 | 4.200 | 1.333 | 4.466 |

Confirmed metric keys: `additional_model_loss`, `learning_rate`, `loss/ar_ce`,
`loss/ar_kl`, `loss/loss`. There is **no** `nar_flow` key (see `DECISIONS.md`).

Headline first-50 vs last-50 (from `generate_plots.py`): `loss/loss` 6.49 → 5.39
(**−1.11**), `loss/ar_ce` 5.45 → 4.20 (−1.25), `loss/ar_kl` 0.37 → 1.34 (+0.96),
`additional_model_loss` 5.53 → 4.47 (−1.06).

## Observations

1. **Healthy, monotone descent over the whole run.** `loss/loss` fell steeply
   for the first ~100 steps, then declined slowly and steadily all the way to
   ~5.39. Raw loss swings ~4.7–6.2 step-to-step, so only the smoothed line is
   meaningful — normal at batch size 1.
2. **`loss/ar_ce` is the whole story.** It dominates `loss/loss` and tracks it
   almost one-to-one (5.23 → 4.20). This is the autoregressive cross-entropy —
   the AR expert doing the composition/arrangement learning that
   `train_window_frames: 0` was set to enable.
3. **`loss/ar_kl` is no longer flat — it is creeping up again.** It rose to a
   ~1.16–1.20 band by step ~900–1300, then resumed a slow climb: 1.28 by
   1801–1900, 1.32 by 2101–2200, **1.33 by 2301–2400**. This is still a gentle
   drift, not a spike or a divergence, but the earlier "plateau" reading no
   longer holds. Treat a continued/accelerating rise as the early warning to
   watch — it measures how far the adapted AR distribution has moved from the
   base (weight 0.2).
4. **Diminishing returns, very clearly.** Per-100-mean improvement of `loss/loss`
   is now within noise of zero: 1301–1400 → 2301–2400 moved only 5.50 → 5.39,
   with several flat/noisy windows (e.g. 2301–2400 ticks *up* slightly from
   2201–2300). At constant LR 1e-4 on a small, repetitive dataset this is the
   expected approach to a plateau. Loss is no longer the useful signal — sample
   quality is.
5. **The L4→A100 resume shows as a small, benign bump.** The 201–300 mean
   (6.072) sits above 101–200 (5.904) and 301–400 (5.953). This window straddles
   the step-250 switch (L4 → A100, re-processing 250–295 after restore); the
   decline resumes cleanly afterward. Not a real regression.
6. **A100 throughput is excellent and now very well-measured.** Over 2079
   post-resume steps (all clip lengths), **median 3.10 s/step**, p10/p90
   2.59/3.69. That is **~4.3× the L4's 13.4 s/step** — above the 2–2.6× estimate
   in `docs/GPU_L4_VS_A100.md`, which was derived from peak-spec ratios rather
   than a measured A100 run. The earlier "does it hold on the longest clips?"
   caution is resolved: it does.
7. **The sample tax is real but smaller here.** Each sample event pauses training
   ~226 s (~3.8 min) — about 42% of the L4's ~388 s. Over the 250-step interval
   it adds ~0.9 s/step amortised, so the headline ETA is longer than the raw
   3.1 s/step implies.
8. **GPU is healthy with large headroom.** While training: ~100% util, ~15–16 GB
   of 80 GB, ~334 W mean / ~424 W max against a 400 W cap, 45–67 °C. Memory was
   never the constraint and there is now ~64 GB free — batch size is deliberately
   left at 1 (`DECISIONS.md`: one variable at a time).
9. **Everything is persisted.** Checkpoints 250–2250 are on disk and in GCS; the
   metrics db, samples, and logs are mirrored on the ~15-min backup cadence.

## Things to watch / decisions to make later

- **Judge the samples, not the loss.** The 40 generated audios are the quality
  signal; loss has plateaued. Use the step-0 samples as the base-model reference
  and listen for whether arrangement-level coherence improves across
  500 → 1250 → 2250 (the whole point of `train_window_frames: 0`).
- **Overfitting.** With 267 highly similar captions and no validation split,
  watch for samples that copy incidental artifacts of specific clips rather than
  generalizing the shared style — the reason rank was kept at 32
  (`DECISIONS.md`).
- **`ar_kl`** — no longer plateaued; a continued climb past ~1.35 is the early
  warning to correlate with sample quality.
- **End of run.** At ~78% with loss flat, the step-2500/2750/3000 samples are the
  main reason to let it finish; consider whether a later run should lower LR or
  add a holdout rather than add steps at this LR.
- The ETA assumes the current sustained rate; a Colab disconnect would invalidate
  it, but auto-resume of this unchanged, approved run is permitted
  (`AGENTS.md`/`DECISIONS.md`).
