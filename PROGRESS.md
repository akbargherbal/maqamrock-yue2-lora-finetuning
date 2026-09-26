# Progress

Durable, cross-session milestone record: what has actually been run, what it produced, and what's next. Append an entry when a run finishes or a phase changes; keep it short. Not a log — *why* things are the way they are lives in `DECISIONS.md`, and transient per-session detail lives in `agent_notes/current.md`.

## 2026-09-19 — Repo created, nothing trained yet

- Dataset built and independently verified: 267 audio/caption pairs, native `mp3, 48000 Hz, stereo`, no format mismatches against `ai-toolkit`'s YuE2 loader requirements. See `verification.md`.
- Config finalized (`config/akbar_arabic_rock_lora.yml`): rank 32, EMA on, `cot: off`, combined single LoRA across all four maqams, backup-aware (`max_step_saves_to_keep: 12`), Colab-ephemeral dataset path (`/content/yue2_dataset`).
- Observability plan settled: `loss_log.db` (via `monitor_loss.py`) as the primary metrics source, `-l` CLI log for tracebacks, `gpu_logger.py` for hardware stats — none of AI Toolkit's own logging surfaces cover GPU usage. See `DECISIONS.md`.
- Training-control policy set: agent may auto-resume an unchanged, already-approved run after a crash; anything new or changed needs the user to type the command.
- Bootstrap (`bootstrap/setup.sh`) written but **not yet run on a real VM** — next session should validate it end-to-end on a fresh Colab L4 before trusting the idempotent-skip logic.
- No training has been launched yet. Next: stand up a Colab L4, run `bootstrap/setup.sh`, confirm `loss_log.db` actually gets created and updates as expected, then launch the real run.

## 2026-09-19 — Bootstrap validated on a fresh Colab L4 (found + fixed two blockers)

- First real-VM `bootstrap/setup.sh` run failed the `ai_toolkit` job. Cause: two stale ai-toolkit pins on Colab's Python 3.13 — `scipy==1.12.0` (no cp313 wheel; its failed source build aborted the whole requirements install) and `torchcodec==0.9.1` (ABI-incompatible with torch 2.13). The bootstrap also installed bare torch -> `2.11.0+cu128`, while `torchcodec` 0.15 needs CUDA 13, so `torchaudio.load()` failed on every dataset mp3.
- Fixed in `bootstrap/setup.sh`: pin `torch/torchvision/torchaudio` to the exact `+cu130` local versions from ai-toolkit's README, relax `scipy`, override `torchcodec` to `0.15.0`, and add a verify step that asserts torch CUDA == 13.0 and decodes a real dataset mp3. Details in `DECISIONS.md`.
- Re-ran setup end-to-end: exit 0, all `[ok]`. Config parses via `toolkit.config.get_config` (`diffusion_trainer` / `yue2`), `run.py --help` exits 0, key deps import.
- Sidecars started by the agent: `backup_to_gcp.py` (first pass synced logs + agent_notes; output skipped until the run creates it) and `gpu_logger.py` (CSV writing). No run launched — awaiting the user's launch command.

## 2026-09-19 — Run launched, then killed at ~27% on a scope correction

- Training launched and ran to ~step 875/3000 (~29%), healthy throughout: clean loss descent, GPU at ~97% util with headroom, no crashes. See `TRAINING_ANALYSIS/` for the step-654 snapshot.
- Mid-run, the actual goal was clarified: full-song structural coherence, not a timbre/style-only adapter. That exposed `model_kwargs.train_window_frames` (left at its implicit 60s default) as a real gap, not a style choice — see `DECISIONS.md`. No amount of additional training under that setting would have produced song-structure learning.
- User's call: kill now (only ~27% / ~2h of Colab L4 sunk) and relaunch with `train_window_frames: 0` rather than finish a run that would be mediocre for the actual goal and require redoing the whole thing anyway.
- Config updated (`config/akbar_arabic_rock_lora.yml`): `train_window_frames: 0` added. **Not yet smoke-tested on real hardware** for VRAM/step-time — that's the next step before trusting the `steps: 3000` budget or its old ETA.
- Next: on the next Colab L4 session, run a short smoke test (a handful of steps, ideally including one of the longest ~370s clips) watching `gpu_logger.py`'s output before committing to a full run; recompute the ETA from real s/step; then launch for real.

## 2026-09-19 — Whole-song relaunch: old run archived (verified), README corrected

