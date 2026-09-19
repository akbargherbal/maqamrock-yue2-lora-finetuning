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
