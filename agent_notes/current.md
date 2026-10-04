# current

## State @ 2026-10-04 (CPU VM) — AHH training dataset BUILT

Branch `experimental-quran-pron`, HEAD `4fea54f`. No training, no GPU, no config
edited. Untracked: `prepare_ahh_quran_dataset.py`. This file = the decision log
for the next run.

### Dataset — BUILT + validated (`/content/quran_ahh_dataset`)

- Source: GCS `…/AHH_Quran_Long_Aya_Filtered_DATASET.zip`, downloaded, **sha256
  verified** (`d30beae0…5509e`), unzipped to
  `/content/AHH_Quran_Long_Aya_Filtered_DATASET` (9,492 mp3, 3 reciters).
- Builder: `prepare_ahh_quran_dataset.py` (NEW; the documented
  `prepare_pron_dataset.py` reconstruction is left intact).
- **train 9,489 · val 6 · smoke 0.** Single caption per clip, 50/50
  simple/uthmani **stratified per reciter** (AB 1199/1199 · Hudhaify 2071/2071 ·
  Husary 1474/1475). Held-out **2:255** (3 clips × both scripts) in `val/`, and
  confirmed **absent from train**. Audio **hardlinked** to the source (dataset dir
  = ~3.7 MB of `.txt`); last-word gate is a no-op (0 clips outside 6–60 words).
- Caption template: `{style}\n[Lyrics]\n[Verse]\n{aya} ۝\n`.
- Style line **in use** (user asked for audio-faithful wording, not s10 parity):
  `Solo male voice, unaccompanied. Quran recitation in murattal style. Classical Arabic with tajwīd, precise articulation. Spoken Words.`
- Validation: 0 problems — every mp3 has a same-stem txt; every aya line reproduces
  Tanzil (NFC) + ` ۝`; save `selection_report.json` + `captions_manifest.jsonl`.
- **Banked to GCS** (2026-10-04): `gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/quran_ahh_dataset.zip`
  (3.69 GiB; sha256 `8c68d6844d7c9ee87ca69956dfcb70419e234a3197043b41526833e81a3e9ff9`,
  also at `…/quran_ahh_dataset.zip.sha256`). Local zip on the VM: `/content/quran_ahh_dataset.zip`.
  Restore: `gcloud storage cp <zip> /content/ && unzip -q /content/quran_ahh_dataset.zip -d /content/`.

Rebuild (captions only; audio hardlinked):
`python prepare_ahh_quran_dataset.py --audio-root /content/AHH_Quran_Long_Aya_Filtered_DATASET --simple quran_text/quran-simple.json --uthmani quran_text/quran-uthmani.json --out /content/quran_ahh_dataset --jobs 16`

### Next (in order)

1. ~~Bank the dataset to GCS~~ **DONE** (zip sha `8c68d684…e9ff9`).
2. **Confirm final name.** Currently `quran_ahh_dataset` (dataset + run proposal
   `quran_ahh_r8`). If renamed, rename the folder + rezip + re-push + update this file.
3. **User OK / edit the style line.** If changed: rerun the builder (rewrites 9,489
   `.txt` in seconds; audio untouched), rezip, re-push.
4. **Config (user's to write):** new run identity; `steps: 9489` (= 1 epoch);
   keep rank 8/8 · lr 1e-4 · `ar_kl_weight` 0.2 · EMA 0.999 · `cache_latents_to_disk: true`.
5. **Phase 1 base-model ceiling probe gates any GPU training** (`QURAN_PRON_REVIEW.md` §5).
   No training until that verdict.

### Open / residual

- Kind=91 `aya-1` clips (sura≠1,9) may carry a recited basmala not in the caption
  (text/audio alignment; not fixable from metadata).
- `docs-reconciler` pass + commit outstanding (new script + this change).