- Archived the killed 60s-window run so the relaunch genuinely starts at step 0 (a same-name relaunch otherwise auto-resumes from the latest checkpoint — see `DECISIONS.md`). Local: `output/akbar_arabic_rock_lora` → `output/akbar_arabic_rock_lora_crop60_killed`. GCS: `gsutil mv` of the matching prefix (58 objects / 487 MiB). Restarted the backup daemon so it writes a **fresh** `run_manifest.json` at the clean prefix; latent cache reused (no re-cache).
- **Supervisor verification — all three confirmed against live state:**
  1. **Local rename is real, not planned.** `_crop60_killed/` (mtime 09:59) holds the three old checkpoints + `optimizer.pt` + `loss_log.db` + `samples/` + `tensorboard/`. The `akbar_arabic_rock_lora/` that reappeared (10:07) is the **new** run: no checkpoints/`optimizer.pt`, `loss_log.db` at 0 steps, auto-saved config `train_window_frames: 0`.
  2. **GCS is clean.** `.../akbar_arabic_rock_lora/` contains only the fresh 608 B `run_manifest.json` (created 10:02:36) plus `agent_notes/` and `logs/`; no `output/`. All old data sits under `..._crop60_killed/output/`. (The archived manifest's internal `prefix` field still reads the old path — historical metadata, harmless.)
  3. **Backup daemon is the post-move one.** Exactly one, pid **155801**, started **10:02:34** — after the `gsutil mv` completed; no stale daemon. The second `pgrep` hit was the shell command matching its own pattern.
- Corrected the stale `README.md` (untouched by earlier commits): opening goal now full-song structure (was "style/timbre adapter"); Status updated from "Nothing has been trained yet" to the killed-run/archive/relaunch state; `train_window_frames: 0` added to the config summary; Observability example fixed from the non-existent `--key nar_flow` to `--key "loss/loss"` and the confirmed key list.
- Corrected the run-1 kill step to 875/3000 (~29%) in this file and `DECISIONS.md` (was noted as ~810/27%).
- Next: smoke-test the whole-song window's VRAM/step-time on the L4 before trusting the `steps: 3000` budget.

## 2026-09-19 — Whole-song run on L4, stopped at step 295; moving to A100

- The whole-song run (`train_window_frames: 0`) launched and ran healthily to **step 295/3000**: ~**13.4 s/step**, 100% GPU util, ~70.5 W of 72 W TDP, 15.8 GB peak VRAM. This resolves the config comment's "UNVERIFIED ON THIS HARDWARE" warning — whole-song fit on the L4, no bounded-window fallback needed. 3000 steps ≈ **~12 h** including ~1.2 h of sample overhead.
- Cost/time analysis (`docs/GPU_L4_VS_A100.md`): A100 is ~**2–2.6×** faster, not the ≥4× required for compute-unit break-even (`6.7 / 1.54 = 4.35×`). The user chose to switch anyway for turnaround; the offered Colab A100 is **SXM4-80GB**.
- **The L4 run was stopped deliberately at step 295** to move to a separate A100 Colab session. Resume begins at the **step-250** checkpoint (steps 251–295 lost, ~10 min).
- **Persisted + verified:** GCS `.../akbar_arabic_rock_lora/output/` holds `akbar_arabic_rock_lora_000000250.safetensors` + `optimizer.pt` + `loss_log.db` + `config.yaml` + `samples/` + `tensorboard/`; `.../agent_notes/current.md` is synced. GitHub clean. The L4 backup daemon and GPU logger are stopped.
- **Resume on the A100 Colab (fresh session):** clone the repo → `bash bootstrap/setup.sh` (wait for all `[ok]`) → `gsutil -m rsync -r` the GCS `output/` into `/content/ai-toolkit/output/akbar_arabic_rock_lora` → start the two sidecars → launch the identical command (user types it). Full runbooks: `docs/START.md` + `docs/PAUSE_RESUME.md`; session-specific handoff in `agent_notes/current.md` (gitignored — pull from GCS if absent). The fresh VM re-caches latents (~12 min) on first launch.
- Next: on A100, measure real s/step over the first ~20 steps, recompute the ETA, then run to 3000.

## 2026-09-19 — A100 resume completed the whole-song run (3000/3000) ✅

- Resumed on a Colab **A100-SXM4-80GB** from the step-250 checkpoint and ran to
  **step 3000/3000**. Clean finish, no traceback; final checkpoint + optimizer
  written, 52 samples generated. `run.py` exited, GPU freed.
- **~4.3× faster than the L4:** A100 median **3.10 s/step** (p10/p90 2.59 / 3.69,
  over 2730 steps) vs the L4's 13.4 s/step. Sample pauses ~226 s each (~42% of
  the L4's ~388 s). This resolved the 2–2.6× estimate in
  `docs/GPU_L4_VS_A100.md` (that estimate was peak-spec-derived, not measured).
- **Final loss** (first-50 → last-50): `loss/loss` 6.49 → 5.17, `loss/ar_ce`
  5.45 → 3.97, `additional_model_loss` 5.53 → 4.27. `loss/ar_kl` 0.37 → **1.50**
  — it never plateaued and drifted upward to its highest value; flagged as the
  metric to watch for any v2. Full write-up: `TRAINING_ANALYSIS/ANALYSIS.md`.
- **Persisted + verified:** 11 numbered checkpoints (`_000000250` … `_000002750`)
  **+ the final `akbar_arabic_rock_lora.safetensors`** + `optimizer.pt` +
  `loss_log.db` + 52 samples, all on disk and in GCS. Docs committed/pushed:
  `docs/LIVE_STATUS.md` (12:01 post-resume snapshot) and
  `TRAINING_ANALYSIS/` (`0f205a1`, `00f4534`).
- **Next:** evaluate the 52 samples by ear for arrangement-level coherence — the
  whole point of `train_window_frames: 0`, and not something loss can confirm.
  Pick the best artifact (final vs an earlier checkpoint if late steps overfit).
  A v2, if any, should change one variable (steps / LR / `ar_kl_weight`) given
  the unbroken `ar_kl` rise.

## 2026-09-19 — Listening evaluation + root cause: captions never carried lyrics

- **Listening (user, final checkpoint, the four `INFERENCE/evaluation_alharith.json` prompts):** style/timbre/arrangement fidelity is strong, but Arabic pronunciation degraded badly — place substitutions (ح→خ), spurious/dropped phonemes, whole-word substitutions, inconsistent errors on repeated lines. Errors increase with step count; earlier checkpoints have cleaner pronunciation but weaker style.
- **Root cause (verified against source + the build script, not inferred): the AR was never trained on real lyrics.** `prepare_yue2_dataset.py`'s docstring (lines 32–37) strips each track's `styles` to the reusable sound description and drops all lyrics on purpose; `verification.md:44` confirms the captions are style-only with empty lyrics. `do_separation` is off and `cot: "off"`, so no other path existed. For all 267 clips, every step, the AR's prompt prefix was "instruction + tags + lyrics" (`yue2_model.py:12`) with the lyrics slot empty — so `loss/ar_ce` rewarded matching real sung tokens from style alone and never rewarded getting the words right. The NAR flow loss is lyrics-independent, which is why style/timbre held while language-conditioned generation degraded; `ar_kl`'s 0.37→1.50 drift is the visible symptom.
- **This superseded the session's earlier framing** of an inherent style-vs-pronunciation tradeoff tunable via `ar_kl_weight`: style and pronunciation are different subsystems (NAR flow vs AR language-conditioning), and only one was being trained correctly. The missing ingredient was data, not a hyperparameter balance. It was a stale decision made under the old "pure style/timbre-transfer" goal (`cot: "off"` entry) that should have been revisited when the goal changed — see `DECISIONS.md`'s goal-correction and Lesson entries.
- **Fix plan (pending sign-off; dataset frozen):** confirm the raw manifest carries a real `lyrics` field; append lyrics in YuE2's native `[Lyrics]` format; delete the cached text embeddings (`_latent_cache` latents stay valid); sanity-check `parse_caption()` offline; smoke-test on the A100; leave loss weights untouched (one variable). The previously-listed v2 options (freeze the AR, raise `ar_kl_weight`, average checkpoints) were downgraded to fallbacks. (Implemented instead by the offline v2 rebuild — see the 2026-09-20 entry.)

## 2026-09-20 — v2 dataset built, verified, and promoted to canonical (local + GCS)

- Fix from the previous entry's "Fix plan" implemented, but via a different
  path than planned: the user built v2 offline with a separate agent that
  rebuilt the dataset from scratch from the raw `min_4stars_ai_music` tree,
  rather than patching the old `.txt` captions in place. This diverges from
  `AGENTS.md`'s "Approved amendment: lyric-conditioned captions" procedure
  (gated Colab-agent workflow, manifests pushed to the repo, append-only patch
  script). Claude flagged the divergence; the user chose to proceed — dataset
  decisions are the user's call. The freeze's safety invariants (audio
  untouched, shortlist unchanged, v1 preserved, no GPU/YAML touched during the
  build) held anyway. See `DECISIONS.md`.
- New standalone `prepare_yue2_dataset_v2.py` (local only, not in this repo);
  `prepare_yue2_dataset.py` untouched. Same shortlist/filename/style-caption
  logic as v1, trigger `arabmaqamrock ` (space, no comma), plus a new
  `\n[Lyrics]\n{cleaned_lyrics}` block. Caption lyric-format rules (Claude's
  call, delegated "as you see fit") in `DECISIONS.md`.
- One bug caught in review: the first build's section-tag whitelist lacked
  `Refrain`, dropping real sung sections as SFX noise in a handful of tracks.
  Fixed and rebuilt; verified `hijaz_tarafa_23072026_008_4cd0acdc` now has
  `[Refrain]` between `[Verse 3]` and `[Verse 4]`.
- Final verified numbers (`yue2_dataset_v2_report.md`, cross-checked): 267
  pairs (matches v1); 1967 manifest tracks scanned, 1700 skipped (not on
  disk); 0 empty lyrics; 157 distinct cleaned lyric texts across 267
  captions; dropped-tag log 70 occurrences / 34 distinct texts, all genuine
  SFX/instrumental asides.
- **Promoted to be "the" dataset**, local and GCS, so the config/eval that
  already point at the plain names need no path edits: local `./yue2_dataset`
  (v1) → `./yue2_dataset_v1_style_only_obsolete`, `./yue2_dataset_v2` →
  `./yue2_dataset`; GCS `dataset/` (v1) → `dataset_v1_style_only_obsolete/`,
  then v2 copied into `dataset/`. Verified: dry-run rsync 0 diffs post-push,
  `[Refrain]` present in the pushed caption, obsolete prefix's Ajam caption
  unchanged (`Symphonic...`, no `[Lyrics]`). GCS prefixes under
  `.../OSTRIS_Arabic_Suno_Finetuning/` are now: `akbar_arabic_rock_lora_crop60_killed/`,
  `akbar_arabic_rock_lora_v1_nolyrics_archived/` (v1's finished-run archive,
  185 objects), `dataset/` (v2, current), `dataset_v1_style_only_obsolete/`
  (v1). See `DECISIONS.md`.
- **Trigger word re-verified against upstream `ai-toolkit` source**
  (`toolkit/prompt_utils.py:715-748`): the prepend is `trigger + " " +
  caption` and only fires when the trigger appears zero times already. v2's
  baked-in `arabmaqamrock ` prefix is byte-equivalent, so `trigger_word`
  stays set in the YAML with no doubling. See `DECISIONS.md`.
- **Run name decided: reuse `akbar_arabic_rock_lora`**, no suffix — matches
  the repo's own precedent (archives get descriptive suffixes, live runs
  never get a number) and needs no change to `name`/`log_dir`/
  `backup_to_gcp.py`'s hardcoded `JOB_NAME`. Conditions for safe reuse (output
  folder empty before launch, GCS restore not run first, wipe any smoke-test
  `.safetensors` before the real run) recorded in `DECISIONS.md`.

## 2026-09-20 — Held-out evaluation set built; training-time samples switched to lyrics + `duration: 360`

