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

- Training launched and ran to ~step 810/3000 (~27%), healthy throughout: clean loss descent, GPU at ~97% util with headroom, no crashes. See `TRAINING_ANALYSIS/` for the step-654 snapshot.
- Mid-run, the actual goal was clarified: full-song structural coherence, not a timbre/style-only adapter. That exposed `model_kwargs.train_window_frames` (left at its implicit 60s default) as a real gap, not a style choice — see `DECISIONS.md`. No amount of additional training under that setting would have produced song-structure learning.
- User's call: kill now (only ~27% / ~2h of Colab L4 sunk) and relaunch with `train_window_frames: 0` rather than finish a run that would be mediocre for the actual goal and require redoing the whole thing anyway.
- Config updated (`config/akbar_arabic_rock_lora.yml`): `train_window_frames: 0` added. **Not yet smoke-tested on real hardware** for VRAM/step-time — that's the next step before trusting the `steps: 3000` budget or its old ETA.
- Next: on the next Colab L4 session, run a short smoke test (a handful of steps, ideally including one of the longest ~370s clips) watching `gpu_logger.py`'s output before committing to a full run; recompute the ETA from real s/step; then launch for real.
