# Current — 2026-11-12

**`arabic_instrumental_lora` is configured and the bootstrap blocker is fixed. Nothing is
training. Next action: a 24 GB+ GPU (this VM is a T4) and your typed launch command.**

Plan + rationale: `docs/ARABIC_INSTRUMENTAL_LORA_PLAN.md` (D1–D10, accepted as defaults).
Dataset runbook: `docs/ARABIC_INSTRUMENTAL_DATASET.md`.

## State (verified 2026-11-12)

```
git              main @ (this commit) · pushed to origin
training         not running · no output/arabic_instrumental_lora/
gpu              Tesla T4 · 15,360 MiB · 0% util · no processes   <- cannot train this recipe
disk             113.0 GB free
GCS dataset      arabic_instrumental_dataset.zip 3,162,874,610 B, sha256 cea34fa2…39954
manifest         482 tracks · 36.60 h · p50 272 s · max 478 s · 283 vocal-flagged / 199 clean
sidecars         backup_to_gcp.py DOWN · gpu_logger.py DOWN (no run yet — start them at launch)
```

## What changed today

| file | change |
|---|---|
| `config/arabic_instrumental_lora.yml` | new — v3 config with exactly 5 edits: `name`, `log_dir`, `trigger_word: "Middle Eastern fusion"`, `steps: 5500`, 2 prose sample prompts |
| `config/arabic_instrumental_lora_l4.yml` | same 5 edits on the L4 base (`gradient_checkpointing: true` kept) |
| `bootstrap/setup.sh` | `DATASET_EXPECTED="${GCP_DATASET_COUNT:-438}"`; verify message uses it (v3 default unchanged) |
| `docs/ARABIC_INSTRUMENTAL_LORA_PLAN.md` | the plan (D1–D10, composability §1.1, launch/eval checklist) |
| `docs/README.md`, `SOURCE_OF_TRUTH.md` | index row + authority row for the new run |

Verified: `bash -n bootstrap/setup.sh` ok; both YAMLs parse; sample prompts contain
`\n[Lyrics]\n[intro]…` (newlines, not folded) and no `arabmaqrock`; diff vs v3 = 5 changes only.

## Launch (needs a 24 GB+ GPU — L4 or A100)

terminal: detached — log `/content/logs/setup.log`; stop: `pkill -f bootstrap/setup.sh`;
resume: re-run the same lines (already-present files are skipped).

```bash
export GCP_DATASET_ZIP=gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/arabic_instrumental_dataset.zip
export GCP_DATASET_COUNT=482
mkdir -p /content/logs
cd /content/maqamrock-yue2-lora-finetuning
setsid nohup bash bootstrap/setup.sh --training > /content/logs/setup.log 2>&1 & disown
```

Expect `[ok] dataset: 482 tracks`. Then hold out the 8 eval tracks (plan §4.4 — the
`python3 - <<'PY'` block), start the two sidecars, and:

terminal: detached — log `/content/logs/train.log`; stop: `python train_ctl.py stop`;
resume: the identical start line (same run name auto-resumes the newest checkpoint).

```bash
cd /content/maqamrock-yue2-lora-finetuning
python train_ctl.py start --config config/arabic_instrumental_lora.yml \
  --run-name arabic_instrumental_lora --dry-run
python train_ctl.py start --config config/arabic_instrumental_lora.yml \
  --run-name arabic_instrumental_lora
```

`--config` and `--run-name` are required: `train_ctl.py` still defaults to the v3 config, and a
default launch would mix the instrumental dataset with the v3 name.

## Unchanged / still open

- **Composability:** one LoRA file per expert, so "mixed" = offline merge. This adapter + pron
  donor = `merge_pron_lora.py`; this adapter + v3 style = no tool yet (plan §1.1).
- Push works today via `gh`'s stored token; on a fresh VM run `bash bootstrap/github_auth.sh`.
- Sidecars are down because there is no run to mirror — start both at launch (plan §5.1).
