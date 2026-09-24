# Training analysis — `pron_lora_ar_only_r8` (AR-only pronunciation LoRA)

**COMPLETE** — finished **2026-09-24 ~07:27 UTC** at **step 6100 / 6100**
(= 1 epoch over 6,099 usable pairs). `run.py` exited cleanly: final adapter +
optimizer written, **no traceback, no OOM**. Final adapter metadata:
`training_info = {"step": 6100, "epoch": 1}`.

Charts produced by the parametrized `TRAINING_ANALYSIS/generate_plots.py`:

```bash
cd /content/maqamrock-yue2-lora-finetuning
python TRAINING_ANALYSIS/generate_plots.py \
  --db /content/ai-toolkit/output/pron_lora_ar_only_r8/loss_log.db \
  --total-steps 6100 --save-every 1525 \
  --outdir TRAINING_ANALYSIS/pron_lora_ar_only_r8 \
  --title "pron_lora_ar_only_r8 (AR-only pronunciation LoRA, rank 8)" \
  --event-label "checkpoint save"
```

> This is **training loss only** — there is no in-training validation
> (`docs/PRON_LORA_VERIFICATION.md` A3) and no samples
> (`train.disable_sampling: true`), so adapter quality must be judged offline
> from the checkpoints, not from loss alone.

## Run at a glance

| | |
|---|---|
| Config | `config/pron_lora_ar_only.yml` (rank **8** LoRA, AR-only via `ignore_if_contains: ["transformer.nar"]`, EMA 0.999, `cot: off`, `train_window_frames: 0`, lr 1e-4) |
| Model | YuE2 3B int8 `convrot8`, flowmatch, batch 1, grad-accum 1 |
| Dataset | `/content/pron_dataset/train` — 6,100 pairs, **6,099 usable** (one mp3 failed to decode at cache time); 6,100 steps = 1 epoch |
| GPU | Colab **A100-SXM4-80GB** |
| Caching | 6,100 clips in **12:26** before step 1 (expected, not a stall) |
| Steps done | **6100 / 6100 (100%)**, steps 1–6099 logged (final save carries step 6100) |
| Step time | **median 0.886 s** (p10 0.872 / p90 0.917) → ~**1.11 steps/s**; **1.52 h** logged training |
| Samples | **none** (`disable_sampling: true`) — grey verticals are checkpoint saves |
| Checkpoints | `…_000001525`, `…_000003050`, `…_000004575` (numbered) + final no-step `pron_lora_ar_only_r8.safetensors` (step 6100); `optimizer.pt` |
| GPU | peak **10,794 MiB (10.5 GB)** of 80 GB; util p50 **22 %**; power mean 79 W; temp ≤ 35 °C |
| Backup | local + GCS (`…/pron_lora_ar_only_r8/output/`, 9 objects / 73.27 MiB) |
| Health | no tracebacks; loss descending; VRAM flat |

## Charts

- [`01_loss_curves.png`](01_loss_curves.png) — all four loss terms, raw + 25-step mean
- [`02_loss_main.png`](02_loss_main.png) — primary `loss/loss` with linear trend
- [`03_learning_rate.png`](03_learning_rate.png) — LR schedule (constant 1e-4)
- [`04_throughput.png`](04_throughput.png) — seconds/step and progress vs wall-clock
- [`05_gpu_usage.png`](05_gpu_usage.png) — A100 util / memory / temp / power

## Loss trend (per-610-step means, deciles)

| steps | `loss/loss` | `loss/ar_ce` | `loss/ar_kl` | `additional_model_loss` |
|---|---|---|---|---|
| 1–610 | 6.457 | 5.130 | 1.019 | 5.333 |
| 611–1220 | 6.069 | 4.708 | 1.301 | 4.968 |
| 1221–1830 | 5.985 | 4.604 | 1.363 | 4.877 |
| 1831–2440 | 5.980 | 4.574 | 1.399 | 4.853 |
| 2441–3050 | 5.914 | 4.517 | 1.435 | 4.804 |
| 3051–3660 | 5.882 | 4.484 | 1.451 | 4.774 |
| 3661–4270 | 5.875 | 4.463 | 1.491 | 4.762 |
| 4271–4880 | 5.813 | 4.396 | 1.503 | 4.697 |
| 4881–5490 | 5.792 | 4.391 | 1.501 | 4.692 |
| 5491–6099 | **5.756** | **4.362** | 1.505 | **4.663** |

