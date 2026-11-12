# Plan — `arabic_instrumental_dataset` (482 tracks, compiled from two instrumental sets)

_Status: **EXECUTED 2026-11-12.** Built and uploaded as
`gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/arabic_instrumental_dataset.zip`
(3,162,874,610 B, 964 entries, sha256 `cea34fa2e584472d0b134f51dc0ae83b66d999ee1dffbc40dad4dcd783e39954`).
Operational runbook: `docs/ARABIC_INSTRUMENTAL_DATASET.md`. Decisions D1–D7 below were accepted
as defaults. Every number was re-derived during the build; see the build report in GCS._

Goal: compile one OSTRIS/YuE2-ready dataset (`audio` + `.txt` prompt pairs) from

- `gs://akbar-december-2024-backup/DATASET/fadhl_shaker_instrumental_18_shortlist` (22 tracks)
- `gs://akbar-december-2024-backup/DATASET/yt500_instrumental` (460 tracks)

in the same shape as
`gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/v3_arabmaqamrock_dataset.zip`.

---

## 0. Verified findings (evidence first)

| # | Finding | How checked |
|---|---|---|
| F1 | Source counts: **460** yt500 tracks + **22** fadhl tracks = **482**. Every source track has `audio.mp3`, `caption.txt`, `lyrics.txt` (plus `style.txt`, `score.abc`, `track.json`, `caption.json`). | `gsutil ls .../tracks/*/{audio.mp3,caption.txt,lyrics.txt}` → 460/460/460 and 22/22/22 |
| F2 | Audio size: **3,019,950,108 B** (yt500) + **142,160,094 B** (fadhl) = **3,162,110,202 B ≈ 2.95 GiB**. Catalog durations sum to **36.59 h** (34.95 + 1.65). | `gsutil ls -l .../tracks/*/audio.mp3`; `catalog.csv` |
| F3 | The reference `v3_arabmaqamrock_dataset.zip` is **flat** (no root folder): `<name>.mp3` + `<name>.txt` at the zip root; 876 objects for 438 tracks. The `.txt` is `style\n[Lyrics]\nlyrics`. Its siblings in GCS are `.zip`, `.zip.sha256` (`<hash>  <filename>`), `_manifest.json`, `_report.md`. | first 600 B + last 400 KB of the zip via `gsutil cat -r`; `prepare_yue2_dataset_v3.py:185,201-204`; `ls` of the OSTRIS prefix |
| F4 | `bootstrap/setup.sh` already consumes this shape: `GCP_DATASET_ZIP` → `gcloud storage cp` + `unzip` **flat** into `/content/yue2_dataset` (`job_dataset_zip`, setup.sh:269-282). No new plumbing needed. | `sed -n 96-110p`, `269-282p bootstrap/setup.sh` |
| F5 | All 482 `caption.txt` are valid UTF-8, non-empty, **199–2289 chars**, 1–4 paragraphs; **none** already carries the prefix, **none** contains a `[Lyrics]` marker, **0 duplicate captions**, no mojibake (`â€`, `Ã`, U+FFFD), no CR. | full read of 964 text objects via `google-cloud-storage` + checks in §4 |
| F6 | All 482 `lyrics.txt` are **pure bracket tags** (no words): 5–12 tags per track from `[intro] [verse] [chorus] [bridge] [interlude] [outro]`. | same full read |
| F7 | Track names are unique (482/482) and ASCII `[A-Za-z0-9-]`; **no collision** between the two sets, so no renaming is required for correctness. | compare track-dir basenames |
| F8 | No song/artist overlap between the two sources (`(title, artist)` exact-normalized set intersection = 0; title-only = 0). | both `catalog.csv` files |
| F9 | Caption rewrite status in yt500: `ok` 417, `fallback` 35, `failed` 6, `single_chunk` 2. All have a non-empty final caption (the 6 "failed" are 1172–1790 chars). fadhl: `ok` 22/22. | `catalog.csv` column `rewrite_status` |
| F10 | The user pasted `percussionâ€”likely`; the **source bytes are correct UTF-8** (em dash `—`). Nothing needs re-encoding; we copy the caption as-is. | byte read of `yt500-0004.../caption.txt` |
| F11 | **280 of 482 captions (58%) explicitly describe vocal content** — "spoken word/sample" 126, "male vocal" 127, "vocal sample" 81, "vocalise" 71, "female vocal" 59, "singing/singer" 36, "vocals" 32, "chant" 16, "choir" 7 (overlapping; 274 yt500, 6 fadhl). 362 captions also contain "wordless/without vocals/no vocals/instrumental". | full read of 482 `caption.txt` + regex counts |

