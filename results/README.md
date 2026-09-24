# Offline AR-loss replay — L4 results (Task 16B)

Full replay of the AR-only pronunciation LoRA over all **180 `val` pairs** for all
**4 trainable checkpoints**, run on a Colab **L4** (sm_89) on 2026-09-24.

- Script: `offline_ar_loss_replay.py` (repo root) — same per-item AR path training used
  (`_prefix_segment` / `_item_prefix_and_abc` / `_ar_inputs` / `_ar_losses`), forward only.
- Command (detached, ~23 min total, zero errors):

  ```bash
  for CKPT in 1525 3050 4575 final; do
    python offline_ar_loss_replay.py --checkpoint $CKPT --device cuda \
      --out /content/logs/replay_l4_full_${CKPT}.json
  done
  ```

- Raw per-item JSON: `replay_l4_full_<ckpt>.json`; full stdout: `replay_l4_full_sweep.log`.
- Kernel-engagement smoke (Step 1): `replay_l4_smoke_final.json`.

## Mean losses per checkpoint (180 val pairs)

| checkpoint | step | mean `ar_ce` | mean `ar_kl` | Δ`ar_ce` | Δ`ar_kl` |
|---|---|---:|---:|---:|---:|
| `_000001525` | 1525 | 5.1157 | 0.7180 | — | — |
| `_000003050` | 3050 | 4.6202 | 1.2715 | −0.4955 | +0.5535 |
| `_000004575` | 4575 | 4.5053 | 1.4241 | −0.1149 | +0.1526 |
| `final` | 6100 | **4.4507** | **1.4828** | −0.0546 | +0.0587 |

Medians track the means closely (`ar_ce` final 4.4359, `ar_kl` final 1.5053; per-item
`ar_ce` sd ≈ 0.42–0.51).

## Reading

`ar_ce` (next-token CE against the val targets — what trains the adapter) falls
monotonically as training progresses, while `ar_kl` (KL(base‖lora) drift from the frozen
base) rises monotonically — the same unbroken-drift shape seen in the v1/v2 whole-song
runs and the pron training run itself. The gains are front-loaded: 1525→3050 buys
−0.50 `ar_ce` for +0.55 `ar_kl`; 4575→final buys only −0.05 `ar_ce` for +0.06 `ar_kl`.

This is a loss report on the held-out `val` pairs only. It does **not** by itself
establish pronunciation quality or pick the merge checkpoint/alpha — that decision (and
the alpha sweep / letter-substitution scorecard) is the user's, informed by these
numbers. No merge has been run.
