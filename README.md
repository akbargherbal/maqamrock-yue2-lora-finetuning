# maqamrock-yue2-lora-finetuning

A LoRA fine-tune of [YuE2](https://github.com/ostris/ai-toolkit) (3B, int8 `convrot`) on Arabic maqam rock, trained with [`ostris/ai-toolkit`](https://github.com/ostris/ai-toolkit). The goal is a LoRA that can generate **structurally coherent full songs**, not a timbre-only adapter: 267 clips across four maqams sharing one fixed genre, production, and instrumentation, with a trigger word `arabmaqamrock`.

Training runs on a rented single GPU in Google Colab, driven over the CLI rather than the Web UI, and is monitored through an agent-readable SQLite metrics db. Colab is ephemeral, so all expensive artifacts are mirrored to GCS as the run proceeds.

## Status

As of the `PROGRESS.md` 2026-09-20 entries: **both training runs have finished
(3000/3000 each); v2 is the current artifact. Nothing is training right now.**

**v1** (`akbar_arabic_rock_lora`, style-only captions) finished **3000/3000** on a Colab A100-SXM4-80GB, with strong style/timbre fidelity but degraded Arabic pronunciation — traced to the dataset's captions carrying no lyrics at all, so the AR expert was never once rewarded for getting the words right (full root-cause in `PROGRESS.md`/`DECISIONS.md`). Its run is archived in GCS as `akbar_arabic_rock_lora_v1_nolyrics_archived` (185 objects, verified), and its dataset as `yue2_dataset_v1_style_only_obsolete` (local) / `dataset_v1_style_only_obsolete/` (GCS). An earlier, even-earlier run was killed at ~875/3000 steps on a separate scope correction (`train_window_frames`); that's archived as `akbar_arabic_rock_lora_crop60_killed`.

**v2** fixes the caption gap: 267 audio/caption pairs rebuilt from scratch with real lyrics appended in YuE2's native `[Lyrics]` format, verified against the manifest and promoted to be *the* dataset under the same plain names v1 used (`./yue2_dataset` locally, `dataset/` in GCS) — no config path edits needed. It then **ran to 3000/3000** on the same A100 with captions as the only change; the lower `loss/ar_ce` there confirms the lyrics now condition the AR (see `TRAINING_ANALYSIS/ANALYSIS.md`). A held-out evaluation set (`INFERENCE/yue2_eval_heldout/`) and updated training-time sample prompts (real lyrics, `duration: 360`) are committed in `config/akbar_arabic_rock_lora.yml`.

**v2 listening result:** style/timbre/arrangement match the target strongly and pronunciation is much improved over v1 (~9/10), with some letters still soft (ح drifting toward خ/ه, ع toward أ). A proposed future fix — a second, **AR-only** pronunciation LoRA (Quran-recitation donor), merged at low weight — is researched but **not scheduled**: [`docs/FUTURE_PRONUNCIATION_LORA.md`](docs/FUTURE_PRONUNCIATION_LORA.md).

## Repo layout

```
config/akbar_arabic_rock_lora.yml   # the training config (rank 32, EMA, cot: off, whole-song, lyric samples)
prepare_yue2_dataset.py             # v1 build: style-only audio + .txt caption pairs (obsolete dataset)
INFERENCE/evaluation_alharith.json  # post-run inference eval prompts (partly contaminated, see DECISIONS.md)
INFERENCE/yue2_eval_heldout/        # v2 held-out eval set: 4 prompts, 0 shared lines with training
monitor_loss.py                     # read-only loss_log.db inspector (step, metrics, ETA)
gpu_logger.py                       # nvidia-smi poller -> CSV (AI Toolkit logs no GPU stats)
backup_to_gcp.py                    # periodic GCS mirror of run artifacts
bootstrap/setup.sh                  # idempotent Colab bootstrap; --training (default) / --inference
bootstrap/github_auth.sh            # token-based git push auth, never exposed to the agent
DECISIONS.md                        # source-verified decisions and non-obvious findings
PROGRESS.md                         # milestone trail across sessions
verification.md                     # independent dataset audit
AGENTS.md                           # operating instructions for the coding agent
docs/                               # runbooks (start, pause/resume, backup, monitor) + future ideas
```

## Dataset

**`./yue2_dataset` currently holds v2 — lyric-conditioned captions — not the original style-only build.** v1's style-only captions (built by `prepare_yue2_dataset.py`, still in this repo and still runnable) are preserved at `./yue2_dataset_v1_style_only_obsolete`:

```bash
python prepare_yue2_dataset.py --root ./min_4stars_ai_music --out ./yue2_dataset_v1_style_only_obsolete
```

Both builds produce **267 audio/caption pairs**, all native `mp3, 48000 Hz, stereo` — exactly what YuE2's loader expects, so no conversion is needed. The shortlist logic is unchanged between v1 and v2: a take is used only if it is both listed in a workspace manifest and physically present. Do not use `--convert-wav`; it hardcodes 44.1 kHz and would force a needless lossy round-trip. v1's audit is in `verification.md`.

v2's captions add a `\n[Lyrics]\n{cleaned_lyrics}` block after the same style text v1 used (genre, maqam, vocals, production, instrumentation, mood) — built to fix v1's degraded pronunciation, traced to the AR expert never seeing real lyric text during training (see `DECISIONS.md`). v2 was built by a standalone `prepare_yue2_dataset_v2.py`, which is **not currently in this repo** (local-only; whether to commit it for reproducibility is open). Caption lyric-formatting rules (which section tags survive, how SFX asides are dropped) are recorded in `DECISIONS.md` and are binding on any other tooling that builds prompts from the same manifests — including the held-out evaluation set at `INFERENCE/yue2_eval_heldout/`. Trigger word (`arabmaqamrock `, space, no comma) is baked into every v2 caption directly rather than relying solely on `ai-toolkit`'s runtime injection; both are verified byte-equivalent, so `trigger_word` in the config is unaffected (`DECISIONS.md`).

## Training config

`config/akbar_arabic_rock_lora.yml` runs `process[].type: diffusion_trainer` with `arch: yue2` on `Comfy-Org/YuE2/checkpoints/yue2_3b_int8_convrot.safetensors` (`quantize: true`, `qtype: convrot8`). Key choices: rank 32 combined LoRA, `ema_config.use_ema: true` with `ema_decay: 0.999`, `model_kwargs.cot: "off"` (captions carry no melodic information, so SheetSage2 is never loaded), `model_kwargs.train_window_frames: 0` (train on whole songs; the implicit default crops one random 60 s window per step, which starves the AR expert of any multi-section gradient — see `DECISIONS.md`), `cache_latents_to_disk: true` (mandatory for YuE2), `noise_scheduler: flowmatch`, and `max_step_saves_to_keep: 12` so the background GCS sync has a buffer before local rotation deletes older checkpoints.

`log_config` at the process root is a dead key left in with a comment, and `aitk_db.db` is not a metrics source — see `DECISIONS.md` for both.

`sample.samples` carries the four `INFERENCE/yue2_eval_heldout/` prompts (one per maqam, real lyrics the model never trained on) at `sample.duration: 360`, so in-training checkpoint samples can actually show pronunciation, not just style — v1's lyric-free, 120s samples never could. See `DECISIONS.md` for the rationale and generation-cost tradeoff.

## Running on Colab

On a fresh VM, restore the repo and start the bootstrap in the background while you authenticate the vscode.dev tunnel in the foreground:

```bash
git clone <this repo's URL>
cd maqamrock-yue2-lora-finetuning
bash bootstrap/setup.sh --training > /content/logs/setup.log 2>&1 &
```

`--training` is the default; `bash bootstrap/setup.sh --inference` prepares a
lean inference-only VM (clones `0xShug0/audio.cpp` — not built — and pre-warms
the `audio-cpp/Yue2-3B-GGUF` bf16 model + VAE; it skips the dataset and the
ai-toolkit/torch install). `--help` prints both modes.

The notebook cell must export `HF_TOKEN` (staged into `/root/.secrets.env`), `GCP_DATASET_PATH` (training only), and `GCP_BACKUP_BASE` first; nothing bucket- or account-specific is hardcoded in the repo. `setup.sh` is idempotent: it skips the dataset download when the completion marker is present and skips any HF asset already cached. It clones ai-toolkit (tracking `main`, deliberately not pinned) and pre-warms only the assets this config actually loads.

Then start the two sidecar processes and launch training from ai-toolkit's directory:

```bash
cd /content/maqamrock-yue2-lora-finetuning
setsid nohup python backup_to_gcp.py --run-name akbar_arabic_rock_lora \
  > /content/logs/gcp_backup_stdout.log 2>&1 & disown
setsid nohup python gpu_logger.py --out /content/logs/gpu_usage.csv \
  > /content/logs/gpu_logger_stdout.log 2>&1 & disown

cd /content/ai-toolkit
python run.py /content/maqamrock-yue2-lora-finetuning/config/akbar_arabic_rock_lora.yml \
  -l /content/logs/train.log
```

Everything for the job lands under `/content/ai-toolkit/output/akbar_arabic_rock_lora/`: checkpoints, the auto-saved `config.yaml`, samples, `loss_log.db`, and the timestamped `tensorboard/` subfolder.

## Observability

Three real surfaces, in priority order:

1. **`loss_log.db`** — the per-step metrics source, written by `UILogger` because `logging.use_ui_logger: true`. Read it with `python monitor_loss.py /content/ai-toolkit/output/akbar_arabic_rock_lora/loss_log.db` (add `--key "loss/loss" --history 50`, or `--watch 30 --total-steps 3000` for a live ETA). It is WAL-mode, so read-only inspection during training is safe. The confirmed keys are `additional_model_loss`, `learning_rate`, `loss/ar_ce`, `loss/ar_kl`, `loss/loss` (there is no `nar_flow`).
2. **`/content/logs/train.log`** — the `-l` stdout/stderr log; the tqdm progress line and any traceback live here.
3. **`/content/logs/gpu_usage.csv`** — utilization/memory/temp/power, sampled every 10s by `gpu_logger.py`. AI Toolkit logs none of this itself.

`aitk_db.db` (the config's `sqlite_db_path`) holds at most a job-status string and only when the Web UI launched the run; a CLI run leaves it untouched entirely. Do not point monitoring at it.

## Backup to GCS

`backup_to_gcp.py` mirrors the run's artifacts to `gs://<base>/<run-name>/` every 15 minutes: `training_folder/akbar_arabic_rock_lora/` → `output/`, `/content/logs/` → `logs/`, and `agent_notes/` → `agent_notes/`. It uses `gsutil rsync` without `-d` (append/update only, never deletes remote), writes a `run_manifest.json` that refuses to mix two runs in one prefix, and gates each sync on the newest file being untouched (`--settle-seconds`) except for `loss_log.db` and its WAL sidecars, which are perpetually fresh during a run. To confirm progress is actually backed up, compare GCS object timestamps against local ones rather than assuming.

For the inference workspace (`setup.sh --inference`) run it with `--inference` instead: it defaults `--run-name` to `audiocpp_inference` and mirrors `/content/audiocpp_inference/{out,prompts,scripts}` plus the converted LoRA (`/content/converter/out`) and the shared `logs/` + `agent_notes/` under `gs://<base>/audiocpp_inference/`. The model GGUFs and prebuilt binary are not mirrored (regenerable; `setup.sh` re-fetches them).

```bash
python backup_to_gcp.py --inference            # daemon
python backup_to_gcp.py --inference --once     # single pass
```

## Docs

`docs/` holds task runbooks — [start on a fresh VM](docs/START.md), [pause/resume across sessions](docs/PAUSE_RESUME.md), [backup/restore](docs/BACKUP_RESTORE.md), [monitoring](docs/MONITOR.md), [L4 vs A100 cost/time](docs/GPU_L4_VS_A100.md), and the [post-run completion/backup checklist](docs/FINAL_BACKUP.md) — plus future ideas that are researched but not scheduled ([pronunciation LoRA](docs/FUTURE_PRONUNCIATION_LORA.md)); see [`docs/README.md`](docs/README.md) for the index. `DECISIONS.md` records source-verified decisions and the reasoning behind non-obvious config fields; read it before changing anything that looks wrong. `PROGRESS.md` is the milestone trail. `TRAINING_ANALYSIS/ANALYSIS.md` is the final v2 training analysis (v1's is archived under `TRAINING_ANALYSIS/v1_nolyrics_archived/`). `verification.md` is the v1 dataset audit. `AGENTS.md` is the operating contract for the coding agent, including the run-control policy (no new or changed run without the user typing the command; auto-resume only an unchanged, already-approved run after an unplanned interruption).