---

## 1. Output (what will exist when done)

### 1.1 Per-track format

Flat, exactly like v3:

```
arabic_instrumental_dataset/
  yt500-0004-xX-bprr9rFo.mp3
  yt500-0004-xX-bprr9rFo.txt
  fs18-hazak_ya_albi_3645837629.mp3
  fs18-hazak_ya_albi_3645837629.txt
  ... (482 pairs)
```

Each `.txt` is generated (source `caption.txt` and `lyrics.txt` are never modified):

```
Middle Eastern fusion, instrumental. <caption.txt, verbatim, stripped>

<caption paragraph breaks inside the caption preserved>
[Lyrics]
[intro]
[verse]
[chorus]
```

Template (byte-exact): `f"Middle Eastern fusion, instrumental. {caption}\n[Lyrics]\n{lyrics}"`
(no trailing newline — same as `prepare_yue2_dataset_v3.py:185`).

- **Section tags are kept** as the `[Lyrics]` block. They are the structural plan the audio was
  generated against (`README.md`: "the 'lyrics' are section tags"), and they keep this dataset
  in the same prompt shape as v3 / the inference prompts.
- Caption paragraphs are preserved (not flattened). A multi-line style block is valid for YuE2's
  `parse_caption` because everything before `[Lyrics]` is style.
- No other rewriting: no dedup, no encoding changes, no tag normalization.

### 1.2 GCS deliverables (mirroring the v3 four siblings)

```
gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/
  arabic_instrumental_dataset.zip               (~3.16 GB, stored, flat root)
  arabic_instrumental_dataset.zip.sha256        `<sha256>  arabic_instrumental_dataset.zip`
  arabic_instrumental_dataset_manifest.json     count, sources, prompt template, per-track records
  arabic_instrumental_dataset_report.md         counts + checks + before/after caption example
```

Manifest per-track record: `out_name`, `source_dataset`, `source_uri`, `audio_bytes`,
`audio_sha256`, `caption_sha256`, `prompt_sha256`, `lyrics_tags`, `caption_status`
(ok/fallback/failed/single_chunk), `caption_vocal_terms` (matched vocal keywords, see F11).
Source URIs make every output byte traceable back to a source object.

---

## 2. Decisions (defaults are my recommendation; reply "go with defaults" to accept all)