- **Why:** every v1 training-time sample prompt had no lyrics, so no
  in-training checkpoint sample could ever show pronunciation (see the prior
  entry's Rule 4). Samples now need lyrics the model never trained on, so
  good pronunciation there can't be memory.
- **Finding: `INFERENCE/evaluation_alharith.json` is not clean held-out.**
  Distinct eval lines shared (diacritic-insensitive) with the 267 training
  captions: Hijaz 8/18, Kurd 6/24, Nahawand 6/24 (same source Mu'allaqa,
  overlapping workspaces); **Ajam 0/22 is clean**. The same poem section
  recurs across workspaces (157 distinct texts across 267 captions), so
  held-out status has to be judged by lyric-line overlap, not by title or
  shortlist membership. See `DECISIONS.md`.
- Built by the user's local offline agent from a self-contained spec
  (selection rules, definitions, checks — no repo references) that reused
  v2's own build functions. One track per maqam, that maqam's own text,
  `shared_lines == 0` vs. all 267 training captions, 24–28 lines, tags
  covering Intro+Verse+Chorus+Outro, four different workspaces, zero mutual
  overlap:

  | Maqam | Workspace | Lines |
  |---|---|---|
  | Hijaz | `New_Abu_Tammam_16082026` | 26 |
  | Kurd | `amin_almanoon_17082026` | 24 |
  | Nahawand | `ibn_zuraiq_20082026` | 26 |
  | Ajam | `alharith_bin_heliza_22082026` | 26 |

  The Ajam pick shares 8 lines with the eval file's own (already-clean) Ajam
  entry, so it's directly comparable to the existing full-length inference
  evaluation.
- Verified independently, not just from the agent's own report: each prompt
  parses through the toolkit's real `parse_caption`; correct maqam and
  `arabmaqamrock ` prefix; only allowed section tags, no `|`, no
  `///***///`; 0 shared normalized lines against every `yue2_dataset/*.txt`.
- **YAML updated and pushed** (`c38fb88`): `sample.samples` replaced with the
  four held-out prompts (one per maqam, its own text — not one shared excerpt
  across all four as originally planned); `sample.duration: 120 → 360`.
  Everything else left alone — see `DECISIONS.md`'s "Leave alone" list.
- **Held-out set pushed to the repo** at `INFERENCE/yue2_eval_heldout/`
  (`heldout_eval_prompts.json`, `heldout_samples_block.yml`,
  `heldout_eval_report.md`), next to the existing `evaluation_alharith.json`
  (`39a4a71`).
- **Not yet done:** final sanity-check pass over the full YAML; deciding
  whether the post-run evaluation uses the held-out set or
  `evaluation_alharith.json`'s clean Ajam entry; whether to commit
  `prepare_yue2_dataset_v2.py` for build reproducibility (open, user's call).
  **v2 training has not started.**

## 2026-09-20 — Pre-launch checklist closed out; ready for the smoke test

- `AGENTS.md` rewritten (1217 words, down from 2120) — base structure from
  `f9a9c03`, two missing Tier-A rules restored (no unilateral config edits;
  `agent_notes/current.md` reminder), the superseded "Approved amendment"
  section cut. See commit `ed6bca1`.
- Final YAML sanity check done: **no value changes**, 7 stale/wrong comments
  fixed (trigger-word framing, GCS sync interval, a dead script reference,
  the `steps` TODO framing, `content_or_style`'s "unconfirmed" note, the
  whole-song VRAM warning, the stale "style-only samples" note). Commit
  `83b1450`.
- `GCP_DATASET_PATH` confirmed from the launching notebook: exactly
  `gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/dataset`
  (the v2-content prefix) — the one item that could have silently trained on
  the wrong data. No action needed.
- **Token-count check done, real tokenizer, no overflow.** 267 training
  captions: 780–1631 prefix tokens (mean 1214), 13,690-token headroom on the
  tightest case against a 370s worst-case clip. 4 held-out prompts: 983–1237
  (mean 1124), 14,334-token headroom against `duration: 360`. Full method +
  numbers in `DECISIONS.md`.
- **Only the smoke test (before the real launch) remains.** Procedure, on
  the A100 Colab session, after `docs/START.md` steps 1–4 (repo cloned,
  `bootstrap/setup.sh` finished all `[ok]`, both sidecars running):
  1. Launch the real command from `docs/START.md` step 5, but stop it
     deliberately well short of step 250 (`save_every: 250` — nothing is
     saved before that, so nothing needs wiping if you stop earlier):
     ```bash
     cd /content/ai-toolkit
     python run.py /content/maqamrock-yue2-lora-finetuning/config/akbar_arabic_rock_lora.yml \
       -l /content/logs/train.log
     ```
  2. Watch `gpu_usage.csv` / step time in `train.log` for ~20–30 steps —
     confirm VRAM and s/step look sane (whole-song already measured clean
     on this exact config in the v1 run: ~15.8 GB peak, ~3.1 s/step on
     A100 — see `DECISIONS.md`). Then `Ctrl+C`.
  3. Check `output/akbar_arabic_rock_lora/` for any `.safetensors`. If the
     smoke test was stopped before step 250, there shouldn't be any.
  4. If any checkpoint *did* get written (smoke test ran past step 250),
     wipe just that run folder before the real launch — reusing the run
     name means `get_latest_save_path()` would otherwise silently
     auto-resume from it instead of starting fresh (see `DECISIONS.md`'s
     "Run name" entry, condition 3).
  5. Launch the real run — same command, same VM, same terminal.
- **Next:** run the smoke test above, then launch for real. User types both
  commands.

## 2026-09-20 — Smoke test passed; v2 run launched (in progress)

- **Smoke test passed** on the A100 with the unchanged v2 config: latent cache
  built ~3.5 min, step-0 sample event 9:43, stopped at step 57/3000 (no
  checkpoint written). Median **3.29 s/step**, VRAM peak ~17.6 GB (steady
  training ~14.8 GB). Output was archived to
  `...akbar_arabic_rock_lora_smoketest_archived` (13 objects) and the local run
  folder wiped, so the real launch started genuinely fresh. Latent cache kept.
- **v2 run launched** by the user (foreground, foreground-only so Ctrl+C works
  — a detached launch inherits SIGINT=ignored, see `agent_notes/current.md`).
  Sidecars `backup_to_gcp.py` + `gpu_logger.py` running throughout.
- **Live snapshot at step ~652/3000 (21.7%, 2026-09-20 08:26 UTC):** ~3.3 s/step,
  VRAM peak 16.4 GB, no errors. `loss/loss` first-50 6.23 → last-50 5.36;
  `ar_ce` 5.19 → 4.26; `ar_kl` 0.39 → 1.16. v2's `loss/loss`/`ar_ce` run below
  v1's at the same step (lyrics now condition the AR); `ar_kl` is the metric to
  watch (slightly above v1 same-step, still rising) — see
  `TRAINING_ANALYSIS/ANALYSIS.md`.
- v1's completed analysis moved to `TRAINING_ANALYSIS/v1_nolyrics_archived/` as
  the no-lyrics baseline; the top-level `TRAINING_ANALYSIS/ANALYSIS.md` now
  documents the live v2 run.
- **Next:** let it reach 3000, finalize the analysis, then listen to the
  held-out-lyric samples.

## 2026-09-20 — v2 run completed 3000/3000 ✅

- Finished **~12:23 UTC** at **step 3000/3000**, clean exit (no traceback,
  final adapter + optimizer written, 52 samples, GPU freed). ~4.73 h logged
  wall span incl. 13 sample events; **median 3.42 s/step**; VRAM peak 17.0 GB.
- **Final loss** (first-50 → last-50): `loss/loss` 6.23 → **4.79**,
  `loss/ar_ce` 5.19 → **3.61**, `additional_model_loss` 5.26 → **3.92**,
  `loss/ar_kl` 0.39 → **1.54**.
- **vs v1** (same config, lyric-free captions): v2 ends lower everywhere except
  `ar_kl` — `loss/loss` 4.79 vs 5.17, `ar_ce` 3.61 vs 3.97, `ar_kl` 1.54 vs
  1.50. The lower `ar_ce` is the mechanism of the caption fix (lyrics now
  condition the AR), **not** by itself proof of better audio; and `ar_kl` still
  never plateaued in either run. Full write-up: `TRAINING_ANALYSIS/ANALYSIS.md`.
- **Persisted + verified:** 11 numbered checkpoints (`_000000250` …
  `_000002750`) **+ the final `akbar_arabic_rock_lora.safetensors`** +
  `optimizer.pt` + `loss_log.db` + `config.yaml` + 52 samples, on disk and in
  GCS. Verified by a no-diff dry-run `rsync` (12 checkpoints, 52 samples remote
  == local). 4 stale smoke-test step-0 samples removed from GCS earlier.
- **Next:** evaluate the 52 samples by ear — the actual v2 goal is pronunciation/
  lyric fidelity in addition to arrangement coherence, neither of which loss can
  confirm. A v3, if any, changes one variable (steps / LR / `ar_kl_weight`) given
  the unbroken `ar_kl` rise.

## 2026-09-20 — First systematic listening pass on v2, step 3000, all four maqams

- **Method:** interviewer-style, word-by-word — one specific track + specific
  rare/hard target words per probe (from `heldout_eval_prompts.json`), not a
  general impression ask. Confirmed suffix→maqam mapping:
  `_0`=Hijaz, `_1`=Kurd, `_2`=Nahawand, `_3`=Ajam.
- **Result, step 3000, all four maqams:** no word substitutions, no dropped
  words, except one genuine phoneme substitution (**ح → خ**: "حُصُونٌ" heard
  as "خُصُونٌ", Ajam). Everything else flagged was performance-level (a rushed
  ر, a soft ع, a light/fast ق) or mix/mastering (vocal prominence tracking
  how quiet the instrumentation is at that moment), not mispronunciation —
  this is a materially better picture than v1's substitution-heavy result
  logged above. This is a first pass, not a full evaluation — see Next.
- **Enjambment resolved, not a v2/LoRA issue:** the model pauses at the end of
  each *written* lyric line even when the grammar spans into the next line
  (e.g. Kurd's "رابِئِ" / "الضُّرَباءِ", one grammatical iḍāfa split across
  two lines). Confirmed present identically in **step 0 (base, no LoRA)** —
  inherited from YuE2/Suno-style generation in general, not introduced or
  amplified by training. The usual mitigation is `...` at line end to mark
  continuation (already used in some captions, e.g. Nahawand's, where no
  phrasing issue was observed).
- **A suspected "weak ع" pattern (Kurd's "الأَكْرُعُ", Nahawand's
  "يُصَدِّعُ"/"يُصَدِّعُهُ") did not replicate in Ajam** ("أَرْعَنَ",
  "الْعَمَاءُ" both clear) — most likely occasional performance softness,
  not a systematic phoneme weakness. Not ruled fully out, just downgraded.
- **Hijaz-only drift check, step 2250 vs 3000, same lines:** no consistent
  directional regression despite `ar_kl` being higher at 3000 — some phonemes
  slightly better at 2250, others at 3000. Style/arrangement favors 3000. This
  check has not yet been repeated on Kurd/Nahawand/Ajam.
- **Next (explicitly deferred to next session for in-depth discussion):**
  decide whether/how to track the single ح→خ substitution across other
  tracks/checkpoints, whether to repeat the step-2250-vs-3000 drift check on
  the other three maqams, whether to sample early checkpoints (0/250/500) on
  non-Hijaz maqams, and ultimately the artifact pick (final vs. an earlier
  checkpoint) — no decision made yet on any of these.

## 2026-09-21 — audio.cpp YuE2 LoRA inference on a T4: OOM was eager attention, not the LoRA

- Ad-hoc inference (separate work area): `0xShug0/audio.cpp` @ `e3de8e3`, CUDA, the converted step-3000 LoRA, held-out prompts; harness in `/content/audiocpp_test/` (later `/content/audiocpp_inference/`). No training-side file was touched. The full mechanism now lives in `DECISIONS.md`'s attention-kernel entry.
- **Root cause: the attention kernel, not the LoRA or the cap.** Under `yue2.attention=auto` on CC 7.5 the NAR path selects eager attention; forcing `--session-option yue2.attention=flash` cut VRAM roughly in half and passed the OOM point (cap 6200 → 7,607 MiB; cap 9000 → self-terminated at 6,355 frames / 7,683 MiB). An earlier "≤5800-frame ceiling" claim was a guess and is **retracted**.
- Length mechanics, VRAM figures, the seed/sidecar policy, and the LoRA-conversion requirement are recorded in `DECISIONS.md`.
- **State:** artifacts were mirrored to GCS `audiocpp_gguf_test/` (later renamed `audiocpp_inference/`). Two caveats on the runs: a live backup daemon during the second run despite protocol (host-side only), and the GGUF precision not being echoed by the CLI's own log.
- **Next:** listen to the uncapped flash render against the PyTorch step-3000 sample on the same words; if quality holds, the other three maqams uncapped.

## 2026-09-22 — Bootstrap split into `--training` / `--inference`; notebook gains an inference cell

- **`bootstrap/setup.sh` now takes a mode flag** (default `--training`, so nothing
  existing breaks). Training is byte-for-byte unchanged: dataset + ai-toolkit/torch
  + training HF assets. New **`--inference`** skips the dataset download *and* the
  (slow) ai-toolkit/torch install entirely; instead it clones `0xShug0/audio.cpp`
  to `/content/audio.cpp` (**clone only — never built**, by the user's explicit
  call) and pre-warms `audio-cpp/Yue2-3B-GGUF` → `yue2-3b-bf16.gguf` +
  `yue2-vae-f16.gguf` into the standard HF cache. Both modes install opencode and
  do the HF login. `--help` prints usage; unknown flags exit 1. The mode-dependent
  verify block checks the dataset/ai-toolkit/asset stack for training, and the
  audio.cpp clone + GGUF assets for inference.
- **BF16 main GGUF, not the Q8 of the 2026-09-21 test runs**, per `DECISIONS.md`:
  BF16 is recommended when a LoRA is merged (Q8/Q4 merge into dequantized weights
  and requantize the result).
- **Notebook** `OSTRIS_ArabicSuno_vscode_anywhere.ipynb` (repo-external; the user's
  local launching copy) gained a final `## Inference setup (fresh VM)` markdown
  cell that mirrors the training cell and launches `setup.sh --inference`; the
  existing cell was labelled `## Training setup (fresh VM)`. Two separate copy-paste
  paths for the two purposes, as intended.
- **Docs synced:** `README.md` (repo-layout line + Colab section now say
  `--training`, with a one-line `--inference` description) and `docs/START.md`
  step 2.
- **Open question — the audio.cpp build may be simpler than the 2026-09-21 entry
  concluded.** That entry's guidance (manual `scripts/build_linux.sh --backend cuda
  --cuda-arch 75 --ccache --model-set custom --models yue2 --target audiocpp_cli`)
  is now suspect: the user's read is that **`build_linux.sh` may itself be buggy or
  redundant**, i.e. a plain cmake/build path might suffice and the earlier ~30 min
  build was self-inflicted by the script's `full` default. **Not re-tested yet.**
  The inference summary `setup.sh` prints still shows that command, now annotated
  in-place as the unverified best guess. Re-verify the real build path on the next
  inference VM before treating any of it as settled.
- **Next:** on a fresh inference VM, verify the actual audio.cpp build path (whether
  `build_linux.sh` is needed at all), then run the held-out prompts through
  `audiocpp_cli` with the converted step-3000 LoRA.

## 2026-09-22 — `setup.sh --inference` now installs `ccache` (the `--ccache` build flag hard-fails without it)

- Preflight on the inference VM (2026-09-22 05:42 UTC) found `ccache` not
  installed, while `setup.sh`'s own recommended next-step build command passes
  `--ccache` to `scripts/build_linux.sh`.
- Verified in `audio.cpp`'s `scripts/build_linux.sh:413-417`: `--ccache` is not
  a graceful no-op — if `command -v ccache` fails it prints
  `--ccache was passed but ccache is not installed` and `exit 1`. The
  recommended build would have died on its first action, before compiling
  anything.
- Fix: `bootstrap/setup.sh`'s `--inference` branch now runs
  `apt-get install -y ccache` (new `job_ccache`, dispatched alongside the other
  inference jobs) and its verify block checks `ccache --version`, failing the
  bootstrap if absent. `--training` untouched.
- Verified on this VM: installed `ccache 4.9.1-1`; `which ccache && ccache
  --version` → `/usr/bin/ccache`, `ccache version 4.9.1`.
- Whether `build_linux.sh` is even the right build tool (vs. a plain cmake path)
  is unchanged and still open — see the 2026-09-22 split entry and
  `DECISIONS.md`'s `--model-set full` entry. This entry only makes the
  documented flag combination runnable.

## 2026-09-22 — `setup.sh` timing instrumentation; `bfa8f29` staging fix smoke-tested (warm VM only)

- **Timing instrumentation** (`bootstrap/setup.sh`): `start_job` now stamps each
  job, the shared wait loop prints per-job elapsed next to `[ok]`/`[FAIL]`
  (`[ok]   hf_yue2_gguf (3s)`), both `done` banners carry total `$SECONDS`, and
  the same per-job + total lines are written to `/content/logs/timing.txt`
  (intentionally not synced to GCS). Applies to both modes via the shared
  `start_job`/wait loop; no job behavior changed.
- **`bfa8f29` smoke test — warm VM, NOT a fresh-VM proof.** Re-ran
  `setup.sh --inference` on this session's already-warm VM: exit 0, all jobs
  `[ok]` with durations (`opencode 1s`, `ccache 3s`, `audio_cpp 3s`,
  `hf_yue2_gguf 3s`, `hf_yue2_sidecars 3s`, `lora_adapters 3s`), banner
  `=== setup.sh done (inference) — total 7s ===`, and `timing.txt` matching
  exactly. Most jobs were cache hits on pre-staged assets, so this only proves
  the timing code runs and the jobs don't error — the from-clean-VM proof of
  `bfa8f29`'s staging (model dir + sidecars + LoRA) is deferred to next session,
  after a restart, on purpose.

## 2026-09-22 — NEXT SESSION AGENDA (fresh VM, after restart)

- **1. First task: the real clean-VM proof.** On a genuinely fresh `/content`
  (nothing pre-staged, nothing cached), run `bootstrap/setup.sh --inference` and
  confirm the verify block passes — model dir + all four sidecars + both LoRA
  files present, no `[FAIL]` lines. This is what actually proves `bfa8f29`'s
  staging works; every test so far ran on an already-warm VM. Also confirm
  `run_one.sh` resolves the build path, defaults to bf16, and includes
  `yue2.attention=flash` (`bfa8f29` + `4a7e4be`), with no manual override.
- **2. Capture the real cold timing number.** That same run is the first honest
  total from the `8289abe` instrumentation — the 7s seen so far was all cache
  hits and means nothing. Record actual per-job + total seconds from the console
  output and `/content/logs/timing.txt`, not from memory.
- **3. Only after 1–2 pass: resume the random-seed-batch plan.** Its sidecar
  metadata wrapper and same-seed-twice bit-identity test are still not started;
  do those before any batch generation. Batch verdict criteria remain
  `TODO(user)`, not an agent task.
- **4. Bring-your-own-lyrics + "4 songs per maqam" — the cold-start ask
  `docs/INFERENCE.md` can't yet answer.** Framed last session as: from a fresh
  context, hand the agent a bunch of new lyrics and ask it to "quickly make 4
  songs for each maqam using the GGUF + our LoRA". The runbook would have to be
  reverse-engineered rather than followed, for two reasons:
  - **(a) New lyrics aren't an input.** `INFERENCE/run_one.sh:22-23` hardcodes the
    prompt files to `/content/audiocpp_inference/prompts/<Maqam>_{style,lyrics}.txt`
    and takes only `<Maqam> <seed> [cap]` — there is no lyrics path argument, so
    "here are a bunch of lyrics" has no path in; you must overwrite the staged
    files, and nothing documents that. Also undocumented: the maqam→file mapping,
    that `style=` comes from a separate file from the lyrics, and that the LoRA is
    fixed (one Arabic-rock LoRA; "maqam" selects the style/lyric pair).
  - **(b) "4 each" needs a batch, and no driver exists.** 4 maqams × 4 songs = 16
    one-shot `run_one.sh` invocations; no loop/wrapper script and no documented
    seed convention (`_runs_status.log` implies batches were run ad hoc; the
    random-seed-batch plan above is still open).
  - **Deliverables, in order:** add a "bring your own lyrics" section and a batch
    section to `docs/INFERENCE.md` (drop path, mapping, seed convention, a
    documented `for`-loop or `run_batch.sh <seeds>` wrapper, and a ~16-run
    estimate). Doc-only first; a new `run_batch.sh` is code, so keep it a proposal
    until the user approves it. This is additive to item 1: it's about the doc
    being answerable from cold, independent of whether the clean-VM proof passes.

## 2026-09-22 — First T4 inference run: four held-out maqams generated; missing GNU `time` fixed in bootstrap

- **First GPU inference on this project** (T4, driver `580.82.07`, CUDA 13.0).
  `bootstrap/setup.sh --inference` ran all `[ok]` (7s) — but still on a **warm**
  VM, so this is **not** the clean-VM proof the 2026-09-22 agenda item 1 asks
  for; that remains open.
- **First `run_one.sh` invocation crashed exit 127 before the model loaded:**
  `INFERENCE/run_one.sh: line 44: /usr/bin/time: No such file or directory`.
  `run_one.sh` wraps every generation in `/usr/bin/time -v -o`, and Colab ships
  only the bash builtin `time`. Fixed `bootstrap/setup.sh`'s `job_ccache` to
  install `ccache time` (both are hard requirements of the build/run path, not
  optional speedups); verify block unchanged. Commit **`34322b7`**, `bash -n`
  clean, pushed. Worked around on this VM with `apt-get install -y time`, then
  re-ran the identical command.
- **All four staged maqams generated, seed 1, exit 0** (one at a time, via
  `INFERENCE/run_one.sh <Maqam> 1`; `duration_cap` auto):

  | Maqam | cap | exit | wav dur | wav size | wall |
  |---|---|---|---|---|---|
  | Ajam | 5750 | 0 | 230.0s | 44,159,788 | 7:02 |
  | Hijaz | 6500 | 0 | 231.2s | 44,390,188 | 7:26 |
  | Kurd | 5500 | 0 | 216.7s | 41,602,348 | 6:42 |
  | Nahawand | 6000 | 0 | 240.0s | 46,079,788 | 7:29 |

  All 48 kHz stereo. Artifacts under `/content/audiocpp_inference/out/`; full
  `_runs_status.log` and setup verify block in `agent_notes/current.md` (the one
  `exit=127` line there is the pre-fix Ajam attempt).
- **Not yet done:** the clean-VM proof + cold timing (agenda items 1–2), the
  random-seed-batch plan (item 3), and any listening pass on these four wavs.

## 2026-09-22 — `backup_to_gcp.py` gains `--inference`, so the audio.cpp workspace is auto-backed-up

- `backup_to_gcp.py` previously only had one hardcoded target set (training
  output + `/content/logs` + `agent_notes`); the inference workspace was being
  mirrored by hand, against `AGENTS.md`'s "fix the script, don't work around it".
- Added **`--inference`**, mirroring `bootstrap/setup.sh`'s own `--training`/
  `--inference` split: targets `INFERENCE_TARGETS` and defaults `--run-name` to
  `audiocpp_inference`. Mirrors `/content/audiocpp_inference/{out,prompts,scripts}`
  + `/content/converter/out` (the converted LoRA) + `logs/` + `agent_notes/` to
  `gs://<base>/audiocpp_inference/`. `models/` (multi-GB GGUFs) and `bin/`
  (prebuilt CLI) are deliberately excluded — regenerable via `setup.sh`.
- `--run-name` is now optional (defaults per mode). `ensure_manifest` now adopts
  a manifest whose recorded `prefix` disagrees with where it sits (the stale
  `audiocpp_gguf_test` manifest at the `audiocpp_inference/` prefix) instead of
  refusing; a manifest naming another run *while claiming this exact prefix*
  still refuses.
- Verified: `py_compile`; dry-run in both modes; a real
  `backup_to_gcp.py --inference --once` synced 6/6 folders and rewrote the
  manifest to `run_name: audiocpp_inference`; a follow-up dry-run copied nothing.
  `README.md` + `AGENTS.md` updated. Committed + pushed.
- **Still open:** the clean-VM proof + cold timing (agenda 1–2), random-seed
  batch (agenda 3), and any listening pass on the four seed-1 wavs.

## 2026-09-22 — Inference documented end-to-end; workspace renamed; L4 (sm_89) binary built and persisted

- **Workspace renamed `audiocpp_gguf_test` -> `audiocpp_inference`** (GCS via
  `gsutil -m mv -r`, 117 objects / 1.0 GiB, old prefix verified gone) and local
  `/content/audiocpp_test` -> `/content/audiocpp_inference`; `setup.sh` /
  `INFERENCE/run_one.sh` references updated (`53b8b2b`, `ffa4320`, `b3ec2ff`).
  `bootstrap/setup.sh --inference` gained `job_audiocpp_binary`, which stages the
  prebuilt binary to `/content/audiocpp_inference/bin/audiocpp_cli` — deliberately
  **outside** `/content/audio.cpp`, so `job_audio_cpp`'s `rm -rf` + re-clone can't
  delete it.
- **Two inference docs added** (indexed in `docs/README.md`):
  - `docs/audiocpp_gpu_arch_builds.md` — CPU-runtime CUDA cross-build methodology,
    the `--cuda-arch` compute-capability table (T4 75 / A100 80 / L4 89), SASS-vs-PTX
    behavior, per-arch GCS layout, verification checklist.
  - `docs/INFERENCE.md` — the end-to-end runbook: **asset provenance** (YuE2 GGUF
    comes from Hugging Face `audio-cpp/Yue2-3B-GGUF`, **not** GCS; LoRA/prompts/scripts
    and the prebuilt binary come from the GCS `audiocpp_inference/` prefix),
    fresh-VM setup, verification, and `INFERENCE/run_one.sh <Maqam> <seed>` usage.
- **L4 (sm_89) binary built from a CPU runtime** (no GPU attached):
  `scripts/build_linux.sh --backend cuda --cuda-arch 89 --ccache --model-set custom
  --models yue2 --target audiocpp_cli` — exit 0, `real 18m18.468s`, **352,411,648 B**;
  `cuobjdump` shows `.sm_89.cubin` + `.sm_89.ptx`. Persisted to
  `audiocpp_inference/build/sm89-l4/audiocpp_cli`. The flat
  `audiocpp_inference/build/audiocpp_cli` (**sm_75 / T4**, 350,161,824 B,
  `real 21m20.226s`) is untouched.
- **Correction recorded while writing the docs:** a bare `--cuda-arch N` does
  **not** produce a SASS-only binary. CMake treats a plain integer as both real and
  virtual — the generated `nvcc` flag is
  `--generate-code=arch=compute_N,code=[compute_N,sm_N]` (verified in the arch-75
  build's `flags.make`, and by `cuobjdump` listing **both** `sm_75.cubin` and
  `sm_75.ptx`). SASS is still locked to that compute capability; the embedded PTX may
  JIT forward but is untested, so per-GPU builds remain the rule.
- **Open:** per-arch binary auto-selection is not designed (bootstrap pulls only the
  flat sm_75 object); the sm89-l4 binary has not been run on an L4; `setup.sh`'s
  closing banner still prints the stale "cloned but NOT built" build instructions
  (predates `job_audiocpp_binary`); the clean-VM proof + cold timing (earlier agenda)
  also remain open.

## 2026-09-22 — First random-seed inference batch (16 tracks); repo audit; outputs partitioned per run

- **First real generation batch on the T4**: 4 maqams × 4 random seeds, alternating
  order (Hijaz→Kurd→Nahawand→Ajam ×4), run detached through a new resilient driver
  (`run_batch_random.sh`) that skips already-succeeded tracks and writes a per-track
  JSON sidecar (seed, prompt + LoRA sha256, GPU, exit, WAV sha256) **before**
  generation. **16/16 `exit=0`**, 13:37–15:21 UTC. Seeds kept for re-runs at
  `out/batch_20260922_seeds.tsv` (local + GCS). ~2 h wall.
- **Benchmark**: mean **389.6 s (6.49 min)/track** on a T4 (median 380.2 s), ~9
  tracks/hour; per-maqam means track the auto cap. In `docs/INFERENCE.md`.
- **Lyrics source unified.** The four `sample.samples` lyrics in
  `config/akbar_arabic_rock_lora.yml` are now canonical everywhere — copied to the
  audio.cpp prompts (local + GCS) and the repo held-out artifacts, with the held-out
  property re-verified (0 shared normalized lines). Commit `4ad9053`. Cause of the
  original gap: `7c14dc4` had corrected only the YAML, while audio.cpp reads the
  separate staged prompt files.
- **Bug found — the batch ran under-capped.** The staged `duration_cap.py` still
  used the old centre fit `92.0 + 0.280·N` while `run_one.sh`/docs specify the
  95th-percentile `111.1 + 0.3126·N`, so all 16 used low caps (6500/5500/6000/5750)
  and **5 self-terminated at the cap (`truncated 1`)**: `Ajam_140828086`,
  `Kurd_1389690935`, `Kurd_3975969445`, `Kurd_514634212`, `Nahawand_441956428`.
  Fix + re-run open (audit item 1).
- **Repo audit** `docs/IMPROVEMENTS.md` (`4527d3a`, extended by `6d65c99`): 21 ranked
  findings (stale docs, script drift, workflow gaps) + ARCHIVED / SUPERSEDED /
  RETRACTED banners on `verification.md`, `docs/investigation.md`,
  `docs/yue2-gguf-lora-findings.md`.
- **Outputs partitioned by run** (audit item 21, applied by hand): the 16 tracks
  moved to `audiocpp_inference/out/20260922-1337_random16/` (82 files); the ~91 old
  experiment renders (735 MiB) + a stray `out/out/` archived to
  `audiocpp_inference/out_archive/20260921_experiments/`. Flat `out/` now holds only
  per-run folders.
- **Supersedes agenda item 3** (random-seed batch): it ran; the sidecar wrapper now
  exists, though the same-seed-twice bit-identity test was not done. Clean-VM proof +
  cold timing (items 1–2) remain open.

## 2026-09-23 — NEXT SESSION AGENDA (Colab: background batch + docs consolidation)

- **Two workstreams in parallel** on the next Colab VM: a generation batch runs in
  the background (user launches per the manual-execution policy; the agent monitors
  from `out/*.log`, `_runs_status.log`, `_gpu.csv`), while the agent does docs work.
- **1. Docs consolidation (headline) — curate, never hack.** `DECISIONS.md` (~550
  lines) and `PROGRESS.md` (~710 lines) are accumulated narrative. `DECISIONS.md`'s
  own header — "One short entry per decision. This is not a log" — already prescribes
  the consolidated form, so this enforces the file's charter, not a new policy.
  Consolidate them:
  - `DECISIONS.md` → admission test per entry: would a fresh session otherwise
    **re-litigate or rediscover** something non-obvious — a verified source quirk, a
    costly trap, a surprising result? Keep those (intact, or conclusion + `<file:line>`
    pointer). Mundane/obvious rationale and process narrative go to git even when the
    decision was real; a decision is not automatically an insight. Git is the archive
    (no separate archive file); record the pre-debloat commit sha in the new header.
  - `PROGRESS.md` → light touch: one line per milestone where the narrative is
    repetitive; recent entries + this agenda kept intact.
  - The docs-reconciler treats both as **frozen** by default; this is a deliberate,
    user-approved one-time unfreeze (compress, never rewrite facts).
  - **Citation hazard:** live docs cite `DECISIONS.md` by line number
    (`docs/INFERENCE.md`, `docs/yue2-gguf-lora-findings.md`, …). Rewriting shifts
    every line — after the debloat, run the reconciler to catch broken citations.
- **2. Docs reconciliation.** Run `docs-reconciler` on the live docs; first batch is
  the 2026-09-23 findings: `prepare_yue2_dataset_v2.py` (README + heldout report),
  `ANALYSIS.md` in `docs/FINAL_BACKUP.md`, `docs/lora.md` in the pronunciation doc.
- **3. Unchanged open items** (do not lose): clean-VM proof + cold timing; re-run the
  5 truncated seeds at the corrected cap; per-arch binary auto-selection; duration-cap
  validation on `yue2_eval_heldout/`.

## 2026-09-23 — Second inference batch: 21/21 exit=0; docs consolidated and pushed

- `generate.py manifests/batch_songs_23092026.json` (deduped from a doubled 42-entry
  manifest to 21 songs, random seeds) → **21/21 exit=0**, 0 failed, total wall
  **2:54:45** (07:13–10:08 UTC), 21 WAVs / ~1004 MB in
  `out/20260923-071255_batch_songs_23092026/`. Per-track 6:05–10:30 (median ~8.3 min).
  Caps from the corrected 95th-percentile formula (6500–8250).
- **One track hit its cap:** `kurd_nabigha_jaadi_21082026_011_77c73eff` ran to exactly
  290.0 s at cap 7250 — flagged by the `generate.py` duration heuristic; the track log had
  no `truncated=1` line, so it is "possibly truncated", not confirmed. All others
  self-terminated under cap.
- **Docs:** `DECISIONS.md` (565→227 lines) and `PROGRESS.md` (740→582) consolidated under the
  user-approved frozen-doc exemption; `docs-reconciler` drift 4→0; added the `command-handover`
  skill. Commits `be54968`, `f52db59`, `4246b22` pushed to `origin/main`.
- **Next:** listen to the 21 tracks (quality / maqam / pronunciation, plus track 13's
  truncation). Still open: clean-VM proof + cold timing; re-run the 2026-09-22 batch's 5
  truncated seeds at the corrected cap; per-arch binary auto-selection.

## 2026-09-24 — Task 14b: AR-only pron LoRA smoke test PASSES on an L4

- `config/pron_lora_ar_only_smoke.yml` ran **10/10** steps cleanly on a Colab **L4**
  (user-typed, foreground), no OOM/crash. Saved adapter is AR-only and rank 8: **224**
  tensors, all under `text_encoders.*`, `diffusion_model.*` == 0, literal `transformer.*`
  == 0, all BF16, file 14,709,672 B (14.03 MiB). All losses finite (`ar_ce` 5.64→5.93,
  `ar_kl` 0.0011→0.0019). L4 numbers, warmup-inflated: ~1.0 s/step steady (first step
  5.29 s), peak VRAM 8,060 MiB of 23,034 MiB. Latent cache at
  `/content/pron_dataset/smoke/_latent_cache`. Verdict: **PASS**.
- **Preflight caught a notebook env bug:** the launching notebook exported
  `GCP_DATASET_PATH=.../pron_dataset` and omitted `GCP_PRON_DATASET_PATH`, so
  `job_dataset` pulled the pron set into `/content/yue2_dataset` and
  `/content/pron_dataset` was never created. Restored the pron set from GCS and corrected
  the notebook (both vars + `git checkout pron-lora-ar-only`). `setup.sh`'s two `[FAIL]`
  verify lines were false negatives (v2-layout glob on nested data); torch is fine. See
  `docs/PRON_LORA_VERIFICATION.md` A7.
- The real 6,100-step run is **not** launched here — separate A100 VM, user-typed.
  Full results: `docs/PRON_LORA_VERIFICATION.md`.

## 2026-09-24 — AR-only pronunciation LoRA (Task 14) prepared, not yet trained

- Added `config/pron_lora_ar_only.yml` (6,100 steps = 1 epoch) + `config/pron_lora_ar_only_smoke.yml`, `docs/PRON_LORA.md` (runbook), `docs/PRON_LORA_VERIFICATION.md` (A0–A6, source-cited), opt-in `job_pron_dataset()` in `bootstrap/setup.sh`, and run-name-aware `backup_to_gcp.py`; Task 13's set exposed at `/content/pron_dataset/{train,val,smoke}`. Runbook: `docs/PRON_LORA.md`.

## 2026-09-24 — Task 14c: AR-only pron LoRA real run completes 6100/6100 on A100 ✅

- `pron_lora_ar_only_r8` ran **6100/6100 steps (1 epoch)** on a Colab
  **A100-SXM4-80GB**, clean exit at ~07:27 UTC (final adapter + optimizer, no
  traceback/OOM). Final-adapter metadata `training_info = {"step": 6100, "epoch": 1}`.
- **Final loss** (step 6099): `loss/loss` 5.412, `loss/ar_ce` 4.163, `loss/ar_kl`
  1.531; last-50 means 5.815 / 4.397 / 1.533. `ar_ce` fell all run (6.13→4.40
  first→last 50); `ar_kl` rose monotonically (0.21→1.53, bounded, max 2.19) — same
  shape as v1/v2. Median **0.886 s/step**, 1.52 h logged. GPU peak 10.5 GB / 80 GB,
  util p50 22 % → **data/CPU-bound, not compute-bound** (A100 is overkill for this
  workload; L4 is fine). Full write-up: `TRAINING_ANALYSIS/pron_lora_ar_only_r8/ANALYSIS.md`.
- **Artifacts local + GCS** (9 objects / 73.27 MiB): checkpoints
  `000001525 / 000003050 / 000004575` + final no-step `pron_lora_ar_only_r8.safetensors`
  + `optimizer.pt` + `loss_log.db` + `config.yaml` + `tensorboard/`. **No
  `_000006100` numbered file** — the post-loop save *is* the step-6100 artifact
  (loop runs steps 0–6099); four trainable artifacts, not five.
- **Found and fixed a backup bug.** `backup_to_gcp.py`'s `wait_for_settle` did
  not exclude the TensorBoard `events.out.tfevents.*` file (rewritten every step),
  so the run's `output/` folder never settled and **no checkpoint reached GCS for
  ~1 h** while `logs/`/`agent_notes/` synced normally. Fix: `_settle_ignored()`
  now skips `tensorboard/` and `events.out.tfevents*`. Verified: forced passes put
  all artifacts in GCS; daemon restarted. Recorded in `DECISIONS.md`.
- **Handoff for the A100→L4 switch written:** `docs/L4_HANDOFF_TASK14C.md` (state,
  GCS paths, gotchas, next tasks). Run results also appended to
  `docs/PRON_LORA_VERIFICATION.md`.
- **Next (L4):** build + run the offline AR-loss replay over the 180 `val` pairs per
  checkpoint (`PRON_LORA_VERIFICATION.md` A3), then merge with the frozen v2 style
  LoRA. **No merge / inference / sweep done.**

## 2026-09-24 — Task 15: offline v2+pron merge tool; no-regression invariant PASSES

- Added `merge_pron_lora.py` (repo root), `tests/test_merge_pron_lora.py` (11 CPU
  tests), `docs/PRON_LORA_MERGE.md`. Method: rank concatenation on the AR branch
  (v2 rank 32 + pron rank 8 → 40), NAR copied from v2; the user `--alpha` dial is
  folded into `B_pron` per ai-toolkit's `(alpha/rank)·(B@A)` convention (quoted
  with file:line in the doc). No dense weight delta is materialized. Supports
  `--pron-checkpoint {1525,3050,4575,final}`.
- **alpha=0 invariant (no regression) — PASS.** Inputs pulled fresh from GCS and
  hashed (v2 `b1d09098…`, pron final `0d506719…`). Merged atomically to v2, then
  converted: the `_ar`/`_nar` outputs match the live converted v2 adapters
  byte-for-byte (sha256 `747d5cfe…` / `ad2c8d86…`) — exactly when the merged input
  keeps v2's basename (the converter stamps its input filename into metadata; a
  different name differs only there, all 392 tensors identical).
