# pron_ckpt_sweep — pron checkpoints 1525 vs 4575 at alpha 0.5 (Hijaz + Kurd)

Renders the two not-yet-shipped pron checkpoints at the already-shipped `alpha=0.5`,
on the same held-out inputs as `results/pron_fine_sweep/` (same staged prompts, same
generation seed `20260924`, same auto cap). 2 configs x 2 maqams = **4 tracks**,
strictly sequential.

`alpha` is the pronunciation-adapter strength folded into the merged AR LoRA
(`W = W_base + 1.0·dW_style + alpha·dW_pron`). Every config is v2 (rank 32) merged with
the AR-only pron adapter at the given checkpoint; nonzero alpha -> AR rank 40, NAR
zero-padded to rank 40.

## Configs

| folder | pron ckpt | alpha | converted AR sha256 |
|---|---:|---:|---|
| `c1525_a0.5` | 1525 | 0.5 | `3324b63706a3a58ea89159250850a3bcab1fbcb851abcaffb7ae0d9d260f534c` |
| `c4575_a0.5` | 4575 | 0.5 | `ebd22026495125e74ab48373ad0ce8a8d767cdb625e018affc38c24b1fc3e56d` |

All converted NAR files are `7d9324bf…` (copied from v2).

## Tracks

Wall = `/usr/bin/time -v` for the whole `audiocpp_cli` process, from `*_time.txt`.

| config | alpha | maqam | cap | duration (s) | wall (s) | truncated | label |
|---|---:|---|---:|---:|---:|:--:|---|
| `c1525_a0.5` | 0.5 | Hijaz | 7250 | 231.4 | 300.0 | no | `Hijaz_B` |
| `c1525_a0.5` | 0.5 | Kurd | 6500 | 222.4 | 220.8 | no | `Kurd_B` |
| `c4575_a0.5` | 0.5 | Hijaz | 7250 | 200.6 | 223.0 | no | `Hijaz_A` |
| `c4575_a0.5` | 0.5 | Kurd | 6500 | 247.4 | 241.6 | no | `Kurd_A` |

Mean wall **246.3 s**, total **985.4 s (16.4 min)** — 4 tracks, one L4.

## Blinded review

`<GCP_BACKUP_BASE>/listening/PRON_CKPT_SWEEP_INPUT/` (GCS, not the repo): `Hijaz_{A,B}.mp3`, `Kurd_{A,B}.mp3`
(ffmpeg 192k, no trim/normalize) + `KEY_open_after_listening.txt`. Label map also at
`results/pron_ckpt_sweep/KEY.json`. Per-track sidecars in `results/pron_ckpt_sweep/sidecars/`.
Raw WAVs + adapters: `/content/pron_ckpt_sweep/`.
