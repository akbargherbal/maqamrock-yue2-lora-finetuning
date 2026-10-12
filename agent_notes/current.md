# current.md — Probe S DONE ✅ (2026-10-12)

Copy/read surface only. Run `2026-10-12T04:48:26Z → 05:40:28Z` (≈52 min wall; projection was ~39 min
at 6.5 min/track — actual ≈8.8 min/track, not anomalous, just slower). Banked.

## Verified — 6 tracks, all exit 0, none truncated
| file (`out/v3_prompt_probe/…`) | exit | trunc | wall | dur_s |
|---|---|---|---|---|
| `lora_on/v3pp_S0_full_2640605763.wav` | 0 | no | 9:35 | 244.0 |
| `lora_on/v3pp_S1_core_2640605763.wav` | 0 | no | 9:18 | 228.1 |
| `lora_on/v3pp_S2_retarget_2640605763.wav` | 0 | no | 8:46 | 210.8 |
| `lora_on/v3pp_S4_prune_2640605763.wav` | 0 | no | 9:09 | 222.5 |
| `lora_off/v3pp_B1_base_full_2640605763.wav` | 0 | no | 7:41 | 258.8 |
| `lora_off/v3pp_B2_base_core_2640605763.wav` | 0 | no | 6:55 | 239.9 |

All 48 kHz stereo; no OOM/errors. Off-arms logged `scale=0.000000` (AR+NAR) — adapter genuinely off.
Adapter sha256 `3531bb91…` / `a7eabcad…` (v3 final pair).

- GPU: free at start (T4, 0 MiB) **and** free at end (0 MiB, no compute apps).
- Bank: `banked -> gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/v3_arabmaqamrock_lora/prompt_probe`
- Sidecars up: `backup_to_gcp.py` (21164), `gpu_logger.py` (21165), vm-continuity OK (0 failures).

## Listening step — rating command (Windows)
Prereq: put `v3_spice.json` somewhere, e.g. `C:\Users\DELL\Downloads\v3_spice.json` (download:
GCS `…/spice_probe/v3_spice_scorecard.json`, or copy the repo's `INFERENCE/scorecards/v3_spice.json`).
Audio = the flat 6-file folder already downloaded: `C:\Users\DELL\Downloads\v3_prompt_probe\eval`.
```powershell
cd C:\Users\DELL\Jupyter_Notebooks\ai_music_rating_app
py app.py --audio "C:\Users\DELL\Downloads\v3_prompt_probe\eval" --label v3_prompt_probe --blind --scorecard "C:\Users\DELL\Downloads\v3_spice.json"
```
Alt (card copied into the app's `scorecards\`): use `--scorecard v3_spice` (bare name).
`--blind` shuffles + hides arm names; the report reveals them. Same `--label` resumes the run.

## eval/ contents (arm-named, the 6 files)
`S0_full.wav · S1_core.wav · S2_retarget.wav · S4_prune.wav · B1_base_full.wav · B2_base_core.wav`

Read-out is the user's: `S0≈S1 && B1≈B2` → base-dominant (prune/retarget pays); `S0≈S1 && B1≠B2`
→ LoRA suppressing prompt responsiveness.
