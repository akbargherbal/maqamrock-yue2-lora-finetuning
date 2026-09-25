# Decisions & insights

Major, durable decisions and non-obvious insights only — the things a fresh session must not re-litigate or rediscover. One short entry per decision. This is not a log: routine per-session state belongs in `agent_notes/current.md`.

Where a claim below says "verified against source," it means the actual `ostris/ai-toolkit` `.py` files were read on the date of this entry, not inferred from the README, a config example, or a GitHub issue thread. Ostris is under active development — re-check the cited file/line if behavior looks different than described here.

**Consolidated 2026-09-23** (frozen-doc exemption, user-approved): entries were admitted only if a fresh session would otherwise re-litigate or rediscover them. Pre-consolidation text: `git show 50c8de8:DECISIONS.md`. Line citations in other docs may have shifted; the live ones were re-pointed.

## Terminal/CLI over the Web UI, on purpose

- Use the CLI (`python run.py config.yaml -l …`), not the Web UI. CLI produces identical metrics — `use_ui_logger: true` is read by the trainer itself (`toolkit/logging_aitk.py`), not by the UI process. **CLI-only loses nothing on observability**; the only thing lost is the Web UI's own job list/dashboard (see the `aitk_db.db` entry).

## Metrics live in `loss_log.db`, not `aitk_db.db`

- `sqlite_db_path` (`aitk_db.db`) only ever gets one `Job` row (a status string), and only when the run was launched by the Web UI (`AITK_JOB_ID` env var). A CLI run leaves it untouched — expected, not a bug.
- The real metrics file is `<training_folder>/<job_name>/loss_log.db`, created whenever `use_ui_logger: true` (verified in `toolkit/logging_aitk.py`). WAL mode, safe to read while training writes. Use `monitor_loss.py`, not hand-written SQL.
- Schema: `steps(step, wall_time)`, `metric_keys(key, first_seen_step, last_seen_step)`, `metrics(step, key, value_real, value_text)`.
- Confirmed keys (first real run, 2026-09-19): `additional_model_loss`, `learning_rate`, `loss/ar_ce`, `loss/ar_kl`, `loss/loss`. There is **no** `nar_flow` key. Primary scalar: `loss/loss`.

## `process[].type: "diffusion_trainer"` is correct

- `"sd_trainer"` and `"diffusion_trainer"` are separately registered (`extensions_built_in/sd_trainer/__init__.py`); `DiffusionTrainer(SDTrainer)` only adds UI/API job hooks that no-op without `AITK_JOB_ID`. The config's `"diffusion_trainer"` is the correct superset; `verification.md`'s `'sd_trainer'` note is not a mismatch to fix.

## TensorBoard (`log_dir`) is real, but writes to a subfolder

