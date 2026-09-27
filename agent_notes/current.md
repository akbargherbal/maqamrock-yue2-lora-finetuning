# agent_notes / current

**Date:** 2026-09-27 · **State: SMOKE DONE — awaiting go-ahead for the sweep.**

## Confirmed design (this turn)
Single **combined** config, no separate arms:
- **caption/style/prompt = one word:** `arabmaqamrock` (the trigger only)
- **lyrics = Suno verbatim** (tags kept; `///***///` dropped), per
  `manifests/workspace_manifest.json`
- adapter = **qfinal** (v2 + `quran_long_aya_r8_s10` final), alphas **0.3 / 0.5**

## Smoke (1 track) — PASSED
- run dir: `/content/audiocpp_inference/out/qfinal_suno_sweep/trigger_a0.5/`
- wav: `trigger_a0.5/nahawand_ibn_zuraiq_20082026_001_c116f240_2249126884.wav`
  (exit 0, wall 5:34, dur 169.3 s, no truncation)
- a0.3 equivalent (earlier, different seed):
  `trigger_a0.3/nahawand_ibn_zuraiq_20082026_001_c116f240_2798138695.wav`
- **Caveat:** the two alphas used different random seeds → not a controlled α compare.
  For a clean α comparison, pin one seed per song across alphas.

## Adapters (GCS library, built this session)
`<base>/loras/audio_cpp/pron/qfinal_a{0.3,0.5}/`
- converted AR a0.3 `0169e5a0ef7d47349bc707c10b3fbf5d937f941e3d28896e9970f0dc3894bdf6`
- converted AR a0.5 `3a06265f33854825309f1cb10ab4ca5c36acf8692491186321b58c867eca90d2`
- NAR (both) `7d9324bfabdfa806c600b12dfa1537501368f25a00d6f4aaf7252449414377c6`

## To run the full set (8 songs, 2 alphas = 16 tracks) once approved
```bash
cd /content/maqamrock-yue2-lora-finetuning
# alpha 0.3 (resumes/skips the 1 existing trigger a0.3 track)
python INFERENCE/generate.py INFERENCE/songs.qfinal_trigger.json \
  --lora-ar /content/converter/out/qfinal_a0.3/akbar_arabic_rock_lora_ar.safetensors \
  --lora-nar /content/converter/out/qfinal_a0.3/akbar_arabic_rock_lora_nar.safetensors \
  --out-dir /content/audiocpp_inference/out/qfinal_suno_sweep/trigger_a0.3 --label qfinal_trigger_a0.3
# alpha 0.5
python INFERENCE/generate.py INFERENCE/songs.qfinal_trigger.json \
  --lora-ar /content/converter/out/qfinal_a0.5/akbar_arabic_rock_lora_ar.safetensors \
  --lora-nar /content/converter/out/qfinal_a0.5/akbar_arabic_rock_lora_nar.safetensors \
  --out-dir /content/audiocpp_inference/out/qfinal_suno_sweep/trigger_a0.5 --label qfinal_trigger_a0.5
```

## Sidecars
- `backup_to_gcp.py --inference` daemon running (pid 25014) → mirrors `out/` to GCS.
- Code/tooling committed & pushed: `c89665d` on `pron-lora-long`.

## Session continuity (vm-continuity) — 2026-09-27
- Installed (shim `/usr/local/bin/vm-continuity`, global skill symlink, AGENTS hint) and
  the watch loop is **healthy**: `loop=running state=OK last_ship_ok=16:25:33 failures=0`.
- Store: `gs://akbar-december-2024-backup/opencode_sessions/by_host/2ec7900a2206/`.
- **Fixed an opencode-1.18.x incompatibility** (tool otherwise captured 0 sessions):
  sessions table `session_v2` → `session` (now auto-detected), and `opencode session
  export/import` → top-level `opencode export`/`import`. Pushed upstream:
  `akbargherbal/vm-continuity@35b3b4b` (README has a compatibility table). Fresh VMs get
  it via `setup.sh`'s clone/pull.

