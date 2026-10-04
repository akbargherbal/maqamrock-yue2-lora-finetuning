# current

## State @ 2026-10-04 (CPU VM) — AHH dataset BUILT, config drafted

Branch `pron-lora-long-aya` (renamed from `experimental-quran-pron`, 2026-10-04);
`main` = `d345a9b` (do NOT merge this long-aya work there). No training, no GPU.
Config `config/quran_ahh_r8.yml` DRAFTED — 4 diffs vs the s10 config: `name`,
`log_dir`, `datasets[0].folder_path`, `steps: 9489`; all hyperparameters unchanged.
This file = the decision log for the next run.

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
2. **Config** `config/quran_ahh_r8.yml` drafted; review/adjust before launch.
3. **Offline eval**: adapt `INFERENCE/pron_ckpt_sweep.py` to free-run held-out 2:255
   per checkpoint (the run has `disable_sampling: true`).
4. **Phase 1 base-model ceiling probe gates any GPU training** (`QURAN_PRON_REVIEW.md`
   §5). No training until that verdict.
5. **First GPU session**: restore dataset from `quran_ahh_dataset.zip`, sidecars,
   launch `quran_ahh_r8`; latent-cache build ~2.4 h on an L4 — bank it when done.

### Open / residual

- 91 `aya-1` clips (sura≠1,9) may carry a recited basmala not in the caption
  (text/audio alignment; not fixable from metadata).
- 3 docs still say `experimental-quran-pron` (`PROGRESS.md`,
  `docs/QURAN_FORMAT_PROBE.md`, `docs/QURAN_ONLY_EXPERIMENT.md`); stale
  `pron-lora-long` branch still exists (ancestor of this one).
- `docs-reconciler` pass outstanding (new builder + config not yet in the docs index).
