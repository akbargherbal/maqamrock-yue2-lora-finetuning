# current

## 1. Plan (corrected 2026-09-28)
**Transcription (audio → ABC): official Python `m-a-p/SheetSage2`** — no audio.cpp,
no GGUF, no build. `model.transcribe(wav, output_dir=…, melody_only=True)` → `score.abc`.
**Generation (cover render): the EXISTING `bin/audiocpp_cli`** — verified it has
`cot`/`abc_file`/`melody`; no rebuild. (It lacks `semantic_prefix` — Form ② needs ≥v0.8.2.)

## 2. Smoke — transcription PASSED (2026-09-28)
Env `/content/.venv-sheetsage2` (uv, py3.11, torch 2.8.0+cu126, transformers 4.45.2) —
build log `/content/logs/sheetsage2_env.log`. One **v2** wav
(`01-…_4032407937`) → `melody_only=True`:
`/content/audiocpp_inference/out/ss2_smoke/score.abc` — **1888 B**, `V: Vocal` + `V: Ins`,
`% intro`/`% chorus`, **0 chord symbols**. T4, ~11 GiB. Log `/content/logs/ss2_smoke.log`.
**Timing:** cold (incl. 2.7 GB download) **136 s**; warm (cached) **82 s/track**, max RSS
3.4 GB, ABC byte-identical on re-run. ⇒ 12 v2 tracks ≈ **16 min** (under the 20-min budget);
all 36 ≈ 50 min (over it).

## 3. Next — cover-render smoke (needs qfinal_a0.3 staged)
qfinal_a0.3 adapters (87 MB each):
`gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/loras/audio_cpp/pron/qfinal_a0.3/akbar_arabic_rock_lora_{ar,nar}.safetensors`.
Call the binary **directly** (`run_one.sh:79` hardcodes `cot=off`): existing `audiocpp_cli`,
qfinal_a0.3 AR+NAR scale 1.0, `--request-option cot=melody --request-option abc_file=<score.abc>`,
same lyrics/style, seed = the v2 track's (`4032407937`). This is the real test of the
`cot=off`-trained adapters under ABC conditioning.

Then: transcribe the v2 arm → persist ABCs to GCS → batch covers → blind A/B vs the
`batch_36_songs` qfinal_a0.3 controls (`INFERENCE/prepare_ab_eval.py`).
`INFERENCE/abc_transcribe.py` targets the *audio.cpp* path — replace with a Python-route
driver before any batch.

## 4. Why we are NOT rebuilding audio.cpp (2026-09-28)
Smoke #1 failed in 3 s: `unsupported model family hint: sheetsage2` — the staged binary was
built `--models yue2` (`DECISIONS.md`); releases ship only `audiocpp_server` (no CLI). Rebuild
abandoned at 88/413. **Do not restart.** Log `/content/logs/build_sheetsage2.log`.

## 5. VM / artifacts
Branch `music-cover`. Staged: SheetSage2-GGUF (2.71 GB, unused), 36 wavs,
`model/Yue2-3B-GGUF`, `bin/audiocpp_cli`, `converter/out/` (v2 pair only). GPU T4.
Session-restore JSON imported:
`gs://akbar-december-2024-backup/opencode_sessions/by_id/ses_f17ef5af2ffeK15W1EBgAHpDJT.json`.

## 6. Still pending
`manifests/batch_36_rock.json` (Measure A). Record: `docs/music-cover-feasibility.md`.