- **alpha=1.0 — PASS**: all 224 AR tensors rank 40 with expected shapes; NAR
  zero-padded to rank 40; `B@A == B_style@A_style + 1.0·B_pron@A_pron` on sampled
  keys; converter accepts. alpha=0.5/ckpt-4575 also runs end-to-end.
- **Finding:** the converter's single-rank guard (`convert_aitoolkit_yue2_lora.py:207`)
  forces the NAR zero-padding at alpha>0 — recorded in `DECISIONS.md`. Counts:
  224 AR tensors merged, 224 NAR passed through. Merge+convert ≈ **3.4 s** → an
  alpha sweep is cheap, no batching. Output dir `output/` is git-ignored.
- **Not done (next):** AR-loss replay over the 180 `val` pairs, the alpha sweep
  against held-out lyrics, and any audio.cpp inference. No GPU used here.

## 2026-09-24 — Task 16B: 720-pass AR-loss replay completes on L4; int8 kernel confirmed engaged

- **Preflight (fresh L4):** branch `pron-lora-ar-only` ✓; all three GCP vars exported ✓
  (incl. `GCP_PRON_DATASET_PATH` — the past VM bug did not recur); `val` 180 mp3 + 180 txt ✓;
  4 checkpoints pulled from GCS ✓. **Sidecars were not running** — agent started
  `backup_to_gcp.py --run-name pron_lora_ar_only_r8` + `gpu_logger.py`.