- `log_dir` wraps every trainer (`jobs/process/BaseTrainProcess.py`), but `setup_tensorboard()` writes to `log_dir/<job_name>_<timestamp>/`, not `log_dir` itself — glob one level down.
- `log_config: {log_every: 1}` at the process root is a **dead key** (never read by `toolkit/config_modules.py`'s `LoggingConfig`); left in the YAML with a comment so it isn't mistaken for a missing feature.
- Redundant with `loss_log.db`; a nice-to-have second view, not the primary source.

## No GPU utilization/temp/power logging exists in AI Toolkit

- `performance_log_every` only triggers `self.timer.print()` (a wall-clock section breakdown), not hardware stats; no cuda/nvidia logging anywhere. `gpu_logger.py` (this repo) is the only source — confirm it is actually running before trusting an idle-GPU read.

## Asset downloads: standard HF Hub cache, not a bespoke tree

- `extensions_built_in/audio_models/yue2/yue2_model.py` + `src/tokenizer.py` resolve every asset via `hf_hub_download`, so they land in the standard HF cache (`~/.cache/huggingface/hub`). `bootstrap/setup.sh` only pre-warms that cache — no staged directory tree, no merge step, no path-mismatch risk.
- Repos/files actually used: `Comfy-Org/YuE2/checkpoints/yue2_3b_int8_convrot.safetensors`; `m-a-p/MERT-v2-FullSong`; `Mothersuperior/yue2-mothersuperior-realaudio-tokenizer-v4` (`tokenizer_head_joint_v4.pt`, and `nar_lora_joint_v4.pt` only if `merge_nar_lora`); `m-a-p/SheetSage2` (`Comfy-Org/YuE2/audio_encoders/sheetsage2_bf16.safetensors`, **only when `cot != "off"`**, so not pre-warmed here).

## Dataset verification

- 267 audio/caption pairs, all native `mp3, 48000 Hz, stereo` — exactly `YuE2AudioModel.sample_rate`. No resampling/format conversion needed. See `verification.md`.
- `prepare_yue2_dataset.py --convert-wav` hardcodes `-ar 44100` (a real bug); don't use that flag on this dataset.
- `cache_latents_to_disk: true` is mandatory — YuE2 raises "needs codec tokens in the latent cache" otherwise.

## Colab torch/CUDA/torchcodec stack: pin exact +cu130 versions

- An unpinned install resolved torch `2.11.0+cu128`, but `torchcodec==0.15.0` links CUDA 13 (`libnvrtc.so.13`) and torchaudio decodes through torchcodec — under cu128 `torchaudio.load()` fails on **every** dataset file, so latent caching never starts.
- Fix: pin `torch==2.13.0+cu130 torchvision==0.28.0+cu130 torchaudio==2.11.0+cu130`. Bare `==2.11.0` is **not** enough — PEP 440 treats it as matching `2.11.0+cu128` and pip keeps the stale torchaudio. Also relax `scipy==1.12.0` (no cp313 wheel; its failed source build aborts the whole requirements install) to `>=1.14`, and override `torchcodec==0.9.1` → `0.15.0`.
- `setup.sh` verifies `torch.version.cuda == "13.0"` plus a real `torchaudio.load()` of one dataset mp3, so a bad re-pin fails the bootstrap, not the first step.

## Rank, EMA, and `cot` — quality rationale

- **Rank 32, not higher.** All 267 captions are near-identical strings; a high-rank adapter on a narrow caption space spends capacity memorizing per-clip artifacts instead of the shared style. Lower is the safer direction if overfitting shows.
- **`ema_config.use_ema: true`, `ema_decay: 0.999`** — a run-to-run consistency lever, not a peak-quality one.
- **`model_kwargs.cot: "off"`.** Captions carry no melodic/ABC info, so `cot: "full"` would pull in SheetSage2 for no benefit at real compute/VRAM cost. Flip only if the goal changes to shaping melodic structure — and then also pre-warm SheetSage2 (asset entry above).
- **PS (2026-09-19):** style-only captions (the same premise) caused the lyrics gap — the AR trained 3000 steps with no lyric text, degrading pronunciation while style held. See the goal-correction and Lesson entries. `cot: "off"` itself is a separate question and unchanged.

## Backup: `loss_log.db` must not gate the settle wait

- `backup_to_gcp.py`'s `wait_for_settle` skips files still being written. `loss_log.db` (WAL) is always being touched during a run, so it and its `-wal`/`-shm` sidecars are excluded by name — otherwise every sync would starve. Checkpoints/`config.yaml`/samples are written atomically and remain safe to gate on.
- **PS (2026-09-24):** the TensorBoard event file (`tensorboard/<job>_<ts>/events.out.tfevents.*`, rewritten every step under `log_every: 1`) has the *same* perpetual-freshness property and was **not** excluded. Effect: `wait_for_settle` on the run's output folder never completed, so `output/` was never synced — the pron run's checkpoints stayed local-only and **no checkpoint reached GCS for ~1 h** (797 wait lines, zero output syncs) until noticed. Fix: `_settle_ignored()` now also skips any path under a `tensorboard/` dir or named `events.out.tfevents*` (they're still uploaded; they just don't gate the pass). When adding any new always-written file to a run folder, add it here too — and watch for "pass complete: 2/3" repeating with no `output` sync as the symptom.

## Goal correction: full-song structure — `train_window_frames` was the gap

- The goal moved from a style/timbre adapter to structurally coherent full songs. Under that goal the implicit `train_window_frames` default (1500 = 60 s @ 25 fps) was a real bug: `condition_noisy_latents()` cropped one 60 s window per step and computed both the NAR flow loss and the AR (`loss/ar_ce`) loss on it, so the AR expert never saw a verse-to-chorus transition in one gradient. No number of extra steps could fix that ceiling.
- Fix: `train_window_frames: 0` disables cropping (`condition_noisy_latents` no-ops when `window <= 0`). Safe for this dataset: AR context ceiling `24576 / 25 ≈ 983 s` vs longest clip 370 s (`verification.md`); the VAE's "60 s chunks" are an encode-time memory trick over independent chunks, not an architectural boundary.
- `content_or_style: "balanced"` was deliberately left unchanged (it weights noise timesteps in the flow loss — a different axis), changing one variable at a time; revisit as a separate lever.
- **PS:** the same goal-change audit missed the caption side (empty lyrics). See the Lesson entry.
- The old-window run was killed at ~29% (step 875/3000) rather than finished toward a stale goal.

## Lesson: a goal change invalidates every decision made under the old goal

- **What happened.** The goal moved from "style/timbre adapter" to "structurally coherent full songs that sing the provided lyrics". Only the config consequence (`train_window_frames`) was caught; the dataset consequence (style-only, lyric-free captions) survived because it was baked into a *build script's docstring*, not the config the audit was reading. Cost: a full 3000-step run trained toward the wrong target for the lyric-following half; bad pronunciation first sent the investigation to YAML knobs downstream of the real cause.
- **Rule 1 — on any goal change, list every artifact that encodes the old goal** and re-justify each against the new one: dataset captions (what's in them and what's missing), `cot`/`do_separation`/loss-weight flags, training-time `sample.samples` prompts, and the evaluation protocol. Config is only one of those places.
- **Rule 2 — record deliberate omissions as decisions.** "We left X out on purpose" has a premise; if it lives only in a code comment it outlives its premise silently.
- **Rule 3 — when a training input is empty by design, ask what the loss then cannot teach.** Empty lyrics meant the AR loss could never reward lyric-following, and the `ar_kl` anchor could never protect it.
- **Rule 4 — test the goal metric *during* training, not only after.** Every training-time sample had no lyrics, so checkpoints could show style but never pronunciation.
- **Rule 5 — when a result looks like a tradeoff, look for missing signal first.** It was missing data, not a weight balance.

## Relaunching under the same run name auto-resumes — it does not start fresh

- `get_latest_save_path()` (`jobs/process/BaseSDTrainProcess.py`) globs `save_root` for the newest `<name>*.safetensors`/`.pt`, and `load_training_state_from_metadata()` copies its embedded `training_info.step` into `start_step`; `optimizer.pt` loads too. A new/changed config pointed at a folder containing checkpoints silently resumes. `train.start_step` only overrides the counter — the old weights/optimizer still load.
- `backup_to_gcp.py`'s manifest only refuses *different* run names, so a same-name relaunch is allowed and would overwrite same-named checkpoints in GCS and append to `loss_log.db` — the two runs would be indistinguishable.
- To genuinely restart: archive the prior output (distinct run name, or move the local folder + `gsutil mv` the GCS prefix), then restart the backup daemon so it writes a fresh `run_manifest.json` (done 2026-09-19 for `akbar_arabic_rock_lora_crop60_killed`).
- The latent cache is **not** invalidated: `/content/yue2_dataset/_latent_cache` holds full-song latents; `train_window_frames` only crops at train time.

## Extending a finished run overwrites the final adapter — snapshot step 3000 first

- The end-of-run save (`BaseSDTrainProcess.py:2814`, `save()` with no step) writes `<run name>.safetensors` with no step suffix. Extending `akbar_arabic_rock_lora` past 3000 rewrites the v2 step-3000 artifact — the exact file the audio.cpp converter consumed. `max_step_saves_to_keep: 12` is already full, so each new save also deletes the oldest numbered checkpoint.
- GCS is **not** append-only for that file: numbered checkpoints are safe, but the un-suffixed final adapter is the same-name overwrite case above.
- `train.start_step` is not protection: it sets the counter only (unset, the counter comes from the newest checkpoint's metadata; set, that read is skipped) and never chooses which checkpoint loads.
- `network.pretrained_lora_path` is **not** a resume: it is consulted only when the save folder has no checkpoint, skips the metadata, and loads weights only — no optimizer state, no EMA, no step counter (unless `start_step` is also set). Untested.
- EMA (source-read, untested): checkpoints are EMA weights; `setup_ema()` rebuilds a fresh EMA after the optimizer loads and no EMA-state restore was found, so a resume continues from EMA'd weights and restarts the average.
- **Rule before any extension of v2:** (1) copy the final adapter outside the run's GCS prefix as `akbar_arabic_rock_lora_v2_step3000.safetensors` and record its sha256; (2) extend under a **new run name**, with the step-3000 checkpoint and `optimizer.pt` copied into that run's output folder, so the v2 folder stays untouched; (3) the user types the launch command (a changed step count is a changed config). Line numbers are from ai-toolkit `main` on 2026-09-21 and may drift.

## Whole-song on L4 vs A100 — measured

- `train_window_frames: 0` (whole-song) ran cleanly on both. **L4** (steps 1–295): ~**13.4 s/step**, 100% util, ~70.5/72 W, 12.9 GB mean / **15.8 GB peak** of 24 GB. **A100-SXM4-80GB** (resumed from step 250): median **3.10 s/step** (p10/p90 2.59/3.69 over 2730 steps) = **~4.3×**, sample pauses ~226 s vs ~388 s. Both reached 3000/3000, no OOM, no bounded-window fallback.
- The spec ceiling for L4→A100 is ~2–2.6× (BF16 tensor-core ratio 121→312; the run is not bandwidth-bound; A100's FP32 CUDA-core rate is *lower* than L4's). The measured ~4.3× beats it, so `docs/GPU_L4_VS_A100.md`'s estimate is directional only. Colab break-even is 4.35×, so the A100 still costs ~1.7–2.2× more units — it buys turnaround, not savings.
- Do **not** reuse the old 60 s-window run's ~7.8 s/step or ~6 h ETA; whole-song is ~1.7× slower per step.

## Cross-VM / cross-GPU resume (Colab session switch)

- Restore the GCS `output/` prefix into `/content/ai-toolkit/output/<run>/` on the new VM, then launch the identical command — the newest checkpoint auto-resumes. Runbooks: `docs/PAUSE_RESUME.md`, `docs/START.md`.
- Non-obvious: a run is portable only once a checkpoint exists **and** reached GCS (with `save_every: 250` the first resumable point is step 250). The latent cache is per-VM and not in GCS, so a fresh VM rebuilds it (~12 min) on first launch. Never run the same run name on two VMs at once (shared GCS prefix/`run_manifest.json`).
- Performance-only knobs (e.g. `gradient_checkpointing`) don't affect resume; changed hyperparameters/network/lr define a different experiment, not a resume.

## Dataset/config decisions are the user's; the agent flags, never blocks

- The v2 build diverged from `AGENTS.md`'s "Approved amendment" procedure (rebuilt from scratch offline instead of patching captions in place). The agent surfaced the divergence; the user chose to proceed. The safety invariants held anyway (audio untouched, shortlist unchanged, v1 preserved, no GPU/YAML touched during the build).

## Caption lyric format for v2 (binding on inference/sample prompts)

- The raw `///***///` line is removed.
- A bracketed tag whose content starts with a canonical section name (`Intro`, `Verse` [+ number], `Chorus`, `Pre-Chorus`, `Bridge`, `Outro`, `Hook`, `Refrain`) collapses to bare `[Section Name]`, dropping everything after the first `|`.
- Any other bracketed tag (arrangement/SFX asides like `[guitars surge — Ajam]`) is dropped and logged.
- Diacritics, the trailing `...` on lyric lines, and the Arabic wording are never touched.
- Binding on anything that builds inference/sample prompts — the held-out set and future eval tooling must use this format, not re-derive their own.
- Bug found in review: the whitelist first lacked `Refrain` (used as a chorus-equivalent), dropping real sung sections; fixed and rebuilt.

## Dataset naming convention: descriptive suffixes on archives, no numeric versions

- Decided (user): "v1, v2, v3 … are meaningless." The live dataset/run keeps its plain name; only a *superseded* artifact gets a suffix describing *why* it was superseded, not a number.
- Applied: `yue2_dataset` is always current — v1 moved to `yue2_dataset_v1_style_only_obsolete` / GCS `dataset_v1_style_only_obsolete/`, v2 occupies the plain names. Same pattern as `akbar_arabic_rock_lora_crop60_killed`.
- Consequence: no config path needed to change — the promotion is a storage-layer content swap (`bootstrap/setup.sh:104-115`'s `job_dataset()` rsyncs whatever `GCP_DATASET_PATH` points to).
- Keep archive folder names attached to a file; don't rename e.g. `akbar_arabic_rock_lora.safetensors` separately, it becomes ambiguous between datasets.

## Trigger word: v2's baked-in prefix does not double with `trigger_word`

- `inject_trigger_into_prompt` (`toolkit/prompt_utils.py:715-748`, via `get_caption` in `toolkit/dataloader_mixins.py:398-461`) prepends `trigger + " " + caption` only when the trigger appears **zero** times already. v2 captions start with a baked-in `arabmaqamrock ` — byte-equivalent, so no doubling; `trigger_word` stays in the YAML. v1 captions had no trigger (`verification.md:43`).
- `setup.sh:177` clones ai-toolkit unpinned (`main`); re-check if the caption-injection code is ever suspected to have changed.

## Run name: reuse `akbar_arabic_rock_lora`, no suffix

- Decided (user): archives get descriptive suffixes, live runs get no number; reuse means `name`, `log_dir`, and `backup_to_gcp.py`'s hardcoded `JOB_NAME` stay untouched, no code change.
- Reuse is bug-free only if all hold at launch: (1) `output/` is empty on the VM before launch (else auto-resume); (2) the GCS restore rsync is **not** run first; (3) after any smoke test, wipe the run folder if it wrote any `.safetensors` (only matters at step 250+).
- v1's finished run is archived as `akbar_arabic_rock_lora_v1_nolyrics_archived` (185 objects, verified).

## Held-out evaluation set: `evaluation_alharith.json` is not clean

- Checked line-by-line (diacritic-insensitive) against the 267 training captions: Hijaz shares 8/18 lines, Kurd 6/24, Nahawand 6/24 (same Mu'allaqa poem, overlapping workspaces); **Ajam is clean, 0/22**.
- Contamination is structural: the same poem section recurs across workspaces (267 captions = only 157 distinct cleaned texts). Held-out status can only be judged by actual lyric-line overlap against the full training set — never by title, workspace, or "not in the shortlist".
- Normalization (used everywhere in v2): delete diacritics (U+064B–U+065F, U+0670) and `.` and whitespace; map U+0671 → U+0627; a lyric line is any non-empty line not starting with `[` and not `///***///`.
- Replacement set built by the user's offline agent (self-contained spec, reused v2's build functions): one pick per maqam, that maqam's own text, `shared_lines == 0` vs all 267, 24–28 lines, Intro+Verse+Chorus+Outro, four workspaces, zero mutual overlap. Claude re-verified independently via the real `parse_caption`, correct maqam/trigger, character-identical lines, 0 shared lines. Files at `INFERENCE/yue2_eval_heldout/`.
- The Ajam pick shares 8 lines with `evaluation_alharith.json`'s own (clean) Ajam entry — directly comparable.
- Open (user's call): which set the post-run evaluation uses; whether to commit `prepare_yue2_dataset_v2.py` for reproducibility (it is not in the repo).

## `sample.duration: 360` — why, and its cost

- v1 samples were lyric-free at `duration: 120`, so no checkpoint sample could show pronunciation. Samples now carry real held-out lyrics and run at 360 so they can show a full intro→verse→chorus→outro arc.
- Cost: sample generation scales with generated length — one 4-prompt event at 120 s cost ~226 s on the A100 (`TRAINING_ANALYSIS/ANALYSIS.md:34`); 360 s roughly triples that, times 12 events over 3000 steps. Factor into any ETA.

## Agent training-control policy (explicit, don't re-litigate)

- The agent may **auto-resume an unchanged, already-approved run** after an unplanned interruption (same config, same run name, nothing changed) — to avoid burning a Colab session's availability waiting for a human.
- The agent may **not** start a new run, or resume with any changed config/hyperparameter, without the human typing the command. A run finishing without errors is not the same as a run being *right* (cf. FL-YuE2's `arabic_joint_v2`, which completed cleanly on scores that didn't capture the maqam).

## Token-count check — measured, no overflow

- Measured with the real BPE tokenizer (extracted from the checkpoint's `text_encoders.yue2_tokenizer_json` via `safetensors.safe_open`, then the `tokenizers` library; script `check_token_counts.py`, uncommitted). Reproduced the AR prefix (`src/tokenizer.py:43-51`, `cot="off"`): `[EOD] + encode(INSTRUCTION + "[Tags]" + style + "[Lyrics]" + lyrics) + [ABC_START, ABC_END, MUSIC_START]`, vs `CONTEXT = 24576` (`src/model.py:30`).
- 267 training captions: 780–1631 prefix tokens (mean 1214); the worst case, vs the dataset's 370 s max clip (`hijaz_short-poems_16082026_027`), leaves 13,690 tokens. 4 held-out prompts: 983–1237 (mean 1124); worst case vs `duration: 360` leaves 14,334. No caption near the ceiling — not a risk, don't re-check.

## v2 finished: the lyric fix worked as designed, and `ar_kl` drift replicated

- v2 (lyric-conditioned captions, otherwise identical to v1) ran 3000/3000; full numbers in `TRAINING_ANALYSIS/ANALYSIS.md`.
- `loss/ar_ce` ended ~0.35 below v1 (3.61 vs 3.97) — the mechanical consequence of the AR now receiving lyrics, **not** a quality claim; audio is judged by ear.
- **`loss/ar_kl` rose unbroken to the end in both runs** (v1 0.37→1.50, v2 0.39→**1.54**); `ar_kl_weight: 0.2` did not make it plateau. A reproduced two-run trend, not a v1 quirk — the first well-motivated lever for a v3 (fewer steps, lower LR, or lower `ar_kl_weight`), one variable at a time.
- Caveat: `ar_ce`/`ar_kl` are computed under different prompt conditioning between v1 and v2, so cross-run values are directional, not an A/B on audio quality.

## T4 VRAM is governed by the attention kernel — force `yue2.attention=flash`

- On compute capability 7.5, `yue2.attention=auto` selects the **eager** NAR attention (`src/framework/core/attention_fallback.cpp`: eager for CC 700–799). Controlled, LoRA-on, eager: cap 5800 → 14,033 MiB / 6000 → 14,577 MiB / **6200 → OOM**. With `--session-option yue2.attention=flash`: cap 6200 → **7,607 MiB** (exit 0) and cap 9000 → natural self-termination at **6,355 frames / 7,683 MiB** — about half the VRAM, and the OOM point passes.
- An earlier "≤5800-frame ceiling" claim was a guess and is **retracted** — do not cite it. The cause is the attention kernel, not the cap or the LoRA. The log reports only `allow_flash 0`/`1`, not the chosen kernel; the conclusion rests on the measured VRAM drop.
- Upstream's `docs/models/yue2.md` states `auto` "uses flash, except on Volta/Turing CUDA GPUs (missing MMA kernels)… where it uses eager" — documented and intentional. Forcing flash on a T4 is the correct override, not a workaround; an L4 (8.9) should need no override.
- VRAM figures: `nvidia-smi` reports 15,360 MiB, but the ggml runtime logs **14,912 MiB** total — use 14,912 for headroom. Colab High-RAM raises system RAM only.
- Length mechanics: output length is `semantic_max_tokens` (25 frames/s); `--duration-seconds` is ignored; the model self-terminates under an ample cap; the generic `--temperature/--top-p/--top-k/--repetition-penalty` flags are no-ops — use the prefixed `semantic_*`/`abc_*` options.
- **Listening (2026-09-21):** the full 4:14 Hijaz/seed-1000 flash render was judged good/acceptable; two isolated words were flagged (`له`→`يه`, `المسلوب`→`المسيوب`), reported to also occur "with the normal model" (baseline not pinned down). One track, one seed — not a verdict on the flash path.
- Still open: other maqams/seeds with flash, and lengths beyond 4:14.

## Inference tests run commands manually; the agent reports from files, not memory

- Changed 2026-09-21 (user's call) after an OOM post-mortem in which an agent prose summary asserted an unsupported "≤5800-frame ceiling" and misattributed a figure from a log later overwritten under the same filename.
- New workflow: the agent writes exact commands to `agent_notes/current.md` as a copy-paste block and **does not run them**; the user runs them in a separate terminal; the agent monitors by **reading** `out/*.log`, `_runs_status.log`, `_gpu.csv` and quotes lines rather than paraphrasing.
- Output filenames must carry every varying parameter (a cap-9000 log was once overwritten by a cap-6500 rerun under the same name).
- Writing this workflow into `AGENTS.md` remains a user's call.

## audio.cpp seeds and reproducibility: the sidecar policy

- `yue2.seed` is accepted in `[0, 2^63)`, default 1234, but both the AR sampler (`ar_runtime.cpp:683`) and the NAR noise (`nar_runtime.cpp:637`) seed with `std::mt19937 rng((uint32_t)seed)` — seeds differing by a multiple of 2^32 produce identical output. **Use seeds below 2^32.**
- Nothing is recorded by default (the settings line is emitted only under trace logging; no metadata sidecar found). **Policy: every generated track gets a JSON sidecar**, written by the wrapper around `scripts/run_one.sh` *before* generation, with seed; full command and request options; prompt-file sha256; sha256 of the main GGUF, the VAE and both LoRAs; checkpoint step; audio.cpp commit; GPU/compute-capability/attention mode; cap, final frame count, `truncated`, wall time, and the WAV's sha256. Filenames must carry every varying parameter.
- **Untested hypothesis:** the seed alone may not reproduce a track — a different GPU/attention kernel could shift floats, flip one sampled token, and diverge. Two cheap tests settle it: same seed twice on the T4 (bit-identical WAV?), then T4 vs L4. Until then, the sidecar's GPU/attention fields are what make a replication attempt honest, and the WAV is the only guaranteed copy.

## Batch verdict criteria must be fixed before generating, not after

- Placeholder was **TODO(user)**: define what counts as "3000 is enough" vs "needs more training" (e.g. a substitution rate on hard words, or maqam adherence) **before** a batch runs; different failures point to different levers (more steps, lower `ar_kl_weight`/LR, dataset changes).
- Hardware (user's figures, 2026-09-21 — recheck Colab pricing): T4 High-RAM (~1.27 CU/h) is the inference workhorse; L4 (~1.54 CU/h) optional; A100 (~6.77 CU/h) is for fine-tuning only, not inference.

## `audio.cpp`'s ~30 min build was `--model-set full` compiling all 80+ families

- `scripts/build_linux.sh` defaults to `--model-set full` — every model family, not just yue2. Fix, three first-party flags:
  ```
  scripts/build_linux.sh --backend cuda --cuda-arch 75 --ccache \
    --model-set custom --models yue2 --target audiocpp_cli
  ```
  `--model-set custom --models yue2` compiles only yue2; `--cuda-arch 75` targets the T4 instead of a portable multi-arch list; `--ccache` wires ccache (cold build ~unchanged, rebuild ~14× faster — persist the ccache directory, don't design a tarball cache).
- No Ubuntu+CUDA prebuilt exists (Releases cover Windows and Ubuntu CPU/Vulkan only), so a scoped build is genuinely required on Colab's T4.

## YuE2 LoRA loading is native in `audio.cpp`; the conversion requirement stands

- Session options load adapters directly (verified in `docs/models/yue2.md`): `yue2.ar_lora`/`yue2.ar_lora_scale`, `yue2.nar_lora`/`yue2.nar_lora_scale`; a new session is required to change adapters or scale; `0` disables one. No server/wrapper code needed.
- It requires **unfused** SafeTensors (not the `_comfyui` layout) — exactly what `converter/convert_aitoolkit_yue2_lora.py` produces. It splits each fused B by rows (A copied verbatim, byte-level); re-running it on the step-3000 `akbar_arabic_rock_lora.safetensors` reproduced both adapter files byte-identically (sha256 `747d5cfe…` / `ad2c8d86…`), both applied at scale 1.0. No new conversion tooling.
- `cot=off` matches this LoRA (trained `cot: "off"`), regardless of upstream docs recommending `cot=full` for a different adapter.
- **Use BF16 main GGUF when a LoRA is loaded** — merging into Q8/Q4 dequantizes and requantizes, not equivalent to merging into BF16 first.

## Merging two YuE2 LoRAs: rank-concat, and the converter wants one rank

- Neither ai-toolkit nor audio.cpp loads two adapters at once (`yue2.ar_lora`/`yue2.nar_lora`, one file + one scalar scale each). Combining v2 (AR+NAR) with the AR-only pron adapter is an **offline file merge**: `merge_pron_lora.py`, doc `docs/PRON_LORA_MERGE.md`.
- ai-toolkit's delta is `(alpha/rank) * (B @ A)` (`toolkit/network_mixins.py:419,434`; `toolkit/lora_special.py:115-116`; `toolkit/kohya_lora.py:237`; clone `460c29b`). Both inputs trained alpha==rank (v2 32/32, pron 8/8), so each saved file is exactly `B@A`. The user dial is folded into `B_pron` (the up-projection side the scale applies to). Method is rank concatenation (32+8→40); the dense delta is never materialized.
- **Non-obvious trap:** the converter enforces a *single* rank across both branches (`converter/convert_aitoolkit_yue2_lora.py:207-208`). So at alpha>0 the rank-32 NAR branch must be zero-padded to rank 40 or conversion fails with "mixed LoRA ranks found"; zero padding is a no-op on the delta. At alpha=0 the pron block is dropped, both branches stay rank 32, and no padding happens.
- **alpha=0 reproduces the live converted v2 adapters byte-for-byte** (`747d5cfe…` / `ad2c8d86…`) — but only when the merged input keeps v2's basename `akbar_arabic_rock_lora.safetensors`, because the converter stamps its **input filename** into the output `source_file` metadata. A different name yields identical tensors and headers but a different whole-file sha256.
- **Merged file sha256 is NOT reproducible — verify by tensor digest / converted hash instead.** `safetensors 0.8.0` serialises the `__metadata__` map in nondeterministic Rust-`HashMap` order, so two runs of the identical merge command emit different whole-file sha256 while *all 448 tensors and all parsed metadata are identical*. Verified 2026-09-25: two live `c3050_a0.5` runs were tensor-identical yet hashed `cf0d69b7…` vs `62e084a7…` (the Task-17 sweep's own run was `8a3dbdbd…`). Consequences: the `merged_sha256` fields in the sweep manifests are convenience records, not equality checks; verify a rebuild with (a) the **tensor digest** (sha256 over sorted `key‖dtype‖shape‖raw bytes`) or (b) the **converted AR/NAR sha256**, which *are* stable (the converter writes no volatile metadata and reproduces to the byte across environments — see below).
- **Production merges (2026-09-25):** v2 + pron ckpt **3050**, `alpha` 0.5 (primary) and 0.3 (fallback); records in `results/pron_production_merge/` (manifest + one sidecar per output + `regenerate.sh`; binaries in GCS `<base>/pron_production_merge/`). Converted AR hashes match the Task-17/Task-18 sweeps exactly (`33e824f2…` / `dd0d4959…`), confirming the same data through the same pipeline.

## `docs/models/yue2.md` is the source of truth for yue2 CLI flags

- It holds the full request/session/sampling option tables (seed range `[0, 2^63)` default 1234; `cot`/`abc`/`abc_file`/`guidance_scale`/`num_inference_steps`; the `semantic_*`/`abc_*` knobs; every `yue2.*` session option including weight type and graph-arena sizing). **Read it first**, not the source or guesswork — it already matches and extends earlier source reads.

## `audiocpp_gguf_test/` → `audiocpp_inference/`; the prebuilt-binary path is the main one

- Renamed 2026-09-22 (GCS 117 objects / 1.0 GiB; old prefix verified gone). The GGUF/audio.cpp CPU-build + prebuilt-binary path is now the adopted low-cost inference path in `bootstrap/setup.sh --inference`; a CUDA `audiocpp_cli` built once on a CPU runtime is persisted to GCS (+ per-arch binaries under `build/<arch>-<gpu>/`).
- **Staging rule:** the binary goes to `$AUDIOCPP_INFERENCE/bin/audiocpp_cli`, deliberately **not** under `/content/audio.cpp` — `job_audio_cpp` does `rm -rf` + re-clone, which would delete anything staged there. Apply this to any future inference artifact.
- Open: per-arch binary auto-selection is not designed (bootstrap pulls only the flat sm_75 object); the sm89-l4 binary has not been run on an L4.

## Handing over a command is part of the job — state its terminal semantics

- The user runs commands by hand in a real terminal; the agent's shell tool is a different session, so human-terminal facts (Ctrl+C, closing the tab, where a detached process logs) are invisible to the agent. On 2026-09-23 the agent handed over a ~2 h inference batch in the foreground — the user had to ask for `disown`. The fix is a standing rule, not a one-off command.
- Rule: before presenting any long-running, background/detached, or state-changing command, load `skills/command-handover/SKILL.md` and follow it — foreground vs detached, output log, stop command, resume command. Training stays foreground on purpose (see the auto-resume / `SIGINT` entries above). New gotchas append to `docs/COMMAND_HANDOVER_GOTCHAS.md`; that list is the accumulation, the skill is the procedure, and `AGENTS.md` carries the always-on trigger.
