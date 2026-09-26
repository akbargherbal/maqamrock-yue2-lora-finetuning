# pron_knob_probe — request-option knob probe at ckpt 3050, alpha 0.5

Follow-up to `results/pron_fine_sweep/`: the pron checkpoint (`3050`) and `alpha` (`0.5`) are now **fixed** at the current best-so-far setting, and exactly **one request option** varies per config. 4 configs x 2 held-out maqams = **8 tracks**, strictly sequential.

The comparison anchor is the fine sweep's existing `c3050_a0.5` tracks (identical seed `20260924`, auto cap, staged prompts and binary) — **reused, not regenerated**. Every config uses the same anchor adapters; only the request-option override differs.

## Configs (one knob vs the anchor defaults)

| folder | knob changed | anchor default | value |
|---|---|---:|---:|
| `g1.0` | `guidance_scale` | 1.01 | **1.0** |
| `g1.5` | `guidance_scale` | 1.01 | **1.5** |
| `t0.8` | `semantic_temperature` | 1.0 | **0.8** |
| `rp1.4` | `semantic_repetition_penalty` | 1.2 | **1.4** |

## Tracks

Wall = `/usr/bin/time -v` for the whole `audiocpp_cli` process, from `*_time.txt`.

| config | knob | maqam | cap | duration (s) | wall (s) | truncated | label |
|---|---|---|---:|---:|---:|:--:|---|
| `g1.0` | `guidance_scale=1.0` | Hijaz | 7250 | 227.6 | 174.0 | no | `Hijaz_B` |
| `g1.5` | `guidance_scale=1.5` | Hijaz | 7250 | 223.12 | 241.0 | no | `Hijaz_A` |
| `t0.8` | `semantic_temperature=0.8` | Hijaz | 7250 | 224.72 | 242.0 | no | `Hijaz_D` |
| `rp1.4` | `semantic_repetition_penalty=1.4` | Hijaz | 7250 | 256.64 | 270.0 | no | `Hijaz_C` |
| `g1.0` | `guidance_scale=1.0` | Kurd | 6500 | 203.28 | 154.0 | no | `Kurd_B` |
| `g1.5` | `guidance_scale=1.5` | Kurd | 6500 | 206.64 | 206.0 | no | `Kurd_A` |
| `t0.8` | `semantic_temperature=0.8` | Kurd | 6500 | 192.92 | 195.0 | no | `Kurd_D` |
| `rp1.4` | `semantic_repetition_penalty=1.4` | Kurd | 6500 | 215.8 | 212.0 | no | `Kurd_C` |

Mean wall **211.8 s**, total **1694 s (28.2 min)** — 8 tracks, one L4.

## Resources per generation

Captured per track: `run_one.sh` wraps each render in `/usr/bin/time -v` (`*_time.txt`: wall, max RSS, CPU%) and samples `nvidia-smi` at 1 Hz into `*_gpu.csv` (util, memory.used, power.draw, temperature.gpu); `gpu_logger.py` records the whole run at 10 s. The per-track peaks/means are in the sidecars' `resources` block; this table is the summary.

| config | maqam | max RSS (GiB) | peak VRAM (MiB) | mean VRAM (MiB) | peak util | peak temp | peak power (W) |
|---|---|---:|---:|---:|---:|---:|---:|
| `g1.0` | Hijaz | 6.75 | 10402.0 | 5649.1 | 100.0% | 80.0 | 74.74 |
| `g1.5` | Hijaz | 7.79 | 10348.0 | 6218.0 | 100.0% | 80.0 | 75.09 |
| `t0.8` | Hijaz | 7.79 | 10368.0 | 6233.5 | 100.0% | 80.0 | 75.25 |
| `rp1.4` | Hijaz | 7.79 | 10758.0 | 6328.1 | 100.0% | 80.0 | 81.56 |
| `g1.0` | Kurd | 6.73 | 10038.0 | 5539.1 | 100.0% | 80.0 | 76.88 |
| `g1.5` | Kurd | 7.33 | 10080.0 | 6009.1 | 100.0% | 80.0 | 78.57 |
| `t0.8` | Kurd | 7.33 | 9912.0 | 5983.8 | 100.0% | 80.0 | 74.89 |
| `rp1.4` | Kurd | 7.33 | 10156.0 | 6035.6 | 100.0% | 80.0 | 75.88 |

## Blinded review

`<GCP_BACKUP_BASE>/listening/PRON_KNOB_PROBE_INPUT/` (GCS, not the repo): `Hijaz_{A,B,C,D}.mp3`, `Kurd_{A,B,C,D}.mp3` (ffmpeg 192k, no trim/normalize) + `KEY_open_after_listening.txt`. Label map also at `results/pron_knob_probe/KEY.json`. Per-track sidecars in `results/pron_knob_probe/sidecars/`. Raw WAVs: `/content/pron_knob_probe/<cfg>/` (GCS-mirrored). Decode only after listening.
