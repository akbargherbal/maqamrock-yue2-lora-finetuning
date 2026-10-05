# current

## State @ 2026-10-05 — `quran_ahh_r8` config REVISED; ready for a fresh L4 run

Branch `pron-lora-long-aya`. Config `config/quran_ahh_r8.yml` was **replaced in place**
(no new config file) to fix the AR-only / rank-8 run, which could only move recitation
*prosody* (madd/waqf) but not the makhraj. Root cause: in YuE2 the AR picks the discrete
semantic codes, but the **NAR flow + VAE render the actual articulation**; freezing the
NAR at the music base leaves the phonemes unadapted (and pushes the frozen NAR
off-distribution). Adapt **both** experts (v2's shape).

| key | old | new |
|---|---|---|
| `network.linear` / `linear_alpha` | 8 / 8 | **32 / 32** |
| `network_kwargs.ignore_if_contains` | `["transformer.nar"]` | **`[]`** (AR + NAR) |
| `model_kwargs.ar_kl_weight` | 0.2 | **0.0** |
| `train.steps` | 9489 (1 epoch) | **28467** (3 epochs) |

lr 1e-4, adamw8bit, EMA 0.999, `cot: off`, `train_window_frames: 0`, the data path, and
the run name `quran_ahh_r8` are unchanged. Committed `674be03`.

## Next session (fresh L4) — exactly this

1. `git checkout pron-lora-long-aya`; `bash bootstrap/setup.sh --training`.
2. Restore the dataset **and reuse the banked latent cache** — the cache stores frozen
   VAE latents + MERT semantic tokens, keyed only on dataloader/base-latent settings, so
   **rank/scope/KL/steps do not invalidate it**; the rank-8 cache is still valid and
   saves the ~50 min encode:
   ```bash
   gcloud storage cp "$GCP_BACKUP_BASE/quran_ahh_dataset.zip" /content/ && unzip -q /content/quran_ahh_dataset.zip -d /content/
   gcloud storage cp "$GCP_BACKUP_BASE/quran_ahh_dataset/_latent_cache.tar" - | tar -C /content/quran_ahh_dataset/train -xf -
   find /content/quran_ahh_dataset/train/_latent_cache -name '*.safetensors' | wc -l   # expect 9489
   ```
   (Or export `GCP_AHH_DATASET_ZIP` and let `setup.sh`'s `job_ahh_dataset` unzip it.)
3. **Do NOT restore `quran_ahh_r8/output/`** — those are rank-8 AR-only adapters,
   incompatible with the new rank-32 AR+NAR network. `/content/ai-toolkit/output/quran_ahh_r8/`
   must be empty/absent for a fresh start (local, not GCS, triggers auto-resume).
4. `nvidia-smi` idle → start sidecars (backup + gpu logger) → launch:
   ```bash
   python train_ctl.py start --config config/quran_ahh_r8.yml --run-name quran_ahh_r8 --log-name train_quran_ahh
   ```
5. Confirm a **cache hit** (no full re-encode) and steps starting. If it re-encodes all
   9,489, STOP and flag — that means the cache hash changed (a dataloader field differs).
6. Per-checkpoint offline eval on held-out 2:255 with the **trained NAR** (not NAR=0 —
   a lone-AR rendering throws away the renderer we are now training).

## Open items
- `docs/QURAN_AHH_RUN.md` §1/§2/§5 updated for the revised config; `ANALYSIS.md` remains the
  record of the *old* rank-8 run.
- `results/quran_pt_gate/` is untracked (contains `KEY.json`, the blind-eval decoder) — not pushed.
