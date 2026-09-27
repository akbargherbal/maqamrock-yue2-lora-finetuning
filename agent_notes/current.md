# agent_notes / current

**Prime with:** `docs/PRON_LORA_LONG.md` + this file.

**Date:** 2026-09-27 · **State:** s10 run **TRAINING** (pid 76687). Latent cache built (8,100) **+ banked** (541.69 MiB). Step **~330/8100**, ~1.35 s/it ⇒ ~3 h for the configured 8,100; first checkpoint at step 1500. Sidecars: backup `quran_long_aya_r8_s10` (73836), `gpu_logger` (34038). No errors.

## What changed and why
The full 81,006-pair set's latent-cache step measures **~1.1 files/s on this L4** →
**~20 h** (live: 974/81,006 after ~15 min), which cannot fit a Colab session. Decision:
train a **frozen 10% random sample of train COMBOS** (both `_simple`/`_uthmani` variants
paired) → **8,100 pairs**, ~3.0 GiB, cache **~2 h** — at the scale of the working reference
(6,100 pairs). Full set + identity `quran_long_aya_r8` stay reserved for high-end hardware.
The prior "5–9 h" figure was an A100 estimate; ignore it.

## Done this turn
- Built `/content/quran_long_aya_dataset_s10/` via `sample_pron_dataset.py` (seed **20260927**):
  **8,100 train pairs, 352 val, 14 smoke**; 9 reciters, 2,779 distinct ayat.
- Locked selection: `docs/quran_long_aya_s10_manifest.json` (all 4,050 stems).
- New config: `config/quran_long_aya_r8_s10.yml` (parses; steps 8,100; folder `..._s10/train`).
- Archived for fast future restores: `/content/quran_long_aya_dataset_s10.tar` (3.0 G, plain tar;
  mp3 is incompressible) + `.sha256` sidecar = `1bf11f0bd5079a44024522b55af4220591350776897da85c0d7984afedafcc24`.
- **Cleanup done:** removed the aborted full run's dead local artifacts — `quran_long_aya_dataset/train/_latent_cache`
  (126 MB), `ai-toolkit/output/quran_long_aya_r8/` (20 KB), stale `train_quran_long.pid`, `train/.aitk_size.json`.
  Kept logs (in GCS) + the GCS `quran_long_aya_r8/` prefix (reserved identity) + the 29 GB full dataset.
- **Backup daemon re-pointed** to `quran_long_aya_r8_s10` (pid 73836); `gpu_logger` (34038) still running.

## Next steps (in order; you type each)

1. Stop the full-set cache build (frees the L4).
   **terminal: foreground** — sends the checkpoint-safe SIGINT and waits for `Job stopped`.
   Nothing to lose: the run is at **0 steps** (still caching), so no checkpoint is at risk.
   The partial `_latent_cache` stays on disk — valid for the full set reserved for high-end hardware.
   ```bash
   cd /content/maqamrock-yue2-lora-finetuning
   python train_ctl.py stop --config config/quran_long_aya_r8.yml --log-name train_quran_long
   ```
   Confirm it's gone:
   ```bash
   pgrep -af 'run\.py'                       # expect empty
   python train_ctl.py status --config config/quran_long_aya_r8.yml --log-name train_quran_long
   ```
   Leave the backup daemon (34037, still on `quran_long_aya_r8`) and `gpu_logger` running —
   step 2 re-points the daemon.

2. ~~Re-point the backup daemon~~ **DONE** — now running `--run-name quran_long_aya_r8_s10` (pid 73836).
   (If it ever needs a restart: `pkill -f '[b]ackup_to_gcp.py'` then relaunch as in git history.)

3. ~~Upload the subset~~ **DONE** — banked the archive (one object, 101 MiB/s in 40 s):
   - `gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/quran_long_aya_dataset_s10.tar` (2.94 GiB)
   - `…/quran_long_aya_dataset_s10.tar.sha256` · `…/quran_long_aya_s10_manifest.json`
   Fresh-VM restore (fast, single object; NOT the ~17k loose files):
   ```bash
   gcloud storage cp gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/quran_long_aya_dataset_s10.tar - \
     | tar -C /content -xf -
   ```

4. ~~Launch the s10 run~~ **DONE** — pid 76687, detached (`--log-name train_quran_long_s10`). First launch caches ~2 h before step 1.

5. ~~Bank the latent cache~~ **DONE** — `quran_long_aya_dataset_s10/_latent_cache.tar` (541.69 MiB). Future VMs untar instead of re-encoding (~1 h).

6. Fresh-VM restore is now via the **archive**, not the rsync job. Either stream it by hand
   (`gcloud storage cp gs://…/quran_long_aya_dataset_s10.tar - | tar -C /content -xf -`) or update
   the notebook / `setup.sh` opt-in job to fetch+extract the tar. Only point
   `GCP_QURAN_LONG_DATASET_PATH` at a loose `_s10` prefix if one is ever uploaded.

7. Pause only with `python train_ctl.py stop --config config/quran_long_aya_r8_s10.yml --log-name train_quran_long_s10`.
   Continuity: `vm-continuity status` is STALE — must read OK before you disconnect.