| | Decision | Recommendation | Why |
|---|---|---|---|
| D1 | Include a `[Lyrics]` block with the section tags | **Yes** | Matches v3 and the source conditioning; the tags are the only lyrics these instrumentals have. Alternative: style-only prompt (no `[Lyrics]`), which trains a different prompt shape. |
| D2 | Exact prefix | **`Middle Eastern fusion, instrumental. `** (period + one space, then the caption) | Your "becomes" block omitted the prefix — read as a paste slip. D2 pins it. Nothing else is changed. |
| D3 | File naming | **Keep source names verbatim** (`yt500-...`, `fs18-...`) | Already unique, ASCII, collision-free; renaming only adds failure modes. Alternative: lowercase snake_case (`yt500_0004_xx_bprr9rfo`) for uniformity. |
| D4 | The 6 yt500 tracks whose caption rewrite `failed` (plus 35 `fallback`) | **Include all 482**, flag status in the manifest | Captions are non-empty and the audio passed the duration gate; excluding 6 changes the count the user asked for. Easy to filter later from the manifest. |
| D5 | Publish an unzipped copy under `DATASET/` too? | **No** — zip only, like v3 | One canonical copy cannot drift; `setup.sh` already unzips it. (Easy to add later; +3.16 GB.) |
| D6 | Multi-paragraph captions | **Preserve** | No information loss; readable in the report; valid prompt text. |
| D7 | Captions that describe vocals (F11) | **Include all**, record a `caption_vocal_terms` flag in the manifest | The source captioner often writes "spoken word sample", "male vocal", "vocalise" even for instrumental takes; the audio may genuinely contain vocal chops. Filtering 280 tracks would change the requested set. With the flag, a filtered subset can be produced later without a rebuild. |

Unzipped build workspace is local only: `/content/arabic_instrumental_build/` (never
`/content/yue2_dataset`, which stays untouched).

---

## 3. Build pipeline (no GPU)

Everything is CPU/network. Peak local disk ≈ 9.5 GB (sources 3.16 + flat hardlinks ~0 + zip
3.16), free today: 112 GB. Estimated 10–30 min, dominated by 3.16 GB down + 3.16 GB up.

1. **Preflight (read-only).** Re-run the F1/F5/F6 checks as assertions; abort on any: missing
   file, empty caption/lyrics, non-UTF-8, already-prefixed caption, `[Lyrics]` inside caption,
   duplicate name, non-bracket lyric line.
2. **Fetch sources.** `gsutil -m cp -r <prefix>/tracks /content/arabic_instrumental_build/src/<ds>/`
   (audio + the 6 small sidecars; text is read from these local copies).
3. **Assemble flat dir.** For each track: `os.link(src/audio.mp3, out/<name>.mp3)` (hardlink;
   fallback to copy) and write `out/<name>.txt` from the template. Hash in the same pass.
4. **Validate assembled set.** 482 `.mp3` + 482 `.txt`; every `.txt` starts with the prefix,
   has exactly one `[Lyrics]`, has ≥1 bracket tag and no non-tag lyric line; every `.mp3`
   passes `ffprobe` (mp3 stream, duration > 0; total ≈ 36.6 h).
5. **Zip.** `cd out && zip -0 -X -q ../arabic_instrumental_dataset.zip *.mp3 *.txt`
   (stored — mp3 is already compressed, mirrors v3) → `unzip -l` must show **964** entries,
   `unzip -t` must pass, `sha256sum` written beside it.
6. **Manifest + report.** From the build's own records (not re-derived), plus a 3-track
   before/after excerpt.
7. **Upload** the four objects with `gcloud storage cp`.
8. **Verify remote.** size equality; local vs remote `md5` + `crc32c` via `gsutil hash -m`;
   stream the remote zip through `sha256sum` and compare to the `.sha256`; list the four
   objects with sizes/timestamps.
9. **Repo.** Commit `prepare_arabic_instrumental_dataset.py` (same reproducibility rule as v3
   D5) + this plan's executed successor runbook `docs/ARABIC_INSTRUMENTAL_DATASET.md`, then run
   the `docs-reconciler` pass and record it in `RECONCILIATION_LOG.md`. No config change: which
   run consumes this dataset is a separate decision (point `GCP_DATASET_ZIP` at it).

### Commands at execution (long-running, foreground, log to file)