- **Kernel smoke (Step 1): PASS.** `--checkpoint final --limit 8 --device cuda` gave
  **0.61 s/item** AR-loss forward (0.23 s steady-state) vs the CPU baseline's
  **272.79 s/item** — ~450×, qualitative. The CPU W8A16-fallback warning is absent, so the
  W8A8 int8 `torch._int_mm` kernel ran on the L4 (cc 8.9). `ar_ce`/`ar_kl` match the CPU
  benchmark to 4 dp, confirming the same path. This is why the L4 is the right box for it.
- **Full sweep (Step 2): 4 checkpoints × 180 = 720 passes, ~23 min, zero errors**
  (detached, user-typed). Mean `ar_ce` / `ar_kl`:

  | ckpt | 1525 | 3050 | 4575 | final |
  |---|---|---|---|---|
  | `ar_ce` | 5.1157 | 4.6202 | 4.5053 | **4.4507** |
  | `ar_kl` | 0.7180 | 1.2715 | 1.4241 | **1.4828** |

  `ar_ce` falls and `ar_kl` rises monotonically (same unbroken-drift shape as training),
  with sharply diminishing `ar_ce` return after 3050.
- **Persisted:** raw JSON + log + summary committed under `results/` (`README.md` table);
  `docs/PRON_LORA_VERIFICATION.md` §A3b updated with these results and the **900→720 pass
  correction** (there were only 4 trainable checkpoints, not 5).
