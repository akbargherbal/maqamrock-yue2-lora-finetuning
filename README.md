# maqamrock-yue2-lora-finetuning

**BETA.** A LoRA fine-tune of [YuE2](https://github.com/ostris/ai-toolkit) (3B, int8
`convrot`) for generating **full, structurally coherent Arabic maqam rock songs**, plus a
small AR-only **pronunciation adapter** trained on Quran recitation to sharpen articulation.
Trained with [`ostris/ai-toolkit`](https://github.com/ostris/ai-toolkit); generated with
[`0xShug0/audio.cpp`](https://github.com/0xShug0/audio.cpp) (GGUF + the converted LoRA).

The style backbone is a single LoRA over the maqamrock dataset — **438 clips across four
maqams** (Hijaz, Kurd, Nahawand, Ajam; the v2 adapter, the current one, trained on 267 of
them) — sharing one fixed genre, production and instrumentation, with the trigger
word `arabmaqamrock`. Training runs on a rented single GPU in Google Colab, driven over the
CLI (not the Web UI) and monitored through an agent-readable SQLite metrics db; Colab is
ephemeral, so all expensive artifacts are mirrored to GCS.

## Status — BETA (~9/10)

**Both training milestones are complete and the inference pipeline is built and exercised.**
Nothing is training right now.

- **v2 style LoRA** (`akbar_arabic_rock_lora`, rank 32) — ran **3000/3000** on an
  A100-SXM4-80GB. Style/timbre/arrangement match the target strongly; pronunciation improved
  over v1 to **~9/10** (a few letters still soften: ح→خ/ه, ع→أ). Dataset: 267
  lyric-conditioned pairs (`./yue2_dataset`; GCS `v2_arabmaqamrock_dataset/`).
- **v3 dataset built (2026-10-10); next run not started.** 438 lyric/caption pairs (v2's
  267 + 171; verbatim Suno lyric tags, style header stripped), GCS
  `v3_arabmaqamrock_dataset.zip`. Planned run `v3_arabmaqamrock_lora` (A100, 5000 steps).
- **Pronunciation donor — parked, not adopted for arabmaqamrock (2026-10-09).** **`quran_ahh_r32`**
  (rank 32, AR+NAR; AHH-filtered **3 reciters** — Husary, Hudhaify, Abdul Basit — 9,489 pairs)
  merged into v2 with `merge_quran_lora.py` at **α0.1** → the `qahh_a0*` candidates. Across two
  listening rounds it showed **no demonstrated diction advantage** over v2 (the rubric saturated),
  so it is **shelved** — kept for a future **dialect** project — and v2-only stays the production
  style. See `PROGRESS.md` M12. (The earlier `pron_lora_ar_only_r8` family and the 9-reciter
  long-aya donor `quran_long_aya_r8_s10` + `qfinal_a*` are retired/archived.)
- **Banked merges (not adopted):** the `qahh_a0*` α sweep (α 0 / 0.1 / 0.2 / 0.3) — v2 style
  merged with `quran_ahh_r32` via `merge_quran_lora.py`. Kept for the dialect project; **no α
  selected**. See [`docs/LORA_INVENTORY.md`](docs/LORA_INVENTORY.md).
- **Inference** — the style LoRA and the merges run against held-out lyrics on audio.cpp
  (GGUF + converted unfused LoRA), driven by [`INFERENCE/run_one.sh`](INFERENCE/run_one.sh)
  and the JSON batch driver [`INFERENCE/generate.py`](INFERENCE/generate.py); GPU-free tests
  in `tests/`.

**Why BETA:** the artifacts and runbooks are exercised end-to-end and reproducible; what is
not settled is the next style round (more data) and the production audio verdict. The
pronunciation donor is **decided** (not adopted; parked for a future dialect project).
Listening evaluations run in the external **rating app**
(`gh repo clone akbargherbal/ai_music_rating_app`; runbook
[`docs/LISTENING_EVAL.md`](docs/LISTENING_EVAL.md)). Open items:
[`docs/IMPROVEMENTS.md`](docs/IMPROVEMENTS.md).

### Superseded / retired

- **v1** style-only captions (`akbar_arabic_rock_lora`, 3000/3000) — strong style, degraded
  pronunciation, root-caused to captions carrying **no lyrics** at all. Its GCS archive and
  the earlier `crop60_killed` (scope-correction) archive are described in `PROGRESS.md`, but
  both are **absent** from the project prefix — **no surviving v1 adapter**. History only.
- **`pron_lora_ar_only_r8`** and its 15 `c3050/c4575/cfinal_a0.*` merges — archived under
  `<base>/archive/pron_lora_ar_only_legacy/` (md5-verified); the run prefix was renamed
  `<base>/pron_lora_ar_only_r8_obsolete/`.
- **Long-aya Quran donor** (`quran_long_aya_r8_s10`, 9 reciters, 8,100 pairs) and its
  `qfinal_a0.3` / `qfinal_a0.5` merges — **retired 2026-10-07**, archived under
  `<base>/archive/quran_long_aya_legacy/`. Superseded by `quran_ahh_r32`.

## Repo layout

```
config/v3_arabmaqamrock_lora.yml + config/v3_arabmaqamrock_lora_l4.yml   # style-LoRA training config, per-GPU variants (v3 dataset, 5000 steps)
config/LEGACY_akbar_arabic_rock_lora.yml   # v1/v2 predecessor (ar_kl 0.2, in-training sampling)
config/quran_long_aya_r8_s10.yml    # RETIRED long-aya Quran pron run (AR-only rank 8, 8,100 pairs)
config/quran_long_aya_r8.yml        # RETIRED full-set ident (never trained)
config/pron_lora_ar_only.yml + config/pron_lora_ar_only_smoke.yml   # superseded pron donor (historical)
prepare_yue2_dataset.py             # v1 build: style-only captions (obsolete dataset)
prepare_yue2_dataset_v3.py          # v3 build: 438 tracks, verbatim lyric tags (+ datasets/v3_arabmaqamrock/)
prepare_pron_dataset.py             # pron dataset build (Task 13)
sample_pron_dataset.py              # seeded 10% subsample -> quran_long_aya_r8_s10
append_ayah_symbol.py               # ayah-symbol post-pass on the long-aya captions
merge_pron_lora.py                  # offline v2 + pron merge (alpha dial); -> audio.cpp adapter
offline_ar_loss_replay.py           # CPU/GPU replay of the val-set AR loss over checkpoints
monitor_loss.py                     # read-only loss_log.db inspector (step, metrics, ETA)
gpu_logger.py                       # nvidia-smi poller -> CSV (AI Toolkit logs no GPU stats)
backup_to_gcp.py                    # periodic GCS mirror (--training default / --inference)
train_ctl.py                        # detached start / status / checkpoint-safe stop
bootstrap/setup.sh                  # idempotent Colab bootstrap; --training (default) / --inference
bootstrap/github_auth.sh            # token-based git push auth, never exposed to the agent
INFERENCE/run_one.sh                # one observed generation; generate.py's execution engine
INFERENCE/generate.py               # JSON-driven batch generation (bring your own lyrics/style)
INFERENCE/yue2_eval_heldout/        # held-out eval set (v2): 4 prompts, now STALE vs v3 — regenerate before eval
INFERENCE/duration_cap.py           # canonical text->duration cap (docs/text_to_duration_formula.md)
INFERENCE/prepare_ab_eval.py        # generic blinded A/B(/N) listening package (EVAL.txt / KEYS.txt)
INFERENCE/{pron_alpha_sweep,pron_fine_sweep,pron_knob_probe,qfinal_suno_sweep}.sh   # sweep drivers (qfinal_suno_sweep: RETIRED)
INFERENCE/{suno_to_songs,pron_ckpt_sweep,maqam_lyric_swap}.py                       # sweep/convert tooling
manifests/workspace_manifest.json   # legacy Suno manifest; input to INFERENCE/suno_to_songs.py
TRAINING_ANALYSIS/                  # per-run loss curves + final analysis (v1 archived under it)
results/                            # committed sweep records: manifests, sidecars, hashes
tests/ + pytest.ini                 # GPU-free unit tests
skills/                             # portable agent skills (crash-resume, inference-batch, ab-blind-eval, ...)
docs/                               # runbooks (start, pause/resume, backup, monitor, inference, pron, merge, sweep) + audit
notebooks/                          # Colab launcher notebooks
DECISIONS.md                        # why: source-verified decisions and non-obvious findings
PROGRESS.md                         # milestones across sessions
SOURCE_OF_TRUTH.md                  # one authority per topic
RECONCILIATION_LOG.md               # dated docs-drift passes
AGENTS.md                           # operating contract for the coding agent
```

## Datasets

**`./yue2_dataset` holds the v2 lyric-conditioned captions** — 267 audio/caption pairs, all
native `mp3, 48000 Hz, stereo`, exactly what YuE2's loader expects. Captions are a style
text (genre, maqam, vocals, production, instrumentation, mood) plus a
`\n[Lyrics]\n{cleaned_lyrics}` block, with the trigger `arabmaqamrock ` baked in.

**v3 (2026-10-10) is the dataset for the next run** — 438 pairs (a strict superset of v2:
+171), GCS `v3_arabmaqamrock_dataset.zip`. Differences from v2: the **lyric tags are kept
verbatim** (v2 collapsed `[Section | asides]` → `[Section]` and dropped non-section tags like
`[orchestral strings swell]`), and for three tracks a stray female phrase is joined into the
`vocals` line (`v3_overrides.json`). Built by `prepare_yue2_dataset_v3.py`; provenance
(`manifest.json`, `build_report.md`, `v3_overrides.json`) is in `datasets/v3_arabmaqamrock/`.
The Suno style header (`[Is_MAX_MODE…]`/`[START_ON…]`) is still stripped. v1's style-only
captions (`prepare_yue2_dataset.py`, still runnable) are obsolete; the v1/v2 builds were
local-only scripts. Caption formatting rules live in `DECISIONS.md` and bind any other
tooling that builds prompts from the same manifests — including the held-out set at
`INFERENCE/yue2_eval_heldout/` (now stale vs v3; regenerate before eval).

Two further datasets feed the **pronunciation** work, both exposed under `/content/` by
`bootstrap/setup.sh` and stored in GCS: `pron_dataset` (Task 13) and
`quran_long_aya_dataset_s10` (the seeded 10% subsample, 8,100 pairs; the full 81,006-pair set
is reserved and does not fit an L4 session — see `DECISIONS.md`).

## Training configs

- `config/v3_arabmaqamrock_lora.yml` (A100) / `config/v3_arabmaqamrock_lora_l4.yml` (L4) — `process[].type: diffusion_trainer`, `arch: yue2`, on
  `Comfy-Org/YuE2/checkpoints/yue2_3b_int8_convrot.safetensors` (`quantize: true`,
  `qtype: convrot8`). Central choices: rank 32, `ema_config.use_ema: true` (`ema_decay:
  0.999`), `model_kwargs.cot: "off"` (captions carry no melodic information, so SheetSage2 is
  never loaded), `model_kwargs.train_window_frames: 0` (whole songs — the default crops one
  random 60 s window per step and starves the AR expert of multi-section gradient),
  `cache_latents_to_disk: true` (mandatory for YuE2), `noise_scheduler: flowmatch`, and
  `max_step_saves_to_keep: 12` so the GCS sync has a buffer before local rotation deletes old
  checkpoints. `sample.samples` are the four held-out prompts at `sample.duration: 360`
  (stale vs v3 and unused while `disable_sampling: true` — see `DECISIONS.md`).
- The long-aya Quran run uses `config/quran_long_aya_r8_s10.yml` — AR-only rank 8, `cot: off`,
  `train_window_frames: 0`. Runbook: [`docs/PRON_LORA_LONG.md`](docs/PRON_LORA_LONG.md).
- `log_config` at the process root is a dead key, and `aitk_db.db` is not a metrics source —
  see `DECISIONS.md`.

## Running on Colab

On a fresh VM, restore the repo and start the bootstrap in the background while you
authenticate the vscode.dev tunnel in the foreground:

```bash
git clone https://github.com/akbargherbal/maqamrock-yue2-lora-finetuning.git
cd maqamrock-yue2-lora-finetuning
bash bootstrap/setup.sh --training > /content/logs/setup.log 2>&1 &
```

`--training` is the default. `bash bootstrap/setup.sh --inference` prepares a lean
inference-only VM — it skips the dataset and the ai-toolkit/torch install and stages what
`INFERENCE/run_one.sh` needs: the prebuilt `audiocpp_cli` (sm_75/T4), the YuE2 bf16 GGUF +
VAE + sidecars (from HF), the converted style LoRA and the `prompts/`/`scripts/` trees (from
GCS), plus `ccache` + GNU `time`. `0xShug0/audio.cpp` is cloned but **not built** (a prebuilt
per-arch binary is used). Full runbook: [`docs/INFERENCE.md`](docs/INFERENCE.md).

The launching notebook must export `HF_TOKEN` (staged into `/root/.secrets.env`),
`GCP_BACKUP_BASE`, and the dataset var — `GCP_DATASET_ZIP` for the v3 zip (preferred) or
`GCP_DATASET_PATH` for a v2 folder; nothing bucket- or account-specific is hardcoded in the
repo. `setup.sh` is idempotent (skips the dataset when its completion marker is present;
skips any HF asset already cached).

Start the sidecars, then launch training through `train_ctl.py` (detached, so a stray Ctrl+C
can't kill it; `stop` sends a checkpoint-safe SIGINT):

```bash
cd /content/maqamrock-yue2-lora-finetuning
setsid nohup python backup_to_gcp.py --run-name v3_arabmaqamrock_lora > /content/logs/gcp_backup_stdout.log 2>&1 & disown
setsid nohup python gpu_logger.py --out /content/logs/gpu_usage.csv > /content/logs/gpu_logger_stdout.log 2>&1 & disown
python train_ctl.py start
```

Everything for the job lands under `/content/ai-toolkit/output/v3_arabmaqamrock_lora/`:
checkpoints, the auto-saved `config.yaml`, samples, `loss_log.db`, and the timestamped
`tensorboard/` subfolder.

## Observability

Three real surfaces, in priority order:

1. **`loss_log.db`** — the per-step metrics source, written by `UILogger` because
   `logging.use_ui_logger: true`. Read it with
   `python monitor_loss.py /content/ai-toolkit/output/v3_arabmaqamrock_lora/loss_log.db`
   (`--key "loss/loss" --history 50`, or `--watch 30 --total-steps 5000` for a live ETA).
   WAL-mode, safe to read during training. Confirmed keys: `additional_model_loss`,
   `learning_rate`, `loss/ar_ce`, `loss/ar_kl`, `loss/loss` (there is no `nar_flow`).
2. **`/content/logs/train.log`** — the `-l` stdout/stderr log; the tqdm line and any traceback.
3. **`/content/logs/gpu_usage.csv`** — utilization/memory/temp/power, sampled every 10 s by
   `gpu_logger.py`. AI Toolkit logs none of this itself.

`aitk_db.db` (the config's `sqlite_db_path`) holds at most a job-status string and only when
the Web UI launched the run; a CLI run leaves it untouched. Do not point monitoring at it.

## Backup to GCS

`backup_to_gcp.py` mirrors run artifacts to `gs://<base>/<run-name>/` every 5 minutes:
`training_folder/v3_arabmaqamrock_lora/` → `output/`, `/content/logs/` → `logs/`, and
`agent_notes/` → `agent_notes/`. It uses `gsutil rsync` without `-d` (append/update only,
never deletes remote), writes a `run_manifest.json` that refuses to mix two runs in one
prefix, and gates each sync on the newest file being untouched — except `loss_log.db` and its
WAL sidecars, which are perpetually fresh during a run. To confirm progress is backed up,
compare GCS object timestamps against local ones.

For the inference workspace, run it with `--inference` (defaults `--run-name
audiocpp_inference`): it mirrors `/content/audiocpp_inference/{out,prompts,scripts}`, the
converted LoRA, and the shared `logs/` + `agent_notes/`. The model GGUFs and prebuilt binary
are not mirrored (regenerable). `--watch LOCAL[:SUB]` mirrors an arbitrary folder *instead of*
the defaults; `--extra LOCAL[:SUB]` keeps the defaults and adds one.

```bash
python backup_to_gcp.py --inference            # daemon
python backup_to_gcp.py --inference --once     # single pass
```

The LoRA library (`<base>/loras/`) is curated by hand, not by the daemon.

## Tests

GPU-free unit tests live in `tests/` and never touch the GPU or `/content`:

```bash
pip install pytest coverage
python -m pytest                       # tests/test_merge_pron_lora.py needs torch
coverage run -m pytest && coverage report -m
```

They cover `INFERENCE/generate.py`, `INFERENCE/suno_to_songs.py`,
`INFERENCE/duration_cap.py`, `INFERENCE/prepare_ab_eval.py`, `backup_to_gcp.py`,
`train_ctl.py`, the offline AR-loss replay, and the pron merge (`merge_pron_lora.py`).

## Docs

`docs/README.md` is the index. Runbooks: [start on a fresh VM](docs/START.md),
[pause/resume](docs/PAUSE_RESUME.md), [backup/restore](docs/BACKUP_RESTORE.md),
[monitoring](docs/MONITOR.md), [inference (audio.cpp + GGUF + LoRA)](docs/INFERENCE.md),
[long-aya Quran pron run](docs/PRON_LORA_LONG.md), [pron merge](docs/PRON_LORA_MERGE.md),
[alpha sweep + listening](docs/PRON_LORA_SWEEP.md), [LoRA inventory](docs/LORA_INVENTORY.md),
[blinded A/B packages](docs/AB_BLIND_EVAL.md), [L4 vs A100 cost/time](docs/GPU_L4_VS_A100.md),
[finish/backup checklist](docs/FINAL_BACKUP.md). `SOURCE_OF_TRUTH.md` records the one
authority per topic; `DECISIONS.md` records source-verified decisions (read it before changing
anything that looks wrong); `PROGRESS.md` is the milestone trail; `AGENTS.md` is the agent
operating contract, including the run-control policy (no new or changed run without the user
typing the command; auto-resume only an unchanged, already-approved run after an unplanned
interruption).
