# agent_notes / current

**Date:** 2026-09-27 · **State: SWEEP RUNNING (detached)** — qfinal inference test:
Suno-prompt compatibility + trigger-only, alpha 0.3 / 0.5, over the 8 songs in
`manifests/workspace_manifest.json`.

## Run layout
- Script: `INFERENCE/qfinal_suno_sweep.sh` — **detached** (setsid; survives Ctrl+C).
  Log: `/content/logs/qfinal_suno_sweep.log`
- Outputs: `/content/audiocpp_inference/out/qfinal_suno_sweep/<arm>_a<alpha>/`
  (so the backup daemon mirrors them to GCS).
- Order: smoke (trigger a0.3, 1 track) → `suno_a0.3` → `trigger_a0.3` (resumes over the
  smoke track) → `suno_a0.5` → `trigger_a0.5`. **32 tracks total, ~7 min each (~3.6 h).**
- Smoke: **PASSED** — trigger a0.3 track 1 exit 0, wall 6:59, dur 215.8 s, no truncation.

## Check progress
```bash
tail -n 40 /content/logs/qfinal_suno_sweep.log
cat /content/audiocpp_inference/out/latest/batch_summary.txt   # newest finished batch
nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader
```

## Stop / resume (resumable: succeeded WAVs are skipped)
```bash
# stop now
pkill -f qfinal_suno_sweep.sh; pkill -f 'generate.py INFERENCE/songs.qfinal'; pkill -f audiocpp_cli
# resume (re-run the same script; already-succeeded tracks are skipped)
cd /content/maqamrock-yue2-lora-finetuning
setsid nohup bash INFERENCE/qfinal_suno_sweep.sh > /content/logs/qfinal_suno_sweep.log 2>&1 & disown
```

## Adapters (Phase 1) — quran_long_aya_r8_s10 final merged with v2 style
Built locally in `/content/converter/out/qfinal_a{0.3,0.5}/`, and **persisted to the LoRA
library** `<base>/loras/audio_cpp/pron/qfinal_a{0.3,0.5}/`.
- source v2 fused sha256 `b1d090987355303129a3765d257e61c983b91d48cecb8a30aa424e09cdd24cd4`
- source qfinal (`quran_long_aya_r8_s10/output/quran_long_aya_r8_s10.safetensors`) sha256
  `f8c842e48b93d142bc3cfee6e98f54809020813ae272485a4afb849320b1e2e8`
- converted NAR (both alphas) `7d9324bfabdfa806c600b12dfa1537501368f25a00d6f4aaf7252449414377c6`
- converted AR: a0.3 `0169e5a0ef7d47349bc707c10b3fbf5d937f941e3d28896e9970f0dc3894bdf6`
  · a0.5 `3a06265f33854825309f1cb10ab4ca5c36acf8692491186321b58c867eca90d2`

## Code changes this session (tested, `pytest tests/test_generate.py tests/test_suno_to_songs.py` = 69 pass)
- `INFERENCE/suno_to_songs.py`: `--style {canonical,verbatim,trigger-only}` +
  `--lyrics-verbatim` (keep Suno tags, drop only `///***///`).
- `INFERENCE/generate.py`: `--lora-ar` / `--lora-nar` (used by preflight + asset
  fingerprint, forwarded to `run_one.sh`), so a batch manifest records the real adapter.
- Inputs: `INFERENCE/songs.qfinal_suno.json` (raw Suno styles) and
  `songs.qfinal_trigger.json` (style `arabmaqamrock` only); both lyrics verbatim.

## Sidecars
- `backup_to_gcp.py --inference` daemon: running (pid 25014), watches
  `/content/audiocpp_inference/out` → GCS. Log `/content/logs/gcp_backup_inference.log`.
  **Note:** it does NOT watch `/content/converter/out` — hence the manual adapter upload.

## Next (Phase 5, after the sweep)
- Blinded listening package via the `ab-blind-eval` skill (arm × alpha per song).
- Update `docs/LORA_INVENTORY.md` with the two qfinal adapters; `backup_to_gcp.py --inference --once`.
