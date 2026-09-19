# Decisions & insights

Major, durable decisions and non-obvious insights only — the things a fresh session must not re-litigate or rediscover. One short entry per decision. This is not a log: routine per-session state belongs in `agent_notes/current.md`.

Where a claim below says "verified against source," it means the actual `ostris/ai-toolkit` `.py` files were read on the date of this entry, not inferred from the README, a config example, or a GitHub issue thread. Ostris is under active development — re-check the cited file/line if behavior looks different than described here.

## Terminal/CLI over the Web UI, on purpose

- Ostris's Web UI (`python -m manager launch` / `ui`) is real and friendlier than ComfyUI's node graph, but the whole point of this workflow is OpenCode in `vscode.dev` acting on text — config files, log files, a database — not clicking through a browser UI on a Colab-forwarded port.
- Training via `python run.py config.yaml -l /content/logs/train.log` produces the exact same metrics as a UI-launched run: `use_ui_logger: true` is read by the trainer class itself (`toolkit/logging_aitk.py`), not by the UI process. **CLI-only loses nothing on observability.**
- What CLI-only *does* lose: the Web UI's own job list won't show this run (see "aitk_db.db only populates..." below), and there's no point-and-click dashboard. Neither matters for this project.

## Metrics live in `loss_log.db`, not `aitk_db.db`

- Your `sqlite_db_path` (`aitk_db.db`) is a *different* database from the one that actually holds step/loss data. Verified in `extensions_built_in/sd_trainer/DiffusionTrainer.py`: it only writes one row to a `Job` table (`status`: running/stopped/error/completed, plus a short `info` string), and only when the job was launched *by the Web UI* (it checks for an `AITK_JOB_ID` env var the UI sets). **A CLI-launched run will leave `aitk_db.db` untouched entirely — this is expected, not a bug.** Don't point monitoring at it.
- The real metrics file, verified in `toolkit/logging_aitk.py` (`UILogger` class), lives at `<training_folder>/<job_name>/loss_log.db` — for this job: `/content/ai-toolkit/output/akbar_arabic_rock_lora/loss_log.db`. It's created the moment `use_ui_logger: true` is set, CLI or UI, no exceptions. Schema:
  - `steps(step INTEGER PRIMARY KEY, wall_time REAL)`
  - `metric_keys(key TEXT PRIMARY KEY, first_seen_step, last_seen_step)`
  - `metrics(step, key, value_real, value_text)`
  Opened with `PRAGMA journal_mode=WAL`, so it is safe to read with a read-only connection *while training is actively writing to it* — no lock contention, no need to stop the run to inspect it. `monitor_loss.py` reads this file; don't hand-write SQL against it ad hoc, that script is the tested path.
