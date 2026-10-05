# Training analysis — `quran_ahh_r8` **revised** (AR+NAR, rank 32, no KL)

**LIVE SNAPSHOT** — captured **2026-10-05 ~15:27 UTC** at **step 7,457 / 28,467 (26.2%)**.
The run is still training (pid 16301, started `2026-10-05T12:35:11`); this is *not* a final
analysis. Charts produced by the parametrized `TRAINING_ANALYSIS/generate_plots.py`:

```bash
cd /content/maqamrock-yue2-lora-finetuning
python TRAINING_ANALYSIS/generate_plots.py \
  --db /content/ai-toolkit/output/quran_ahh_r8/loss_log.db \
  --gpu-csv /content/logs/gpu_usage.csv \
  --total-steps 28467 --save-every 1500 \
  --outdir TRAINING_ANALYSIS/quran_ahh_r8_rank32 \
  --title "quran_ahh_r8 (AR+NAR rank-32 AHH pronunciation LoRA)" \
  --event-label "checkpoint save"
```

> **This directory is the revised rank-32 run.** The prior **AR-only, rank-8** run of the
> same name — completed 2026-10-05 07:39 UTC — is analyzed at
> [`../quran_ahh_r8/ANALYSIS.md`](../quran_ahh_r8/ANALYSIS.md); it shares the run name and
> the `/content/ai-toolkit/output/quran_ahh_r8/` path, which are now this run's.

> This is **training loss only** — no in-training validation and **no samples**
> (`train.disable_sampling: true`), so adapter quality must be judged offline from the
> checkpoints, not from loss alone (`docs/QURAN_PRON_REVIEW.md` §1).

## Run at a glance

| | |
|---|---|
| Config | `config/quran_ahh_r8.yml` (rank **32**/32 LoRA, **AR + NAR** via `ignore_if_contains: []`, `ar_kl_weight: 0.0`, EMA 0.999, `cot: off`, `train_window_frames: 0`, lr 1e-4, `adamw8bit`, bf16) |
| Model | YuE2 3B int8 `convrot8`, flowmatch, batch 1, grad-accum 1 |
| Dataset | `/content/quran_ahh_dataset/train` — **9,489 pairs** (AHH filtered, 3 reciters, single caption/clip, 50/50 simple/uthmani stratified); `steps: 28467` = **3 epochs** |
| GPU | Colab **L4** (23,034 MiB) |
| Caching | 9,489 clips on the banked `_latent_cache.tar` — pass completed **< 1 s** at launch (cache HIT, no re-encode) |
| Steps done | **7,457 / 28,467 (26.2%)** at snapshot |
| Step time | **median 1.247 s** (p10 1.216 / p90 1.737; mean 1.370, max 5.804) → ~**0.73 steps/s** avg (0.67 recent) |
| Save cadence | every **1500** steps (~34 min at current rate) |
| Samples | **none** (`disable_sampling: true`) — grey verticals are checkpoint saves |
| Checkpoints | `_000001500 / _3000 / _4500 / _6000` + `optimizer.pt` (step 6000) — local + GCS (verified); next save 7500 |
| GPU (training window) | mem p50 **9,038** / peak **9,150** MiB of 23,034; util p50 **50 %**, p90 100 %; temp p50 77 / max 80 °C; power p50 65 / max 75 W (limit 72) |
| Health | clean — no tracebacks/OOM; VRAM flat; matching ~34 min save cadence |

## Charts

- [`01_loss_curves.png`](01_loss_curves.png) — all logged loss terms, raw + 25-step mean
- [`02_loss_main.png`](02_loss_main.png) — primary `loss/loss` with linear trend
- [`03_learning_rate.png`](03_learning_rate.png) — LR schedule (constant 1e-4)
- [`04_throughput.png`](04_throughput.png) — seconds/step and progress vs wall-clock
- [`05_gpu_usage.png`](05_gpu_usage.png) — L4 util / memory / temp / power

## Loss trend (per 1,000-step bin)

