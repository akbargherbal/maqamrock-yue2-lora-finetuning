# current.md — v3 dataset built + repo reconciled (2026-10-10)

**Done this session (no GPU used).**

## Dataset
- Built **v3 = 438 tracks** (Ajam 118 · Hijaz 107 · Kurd 101 · Nahawand 112), verbatim lyric
  tags, Suno header stripped, 3 surgical `vocals` overrides. Strict superset of v2 (267+171).
- Local: `ostris_prepare_dataset/v3_arabmaqamrock_dataset/` + `.zip`.
  sha256 `5b5624ee4bc03dcb9d89450a9e2a81871343ddd59558f9a24e98f4ca49e7830f`.
- GCS: renamed **`dataset/` → `v2_arabmaqamrock_dataset/`** (534 objects, CRC-verified);
  uploaded **`v3_arabmaqamrock_dataset.zip`** (+ `.sha256`, `manifest.json`, `report.md`).
  Upload verified: size 2530501579 + CRC32C `beq20A==` match.

## Naming (decided)
- Runs: **`v3_arabmaqamrock_lora`** (A100) · **`v3_arabmaqamrock_lora_l4`** (L4).
- Configs: `config/v3_arabmaqamrock_lora.yml` · `..._l4.yml` (staged from the A100/L4 variants;
  `steps: 5000`, `name`/`log_dir` updated).
- Local dataset path unchanged: `/content/yue2_dataset`.

## Code/doc changes (staged → applied)
- `bootstrap/setup.sh`: new **`GCP_DATASET_ZIP`** path (`cp`+unzip) vs `GCP_DATASET_PATH`
  (folder); dataset count check = 438 only in zip mode.
- Notebook: `GCP_DATASET_PATH` → v2 prefix; added `GCP_DATASET_ZIP`.
- `backup_to_gcp.py`, `README.md`, `SOURCE_OF_TRUTH.md`, `docs/README.md`, `docs/START.md`,
  `docs/PRON_LORA*.md`, `text_to_duration_formula.md`, `INFERENCE.md`, held-out report,
  `DECISIONS.md` (dated entry).
- Added `prepare_yue2_dataset_v3.py` + `datasets/v3_arabmaqamrock/{README,manifest,build_report,v3_overrides}`.

## Next: launch training (fresh VM, you type it)
1. Notebook exports `GCP_DATASET_ZIP` (already set) → `bash bootstrap/setup.sh --training`.
2. Sidecars: `backup_to_gcp.py --run-name v3_arabmaqamrock_lora` + `gpu_logger.py`.
3. `python train_ctl.py start --config config/v3_arabmaqamrock_lora.yml`.
   (~5000 steps ≈ 4.75 h on A100; latent cache rebuilds ~20 min.)

## Open
- Held-out eval set is **stale vs v3** (3/4 contaminated) — regenerate before any eval.
- `sample.samples` in the configs are stale and inert (`disable_sampling: true`).