- Column names for `yue2`/`diffusion_trainer` match `loss_dict` keys the trainer logs each step (learning_rate, plus whatever `loss_dict.items()` the model returns — expect something like `ar_ce`, `nar_flow`, similar in spirit to the AR/NAR split seen in the FL-YuE2 project's `DECISIONS.md`, but **not guaranteed to be the same key names**. **Confirmed on the first real run (2026-09-19):** the actual keys are `additional_model_loss`, `learning_rate`, `loss/ar_ce`, `loss/ar_kl`, `loss/loss`. There is **no** `nar_flow` key — don't look for one. The primary scalar to watch is `loss/loss`.

## `process[].type: "diffusion_trainer"` is correct, not a mismatch with `verification.md`

- `verification.md` (this session's independent verification pass) names `process[].type: 'sd_trainer'` as what's needed. Both `"sd_trainer"` and `"diffusion_trainer"` are legitimate, separately registered process types — verified in `extensions_built_in/sd_trainer/__init__.py`: `uid = "sd_trainer"` → `SDTrainer`, and `uid = "diffusion_trainer"` → `DiffusionTrainer(SDTrainer)`. `DiffusionTrainer` only *adds* optional UI/API job-status hooks on top of `SDTrainer` and, per the previous entry, every one of those hooks silently no-ops when there's no `AITK_JOB_ID` env var. **The config's `"diffusion_trainer"` is the correct, superset choice — nothing to change.**

## TensorBoard (`log_dir`) is real and architecture-generic, but writes to a subfolder

- Verified in `jobs/process/BaseTrainProcess.py`: `log_dir` is read directly off the process config in `__init__` and wraps every trainer type equally — nothing yue2-specific gates it, resolving last session's "unconfirmed" flag. But `setup_tensorboard()` creates `log_dir/<job_name>_<YYYYMMDD-HHMMSS>/` and points `SummaryWriter` there — **not** `log_dir` itself. An agent checking for TensorBoard events needs to glob one level down (`output/akbar_arabic_rock_lora/tensorboard/*/`), not assume a fixed path.
- `log_config: {log_every: 1}` at the process root (as opposed to `logging.log_every`) is never read by `toolkit/config_modules.py`'s `LoggingConfig` — it's a dead key. Left in the YAML with a comment rather than deleted, so it isn't mistaken for a missing feature later.
- TensorBoard is redundant with `loss_log.db` for this project's purposes (same numbers, less convenient to query from a script) — treat it as a nice-to-have second view, not the primary source an agent polls.

## No GPU utilization/temp/power logging exists anywhere in AI Toolkit

- Grepped `DiffusionTrainer.py` and the base trainer for anything cuda/memory/nvidia-related: nothing. `performance_log_every` (already set to 10) only triggers `self.timer.print()` — a breakdown of wall-clock time spent in named code sections (`log_to_tensorboard`, `validate`, `batch_cleanup`, etc.) per interval, not hardware stats.
- This confirms last session's finding was correct, not a documentation gap to keep re-checking. `gpu_logger.py` (this repo) is the answer — plain `nvidia-smi --query-gpu` polling to a CSV, same role as the FL-YuE2 project's GPU logger, and it's launched the same way (background process, synced by the backup script).

## Asset downloads: standard HF Hub cache, not a bespoke local tree

- FL-YuE2 (last project) needed each weight staged into a specific `ComfyUI/models/yue2/<name>/` folder, because its own loader expected fixed local paths — hence that project's `bootstrap/setup.sh` did a download-to-staging-then-merge dance.
- Ostris's yue2 support (verified in `extensions_built_in/audio_models/yue2/yue2_model.py` and `.../src/tokenizer.py`) resolves every asset through plain `huggingface_hub.hf_hub_download` calls, which land in the standard HF cache (`~/.cache/huggingface/hub`) by default. **`bootstrap/setup.sh` for this project only needs to pre-warm that cache with `hf download` calls for the same repos** — no local directory tree to construct, no merge step, no risk of a path mismatch between what was staged and what the loader expects.
- Confirmed repos/files actually used (same identities as last project's bootstrap guessed, now confirmed from source, not a GitHub post):
  - `Comfy-Org/YuE2/checkpoints/yue2_3b_int8_convrot.safetensors` — the quantized 3B backbone (`toolkit/models/registry.py`'s yue2 default).
  - `m-a-p/MERT-v2-FullSong` — the semantic feature extractor used at latent-caching time.
  - `Mothersuperior/yue2-mothersuperior-realaudio-tokenizer-v4`: `tokenizer_head_joint_v4.pt` (semantic head) and `nar_lora_joint_v4.pt` (only loaded if `merge_nar_lora` is set — not needed for this config).
  - `m-a-p/SheetSage2` (`Comfy-Org/YuE2/audio_encoders/sheetsage2_bf16.safetensors`) — **only loaded when `model_kwargs.cot != "off"`**. This config has `cot: "off"`, so `bootstrap/setup.sh` deliberately does **not** pre-warm this one — it would be a wasted multi-GB download.

## Dataset verification (from `verification.md`, this session)

- 267 audio/caption pairs, all already native `mp3, 48000 Hz, stereo` — exactly what `YuE2AudioModel.sample_rate` (48000) expects. **No resampling or format conversion is needed before training.**
- `prepare_yue2_dataset.py --convert-wav` has a real bug (not used, but worth knowing if anyone reaches for it later): it hardcodes `-ar 44100` in its `ffmpeg` call, which would make the loader resample back up to 48k — a needless lossy round-trip on data that's already correct. Don't use that flag on this dataset.
- `cache_latents_to_disk: true` (already set) is mandatory — YuE2 raises `"needs codec tokens in the latent cache; enable latent caching"` otherwise. Not optional, not a speed knob.

## Colab torch/CUDA/torchcodec stack: pin exact +cu130 local versions

- `bootstrap/setup.sh` originally did an unpinned `pip install torch torchvision torchaudio --index-url .../cu128`, which on this ai-toolkit commit resolves to `2.11.0+cu128`. But ai-toolkit's README/manager stack is torch 2.13.0 / cu130, and `torchcodec==0.15.0` (which upstream installs as an override to `requirements_base.txt`'s stale `torchcodec==0.9.1`, per `manager/spec.py`) links against CUDA 13 (`libnvrtc.so.13`). Under cu128, loading `torchcodec` fails ("Could not load libtorchcodec"); and because torchaudio 2.11 decodes audio *through* torchcodec, `torchaudio.load()` fails on **every** dataset file — latent caching could never start. Colab's L4 driver (580.x) supports CUDA 13.
- Fix: pin the exact local versions from ai-toolkit's README manual-install block — `torch==2.13.0+cu130 torchvision==0.28.0+cu130 torchaudio==2.11.0+cu130`. Bare `==2.11.0` is **not** enough: PEP 440 treats it as matching `2.11.0+cu128`, so pip silently keeps the stale cu128 torchaudio and it then refuses to import ("PyTorch has CUDA 13.0 whereas TorchAudio has CUDA 12.8").
- Also patched before install (idempotent seds, since ai-toolkit is cloned fresh): `scipy==1.12.0` has no cp313 wheel and its failed source build aborts the **entire** `pip install -r requirements.txt`, leaving every other pin uninstalled — relax to `scipy>=1.14`; `torchcodec==0.9.1` -> `0.15.0`.
- `setup.sh` now verifies rather than trusting exit codes: `assert torch.version.cuda == "13.0"` plus a real `torchaudio.load()` of one `/content/yue2_dataset/*.mp3`. A future re-pin that breaks audio decode fails the bootstrap, not the first training step.

## Rank, EMA, and `cot` — quality rationale (carried over from last session, condensed)

- **Rank kept at 32, not raised.** All 267 captions are near-identical strings (fixed genre/production/instrumentation, only "Maqam X" + a short mood clause vary). A high-rank adapter pointed at a narrow, repetitive caption space tends to spend its spare capacity memorizing incidental per-clip artifacts rather than generalizing the shared style. Rank trades *capacity* for *generalization headroom* here, not speed — on this dataset, lower is the safer direction if overfitting shows up in samples.
- **`ema_config.use_ema: true`, `ema_decay: 0.999`.** Community YuE2 LoRA trainers specifically credit this for reducing run-to-run variance; it's a consistency lever, not a peak-quality one.
- **`model_kwargs.cot: "off"`.** Captions carry zero melodic/ABC information, so training with `cot: "full"` would pull in SheetSage2 transcription for no benefit and add real compute/VRAM cost. `"off"` is aligned with a pure style/timbre-transfer goal. Flip to `"full"` only if the goal changes to also shaping melodic structure — and if so, also update `bootstrap/setup.sh` to pre-warm SheetSage2 (see asset-download entry above).

## Backup: `loss_log.db` must not gate the settle wait

- `backup_to_gcp.py`'s `wait_for_settle` blocks a sync until the newest file in a watched folder has been untouched for N seconds — meant to avoid syncing a checkpoint mid-write. `loss_log.db` (WAL mode) is *always* being touched during an active run, the same way FL-YuE2's per-job `.log` file was in the old project. The exclusion that used to skip the `jobs/` subtree now skips `loss_log.db` (and its `-wal`/`-shm` sidecar files) by name instead, for the same reason: real state (checkpoints, `config.yaml`, samples) is written atomically and is safe to gate on; the metrics db is continuously appended and would starve every sync.

## Goal correction: full-song structure, not timbre-only -- `train_window_frames` was the gap

- The project goal was re-scoped mid-run: not a style/timbre-only adapter, but a LoRA that can generate structurally coherent full songs. Under that goal, `model_kwargs.train_window_frames` (left at its implicit default) was a real bug, not a style choice.
- Verified in `yue2_model.py`'s `condition_noisy_latents()`: with the default 1500 frames (25fps -> 60s), every step crops one random 60-second window out of the cached full-song latents and computes **both** the NAR flow loss and the AR next-token loss (`loss/ar_ce`, confirmed the dominant term in `TRAINING_ANALYSIS/ANALYSIS.md`) on that window alone. Over many steps every part of a song eventually gets sampled, but never two distant parts *together* in one gradient -- the AR expert (the part responsible for composition/arrangement) never once saw a verse-to-chorus transition. No number of additional steps at this setting would have fixed that; it's a ceiling on what the loss signal can see, not a rate-of-learning issue.
- Fix: `train_window_frames: 0` disables cropping entirely (`condition_noisy_latents` no-ops when `window <= 0`). Confirmed safe for this dataset: `verification.md` puts the AR hard context ceiling at `CONTEXT 24576 / 25fps ~= 983s`, and the dataset's longest clip is 370s. The VAE's "60s chunks" (`src/vae.py`'s `encode()`) are only an offline, encode-time memory trick over independent chunks that get concatenated into one contiguous per-song latent tensor -- not an architectural boundary that a larger training window would be crossing.
- **Not verified on real hardware yet:** whole-song windows (up to ~6x the frames of the killed run's 60s window, on the longest clips) have an unknown VRAM/step-time cost on an L4. The killed run's ~7.8s/step and ~6h ETA are void under this change -- don't reuse them. Smoke-test on the longest clips before trusting a full step budget; fall back to a bounded window (~4000-6000 frames, ~2.5-4 min) rather than 0 if the L4 can't hold whole songs.
- Deliberately left `content_or_style: "balanced"` unchanged even though it's now confirmed real (found in `BaseSDTrainProcess.py`'s generic timestep sampler, not yue2-specific -- resolves last session's "unconfirmed" flag). It biases which *noise timesteps* get weighted in the flow-matching loss (structure-of-a-moment vs. fine texture), which is a different axis from `train_window_frames` (whether the loss spans more than one moment at all). Changed one variable at a time so the next run's results are actually diagnosable; revisit `content_or_style` as a separate, later lever if `train_window_frames: 0` alone doesn't get arrangement-level coherence.
- Run killed at ~27% (step ~810/3000) rather than let it finish, since every further step under the old window was training toward a goal that had changed. See `PROGRESS.md`.

## Relaunching under the same run name auto-resumes — it does not start fresh

- Verified in `jobs/process/BaseSDTrainProcess.py`: `get_latest_save_path()` globs the run's `save_root` for `<name>*.safetensors`/`<name>*.pt` and takes the newest by ctime; `load_training_state_from_metadata()` then copies that checkpoint's embedded `training_info.step` into `self.start_step`, and the train loop is `for step in range(start_step_num, self.train_config.steps)` (~line 2528). `optimizer.pt` is loaded too (~line 2171) and adapter weights come from the latest save. **So pointing a new/changed config at an output folder that already contains checkpoints silently resumes from them** — it does not start at step 0. Setting `train.start_step` only overrides the counter; the old weights/optimizer still load.
- `backup_to_gcp.py`'s manifest only refuses to mix *different* run names, so a same-name relaunch is allowed and would overwrite same-named checkpoints in GCS and append to `loss_log.db` — the two runs would be indistinguishable after the fact.
- Correct way to genuinely restart after a config fix: archive the prior output, either via a distinct run name, or by moving the local folder and `gsutil mv`-ing the GCS prefix. Done 2026-09-19 for the killed 60s-window run: `output/akbar_arabic_rock_lora` → `..._crop60_killed` locally, same move in GCS, then the backup daemon was restarted so it writes a **fresh** `run_manifest.json` at the clean prefix.
- Latent cache is **not** invalidated by this: `/content/yue2_dataset/_latent_cache` holds full-song latents, and `train_window_frames` only crops at train time — so a relaunch reuses the cache and skips the ~12-min re-cache.

## Agent training-control policy (explicit, don't re-litigate)

- The agent may **auto-resume an unchanged, already-approved run** after an unplanned interruption (VM death, disconnect) — same config, same run name, nothing changed. This exists specifically to avoid burning a Colab session's availability waiting for a human to notice and retype a resume command.
- The agent may **not** start a new run, or resume with any changed config or hyperparameter, without the human typing the command themselves. A run finishing without errors is not the same as a run being *right* — see the FL-YuE2 project's `arabic_joint_v2`, which ran to completion cleanly while training on scores that didn't capture the maqam. That kind of mistake is cheap to catch by eyeballing a launch command before it runs and expensive (hours of rented GPU) to catch after the fact.
