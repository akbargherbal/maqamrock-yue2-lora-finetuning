# Current — 2026-11-12

**Done: `arabic_instrumental_dataset` built, uploaded, and end-to-end verified.**

## Delivered

`gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/`

| object | size |
|---|---|
| `arabic_instrumental_dataset.zip` | 3,162,874,610 B (964 entries: 482 mp3 + 482 txt) |
| `arabic_instrumental_dataset.zip.sha256` | `cea34fa2e584472d0b134f51dc0ae83b66d999ee1dffbc40dad4dcd783e39954` |
| `arabic_instrumental_dataset_manifest.json` | per-track records (482) |
| `arabic_instrumental_dataset_report.md` | build report |

482 tracks = 460 `yt500_instrumental` + 22 `fadhl_shaker_instrumental_18_shortlist`;
3,162,110,202 B audio; 36.60 h.

Every `.txt` = `Middle Eastern fusion, instrumental. ` + caption verbatim + `\n[Lyrics]\n` +
section tags. Captions/sections copied byte-for-byte; source datasets untouched.

## Verified

- 482 mp3 + 482 txt, one-to-one; every prompt has the prefix, one `[Lyrics]`, tag-only lines.
- All 482 mp3 decode (`ffprobe`), positive duration.
- `unzip -t` OK; 4 random tracks re-hashed out of the zip match the manifest.
- Remote zip streamed: sha256 `cea34fa2…39954` == local recorded sha256.
- Manifest/report/sha256 sidecars byte-identical remote vs local.

## Use

```bash
export GCP_DATASET_ZIP=gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/arabic_instrumental_dataset.zip
```

`bootstrap/setup.sh` unzips it flat into `/content/yue2_dataset` (`job_dataset_zip`).

## Repo

Committed locally (`git log -1`). Not pushed to GitHub yet (needs
`bash bootstrap/github_auth.sh` + `git push origin main`). A full `git bundle` is in
`<base>/repo_bundles/` so the work survives VM shutdown without GitHub auth.

- new: `prepare_arabic_instrumental_dataset.py`, `docs/ARABIC_INSTRUMENTAL_DATASET.md`,
  `docs/ARABIC_INSTRUMENTAL_DATASET_PLAN.md`
- edited: `SOURCE_OF_TRUTH.md` (dataset row), `docs/README.md` (index row),
  `RECONCILIATION_LOG.md` (pass entry; 52 flagged = 3.0%, all `missing_path` false positives)

## Build workspace

`/content/arabic_instrumental_build/` (`src/`, flat dataset with hardlinks, zip, manifest,
report, build.log). Safe to delete to reclaim ~6.5 GB; GCS copy is verified.

## Caveats

- Captions are prose (not v3's tag-style captions) and 283/482 mention vocal material
  (`caption_vocal_terms` in the manifest). Details: `docs/ARABIC_INSTRUMENTAL_DATASET.md`.
