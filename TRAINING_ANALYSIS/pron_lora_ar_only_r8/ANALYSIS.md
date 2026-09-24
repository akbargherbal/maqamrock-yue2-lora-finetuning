# Training analysis — `pron_lora_ar_only_r8` (AR-only pronunciation LoRA)

**IN PROGRESS** — snapshot generated **2026-09-24 ~07:20 UTC** at logged
**step 4967 / 6100 (81.4%)**, ~1 epoch. `run.py` healthy (no traceback). Charts
produced by the (now parametrized) `TRAINING_ANALYSIS/generate_plots.py`:

```bash
cd /content/maqamrock-yue2-lora-finetuning
python TRAINING_ANALYSIS/generate_plots.py \
  --db /content/ai-toolkit/output/pron_lora_ar_only_r8/loss_log.db \
  --total-steps 6100 --save-every 1525 \
  --outdir TRAINING_ANALYSIS/pron_lora_ar_only_r8 \
  --title "pron_lora_ar_only_r8 (AR-only pronunciation LoRA, rank 8)" \
  --event-label "checkpoint save"
```

> **Re-run this after the run finishes** to replace this snapshot with the final
> charts. This is **training loss only** — there is no in-training validation
> (`docs/PRON_LORA_VERIFICATION.md` A3), so adapter quality must be judged
> offline from the checkpoints, not from loss alone.

## Run at a glance

| | |
|---|---|
| Config | `config/pron_lora_ar_only.yml` (rank **8** LoRA, AR-only via `ignore_if_contains: ["transformer.nar"]`, EMA 0.999, `cot: off`, `train_window_frames: 0`, lr 1e-4) |
| Model | YuE2 3B int8 `convrot8`, flowmatch, batch 1, grad-accum 1 |
| Dataset | `/content/pron_dataset/train` — 6,100 pairs, **6,099 usable** (one mp3 failed to decode at cache time); 6,100 steps ≈ 1.0002 epoch |
| GPU | Colab **A100-SXM4-80GB** |
| Caching | 6,100 clips in **12:26** before step 1 (expected, not a stall) |
| Steps at snapshot | **4967 / 6100 (81.4%)** |
| Step time | **median 0.886 s** (p10 0.872 / p90 0.917) → ~**1.11 steps/s** |
| ETA | ~**17 min** at the recent rate |
| Samples | **none** (`train.disable_sampling: true`) — grey verticals are checkpoint saves, not sample pauses |
| Checkpoints so far | `…_000001525` (06:19), `…_000003050` (06:41), `…_000004575` (07:04); next 6100, then final no-step |
| GPU | peak **10,794 MiB (10.5 GB)** of 80 GB; util p50 **22 %**; power mean 79 W; temp ≤ 35 °C |
| Health | no tracebacks; loss descending; VRAM flat |
| Backup | local + GCS (`…/pron_lora_ar_only_r8/output/`) after the 2026-09-24 settle fix (`DECISIONS.md`) |

## Charts

- [`01_loss_curves.png`](01_loss_curves.png) — all four loss terms, raw + 25-step mean
- [`02_loss_main.png`](02_loss_main.png) — primary `loss/loss` with linear trend
- [`03_learning_rate.png`](03_learning_rate.png) — LR schedule (constant 1e-4)
- [`04_throughput.png`](04_throughput.png) — seconds/step and progress vs wall-clock
- [`05_gpu_usage.png`](05_gpu_usage.png) — A100 util / memory / temp / power

## Loss trend (per-500-step means)

| steps | `loss/loss` | `loss/ar_ce` | `loss/ar_kl` | `additional_model_loss` |
|---|---|---|---|---|
| 1–500 | 6.519 | 5.199 | 0.975 | 5.394 |
| 501–1000 | 6.108 | 4.748 | 1.277 | 5.004 |
| 1001–1500 | 6.023 | 4.643 | 1.335 | 4.910 |
| 1501–2000 | 5.971 | 4.589 | 1.387 | 4.866 |
| 2001–2500 | 5.951 | 4.547 | 1.399 | 4.827 |
| 2501–3000 | 5.939 | 4.538 | 1.435 | 4.825 |
| 3001–3500 | 5.868 | 4.475 | 1.454 | 4.766 |
| 3501–4000 | 5.885 | 4.478 | 1.463 | 4.771 |
| 4001–4500 | 5.849 | 4.435 | 1.497 | 4.734 |
| 4501–5000 | 5.830 | 4.402 | 1.522 | 4.707 |

