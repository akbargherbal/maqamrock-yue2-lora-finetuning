# Training analysis — `akbar_arabic_rock_lora` (v2, lyric-conditioned captions)

**COMPLETE** — finished **2026-09-20 ~12:23 UTC** at **step 3000 / 3000**.
`run.py` exited cleanly (no traceback; final adapter + optimizer written; 52
samples generated; GPU freed). Charts regenerated from the final `loss_log.db`
and `gpu_usage.csv` with:

```bash
python TRAINING_ANALYSIS/generate_plots.py
```

> This is **training loss only**. There is no held-out validation split, so
> quality must be judged from the generated samples too — loss alone can't tell
> you the LoRA learned the maqam or the lyrics.

> **What changed vs v1:** identical config/architecture (rank 32, EMA 0.999,
> `cot: off`, `train_window_frames: 0`, lr 1e-4, 3000 steps). The **only intended
> change is the dataset captions**: v2 captions now carry a real `[Lyrics]`
> block, closing the missing-signal gap that degraded Arabic pronunciation in v1
> (see `DECISIONS.md` / `PROGRESS.md`). v1's finished run and its analysis are
> preserved — the analysis as `TRAINING_ANALYSIS/v1_nolyrics_archived/`, the run
> as `...akbar_arabic_rock_lora_v1_nolyrics_archived` in GCS.

## Run at a glance

| | |
|---|---|
| Config | `config/akbar_arabic_rock_lora.yml` (rank 32 LoRA, EMA 0.999, `cot: off`, `train_window_frames: 0`, lr 1e-4) |
| Model | YuE2 3B int8 `convrot8`, flowmatch, batch 1 |
| Dataset | 267 clips, 267 **lyric-bearing** captions, one combined LoRA across four maqams |
| GPU | Colab **A100-SXM4-80GB** |
| Steps done | **3000 / 3000 (100%)**, latest logged step 2999 |
| Step time | **median 3.42 s/step** (p10 2.80 / p90 4.01, excluding sample pauses) |
| Sample tax | 4 samples/event at `duration: 360`, ~9.5–11 min/event; **13 events** (steps 0/250/…/3000) |
| Checkpoints | 11 numbered `_000000250` … `_000002750` **+ final `akbar_arabic_rock_lora.safetensors`** + `optimizer.pt` — on disk and in GCS (verified) |
| Samples | **52 mp3s** |
| GPU | peak **17.0 GB** (17382 MiB), mean 12.6 GB of 80 GB; ~93% util, ~289 W mean |
| Wall span | 4.73 h logged (includes 13 sample events) |
| Health | no tracebacks; loss descending cleanly; VRAM flat |

## Charts

- [`01_loss_curves.png`](01_loss_curves.png) — all four loss terms, raw + 25-step mean
- [`02_loss_main.png`](02_loss_main.png) — primary `loss/loss` with linear trend
- [`03_learning_rate.png`](03_learning_rate.png) — LR schedule (constant 1e-4)
- [`04_throughput.png`](04_throughput.png) — seconds/step and progress vs wall-clock
- [`05_gpu_usage.png`](05_gpu_usage.png) — A100 util / memory / temp / power

## Loss trend (per-100-step means)

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
| 2401–2500 | 4.943 | 3.769 | 1.429 | 4.055 |
| 2501–2600 | 4.974 | 3.797 | 1.411 | 4.080 |
| 2601–2700 | 4.954 | 3.756 | 1.458 | 4.048 |
| 2701–2800 | 4.928 | 3.735 | 1.426 | 4.021 |
| 2801–2900 | 4.901 | 3.711 | 1.476 | 4.006 |
| 2901–3000 | 4.845 | 3.649 | 1.525 | 3.954 |

Confirmed metric keys: `additional_model_loss`, `learning_rate`, `loss/ar_ce`,
`loss/ar_kl`, `loss/loss`. There is **no** `nar_flow` key (see `DECISIONS.md`).

First-50 vs last-50: `loss/loss` 6.23 → **4.79** (−1.44), `loss/ar_ce` 5.19 →
**3.61** (−1.57), `loss/ar_kl` 0.39 → **1.54** (+1.15), `additional_model_loss`
5.26 → **3.92** (−1.34). Minimum `loss/loss` 4.30 at step 2796.

