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
