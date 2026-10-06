# Training analysis — `quran_ahh_r8` **revised** (AR+NAR, rank 32, no KL)

**LIVE SNAPSHOT** — captured **2026-10-06 ~02:27 UTC (05:27 Bahrain)** at **step 22,855 / 28,467
(80.3%)**. The run is still training (pid 37073; resumed `2026-10-06T01:09:51` from ckpt 19,500
after the 2026-10-05 pause); this is *not* a final analysis. Charts produced by the parametrized
`TRAINING_ANALYSIS/generate_plots.py`:

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

> **This directory is the revised rank-32 run.** The prior **AR-only, rank-8** run of the same
> name — completed 2026-10-05 07:39 UTC — is analyzed at
> [`../quran_ahh_r8/ANALYSIS.md`](../quran_ahh_r8/ANALYSIS.md). The run name `quran_ahh_r8` is a
> **misnomer (it is rank 32)**; the rename is **deferred until training completes** (renaming
> mid-run breaks resume) — see `agent_notes/current.md`. Not to be confused with the archived
> rank-8 `…/archive/quran_ahh_r8_rank8_aronly/`.

> Training-loss only — no in-training validation, **no samples** (`disable_sampling: true`).
> A first listening verdict (T4 probe c4500/c7500) is below.

## Run at a glance

| | |
|---|---|
| Config | `config/quran_ahh_r8.yml` (rank **32**/32 LoRA, **AR + NAR** via `ignore_if_contains: []`, `ar_kl_weight: 0.0`, EMA 0.999, `cot: off`, `train_window_frames: 0`, lr 1e-4, `adamw8bit`, bf16) |
| Model | YuE2 3B int8 `convrot8`, flowmatch, batch 1, grad-accum 1 |
| Dataset | `/content/quran_ahh_dataset/train` — **9,489 pairs** (AHH filtered, 3 reciters, single caption/clip, 50/50 simple/uthmani stratified); `steps: 28467` = **3 epochs** |
| GPU | Colab **L4** (23,034 MiB) |
| Caching | banked `_latent_cache.tar` — launch pass **< 1 s** (cache HIT, no re-encode) |
| Steps done | **22,855 / 28,467 (80.3%)** at snapshot |
| Step time | **median 1.238 s** (p10 1.207 / p90 1.763; max 4.719) → ~**0.75 steps/s** (0.75 recent) |
| Save cadence | every **1500** steps (~34 min) |
| Samples | **none** — grey verticals are checkpoint saves |
| Checkpoints | `_000001500 … _000022500` (**15**) + `optimizer.pt` (step 22500) — local + GCS (verified); next save = **24000** |
| GPU (resumed window) | mem p50 **8,430** / peak **8,730** MiB of 23,034; util p50 **48 %**, p90 100 %; temp p50 76 / max 80 °C; power p50 64 / max 75 W (limit 72) |
| ETA | **~125 min (2.1 h)** at the recent rate → completion ~**04:32 UTC / 07:32 Bahrain** |
| Health | clean — no tracebacks/OOM; VRAM flat; steady ~34 min save cadence |

## Charts

- [`01_loss_curves.png`](01_loss_curves.png) — all logged loss terms, raw + 25-step mean
- [`02_loss_main.png`](02_loss_main.png) — primary `loss/loss` with linear trend
- [`03_learning_rate.png`](03_learning_rate.png) — LR schedule (constant 1e-4)
- [`04_throughput.png`](04_throughput.png) — seconds/step and progress vs wall-clock
- [`05_gpu_usage.png`](05_gpu_usage.png) — L4 util / memory / temp / power

## Loss trend (per 1,000-step bin)

| steps | `loss/loss` | `loss/ar_ce` | residual (`loss/loss − ar_ce`) |
|---|---|---|---|
| 1–1000 | 4.8924 | 4.1625 | 0.7299 |
| 1001–2000 | 4.5615 | 3.8524 | 0.7091 |
| 2001–3000 | 4.4437 | 3.7499 | 0.6938 |
| 3001–4000 | 4.3674 | 3.6774 | 0.6900 |
| 4001–5000 | 4.3079 | 3.6310 | 0.6769 |
| 5001–6000 | 4.2735 | 3.5984 | 0.6751 |
| 6001–7000 | 4.2116 | 3.5472 | 0.6644 |
| 7001–8000 | 4.2126 | 3.5345 | 0.6780 |
| 8001–9000 | 4.1680 | 3.5015 | 0.6665 |
| 9001–10000 | 4.0953 | 3.4341 | 0.6613 |
| 10001–11000 | 4.0645 | 3.3996 | 0.6649 |
| 11001–12000 | 4.0479 | 3.3852 | 0.6627 |
| 12001–13000 | 4.0244 | 3.3674 | 0.6571 |
| 13001–14000 | 4.0316 | 3.3737 | 0.6578 |
| 14001–15000 | 4.0225 | 3.3626 | 0.6598 |
| 15001–16000 | **3.9897** | **3.3396** | 0.6502 |
| 16001–17000 | 3.9827 | 3.3323 | 0.6504 |
| 17001–18000 | 3.9643 | 3.3166 | 0.6477 |
| 18001–19000 | 3.9815 | 3.3294 | 0.6521 |
| 19001–20000 | **3.8272** | **3.1780** | 0.6492 |
| 20001–21000 | 3.8479 | 3.2006 | 0.6474 |
| 21001–22000 | 3.8640 | 3.2143 | 0.6498 |
| 22001–22855 | 3.8637 | 3.2210 | 0.6427 |

