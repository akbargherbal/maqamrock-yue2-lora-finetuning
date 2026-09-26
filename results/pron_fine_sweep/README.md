# pron_fine_sweep — fine alpha sweep at checkpoint 3050 (Hijaz + Kurd)

Follow-up to Task 17's `pron_sweep` (5 configs x 4 maqams). Here the pron checkpoint is
**fixed at 3050**, `alpha` is the only variable, and only the two maqams with the clearest
signal are rendered — **Hijaz + Kurd**, 4 alphas x 2 maqams = **8 tracks**.

Task 17's `a0` (v2 baseline) and `c3050_a0.5` (best-so-far) tracks are **reused, not
regenerated**, so this batch carries only 4 labels per maqam (`A..D`), not 5.

`alpha` is the pronunciation-adapter strength folded into the merged AR LoRA
(`W = W_base + 1.0·dW_style + alpha·dW_pron`). Every config is v2 (rank 32, AR+NAR) merged
with the AR-only pron adapter at checkpoint 3050; nonzero alpha -> AR rank 40, NAR
zero-padded to rank 40 (converter's single-rank guard).

## Configs

| folder | pron ckpt | pron step | alpha | converted AR sha256 |
|---|---|---:|---:|---|
| `c3050_a0.2` | 3050 | 3050 | 0.2 | `c68217ab619a9cfa992bbba650f03dd19616ea19fd0967060d0a45e9e415d34c` |
| `c3050_a0.3` | 3050 | 3050 | 0.3 | `dd0d495924c3b533df2fe89cdb5ff82c5a708047c3e3b0bf6ccec42d6033c6e9` |
| `c3050_a0.55` | 3050 | 3050 | 0.55 | `ba328949f995e539bc8d968eaca62b7923ff321c165ef312a2289f8c19ebf53f` |
| `c3050_a0.65` | 3050 | 3050 | 0.65 | `e495beca26aa4e7922b18e03a799b45f0d48e38a2efbe6d662fe3584b17c4d00` |

All four converted NAR files are the same `7d9324bf…` (NAR is copied from v2 and does not
depend on alpha); all four AR hashes are distinct.

## Inputs (reused byte-for-byte from Task 17; only alpha differs)

- Generation seed **20260924** (Task 17's seed). Auto cap.
- Hijaz: `New_Abu_Tammam_16082026` / `05-استجابة-النداء-وامعتصماه-وكرامة-الفرسان`
  (26 lines) -> cap **7250**.
- Kurd: `amin_almanoon_17082026` / `04-مثل-الدهر-الأول-2-مكمن-القانص-ومصرع-الأتن`
  (24 lines) -> cap **6500**.
- Staged prompts `/content/audiocpp_inference/prompts/{Hijaz,Kurd}_{style,lyrics}.txt`
  hash-match Task 17's `sweep_manifest.json` (style `9e201bfb…`/`0e789bfd…`,
  lyrics `1b8dc015…`/`ac29850a…`).
- v2 raw `b1d09098…`, pron 3050 `ead30d52…`; sm89-l4 binary `97028a71…`; NVIDIA L4 (cc 8.9).
- Blinding seed **20260925** (new; labels only).

## Tracks

8/8 `exit=0`, zero failures, **zero cap-truncations**. Wall = `/usr/bin/time -v` for the
whole `audiocpp_cli` process, from `*_time.txt`.

| config | alpha | maqam | cap | duration (s) | wall (s) | truncated | label |
|---|---:|---|---:|---:|---:|:--:|---|
| `c3050_a0.2` | 0.2 | Hijaz | 7250 | 259.2 | 269.8 | no | `Hijaz_C` |
| `c3050_a0.2` | 0.2 | Kurd | 6500 | 199.2 | 197.4 | no | `Kurd_B` |
| `c3050_a0.3` | 0.3 | Hijaz | 7250 | 216.2 | 231.8 | no | `Hijaz_A` |
| `c3050_a0.3` | 0.3 | Kurd | 6500 | 201.0 | 198.8 | no | `Kurd_A` |
| `c3050_a0.55` | 0.55 | Hijaz | 7250 | 193.5 | 212.7 | no | `Hijaz_D` |
| `c3050_a0.55` | 0.55 | Kurd | 6500 | 166.8 | 172.9 | no | `Kurd_C` |
| `c3050_a0.65` | 0.65 | Hijaz | 7250 | 228.4 | 243.0 | no | `Hijaz_B` |
| `c3050_a0.65` | 0.65 | Kurd | 6500 | 229.1 | 221.3 | no | `Kurd_D` |

Mean wall **218.5 s**, total **1747.7 s (29.1 min)** — 8 tracks, one L4. Every render is
full-length; none shows the short collapse `alpha=1.0` produced in Task 17. Per-track WAV
sha256 + sidecars live under `/content/pron_fine_sweep/<cfg>/` (GCS-mirrored); the WAVs are
the untouched originals, the mp3s are 192k review copies made with no trim/normalize/fade.

## L4 arch / kernel check

- Binary in use: `/content/audiocpp_inference/bin/audiocpp_cli`, sha256 `97028a71…`,
  `cuobjdump -lelf`/`-lptx` both show `.sm_89` (native L4 SASS + PTX) — matches the prior
  sweep's binary exactly.
- Every generation log shows `yue2.attention.allow_flash 1` and loads the rank-40 AR
  adapter (`projections=196`, scale 1.0).
- **Note:** the int8 "quantized kernel vs dequant fallback" check
  (`torch._int_mm` W8A8 vs dequantized W8A16) belongs to the AR-loss replay
  (`offline_ar_loss_replay.py`, `docs/PRON_LORA_VERIFICATION.md` §A3b), **not** to this
  `audiocpp_cli` path — generation uses the BF16 GGUF (`yue2-3b-bf16.gguf`), so there is no
  int8 matmul to engage or fall back from. The arch-appropriate check for generation is
  the sm_89 binary + `allow_flash 1`, both verified above.

## Blinded review

`<GCP_BACKUP_BASE>/listening/PRON_FINE_SWEEP_INPUT/` (GCS, not the repo): `Hijaz_{A,B,C,D}.mp3`, `Kurd_{A,B,C,D}.mp3`
(ffmpeg 192k, no trim/normalize) + `KEY_open_after_listening.txt`. Label map also at
`results/pron_fine_sweep/KEY.json`. WAVs stay the untouched originals under
`/content/pron_fine_sweep/<cfg>/` (mirrored to GCS). Decode only after listening.
