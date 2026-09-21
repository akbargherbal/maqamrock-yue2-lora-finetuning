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

## 2026-09-19 — Listening evaluation + root cause: captions never carried lyrics, not an inherent style/pronunciation tradeoff

- **Listening evaluation** (user, final checkpoint against the four
  `INFERENCE/evaluation_alharith.json` prompts, one per maqam): style/timbre/
  arrangement fidelity to the training data is strong — clear adaptation to
  the target sound. The base model's Arabic pronunciation was already good
  pre-LoRA; the final checkpoint shows articulation degrading substantially:
  - Place-of-articulation substitutions, pharyngeal ح → velar/uvular خ (e.g.
    آذنتنا → آذتنا/آذتتنا; الناطق المرقش → الناطك المركي; حدثتموه → خدثتموه).
  - Spurious/dropped phonemes (e.g. إخواننا → أهخواننا, extra ه inserted).
  - Whole-word substitution errors (e.g. ضوضاء → ضواء).
  - Localized word-level garbling (e.g. عِنْدَ عَمْرٍ → عندرن) and cross-word
    boundary blending.
  - Inconsistent errors on repeated lines — the same word mispronounced
    differently each time it recurs.
  - **Overall impression:** melisma and maqam coloring land as intended, but
    delivery reads as a non-native approximation of Arabic (user's read: "like
    a Jewish or Turkish singer"). Errors increase with step count — earlier
    checkpoints have cleaner pronunciation but weaker style match to the
    training data. Pronunciation was not a known weak point of the base model
    going in.

- **Root cause — verified against source, and against the dataset build
  script, not inferred: the AR was never trained on real lyrics at all.**
  `prepare_yue2_dataset.py`'s own docstring (lines 32–37) says it outright —
  each manifest track's `styles` field is stripped down to the reusable sound
  description (genre/vocals/production/instrumentation/mood); the Suno
  control headers and **all lyrics are dropped, on purpose**: *"a style LoRA
  should learn the sound, not memorize which poem starts with which line.
  `lyrics` is never used."* `verification.md` (line 44) independently confirms
  the result: *"Captions are style-only (no `[Lyrics]` section), so YuE2's
  `parse_caption` treats the whole string as tags/`style` with empty lyrics —
  intended."* `do_separation` is off and `cot` is `"off"` too, so there is no
  other path (vocals-only stem, ABC/melody sheet) by which lyric content could
  have entered training. Per the model's own docstring
  (`yue2_model.py` line 12), the AR's prompt prefix is supposed to be
  *"instruction + tags + lyrics"* — for all 267 clips, the lyrics slot was
  empty, every step, for the entire run.
  - **Why this produces exactly this failure mode.** The AR's `loss/ar_ce`
    target every step was the real codec tokens of real singers singing real
    words — but the prefix conditioning it, to predict from, carried style
    tags only. The loss rewarded matching those tokens from style alone, and
    never once rewarded getting the words right, because there was no lyric
    text to get right against. The NAR flow loss (`additional_model_loss`,
    the main rendering pathway) is caption-lyrics-independent and was never
    affected — which is why style/timbre fidelity is strong while
    only language-conditioned generation degraded. The `ar_kl` divergence
    from base (0.37 → 1.50 across the run, `TRAINING_ANALYSIS/ANALYSIS.md`)
    is the visible symptom of this: with no lyric-fidelity signal to hold it
    in place, the AR expert's language-facing weights were free to drift
    purely toward style, unopposed except by the generic (and, per the loss
    curves, insufficient) `ar_kl_weight: 0.2` anchor.
  - **This supersedes the initial framing from this same session** that
    treated `ar_loss_weight` (absent from the config, defaulting to `1.0` per
    `yue2_model.py:196`) and the empty `network_kwargs.ignore_if_contains`
    (`config/akbar_arabic_rock_lora.yml` line 21, meaning LoRA is attached
    inside `model.ar` per `toolkit/lora_special.py:524` and confirmed by the
    `.ar.`-matching code at `yue2_model.py:598`) as an inherent style-vs-
    pronunciation tradeoff to be dialed via `ar_kl_weight`. That mechanism
    description is still factually correct — those are the actual knobs that
    moved — but the tradeoff framing was wrong. There was nothing to trade
    off: style and pronunciation are different subsystems (NAR flow vs. AR
    language-conditioning), and only one of them was ever being trained
    correctly. No amount of reweighting `ar_loss_weight`/`ar_kl_weight` could
    have delivered both, because the missing ingredient was data, not a
    hyperparameter balance.
  - **Second, independent confirmation this was a stale decision, not a
    one-off bug.** `DECISIONS.md`'s `cot: "off"` entry states the style-only
    captions were explicitly "aligned with a pure style/timbre-transfer
    goal" — the same goal that was later corrected (see the
    `train_window_frames` entry above) to require full-song structural
    coherence. `train_window_frames` was caught and fixed at that
    correction; the lyrics-stripping decision, made under the same
    superseded framing, was not — it should have been revisited at the same
    time, for the same reason.