```bash
# 1. fetch sources (~3.2 GB)
mkdir -p /content/arabic_instrumental_build/src
gsutil -m cp -r gs://akbar-december-2024-backup/DATASET/yt500_instrumental/tracks \
  /content/arabic_instrumental_build/src/yt500
gsutil -m cp -r gs://akbar-december-2024-backup/DATASET/fadhl_shaker_instrumental_18_shortlist/tracks \
  /content/arabic_instrumental_build/src/fadhl

# 2. assemble + validate + manifest/report
cd /content/maqamrock-yue2-lora-finetuning
python3 prepare_arabic_instrumental_dataset.py \
  --src /content/arabic_instrumental_build/src \
  --out /content/arabic_instrumental_build/arabic_instrumental_dataset \
  2>&1 | tee /content/arabic_instrumental_build/build.log

# 3. zip + hash
cd /content/arabic_instrumental_build/arabic_instrumental_dataset
zip -0 -X -q ../arabic_instrumental_dataset.zip *.mp3 *.txt
cd .. && unzip -tq arabic_instrumental_dataset.zip && \
  sha256sum arabic_instrumental_dataset.zip > arabic_instrumental_dataset.zip.sha256

# 4. upload (state-changing; shown and confirmed before it runs)
gcloud storage cp arabic_instrumental_dataset.zip \
  gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/
gcloud storage cp arabic_instrumental_dataset.zip.sha256 \
  gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/
gcloud storage cp arabic_instrumental_dataset_manifest.json arabic_instrumental_dataset_report.md \
  gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/
```

Build and validate locally first; the upload is a separate, explicit step.

---

## 4. Must-pass verification checklist

- [ ] 482 tracks; `.mp3`/`.txt` one-to-one; no leftovers.
- [ ] Every `.txt` byte 0 starts with `Middle Eastern fusion, instrumental. `.
- [ ] Exactly one `[Lyrics]` per `.txt`; every following non-blank line is `^\[[^\]]+\]$`.
- [ ] Every `.mp3` decodes (`ffprobe`), duration > 0, total ≈ 36.6 h.
- [ ] 0 duplicate `out_name`; 0 duplicate captions (already true, re-assert).
- [ ] Zip: 964 entries, `unzip -t` OK, size ≈ 3.16 GB, sha256 recorded.
- [ ] Remote sha256 == local sha256; md5/crc32c match; 4 objects present with expected sizes.
- [ ] Spot-check: 3 random `.txt` files printed in the report (prefix + `[Lyrics]` + tags).
- [ ] Source datasets untouched (no write/move/delete in either prefix).

---

## 5. Risks / caveats (not blockers)

1. **Caption distribution differs from v3.** v3 prompts are structured tag lines
   (`arabmaqamrock <genre>. Maqam X. ...`); these are descriptive prose. A model trained on this
   set must be prompted with prose at inference. Do not mix this `.zip` into the v3 config
   without a deliberate decision.
2. **"instrumental" prefix vs vocal descriptions (F11).** 280/482 captions mention a spoken-word
   sample, vocalise, or male/female vocal — inherited from the source captioner, not introduced
   here. The audio may contain vocal chops, and a prompt that says "instrumental" while its own
   caption says "male vocal" is a mild train-time contradiction. Included by default (D7); the
   manifest flag lets you cut a filtered subset later.
3. **Synthetic audio.** Both sources are generated takes, not human recordings; quality varies
   within the source gates. The merge adds no new quality gate; it inherits the sources'.
4. **Caption status flags.** 41 yt500 captions are `fallback`/`failed` rewrites (F9). Visible in
   the manifest; D4 says include.
5. **Near-duplicate concepts.** yt500 has 460 takes over 142 unique section plans (multiple
   takes per song); fadhl has 1 take per song. Not duplicates at the file level.
6. **Section tags as "lyrics".** The block is structural, not sung text — same convention as v3
   and the sources.
7. **No new audio dedup / loudness normalization** is in scope. If wanted, it is a separate pass
   before zipping.

---

## 6. Out of scope

- No training run, no config edit, no GPU work.
- No change to `/content/yue2_dataset`, `prepare_yue2_dataset_v3.py`, or either source dataset.
- No deletion/retirement of any GCS object.