- **Next (not this task):** choose checkpoint + `alpha` from these numbers, merge with the
  frozen v2 style LoRA, run the alpha sweep against held-out lyrics, then the
  letter-substitution scorecard. No merge/inference done here.

## 2026-09-24 — Task 17: pron alpha sweep generated on L4 (20/20) + blinded review package

- **Grid:** 5 merged-LoRA configs (`a0`, `c3050_a0.5`, `c3050_a1.0`, `cfinal_a0.5`,
  `cfinal_a1.0`) × 4 held-out maqams, one seed (`20260924`), auto cap, **strictly
  sequential** (maqam-major). **20/20 exit 0, zero failures, zero cap-truncations**,
  ~58 min total (13:47–14:45 UTC) on a Colab **L4**.
- **Tooling:** `INFERENCE/run_one.sh` gained `LORA_AR`/`LORA_NAR` env overrides (defaults
  unchanged → prior behavior byte-identical); new `INFERENCE/pron_alpha_sweep.sh` driver
  (resumable: skips WAV + `Exit status: 0`; failures → `_failed.log`). Commit `d4c5592`.
- **Adapters (CPU):** all 5 built + converted; checks passed — `a0` AR `747d5cfe…` / NAR
  `ad2c8d86…` (v2 verbatim), the 5 AR hashes distinct, the 4 non-zero configs AR rank 40.
  `sweep_manifest.json` written before generation. Smokes (`a0`, `c3050_a1.0` at cap 750)
  passed first.
