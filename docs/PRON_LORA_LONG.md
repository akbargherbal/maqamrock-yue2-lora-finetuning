# `quran_long_aya_r8` — runbook (canonical)

This is the **entry point for the multi-day, multi-VM long-aya pronunciation
LoRA**. Point the agent here at the start of a session and it should be able to
say what the run is, where it stands, and what the next step is.

**Prime prompt** (paste at session start):
```text
Read docs/PRON_LORA_LONG.md and agent_notes/current.md, then report the current
state of quran_long_aya_r8 from live artifacts (not memory) and propose the next step.
```

## Canonical docs — read in this order

| # | Doc | Answers |
|---|---|---|
| 1 | **this runbook** | what the run is, where it stands, the commands that matter |
| 2 | [`../agent_notes/current.md`](../agent_notes/current.md) | the live *next step* (updated every session close) |
| 3 | [`PRON_LORA_LONG_PLAN.md`](PRON_LORA_LONG_PLAN.md) | the design and locked decisions (*why*) |
| 4 | [`SESSION_PROTOCOL.md`](SESSION_PROTOCOL.md) | how to prime/resume the agent across VMs; the opening/closing ritual |
| 5 | [`GPU_OPENING_PROMPT.md`](GPU_OPENING_PROMPT.md) | **first session only** (no checkpoints yet) — obsolete afterwards |
| — | [`PAUSE_RESUME.md`](PAUSE_RESUME.md) · [`MONITOR.md`](MONITOR.md) · [`BACKUP_RESTORE.md`](BACKUP_RESTORE.md) | generic run mechanics |

## Snapshot (updated each session; facts, not narrative)

| | |
|---|---|
| Run name | `quran_long_aya_r8` |
| Config | `config/quran_long_aya_r8.yml` (steps 81,006 · `save_every` 1500 · `max_step_saves_to_keep` 24 · `cache_text_embeddings: false` · `cache_latents_to_disk: true`) |
| Branch | `pron-lora-long` |
| Dataset | `gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/quran_long_aya_dataset/` — 81,006 train pairs / 352 val / 14 smoke; 28.04 GiB |
| Local dataset | `/content/quran_long_aya_dataset/` |
| Run output | `/content/ai-toolkit/output/quran_long_aya_r8/` → GCS `…/quran_long_aya_r8/output/` |
| Log / metrics | `/content/logs/train_quran_long.log` · `<output>/loss_log.db` · `/content/logs/gpu_usage.csv` |
| Latent cache | `/content/quran_long_aya_dataset/train/_latent_cache` (~5.2 GiB; banked as `…/quran_long_aya_dataset/_latent_cache.tar`) |
| Status | **GPU work not started.** 0 steps. No checkpoints. Cache not built. Dataset uploaded; branch pushed. |

## Commands that matter

```bash
cd /content/maqamrock-yue2-lora-finetuning

# launch (you type it; detached — survives Ctrl+C)
python train_ctl.py start --config config/quran_long_aya_r8.yml \
  --run-name quran_long_aya_r8 --log-name train_quran_long

# pause cleanly (checkpoint-safe)
python train_ctl.py stop --log-name train_quran_long

# is it healthy? / progress
python train_ctl.py status --log-name train_quran_long
python monitor_loss.py /content/ai-toolkit/output/quran_long_aya_r8/loss_log.db

# mirror to GCS now
python backup_to_gcp.py --run-name quran_long_aya_r8 --once

# restore on a fresh VM (dataset; the run output prefix; then the banked cache)
gcloud storage rsync -r gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/quran_long_aya_dataset /content/quran_long_aya_dataset
mkdir -p /content/ai-toolkit/output/quran_long_aya_r8
gsutil -m rsync -r gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/quran_long_aya_r8/output /content/ai-toolkit/output/quran_long_aya_r8
# tar the cache when built (one-time): see PRON_LORA_LONG_PLAN.md §4.3
```

## Progress log (append one row per session)

| Date | Session | Steps (from→to) | Approx wall | How it ended | Notes |
|---|---|---|---|---|---|
| 2026-09-27 | planning/recovery | 0 → 0 | — | n/a | recovered builder+config+plan after VM loss; dataset uploaded; decisions locked |

Keep this row-per-session: it is the durable "how much training have we done"
record. `agent_notes/current.md` holds only the live next step.
