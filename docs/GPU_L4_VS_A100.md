# L4 vs A100 for this training run — decision note

Date: 2026-09-19. Measured on the live whole-song run (`akbar_arabic_rock_lora`),
at ~step 164/3000 (~5%). This is a *cost/benefit* note, not a config change.

## Bottom line

- **A100 is not ~4× faster. Realistic estimate is ~2–2.6×.**
- Cost break-even needs **≥ 4.35×** (A100 costs `6.7 / 1.54` = 4.35× the L4 per hour).
- So under A100 the run would finish in **~4.5–6 h instead of ~12 h**, but at
  **~1.7–2.2× the compute units**.
- **A100 wins on turnaround time; L4 wins on compute-unit cost.** Which matters
  depends on what the budget optimizes for.

## Measured L4 baseline (this run)

| Metric | Value |
|---|---|
| Step time | **13.4 s/step** (median; p10/p90 = 11.0 / 15.6) |
| GPU util | 98.2% (max 100) |
| Board power | 70.5 W mean / 76 W max → **98% of L4's 72 W TDP** |
| VRAM | 12.9 GB mean / **15.8 GB peak** of 24 GB |
| Temperature | 73.8 °C mean / 78 max |
| Steps | 3000 → ~12 h + ~1.2 h sample overhead ≈ **~12–13 h** |

The near-TDP power and ~98% util mean the **GPU itself is the bottleneck**, not
the dataloader or CPU — so a faster GPU does help. But the same numbers say the
SMs are saturated doing math, which is what caps the size of the win.

## Hardware (NVIDIA datasheets)

| Spec | L4 | A100 40GB (SXM4, Colab) | A100 / L4 |
|---|---|---|---|
| BF16 / FP16 tensor, dense | 121 TFLOPS | 312 TFLOPS | **2.58×** |
| INT8 tensor, dense | 242 TOPS | 624 TOPS | **2.57×** |
| FP32 (CUDA cores) | 30.3 TFLOPS | 19.5 TFLOPS | **0.64×** (L4 faster) |
| Memory bandwidth | 300 GB/s | 1,555 GB/s | **5.2×** |
| Memory | 24 GB | 40 GB | 1.67× |
| TDP | 72 W | 400 W | 5.6× |

The load-bearing number is the **tensor-core ratio: ~2.6×**. Only a
memory-bandwidth-bound workload would approach the 5.2× row, and this one isn't:
the 3B int8 model reads ~3 GB of weights per pass, which at 13 s/step is well
under 1 GB/s — nowhere near L4's 300 GB/s. A bandwidth-bound kernel also wouldn't
sit at 98% of a 72 W board limit.

Two further drags on the aggregate speedup:

1. **A100's FP32 CUDA-core rate is *lower* than L4's** (19.5 vs 30.3 TFLOPS).
   Attention softmax, layer-norms, and elementwise ops run in FP32; those parts
   don't speed up and can slow down, pulling the mix below 2.6×.
2. **Overheads that don't scale 1:1** (sample generation, checkpointing, Python
   loop) dilute the step-level speedup slightly.

## Economics

Break-even speedup = `6.7 / 1.54` = **4.35×**.
Current L4 run: ~12 h × 1.54 = **~18.5 compute units**.

| A100 speedup | A100 wall-clock | A100 units | vs L4 units |
|---|---|---|---|
| 2.0× | ~6.0 h | ~40 | 2.2× more |
| 2.5× | ~4.8 h | ~32 | 1.7× more |
| 2.6× (tensor ceiling) | ~4.6 h | ~31 | 1.7× more |
| **4.35× (break-even)** | 2.8 h | 18.5 | same |

## Recommendation

- If the goal is **lowest compute-unit cost**: **stay on L4**. A100 is ~1.7–2.2×
  more expensive per run at the realistic speedup.
- If the goal is **same-day completion / fewer overnight sessions / less
  scheduling risk**: **A100 is reasonable** — ~12 h becomes ~4.5–6 h.
- **Settle it cheaply:** run a 30–60 min A100 trial on the identical config and
  compare s/step. If measured step time is ≤ ~3.1 s (13.4 / 4.35) the 4× case is
  real; if it lands near ~5 s, the realistic figure is ~2.6×.

## If the decision is to switch

- We are ~5% in, so a switch now costs little. The first checkpoint is at step
  250; switching **right after** it avoids losing progress.
- Migrate by restoring the run folder from GCS on the A100 VM — same procedure as
  [PAUSE_RESUME.md](PAUSE_RESUME.md). Use the **same run name and config** so the
  optimizer state and step counter carry over.

## Assumptions / caveats

- Colab's A100 is assumed to be the **40 GB SXM4** (1,555 GB/s). An 80 GB A100
  would improve bandwidth (2,039 GB/s) but has the **same 312 TFLOPS** compute,
  so the ~2.6× tensor ceiling does not move.
- Estimates are derived from published peak specs and measured L4 behavior, not a
  measured A100 run — hence the trial recommendation.
- This project deliberately changes one variable at a time; the comparison
  assumes the **identical config** (batch 1, whole-song window), not a larger
  batch that an A100's extra VRAM would allow.

## Post-run result (added 2026-09-19)

- The whole-song run **completed 3000/3000 on the A100**. Measured median was
  **3.10 s/step** (p10/p90 2.59 / 3.69, over 2730 post-resume steps) vs the L4's
  13.4 s/step = **~4.3×** — materially above the 2–2.6× tensor-core-ceiling
  estimate above, which was derived from spec-sheet ratios rather than a measured
  run. Sample generation was also faster (~226 s vs ~388 s per event).
- The direction of the economics conclusion is unchanged (A100 buys wall-clock at
  a higher compute-unit cost), but the turnaround win is larger than predicted:
  ~12 h of L4 work became ~3 h on the A100. VRAM peaked at ~15–16 GB, so the
  extra 80 GB was never needed for this config.
