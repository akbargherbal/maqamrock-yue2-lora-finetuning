# v3 maqamrock training dataset (provenance)

The training set for the **`v3_arabmaqamrock_lora`** run. The data itself is **not in this
repo** (2.4 GB); this folder keeps the build provenance. Audio + captions live on GCS:

```
gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/v3_arabmaqamrock_dataset.zip
  … .zip.sha256
  … v3_arabmaqamrock_dataset_manifest.json
  … v3_arabmaqamrock_dataset_report.md
```

- **438 tracks** (Ajam 118 · Hijaz 107 · Kurd 101 · Nahawand 112), mp3 48 kHz stereo,
  max 370 s. A strict superset of the v2 267 (v2 → `<base>/v2_arabmaqamrock_dataset/`).
- **Verbatim lyric tags** — v2 collapsed `[Section | asides]` → `[Section]` and dropped
  non-section tags (`[orchestral strings swell]`, …); v3 keeps them. The Suno style header
  (`[Is_MAX_MODE…]`/`[START_ON…]`) is still stripped.
- Built by [`prepare_yue2_dataset_v3.py`](../../prepare_yue2_dataset_v3.py) from the
  `NEW_min_4stars_ai_music.zip` manifest tree.

## Files here
| file | what |
|---|---|
| `manifest.json` | the 438 `out_name → {maqam, workspace, source filename, clip_id}` map |
| `build_report.md` | counts, kept tags, empty-lyrics check |
| `v3_overrides.json` | 3 surgical `vocals` edits (see below) |

## Surgical overrides (3)
Three nahawand tracks carry a stray trailing tag `emotional female voice`; the build joins it
into the vocals line (`Male deep baritone and emotional female voice, …`):
`nahawand_nabigha_17072026_A_{001_cb2bb293,002_82f1d0a7,011_317ab59b}`.
(Two other tracks carried a stray `grave male vocals` and two `female harmonies`; those were
left ignored — trailing text outside quoted fields never reaches a caption.)

## Reproduce
```bash
python prepare_yue2_dataset_v3.py \
  --root <unzipped NEW_min_4stars_ai_music> \
  --out  v3_arabmaqamrock_dataset \
  --overrides datasets/v3_arabmaqamrock/v3_overrides.json
```

## Integrity
`v3_arabmaqamrock_dataset.zip` (2,530,501,579 bytes) sha256 =
`5b5624ee4bc03dcb9d89450a9e2a81871343ddd59558f9a24e98f4ca49e7830f`
(also at GCS as `.sha256`; CRC32C verified on upload).
