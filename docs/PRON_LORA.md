# AR-only pronunciation LoRA (`pron_lora_ar_only_r8`)

A **separate** small LoRA trained on Quran verse recitation (audio + fully
diacritized text) to sharpen consonant articulation (ح خ ع ض). It is **AR-only**
(the AR expert carries the text/next-token path; `network_kwargs.ignore_if_contains:
["transformer.nar"]`), low rank (8), no trigger word, and no style-caption words.
It is intentionally **not** a style adapter: it must not learn recitation style,
only articulation. It is merged offline with the frozen v2 style LoRA as
`W = W_base + 1.0*dW_style + alpha*dW_pron`. **The v2 checkpoint is never
retrained or modified.**

- Dataset: Task 13's output, exposed at `/content/pron_dataset/{train,val,smoke}`.
- Config: `config/pron_lora_ar_only.yml` (real, 6,100 steps = 1 epoch);
  `config/pron_lora_ar_only_smoke.yml` (10 steps).
- Source verification: `docs/PRON_LORA_VERIFICATION.md` (A0–A6).

## Output locations

- Checkpoints / `loss_log.db` / `config.yaml`:
  `/content/ai-toolkit/output/pron_lora_ar_only_r8/`
- TensorBoard: `/content/ai-toolkit/output/pron_lora_ar_only_r8/tensorboard/pron_lora_ar_only_r8_<timestamp>/`
- Log: `/content/logs/train_pron.log`

## Restore on a fresh Colab VM

`setup.sh` restores the pron dataset **only** when `GCP_PRON_DATASET_PATH` is
exported (opt-in; v2-only bootstraps are unchanged). The launching notebook (or
`/root/.secrets.env`) must export:

```bash
export GCP_PRON_DATASET_PATH=gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/pron_dataset
```

`GCP_DATASET_PATH` must point at the **v2** dataset
(`.../OSTRIS_Arabic_Suno_Finetuning/dataset`), **not** at `.../pron_dataset`.
Training-mode `setup.sh` hard-requires it (`bootstrap/setup.sh:93`) and always
runs `job_dataset`, which otherwise downloads the pron set into
`/content/yue2_dataset` while `job_pron_dataset()` is silently skipped — see
`docs/PRON_LORA_VERIFICATION.md` A7. The launching notebook exports both paths.

Then, as usual:

```bash
git clone <this repo's URL>
cd maqamrock-yue2-lora-finetuning
git checkout pron-lora-ar-only     # the pron configs/docs live on this branch, not main
bash bootstrap/setup.sh > /content/logs/setup.log 2>&1 &
# authenticate vscode.dev in the foreground while setup runs
```

`job_pron_dataset()` rsyncs `$GCP_PRON_DATASET_PATH` into `/content/pron_dataset`
and drops the completion marker at `/content/pron_dataset/.bootstrap_complete`
(idempotent; marker not inside `train/`, `val/`, or `smoke/`). It is separate
from `job_dataset()` and `GCP_DATASET_PATH`, so it can never contaminate
`/content/yue2_dataset`.

## Smoke test (foreground; run it once before the real run)

Runs 10 steps over the 16-pair smoke set and saves a checkpoint to prove the
adapter is AR-only and rank 8.

```bash
cd /content/ai-toolkit
python run.py /content/maqamrock-yue2-lora-finetuning/config/pron_lora_ar_only_smoke.yml -l /content/logs/train_smoke.log
```

- Foreground on purpose (Ctrl+C stops it).
- After it finishes, inspect `output/pron_lora_ar_only_smoke/*.safetensors`.
  As saved, the AR (trainable) adapter is under **`text_encoders.*`** and the
  ignored NAR would be under **`diffusion_model.*`** (post-save prefix rewrite —
  see `docs/PRON_LORA_VERIFICATION.md` A1). Expect `text_encoders.*` > 0,
  `diffusion_model.*` == 0, and rank 8. Append the result to
  `docs/PRON_LORA_VERIFICATION.md`.
- Per-step time is in `/content/logs/train_smoke.log`; peak VRAM is in
  `/content/logs/gpu_usage.csv` (AI Toolkit logs no GPU stats — `gpu_logger.py`
  must be running).

## Real run (foreground; user-typed only)

```bash
cd /content/ai-toolkit
python run.py /content/maqamrock-yue2-lora-finetuning/config/pron_lora_ar_only.yml -l /content/logs/train_pron.log
```

- **Foreground on purpose** — Ctrl+C stops it. Do not detach it.
- Expect 4 checkpoints (quarter-epoch cadence, `save.save_every: 1525`,
  `max_step_saves_to_keep: 12` so all survive):
  - `pron_lora_ar_only_r8_000001525.safetensors`
  - `pron_lora_ar_only_r8_000003050.safetensors`
  - `pron_lora_ar_only_r8_000004575.safetensors`
  - `pron_lora_ar_only_r8_000006100.safetensors`
  - (plus a final no-step `pron_lora_ar_only_r8.safetensors` after the loop)
- Monitoring: `python monitor_loss.py /content/ai-toolkit/output/pron_lora_ar_only_r8/loss_log.db`,
  and tail `/content/logs/train_pron.log`.

## Backup

Training checkpoints back up to `<base>/pron_lora_ar_only_r8/output/`:

```bash
cd /content/maqamrock-yue2-lora-finetuning
setsid nohup python backup_to_gcp.py --run-name pron_lora_ar_only_r8 \
  > /content/logs/gcp_backup_stdout.log 2>&1 & disown
```

(`--run-name` now selects both the remote prefix and the local
`/content/ai-toolkit/output/<run-name>/` source — see `backup_to_gcp.py`.)

## Dataset persistence (one-time, from this VM)

Upload each split (the `/content/pron_dataset/*` entries are symlinks, so resolve
them to the real Task 13 paths; `gcloud storage rsync` ignores symlinks by
default):

```bash
for d in train val smoke; do
  src="$(readlink -f /content/pron_dataset/$d)"
  gcloud storage rsync -r "$src" \
    "gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/pron_dataset/$d"
done
```

Check object counts (expect 12200 / 360 / 32):

```bash
for d in train val smoke; do
  echo -n "$d: "
  gcloud storage ls -r "gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/pron_dataset/$d" | wc -l
done
```
