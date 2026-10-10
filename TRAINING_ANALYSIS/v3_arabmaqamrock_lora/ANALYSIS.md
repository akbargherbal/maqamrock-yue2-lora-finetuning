# Training analysis — `v3_arabmaqamrock_lora` (438-track verbatim-lyric)

**COMPLETE — finished 2026-10-10 ~13:34 UTC at step 5000 / 5000** (~16:34 Bahrain).
`run.py` exited cleanly — the log shows `5000/5000`, `Saved checkpoint to
…/v3_arabmaqamrock_lora.safetensors`, `Saved optimizer to …/optimizer.pt`. Final adapter +
`optimizer.pt` + all checkpoints are in GCS.

Charts regenerated from the final `loss_log.db` + `gpu_usage.csv` via:
```bash
python TRAINING_ANALYSIS/generate_plots.py \
  --db /content/ai-toolkit/output/v3_arabmaqamrock_lora/loss_log.db \
  --gpu-csv /content/logs/gpu_usage.csv \
  --total-steps 5000 --save-every 250 \
  --outdir TRAINING_ANALYSIS/v3_arabmaqamrock_lora \
  --title "v3_arabmaqamrock_lora (438-track, 5000/5000)" --event-label "checkpoint save"
```

> Training loss only — there is **no held-out split**, so quality must be judged from the
> (offline) generated samples too. Loss alone can't tell you the LoRA learned the maqam or
> the lyrics. Held-out/eval prompts are **stale vs the 438** and must be regenerated before
> any evaluation.

## Run at a glance

| | |
|---|---|
| Config | `config/v3_arabmaqamrock_lora.yml` (A100 80 GB; rank 32 LoRA, EMA 0.999, `cot: off`, `train_window_frames: 0`, lr 1e-4, 5000 steps) |
| Model | YuE2 3B int8 `convrot8`, flowmatch, batch 1 |
| Dataset | **438** clips (Ajam 118 · Hijaz 107 · Kurd 101 · Nahawand 112), verbatim-lyric captions |
| GPU | Colab **A100-SXM4-80GB** |
| Steps done | **5000 / 5000 (100%)**, last logged step 4999 |
| Step time | ~**2.4 s/step** (avg 0.4161 steps/s, last-100 0.4182) |
| Wall span (logged) | 3.34 h |
| Sampling | **none** (`disable_sampling: true`, L93) — offline later |
| Checkpoints | every 250 (`save_every: 250`, L46); **all 19** numbered (250→4750) + final adapter in GCS |
| Health | no tracebacks; loss descending cleanly; **VRAM flat near cap — see callout** |

## Charts

- [`01_loss_curves.png`](01_loss_curves.png) — all loss terms, raw + 25-step mean
- [`02_loss_main.png`](02_loss_main.png) — primary `loss/loss` + linear trend
- [`03_learning_rate.png`](03_learning_rate.png) — LR schedule (constant 1e-4)
- [`04_throughput.png`](04_throughput.png) — seconds/step + progress vs wall-clock
- [`05_gpu_usage.png`](05_gpu_usage.png) — GPU util / memory / temp / power

## Loss trend (first-50 vs last-50 means)

| key | first50 | last50 | delta | min |
|---|---|---|---|---|
| `loss/loss` | 6.1719 | 4.3905 | **−1.7815** | 3.7597 @ step 4946 |
| `loss/ar_ce` | 5.2051 | 3.4825 | −1.7226 | 2.9563 @ step 4635 |
| `additional_model_loss` | 5.2051 | 3.4825 | −1.7226 | 2.9563 @ step 4635 |
| `learning_rate` | 1.0e-4 | 1.0e-4 | 0 | — |

`loss/ar_kl` is **absent** — `ar_kl_weight: 0.0` (L115) skips the KL term entirely.
Raw `loss/loss` is noisy at batch size 1; read the 25/50-step means. Compare to **v2**:
`loss/loss` 6.23 → 4.79 over 3000 steps (`../ANALYSIS.md`); v3 is a different
prompt/dataset, so cross-run loss values are directional only.

## ⚠️ VRAM was flat near capacity (~79.2 GB / 80 GB)

| metric | value |
|---|---|
| peak mem | **81144 MiB (79.2 GB, 99.05%)** |
| mean util | 93.7% |
| temp max | 69 °C |
| power | median 393 W, p90 408 W, max 427 W |

**Cause:** `gradient_checkpointing: false` (L78) — the only memory-relevant change vs v2
(`LEGACY…yml:72` had `true`; v2 peaked **17.0 GB**, `../ANALYSIS.md:37`). With
`train_window_frames: 0` (whole-song, L129) and batch 1, all activations are retained for the
backward pass. It bought ~30% speed (v2 median 3.42 s/step → here ~2.4). The config's own
justification ("~15-16 GB… skip activation recompute", L78) cites the figure that holds only
*with* checkpointing ON. **It survived to 5000** (never OOM'd) — but headroom was ~776 MiB at
peak. For the next run, `gradient_checkpointing: true` restores ~17 GB / ~3.4 s/step; or accept
the risk.

## What changed vs v2 (`LEGACY_akbar_arabic_rock_lora.yml`)

- dataset 267 → **438** (verbatim lyric tags)
- `steps` 3000 → **5000** (≈ same per-track exposure: 11.4 vs 11.2 epochs)
- `disable_sampling` false → **true** (sampling moved offline)
- `ar_kl_weight` 0.2 → **0.0** (the anchor never plateaued `ar_kl`; `DECISIONS.md`)
- `gradient_checkpointing` true → **false** (the VRAM cost above)