- **L4 benchmark:** mean wall **174.6 s**, median 199.2, min/max 71.2/257.9, total 3495 s,
  ~20.6 tracks/hour — vs the T4's 389.6 s (setup-specific: the merged adapters'
  renders self-terminate early more often). The **sm89-l4 binary ran on an L4 for the
  first time** here.
- **Blinded review package:** `results/pron_sweep/{sweep_manifest.json, README.md,
  KEY.json}` (committed); `/content/pron_sweep_listen.zip` (20 mp3 @192k, no
  trim/normalize, + `KEY_open_after_listening.txt`); WAVs + logs + manifests + zip in
  GCS `.../pron_alpha_sweep/` (107 objects). Blinding: single `random.Random(20260924)`,
  shuffle per maqam.
- **Docs:** new `docs/PRON_LORA_SWEEP.md` runbook; all four pron docs indexed in
  `docs/README.md`; `SOURCE_OF_TRUTH.md` created; reconciler 10→0. `docs/INFERENCE.md`
  gained the L4 benchmark and its sm89/"not run on an L4" stale line is fixed. Commit
  `ca2d2fa`.
- **Next (user's):** listen to the blinded package, pick checkpoint + `alpha`, then the
  merge at that setting and the letter-substitution scorecard. No quality verdict made.

## 2026-09-24 — Task 18: fine alpha sweep — ckpt 3050, alpha {0.2,0.3,0.55,0.65}, Hijaz + Kurd

- Fine round on Task 17: pron checkpoint **fixed at 3050**, alpha ∈ {0.2, 0.3, 0.55,
  0.65}, **Hijaz + Kurd only** — 8 tracks, alpha the only variable vs Task 17's existing
  `a0` / `c3050_a0.5` (reused, not regenerated). Held-out inputs reused byte-for-byte:
  **Hijaz** `New_Abu_Tammam_16082026` / `05-استجابة-النداء-وامعتصماه-وكرامة-الفرسان`
  (26 lines, auto cap **7250**); **Kurd** `amin_almanoon_17082026` /
  `04-مثل-الدهر-الأول-2-مكمن-القانص-ومصرع-الأتن` (24 lines, auto cap **6500**);
  generation **seed 20260924**; **pron ckpt 3050**; L4 + sm89 binary `97028a71…`; new
  blinding seed **20260925**. **8/8 exit 0**, no failures, no cap-truncations, mean
  **218.5 s/track** (~29 min).
- Blinded package `PRON_FINE_SWEEP_INPUT/` (`Hijaz_{A..D}.mp3`, `Kurd_{A..D}.mp3`,
  `KEY_open_after_listening.txt`); records `results/pron_fine_sweep/`; driver
  `INFERENCE/pron_fine_sweep.sh`. GCS `<base>/audiocpp_inference/pron_fine_sweep/`.
- **Next (user's):** listen blind, then decode. No quality verdict/winner made.

## 2026-09-25 — Task 19: production merges baked (v2 + pron ckpt 3050, alpha 0.5 primary / 0.3 fallback)

- **Merge-only, CPU.** No GPU present (`torch 2.11.0+cpu`, no `nvidia-smi`), no
  inference. Inputs pulled from GCS and hash-checked: v2 raw `b1d09098…`, pron 3050
  `ead30d52…` — both match `docs/PRON_LORA_MERGE.md` and the sweep manifests.
- **Built with `merge_pron_lora.py --pron-checkpoint 3050`** at `alpha` 0.5 and 0.3
  (rank 32+8→40, NAR zero-padded to 40), then converted with
  `convert_aitoolkit_yue2_lora.py`. Converted AR/NAR sha256 match the sweeps
  **exactly** (`c3050_a0.5` AR `33e824f2…`; `c3050_a0.3` AR `dd0d4959…`; both NAR
  `7d9324bf…`) — same data, same pipeline. Converter byte-level check passed.
- **New non-obvious finding (recorded in `DECISIONS.md`):** merged **file sha256 is
  not reproducible** — `safetensors 0.8.0` writes `__metadata__` in nondeterministic
  HashMap order, so re-running the identical merge yields different file bytes while
  all 448 tensors and parsed metadata are identical (two live `a0.5` runs:
  `cf0d69b7…` vs `62e084a7…`). Stable identities = **tensor digest** and
  **converted AR/NAR sha256**.
- **Persisted:** merged (140 MiB each, over GitHub's 100 MiB limit → not committed,
  matching `results/pron_sweep/`) + converted under `/content/pron_production_merge/`;
  GCS `<base>/pron_production_merge/`. Records committed: `results/pron_production_merge/`
  (`README.md`, `merge_manifest.json`, one sidecar per output, `regenerate.sh`).
  `regenerate.sh` re-run end-to-end into a scratch dir → **PASS**.
- **No quality verdict and no audio generated** — the listening blind on
  `PRON_FINE_SWEEP_INPUT/` is still the user's call; these are the merge artifacts
  ready for whichever ckpt/alpha the listen selects.

## 2026-09-25 — Task 20: request-option knob probe (c3050_a0.5) + generic A/B blind-eval tool

- **Round 5 knob probe.** With pron checkpoint **3050** and `alpha` **0.5** fixed, exactly
  one `audiocpp_cli` request option varied per config — `g1.0`/`g1.5`
  (`guidance_scale`; anchor default **1.01** for `cot=off`), `t0.8`
  (`semantic_temperature` 0.8), `rp1.4` (`semantic_repetition_penalty` 1.4) — x Hijaz +
  Kurd = **8 tracks**, strictly sequential. Anchor = the fine sweep's existing
  `c3050_a0.5` renders (same seed `20260924`, auto cap, prompts, sm89 binary `97028a71…`),
  reused not regenerated. **8/8 exit=0, zero truncations**, mean wall **211.8 s**, total
  **1694 s (28.2 min)** on an L4.
- **Tooling:** `INFERENCE/run_one.sh` gained the additive `EXTRA_REQUEST_OPTS` env hook
  (space-separated `key=value` -> extra `--request-option`; unset = unchanged), documented
  in `docs/INFERENCE.md`. New `INFERENCE/pron_knob_probe.sh` (fine-sweep resumable/skip
  contract + full per-track sidecar, now incl. a `resources` block).
- **Resource tracking confirmed + committed:** per-track `/usr/bin/time -v` (`*_time.txt`:
  RAM/RSS, CPU%) and 1 Hz `nvidia-smi` (`*_gpu.csv`: util/mem/power/temp), plus the global
  `gpu_logger.py` CSV. Recorded per sidecar + a README table: RAM **6.7–7.8 GiB**, peak VRAM
  **9.9–10.8 GiB** (mean 5.5–6.3 GiB), 100 % util, 80 °C, 74.7–81.6 W.
- **Records + blinded package:** `results/pron_knob_probe/` (`README.md`, `KEY.json`,
  `sweep_manifest.json`, per-track `sidecars/`), `PRON_KNOB_PROBE_INPUT/` (8 mp3 @192k,
  no trim/normalize + listener key). New blinding seed `20260928`. No quality verdict — the
  user's listen decides.
- **Generic A/B blind-eval tool (commit `b46a0b0`):** root-level scratch
  `prepare_ab_eval.py` adapted and moved to `INFERENCE/prepare_ab_eval.py` — generic over
  variants (A/B/…), public `EVAL.txt` split from secret `KEYS.txt`, per-category consistent
  labels, copy/wav/mp3, `--json`, `--dry-run`. Added CPU tests, `docs/AB_BLIND_EVAL.md`, and
  the `ab-blind-eval` skill (+ symlink).

## 2026-09-25 — Backup gap fixed: two lost Kurd WAVs re-rendered on T4 (arch divergence confirmed)

- **Gap found:** Round 5's `pron_knob_probe` reached GitHub intact, but the GCS mirror
  `.../pron_knob_probe/` was missing 6 objects — both Kurd lossless WAVs: `t0.8/Kurd.wav`
  (its `_time.txt` written 0 B) and all of `rp1.4/Kurd.{wav,json,log,_gpu.csv,_time.txt}`.
  Cause: the 15-min backup daemon's last pass was ~15:12:26Z and the VM ended before the
  next (~15:27), *after* `t0.8/Kurd` finished (15:12:57) and `rp1.4/Kurd` ran
  (15:13:20–15:17:15). `pron_knob_probe` **was** a daemon target — cadence + VM death, not
  a coverage bug. `/content` is ephemeral, so the originals were gone.
- **Fix:** re-rendered the two tracks on the only GPU available (Tesla **T4 / sm_75**, binary
  `7ad69d1c…`) with byte-identical inputs (seed `20260924`, cap `6500`, `c3050_a0.5`, Kurd
  prompts, BF16 GGUF). Both `exit=0`, no cap-truncation.
- **Result — cross-arch reproduction does NOT hold** (settles the `DECISIONS.md` hypothesis):
  `t0.8/Kurd` `d783a3bb…` (192.92 s) → `37c252c2…` (204.92 s); `rp1.4/Kurd` `01e903ed…`
  (215.80 s) → `ddae993e…` (187.44 s). The committed L4 MP3s remain the canonical copies.
- **Mirrored** to GCS `.../pron_knob_probe/t4_regen/` (a **separate prefix**, so the
  surviving original L4 `t0.8/Kurd` companions are not overwritten). Sidecars with a
  `regen` block committed at `results/pron_knob_probe/sidecars_t4_regen/`; write-up
  `results/pron_knob_probe/T4_REGEN.md`.
- **Tooling fix:** `INFERENCE/pron_knob_probe.sh` used `re.match` in its sidecar writer
  without `import re`, so *every* run's completion sidecar silently failed (only
  `status: started` was written). Added `import re`, plus `MAQAMS`/`CFGS` env overrides so a
  partial regeneration can target only the missing tracks.

## 2026-09-26 — LoRA inventory: current adapters consolidated into `<base>/loras/`

- Created the canonical LoRA library and moved the current deployable set in:
  style pair → `loras/audio_cpp/style/`; production merges `c3050_a0.5/a0.4/a0.3` →
  `loras/audio_cpp/pron/<cfg>/`; pinned source fused finals → `loras/source/`.
  **10 objects / 758 MiB.** `c3050_a0.4` confirmed **current** (ships alongside 0.5/0.3).
- Duplicates folded in were verified byte-identical by GCS md5 before removal; the
  redundant copies in `audiocpp_inference/converter/` were deleted and
  `pron_production_merge/converted/` is gone (its `merged/` intermediates remain).
- Rewired references: `bootstrap/setup.sh` (`LORA_GCS` → `loras/audio_cpp/style`, plus the
  converter tool staged separately); `backup_to_gcp.py --inference` (removed the
  `converter/` mirror target); `docs/INFERENCE.md`, `docs/PRON_LORA_MERGE.md`,
  `results/pron_production_merge/README.md`, `docs/BACKUP_RESTORE.md`.
- New `docs/LORA_INVENTORY.md` (what exists / how many / where) + rows in
  `SOURCE_OF_TRUTH.md` and `docs/README.md`. Decision recorded in `DECISIONS.md`.
- **Found (project-dir scan):** the v1 archive `akbar_arabic_rock_lora_v1_nolyrics_archived/`
  — and `akbar_arabic_rock_lora_crop60_killed/` and `dataset_v1_style_only_obsolete/` —
  are documented in this file as verified GCS archives but are **absent** from the project
  prefix. No surviving v1 adapter.
- CPU-only; `pytest` green (exit 0), `bash -n` + `py_compile` clean. Committed and
  pushed to `origin/pron-lora-ar-only` as **`cf0c4b3`**.
- Moved the four blinded listening packages (`PRON_CKPT_SWEEP_INPUT`, `PRON_FINE_SWEEP_INPUT`,
  `PRON_KNOB_PROBE_INPUT`, `MAQAM_LYRIC_SWAP_INPUT`; 122 MB) out of the repo: mirrored to
  GCS `<base>/listening/` and untracked (`.gitignore` `*_INPUT/`). Docs referencing
  "repo root" packages updated; decision in `DECISIONS.md`.
- Added two library adapters, `c3050_a0.1` (new, AR `184bbd29…`) and `c3050_a0.2`
  (AR `c68217ab…`, reproduces the pre-existing experiment byte-for-byte), merged at pron
  ckpt 3050 from the pinned `loras/source/` inputs and placed under
  `<base>/loras/audio_cpp/pron/`. The duplicate experiment converted copy of a0.2 was
  removed; `docs/LORA_INVENTORY.md` updated. Neither is listened to yet.
- **Hedged the labels and capped α at 0.5.** Dropped "primary / current / production /
  best-so-far" wording from the live docs — no α/checkpoint is selected until the blinded
  listening decides; candidates are described by their parameters and marked unlistened.
  Archived every α>0.5 artifact (`c3050_a0.55`, `c3050_a0.65`, `c3050_a1.0`, `cfinal_a1.0`:
  converted pairs, fused merges, renders — 15 dirs) to `<base>/archive/alpha_gt_0.5/`.
  Decision in `DECISIONS.md`.
- **Completed the α grid in the library** (`{3050, 4575, 6100(final)}` × α `{0.1…0.5}` =
  15 configs, 30 files). Built the 10 missing ones (4575 & final) from the pinned
  `loras/source/` inputs; overlaps reproduced the old records exactly (`c4575_a0.5`
  `ebd22026…`, `cfinal_a0.5` `525d3af2…`). Pinned the 4575/final fused checkpoints into
  `loras/source/`; removed the duplicate `c4575_a0.5` experiment copy. Library now
  **16 adapters / 36 objects / 2.72 GiB**; `docs/LORA_INVENTORY.md` updated.

## 2026-09-26 — NEXT SESSION AGENDA (project chores)

- **graphify update** (`graphify update .`) after this session's edits, before any merge.
- **Docs reconciliation** (`docs-reconciler`) — this session added the standalone
  `vm-continuity` repo and touched `AGENTS.md`, `DECISIONS.md`, `bootstrap/setup.sh`; check
  live docs for drift (skill lists, backup docs, setup references).
- **Other setup chores** — the user's list (TBD).
- Parked, **idle-time only** (never GPU-paid): vm-continuity Milestone 1 (per-session
  layout). See `agent_notes/current.md` and `DECISIONS.md`'s continuity-priority entry.

## 2026-09-26 — Cold-VM restore proof: vm-continuity recovered the lost session (worked)

- Colab dropped mid-discussion; a fresh VM came up with the repo but empty `/content/logs`
  and `agent_notes/` and no vm-continuity. First real end-to-end cold-VM test of
  `vm-continuity` — **it recovered the interrupted session**
  `ses_f235771d7ffelzQ283jqWnMj7h` ("Updating graph for current directory", the docs-Q&A
  discussion) from the lost VM's namespace `by_host/908cec5499a9/` (captured 08:29:45,
  6 sessions), with all 42 messages intact.
