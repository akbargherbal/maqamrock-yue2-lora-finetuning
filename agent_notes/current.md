# current

> **Session plan:** [`docs/QURAN_AHH_RESUME_PLAN.md`](../docs/QURAN_AHH_RESUME_PLAN.md)
> — resume training → T4 round-2 probe → finish run → rename.

## State @ 2026-10-06 01:15 UTC — **TRAINING RUNNING** (resumed @ step 19,500)

Fresh Colab VM; `setup.sh --training` done 00:57 UTC. Branch `pron-lora-long-aya` @ `8440f64`.
Config `config/quran_ahh_r8.yml` unchanged (rank 32/32, AR+NAR, `ar_kl_weight 0.0`, steps 28467) —
authority. `output/quran_ahh_r8/` + `_latent_cache` restored; sidecars up (`gpu_logger` 23442,
`backup_to_gcp --run-name quran_ahh_r8` 23443).

**Resume verified** (`run.py` pid 37073, started by agent on user's explicit instruction):
```
#### IMPORTANT RESUMING FROM /content/ai-toolkit/output/quran_ahh_r8/quran_ahh_r8_000019500.safetensors ####
Found step 19500 in metadata, starting from there
Loading optimizer state from /content/ai-toolkit/output/quran_ahh_r8/optimizer.pt
```
Stepping past 19500 with no crash (was at step ~19,639; loss ~4.2; ~1.28 s/it).

### Two problems FIXED this session (in `docs/COMMAND_HANDOVER_GOTCHAS.md`)
1. **Wrong resume point:** rsync re-created all ckpts with ~equal ctime → ai-toolkit's
   newest-by-ctime pick chose `_000009000`. Fixed by `chmod 644 quran_ahh_r8_000019500.safetensors`.
2. **Corrupt `loss_log.db`:** GCS backup captured a mid-checkpoint WAL db → every resume crashed
   in `_prune_future_steps`. Rebuilt from the readable prefix (19,500 steps / 78,000 rows,
   integrity `ok`) and swapped in. Corrupt original at `/tmp/loss_log_db_corrupt/`.

## Next (agent, Phase 2)
Monitor step/%, loss trend, VRAM, ckpt local-vs-GCS, sidecars. Saves every 1500 steps →
`_21000` next (~04:37 UTC). Watch for the `_21000` save and confirm it lands in GCS.

## Still open
- Phase 3 T4 round-2 probe (`c10500` vs `c16500`) — separate GPU.
- Phase 4 finalize at step 28,467 + bank final adapter/optimizer.
- Phase 5 rename `quran_ahh_r8` → `quran_ahh_r32` + docs reconcile + blind eval.
- Durable fixes: restore helper that fixes ckpt ctime; backup daemon that
  `wal_checkpoint(TRUNCATE)`s `loss_log.db` before syncing.

## Gotcha
`run.py -l <log>` **appends** — verify resume with `grep 'Found step' <log> | tail -1`, not `-m1`.