First-50 vs last-50: `loss/loss` 7.36 → **5.815** (−1.55), `loss/ar_ce` 6.13 →
**4.397** (−1.73), `loss/ar_kl` 0.21 → **1.533** (+1.33),
`additional_model_loss` 6.17 → **4.703** (−1.47). Minimum `loss/loss` **4.402
at step 5870** (end-of-run, not an early dip).

Metric keys: `additional_model_loss`, `learning_rate`, `loss/ar_ce`,
`loss/ar_kl`, `loss/loss` — same five as v1/v2, **no `nar_flow`** key.

## Observations / flags

1. **Completed cleanly.** `loss/loss` fell steeply over the first ~200 steps
   (7.4 → ~6.2) then declined steadily to **5.76** (last decile). No tracebacks,
   no loss spikes beyond batch-1 noise, VRAM flat, and the global minimum is at
   the very end (step 5870) — no late overfitting regression in the loss.
2. **`loss/ar_ce` — the term that actually trains this adapter — kept falling to
   the end**: 5.13 (1–610) → **4.36** (5491–6099), last-50 4.40. This is the AR
   next-token loss on the recitation text and is the only thing the adapter
   optimises (NAR is excluded; its flow loss is detached). It was still
   improving at step 6100, so 1 epoch is not obviously over-long by this metric.
3. **`loss/ar_kl` rose monotonically the whole way, exactly as in v1 and v2**:
   0.21 → **1.53** last-50, deciles 1.02 → 1.51, max **2.19** (step 4313). It is
   the trust-region KL(base ‖ lora) on AR distributions, **bounded** (no
   blow-up), but the unbroken upward drift is the same pattern the whole-song
   runs showed. If the pron adapter turns out to over-drift the AR (audible on
   the offline eval), `ar_kl_weight` / fewer steps / lower LR is the first
   single-variable lever.
4. **`loss/loss` here is AR-dominated** (`additional_model_loss` ≈ `ar_ce`), as
   expected for an AR-only adapter — the NAR/flow path contributes ~no gradient
   (A4 in `PRON_LORA_VERIFICATION.md`). Do not read `loss/loss` as audio quality.
5. **Diminishing returns, but not flat.** Per-610-step `loss/loss` deltas:
   −0.39, −0.08, −0.01, −0.07, −0.03, −0.01, −0.06, −0.02, −0.04. The tail is
   small but still negative, and `ar_ce` (the objective that matters) also kept
   inching down. Unlike v2 (which plateaued hard by 3000), this run had a little
   headroom left — worth noting if a longer run is ever considered.
6. **The A100 was not the bottleneck.** Median util **22 %**, power mean 79 W,
   VRAM only 10.5 GB of 80 GB, yet step time is **0.886 s** — barely faster than
   the L4 smoke's ~1.0 s/step (which was warmup-inflated). This run is
   data/CPU-bound (short-clip VAE/audio path), not compute-bound; an A100 is
   over-provisioned for it. Full epoch ≈ 1.5 h.
7. **Early transients, not trends.** Max loss at step 19 (9.42) is warmup; the
   apparent minima at steps 547 (`loss/loss` 4.41) and 2546 (`ar_ce` 2.97) are
   single-batch dips. The only `loss/loss` minimum now (4.40 @ 5870) is genuine.

## Caveats

- **No validation split** and **no samples**, so this says nothing about whether
  articulation actually improves. That requires the offline AR-loss replay over
  the 180 `val` pairs described in `PRON_LORA_VERIFICATION.md` A3, run per
  checkpoint.
- **Not comparable to v1/v2 loss levels**: different dataset (short recitation
  clips vs whole songs), rank (8 vs 32), and objective (AR-only vs full). Only
  the *shape* of `ar_kl` is directly comparable, and it matches both.
- **No `_000006100` numbered checkpoint** — the numbered saves are at 1525/3050/
  4575 (loop runs steps 0–6099); the post-loop save `pron_lora_ar_only_r8.safetensors`
  *is* the step-6100 artifact (metadata-verified), not a separate extra file.

## Next steps

- Offline-eval all four artifacts (`…_000001525 / _000003050 / _000004575` +
  final) over the 180 `val` pairs (`loss/ar_ce`, `loss/ar_kl`); prefer an earlier
  checkpoint if late steps over-drift.
- Merge with the frozen v2 style LoRA only after that audit (next session).
