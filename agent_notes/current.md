# agent_notes / current

**Prime with:** `docs/PRON_LORA_LONG.md` (canonical hub) + this file.

**Date:** 2026-09-27 · **State:** nothing training. Repo aligned to the locked prompt. **This VM has NO GPU.**

## Locked (matches the kickstart prompt in `docs/PRON_LORA_LONG.md`)
- Run **`quran_long_aya_r8`** · branch **`pron-lora-long`** · config **`config/quran_long_aya_r8.yml`**.
- steps **81,006** · `save_every: 1500` · `max_step_saves_to_keep: 24` ·
  `cache_text_embeddings: false` · `cache_latents_to_disk: true`.
- Pair count **A** (both variants). **Bank the latent cache** (~5.2 GiB, one-time build ~5–9 h before step 1).
- Dataset FINAL: `quran_long_aya_dataset/` — 81,006 train pairs, 352 val, 14 smoke, 28.04 GiB (verified).

## Repo state
- Pushed: `origin/pron-lora-long` (tracked). Files: `config/quran_long_aya_r8.yml`,
  `prepare_pron_dataset.py`, `append_ayah_symbol.py`, `docs/PRON_LORA_LONG.md` (canonical
  runbook), `docs/PRON_LORA_LONG_PLAN.md` (design). `bootstrap/setup.sh` is **unmodified**
  (the runbook restores the dataset by hand). `agent_notes/current.md` is tracked.
- This CPU session was captured to GCS: `opencode_sessions/by_host/87f6392cc09a/`
  (pull + `restore opencode` to recover it; loop left running, 5-min interval).
- Launcher: `notebooks/L4_QPRON_ArabicSuno_vscode_anywhere.ipynb` (copy also at
  `/content/`) now checks out `pron-lora-long`, exports `GCP_QURAN_LONG_DATASET_PATH`,
  and pulls the 28 GiB dataset **in parallel** with the vscode.dev tunnel auth.

## GPU phase — the exact sequence
1. **Preflight:** confirm branch `pron-lora-long` + config parses; report `nvidia-smi`, disk, `vm-continuity` health.
2. **Bootstrap + restore:**
   ```bash
   cd /content/maqamrock-yue2-lora-finetuning
   git checkout pron-lora-long
   bootstrap/setup.sh --training          # may also pull the v2 dataset — ignore that
   gcloud storage rsync -r gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/quran_long_aya_dataset \
     /content/quran_long_aya_dataset
   ```
   Verify 81,006 train `.mp3` + 81,006 `.txt`, 352/352 val, 14/14 smoke.
3. **Sidecars:** `backup_to_gcp.py --run-name quran_long_aya_r8` + `gpu_logger.py`.
4. **Launch (you type it; detached):**
   ```bash
   python train_ctl.py start --config config/quran_long_aya_r8.yml \
     --run-name quran_long_aya_r8 --log-name train_quran_long
   ```
5. **Bank the cache** when `_latent_cache` reaches ~81,006 (watch `train_quran_long.log`):
   ```bash
   tar -C /content/quran_long_aya_dataset/train -cf - _latent_cache \
     | gcloud storage cp - gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/quran_long_aya_dataset/_latent_cache.tar
   ```
6. **Measure** ~50 steps (s/step, VRAM peak, wall clock per 1500-step save). **Do not edit the config.**
7. **Pause** only with `python train_ctl.py stop --log-name train_quran_long`. **No auto-resume.**
   Later fresh VM = restore dataset → untar banked cache → restore run output prefix → relaunch identical command.
