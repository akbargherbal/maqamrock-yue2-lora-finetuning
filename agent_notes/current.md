# current

## 1. Plan — corrected 2026-09-28 (cover = Python SheetSage2 + existing yue2 binary)

**Transcription (audio → ABC): official Python `m-a-p/SheetSage2`** — no audio.cpp,
no GGUF, no build. `model.transcribe(wav, output_dir=…, melody_only=True)` → `score.abc`.
Own env: torch 2.8 / torchaudio 2.8 (cu126), transformers 4.45.2, ffmpeg 6.1 + shared
libs, mir_eval/pretty_midi/mido. Backbone `MERT-v2-FullSong` (632 M, ~2.5 GB) not cached.
GPU or CPU. The audio.cpp GGUF was validated to match this reference's ABC, so the ABC
drops straight into `--request-option abc_file=`.

**Generation (cover render): the EXISTING `/content/audiocpp_inference/bin/audiocpp_cli`** —
verified it already has `cot` / `abc_file` / `melody` (so `cot=melody` + `abc_file=<score.abc>`
works). **No rebuild.** It lacks `semantic_prefix` (Form ②, needs ≥v0.8.2) — Form ① does not.

## 2. Why we are NOT rebuilding audio.cpp (finding, 2026-09-28)
Smoke #1 failed in 3 s: `unsupported model family hint: sheetsage2`. Root cause: the staged
binary was built `--model-set custom --models yue2` (`DECISIONS.md` build entry); `strings`
show **0** `sheetsage`. Upstream releases ship **only `audiocpp_server`** (HTTP, no CLI mode)
— no prebuilt `audiocpp_cli`. A sheetsage2-only rebuild was started per
`docs/audiocpp_gpu_arch_builds.md` and **stopped at 88/413** once we saw the existing binary
already has the generation knobs and Python SheetSage2 covers transcription.
**Do not restart the build.** Log: `/content/logs/build_sheetsage2.log`.

## 3. Next steps
1. One-track smoke: official Python SheetSage2 (`melody_only=True`) on a v2 wav → `score.abc`.
2. Cover smoke: existing `audiocpp_cli`, `qfinal_a0.3` LoRA, `cot=melody` + `abc_file`,
   same lyrics/seed.
3. If it holds: transcribe the v2 arm → persist ABCs to GCS → batch covers →
   blind A/B vs the `batch_36_songs` qfinal_a0.3 controls (`INFERENCE/prepare_ab_eval.py`).
4. `INFERENCE/abc_transcribe.py` targets the *audio.cpp* path — re-point/replace it for the
   Python route before any batch.

## 4. VM / artifacts
Branch `music-cover`. Staged: `models/SheetSage2-GGUF/sheetsage2-orig.gguf` (2.71 GB, now
unused), 36 wavs in `out/batch_36_songs/`, `bin/audiocpp_cli`. GPU T4, 0 MiB used.
Session-restore JSON (conversation continuity) imported successfully:
`gs://akbar-december-2024-backup/opencode_sessions/by_id/ses_f17ef5af2ffeK15W1EBgAHpDJT.json`.

## 5. Still pending
`manifests/batch_36_rock.json` (Measure A prompt arm). Feasibility record:
`docs/music-cover-feasibility.md`.