First-50 vs last-50: `loss/loss` 7.36 → **5.89** (−1.47), `loss/ar_ce` 6.13 →
**4.45** (−1.68), `loss/ar_kl` 0.21 → **1.55** (+1.35),
`additional_model_loss` 6.17 → **4.76** (−1.41).

Metric keys present: `additional_model_loss`, `learning_rate`, `loss/ar_ce`,
`loss/ar_kl`, `loss/loss` — same five as v1/v2, **no `nar_flow`** key.

## Observations / flags

1. **Clean and still descending.** `loss/loss` falls steeply over the first
   ~200 steps (7.4 → ~6.2) then declines slowly to ~5.9. The 50-step trend is
   **−7.7e−5/step** at the snapshot. No tracebacks, no OOM, VRAM flat at ~10.5 GB.
2. **`loss/ar_ce` — the term that actually trains this adapter — is still
   falling**: 5.20 (1–500) → **4.40** (4501–5000). This is the AR next-token
   loss on the recitation text; it is the only thing the adapter is optimising
   (NAR is excluded and its flow loss is detached). The curve is flattening but
   not flat, so the remaining ~1,100 steps still carry (small) signal.
3. **`loss/ar_kl` rises monotonically the whole way, exactly as in v1 and v2**:
   0.21 → 1.55 last-50, windowed 0.98 → 1.52, max **2.186** at step 4313. It is
   the trust-region KL(base ‖ lora) on AR distributions and it is **bounded** —
   no blow-up — but the unbroken upward drift is the same pattern the whole-song
   runs showed. If the pron adapter turns out to over-drift the AR (audible on
   the offline eval), `ar_kl_weight` / fewer steps / lower LR is the first
   single-variable lever.
4. **`loss/loss` here is AR-dominated** (`additional_model_loss` ≈ `ar_ce`), as
   expected for an AR-only adapter — the NAR/flow path contributes ~no gradient
   (A4 in `PRON_LORA_VERIFICATION.md`). Do not read `loss/loss` as audio quality.
5. **Diminishing returns.** Per-500 improvements collapsed after the first
   window: −0.41, −0.09, −0.05, −0.02, −0.01, −0.07, +0.02, −0.04, −0.02. The
   last ~2,500 steps moved `loss/loss` by well under 0.15 while `ar_kl` kept
   drifting up. Late steps mostly refine `ar_ce` (still slowly improving) and let
   the KL anchor grow.
6. **The A100 is not the bottleneck.** Median util **22 %**, power mean 79 W,
   VRAM only 10.5 GB of 80 GB, yet step time is **0.886 s** — barely faster than
   the L4 smoke's ~1.0 s/step (which was warmup-inflated). This run is
   data/CPU-bound (short-clip VAE/audio path), not compute-bound; an A100 is
   over-provisioned for it. Full epoch ≈ `6100 × 0.886 s ≈ 1.5 h` of training.
7. **Early transients, not trends.** Max loss at step 19 (9.42) is warmup; the
   apparent minima at steps 547 (`loss/loss` 4.41) and 2546 (`ar_ce` 2.97) are
   single-batch dips, not a regime change.

## Caveats

- **Mid-run snapshot (81.4%).** Numbers will move slightly; regenerate after
  step 6100.
- **No validation split** and **no samples** (`disable_sampling: true`), so this
  says nothing about whether the articulation actually improves. That requires
  the offline AR-loss replay over the 180 `val` pairs described in
  `PRON_LORA_VERIFICATION.md` A3, run per checkpoint.
- **Not comparable to v1/v2 loss levels**: different dataset (short recitation
  clips vs whole songs), rank (8 vs 32), and objective (AR-only vs full). Only
  the *shape* of `ar_kl` is directly comparable, and it matches both.

## Next steps

- Regenerate the charts once training completes (same command; drop the
  "IN PROGRESS" note).
- Offline-eval checkpoints `000001525 / 000003050 / 000004575 / 000006100` +
  final over the 180 `val` pairs (`loss/ar_ce`, `loss/ar_kl`); prefer an earlier
  checkpoint if late steps over-drift.
- Merge with the frozen v2 style LoRA only after that audit (next session).
