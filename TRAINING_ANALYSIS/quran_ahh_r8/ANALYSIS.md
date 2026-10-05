# Training analysis — `quran_ahh_r8` (AR-only AHH pronunciation LoRA)

**COMPLETE** — finished **2026-10-05 07:39 UTC** at **step 9,489 / 9,489 (100%)** (1 epoch
over the 9,489-pair AHH set). `run.py` **self-stopped at its target**: final adapter +
`optimizer.pt` written, **no traceback, no OOM**. Charts produced by the parametrized
`TRAINING_ANALYSIS/generate_plots.py`:

```bash
cd /content/maqamrock-yue2-lora-finetuning
python TRAINING_ANALYSIS/generate_plots.py \
  --db /content/ai-toolkit/output/quran_ahh_r8/loss_log.db \
  --gpu-csv /content/logs/gpu_usage.csv \
  --total-steps 9489 --save-every 1500 \
  --outdir TRAINING_ANALYSIS/quran_ahh_r8 \
  --title "quran_ahh_r8 (AR-only AHH pronunciation LoRA)" \
  --event-label "checkpoint save"
```

> This is **training loss only** — no in-training validation and **no samples**
> (`train.disable_sampling: true`), so adapter quality must be judged offline from the
> checkpoints, not from loss alone (`docs/QURAN_PRON_REVIEW.md` §1).

## Run at a glance

| | |
|---|---|
| Config | `config/quran_ahh_r8.yml` (rank **8** LoRA, **AR-only** via `ignore_if_contains: ["transformer.nar"]`, EMA 0.999, `cot: off`, `train_window_frames: 0`, lr 1e-4, `adamw8bit`, bf16) |
| Model | YuE2 3B int8 `convrot8`, flowmatch, batch 1, grad-accum 1 |
| Dataset | `/content/quran_ahh_dataset/train` — **9,489 pairs** (AHH filtered, 3 reciters, single caption/clip, 50/50 simple/uthmani stratified); 9,489 steps = 1 epoch |
| GPU | Colab **L4** (23,034 MiB) |
| Caching | 9,489 clips in **~50 min** before step 1 (~3–4 files/s encode); banked as `_latent_cache.tar` (703 MiB) to GCS at 04:51:16Z |
| Steps done | **9,489 / 9,489 (100%)**, steps 1–9,488 logged (the final no-step save carries step 9,489) |
| Step time | **median 0.960 s** (p10 0.903 / p90 1.391) → ~**0.93 steps/s**; **2.82 h** logged span (log loop 2:49:12) |
| Samples | **none** (`disable_sampling: true`) — grey verticals are checkpoint saves |
| Checkpoints | `…_000001500 / _3000 / _4500 / _6000 / _7500 / _9000` + final no-step `quran_ahh_r8.safetensors` (9,489); `optimizer.pt` — local + GCS (verified) |
| GPU (training window) | mem p50 **8,962** / peak 9,978 MiB of 23,034; util p50 **64 %**, p90 100 %; temp p50 77 / max 79 °C; power p50 66 / max 76 W (limit 72) |
| Health | **one launch crash at step 0** (cuDNN orphan libs, fixed — see below); clean thereafter |

## Launch crash (step 0) — resolved before training began

The first `train_ctl.py start` died during the latent-cache build, in the VAE `conv1d`:
`CUDNN_STATUS_SUBLIBRARY_VERSION_MISMATCH`. Cause: two cuDNN libs orphaned by the CUDA-13
base image (`libcudnn_engines_tensor_ir.so.9`, `libcudnn_ext.so.9`) that are not part of the
pinned `nvidia-cudnn-cu13==9.20.0.48` wheel; the 9.20 frontend loaded the stale one. Resolved
by moving them aside; `bootstrap/setup.sh` now prunes non-manifest libs and the verify block
runs a cuDNN conv (committed `f68f7a6` on `pron-lora-long-aya`, cherry-picked to `main` as
`ab8640d`). No training progress was lost (the crash was before step 1). Full write-up:
`docs/COMMAND_HANDOVER_GOTCHAS.md` (2026-10-05).

## Loss trend (per 1,000-step bin)

| steps | `loss/loss` | `loss/ar_ce` | `loss/ar_kl` | `additional_model_loss` |
|---|---|---|---|---|
| 1–1000 | 5.5045 | 4.3277 | 1.0466 | 4.5370 |
| 1001–2000 | 5.2434 | 4.0161 | 1.2948 | 4.2750 |
| 2001–3000 | 5.1741 | 3.9269 | 1.3640 | 4.1997 |
| 3001–4000 | 5.1050 | 3.8508 | 1.4053 | 4.1319 |
| 4001–5000 | 5.0916 | 3.8259 | 1.4425 | 4.1144 |
| 5001–6000 | 5.0603 | 3.7848 | 1.4673 | 4.0782 |
| 6001–7000 | 5.0210 | 3.7517 | 1.4762 | 4.0470 |
| 7001–8000 | 5.0070 | 3.7297 | 1.5004 | 4.0297 |
| 8001–9000 | 4.9702 | 3.7032 | 1.5041 | 4.0040 |
| 9001–9488 | **4.9807** | **3.6840** | 1.5339 | 3.9908 |