- **Fix plan — not yet executed, pending sign-off on touching the dataset
  (currently frozen per `AGENTS.md` line 33):**
  1. **Verify the fix is free.** Confirm a raw `workspace_manifest.json`
     track object actually carries a `lyrics` field with the real per-clip
     sung text (the `prepare_yue2_dataset.py` docstring implies it exists and
     is simply unused; `evaluation_alharith.json`'s separate `styles`/
     `lyrics` keys support this). If confirmed, no new data collection is
     needed — only a script change.
  2. **Patch the caption builder** (or, preferably, a small standalone script
     that only rewrites existing `.txt` captions, touching neither audio nor
     the shortlist) to append the lyrics in YuE2's native format —
     style text, then a literal `[Lyrics]` line, then the lyric block —
     matching `parse_caption()`'s expected layout (`yue2_model.py:129-157`).
  3. **Invalidate the cache.** `cache_latents_to_disk` (audio-derived codec
     tokens) is caption-independent and stays valid; `cache_text_embeddings`
     (prefix embeddings) is not — delete `_latent_cache` before the next run
     so it rebuilds against the new captions.
  4. **Sanity-check offline first**: run `parse_caption()` on a few of the
     new `.txt` files locally (no GPU) to confirm the `style`/`lyrics` split
     comes out clean before spending any compute.
  5. **Smoke-test on the A100** for a handful of steps (VRAM/step-time should
     be materially unchanged; captions are small) before committing the full
     step budget.
  6. **Leave `ar_loss_weight`, `ar_kl_weight`, and `ignore_if_contains`
     untouched for this run.** They were compensating for a missing-signal
     problem; with real lyric-conditioned targets, the existing
     `ar_kl_weight: 0.2` anchor may already be sufficient, and changing them
     at the same time would confound whether the caption fix alone worked —
     one variable, per the project's standing discipline, and this is the
     one that was actually wrong.
  7. **Evaluate apples-to-apples** against the same four
     `INFERENCE/evaluation_alharith.json` prompts. If pronunciation recovers
     but style regresses, `do_separation: true` (an explicit lyrics-only →
     vocals-only AR term, `yue2_model.py` lines 19–24) is the next lever —
     as a follow-up step, not bundled into this one.

- **The previously-listed "options for a v2"** (freeze the AR via
  `ar_loss_weight: 0`, exclude it via `ignore_if_contains`, raise
  `ar_kl_weight`, or average across checkpoints) are **downgraded to
  fallbacks only**, not first-choice fixes: each either forfeits the
  structural-coherence learning `train_window_frames: 0` was introduced for,
  or re-creates the same averaging the user explicitly rejected. They remain
  worth knowing about if the caption fix above turns out to be blocked or
  insufficient, but are not the plan.
- **Next:** confirm the raw manifest's lyrics field (step 1 above), then
  decide whether to lift the dataset freeze for this specific, narrowly-
  scoped change.

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

## 2026-09-21 — audio.cpp YuE2 LoRA inference (separate work area): T4 OOM root cause + frame ceiling

- **Scope.** Ad-hoc inference run alongside training: `0xShug0/audio.cpp` @ `e3de8e3`, CUDA, driven with
  the converted step-3000 LoRA (`/content/converter/out/akbar_arabic_rock_lora_{ar,nar}.safetensors`,
  AR+NAR scale 1.0) on the four held-out maqam prompts. Everything lives under `/content/audiocpp_test/`
  and is mirrored to GCS `.../OSTRIS_Arabic_Suno_Finetuning/audiocpp_gguf_test/`. This repo's only change
  is this entry — nothing committed/pushed.
- **Output length = `semantic_max_tokens` (25 frames/s); `--duration-seconds` is ignored by YuE2.**
  Sampling knobs are the prefixed `semantic_*` / `abc_*` request-options (audio.cpp `docs/models/yue2.md`);
  the generic `--temperature/--top-p/--top-k/--repetition-penalty` flags are **no-ops** for YuE2.
- **`docs/text_to_duration_formula.md` used for a dynamic cap** (`duration_s ≈ 92 + 0.280·N_letters`,
  rounded to nearest 10 s, ×25): Hijaz 6500, Nahawand 6000, Ajam 5750, Kurd 5500 for our held-out lyrics.
- **OOM root cause — VRAM, not the cap.** The model self-terminates (`truncated=0`) well under the cap;
  length is seed-dependent (Hijaz seed 42 → 5189 frames; seed 1000 → 6355; seed 1001 → 6536). The crash is
  `CUDA error: out of memory` / `cuMemCreate` at `ggml-cuda.cu:535`, during **NAR graph construction**.
  NAR-graph VRAM is ~linear in frames, and the LoRA adds ~2.6 GiB of merged decoder weights right before it
  (`yue2.lora.decoder_merge_values 2818572288`). Measured: no-LoRA 6095 frames peaked 14,843 MiB (96.6%,
  OK); LoRA 5189 frames 12,463 MiB (OK); LoRA 6536 frames → OOM. **The earlier 360-cap run survived only
  because its seed emitted 5189 frames — the cap was never the binding constraint.**
- **T4 ceiling ≈ ≤5800 frames (~3:52).** So the formula-based dynamic cap does **not** rescue
  Hijaz/Nahawand (they naturally emit ~6355 / ~6045). Options for a next session (not decided):
  (1) cap ≤5800 → all runs complete but endings truncate; (2) drop/omit the NAR LoRA at long lengths;
  (3) run on the A100-80GB, where natural-length LoRA songs fit easily.
- **State.** GCS `audiocpp_gguf_test/` holds `converter/`, `out/` (30 s + 360-cap A/B, batch runs, logs,
  1 Hz `_gpu.csv`), `prompts/`, `scripts/` (`run_one.sh`, `run_batch16_resilient.sh`, `duration_cap.py`,
  `backup_live.py`), `agent_notes/`. A resilient batch runner (continues past OOM, skips completed runs,
  logs failures to `out/_failed_runs.log`) was launched; all Hijaz seeds at cap 9000 OOM'd, then it was
  relaunched with dynamic caps (still running at session end). Per-session detail: `agent_notes/current.md`
  and GCS `audiocpp_gguf_test/agent_notes/current.md`.
