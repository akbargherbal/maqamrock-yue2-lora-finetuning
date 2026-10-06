# jarir_qahh — maqamrock × `quran_ahh_r8` (AR+NAR) α sweep

Merge the Quran pronunciation LoRA `quran_ahh_r8` (final, AR+NAR rank 32) into the frozen
maqamrock style adapter (v2, AR+NAR rank 32) at **α 0 / 0.1 / 0.2 / 0.3**, then blind-listen on a
held-out Jarir poem for pronunciation sharpening **without** Quranic-style bleed.

## Why a new merge tool

`merge_pron_lora.py` merges an **AR-only** donor (keeps v2's NAR, hard-errors on any
`diffusion_model.*` key). `quran_ahh_r8` is **AR+NAR** — the revised run trained the NAR because
"the NAR flow + VAE render the actual articulation". So `merge_quran_lora.py` (repo root, new) folds
**both** branches: rank concat `32+32 → 64` on AR *and* NAR, α folded into `B_quran` (same convention
as `PRON_LORA_MERGE.md`). α0 = v2 verbatim (verified: all 392 AR + 392 NAR tensors byte-identical to
the live converted v2).

## Sources

| input | sha256 |
|---|---|
| v2 fused style (`loras/source/akbar_arabic_rock_lora.safetensors`) | `b1d090987355303129a3765d257e61c983b91d48cecb8a30aa424e09cdd24cd4` |
| quran final (`quran_ahh_r8/output/quran_ahh_r8.safetensors`) | `7e82aaf490d0e30adeedfaa4c3d4e40ad318a3327dcacddbe8b3cf9292c314a4` |

## Variants

| folder | α | merged sha256 | converted AR sha256 (rank 64) |
|---|---:|---|---|
| `qahh_a0` | 0.0 | `163cd17e9137e2620731e76eeea3bbc2c399b260977f8bd7efc0e58e91e3c579` | `0e4b710dfbd84d50e0171d24c90b21f46c9d2c82a41bfcac939e73a24e09ab11` |
| `qahh_a0p1` | 0.1 | `f38137b6889347a76c23222c7e06f94525075a3934de485595f55fdbd9d5b7f5` | `4b4d2103e59de6b3279088d53cb28b15df901f96e4a37a67e2306e9bfdac0ecb` |
| `qahh_a0p2` | 0.2 | `033489148a0f52b7969aa4061931ea90cba6a6d18fd5409aaa8a3f1b98472740` | `410daba1f67247cfdb2c0fb49f44b97a3b19317019a2dbd43df095030a826174` |
| `qahh_a0p3` | 0.3 | `57d3e19fd29801accf5f265ce782f53b728fde2664bbb2adbc18139c31075c3a` | `ddb3b2da4f6dfe7fc8a1479481f8e21901af98bfa6d6eea73491cf2873d3c2ac` |

Merged + converted artifacts mirrored to
`$GCP_BACKUP_BASE/quran_ahh_r8_rank32/maqamrock_merge/{merged,convert/}`.

## Prompt

`/content/jarir_poets_poison.json` — one Jarir poem, **verbatim Suno style** (meta tags kept) with
the `arabmaqamrock` trigger prepended by `generate.py`; lyrics verbatim except the `///***///`
separator dropped. Auto cap at q0.95 = 6500 (484 Arabic letters).

## Round A — fixed seed `20261006`

Run dir `/content/audiocpp_inference/out/jarir_poets_qahh/` (cap 6500).

| arm | α | exit | wall | WAV dur | truncated |
|---|---:|---:|---:|---:|---|
| jarir_a0 | 0 | 0 | 8:47 | 204.8 s | no |
| jarir_a0p1 | 0.1 | 0 | 10:30 | 212.0 s | no |
| jarir_a0p2 | 0.2 | 0 | 11:51 | 260.0 s | **yes** (6500 tok) |
| jarir_a0p3 | 0.3 | 0 | 9:26 | 177.8 s | no |

α0.2 hit the cap, so it was **re-rendered** at cap 8000 (same seed/adapter:
`/content/audiocpp_inference/out/jarir_a0p2_hi/`, exit 0, 12:27, 264.7 s, `truncated 0`, 6618 tok).
The other three self-terminated.

## Benchmark — Colab **free T4** (2 vCPU, 12.7 GB RAM, no swap)

| track | α | wall | max RSS | CPU % | GPU util | GPU mem | power | temp | AR load |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| jarir_a0 | 0 | 8:47 | 7.66 GB | 96 % | 63 % | 9,941 MB | 53 W | 82 °C | 96.5 s |
| jarir_a0p1 | 0.1 | 10:30 | 7.95 GB | 102 % | 55 % | 10,025 MB | 52 W | 83 °C | 140.7 s |
| jarir_a0p2 | 0.2 | 11:51 | 7.95 GB | 100 % | 60 % | 10,597 MB | 54 W | 83 °C | 138.8 s |
| jarir_a0p3 | 0.3 | 9:26 | 7.95 GB | 103 % | 50 % | 9,621 MB | 50 W | 83 °C | 143.1 s |

CPU-bound (GPU util 50–63 %; `run_one.sh` passes `--threads 8` to a 2-vCPU box). The rank-64 merges
load ~45 s slower than v2. Reference (prior T4, `docs/INFERENCE.md`): 389.6 s/track → this box ≈ 1.6×.

## Blind package

`$GCP_BACKUP_BASE/listening/JARIR_QAHH_INPUT/` — 4 × 192k mp3 + `EVAL.txt` (public) + `KEYS.txt`
(secret). **Blinding seed `20261008`**; label→variant map in [`KEY.json`](KEY.json). A/B/C/D over the
same lyrics/style; only the adapter differs (α0.2 from the cap-8000 re-render).

## Round B — random seed per arm

Run dir `/content/audiocpp_inference/out/jarir_poets_qahh_rand/`, cap 8000, one fresh random seed
per arm (recorded in its `batch_manifest.json`). Status: **pending**.
