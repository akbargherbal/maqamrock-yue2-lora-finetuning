# Quran pron LoRA alone (α=1) on the base model

Status: **first sample generated 2026-10-04** (branch `experimental-quran-pron`). This doc is
the durable record of the experiment; the live next-step handoff is `agent_notes/current.md`.

## Goal

Hear the pronunciation adapter **by itself** — no v2 style LoRA — at full strength (α=1) on
the base YuE2 model, and judge it on articulation. Every current library candidate is a
*merge* (`qfinal_a0.3`/`a0.5` = v2 style + Quran pron), so the adapter's isolated effect was
untested. Background/why: `docs/FUTURE_PRONUNCIATION_LORA.md`, `docs/LORA_INVENTORY.md`.

## Why "α=1" needs no scaling

The Quran adapter (`quran_long_aya_r8_s10`) is **AR-only, rank 8** — config
`config/quran_long_aya_r8_s10.yml` (`linear/linear_alpha 8/8`,
`network_kwargs.ignore_if_contains: ["transformer.nar"]`). Pronunciation lives in the **AR**
expert; NAR is timbre/rendering. Trained `alpha == rank`, so the saved delta is already
`B @ A` at full strength: **converting the raw file verbatim *is* the α=1 arm.** No
`merge_pron_lora.py` call — merging would re-introduce v2's AR and defeat the test.

## Building the lone adapter (the converter requires both branches)

The audio.cpp converter **needs an AR *and* a NAR branch**. A direct convert of the AR-only
pron file fails:

```
ERROR: NAR branch: missing [(0,'mlp.down_proj'), …] (expected 28 layers x 4 modules)
```

Workaround (script: `build_pron_only_fused.py`, repo root): build a fused file whose
**AR = pron verbatim** and **NAR = zeros** at the same rank (the zero NAR is a no-op ⇒ base
NAR), then convert that.

```bash
export GCP_BACKUP_BASE=gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning
mkdir -p /content/pron_src /content/v2_src
# pron final (AR-only rank 8)
gsutil cp "$GCP_BACKUP_BASE/quran_long_aya_r8_s10/output/quran_long_aya_r8_s10.safetensors" /content/pron_src/
# fused v2 (for NAR key names/shapes only)
gsutil cp "$GCP_BACKUP_BASE/loras/source/akbar_arabic_rock_lora.safetensors" /content/v2_src/

python build_pron_only_fused.py \
  --pron /content/pron_src/quran_long_aya_r8_s10.safetensors \
  --v2   /content/v2_src/akbar_arabic_rock_lora.safetensors \
  --out  /content/quran_only_build/quran_long_aya_r8_s10_zeronar.safetensors

python /content/converter/out/convert_aitoolkit_yue2_lora.py \
  /content/quran_only_build/quran_long_aya_r8_s10_zeronar.safetensors \
  --out-dir /content/converter/out/quran_only --stem quran_long_aya_r8_s10
# -> quran_long_aya_r8_s10_ar.safetensors (rank 8, real) / _nar.safetensors (rank 8, zeros)
```

## First sample (2026-10-04, T4)

First song of `manifests/batch_36_songs.json` (`07-الحر-الشديد-وقطع-القفر-والوعول`); its
per-song style block replaced with the unaccompanied-recitation caption:

> `Solo male voice, unaccompanied. Quran recitation. Clear precise classical Arabic diction. Spoken Words.`

Lyrics kept, cleaned by the repo's `suno_to_songs.clean_lyrics` (drop `///***///`, collapse
`[Section | …]` → `[Section]`). Driven by `INFERENCE/generate.py --no-trigger` (no
`arabmaqamrock ` prefix) with the `quran_only` alias (AR scale 1.0, NAR scale 0.0), seed
`20261004`, auto cap 7500.

**Result:** exit 0, wall 1:52, **52.2 s** WAV, `truncated=false`.
- wav: `/content/audiocpp_inference/out/quran_only_sample/07-الحر-الشديد-وقطع-القفر-والوعول_20261004.wav`
  (sha256 `ff21ed9f74fc2884ba5465aecfdedf0bd575a8727989887ef24738a0681464c2`), GCS-mirrored
  under `audiocpp_inference/out/quran_only_sample/`.
- converted AR sha256 `a739a0f1b18a00dd8a95aa71c0c300a5896064ed42fa7db27ffdcf6289cafb57`;
  pron source `f8c842e4…`; fused v2 source `b1d09098…`.

### Finding: the track self-terminates early (≈52 s, one aya-length)

The CLI log shows a **natural end-of-sequence**, not a cap:

```
yue2.sampling.semantic … min_tokens=200 max_tokens=7500
yue2.semantic.tokens 1304
yue2.semantic.truncated 0        # 0 = model-chosen EOS, not the 7500 cap
```

Cause (reasoned from the training data, not measured here): the adapter is **AR-only**, and
AR controls sequence length. Its training clips were single long-ayat recitations filtered to
`min_words=6, max_words=60` (`docs/PRON_LORA_LONG_PLAN.md:36`; config comment
`quran_long_aya_r8_s10.yml:116`), averaging **~23 s** (`PRON_LORA_LONG_PLAN.md:120`). So it
recites roughly one such passage (~1300 tokens ≈ 52 s) and stops. v2's AR, trained on whole
~220 s songs, is why the merged candidates run long. **Raising the cap cannot help**
(`truncated 0`). To render a full poem, chunk the lyrics to the training length and stitch
several takes — that is the adapter behaving in-domain.

## Arms (for the comparison)

| Arm | AR | NAR | note |
|---|---|---|---|
| base | off | off | model's own articulation ceiling |
| **quran-alone** (done) | Quran 1.0 | off | this doc |
| quran-AR + v2-NAR | Quran 1.0 | v2 1.0 | isolates the AR swap, keeps arabmaqamrock timbre |
| `qfinal_a0.5` | merged 1.0 | merged 1.0 | shipping control |

`INFERENCE/run_one.sh` reads `LORA_AR_SCALE` / `LORA_NAR_SCALE` (default 1.0; 0 = off).

## Gotchas hit

- **Converter needs both branches** — see above; `build_pron_only_fused.py`.
- **CUDA-13 image ⇒ binary needs CUDA-12 libs on `LD_LIBRARY_PATH`.** The prebuilt sm_75
  `audiocpp_cli` links `libcublas.so.12`/`libcudart.so.12`; on a CUDA-13 Colab image it dies
  instantly with `exit=127` unless the pip `nvidia-*-cu12` lib dirs are on the loader path.
  Details + fix: `docs/COMMAND_HANDOVER_GOTCHAS.md` (2026-10-04).
