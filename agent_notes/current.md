# current

> **Session plan:** [`docs/QURAN_AHH_RESUME_PLAN.md`](../docs/QURAN_AHH_RESUME_PLAN.md)
> — resume training → T4 probe → finish run → rename.
> **This file is a handoff copy surface, not a source of truth** — re-derive from live artifacts.

## State @ 2026-10-06 04:36 UTC — **TRAINING COMPLETE** (28,467/28,467)

`quran_ahh_r8` (revised: AR+NAR, **rank 32**, `ar_kl_weight 0.0`, `steps 28467` = 3 epochs)
finished **cleanly** on the Colab L4 — `run.py` self-stopped, no traceback. Resumed
`2026-10-06T01:09:51` from ckpt 19,500; final step reached 04:34 UTC.

Final artifacts (local `output/quran_ahh_r8/` **and** GCS, sizes match):
- `quran_ahh_r8.safetensors` — 117,500,848 B (final, un-suffixed) → GCS `04:35:30`
- `optimizer.pt` — 119,807,781 B (step 28,467) → GCS `04:35:30`
- 18 periodic ckpts `_000001500 … _000027000`; `loss_log.db` (28,466 steps logged).
- Forced backup `backup_to_gcp.py --run-name quran_ahh_r8 --once` = **exit 0, 3/3 folders**.
  **Safe to disconnect / switch to T4.**

Training analysis finalized: `TRAINING_ANALYSIS/quran_ahh_r8_rank32/ANALYSIS.md` (+5 PNGs).
Loss plateaued hard after ~19.5k (`loss/ar_ce` ~3.19–3.22 for ~8.5k steps) — "later = better"
is a listening question, not a loss one.

## Next — Phase 3b (T4, separate GPU)
Convert **`c9000`** (≈epoch 1), **`c19500`** (≈epoch 2), and the **final** adapter; render all
three on **Ayat al-Kursi (Quran 2:255)**, fixed seed; then blind-A/B (`ab-blind-eval`).
Exact epoch ends 9489/18978/28467 don't land on saves; c9000/c19500 are the nearest.
(T4 handover recipe: `docs/QURAN_AHH_RESUME_PLAN.md` Phase 3 / 3b.)

## Still open
- Phase 3b epoch test above; round-2 `c10500` vs `c16500` also banked and untested.
- Phase 5: rename `quran_ahh_r8` → `quran_ahh_r32`; docs-reconciler; blind gate before any merge.
- Durable fixes (not yet done): restore helper that fixes ckpt ctime; backup daemon that
  `wal_checkpoint(TRUNCATE)`s `loss_log.db` before syncing.

## Gotchas (see `docs/COMMAND_HANDOVER_GOTCHAS.md`)
- `run.py -l <log>` **appends** — verify resume with `grep 'Found step' <log> | tail -1`, not `-m1`.
- GCS restore randomizes ckpt ctime → auto-resume picks the wrong step; `chmod` (not `touch`) fixes it.
- Backup can capture a mid-checkpoint WAL `loss_log.db` → crash in `_prune_future_steps`; repair by salvage.
