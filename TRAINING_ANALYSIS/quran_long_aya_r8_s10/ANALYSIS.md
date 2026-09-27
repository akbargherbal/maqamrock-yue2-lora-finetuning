# Training analysis — `quran_long_aya_r8_s10` (long-aya Quran pronunciation LoRA, 10% subsample)

**COMPLETE** — finished **2026-09-27 12:14 UTC** at **step 8100 / 8100** (1 epoch over the
8,100-pair frozen subsample). `run.py` **self-stopped at its target**: final adapter +
optimizer written, **no traceback, no OOM**. Final adapter metadata:
`training_info = {"step": 8100, "epoch": 0}`.

Charts produced by the parametrized `TRAINING_ANALYSIS/generate_plots.py`:

```bash
cd /content/maqamrock-yue2-lora-finetuning
python TRAINING_ANALYSIS/generate_plots.py \
  --db /content/ai-toolkit/output/quran_long_aya_r8_s10/loss_log.db \
  --gpu-csv /content/logs/gpu_usage.csv \
  --total-steps 8100 --save-every 1500 \
  --outdir TRAINING_ANALYSIS/quran_long_aya_r8_s10 \
  --title "quran_long_aya_r8_s10 (long-aya Quran pron LoRA, 10% subsample)" \
  --event-label "checkpoint save"
```

> This is **training loss only** — no in-training validation and no samples
> (`train.disable_sampling: true`), so adapter quality must be judged offline from the
> checkpoints, not from loss alone.

## Run at a glance

| | |
|---|---|
| Config | `config/quran_long_aya_r8_s10.yml` (rank **8** LoRA, AR-only via `ignore_if_contains: ["transformer.nar"]`, EMA 0.999, `cot: off`, `train_window_frames: 0`, lr 1e-4) |
| Model | YuE2 3B int8 `convrot8`, flowmatch, batch 1, grad-accum 1 |
| Dataset | `/content/quran_long_aya_dataset_s10/train` — **8,100 pairs** (frozen, seeded 10% sample of train combos; both `_simple`/`_uthmani`); 8,100 steps = 1 epoch |
| GPU | Colab **L4** (23,034 MiB) |
| Caching | 8,100 clips in **~1 h** before step 1 (measured ~1.1–3.8 files/s encode) — banked as a tar |
| Steps done | **8100 / 8100 (100%)**, steps 1–8099 logged (final save carries step 8100) |
| Step time | **median 1.239 s** (p10 0.913 / p90 1.454) → ~**0.81 steps/s**; **2.77 h** logged span (2:46 for steps 1–8100) |
| Samples | **none** (`disable_sampling: true`) — grey verticals are checkpoint saves |
| Checkpoints | `…_000001500 / _3000 / _4500 / _6000 / _7500` + final no-step `quran_long_aya_r8_s10.safetensors` (step 8100); `optimizer.pt` |
| GPU | mem p50 **8,950** / peak 9,478 MiB of 23,034; util p50 **38 %**, p90 100 %; temp p50 76 / max 80 °C; power p50 60 / max 76 W (limit 72) |
| Backup | local + GCS (`…/quran_long_aya_r8_s10/output/`) |
| Health | no tracebacks; loss descending; VRAM flat; **data-bound** (bursty util) |

## Loss trend (per 810-step decile)

| steps | `loss/loss` | `loss/ar_ce` | `loss/ar_kl` |
|---|---|---|---|
| 1–810 | 5.826 | 4.603 | 0.946 |
| 811–1620 | 5.561 | 4.292 | 1.191 |
| 1621–2430 | 5.471 | 4.196 | 1.243 |
| 2431–3240 | 5.454 | 4.158 | 1.274 |
| 3241–4050 | 5.393 | 4.107 | 1.311 |
| 4051–4860 | 5.400 | 4.088 | 1.337 |
| 4861–5670 | 5.360 | 4.048 | 1.359 |
| 5671–6480 | 5.339 | 4.016 | 1.374 |
| 6481–7290 | 5.309 | 3.994 | 1.396 |
| 7291–8100 | **5.280** | **3.968** | 1.392 |

First-50 vs last-50 means (from `generate_plots.py`): `loss/loss` **6.568 → 5.256**
(−1.312), `loss/ar_ce` **5.499 → 3.967** (−1.532), `additional_model_loss` 5.534 → 4.243
(−1.291), `loss/ar_kl` **0.174 → 1.381** (+1.207). Minimum `loss/loss` **4.205 @ step 7506**
(near end, not an early dip). Metric keys: `additional_model_loss`, `learning_rate`,
`loss/ar_ce`, `loss/ar_kl`, `loss/loss` — same five as v1/v2, **no `nar_flow`**.

## Observations / flags

1. **Completed cleanly.** Self-stopped at the `steps: 8100` target; final adapter + optimizer
   written; no tracebacks/OOM; VRAM flat.
2. **`loss/ar_ce` — the term that actually trains this adapter — fell monotonically** across
   all ten deciles (4.60 → 3.97). This is the AR next-token loss on the recitation text and the
   only thing the adapter optimises (NAR excluded, its flow loss detached). Still inching down
   at the end, so 1 epoch is not obviously over-long by this metric.
3. **`loss/ar_kl` rose monotonically and bounded** (0.17 → 1.38, deciles flat after ~step 5670) —
   the **same shape as v1/v2** and the reference AR-only run (0.21 → 1.53). The trust-region KL
   on AR distributions; the unbroken early rise is the pattern to watch if quality over-drifts.
4. **`loss/loss` here is AR-dominated** (`additional_model_loss` ≈ `ar_ce`), as expected for an
   AR-only adapter. Do not read `loss/loss` as audio quality.
5. **Diminishing returns.** Decile deltas of `loss/loss`: −0.265, −0.090, −0.017, −0.061, +0.007,
   −0.040, −0.021, −0.030, −0.029 — the tail is small but mostly still negative; `ar_ce`'s tail
   stayed monotone.
6. **The L4 was not the bottleneck.** util **p50 38 %** (p90 100 %), ~9 GB of 23 GB, yet
   median 1.239 s/step — **data/CPU-bound** (same as the reference run: A100 sat at ~22 % util).
   The GPU idles waiting on the single-batch audio path between compute bursts.
7. **First 50 are warmup-inflated** (`loss/loss` starts ~6.6 including the early spike); the
   per-step series is noisy — trust the deciles, not single steps.

## Caveats

- **No validation split and no samples**, so this says nothing about whether pronunciation
  actually improved. That requires the checkout-point offline eval (merge → convert → generate
  on a T4; `docs/PRON_LORA_MERGE.md`, `INFERENCE/pron_ckpt_sweep.py`) plus the AR-loss replay
  (`offline_ar_loss_replay.py`).
- **This is the 10% subsample.** Absolute loss is not comparable to the full-set plan (81,006
  pairs) or to the reference (6,100 pairs; different data/captions/GPU). Only the *shape*
  (monotone `ar_ce` down, `ar_kl` up) is directly comparable, and it matches.

## Next steps

- Evaluate the **6 checkpoints** on a T4 (compare pronunciation across steps; prefer an earlier
  checkpoint if late steps over-drift).
- **Extend or conclude:** the run targets 8,100; to train more, bump `steps` and relaunch — it
  auto-resumes from step 8100 (cache + optimizer preserved; `docs/PAUSE_RESUME.md`).
