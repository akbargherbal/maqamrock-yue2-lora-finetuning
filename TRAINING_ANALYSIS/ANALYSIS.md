# Training analysis — `akbar_arabic_rock_lora` (v2, lyric-conditioned captions)

> **IN PROGRESS — live snapshot at 2026-09-20 10:00 UTC, step ~1551 / 3000 (51.7%).**
> The run is still training. Numbers below are current, not final; this file is
> regenerated/updated as the run proceeds and finalized at step 3000. Charts are
> regenerated from the live `loss_log.db` and `gpu_usage.csv` with:
>
> ```bash
> python TRAINING_ANALYSIS/generate_plots.py
> ```
> (Note: the script's "recent rate"/ETA line can be distorted downward by a
> sample pause inside its last-100 window — use the median below, not that line.)

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
| Steps done | **~1551 / 3000 (51.7%)** at snapshot |
| Step time | **median 3.40 s/step** (p10 2.80 / p90 4.00, excluding sample pauses) |
| Sample tax | 4 samples per event at `duration: 360`, ~**10.5 min/event** (595–679 s gaps); **28 samples** so far (steps 0/250/…/1500) |
| Checkpoints | 6 so far: `_000000250` … `_000001500`, on disk and in GCS |
| ETA | **~2.4 h** remaining (~82 min of steps + ~63 min of 6 sample events) |
| GPU | peak **16.7 GB** (17134 MiB), mean 12.4 GB of 80 GB; ~93% util, ~286 W mean (incl. sample pauses) |
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
| 1501–1600 * | 5.203 | 4.041 | 1.281 | 4.298 |

\* partial window (to ~step 1551 at snapshot).

Confirmed metric keys: `additional_model_loss`, `learning_rate`, `loss/ar_ce`,
`loss/ar_kl`, `loss/loss`. There is **no** `nar_flow` key (see `DECISIONS.md`).

First-50 vs last-50 (step ~1551): `loss/loss` 6.23 → 5.20 (**−1.03**),
`loss/ar_ce` 5.19 → 4.04 (−1.15), `loss/ar_kl` 0.39 → 1.28 (**+0.90**),
`additional_model_loss` 5.26 → 4.29 (−0.97).

## v2 vs v1 at the same step (not apples-to-apples — read the caveat)

| window | `loss/loss` | `loss/ar_ce` | `loss/ar_kl` | `additional_model_loss` |
|---|---|---|---|---|
| v1 1–100 | 6.287 | 5.227 | 0.579 | 5.343 |
| **v2 1–100** | **6.015** | **4.942** | 0.588 | **5.060** |
| v1 1401–1500 | 5.536 | 4.409 | 1.194 | 4.648 |
| **v2 1401–1500** | **5.198** | **4.054** | 1.251 | **4.304** |
| v1 1501–1600 | 5.509 | 4.372 | 1.215 | 4.615 |
| **v2 1501–1600** | **5.203** | **4.041** | 1.281 | **4.298** |

**Caveat:** the audio targets are identical, but v2's prompts now contain the
lyrics, so the AR has the actual words to predict from. A lower `loss/ar_ce` is
therefore *expected* and is the mechanism by which pronunciation should be
protected — it is not by itself proof of better output. It does confirm the
lyric signal is reaching the AR (the v1 failure was that it never did).

## Observations / flags

1. **Healthy and still descending.** `loss/loss` fell steeply over the first
   ~100 steps then declined steadily; at the last window it is ~5.20. No
   tracebacks, no loss spikes beyond batch-1 noise, VRAM flat (never climbing).
2. **The lyric signal is present and stable.** `loss/ar_ce` sits ~0.33 lower
   than v1's at the same step (4.04 vs 4.37 by 1501–1600) — consistent with the
   AR conditioning on real lyrics rather than style tags alone.
3. **`loss/ar_kl` — the one to watch, and it has not plateaued.** It rose
   0.39 → 1.28 (+0.90) and is now *above* v1's same-step (1.19–1.22). v1 briefly
   paused near ~1.2 around steps 900–1300, then resumed to 1.50 by step 3000; v2
   has shown no such pause and is ahead of that curve. **Bounded drift, not a
   blow-up — but the trend is up.** If it keeps climbing past ~1.3–1.5 to the
   end, that is the first lever for a v3 (fewer steps / lower LR / lower
   `ar_kl_weight`), one variable at a time.
4. **Throughput/VRAM as expected.** Median 3.40 s/step, ~16.7 GB peak; each
   `duration: 360` sample event pauses training ~10.5 min (visible as spikes in
   `04_throughput.png`) — the ETA in `generate_plots.py`'s summary line can read
   too pessimistic if a sample pause falls in its last-100 window.
5. **Sample quality is the real test.** 28 samples so far (steps 0/250/…/1500)
   with held-out lyrics; the point of this run is that checkpoints can now
   *show* pronunciation. Listen for lyric fidelity + arrangement coherence, not
   loss.
6. **Ops note (resolved 2026-09-20):** `backup_to_gcp.py` uses append-only
   `gsutil rsync`, so the 4 smoke-test step-0 samples had persisted in the run's
   GCS `output/samples/` after the local wipe (8 step-0 files instead of 4).
   They were removed from GCS; the run prefix is now exactly 4 per step
   (0/250/…/1500, 28 total). No effect on training.

## Next steps

- Let the run reach 3000; re-run `generate_plots.py` and finalize this doc with
  the complete per-100 table and chart set.
- **Listen to the samples** (held-out lyrics) at 250/500/… compared with step 0
  (base). If pronunciation recovers but style regresses, `do_separation: true`
  is the next lever (`DECISIONS.md`), as a follow-up.
- Compare against v1's archived analysis (`v1_nolyrics_archived/ANALYSIS.md`) —
  same prompts, same loss framing, different captions.