- Both restore paths verified: export-mode imported 6/6 sessions into this project
  (`opencode session list` shows them; the target has 42 `session_message` rows), and the
  whole-DB fallback restored to an alternate `--db-path` reproduced all 6 sessions without
  touching the live service.
- **Found a tooling bug:** the documented `restore opencode -- --mode db|export` is broken
  (argparse rejects `--mode`). Working forms in `DECISIONS.md`.
- Started this VM's capture loop (`by_host/c238efce27da/`, 7/7 sessions) so this session is
  protected. Caveat: `/content` files (e.g. `B_questions.md`) are **not** covered by
  vm-continuity — only OpenCode sessions are.

## 2026-09-26 — `AGENTS.md` rewritten as a lean charter; `train_ctl.py` run-control; troubleshooting checklist

- Rewrote the agent contract (`AGENTS.md`): lean charter that **points** to the canonical
  docs instead of duplicating them; fixed two dead paths (`training_folder/…` →
  `/content/ai-toolkit/output/akbar_arabic_rock_lora/`; an un-runnable stack command) and the
  missing-`/content/logs` restore bug; reframed `agent_notes/current.md` as a **copy/paste
  surface, not documentation**; readiness is now **mode-dependent** (per-mode runbook).
- **Run-control change: training is detached, not foreground**, so an accidental Ctrl+C (the
  Linux copy-paste habit) can't kill it. An independent review (`AGENTS_REVIEW.md`) caught that
  the first fix (`trap - INT`) was wrong — a non-interactive shell can't un-ignore an inherited
  `SIGINT=SIG_IGN`. Replaced with **`train_ctl.py`** (`start`/`status`/`stop`): spawns via
  `Popen(start_new_session=True)` + a SIGINT reset, writes a pid/state file, refuses a
  double-run, and verifies the PID before signalling. Verified on-VM (own session; clean SIGINT
  stop in ~1 s) and with GPU-free tests (`tests/test_train_ctl.py`; full suite 161 passed, 1 skipped).
- Ripple landed atomically: `docs/START.md`, `docs/PAUSE_RESUME.md`,
  `docs/COMMAND_HANDOVER_GOTCHAS.md` (+ the `trap - INT` finding), `skills/command-handover`,
  `skills/crash-diagnose-and-resume` (auto-resume bar → "evidence, else ask"), `DECISIONS.md`
  (run-control entry), `docs/PRON_LORA.md`, `docs/FINAL_BACKUP.md`.
- Added **`docs/EXPERIENCE_CHECKLIST.md`** — a user-POV instrument (10 experience
  scores + a friction/pitfalls checklist + a hand-off block) for evaluating how it
  *felt* to work with the agent, not only whether it worked. Indexed in
  `docs/README.md`. (A more technical `docs/TROUBLESHOOTING.md` was added and then
  removed at the user's call.)

