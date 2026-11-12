# Arabic instrumental dataset (482 tracks) — build, verify, use

_Status: **built and uploaded 2026-11-12.** This runbook describes the delivered artifact; the
build script is `prepare_arabic_instrumental_dataset.py` and the pre-build plan (with the
verified source findings) is `docs/ARABIC_INSTRUMENTAL_DATASET_PLAN.md`._

## What it is

A flat, YuE2/OSTRIS-format dataset compiled from two generated instrumental sets:

| source | tracks | audio |
|---|---:|---:|
| `gs://akbar-december-2024-backup/DATASET/yt500_instrumental` | 460 | 3,019,950,108 B |
| `gs://akbar-december-2024-backup/DATASET/fadhl_shaker_instrumental_18_shortlist` | 22 | 142,160,094 B |
| **total** | **482** | **3,162,110,202 B · 36.60 h** |

GCS deliverables (`<base>` = `gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning`):

```
<base>/arabic_instrumental_dataset.zip                  3,162,874,610 B, 964 entries
<base>/arabic_instrumental_dataset.zip.sha256           cea34fa2e584472d0b134f51dc0ae83b66d999ee1dffbc40dad4dcd783e39954
<base>/arabic_instrumental_dataset_manifest.json        per-track records (482)
<base>/arabic_instrumental_dataset_report.md            build report
```

The zip root is flat — `<name>.mp3` + `<name>.txt`, no directory — matching
`v3_arabmaqamrock_dataset.zip`. The names are the source track-directory names verbatim
(`yt500-…`, `fs18-…`), already unique and ASCII.

## Per-track format

```
<name>.txt  =  "Middle Eastern fusion, instrumental. " + <caption.txt> + "\n[Lyrics]\n" + <lyrics.txt>
<name>.mp3  =  <source audio.mp3>, byte-identical (hardlinked at build time)
```

- The caption is copied **verbatim** (only leading/trailing whitespace stripped); paragraph
  breaks are preserved. The prefix is the only added text.
- `lyrics.txt` in both sources is a **section-tag plan**, not sung text — 5–12 tags
  (`[intro]`, `[verse]`, `[chorus]`, `[bridge]`, `[interlude]`, `[outro]`). It is kept as the
  `[Lyrics]` block, matching v3's prompt shape.
- No trailing newline after the last tag (same as `prepare_yue2_dataset_v3.py`).

Manifest fields per track: `out_name`, `source_dataset`, `source_uri`, `title`, `artist`,
`audio_bytes`, `audio_sha256`, `audio_duration_s`, `caption_chars`, `caption_paragraphs`,
`caption_status`, `caption_vocal_terms`, `lyrics_tags`, `caption_sha256`, `prompt_sha256`.

## Build

Sources are fetched first (the builder is offline, read-only on them):

```bash
mkdir -p /content/arabic_instrumental_build/src/{yt500,fadhl}
gsutil -m cp -r gs://akbar-december-2024-backup/DATASET/yt500_instrumental/tracks \
  /content/arabic_instrumental_build/src/yt500/
gsutil -m cp -r gs://akbar-december-2024-backup/DATASET/fadhl_shaker_instrumental_18_shortlist/tracks \
  /content/arabic_instrumental_build/src/fadhl/

cd /content/maqamrock-yue2-lora-finetuning
python3 prepare_arabic_instrumental_dataset.py \
  --src /content/arabic_instrumental_build/src \
  --out /content/arabic_instrumental_build/arabic_instrumental_dataset
```

The builder hardlinks audio (copy fallback), writes the prompts, `ffprobe`s every mp3, hashes
each file, and writes the manifest + report next to the output directory. It aborts on:
missing/empty source file, non-UTF-8, caption already prefixed, `[Lyrics]` inside a caption,
duplicate/unsafe track name, non-tag lyric line, empty caption.

Zip and hash:

```bash
cd /content/arabic_instrumental_build/arabic_instrumental_dataset
zip -0 -X -q ../arabic_instrumental_dataset.zip *.mp3 *.txt
cd .. && unzip -tq arabic_instrumental_dataset.zip   # 964 entries, no errors
sha256sum arabic_instrumental_dataset.zip > arabic_instrumental_dataset.zip.sha256
```

Upload the four objects:

```bash
cd /content/arabic_instrumental_build
gcloud storage cp arabic_instrumental_dataset.zip arabic_instrumental_dataset.zip.sha256 \
  arabic_instrumental_dataset_manifest.json arabic_instrumental_dataset_report.md \
  gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/
```

## Verify (any session)

```bash
# object sizes + the sidecar
gsutil ls -l gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/arabic_instrumental_dataset*

# remote bytes vs the recorded sha256 (streams 3.0 GiB, ~1 min)
gsutil cat gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/arabic_instrumental_dataset.zip \
  | sha256sum
cat /content/arabic_instrumental_build/arabic_instrumental_dataset.zip.sha256
```

Local source of the delivered bytes (if the build workspace still exists):

```bash
cd /content/arabic_instrumental_build
gsutil hash -c arabic_instrumental_dataset.zip      # crc32c matches the remote object
unzip -l arabic_instrumental_dataset.zip | tail -1  # 964 files
```

Verified at build time (2026-11-12):

- 482 mp3 + 482 txt, one-to-one, no leftovers.
- Every prompt starts with the prefix; exactly one `[Lyrics]`; every lyric line is a bracket tag.
- Every mp3 decodes as mp3 with a positive duration (482/482); total 36.60 h.
- 0 empty captions, 0 duplicate track names, 0 duplicate captions.
- `unzip -t` OK; 4 random tracks re-hashed straight out of the zip (prompt + audio) match the
  manifest.
- Remote sha256 equals `cea34fa2…39954`; remote crc32c equals the local crc32c.

## Use for training

`bootstrap/setup.sh` already supports a zip-only dataset (`job_dataset_zip`, setup.sh:269-282):
set the launching notebook/env to

```bash
export GCP_DATASET_ZIP=gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/arabic_instrumental_dataset.zip
```

and the dataset is unzipped flat into `/content/yue2_dataset` on bootstrap. No config edit is
included here: which run consumes this dataset (and at what steps/LR) is a separate, user-typed
launch decision.

## Caveats

1. **Prompt style is prose, not v3's tag list.** v3 captions are structured
   (`arabmaqamrock … Maqam X. …`); these are descriptive paragraphs written from each take's
   audio. Training on this set means prompting with prose at inference. Do not silently mix the
   two zips inside one run.
2. **"instrumental" prefix vs vocal descriptions.** 283/482 captions mention a spoken-word
   sample, vocalise, or male/female vocal (ACE-Step captioner output, inherited from the
   sources). The audio may indeed contain vocal chops. The manifest records `caption_vocal_terms`
   per track so a filtered subset can be made without rebuilding.
3. **Caption status.** 439 `ok`, 35 `fallback`, 6 `failed`, 2 `single_chunk` rewrites; all have a
   non-empty final caption. Status is in the manifest.
4. **Synthetic audio.** Both sources are generated takes, not human recordings; this merge adds
   no new quality gate and inherits the sources' duration gates.
5. **Section tags are structural.** `[verse]` etc. are plans, not lyrics; the tracks are
   instrumental.
6. Not included: `style.txt`, `score.abc`, `track.json`, `caption.json` from the sources. They
   stay in the two source datasets, which are unchanged.
