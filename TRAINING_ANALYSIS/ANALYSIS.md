# Training analysis — `akbar_arabic_rock_lora` (v2, lyric-conditioned captions)

> **IN PROGRESS — live snapshot at 2026-09-20 08:26 UTC, step ~652 / 3000 (21.7%).**
> The run is still training. Numbers below are current, not final; this file is
> regenerated/updated as the run proceeds and finalized at step 3000. Charts are
> regenerated from the live `loss_log.db` and `gpu_usage.csv` with:
>
> ```bash
> python TRAINING_ANALYSIS/generate_plots.py
> ```

> This is **training loss only**. There is no held-out validation split, so
> quality must be judged from the generated samples too — loss alone can't tell
> you the LoRA learned the maqam or the lyrics.

> **What changed vs v1:** identical config/architecture (rank 32, EMA 0.999,
> `cot: off`, `train_window_frames: 0`, lr 1e-4, 3000 steps). The **only intended
> change is the dataset captions**: v2 captions now carry a real `[Lyrics]`
> block, closing the missing-signal gap that degraded Arabic pronunciation in v1
> (see `DECISIONS.md` / `PROGRESS.md`). v1's finished run and its analysis are
> preserved — the analysis as `TRAINING_ANALYSIS/v1_nolyrics_archived/`, the run
> as `...akbar_arabic_rock_lora_v1_nolyrics_archived` in GCS. **This run is a
> genuine fresh start** (smoke-test output archived first, no checkpoint to
> auto-resume from); the latent cache was reused (~3.5 min saved).

## Run at a glance (live)

| | |
|---|---|
| Config | `config/akbar_arabic_rock_lora.yml` (rank 32 LoRA, EMA 0.999, `cot: off`, `train_window_frames: 0`, lr 1e-4) |
| Model | YuE2 3B int8 `convrot8`, flowmatch, batch 1 |
| Dataset | 267 clips, 267 **lyric-bearing** captions, one combined LoRA across four maqams |
| GPU | Colab **A100-SXM4-80GB** |
| Steps done | **~652 / 3000 (21.7%)** at snapshot |
| Step time | **~3.3 s/step** (recent 100: 0.298 steps/s) |
| Sample tax | 4 samples per event at `duration: 360`; **12 samples** so far (steps 0/250/500) |
| ETA | **~2.2 h** at recent rate, plus sample events |
| GPU | peak **16.4 GB** (16810 MiB), mean 12.3 GB of 80 GB; ~93% util, ~285 W mean (incl. sample pauses) |
| Health | no tracebacks; loss descending cleanly |

## Charts

- [`01_loss_curves.png`](01_loss_curves.png) — all four loss terms, raw + 25-step mean
- [`02_loss_main.png`](02_loss_main.png) — primary `loss/loss` with linear trend
- [`03_learning_rate.png`](03_learning_rate.png) — LR schedule (constant 1e-4)
- [`04_throughput.png`](04_throughput.png) — seconds/step and progress vs wall-clock
- [`05_gpu_usage.png`](05_gpu_usage.png) — A100 util / memory / temp / power

## Loss trend (per-100-step means, v2 in progress)

| steps | `loss/loss` | `loss/ar_ce` | `loss/ar_kl` | `additional_model_loss` |
|---|---|---|---|---|
| 1–100 | 6.015 | 4.942 | 0.588 | 5.060 |
| 101–200 | 5.614 | 4.508 | 0.958 | 4.700 |
| 201–300 | 5.500 | 4.384 | 1.042 | 4.593 |
| 301–400 | 5.470 | 4.362 | 1.064 | 4.574 |
| 401–500 | 5.414 | 4.288 | 1.105 | 4.509 |
| 501–600 | 5.374 | 4.262 | 1.104 | 4.483 |
| 601–700 * | 5.373 | 4.259 | 1.154 | 4.490 |

\* partial window (to ~step 652 at snapshot).

Confirmed metric keys: `additional_model_loss`, `learning_rate`, `loss/ar_ce`,
`loss/ar_kl`, `loss/loss`. There is **no** `nar_flow` key (see `DECISIONS.md`).

First-50 vs last-50 (step ~652): `loss/loss` 6.23 → 5.36 (**−0.86**),
`loss/ar_ce` 5.19 → 4.26 (−0.93), `loss/ar_kl` 0.39 → 1.16 (**+0.77**),
`additional_model_loss` 5.26 → 4.49 (−0.77).

## v2 vs v1 at the same step (not apples-to-apples — read the caveat)

| window | `loss/loss` | `loss/ar_ce` | `loss/ar_kl` | `additional_model_loss` |
|---|---|---|---|---|
| v1 1–100 | 6.287 | 5.227 | 0.579 | 5.343 |
| **v2 1–100** | **6.015** | **4.942** | 0.588 | **5.060** |
| v1 601–700 | 5.726 | 4.604 | 1.050 | 4.814 |
| **v2 601–700** | **5.373** | **4.259** | 1.154 | **4.490** |

**Caveat:** the audio targets are identical, but v2's prompts now contain the
lyrics, so the AR has the actual words to predict from. A lower `loss/ar_ce` is
therefore *expected* and is the mechanism by which pronunciation should be
protected — it is not by itself proof of better output. It does confirm the
lyric signal is reaching the AR (the v1 failure was that it never did).

## Observations / flags

1. **Healthy descent, no errors.** `loss/loss` fell steeply over the first ~100
   steps then declined steadily; no tracebacks, no loss spikes beyond normal
   batch-1 noise, VRAM flat (never climbing).
2. **The lyric signal is present.** `loss/ar_ce` is ~0.35 lower than v1's at the
   same step (4.26 vs 4.60 by 601–700), consistent with the AR now conditioning
   on real lyrics instead of style tags alone.
3. **`loss/ar_kl` — the one to watch.** It rose 0.39 → 1.16 by step ~652 (+0.77).
   At this point it is slightly *above* v1's same-step value (1.05), and v1's
   pattern was a brief plateau near ~1.2 around steps 900–1300, then a continued
   rise to 1.50 by step 3000. **Bounded drift, not a blow-up — but not plateaued
   either.** If it keeps climbing past ~1.3–1.5 with no flattening, that is the
   first lever for a v3 (fewer steps / lower LR / lower `ar_kl_weight`), one
   variable at a time.
4. **Throughput/VRAM as expected.** ~3.3 s/step and ~16.4 GB peak on the A100 —
   in line with v1's whole-song run; sample events add the usual pauses
   (visible as spikes in `04_throughput.png`).
5. **Sample quality is the real test.** 12 samples so far (steps 0/250/500) with
   held-out lyrics; the point of this run is that checkpoints can now *show*
   pronunciation. Listen for lyric fidelity + arrangement coherence, not loss.

## Next steps

- Let the run reach 3000; re-run `generate_plots.py` and finalize this doc with
  the complete per-100 table and chart set.
- **Listen to the samples** (held-out lyrics) at 250/500/… compared with step 0
  (base). If pronunciation recovers but style regresses, `do_separation: true`
  is the next lever (`DECISIONS.md`), as a follow-up.
- Compare against v1's archived analysis (`v1_nolyrics_archived/ANALYSIS.md`) —
  same prompts, same loss framing, different captions.
