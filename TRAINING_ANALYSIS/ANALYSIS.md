# Training analysis — `akbar_arabic_rock_lora` (v2, lyric-conditioned captions)

> **IN PROGRESS — live snapshot at 2026-09-20 11:24 UTC, step ~2481 / 3000 (82.7%).**
> The run is still training (~30 min of steps + 3 sample events left). Numbers
> below are current, not final; this file is regenerated/updated as the run
> proceeds and finalized at step 3000. Charts are regenerated from the live
> `loss_log.db` and `gpu_usage.csv` with:
>
> ```bash
> python TRAINING_ANALYSIS/generate_plots.py
> ```
> (Note: the script's "recent rate"/ETA line can be distorted downward by a
> sample pause inside its last-100 window — use the median below.)

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
| Steps done | **~2481 / 3000 (82.7%)** at snapshot |
| Step time | **median 3.41 s/step** (p10 2.80 / p90 4.00, excluding sample pauses) |
| Sample tax | 4 samples per event at `duration: 360`, ~**10.5 min/event** (594–679 s gaps); **40 samples** so far (steps 0/250/…/2250) |
| Checkpoints | 9 so far: `_000000250` … `_000002250`, on disk and in GCS |
| ETA | **~1 h** remaining (~30 min of steps + 3 sample events) |
| GPU | peak **16.9 GB** (17282 MiB), mean 12.7 GB of 80 GB; ~94% util, ~294 W mean (incl. sample pauses) |
| Health | no tracebacks; loss descending cleanly; VRAM flat |

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
| 601–700 | 5.339 | 4.227 | 1.160 | 4.459 |
| 701–800 | 5.353 | 4.215 | 1.161 | 4.447 |
| 801–900 | 5.326 | 4.172 | 1.177 | 4.407 |
| 901–1000 | 5.274 | 4.153 | 1.194 | 4.392 |
| 1001–1100 | 5.280 | 4.138 | 1.198 | 4.378 |
| 1101–1200 | 5.231 | 4.093 | 1.225 | 4.338 |
| 1201–1300 | 5.261 | 4.108 | 1.230 | 4.354 |
| 1301–1400 | 5.198 | 4.048 | 1.261 | 4.300 |
| 1401–1500 | 5.198 | 4.054 | 1.251 | 4.304 |
| 1501–1600 | 5.198 | 4.041 | 1.275 | 4.296 |
| 1601–1700 | 5.122 | 3.962 | 1.313 | 4.225 |
| 1701–1800 | 5.164 | 4.010 | 1.272 | 4.264 |
| 1801–1900 | 5.110 | 3.961 | 1.323 | 4.225 |
| 1901–2000 | 5.080 | 3.920 | 1.327 | 4.185 |
| 2001–2100 | 5.086 | 3.906 | 1.353 | 4.177 |
| 2101–2200 | 5.061 | 3.900 | 1.326 | 4.165 |
| 2201–2300 | 5.019 | 3.847 | 1.400 | 4.127 |
| 2301–2400 | 5.005 | 3.858 | 1.386 | 4.135 |
| 2401–2500 * | 4.936 | 3.763 | 1.426 | 4.048 |

\* partial window (to ~step 2481 at snapshot).

Confirmed metric keys: `additional_model_loss`, `learning_rate`, `loss/ar_ce`,
`loss/ar_kl`, `loss/loss`. There is **no** `nar_flow` key (see `DECISIONS.md`).

First-50 vs last-50 (step ~2481): `loss/loss` 6.23 → 4.94 (**−1.29**),
`loss/ar_ce` 5.19 → 3.77 (−1.42), `loss/ar_kl` 0.39 → 1.42 (**+1.04**),
`additional_model_loss` 5.26 → 4.05 (−1.21). Minimum `loss/loss` 4.43 at step
2451 (single-step noise).

## v2 vs v1 at the same step (not apples-to-apples — read the caveat)

| window | `loss/loss` | `loss/ar_ce` | `loss/ar_kl` | `additional_model_loss` |
|---|---|---|---|---|
| v1 1–100 | 6.287 | 5.227 | 0.579 | 5.343 |
| **v2 1–100** | **6.015** | **4.942** | 0.588 | **5.060** |
| v1 1901–2000 | 5.409 | 4.252 | 1.280 | 4.508 |
| **v2 1901–2000** | **5.080** | **3.920** | 1.327 | **4.185** |
| v1 2401–2500 | 5.304 | 4.126 | 1.392 | 4.405 |
| **v2 2401–2500** | **4.936** | **3.763** | 1.426 | **4.048** |

**Caveat:** the audio targets are identical, but v2's prompts now contain the
lyrics, so the AR has the actual words to predict from. A lower `loss/ar_ce` is
therefore *expected* and is the mechanism by which pronunciation should be
protected — it is not by itself proof of better output. It does confirm the
lyric signal is reaching the AR (the v1 failure was that it never did).

## Observations / flags

1. **Healthy and still descending.** `loss/loss` fell steeply over the first
   ~100 steps then declined steadily; last window ~4.94. No tracebacks, no loss
   spikes beyond batch-1 noise, VRAM flat (never climbing).
2. **The lyric signal is present and stable.** `loss/ar_ce` sits ~0.33–0.36
   lower than v1's at the same step (e.g. 3.76 vs 4.13 by 2401–2500) —
   consistent with the AR conditioning on real lyrics rather than style tags
   alone.
3. **`loss/ar_kl` — still rising, no plateau, and now tracking v1 closely.**
   It rose 0.39 → 1.42 (+1.04); at 2401–2500 v2 is 1.43 vs v1's 1.39. v1 ended
   its run at 1.48. With ~520 steps left, **v2 looks set to finish at ~1.5 or
   above** — the same unbounded-drift signature v1 showed. Bounded, not a
   blow-up, but if a v3 is run this is still the first lever (fewer steps /
   lower LR / lower `ar_kl_weight`), one variable at a time.
4. **Diminishing returns.** The per-100 drop has shrunk to ~0.07–0.08 by
   2201–2500 (e.g. 5.019 → 5.005 → 4.936), the expected approach to a plateau
   at constant LR on a small, repetitive dataset. Remaining signal is in the
   samples.
5. **Throughput/VRAM as expected.** Median 3.41 s/step, ~16.9 GB peak; each
   `duration: 360` sample event pauses training ~10.5 min (spikes in
   `04_throughput.png`).
6. **Sample quality is the real test.** 40 samples so far (steps 0/250/…/2250)
   with held-out lyrics — the point of this run is that checkpoints can now
   *show* pronunciation. Listen for lyric fidelity + arrangement coherence, not
   loss.
7. **Ops note (resolved 2026-09-20):** `backup_to_gcp.py` uses append-only
   `gsutil rsync`, so the 4 smoke-test step-0 samples had persisted in the run's
   GCS `output/samples/` after the local wipe (8 step-0 files instead of 4).
   They were removed from GCS; the run prefix is now exactly 4 per step. No
   effect on training.

## Next steps

- Let the run reach 3000; re-run `generate_plots.py` and finalize this doc with
  the complete per-100 table and chart set.
- **Listen to the samples** (held-out lyrics) at 250/500/… compared with step 0
  (base). If pronunciation recovers but style regresses, `do_separation: true`
  is the next lever (`DECISIONS.md`), as a follow-up.
- Compare against v1's archived analysis (`v1_nolyrics_archived/ANALYSIS.md`) —
  same prompts, same loss framing, different captions.
