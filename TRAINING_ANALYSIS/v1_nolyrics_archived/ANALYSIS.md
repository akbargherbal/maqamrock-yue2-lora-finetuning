# Training analysis — `akbar_arabic_rock_lora` (v1, **lyric-free / no-lyrics** captions)

> **ARCHIVED — this is the v1 (no-lyrics) run's analysis, kept as the baseline
> for the v2 lyric-conditioned run.** The v1 run is archived in GCS as
> `...akbar_arabic_rock_lora_v1_nolyrics_archived`; v1's captions had no
> `[Lyrics]` block, which is why its AR never learned lyric fidelity
> (see `DECISIONS.md`). The **live** analysis is the top-level
> `TRAINING_ANALYSIS/ANALYSIS.md`; `TRAINING_ANALYSIS/generate_plots.py` now
> targets the v2 run's `loss_log.db`, so the command below would regenerate v2
> charts, not these.

**COMPLETE** — snapshot taken **2026-09-19 14:55 UTC** (17:55 Bahrain) at
**step 3000 / 3000 (100%)**. The run finished cleanly (no traceback; final
checkpoint + optimizer written; 52 samples generated).

Charts (in this folder) were regenerated from v1's final `loss_log.db` and
`gpu_usage.csv`.

> This is **training loss only**. There is no held-out validation split, so quality
> has to be judged from the generated samples as well — loss alone can't tell you
> the LoRA learned the maqam.

> **Cross-VM note.** This run began on an L4 (steps 1–250, whole-song) and was
> resumed on an A100-SXM4-80GB at step 250 and ran to completion. The loss history
> is continuous across the switch; the throughput/GPU panels are A100-only
> (`gpu_usage.csv` started fresh on the A100 VM). Steps 251–295 were re-processed
> on the A100 after resume (they existed locally but never reached a saved
> checkpoint on the L4).

## Run at a glance

| | |
|---|---|
| Config | `config/akbar_arabic_rock_lora.yml` (rank 32 LoRA, EMA 0.999, `cot: off`, `train_window_frames: 0`, lr 1e-4) |
| Model | YuE2 3B int8 `convrot8`, flowmatch, batch 1 |
| Dataset | 267 clips, 267 captions, one combined LoRA across four maqams |
| GPU | Colab **A100-SXM4-80GB** (steps 1–250 were L4 24 GB) |
| Steps done | **3000 / 3000 (100%)**, latest logged step 2999 |
| Median step time | **3.10 s/step** on A100 (p10/p90 = 2.59 / 3.69, over 2730 steps); L4 was 13.4 s/step |
| Sample tax | ~226 s (~3.8 min) per sample event, every 250 steps (L4 was ~388 s) |
| Checkpoints | `_000000250` … `_000002750` (11) **+ final `akbar_arabic_rock_lora.safetensors`** + `optimizer.pt` — on disk and in GCS |
| Samples | **52 mp3s** (4 prompts at steps 0, 250, …, 3000) |

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
| 2401–2500 | 5.304 | 4.126 | 1.392 | 4.405 |
| 2501–2600 | 5.291 | 4.130 | 1.359 | 4.402 |
| 2601–2700 | 5.252 | 4.080 | 1.385 | 4.357 |
| 2701–2800 | 5.206 | 4.036 | 1.422 | 4.320 |
| 2801–2900 | 5.249 | 4.079 | 1.394 | 4.358 |
| 2901–3000 | 5.167 | 3.976 | 1.480 | 4.272 |

Confirmed metric keys: `additional_model_loss`, `learning_rate`, `loss/ar_ce`,
`loss/ar_kl`, `loss/loss`. There is **no** `nar_flow` key (see `DECISIONS.md`).

Headline first-50 vs last-50: `loss/loss` 6.49 → 5.17 (**−1.32**), `loss/ar_ce`
5.45 → 3.97 (−1.49), `loss/ar_kl` 0.37 → 1.50 (+1.12),
`additional_model_loss` 5.53 → 4.27 (−1.26). Minimum `loss/loss` 4.53 at step
2941 (single-step noise).

## Observations

1. **Completed cleanly and monotonically.** `loss/loss` fell steeply for the
   first ~100 steps, then declined slowly and steadily all the way to ~5.17.
   Raw loss swings ~4.5–6.2 step-to-step; only the smoothed line is meaningful,
   as expected at batch size 1.
2. **`loss/ar_ce` is the whole story.** It dominates `loss/loss` and tracks it
   almost one-to-one (5.23 → 4.20 → 3.98 by the end). This is the autoregressive
   cross-entropy — the AR expert doing the composition/arrangement learning that
   `train_window_frames: 0` was set to enable.
3. **`loss/ar_kl` never stopped rising.** It climbed from ~0, paused briefly near
   1.2 around steps 900–1300, then resumed climbing and ended at **~1.48–1.50**.
   The gradient moderated in places (e.g. 2501–2600 dipped to 1.359) but the
   trend is upward and it is now the highest it has been. This measures how far
   the adapted AR distribution has drifted from the base (weight 0.2); it is
   still a bounded drift, not a blow-up, but it did **not** plateau as hoped. If
   a future run continues past 3000 or repeats this one, this is the first metric
   to watch.
4. **Diminishing returns by the end.** From 2701–2800 (5.206) to 2901–3000
   (5.167) the per-100 improvement was only ~0.04, and 2801–2900 ticked up
   slightly. At constant LR 1e-4 on a small, repetitive dataset this is the
   expected approach to a plateau; the remaining signal is in the samples.
5. **The L4→A100 resume shows as a small, benign bump.** The 201–300 mean
   (6.072) sits above 101–200 (5.904) and 301–400 (5.953). This window straddles
   the step-250 switch; the decline resumes cleanly afterward — not a regression.
6. **A100 throughput, well-measured:** over 2730 post-resume steps (all clip
   lengths), **median 3.10 s/step**, p10/p90 2.59/3.69 — **~4.3× the L4's
   13.4 s/step**, above the 2–2.6× peak-spec estimate in
   `docs/GPU_L4_VS_A100.md`.
7. **Sample tax:** each sample event paused training ~226 s (~3.8 min), about 42%
   of the L4's ~388 s; amortised ~0.9 s/step over each 250-step interval.
8. **GPU healthy throughout:** ~100% util, ~15–16 GB of 80 GB, ~334 W mean /
   ~424 W max against a 400 W cap, 45–67 °C. Memory was never the constraint;
   batch was deliberately kept at 1 (one variable at a time).
9. **Everything persisted:** 11 numbered checkpoints + the final save +
   `optimizer.pt` + `loss_log.db` + 52 samples are mirrored to GCS.

## Next steps / things to judge

- **Listen to the samples.** The 52 generated audios (4 prompts at each 250-step
  mark, step 0 → 3000) are the only quality signal. Compare step 0 (base model)
  against 1250/2500/3000 and listen specifically for arrangement-level coherence
  — that is the point of `train_window_frames: 0`, and it is not something loss
  can confirm.
- **Pick the artifact.** The final `akbar_arabic_rock_lora.safetensors` and the
  numbered checkpoints 2250/2500/2750 are all in GCS; if an earlier checkpoint
  sounds better (possible if late steps overfit), it is available.
- **Overfitting check.** With 267 highly similar captions and no validation
  split, listen for samples copying incidental artifacts of specific clips
  rather than generalizing the shared style (why rank stayed at 32).
- **If a v2 is considered:** `ar_kl`'s unbroken rise suggests either fewer steps,
  a lower LR, or a KL-weight/loss adjustment — but change one variable at a time
  and keep the dataset/goal fixed (`DECISIONS.md`).