## v2 vs v1, same configuration, different captions

| metric (first-50 → last-50) | v1 (no lyrics) | v2 (lyrics) |
|---|---|---|
| `loss/loss` | 6.49 → 5.17 | 6.23 → **4.79** |
| `loss/ar_ce` | 5.45 → 3.97 | 5.19 → **3.61** |
| `loss/ar_kl` | 0.37 → 1.50 | 0.39 → **1.54** |
| `additional_model_loss` | 5.53 → 4.27 | 5.26 → **3.92** |

| final window (2901–3000) | `loss/loss` | `loss/ar_ce` | `loss/ar_kl` | `additional_model_loss` |
|---|---|---|---|---|
| v1 | 5.167 | 3.976 | 1.480 | 4.272 |
| **v2** | **4.845** | **3.649** | 1.525 | **3.954** |

**Caveat:** the audio targets are identical, but v2's prompts now contain the
lyrics, so the AR has the actual words to predict from. Lower `ar_ce` is
therefore *expected* and is the mechanism by which pronunciation should be
protected — it is not by itself proof of better output. It does confirm the
lyric signal reached the AR (the v1 failure was that it never did).

## Observations / flags

1. **Completed cleanly.** `loss/loss` fell steeply over the first ~100 steps
   then declined steadily to 4.79 (last-50). No tracebacks, no loss spikes
   beyond batch-1 noise, VRAM flat (never climbing).
2. **`loss/ar_ce` is the dominant term and it is much lower than v1's** at the
   same steps and at the end (3.61 vs 3.97 last-50). This is the AR now
   conditioning on real lyrics rather than style tags alone — the intended
   effect of the v2 caption fix, not a claim of better audio.
3. **`loss/ar_kl` never plateaued, in either run — and v2 ended slightly
   higher.** v2 rose 0.39 → **1.54**, essentially tracking v1's 0.37 → 1.50
   (v2 marginally ahead throughout the second half). This is the adapted-AR
   distribution drifting from base under `ar_kl_weight: 0.2`; it stayed bounded
   (no blow-up), but it is an unbroken upward trend in both runs. **If a v3 is
   run, this is the first lever** — fewer steps, lower LR, or lower
   `ar_kl_weight` — one variable at a time (see `DECISIONS.md`).
4. **Diminishing returns by the end.** Per-100 `loss/loss` improvement fell to
   ~0.05–0.06 in the last 500 steps (4.94 → 4.85), the expected approach to a
   plateau at constant LR on a small, repetitive dataset. Remaining signal is in
   the samples.
5. **GPU healthy throughout:** median 3.42 s/step, peak 17.0 GB of 80 GB, ~93%
   util, ~289 W mean. Each `duration: 360` sample event paused training
   ~9.5–11 min (spikes in `04_throughput.png`).
6. **Everything persisted:** 11 numbered checkpoints + final adapter +
   `optimizer.pt` + `loss_log.db` + `config.yaml` + 52 samples are mirrored to
   GCS (`...akbar_arabic_rock_lora/output/`), verified by a no-diff dry-run
   `rsync`. The 4 stale smoke-test step-0 samples noted mid-run were removed.

## Next steps

- **Listen to the samples.** 52 audios (4 held-out-lyric prompts at each
  250-step mark, step 0 → 3000) are the only quality signal. Compare step 0
  (base) against 1250/2500/3000 and listen specifically for (a) Arabic
  pronunciation/lyric fidelity — the v2 goal — and (b) arrangement-level
  coherence from `train_window_frames: 0`.
- **Pick the artifact.** The final adapter and checkpoints 2250/2500/2750 are in
  GCS; if an earlier checkpoint sounds better (possible if late steps overfit),
  it's available. Errors in v1 increased with step count, so a mid checkpoint is
  worth auditioning.
- **If pronunciation recovers but style regresses:** `do_separation: true` (an
  explicit lyrics-only → vocals-only AR term) is the next lever — a follow-up
  run, not bundled in.
- **A v3, if any, should change one variable:** steps / LR / `ar_kl_weight`,
  given the unbroken `ar_kl` rise in both v1 and v2.
