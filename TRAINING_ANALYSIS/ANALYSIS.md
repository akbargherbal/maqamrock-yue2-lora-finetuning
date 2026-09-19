# Training analysis — `akbar_arabic_rock_lora`

Snapshot taken **2026-09-19 09:23 UTC** (12:23 Bahrain) at **step ~654 / 3000 (~22%)**.
Charts are regenerated from the live `loss_log.db` and `gpu_usage.csv` with:

```bash
python TRAINING_ANALYSIS/generate_plots.py
```

> This is **training loss only**. There is no held-out validation split, so quality
> has to be judged from the generated samples as well — loss alone can't tell you
> the LoRA learned the maqam.

## Run at a glance

| | |
|---|---|
| Config | `config/akbar_arabic_rock_lora.yml` (rank 32 LoRA, EMA 0.999, `cot: off`, lr 1e-4) |
| Model | YuE2 3B int8 `convrot8`, flowmatch |
| Dataset | 267 clips, 267 captions, one combined LoRA across four maqams |
| GPU | Colab L4 24 GB |
| Steps done | **654 / 3000 (21.8%)** |
| Elapsed (logged span) | 1.63 h |
| Median step time | **7.8 s/step** |
| Effective rate incl. samples | ~400 steps/h (0.111 steps/s) |
| ETA | **~5.9–6.2 h from snapshot → ~15:15–15:35 UTC / ~18:15–18:35 Bahrain** |
| Checkpoints | `..._000000250.safetensors`, `..._000000500.safetensors` (every 250, keep 12) |
| Samples | 12 mp3s (4 prompts at steps 0, 250, 500) |

## Charts

- [`01_loss_curves.png`](01_loss_curves.png) — all four loss terms, raw + 25-step mean
- [`02_loss_main.png`](02_loss_main.png) — primary `loss/loss` with linear trend
- [`03_learning_rate.png`](03_learning_rate.png) — LR schedule (constant 1e-4)
- [`04_throughput.png`](04_throughput.png) — seconds/step and progress vs wall-clock
- [`05_gpu_usage.png`](05_gpu_usage.png) — GPU util / memory / temp / power

## Loss trend (per-100-step means)

| steps | `loss/loss` | `loss/ar_ce` | `loss/ar_kl` | `additional_model_loss` |
|---|---|---|---|---|
| 1–100 | 6.302 | 5.227 | 0.562 | 5.339 |
| 101–200 | 5.925 | 4.817 | 0.885 | 4.994 |
| 201–300 | 5.822 | 4.694 | 0.987 | 4.891 |
| 301–400 | 5.758 | 4.623 | 1.050 | 4.833 |
| 401–500 | 5.727 | 4.601 | 1.057 | 4.812 |
| 501–600 | 5.677 | 4.537 | 1.088 | 4.755 |
| 601–654 | 5.671 | 4.521 | 1.099 | 4.741 |

Note the confirmed metric keys: `additional_model_loss`, `learning_rate`,
`loss/ar_ce`, `loss/ar_kl`, `loss/loss`. There is **no** `nar_flow` key (see
`DECISIONS.md`).

## Observations

1. **Classic shape, healthy descent.** `loss/loss` falls steeply for the first
   ~100 steps (7.5 → ~6.0), then settles into a slow, steady decline. The
   fitted trend over the smoothed curve is about **−6.2e-4 per step**. Raw loss
   swings between ~5.0 and ~6.2 step-to-step, so only the smoothed line is
   meaningful — this is normal for batch size 1.
2. **`loss/ar_ce` is the whole story.** It dominates `loss/loss` and tracks it
   almost one-to-one (5.23 → 4.52 over the run). That is the autoregressive
   cross-entropy doing the learning.
3. **`loss/ar_kl` rose from ~0 to ~1.1 and has now plateaued.** Early steps sit
   at ~0, then it climbs for ~200 steps and flattens around 1.05–1.10. This is
   the KL regularizer (weight 0.2) measuring how far the adapted AR distribution
   has drifted from the base — a *rise is expected* as the adapter starts to
   move, and the **plateau is the reassuring part**: it is bounded, not
   diverging. If it starts climbing again later, that would be the thing to
   investigate.
4. **Diminishing returns are showing.** `loss/loss` improvement per 100 steps
   has shrunk from −0.38 (100→200) to roughly −0.005 (600→654). At a constant
   LR of 1e-4 this is the expected approach to a plateau on a small, very
   repetitive dataset. It doesn't mean the run is broken — but it does mean the
   remaining 78% of steps are unlikely to move the training loss much, and
   sample quality is the better signal from here.
5. **Throughput is good but samples are a real tax.** Median step time is
   **7.8 s/step**, but each sample event (every 250 steps) pauses training for
   **~388 s (~6.5 min)** — nearly 20% of the wall-clock cost of each 250-step
   interval. That's why the headline ETA is ~6 h rather than the ~5 h the raw
   step rate suggests.
6. **GPU is healthy and has headroom.** While training (excluding the caching
   phase) the L4 runs ~97% util, ~12.4 GB mean / 16.0 GB peak of 23 GB, ~71 W,
   and 75 °C mean / **78 °C peak**. Memory is not the constraint; there is room,
   but batch size is best left at 1 for this dataset.
7. **Everything is being persisted.** Checkpoints at 250 and 500 are on disk and
   in GCS; samples and the metrics db are mirrored on the ~15-min backup cadence.

## Things to watch / decisions to make later

- **Judge the samples, not the loss.** The step-250/500 audios are the only
  quality signal for a style/timbre adapter. If they already sound like the
  target and loss has plateaued, killing the run early and using the current
  checkpoint is a legitimate (and cheaper) call.
- **Overfitting.** With 267 highly similar captions and no validation split,
  watch for samples that copy incidental artifacts of specific clips rather
  than generalizing the shared style — this is the main reason rank was kept
  at 32 (`DECISIONS.md`).
- **`ar_kl`** — treat a renewed upward trend as an early warning, not a spike.
- The ETA assumes the current sustained rate; a Colab disconnect would invalidate
  it, but auto-resume of this unchanged, approved run is permitted
  (`AGENTS.md`/`DECISIONS.md`).
