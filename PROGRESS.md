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
