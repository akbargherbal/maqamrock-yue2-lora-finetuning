# Training analysis — `akbar_arabic_rock_lora`

Snapshot taken **2026-09-19 13:02 UTC** (16:02 Bahrain) at **step ~1349 / 3000 (~45%)**.
Charts are regenerated from the live `loss_log.db` and `gpu_usage.csv` with:

```bash
python TRAINING_ANALYSIS/generate_plots.py
```

> This is **training loss only**. There is no held-out validation split, so quality
> has to be judged from the generated samples as well — loss alone can't tell you
> the LoRA learned the maqam.

> **Cross-VM note.** This run began on an L4 (steps 1–250, whole-song) and was
> resumed on an A100-SXM4-80GB at step 250 (now to ~1349). The loss history is
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
| Steps done | **~1349 / 3000 (45.0%)** |
| Median step time | **3.10 s/step** on A100 (p10/p90 = 2.59 / 3.72); L4 was 13.4 s/step |
| Sample tax | ~226 s (~3.8 min) per sample event, every 250 steps (L4 was ~388 s) |
| Effective rate incl. samples | ~0.25 steps/s (~4.0 s/step amortised) |
| ETA | **~1.8–1.9 h from snapshot → ~14:50 UTC / ~17:50 Bahrain** |
| Checkpoints | `..._000000250/500/750/1000/1250.safetensors` — all on disk **and in GCS** (every 250, keep 12) |
| Samples | 24 mp3s (4 prompts at steps 0, 250, 500, 750, 1000, 1250) |

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
| 1301–1400 | 5.517 | 4.369 | 1.200 | 4.609 |

Confirmed metric keys: `additional_model_loss`, `learning_rate`, `loss/ar_ce`,
`loss/ar_kl`, `loss/loss`. There is **no** `nar_flow` key (see `DECISIONS.md`).

Headline first-50 vs last-50 (from `generate_plots.py`): `loss/loss` 6.49 → 5.52
(**−0.97**), `loss/ar_ce` 5.45 → 4.38 (−1.08), `loss/ar_kl` 0.37 → 1.20 (+0.83),
`additional_model_loss` 5.53 → 4.62 (−0.91).

## Observations

1. **Healthy, monotone descent over the whole run.** `loss/loss` falls steeply
   for the first ~100 steps, then declines slowly and steadily all the way to
   ~5.5. Raw loss swings ~5.0–6.2 step-to-step, so only the smoothed line is
   meaningful — normal at batch size 1.
2. **`loss/ar_ce` is the whole story.** It dominates `loss/loss` and tracks it
   almost one-to-one (5.23 → 4.37). This is the autoregressive cross-entropy —
   the AR expert doing the composition/arrangement learning that
   `train_window_frames: 0` was set to enable.
3. **`loss/ar_kl` rose then plateaued.** It starts near 0, climbs for ~300 steps,
   and has sat in the 1.16–1.20 band from step ~900 through 1400. The **plateau
   is the reassuring part**: the adapted AR distribution is drifting from the
   base but is bounded, not diverging. A renewed climb would be the early warning.
4. **Diminishing returns are showing.** Per-100-mean improvement has shrunk from
   −0.38 (100→200) to roughly −0.05 (1200→1300). At constant LR 1e-4 this is the
   expected approach to a plateau on a small, highly repetitive dataset. It does
   not mean the run is broken — it means sample quality is the better signal
   from here, not the loss.
5. **The L4→A100 resume shows as a small, benign bump.** The 201–300 mean
   (6.072) sits above 101–200 (5.904) and 301–400 (5.953). This window straddles
   the step-250 switch (L4 → A100, re-processing 250–295 after restore); the
   decline resumes cleanly afterward. Not a real regression.
6. **A100 throughput is excellent and now well-measured.** Over 1090 post-resume
   steps (all clip lengths), **median 3.10 s/step**, p10/p90 2.59/3.72. That is
   **~4.3× the L4's 13.4 s/step** — above the 2–2.6× estimate in
   `docs/GPU_L4_VS_A100.md`, which was derived from peak-spec ratios rather than a
   measured A100 run. This resolves the earlier "does it hold on the longest
   clips?" caution: it does.
7. **The sample tax is real but smaller here.** Each sample event pauses training
   ~226 s (~3.8 min) — about 42% of the L4's ~388 s — because generation is faster
   too. Still, over the 250-step interval it adds ~0.9 s/step amortised, which is
   why the headline ETA (~1.9 h) is longer than the raw 3.1 s/step implies
   (~1.4 h).
8. **GPU is healthy with large headroom.** While training: ~100% util, **peak
   15.25 GB of 80 GB**, ~334 W mean / 424 W max against a 400 W cap, 45–67 °C.
   Memory was never the constraint and there is now ~65 GB free — but batch size
   is deliberately left at 1 (`DECISIONS.md`: one variable at a time).
9. **Everything is persisted.** Checkpoints 250–1250 are on disk and in GCS; the
   metrics db, samples, and logs are mirrored on the ~15-min backup cadence.

## Things to watch / decisions to make later

- **Judge the samples, not the loss.** The 24 generated audios (steps 0/250/…/
  1250) are the quality signal; loss has largely plateaued. The step-0 samples
  are a useful base-model reference to A/B against the later ones.
- **Overfitting.** With 267 highly similar captions and no validation split,
  watch for samples that copy incidental artifacts of specific clips rather than
  generalizing the shared style — the reason rank was kept at 32
  (`DECISIONS.md`).
- **`ar_kl`** — treat a renewed upward trend past ~1.2 as an early warning.
- **Structure vs timbre.** The whole point of `train_window_frames: 0` is that
  the AR loss now spans entire songs, so `ar_ce`'s long descent is the number to
  correlate with whether generated songs hold together arrangementally — best
  judged by ear across the 500→1250 samples.
- The ETA assumes the current sustained rate; a Colab disconnect would invalidate
  it, but auto-resume of this unchanged, approved run is permitted
  (`AGENTS.md`/`DECISIONS.md`).