First-50 vs last-50 means: `loss/loss` **5.8409 → 3.8592** (−1.982), `loss/ar_ce`
**5.0275 → 3.2093** (−1.818), `additional_model_loss` identical. `loss/loss` minimum
**3.0433 @ step 22800**.

Per-checkpoint 500-step windows (`loss/loss` mean) — the "is later training better?" read:

| from step | 15,000 | 16,500 | 18,000 | 19,500 | 21,000 | 22,500 |
|---|---|---|---|---|---|---|
| `loss/loss` (next 500) | 4.0024 | 3.9907 | 4.0014 | **3.8073** | 3.8653 | 3.8620 |

## Observations / flags

1. **Only 4 metric keys**; `additional_model_loss` is byte-identical to `loss/ar_ce` (a duplicate
   label, not a second loss). The NAR/flow term is visible only as the residual
   `loss/loss − ar_ce` ≈ **0.65–0.68** (0.776 → 0.674 over the run). Both experts train, but the
   log gives no clean separate read on the NAR.
2. **`loss/ar_ce` has largely flattened.** It drifted to ~3.32 by 17k, dropped to **3.1780**
   (19001–20000), and has since held at **~3.20–3.22** — the descent has plateaued over the last
   ~4k steps (a small step-down at the 19,500 resume, then flat).
3. **Later checkpoints improved, then plateaued.** Next-500 means: 4.0024 @15k → **3.8073 @19.5k**
   → 3.8620 @22.5k. The step-down coincides with the 19.5k resume; since then it is flat — whether
   the extra steps help is a listening question, not a loss one.
4. **`loss/loss` is AR-dominated** — not a quality metric; the held-out free-run is the signal.
5. **The L4 is not the bottleneck.** util p50 **48 %** (p90 100 %), ~8.7 GB of 23 GB — data/CPU-bound;
   power saturates at the 72 W limit.
6. **First 50 are warmup-inflated** (~5.84) and the per-step series is noisy — trust the bins.
   Occasional multi-second spikes (max 5.80 s/step) align with the 1500-step saves.

## Listening verdict — round 1 (T4, c4500/c7500, 2026-10-05)

`…/audiocpp_inference/out/20261005-154621_quran_pt_probe/`. All "sound like Alhusary — more or
less"; **best = c7500_simple** (one mistake); **simple > uthmani**; **hard letters (ح، ع) much
improved vs rank-8** but not solved. Genuine improvement; not a plateau.

## Next — round 2 (T4, c10500 vs c16500)

Adapters banked: `…/quran_ahh_r8_rank32/convert/{c4500,c7500,c10500,c16500}/`. Run:
`INFERENCE/quran_pt_probe.py --prefix quran_ahh_r8_rank32/convert --arms c10500,c16500`.

## Checkpoints (on disk + GCS)

`/content/ai-toolkit/output/quran_ahh_r8/`: `quran_ahh_r8_000001500 … _000022500` (15 ×
117,500,848 B ≈ 112 MiB) + `optimizer.pt` (step 22500) + `loss_log.db`. GCS mirror verified
(15 checkpoints + optimizer + a `README.md` marker).

## Caveats

- **Mid-run snapshot** — re-run the command above for the final charts/bins.
- **No validation split / no samples**; the listening read is single-aya, single-listen — a human
  blind gate (`ab-blind-eval`) is still required before any merge.
- **Saved adapters are EMA weights** (decay 0.999).
- Absolute loss is not comparable to the rank-8 run (different rank/scope/epoch count).
- **Run name is a misnomer** (rank 32); rename deferred to post-training.

## Next steps

- Continue to **28,467** (~07:32 Bahrain at the current rate, if the VM stays up).
- **c10500 vs c16500 T4 probe** (round 2) — `c16500` is now banked; the immediate test.
- Human blind gate (`ab-blind-eval`) before any merge.