| steps | `loss/loss` | `loss/ar_ce` | `additional_model_loss` | residual (`loss/loss − ar_ce`) |
|---|---|---|---|---|
| 1–1000 | 4.8924 | 4.1625 | 4.1625 | 0.7299 |
| 1001–2000 | 4.5615 | 3.8524 | 3.8524 | 0.7091 |
| 2001–3000 | 4.4437 | 3.7499 | 3.7499 | 0.6938 |
| 3001–4000 | 4.3674 | 3.6774 | 3.6774 | 0.6900 |
| 4001–5000 | 4.3079 | 3.6310 | 3.6310 | 0.6769 |
| 5001–6000 | 4.2735 | 3.5984 | 3.5984 | 0.6751 |
| 6001–7000 | 4.2116 | 3.5472 | 3.5472 | 0.6644 |
| 7001–7457 | 4.2369 | 3.5527 | 3.5527 | 0.6842 |

First-50 vs last-50 means (from `generate_plots.py`): `loss/loss` **5.8409 → 4.2155**
(−1.625), `loss/ar_ce` **5.0275 → 3.5393** (−1.488), `additional_model_loss` identical,
`learning_rate` constant 1e-4. `loss/loss` minimum **3.3256 @ step 6406**.

## Observations / flags

1. **Only 4 metric keys** — `additional_model_loss`, `learning_rate`, `loss/ar_ce`,
   `loss/loss`. **No `ar_kl`** (weight is now 0.0, correct) and **no separately-keyed NAR
   term**.
2. **`additional_model_loss` is byte-identical to `loss/ar_ce`** across all 7,465 rows
   (max abs diff `0.0`) — it is a duplicate label, **not** a second loss. Do not read it as
   the NAR expert.
3. **The NAR/flow term is only visible as the residual** `loss/loss − ar_ce` ≈ **0.68**
   (0.776 → 0.676, min 0.445 @ step 3029). It is descending, so the second (NAR) expert is
   being trained — but the logging gives **no clean, separate read on it**. Worth flagging
   to the evaluator: the AR+NAR claim is corroborated by the residual, not by a dedicated key.
4. **`loss/ar_ce` — the AR term — falls monotonically** across all bins (4.16 → 3.55) and is
   still inching down; the partial final bin ticks up slightly (+0.006), i.e. early plateau.
5. **`loss/loss` is AR-dominated**, so do **not** read it as audio quality; the held-out
   free-run eval is the only quality signal.
6. **The L4 is not the bottleneck.** Training util p50 **50 %** (p90 100 %), ~9 GB of
   23 GB — data/CPU-bound, same profile as the prior runs. Power saturates (p90 = 72 W limit).
7. **First 50 are warmup-inflated** (`loss/loss` ~5.84); the per-step series is noisy —
   trust the bins, not single steps.
8. **Throughput shows occasional multi-second spikes** (max 5.80 s/step), aligning with the
   1500-step saves; the median stays ~1.25 s/step.

## Checkpoints (on disk + GCS)

`/content/ai-toolkit/output/quran_ahh_r8/`:
`quran_ahh_r8_000001500.safetensors`, `_000003000`, `_000004500`, `_000006000`
(each 117,500,848 B ≈ 112 MiB) + `optimizer.pt` (119,807,781 B) + `loss_log.db`.
GCS mirror `…/quran_ahh_r8/output/` verified (9 objects; last loss_log.db sync 15:23 UTC).

## Caveats

- **Mid-run snapshot** — numbers will move; re-run the command above (or wait for
  completion) for the final charts and bins.
- **No validation split and no samples** (`disable_sampling: true`), so loss says nothing
  about pronunciation. That requires the offline free-run held-out 2:255 eval per checkpoint
  (`docs/QURAN_PRON_REVIEW.md` §2.1). The T4 probe driver (`INFERENCE/quran_pt_probe.py`)
  and the prior rank-8 arms target that; the revised run's arms are not yet converted.
- **Saved adapters are EMA weights** (`ema_config.use_ema: true`, decay 0.999).
- Absolute loss is not comparable to the rank-8 run (different rank/scope/data epoch count);
  only the *shape* (monotone `ar_ce` down) is.

## Next steps

- Let it reach the next save (7500) and continue to 28,467; regenerate charts at checkpoints.
- Convert the numbered checkpoints to audio.cpp AR/NAR adapters and run the held-out 2:255
  free-run sweep; **human blind gate** (`ab-blind-eval`) before any merge.
- If the NAR term matters to the verdict, add a dedicated NAR-loss log key (or inspect the
  toolkit's metric emission) so it is no longer only a residual.
