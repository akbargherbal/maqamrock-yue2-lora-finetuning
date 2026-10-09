# quran_ahh_epochs — end-of-epoch checkpoints on Ayat al-Kursi (2:255)

Phase 3b of `docs/QURAN_AHH_RESUME_PLAN.md`: one checkpoint per epoch, free-run on the
held-out ayah **2:255** at a fixed seed, then a blind A/B/C listen. Exact epoch ends
(9,489 / 18,978 / 28,467) don't land on saves (`save_every: 1500`); `c9000`/`c19500` are
the nearest, `final` is exact.

## Variants

| folder | ≈ epoch | step | source checkpoint | converted AR sha256 |
|---|---:|---:|---|---|
| `c9000`  | end 1 | 9,000  | `quran_ahh_r32_000009000.safetensors` | `1220f386539656f5…` |
| `c19500` | end 2 | 19,500 | `quran_ahh_r32_000019500.safetensors` | `4e7a183a78751972…` |
| `final`  | end 3 | 28,467 | `quran_ahh_r32.safetensors` (un-suffixed) | `c9305c35798c5453…` |

Converted with `audiocpp_inference/converter/convert_aitoolkit_yue2_lora.py --stem
quran_ahh_r32` (rank 32, AR+NAR real, byte-level verified) and banked under
`$GCP_BACKUP_BASE/quran_ahh_r32/convert/{c9000,c19500,final}/`. Full hashes live in
that prefix's `adapter_manifest.json`.

## Run

`INFERENCE/quran_pt_probe.py --prefix quran_ahh_r32/convert --arms c9000,c19500,final`
— 3 arms × {uthmani, simple} = **6 tracks**; model seed `20261004`,
`semantic_max_tokens 7500`, `cot=off`, `yue2.attention=flash`, bf16 GGUF, sm_75 binary, T4.
Run dir: `$GCP_BACKUP_BASE/audiocpp_inference/out/20261006-052626_quran_pt_probe/`.
All 6 `exit=0`, no truncation, total wall 14:12.

## Blind package

`$GCP_BACKUP_BASE/listening/QURAN_AHH_EPOCHS_INPUT/` — 6 × 192k mp3 (untouched),
`EVAL.txt` (public) + `KEYS.txt` (secret). Blinding seed **20261006**,
`shuffle_per=category` (labels consistent across both scripts):

| label | variant |
|---|---|
| A | `final` (epoch 3, step 28,467) |
| B | `c9000` (≈epoch 1) |
| C | `c19500` (≈epoch 2) |

Decode from `KEY.json` / `KEY_open_after_listening.txt`. **Not yet listened** — no adapter
is "best" before the listen (`AGENTS.md` §5).

## Provenance

- Run config (authority): `config/quran_ahh_r32.yml` — AR+NAR, rank 32, `ar_kl_weight 0.0`,
  `steps 28467`, saved adapters = EMA.
- Training analysis: `TRAINING_ANALYSIS/quran_ahh_r32/ANALYSIS.md` (loss plateaued
  after ~19.5k — "later is better" is a listening question, not a loss one).
- The CUDA-12 loader fix that made this render runnable at all: commit `72297f0`.
