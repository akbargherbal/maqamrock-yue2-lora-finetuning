# Current — 2026-11-12

**Plan written: `arabic_instrumental_lora` (style LoRA on the 482-track Arabic instrumental zip).
Nothing launched, no config written — waiting on D1–D9 approval.**

Full plan (copy/read target): `docs/ARABIC_INSTRUMENTAL_LORA_PLAN.md`
Dataset runbook (already delivered, verified): `docs/ARABIC_INSTRUMENTAL_DATASET.md`

## State (verified this turn)

```
status.py        env Colab · git main @ f1d4b1b · disk 113.0 GB free
training         not running (v3_arabmaqamrock_lora) · no loss_log.db
gpu              Tesla T4 · 15,360 MiB · 0% util · no processes   <- cannot train this recipe
sidecars         backup_to_gcp.py DOWN · gpu_logger.py DOWN · vm-continuity not installed
GCS dataset      arabic_instrumental_dataset.zip 3,162,874,610 B (2026-11-12T10:49:46Z)
manifest         482 tracks · 36.60 h · p50 272 s · max 478 s · 283 vocal-flagged / 199 clean
```

## Two findings that change the launch

1. **Bootstrap blocks it:** `bootstrap/setup.sh:552-556` hard-codes `438` tracks for a zip
   dataset → a 482-track zip makes setup print `[FAIL] dataset:` and stop. Fix = env var
   `GCP_DATASET_COUNT` (default 438), plan §4.1.
2. **`trigger_word` would fire:** v3's `arabmaqamrock` appears in **none** of these captions, so
   toolkit injects it into every prompt (`DECISIONS.md:26`). Plan D6 sets it to
   `Middle Eastern fusion` (present in all 482 → no-op).

## Plan in one table

| | |
|---|---|
| New run | `arabic_instrumental_lora` (+ `_l4`) — fresh from base, **not** an extension of v3 |
| Config | v3 pair with 5 edits: `name`, `log_dir`, `trigger_word`, `train.steps` 5000→5500, sample prompts |
| Steps | 5500 ≈ 11.4 epochs (v3 exposure) · eval holdout 8 tracks → 474 trained |
| Wall clock | ~5–6 h A100 · ~22–24 h L4 · cost ≈ equal (4.3× measured vs 4.35× break-even) |
| GPU needed | L4 24 GB or A100 — **T4 is out** |

## Commands for when the GPU is right (approval first)

terminal: detached — log `/content/logs/setup.log`; stop: `pkill -f bootstrap/setup.sh`;
resume: re-run the same line.

```bash
export GCP_DATASET_ZIP=gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/arabic_instrumental_dataset.zip
export GCP_DATASET_COUNT=482
mkdir -p /content/logs
cd /content/maqamrock-yue2-lora-finetuning
setsid nohup bash bootstrap/setup.sh --training > /content/logs/setup.log 2>&1 & disown
```

terminal: detached — log `/content/logs/train.log`; stop: `python train_ctl.py stop`;
resume: the identical start line.

```bash
cd /content/maqamrock-yue2-lora-finetuning
python train_ctl.py start --config config/arabic_instrumental_lora.yml \
  --run-name arabic_instrumental_lora --dry-run
```

## Next action (needs you)

Approve D1–D9 (or override). Then: write the two configs + the `setup.sh` count change, commit,
push (needs `bash bootstrap/github_auth.sh` + PAT). Nothing GPU-side happens before that.

Repo: uncommitted = this plan + `docs/README.md` row + `RECONCILIATION_LOG.md` entry.
