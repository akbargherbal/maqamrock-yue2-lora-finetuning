# YuE2 Dataset Verification

Verification of `./yue2_dataset` produced by `prepare_yue2_dataset.py` against what
`ostris/ai-toolkit`'s YuE2 support actually expects.

## 1. Script run

```
python3 prepare_yue2_dataset.py --root ./min_4stars_ai_music --out ./yue2_dataset
```

Result: **Wrote 267 audio/caption pairs**. No warnings: 0 workspaces missing a
manifest, 0 on-disk files absent from their manifest, 0 maqam mismatches.
(1700 manifest entries were skipped as expected — those takes aren't on disk.)

## 2. What the YuE2 loader actually requires

Source of truth (fresh clone of `ostris/ai-toolkit`): `toolkit/data_loader.py`
(`AiToolkitDataset`), `toolkit/dataloader_mixins.py`,
`extensions_built_in/audio_models/yue2/yue2_model.py`. There is **no
`config/examples/*yue2*.yaml`**; defaults live in `toolkit/models/registry.py:59`.

- **Audio extensions:** `.mp3 .wav .flac .aac .ogg .m4a` — all fine.
- **Pairing:** caption = `<audio stem> + caption_ext` (default `.txt`) in the same
  directory. `caption_ext` normalizes to `.txt`.
- **Traversal:** recursive `os.walk`, so a flat folder is fine (only `--per-maqam`
  would add subfolders, also fine).
- **Sample rate:** `YuE2AudioModel.sample_rate == 48000` (`src/vae.py:17`). Loaded
  with `torchaudio`, **auto-resampled to 48k** and up/mixed to stereo. Pre-48k
  files are not required.
- **Clip length:** no hard min/max in the loader. VAE encodes in 60 s chunks
  (HOP=1920) and drops trailing <0.04 s; AR hard ceiling is
  `CONTEXT 24576 / 25 fps ≈ 983 s`. Dataset is 162–370 s → safe.
- **Naming:** any ASCII path works; no fixture naming convention beyond `stem.txt`.
- **Hard requirement:** YuE2 raises `"needs codec tokens in the latent cache;
  enable latent caching"` unless `cache_latents`/`cache_latents_to_disk` is on.

## 3. Produced dataset vs those requirements — no blocking mismatch

Verified read-only with `/tmp/opencode/verify_dataset.py`:

- **267 audio + 267 `.txt`**, 0 other files; no orphan audio, no orphan caption,
  no duplicate stems. All `.mp3`.
- Probe of **all 267**: `codec_name=mp3, sample_rate=48000, channels=2` — already
  native YuE2 format.
- **Filenames:** all ASCII, space-free, max 55 chars, max bytes well under 255.
- **Captions:** 740–811 chars (~200 tokens), none empty/short/NUL/BOM; all contain
  `Maqam <X>`; none contain `[Is_MAX_MODE`/`[QUALITY`/`[REALISM`/`[START_ON`/
  `///***///`/`[Intro`/`[Verse`.
- **Exact-match:** all 267 captions byte-equal a caption re-derived independently
  from the manifests.

## 4. Caption spot-check vs `workspace_manifest.json`

For `ajam_amro_bin_kalthoum_23072026_029_...` the `.txt` is exactly
`genre + "Maqam Ajam." + vocals + production + instrumentation + mood`; the
`[Is_MAX_MODE...] [QUALITY...] [REALISM...]` + two `[START_ON: ...]` lines and all
`lyrics` were stripped (no lyric line from the source appears). Across the
shortlisted set, `genre/vocals/production/instrumentation` are present on all 267;
`mood` is present where the manifest had it. A whole-manifest audit found 25
tracks whose `styles` has no Suno header/genre fields — **none of them are on
disk**, so none entered the dataset.

## 5. Notes / non-blocking issues

- **Don't use `--convert-wav`:** source is already 48 kHz stereo; the script's WAV
  path hardcodes `-ar 44100`, which the loader would resample back to 48 k (a
  needless lossy round-trip). The help text saying "44.1kHz WAV" is stale.
- **Provenance loss:** the 6 files from the Arabic-named workspace `منوعات` became
  `<maqam>_ws_*` (sanitizer collapses non-ASCII to `ws`). Valid, but the workspace
  name is gone.
- Dataset has **no trigger word** (ran without `--trigger`); that's fine because
  config injects it.
- Captions are style-only (no `[Lyrics]` section), so YuE2's `parse_caption`
  treats the whole string as tags/`style` with empty lyrics — intended.

## 6. Config still needed to launch (none of this is in the repo)

`process[].type: 'sd_trainer'` plus:

- `model.arch: yue2` — **required**; `get_model_class` resolves by `arch` and
  errors on unknown/None.
- `model.name_or_path: Comfy-Org/YuE2/checkpoints/yue2_3b_int8_convrot.safetensors`,
  `quantize: true`, `qtype: convrot8` (registry default).
- Tokenizer path: **not needed** — embedded in the checkpoint
  (`text_encoders.yue2_tokenizer_json`). Separately auto-downloaded from HF unless
  overridden in `model_kwargs`: `semantic_head_path` (MERT-v2 head, required for
  caching), `nar_lora_path` (only with `merge_nar_lora`), `sheetsage_path` (only
  when `cot != "off"`).
- `datasets[]`: `folder_path: ./yue2_dataset`, `caption_ext: txt`,
  **`cache_latents_to_disk: true`** (mandatory for YuE2), plus `resolution`
  (irrelevant for audio but config expects it).
- `train.noise_scheduler: flowmatch`; standard `network`/`save`/`sample` blocks;
  `sample` should use `sampler: flowmatch` and `duration`.
- Optional: process-level `trigger_word` (auto-prepended if absent — no dataset
  edit needed); `model_kwargs` `cot` (default `"full"` → needs SheetSage2),
  `train_window_frames` (default 1500 = 60 s), `ar_loss_weight`, `do_separation`.

The dataset and script were not modified. Verification script:
`/tmp/opencode/verify_dataset.py`.
