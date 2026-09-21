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
  - **PS (2026-09-19, superseded in part — this bullet's premise caused the lyrics gap):** "Captions carry zero melodic/ABC information" and "a pure style/timbre-transfer goal" were the reasoning behind style-only captions in general, not only `cot`. The goal later changed to full songs *that sing the provided lyrics* (see the goal-correction entry below), and this decision was **not** revisited then. Result: all 267 captions have an empty lyrics field, so the AR was trained for 3000 steps to predict real sung-Arabic codec tokens with no lyric text in its prompt, and Arabic pronunciation degraded while style stayed strong. Root-cause analysis and fix plan: `PROGRESS.md`, "Listening evaluation + root cause". `cot: "off"` itself is a separate question and is unchanged; the empty-lyrics caption is what needs fixing. **Lesson: this decision lived only in the `prepare_yue2_dataset.py` docstring, the README, and this bullet's rationale; it was never recorded as a decision of its own, which is why the goal-correction audit didn't find it. See the lesson below.**

## Backup: `loss_log.db` must not gate the settle wait

- `backup_to_gcp.py`'s `wait_for_settle` blocks a sync until the newest file in a watched folder has been untouched for N seconds — meant to avoid syncing a checkpoint mid-write. `loss_log.db` (WAL mode) is *always* being touched during an active run, the same way FL-YuE2's per-job `.log` file was in the old project. The exclusion that used to skip the `jobs/` subtree now skips `loss_log.db` (and its `-wal`/`-shm` sidecar files) by name instead, for the same reason: real state (checkpoints, `config.yaml`, samples) is written atomically and is safe to gate on; the metrics db is continuously appended and would starve every sync.

## Goal correction: full-song structure, not timbre-only -- `train_window_frames` was the gap

- The project goal was re-scoped mid-run: not a style/timbre-only adapter, but a LoRA that can generate structurally coherent full songs. Under that goal, `model_kwargs.train_window_frames` (left at its implicit default) was a real bug, not a style choice.
- Verified in `yue2_model.py`'s `condition_noisy_latents()`: with the default 1500 frames (25fps -> 60s), every step crops one random 60-second window out of the cached full-song latents and computes **both** the NAR flow loss and the AR next-token loss (`loss/ar_ce`, confirmed the dominant term in `TRAINING_ANALYSIS/ANALYSIS.md`) on that window alone. Over many steps every part of a song eventually gets sampled, but never two distant parts *together* in one gradient -- the AR expert (the part responsible for composition/arrangement) never once saw a verse-to-chorus transition. No number of additional steps at this setting would have fixed that; it's a ceiling on what the loss signal can see, not a rate-of-learning issue.
- Fix: `train_window_frames: 0` disables cropping entirely (`condition_noisy_latents` no-ops when `window <= 0`). Confirmed safe for this dataset: `verification.md` puts the AR hard context ceiling at `CONTEXT 24576 / 25fps ~= 983s`, and the dataset's longest clip is 370s. The VAE's "60s chunks" (`src/vae.py`'s `encode()`) are only an offline, encode-time memory trick over independent chunks that get concatenated into one contiguous per-song latent tensor -- not an architectural boundary that a larger training window would be crossing.
- **Not verified on real hardware yet:** whole-song windows (up to ~6x the frames of the killed run's 60s window, on the longest clips) have an unknown VRAM/step-time cost on an L4. The killed run's ~7.8s/step and ~6h ETA are void under this change -- don't reuse them. Smoke-test on the longest clips before trusting a full step budget; fall back to a bounded window (~4000-6000 frames, ~2.5-4 min) rather than 0 if the L4 can't hold whole songs. **(Resolved — see the "A100 measured" entry below: whole-song ran to 3000/3000 on both the L4 and the A100 with no OOM.)**
- Deliberately left `content_or_style: "balanced"` unchanged even though it's now confirmed real (found in `BaseSDTrainProcess.py`'s generic timestep sampler, not yue2-specific -- resolves last session's "unconfirmed" flag). It biases which *noise timesteps* get weighted in the flow-matching loss (structure-of-a-moment vs. fine texture), which is a different axis from `train_window_frames` (whether the loss spans more than one moment at all). Changed one variable at a time so the next run's results are actually diagnosable; revisit `content_or_style` as a separate, later lever if `train_window_frames: 0` alone doesn't get arrangement-level coherence.
- **PS:** this audit fixed the config but missed the caption side of the same goal change (empty lyrics). See the "Lesson" entry below.
- Run killed at ~29% (step 875/3000) rather than let it finish, since every further step under the old window was training toward a goal that had changed. See `PROGRESS.md`.

## Lesson: a goal change invalidates every decision made under the old goal — audit them all, not just the config

- **What happened.** The goal moved from "style/timbre adapter" to "structurally coherent full songs that sing the provided lyrics". Only the config-level consequence (`train_window_frames`) was caught. The dataset-level consequence (style-only, lyric-free captions) survived, because it was baked into a *build script's docstring*, not into the config the audit was reading. Cost: a full 3000-step run (~L4 + A100 hours) trained toward the wrong target for the lyric-following half of the goal. The symptom (bad pronunciation) also first sent the investigation to YAML knobs (`ar_loss_weight`, `ar_kl_weight`, `ignore_if_contains`) that were downstream of the real cause.
- **Rule 1 — on any goal change, list every artifact that encodes the old goal** and re-justify each against the new one: dataset captions (what's in them, and what's *missing*), `cot`/`do_separation`/loss-weight flags, training-time `sample.samples` prompts, and the evaluation protocol. Config is only one of those places.
- **Rule 2 — record deliberate omissions as decisions.** "We left X out on purpose" is a decision with a premise; if it lives only in a code comment, it will outlive its premise silently. Put it here with the goal it was justified by.
- **Rule 3 — when a training input is empty by design, ask what the loss then cannot teach.** Empty lyrics meant the AR loss could never reward lyric-following, and the `ar_kl` anchor (computed on the same lyric-less prompt) could never protect it either.
- **Rule 4 — test the goal metric *during* training, not only after.** Every training-time sample prompt had no lyrics, so checkpoints from step 250 onward could show style but never pronunciation; the gap surfaced only in a post-run listening test. Sample prompts should exercise every part of the stated goal.
- **Rule 5 — when a result looks like a tradeoff, look for missing signal first.** Last session first framed this as an inherent style-vs-pronunciation tradeoff tunable via loss weights. It was a missing-data problem; no weight balance could have fixed it.

## Relaunching under the same run name auto-resumes — it does not start fresh

- Verified in `jobs/process/BaseSDTrainProcess.py`: `get_latest_save_path()` globs the run's `save_root` for `<name>*.safetensors`/`<name>*.pt` and takes the newest by ctime; `load_training_state_from_metadata()` then copies that checkpoint's embedded `training_info.step` into `self.start_step`, and the train loop is `for step in range(start_step_num, self.train_config.steps)` (~line 2528). `optimizer.pt` is loaded too (~line 2171) and adapter weights come from the latest save. **So pointing a new/changed config at an output folder that already contains checkpoints silently resumes from them** — it does not start at step 0. Setting `train.start_step` only overrides the counter; the old weights/optimizer still load.
- `backup_to_gcp.py`'s manifest only refuses to mix *different* run names, so a same-name relaunch is allowed and would overwrite same-named checkpoints in GCS and append to `loss_log.db` — the two runs would be indistinguishable after the fact.
- Correct way to genuinely restart after a config fix: archive the prior output, either via a distinct run name, or by moving the local folder and `gsutil mv`-ing the GCS prefix. Done 2026-09-19 for the killed 60s-window run: `output/akbar_arabic_rock_lora` → `..._crop60_killed` locally, same move in GCS, then the backup daemon was restarted so it writes a **fresh** `run_manifest.json` at the clean prefix.
- Latent cache is **not** invalidated by this: `/content/yue2_dataset/_latent_cache` holds full-song latents, and `train_window_frames` only crops at train time — so a relaunch reuses the cache and skips the ~12-min re-cache.

## Extending a finished run overwrites the final adapter — snapshot step 3000 first

- **Why it matters.** The end-of-run save is `self.save()` with no step (`BaseSDTrainProcess.py:2814`), which
  names the file `<run name>.safetensors` with no step suffix (`save()`: `filename = f'{self.job.name}{step_num}.safetensors'`).
  Extending `akbar_arabic_rock_lora` past 3000 under the same run name will therefore rewrite
  `akbar_arabic_rock_lora.safetensors` — the v2 step-3000 artifact, and the exact file the audio.cpp LoRA converter
  consumed (its two outputs are pinned by sha256 in the T4 entry below). Numbered checkpoints are also rotated by
  `max_step_saves_to_keep: 12`, which v2 already filled (`docs/FINAL_BACKUP.md` expects 11 numbered + the final), so
  each new save deletes the oldest local checkpoint.
- **GCS is not append-only for that file.** `docs/FINAL_BACKUP.md:65` calls GCS append-only; that holds for numbered
  checkpoints, but the un-suffixed final adapter is the same-name case described in the auto-resume entry above and
  would be overwritten. Fixing that wording is the user's call.
- **`train.start_step` is not the answer.** It is a config key, not a CLI flag, and it only sets the step counter: with
  it unset, the counter comes from the newest checkpoint's embedded metadata (`:887–891`); with it set, that read is
  skipped (`:2151–2153`). It does not choose which checkpoint loads — `get_latest_save_path()` always takes the newest
  `<run name>*.safetensors` — so it does nothing to protect the final adapter.
- **`network.pretrained_lora_path` is not an equivalent of a resume.** It is only consulted when the save folder has no
  checkpoint (`:859–862`), and it deliberately skips the metadata (`:873–876`). It would load weights only: no
  optimizer state, no EMA, and no step counter unless `start_step` is also set. That is a different experiment. The rest
  of its loading path was not traced and no run has tested it.
- **EMA (source-read, untested).** Saved checkpoints are EMA weights (`save()` puts the EMA in eval first); `setup_ema()`
  builds a fresh EMA from the current params after the optimizer loads, and no EMA state restore was found. A resume
  therefore continues from the EMA'd weights and restarts the average. The step-250 A100 resume already went through
  this. All line numbers above are from a shallow clone of ai-toolkit `main` on 2026-09-21 and may drift.
- **Rule before any extension of v2.** (1) Copy the final adapter to a separate GCS prefix, outside the run's prefix,
  as `akbar_arabic_rock_lora_v2_step3000.safetensors`, and record its sha256. (2) Extend under a **new run name**, with
  the step-3000 checkpoint and `optimizer.pt` copied into that run's output folder, so ai-toolkit performs a true
  resume and the v2 folder stays untouched. (3) Per `AGENTS.md`, the user types the launch command; a changed step
  count is a changed config. Whether a separate step-3000 snapshot already exists in GCS has not been checked.

## Whole-song (`train_window_frames: 0`) on L4 — measured

- The config comment's "UNVERIFIED ON THIS HARDWARE" is now resolved. Whole-song ran cleanly on the L4 over steps 1–295: **~13.4 s/step** median, 100% GPU util, ~**70.5 W of L4's 72 W TDP**, 12.9 GB mean / **15.8 GB peak** of 24 GB, ~74 °C. No bounded-window fallback was needed on VRAM grounds. 3000 steps ≈ **~12 h** (incl. ~1.2 h of sampling every 250).
- **Do not reuse the earlier 60 s-window run's ~7.8 s/step or ~6 h ETA** for this config — whole-song is ~1.7× slower per step.

## L4 vs A100 for this workload: ~2–2.6×, not 4× (and A100 here is 80 GB)

- The measured ~100% util and ~98%-of-TDP power mean the L4 is GPU-bound, not dataloader-bound, so a faster GPU helps. But the ceiling is the tensor-core ratio: BF16/FP16 dense **121 (L4) vs 312 (A100) = 2.58×** (INT8 242 vs 624 = 2.57×). The run is **not** memory-bandwidth-bound (weights read well under 1 GB/s at 13 s/step), and **A100's FP32 CUDA-core rate is *lower* than L4's (19.5 vs 30.3 TFLOPS)**, so non-tensor ops don't speed up. Realistic speedup ≈ **2–2.6×** (~12 h → ~4.5–6 h).
- Colab compute-unit break-even = `6.7 / 1.54` = **4.35×**, so A100 costs ~**1.7–2.2× more units** for the same run. It buys turnaround time, not savings. Full write-up: `docs/GPU_L4_VS_A100.md`.
- The Colab A100 on offer here is **SXM4-80GB** (2,039 GB/s, 80 GB VRAM) but the **same 312 TFLOPS compute** — the ~2.6× ceiling does not change.

## A100 measured: ~4.3×, and the whole-song run completed 3000/3000

- Measured over the completed run, not estimated: A100-SXM4-80GB **median 3.10 s/step** (p10/p90 2.59 / 3.69, 2730 post-resume steps) vs the L4's 13.4 s/step = **~4.3×**, well above the 2–2.6× peak-spec ceiling in `docs/GPU_L4_VS_A100.md`. Sample generation was also ~42% faster (~226 s vs ~388 s per event). So the L4-vs-A100 cost direction is unchanged (A100 costs more compute units for the same run), but its wall-clock win is larger than the note predicted: ~12 h of L4 work ran in ~3 h on the A100.
- Whole-song (`train_window_frames: 0`) ran to **3000/3000** with peak ~15–16 GB on both the L4 (24 GB) and the A100 (80 GB) — no OOM on either, no bounded-window fallback needed. This resolves the config comment's "UNVERIFIED ON THIS HARDWARE" warning and the earlier "Not verified on real hardware yet" bullet.
- `loss/ar_kl` never plateaued: it ended at **1.50** (from 0.37), its highest value, after a brief pause near 1.2 around steps 900–1300. It is the one metric still trending upward at the end — the first lever to consider (fewer steps / lower LR / lower `ar_kl_weight`) if a v2 is run. See `TRAINING_ANALYSIS/ANALYSIS.md`.

## Cross-VM / cross-GPU resume (Colab session switch)

- Run state is portable across VMs/GPUs: restore the GCS `output/` prefix into `/content/ai-toolkit/output/<run>/` on the new VM, then launch the identical command — ai-toolkit auto-resumes from the newest checkpoint (see the auto-resume entry above). Runbooks: `docs/PAUSE_RESUME.md`, `docs/START.md`.
- A run is only portable once a checkpoint exists **and** reached GCS. With `save_every: 250`, the first resumable point is step 250; killing before that loses all progress. (We stopped the L4 run at step 295, so resume is from 250.)
- The latent cache (`/content/yue2_dataset/_latent_cache`) is per-VM and **not** in GCS, so a fresh VM rebuilds it (~12 min) on first launch — expected.
- Never run the same run name on two VMs at once: they share one GCS prefix and `run_manifest.json`. Stop one before starting the other.
- Performance-only knobs (e.g. `gradient_checkpointing`) don't affect resume or the trained objective; changing hyperparameters / network / lr defines a *different* experiment, not a resume.

## v2 dataset build diverged from `AGENTS.md`'s approved amendment — user's call, invariants held anyway

- `AGENTS.md`'s "Approved amendment: lyric-conditioned captions" specifies a
  gated Colab-agent procedure: manifests pushed to the repo, a read-only
  investigation report, a Gate on caption format, an append-only
  `add_lyrics_to_captions.py` patch script. The user instead worked locally
  and offline with a separate agent that had no knowledge of this repo's
  docs, and had it rebuild the dataset from scratch from the raw
  `min_4stars_ai_music` tree rather than patch the existing captions in
  place.
- Claude flagged the divergence before proceeding; the user chose to
  continue — dataset/config decisions are the user's to make, not the
  agent's or the doc's.
- The amendment's underlying safety invariants held regardless of the path
  taken: audio untouched, shortlist logic unchanged (same "in manifest AND
  on disk" rule), v1 preserved (archived, not overwritten), no GPU/YAML
  touched during the build.
- Practical effect: the repo's docs said nothing about the v2 build until
  this session's update — a known gap the user deliberately deferred closing
  until now.

## Caption lyric format for v2 — Claude's call, delegated by the user

- The user delegated the caption lyric-formatting rules "as you see fit."
  Rules applied, named as such at the time:
  - The raw `///***///` line is removed entirely.
  - A bracketed tag whose content starts with a canonical section name
    (`Intro`, `Verse` [+ number], `Chorus`, `Pre-Chorus`, `Bridge`, `Outro`,
    `Hook`, `Refrain`) collapses to bare `[Section Name]`, dropping
    everything after the first `|` (production descriptors).
  - Any other bracketed tag — arrangement/SFX asides like `[guitars surge —
    Ajam]`, `[Instrumental Interlude | ...]` — is dropped entirely and
    logged.
  - Diacritics, the trailing `...` on lyric lines, and the Arabic wording
    itself are never touched.
- **Binding on anything that builds inference/sample prompts** — the
  held-out set and any future eval tooling must use this same format, not
  re-derive their own.
- One bug found in review: the first pass's tag whitelist lacked `Refrain`,
  used as a chorus-equivalent in some tracks; `[Refrain | ...]` was dropped
  as SFX noise, leaving real sung sections unlabeled. Fixed by whitelisting
  `Refrain`; rebuilt and reverified.
- Still-open diagnostic, never run: base model, no LoRA, same seed, eval
  lyrics with vs. without Suno descriptors — available if v2 pronunciation or
  structure comes out oddly and the cause needs isolating from the caption
  format itself.

## Dataset naming convention: descriptive suffixes on archives, no numeric versions

- Decided (user): "v1, v2, v3 ... those are meaningless." The live dataset
  and the live run keep their original plain names; only a *superseded*
  artifact gets a suffix, and that suffix describes why it was superseded,
  not a version number.
- Applied this session: the plain name `yue2_dataset` always means the
  current dataset — v1's content moved to
  `yue2_dataset_v1_style_only_obsolete` locally /
  `dataset_v1_style_only_obsolete/` in GCS, freeing the plain name for v2,
  which now occupies it. Same pattern already used for the killed
  60s-window run (`akbar_arabic_rock_lora_crop60_killed`).
- Consequence: neither the training YAML's `folder_path` (absolute
  `/content/yue2_dataset`) nor `GCP_DATASET_PATH` (points at `dataset/`)
  needed to change — the promotion is entirely a naming/content swap at the
  storage layer. See `bootstrap/setup.sh:104-115`'s `job_dataset()` for why
  this works: it rsyncs whatever `GCP_DATASET_PATH` currently points to,
  with no notion of "v1" or "v2" baked in.
- A loose file named e.g. `akbar_arabic_rock_lora.safetensors` becomes
  ambiguous between the two datasets' outputs once separated from its
  containing folder — keep archive folder names attached, don't rename the
  file itself.

## Trigger word: v2's baked-in prefix does not double with `trigger_word`

- v1's dataset captions had no trigger baked in (`verification.md:43`);
  `trigger_word: "arabmaqamrock"` in the YAML had `ai-toolkit` prepend it at
  train time.
- Re-verified against upstream `ai-toolkit main` this session:
  `inject_trigger_into_prompt` (`toolkit/prompt_utils.py:715-748`, called
  from `get_caption` in `toolkit/dataloader_mixins.py:398-461`) prepends
  `trigger + " " + caption` (space, no comma) and only does so when the
  trigger appears **zero** times already (`:738-742`).
- v2's captions now start with a baked-in `arabmaqamrock ` prefix,
  byte-equivalent to what the injector would add — so the injector's
  zero-occurrence check means it does **not** double it. `trigger_word`
  stays set in the YAML unchanged.
- The YAML's line-10 comment ("dataset captions have none baked in") is now
  stale and was not edited — see the deferred comment-cleanup item.
- `setup.sh:177` clones `ai-toolkit` unpinned (`main`), so this is
  re-verified against current upstream, not assumed; re-check if the
  toolkit's caption-injection code is ever suspected of having changed.

## Run name: reuse `akbar_arabic_rock_lora`, no suffix

- Decided (user). Reasoning: the repo's own precedent is that archives get a
  descriptive suffix when superseded and live runs never get a number (see
  the dataset-naming entry above); reuse means `name`, `log_dir`, and
  `backup_to_gcp.py`'s hardcoded `JOB_NAME = "akbar_arabic_rock_lora"`
  (`backup_to_gcp.py:69`) all stay untouched, no code change required.
- Reuse is only bug-free under these conditions, all must hold at launch:
  1. `/content/ai-toolkit/output/` is empty on the VM before launch —
     `get_latest_save_path()` silently resumes from the newest matching
     `.safetensors` otherwise (see the auto-resume entry above).
  2. The GCS restore rsync (`docs/BACKUP_RESTORE.md`) is **not** run before
     this launch — that step is for resuming an interrupted run, not
     starting a new one.
  3. After any smoke test, wipe `output/akbar_arabic_rock_lora/` (or use a
     fresh VM) if it wrote any `.safetensors` — with `save_every: 250`,
     only a smoke test reaching step 250+ would.
- v1's finished run is archived as `akbar_arabic_rock_lora_v1_nolyrics_archived`
  in GCS (185 objects, verified) — the plain name is free for v2 to reuse.

## Held-out evaluation set: `evaluation_alharith.json` is not clean, and how the replacement was built

- **Finding:** `INFERENCE/evaluation_alharith.json`'s four prompts are not
  all held-out. Checked line-by-line (diacritic-insensitive) against the 267
  v2 training captions: Hijaz shares 8/18 distinct lines, Kurd 6/24,
  Nahawand 6/24 — all from training workspaces named
  `{maqam}_alharith_bin_heliza_22082026` (same Mu'allaqa poem, overlapping
  lines across workspaces). **Ajam is clean, 0/22 shared.**
- The contamination is structural, not a one-off: the same poem section
  recurs across multiple workspaces and takes (267 captions = only 157
  distinct cleaned lyric texts). So held-out status can only be judged by
  actual lyric-line overlap against the full training set — never by title,
  workspace name, or "not in the training shortlist," since a
  non-shortlisted take can still carry lyrics a shortlisted take trained on.
- Normalization used for the overlap check (and everywhere else in v2):
  delete Arabic diacritics (U+064B–U+065F, U+0670) and `.` and whitespace;
  map U+0671 (alef wasla) → U+0627; a lyric line is any non-empty line that
  doesn't start with `[` and isn't `///***///`.
- **Replacement set built** by the user's local offline agent, from a
  self-contained spec (no reference to this repo's docs) that reused v2's
  build-script functions. Selection: one pick per maqam, using that maqam's
  own text (first `Maqam (Hijaz|Kurd|Nahawand|Ajam)` match in the track's
  `styles`), `shared_lines == 0` against all 267 training captions, 24–28
  lyric lines, tags covering Intro+Verse+Chorus+Outro, four different source
  workspaces, zero mutual overlap between the four picks themselves.
- Claude independently re-verified the delivered files rather than trusting
  the agent's own report: each prompt parses through the toolkit's real
  `parse_caption`; correct maqam and `arabmaqamrock ` prefix; only allowed
  section tags present, no `|`, no `///***///`; each lyric line
  character-for-character identical to its manifest source; 0 shared
  normalized lines against every `yue2_dataset/*.txt`.
- The Ajam pick (`alharith_bin_heliza_22082026`,
  `03-الرد-على-الواشي-والرسوخ-كالأرعن`) shares 8 lines with
  `evaluation_alharith.json`'s own (clean) Ajam entry — same poem, neither
  trained on — so it's directly comparable to the existing full-length
  inference evaluation.
- Open, user's call: whether the post-run evaluation uses this held-out set
  or `evaluation_alharith.json`'s clean Ajam entry (or both); whether to
  commit `prepare_yue2_dataset_v2.py` for reproducibility, since the report
  cites it as the prompts' source but it's not in the repo.

## `sample.duration: 360` — why, and its cost

- v1's training-time samples ran at `duration: 120`, generating from
  lyric-free prompts, so no checkpoint sample could ever show
  pronunciation — only the post-run listening test could. Since these
  samples are the only in-training look at the actual goal metric (structure
  + lyric fidelity), they now carry real held-out lyrics, and duration was
  raised to 360 so a sample has room to show a full arc
  (intro→verse→chorus→outro) rather than being cut off mid-section.
- Cost: sample generation scales with generated length; one 4-prompt event
  at 120s cost ~226s on the A100 (`TRAINING_ANALYSIS/ANALYSIS.md:34`). At
  `sample_every: 250` over `steps: 3000`, that's 12 sample events. Tripling
  duration to 360 roughly triples the per-event generation cost — factor
  this into any ETA recompute in the final YAML sanity pass, not just the
  training step time.

## Agent training-control policy (explicit, don't re-litigate)

- The agent may **auto-resume an unchanged, already-approved run** after an unplanned interruption (VM death, disconnect) — same config, same run name, nothing changed. This exists specifically to avoid burning a Colab session's availability waiting for a human to notice and retype a resume command.
- The agent may **not** start a new run, or resume with any changed config or hyperparameter, without the human typing the command themselves. A run finishing without errors is not the same as a run being *right* — see the FL-YuE2 project's `arabic_joint_v2`, which ran to completion cleanly while training on scores that didn't capture the maqam. That kind of mistake is cheap to catch by eyeballing a launch command before it runs and expensive (hours of rented GPU) to catch after the fact.

## Token-count check (agenda step 5b) — measured, no overflow

- Never previously measured with the real tokenizer; `verification.md` only
  had a char-count/4 estimate (~200 tokens per caption). Measured this
  session on a CPU-only Colab runtime, no `ai-toolkit` clone needed — the
  tokenizer is a tensor embedded in the checkpoint itself
  (`text_encoders.yue2_tokenizer_json`), extracted via `safetensors`'
  lazy `safe_open` (no full ~4GB model load), then run through the plain
  `tokenizers` library. Script: `check_token_counts.py` (not committed —
  local tooling, like the v2 build script).
- Reproduced the AR expert's actual prefix construction, verified against a
  fresh `ostris/ai-toolkit` clone (`src/tokenizer.py:43-51`, `cot="off"`
  matching this project's `model_kwargs.cot`):
  `[EOD] + encode(INSTRUCTION + "[Tags]" + style + "[Lyrics]" + lyrics) +
  [ABC_START, ABC_END, MUSIC_START]`, checked against
  `CONTEXT = 24576` (`src/model.py:30`).
- **Results, real BPE tokenizer, both sets clear with large margin:**
  - 267 v2 training captions: prefix tokens 780–1631 (mean 1214). Checked
    against the worst-case 370s clip (9250 audio tokens @ 25fps,
    `verification.md`'s dataset max) — tightest case
    (`hijaz_short-poems_16082026_027`) still has 13,690 tokens of headroom.
  - 4 held-out eval prompts: prefix tokens 983–1237 (mean 1124). Checked
    against `sample.duration: 360` (9000 audio tokens) — tightest case
    (Hijaz) has 14,334 tokens of headroom.
- No caption anywhere near the 24,576 context ceiling — token count is not a
  risk for this run. Nothing to change in the config.

## v2 finished: the lyric fix worked as designed, and `ar_kl` drift replicated

- v2 (lyric-conditioned captions, otherwise identical to v1) ran **3000/3000**
  cleanly, 2026-09-20. Full numbers: `TRAINING_ANALYSIS/ANALYSIS.md`.
- **`loss/ar_ce` is ~0.35 lower than v1's at the same steps and at the end**
  (3.61 vs 3.97 last-50). This is the expected, mechanical consequence of the
  AR now receiving the real lyrics in its prompt — it confirms the caption fix
  reached the AR (v1's failure), but it is **not** a quality claim on its own.
  Style/pronunciation still has to be judged by ear on the samples.
- **`loss/ar_kl` rose unbroken to the end in both runs** (v1 0.37 → 1.50, v2
  0.39 → **1.54**; v2 marginally ahead in the second half). `ar_kl_weight: 0.2`
  visibly did not make it plateau. It stayed bounded (no blow-up), but this is
  now a **reproduced** two-run trend, not a v1 quirk — making it the first,
  well-motivated lever for any v3: fewer steps, lower LR, or lower
  `ar_kl_weight`. One variable at a time (see the one-variable discipline in
  `PROGRESS.md`/the kill-and-relaunch entries).
- **Diagnostic caveat to carry forward:** `ar_ce` and `ar_kl` are computed under
  different prompt conditioning between v1 and v2, so cross-run loss values are
  directional evidence, not an A/B on audio quality. The samples are the arbiter.

## T4 VRAM is governed by the attention kernel, not the cap or the LoRA — force `yue2.attention=flash`

- `0xShug0/audio.cpp` @ `e3de8e3` OOM'd on a T4 building the NAR graph (Hijaz/seed-1000, LoRA on,
  cap 6200): `CUDA error: out of memory` at `ggml-cuda.cu:535`, exit 134. A first write-up (`ebb3f10`)
  blamed a fixed LoRA decoder-merge cost (`decoder_merge_values`, 2,818,572,288 bytes = ~2.6 GiB, constant
  across runs) plus frame-scaled NAR allocation, and posited a "≤5800-frame ceiling." **That ceiling is
  retracted** — it was a guess, never measured. The "fix" (drop to cap 6500) OOM'd too, and the raw logs show
  both outcomes under that cap: seed 1000 self-terminated at 6,355 frames (`truncated=0`), seed 1001 hit its
  cap at 6,500 (`truncated=1`), both OOM'ing in the NAR graph. The 6,536 figure came from a cap-9000 seed-1001
  attempt whose log a later cap-6500 rerun overwrote under the same filename.
- **Verified cause: the attention kernel.** On compute capability 7.5, `yue2.attention=auto` selects the
  **eager** NAR attention (`audio.cpp` `src/framework/core/attention_fallback.cpp`: eager for CC 700–799).
  Controlled, LoRA-on, eager: cap 5800 → 14,033 MiB / cap 6000 → 14,577 MiB / cap 6200 → OOM. With
  `--session-option yue2.attention=flash`: cap 6200 → **7,607 MiB** (exit 0) and cap 9000 → natural
  self-termination at **6,355 frames / 7,683 MiB** (exit 0). About half the VRAM; the OOM point passes.
  The log reports only `allow_flash 0`/`1`, not the chosen kernel — the conclusion rests on the measured
  VRAM drop, not a kernel name in the log.
- Consequence: uncapped-length, LoRA-on inference on a 16 GB T4 is back on the table (peak ~7.7 GiB at
  4:14, ~76 MiB added from 6,200→6,355 frames), no bounded-window fallback needed. `nvidia-smi` reports
  15,360 MiB, but the ggml runtime logs **14,912 MiB** total VRAM (the allocator's figure) — use 14,912 for
  headroom; Colab High-RAM raises system RAM only.
- Length mechanics for any future YuE2 inference: output length is `semantic_max_tokens` (25 frames/s);
  `--duration-seconds` is ignored; the model self-terminates (`truncated=0`) under an ample cap; the generic
  `--temperature/--top-p/--top-k/--repetition-penalty` flags are no-ops — use the prefixed
  `semantic_*`/`abc_*` request-options.
- **Listening result on the flash render (2026-09-21, user):** the full 4:14 Hijaz/seed-1000 render
  (`out/Hijaz_1000_cap9000_flash.wav`) was judged good/acceptable, with no noticeable pronunciation problems. Two isolated
  words were flagged: `له` heard as `يه`, and `المسلوب` heard as `المسيوب`. The user reports both also occur with "the
  normal model"; **which baseline that meant (PyTorch v2 step-3000, or base YuE2) was not pinned down** — if only the
  PyTorch path is clean on those words, the flash path could be adding drift, so pin it down when logging. One track,
  one seed: this is not yet a verdict on the flash path in general.
- Still open: the other three maqams and other seeds with flash, and lengths beyond 4:14.
- **Why `auto` picks eager on a T4 (inference, not verified on hardware).** Upstream's gate is
  `cc >= 700 && cc < 800` (`attention_fallback.cpp`), added by `e39fe22` ("fallback for GPUs without flash MMA kernels
  (sm70)") for Volta (7.0), where the MMA flash kernel lacks usable device code. The range also catches Turing (7.5),
  so the T4 may get eager attention through an over-broad range rather than a real kernel limitation. That would make
  forcing `flash` legitimate rather than a workaround; it would also mean an L4 (8.9) needs no override. The measured
  VRAM drop supports this, but the log does not show which kernel actually ran.
- **LoRA conversion is required, and it must be exact.** ai-toolkit saves a *fused* LoRA
  (`text_encoders…self_attn.qkv_proj`/`o_proj`, `diffusion_model…mlp.gate_up_proj`/`down_proj`; rank 32,
  alpha == rank). audio.cpp does exact-name lookups for *unfused* per-projection adapters — AR
  `layers.{i}.self_attn.{q,k,v,o}_proj` + `mlp.{gate,up,down}_proj`, NAR `layers.{i}.nar_self_attn.*` +
  `nar_mlp.*`, no `model.` prefix and no `.weight` suffix. `converter/convert_aitoolkit_yue2_lora.py` splits
  each fused B by rows (A copied verbatim, byte-level, no torch); re-running it on the final step-3000
  `akbar_arabic_rock_lora.safetensors` reproduced both adapter files byte-identically (sha256 `747d5cfe…` /
  `ad2c8d86…`). The two outputs are `akbar_arabic_rock_lora_{ar,nar}.safetensors`, both applied at scale 1.0.
- Corollary for any doc that repeats it: `docs/yue2-gguf-lora-findings.md` (`afab34e`) says the LoRA needs
  no conversion for `audio.cpp` — **wrong for this file** (see the conversion note above); that doc was left
  stale on purpose, flag it if it comes up.

## Inference tests run commands manually; the Colab agent reports from files, not memory

- Changed 2026-09-21 (user's call), because of how the OOM post-mortem went: the Colab agent's own prose
  summary in `PROGRESS.md` (`ebb3f10`) asserted an unsupported "≤5800-frame ceiling" and misattributed a
  6,536-frame figure that came from a log later overwritten under the same filename. When the human reads the
  same raw files, a bad summary is caught immediately.
- New workflow for Colab-agent inference tests: the agent writes the exact commands to
  `agent_notes/current.md` as a copy-paste block and **does not run them**; the user runs them in a separate
  terminal; the agent monitors by **reading** `out/*.log`, `_runs_status.log`, `_gpu.csv` and reports only
  what the files say, quoting the line rather than paraphrasing.
- Output filenames must carry the varying parameter (e.g. the cap) — a cap-9000 log was once silently
  overwritten by a cap-6500 rerun under the same name, which produced the wrong 6536 frame figure above.
- Writing this workflow into `AGENTS.md` is a user's call, not done here.

## audio.cpp seeds and reproducibility: what it gives, and the sidecar policy

- **Seed range.** `yue2.seed` is accepted in `[0, 2^63)` (`request.cpp`), default 1234 (`session.cpp`), but both the AR
  sampler (`ar_runtime.cpp:683`) and the NAR noise (`nar_runtime.cpp:637`) seed with
  `std::mt19937 rng(static_cast<uint32_t>(seed))`. Seeds that differ by a multiple of 2^32 produce identical output. **Use
  seeds below 2^32.** (Source-read at upstream `f7f5dd1`.)
- **Nothing is recorded by default.** The settings line (seed, cot, guidance, `num_inference_steps`, context, sampling
  options) is emitted only when trace logging is enabled (`pipeline.cpp`, `run()`); no metadata sidecar was found in the
  YuE2 path. `--batch-manifest-out` exists in the CLI help, but what it records was not checked.
- **Policy: every generated track gets a JSON sidecar**, written by the wrapper around `scripts/run_one.sh`, with the seed
  drawn and written *before* generation so a crash still leaves a record (`secrets.randbelow(2**32)` when random).
  Fields: seed; full command and request options; prompt-file sha256; sha256 of the main GGUF, the VAE GGUF and both LoRA
  files; checkpoint step; `audio.cpp` commit; GPU name, compute capability and attention mode; the cap, final frame
  count, `truncated`, wall time; and the output WAV's sha256. Output filenames must carry every varying parameter (see
  the manual-execution entry above).
- **Untested hypothesis — the seed alone may not reproduce a track.** The seed pins the RNG, but tokens are sampled from
  GPU-computed logits; a different GPU or attention kernel (T4 vs L4, eager vs flash) could shift the floats slightly and
  flip one sampled token, after which the trajectory diverges. Not observed, not ruled out. Two cheap tests settle it:
  the same seed twice on the T4 (is the WAV bit-identical?), then the same seed on T4 vs L4. Until then, the sidecar's
  GPU and attention-mode fields are what make a replication attempt honest, and the WAV itself is the only guaranteed copy
  of a track.

## Current plan (2026-09-21): generate many tracks with the step-3000 LoRA before deciding on more training

- **Deferred, not dropped:** extending training past 3000. It is a future step; see the extension entry above for what
  must happen first.
- **Urgent:** generate many tracks with random seeds using `audio.cpp` + GGUF + the converted step-3000 LoRA, with
  `yue2.attention=flash` forced, and use them to judge whether 3000 is good enough or more fine-tuning is needed. The user
  suspects more fine-tuning is needed; nothing measured yet says so, and `ar_kl` has risen in both runs (see the v2
  finished entry), so more steps could as easily hurt.
- **Order:** (1) the sidecar wrapper, (2) the same-seed-twice bit-identity test on the T4, (3) time one full track to size
  the batch in compute units, (4) the batch.
- **Hardware (user's figures, 2026-09-21 — recheck current Colab pricing):** T4 High-RAM (~1.27 CU/h) is the inference
  workhorse, pushed to its limit; L4 (~1.54 CU/h) is optional; the A100 (~6.77 CU/h) is for fine-tuning only, not inference.
  No GGUF generation time is recorded anywhere in the repo yet.
- **Verdict criteria are fixed before generating, not after.** What counts as "3000 is enough" vs "needs more training"
  is to be set by the user, e.g. a substitution rate on hard words, or maqam adherence; different failures point to
  different levers (more steps, lower `ar_kl_weight` / LR, dataset changes). Placeholder: **TODO(user) — write the
  criteria here before the batch runs.** Suggested method: quick triage listening across all tracks, and word-level
  interviewer probes only on flagged ones.

## `audio.cpp`'s ~30 min Colab build was `--model-set full` compiling all 80+ families — not something to cache around

- **Root cause, confirmed from `audio.cpp`'s own README, not guessed.** Composite builds are a first-party feature:
  `full` (the default `scripts/build_linux.sh` uses if you don't pass `--model-set`) compiles every one of `audio.cpp`'s
  80+ model families — TTS, ASR, VAD, diarization, all of it — not just `yue2`. That is almost certainly the entire
  30-minute cost observed this session. **Nothing to cache, build once, or design infrastructure around — just don't
  build what isn't needed.**
- **Fix, three flags, all first-party (no custom scripting required):**
  ```
  scripts/build_linux.sh --backend cuda --cuda-arch 75 --ccache \
    --model-set custom --models yue2 \
    --target audiocpp_cli
  ```
  - `--model-set custom --models yue2` — compiles only the `yue2` loader instead of all 80+ families.
  - `--cuda-arch 75` — T4 is Turing, compute capability 7.5. Without `--cuda-arch`, the build targets a **portable
    multi-arch list** (works on many GPUs, much slower to build) instead of just the local GPU.
  - `--ccache` — wires up `ccache` as the compiler launcher. Per the README: "leaves a cold build about as slow as it
    already is and makes a rebuild roughly **14x faster**." This is the project's own answer to "cache the build" —
    **persist the ccache directory itself** (e.g. to GCS/Drive, same pattern as everything else this project persists
    across VMs) rather than designing a commit-keyed tarball cache from scratch. A from-scratch GCS-tarball build-cache
    scheme was drafted earlier this session and should be treated as **superseded and unnecessary** — don't rebuild it
    next session.
- **No prebuilt CUDA binary exists for Linux to skip the build entirely.** Checked the Releases page: prebuilt packages
  cover Windows (CPU/Vulkan/CUDA) and Ubuntu x64 (CPU/Vulkan only) and macOS (Metal). No Ubuntu+CUDA prebuilt — a
  from-scratch build (now scoped down per above) is genuinely required on Colab's T4.

## YuE2 LoRA loading is a native, first-party `audio.cpp` feature — no server/wrapper code needed, and it confirms the conversion requirement already in place

- **Verified against `audio.cpp`'s own `docs/models/yue2.md`, not inferred.** LoRA loading is built into the CLI/server
  via session options — nothing to build or patch:
  ```
  --session-option yue2.ar_lora=/path/to/akbar_arabic_rock_lora_ar.safetensors \
  --session-option yue2.ar_lora_scale=1.0 \
  --session-option yue2.nar_lora=/path/to/akbar_arabic_rock_lora_nar.safetensors \
  --session-option yue2.nar_lora_scale=1.0
  ```
  Either adapter can be used alone or together. A new session is required to change adapters or scale (merged weights
  are cached in CPU memory for the life of the session, not re-merged per request). `0` disables an adapter entirely,
  including the NAR adapter's `vae2llm`/`llm2vae` projection replacements.
- **This confirms, rather than replaces, the existing conversion step.** `audio.cpp`'s docs require "unfused SafeTensors
  files, not the `_comfyui` layouts" — exactly the fused→unfused split `converter/convert_aitoolkit_yue2_lora.py`
  already produces (see the earlier T4/LoRA-conversion entry). **No new conversion tooling needed; the existing
  converter's output format is the correct target.**
- **Do not confuse `cot` guidance between adapters.** `audio.cpp`'s docs recommend `cot=full` for *their* reference
  instrumental adapter (Mothersuperior's). That is unrelated to `akbar_arabic_rock_lora`, which was trained with
  `model_kwargs.cot: "off"` — keep `cot=off` at inference to match training, regardless of what the upstream docs say
  about a different LoRA.
- **BF16 main GGUF is recommended for LoRA merges.** Loading a LoRA onto a Q8/Q4 base merges into dequantized weights
  and requantizes the result — not equivalent to merging into the original BF16 model first. If quality matters more
  than the VRAM/speed savings of quantization, prefer `yue2.model_gguf=yue2-3b-bf16.gguf` when a LoRA is loaded.

## T4 `auto` picking eager attention is upstream's documented, intentional behavior — not an over-broad-range guess

- The earlier "why `auto` picks eager on a T4 (inference, not verified on hardware)" entry's speculation is now
  **resolved, not just corroborated.** `audio.cpp`'s own `docs/models/yue2.md` states outright: `yue2.attention=auto`
  "uses flash, except on Volta/Turing CUDA GPUs (missing MMA kernels) ... where it uses eager." This is official,
  documented, intentional behavior for that hardware class — not an accidentally over-broad `cc >= 700 && cc < 800`
  gate as speculated. **Forcing `--session-option yue2.attention=flash` on the T4 remains the correct override**; there
  is no longer any open question about whether it's "legitimate rather than a workaround" — it is legitimate,
  confirmed by upstream's own docs, and needs no further verification.

## `docs/models/yue2.md` is the source of truth for yue2 CLI flags — read it before re-deriving flags from source

- Full request/session/sampling option tables exist in the upstream doc (seed range `[0, 2^63)` default `1234`,
  `cot`/`abc`/`abc_file`/`guidance_scale`/`num_inference_steps`, the `semantic_*`/`abc_*` sampling knobs, and every
  `yue2.*` session option including weight-type and graph-arena sizing). Next session should **read this doc first**
  rather than re-deriving flag names/behavior from `audio.cpp` source reads or guesswork — it already matches and
  extends what earlier source-reading sessions found (e.g. the seed range and default agree exactly).
