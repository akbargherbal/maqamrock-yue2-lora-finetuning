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
- Configs: `config/v3_arabmaqamrock_lora.yml` · `..._l4.yml` (`steps: 5000`,
  `name`/`log_dir` updated).
- Local dataset path unchanged: `/content/yue2_dataset`.

## Latent cache (2026-10-10)
- **Must be built** — `cache_latents_to_disk: true` is mandatory for YuE2 (else it raises
  "needs codec tokens in the latent cache"). Built automatically on the **first launch**,
  before step 1. Not a separate manual step.
- Path (flat dataset): **`/content/yue2_dataset/_latent_cache/`**.
- Cost: **~7 min for the 438** — measured, not extrapolated. The v2 run's own `train.log`
  shows the 267-track latent cache took **04:03** (`Caching latents to disk: 267/267
  [04:03, 1.10it/s]`); v3 is 1.64× the audio duration (30.99 h vs 18.84 h) → ~6:40. On
  **L4** the encode is ~3–4× slower (≈12 min for 267, ≈20 min for 438) — so the docs'
  "~12 / ~20 min" are the **L4** figures (`docs/START.md` is L4-scoped), not an error;
  the **A100** figures are ~4 min (267) / ~7 min (438). **This is GPU work** (YuE2 VAE `conv1d`
  encode + codec tokens on `device: cuda`; `QURAN_AHH_RUN.md:101` "GPU choice is the cache
  lever") — it counts against the one-GPU rule, so `nvidia-smi` before launch. CPU only
  does the per-file `torchaudio.load` decode. A crash mid-build loses the cache progress
  (not resumable unless banked) but no training steps (it's before step 1).
- **NOT saved to GCS** — `backup_to_gcp.py` mirrors run output + `/content/logs` +
  `agent_notes/` only. v2 never banked it; only the two quran runs did (manually).
  Plan's call: rebuild per fresh VM (~7 min) rather than transport it.

### If you want to bank it once (optional, manual — mirrors the quran runs)
```bash
# after the cache is built (first run, before you need it again):
tar -C /content/yue2_dataset -cf - _latent_cache \
  | gcloud storage cp - gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/v3_arabmaqamrock_dataset_latent_cache.tar

# on a fresh VM, after setup.sh has unzipped the dataset:
gcloud storage cp gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/v3_arabmaqamrock_dataset_latent_cache.tar /content/
tar -C /content/yue2_dataset -xf /content/v3_arabmaqamrock_dataset_latent_cache.tar
```
Not wired into `bootstrap/setup.sh` yet — would need a fetch+untar step added.

## Prep timeline (fresh VM → step 1)
| Phase | Measured / est | GPU? |
|---|---|---|
| Notebook: clone repo, stage secrets, vscode tunnel | ~1–3 min (manual) | no |
| `setup.sh --training` — parallel: torch+ai-toolkit, dataset, HF backbone/MERT/tokenizer | **v2 measured 266 s (~4.5 min)**; v3 zip is 2.5 GB → **~5–7 min** | no (verify block does one tiny cuDNN conv) |
| Start sidecars | ~10 s | no |
| `train_ctl.py start` → model load + latent cache | **~7–10 min** on A100 (cache ~7 + load ~1–3); ~20–25 min on L4 | **yes** |
| step-0 sample | **0** (`disable_sampling: true`; v2's was 9:43) | — |
| **→ first training step** | **~15 min total** (~8–10 min GPU) | |

Source for setup: v2 `logs/setup.log` → `total 266s`. Source for cache: v2 `logs/train.log`
→ `Caching latents to disk: 267/267 [04:03, 1.10it/s]`, ×1.645 for 438.

## Next: launch training (fresh VM, you type it)
1. Notebook exports `GCP_DATASET_ZIP` → `bash bootstrap/setup.sh --training`.
2. Sidecars: `backup_to_gcp.py --run-name v3_arabmaqamrock_lora` + `gpu_logger.py`.
3. `python train_ctl.py start --config config/v3_arabmaqamrock_lora.yml`.
   (~5000 steps ≈ 4.75 h on A100; latent cache rebuilds ~7 min first.)

## Open
- Held-out eval set is **stale vs v3** (3/4 contaminated) — regenerate before any eval.
- `sample.samples` in the configs are stale and inert (`disable_sampling: true`).
- Cache times are **GPU-specific**: docs say ~12 min (267) / ~20 min (438) = **L4**;
  A100 measured ~4 min (267) / ~7 min (438). `docs/START.md` doesn't label the GPU —
  optional clarifying edit only (not a factual error).
