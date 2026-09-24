# L4 handoff — after Task 14c (AR-only pronunciation LoRA, A100)

**Audience: the next agent session, on a fresh Colab L4 VM.** This file exists so
context survives the A100→L4 switch (the VM is wiped; only GitHub + GCS persist).
Read it top to bottom before doing anything. Branch: **`pron-lora-ar-only`**
(never `main`). Task 14c is **DONE**; this is a pre-work handoff for the *next*
phase (offline eval + merge), not a resume.

## 1. TL;DR state

- `pron_lora_ar_only_r8` — the AR-only rank-8 pronunciation LoRA — trained
  **6100/6100 steps (1 epoch)** on an A100, clean exit, no traceback/OOM.
- All artifacts are **local (gone when the VM died) AND in GCS** (persistent,
  verified). Nothing needs re-running.
- **No merge, no inference, no sweep has been done** — those are the next
  session's tasks (and the reason to be on an L4).
- **L4 is the right choice.** The A100 run was **not** compute-bound: median
  util 22 %, 10.5 GB of 80 GB VRAM, **0.886 s/step** — barely faster than the L4
  smoke's ~1.0 s/step (warmup-inflated). These are short recitation clips, so the
  bottleneck is the data/audio/CPU path, not the GPU. An A100 is overkill for
  this workload and for inference.

## 2. Where everything is (GCS base = `gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/`)

| What | Path |
|---|---|
| Run output (checkpoints, optimizer, loss_log.db, config.yaml, tensorboard) | `.../pron_lora_ar_only_r8/output/` (9 objects / 73.27 MiB) |
| Train/val/smoke dataset | `.../pron_dataset/{train,val,smoke}` = 12,200 / 360 / 32 real files |
| This repo + docs | GitHub, branch `pron-lora-ar-only` |

Artifacts in `.../pron_lora_ar_only_r8/output/`:
`pron_lora_ar_only_r8_000001525.safetensors`, `…_000003050`, `…_000004575`
(each 14,709,664 B), `pron_lora_ar_only_r8.safetensors` (**final, step 6100**),
`optimizer.pt` (15,174,731 B), `loss_log.db`, `config.yaml`, `tensorboard/`.

**Gotcha:** there is **no `_000006100` numbered checkpoint**. The loop runs
steps 0–6099, so numbered saves land at 1525/3050/4575; the post-loop no-step
save *is* the step-6100 artifact (`training_info = {"step": 6100, "epoch": 1}`,
metadata-verified). Four trainable artifacts total, not five. Don't chase a
missing file.

## 3. Run results (for context; full write-up in `TRAINING_ANALYSIS/pron_lora_ar_only_r8/ANALYSIS.md`)

- Final losses (step 6099): `loss/loss` 5.412, `loss/ar_ce` 4.163, `loss/ar_kl` 1.531.
- Last-50 means: 5.815 / 4.397 / 1.533. `ar_ce` fell all run (6.13→4.40
  first→last 50) — this is the metric that actually trains the adapter.
- `ar_kl` rose monotonically (0.21→1.53, bounded, max 2.19) — same unbroken drift
  as the v1/v2 whole-song runs. First lever if the offline eval shows over-drift.
- Median step time 0.886 s; 1.52 h logged. No in-training validation and no
  samples (`disable_sampling: true`), so **loss alone says nothing about
  pronunciation quality** — that's what the offline eval below is for.

## 4. Next session's task (in order)

1. **Offline AR-loss replay over the 180 `val` pairs**, per checkpoint. This is
   the "smallest offline alternative" specified in
   `docs/PRON_LORA_VERIFICATION.md` A3: load each adapter through
   `convert_lora_weights_before_load` (`yue2_model.py`) and run the same AR
   forward/loss path as training (`_ar_losses`), reporting `loss/ar_ce` and
   `loss/ar_kl`. **The script does not exist yet** — write it this session.
   Compare `_000001525 / _000003050 / _000004575` + final; prefer an earlier
   checkpoint if late steps over-drifting.
2. **Then merge** with the frozen v2 style LoRA:
   `W = W_base + 1.0*dW_style + alpha*dW_pron`, choosing checkpoint + `alpha`
   after the eval. v2 is never retrained. Conversion tooling:
   `converter/convert_aitoolkit_yue2_lora.py` (see `DECISIONS.md`).
3. **Inference is L4 work** (the point of switching back): audio.cpp + converted
   LoRA. Use `bootstrap/setup.sh --inference`; runbooks `docs/INFERENCE.md`,
   `docs/PRON_LORA.md`, skill `inference-batch-run`.

## 5. Fresh-L4 setup reminders (read before restoring)

- Clone this repo and `git checkout pron-lora-ar-only` — the pron configs/docs
  live on this branch, not `main`.
- Training-mode `setup.sh` **always** downloads the v2 dataset and needs
  `GCP_DATASET_PATH=.../dataset`; the pron set is opt-in via
  `GCP_PRON_DATASET_PATH=.../pron_dataset`. The launching notebook must export
  **both** (a past smoke VM set only `GCP_DATASET_PATH` to the pron path and
  broke — see `PRON_LORA_VERIFICATION.md` A7). `GCP_BACKUP_BASE` too.
- To get the run artifacts locally (only if you need to inspect/train further):
  ```bash
  mkdir -p /content/ai-toolkit/output/pron_lora_ar_only_r8
  gsutil -m rsync -r \
    gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/pron_lora_ar_only_r8/output \
    /content/ai-toolkit/output/pron_lora_ar_only_r8
  ```
- Latent cache and HF cache are **per-VM** and rebuild via `bootstrap/setup.sh`.

## 6. Guardrails (still binding — from `AGENTS.md`)

- Do **not** edit `config/akbar_arabic_rock_lora.yml` or
  `config/pron_lora_ar_only.yml` (or any run config) on your own initiative;
  config/hyperparameter decisions are the user's. Measure, report, recommend.
- Do **not** touch `/content/yue2_dataset` or `/content/pron_dataset` builds.
- Training commands: the **user types them**; hand over exact commands with
  terminal semantics (load the `command-handover` skill). Auto-resume is the
  only agent-run exception (identical config + run name, unplanned stop).
- `agent_notes/current.md` is **git-ignored** (mirrored to GCS by
  `backup_to_gcp.py`); committed durable state lives in `DECISIONS.md` /
  `PROGRESS.md`. Overwrite `current.md` per session; never append.
- Before any new run: confirm the backup daemon + GPU logger are running
  (`pgrep -af 'backup_to_gcp.py|gpu_logger.py'`) and that `backup_to_gcp.py`'s
  settle logic covers the run folder (see the 2026-09-24 fix in `DECISIONS.md` —
  the TensorBoard event file used to starve the settle and block GCS sync).

## 7. Key doc pointers

- `docs/PRON_LORA_VERIFICATION.md` — A0–A6 source analysis, smoke PASS, A100
  preflight, and the **real-run results** note.
- `docs/PRON_LORA.md` — the AR-only pron LoRA runbook (restore, run, backup).
- `TRAINING_ANALYSIS/pron_lora_ar_only_r8/ANALYSIS.md` — final training analysis.
- `DECISIONS.md` / `PROGRESS.md` — durable decisions + milestone trail.
- `docs/PAUSE_RESUME.md`, `docs/START.md`, `docs/INFERENCE.md` — runbooks.
