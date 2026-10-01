# current

_Copy surface, not authority. Session · 2026-10-01 · **T4 High-RAM Colab**, branch `music-cover`._

## Rescue batch — DONE + benchmarked

24/24 takes, **0 failures**, ran `06:40:05Z → 09:20:35Z` (2.67 h). Config: **`qfinal_a0.3` +
`cot=full` + fresh seed per take**, guided by each take's SheetSage2 melody-only ABC.

**Benchmark (T4 High-RAM — T4 15 GB, 8 vCPU, 50 GiB RAM):** mean **401.0 s/track (6.68 min)**,
median 406.7, range 307.6–490.1; **~9.0 tracks/hour**; realtime **~1.62×**; peak RSS **~6.9 GB**;
GPU ~99% / ~5.4 GB VRAM; ~3% slower than the `cot=off` pass-1 benchmark. Recorded in
`docs/INFERENCE.md` (Rescue batch benchmark) + raw `results/rescue_batch12_t4_benchmark/per_track.json`.

- **GCS (all 24):** `…/audiocpp_inference/workspace/out/rescue_v2abc_batch12_winning/`
- **Old melody run:** archived → `…/audiocpp_inference/out_archive/rescue_v2abc_batch12_winning_melody_20261001/`.

## Next — listen / package

Package rescue-vs-pass-1 for blind listening with `INFERENCE/prepare_ab_eval.py` (skill
`ab-blind-eval`). Reminder: it needs **variant subfolders with the same stem**
(`…/<variant>/track.wav`), not a flat folder. NB the rescue names use **fresh seeds**, so the
pass-1 stem differs — pair by song, not by identical filename.

## Housekeeping (approved plan) — status

- **Phase 0–2:** done. `DECISIONS.md` (frozen) reverted; reconciler **0 flagged**; docs updated.
- **Phase 3 (graph):** **blocked** — `graphify` not on PATH; graph stale (`cfbc3dd` vs HEAD).
- **Phase 4 (tests):** **PASS** — full suite exit 0 (1 skip); log `/content/logs/post_batch_housekeeping.log`.
- **Phase 5 (push):** pushed; `origin/music-cover` == local HEAD.
- **Phase 6 (backup):** daemon current; one-shot confirm `local_wavs=24 gcs_wavs=24`.
- **Phase 7:** this file.

## prepare_ab_eval layout fix (from earlier)

Flat root → `error: '…' is not in the subpath …`; the tool needs `…/<variant>/<track>.wav` with a
shared stem. PowerShell restructure + command are in `docs/COMMAND_HANDOVER_GOTCHAS.md` (2026-10-01)
and the prior handoff.

## Notes

- Backup daemon `--inference` up (flat dirs via `--extra`); `vm-continuity` healthy; `gpu_logger` down.
- A harness-backgrounded watcher died once (`exit 1`, no notification); the detached re-run
  (`setsid nohup /content/logs/post_batch_housekeeping.sh`) completed. Prefer `setsid nohup` for
  long jobs here.
