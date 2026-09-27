# 2026-09-26 — quran_long_aya_dataset / run `quran_long_aya_r8`

> **First GPU session only — this file goes obsolete afterwards.** It is the
> kickstart for a run that has *no checkpoints yet* (steps 5–6, banking the cache
> and the first speed measurement, are one-time). For every **subsequent** session
> use the **resume prompt** in `docs/SESSION_PROTOCOL.md`; only two things here
> still apply then — restore the dataset, and relaunch the identical command.

State: dataset built + validated (**uploaded** to GCS, 81,006 train pairs, 28.04 GiB);
config written; branch `pron-lora-long` **pushed**; no GPU work yet.
Plan: `docs/PRON_LORA_LONG_PLAN.md`. Continuity: `docs/SESSION_PROTOCOL.md`.

## PREREQUISITE before the GPU session — push the branch (agent can't push)
```bash
cd /content/maqamrock-yue2-lora-finetuning
bash bootstrap/github_auth.sh          # paste PAT at the hidden prompt
git push -u origin pron-lora-long
# on the fresh VM the notebooks check out pron-lora-ar-only, so: git checkout pron-lora-long
```

## COPY-PASTE FIRST MESSAGE for the fresh GPU session
```text
Fresh Colab GPU VM — start the GPU phase for the quran_long_aya_dataset run
(branch pron-lora-long). Read docs/PRON_LORA_LONG_PLAN.md + agent_notes/current.md first.

Context: dataset quran_long_aya_dataset (81,006 train pairs, 29 GB) is built and in GCS;
config/quran_long_aya_r8.yml is written (steps 81006 = 1 epoch, save_every 1500,
cache_text_embeddings false, cache_latents_to_disk true). First GPU session — no
checkpoints exist yet.

1. Preflight: confirm the branch is pron-lora-long and the config parses; report nvidia-smi
   (GPU/VRAM), disk, and whether vm-continuity is healthy.
2. Run bootstrap/setup.sh --training (it may also pull the old v2 dataset — ignore that),
   then restore OUR dataset:
     gcloud storage rsync -r gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/quran_long_aya_dataset /content/quran_long_aya_dataset
   Verify 81,006 train .mp3 + 81,006 .txt, 352/352 val, 14/14 smoke.
3. Start sidecars: backup_to_gcp.py --run-name quran_long_aya_r8 ; gpu_logger.py.
4. The first launch builds the latent cache (~5-9 h) before step 1. Give me the exact
   detached launch command to type:
     python train_ctl.py start --config config/quran_long_aya_r8.yml --run-name quran_long_aya_r8 --log-name train_quran_long
5. After I launch: watch /content/quran_long_aya_dataset/train/_latent_cache/*.safetensors
   until it is ~81,006 (log /content/logs/train_quran_long.log). The MOMENT it is complete,
   bank it (one-time expensive artifact):
     tar -C /content/quran_long_aya_dataset/train -cf - _latent_cache | gcloud storage cp - gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/quran_long_aya_dataset/_latent_cache.tar
   then confirm the tar is in GCS and report its size.
6. Once steps run, measure real speed over ~50 steps (monitor_loss.py + /content/logs/gpu_usage.csv):
   report s/step, VRAM peak, and the wall clock per 1500-step save. Do not change the config.
7. Do not edit the config or auto-resume anything. I'll pause with train_ctl.py stop. Later
   fresh VM = restore dataset, untar the banked cache, restore the run output prefix, relaunch
   the identical command.
8. Continuity check BEFORE I disconnect: update agent_notes/current.md, commit + push, and
   confirm this session shipped (vm-continuity status; run vm-continuity ship if needed so the
   conversation is recoverable on the next VM). See docs/SESSION_PROTOCOL.md.
```

## State / next steps
- GCS dataset: gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/quran_long_aya_dataset/
  (complete: 81,006 train pairs / 352 val / 14 smoke; 28.04 GiB).
- Config: `config/quran_long_aya_r8.yml` — steps 81006, save_every 1500,
  max_step_saves_to_keep 24, cache_text_embeddings false; else identical to
  `pron_lora_ar_only.yml`.
- Cache: latent ~5.2 GiB; one-time build ~5–9 h; bank it (step 5 above).
- Queue after GPU: multi-day training at 1500-step saves, GCS mirror 5 min.

## Before you disconnect — continuity check
Run this before you let the VM go (it is also step 8 of the copy-paste message):
1. `vm-continuity status` — exit 0 = the session-backup loop is healthy.
2. `vm-continuity ship` — force one pass so the latest conversation is in GCS
   (`<CONTINUITY_GCS>/opencode_sessions/by_host/<host>/`); confirm the ship time.
3. Confirm the run mirror is current:
   `backup_to_gcp.py --run-name quran_long_aya_r8 --once`, and that
   `agent_notes/current.md` was updated and pushed.
Full detail: `docs/SESSION_PROTOCOL.md`.