First-50 vs last-50 means (from `generate_plots.py`): `loss/loss` **6.331 → 5.003**
(−1.327), `loss/ar_ce` **5.310 → 3.719** (−1.590), `loss/ar_kl` **0.227 → 1.552** (+1.326),
`additional_model_loss` 5.355 → 4.030 (−1.325). Metric keys are the usual five
(`additional_model_loss`, `learning_rate`, `loss/ar_ce`, `loss/ar_kl`, `loss/loss`) —
**no `nar_flow`** (AR-only). The `loss/loss` **minimum 3.96 @ step 4356** is a one-off
(same step as the `ar_ce`/`additional` minima — a single anomalous low sample), not a trend.

## Observations / flags

1. **Completed cleanly.** Self-stopped at the `steps: 9489` target; final adapter + optimizer
   written; no tracebacks/OOM; VRAM flat. (One step-0 cuDNN crash before training, fixed.)
2. **`loss/ar_ce` — the term that trains this adapter — falls monotonically** across all ten
   bins (4.33 → 3.68) and is still inching down at the end. By this metric 1 epoch is not
   obviously over-long.
3. **`loss/ar_kl` rises then flattens** (1.05 → 1.53, last bins 1.500 → 1.504 → 1.534). The
   trust-region KL on AR distributions; **same shape as the prior pron runs** (s10: 0.17 →
   1.38; reference: 0.21 → 1.53). Bounded, no blow-up — but the unbroken early rise is the
   lever to watch if quality over-drifts.
4. **`loss/loss` is AR-dominated** (`additional_model_loss` ≈ `ar_ce`), as expected for an
   AR-only adapter. **Do not read `loss/loss` as audio quality.**
5. **Platform.** Per-1,000 deltas of `loss/loss`: −0.261, −0.069, −0.069, −0.013, −0.031,
   −0.039, −0.014, −0.037, **+0.011** — the tail is small and the final partial bin turns
   marginally up, i.e. a genuine plateau at constant LR.
6. **The L4 is not the bottleneck.** Training util p50 **64 %** (p90 100 %), ~9 GB of 23 GB,
   median 0.960 s/step — data/CPU-bound, same as the s10 L4 run.
7. **First 50 are warmup-inflated** (`loss/loss` ~6.33 including the early spike); the
   per-step series is noisy — trust the bins, not single steps.

## Checkpoints & offline eval (the only quality signal)

Six numbered checkpoints + the final adapter were converted on this VM (CPU) to audio.cpp
format as **lone-AR** adapters (AR = checkpoint verbatim at α=1, NAR = zeros rank 8; **no v2
merge** — a merge would re-introduce v2's AR style and mask the pronunciation signal) and
banked in GCS:

`$GCP_BACKUP_BASE/quran_ahh_r8/convert/{base,quran_only,c1500,c3000,c4500,c6000,c7500,c9000,final}/`
(`base` = all-zero adapter; `quran_only` = prior s10 adapter for the ceiling control).
Manifest: `convert/adapter_manifest.json`.

A turnkey T4 probe (`INFERENCE/quran_pt_probe.py`) renders all arms, free-run, on held-out
**2:255** in the exact training caption format (`[Verse]` + ` ۝`), one seed.

## Caveats

- **No validation split and no samples** (`disable_sampling: true`), so this says nothing
  about whether pronunciation improved — the very failure mode `docs/QURAN_PRON_REVIEW.md`
  §2.1 documented. That requires the free-run held-out 2:255 eval per checkpoint.
- **Saved adapters are EMA weights** (`ema_config.use_ema: true`, decay 0.999).
- Absolute loss is not comparable to other runs (different data); only the *shape*
  (monotone `ar_ce` down, `ar_kl` up-then-flat) is, and it matches the priors.

## Next steps

- **Run the T4 eval** (`INFERENCE/quran_pt_probe.py`): base / `quran_only` / each checkpoint /
  `final` on held-out 2:255. Verdict (`docs/QURAN_PRON_REVIEW.md` §5): base **also wrong** ⇒
  representational ceiling ⇒ **stop the LoRA line**; base OK but adapter wrong ⇒ training issue.
- **Human blind gate** (`ab-blind-eval`) before any merge — no adapter is "best" before the
  listen.
- **Extend later** by bumping `steps` under a **new run name** (extending overwrites the final
  adapter; `DECISIONS.md`, `docs/PAUSE_RESUME.md`).
