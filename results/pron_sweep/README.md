# pron_alpha_sweep — L4 results (Task 17)

20 songs = 5 merged-LoRA configs × 4 held-out maqams, seed **20260924**, auto cap, generated sequentially on an **NVIDIA L4** (sm_89). Built 2026-09-24 14:55 UTC.

`alpha` is the pronunciation-adapter strength folded into the merged AR LoRA (`W = W_base + 1.0·dW_style + alpha·dW_pron`). All five are v2 (rank 32, AR+NAR) merged with the AR-only pron adapter; non-zero alpha → AR rank 40.

## Configs

| folder | pron ckpt | pron step | alpha | converted AR sha256 |
|---|---|---:|---:|---|
| `a0` | final | 6100 | 0 | `747d5cfe2224b1bae6e582ccf5f2ee2a57e3f030c53d54e134f34a85960426fa` |
| `c3050_a0.5` | 3050 | 3050 | 0.5 | `33e824f24f1eec1ab06a45365e93a19b078a2a7cfbea724eba1b908d27360509` |
| `c3050_a1.0` | 3050 | 3050 | 1 | `b4868133ad8094f898002aa28b311f9965f44ef37ffb84afa74000f8ef90b781` |
| `cfinal_a0.5` | final | 6100 | 0.5 | `525d3af25dfcddabbd587673c36dfaecd148cf97a0dfc6d90cbede15ed700ada` |
| `cfinal_a1.0` | final | 6100 | 1 | `394ff2ca8dc65f464a88217eada72353400d51563a9fdbe258622cda7006f0f2` |

## L4 benchmark

Wall = `/usr/bin/time -v` for the whole `audiocpp_cli` process (model load + generation), per `*_time.txt`.

| metric | value |
|---|---|
| tracks measured | 20 |
| **mean wall** | **174.6 s (2.91 min)** |
| median | 199.2 s |
| min / max | 71.2 / 257.9 s |
| total (driver span) | 3495 s (58.2 min) |
| throughput | ~20.6 tracks/hour |

Per config (mean wall):

| config | mean wall (s) |
|---|---:|
| `a0` | 235.4 |
| `c3050_a0.5` | 215.2 |
| `c3050_a1.0` | 106.6 |
| `cfinal_a0.5` | 208.9 |
| `cfinal_a1.0` | 107.2 |

Per maqam (mean wall):

| maqam | cap | mean wall (s) |
|---|---:|---:|
| Hijaz | 7250 | 186.6 |
| Kurd | 6500 | 168.1 |
| Nahawand | 7000 | 180.6 |
| Ajam | 6500 | 163.3 |

**vs T4:** the T4 benchmark in [`docs/INFERENCE.md`](../../docs/INFERENCE.md) is mean **389.6 s** (median 380.2, ~9 tracks/hour) on the same model/LoRA setup. The L4 is ~**2.2×** faster here (mean 175 s). Much of that is fewer/short generations self-terminating early, so treat the ratio as setup-specific, not a pure hardware measure.

## Tracks

| config | alpha | pron ckpt | maqam | cap | duration (s) | wall (s) | truncated |
|---|---:|---|---|---:|---:|---:|:--:|
| `a0` | 0 | final | Hijaz | 7250 | 247.7 | 257.9 | no |
| `c3050_a0.5` | 0.5 | 3050 | Hijaz | 7250 | 223.0 | 241.0 | no |
| `c3050_a1.0` | 1 | 3050 | Hijaz | 7250 | 12.7 | 71.2 | no |
| `cfinal_a0.5` | 0.5 | final | Hijaz | 7250 | 227.4 | 246.4 | no |
| `cfinal_a1.0` | 1 | final | Hijaz | 7250 | 72.6 | 116.8 | no |
| `a0` | 0 | final | Kurd | 6500 | 214.6 | 208.1 | no |
| `c3050_a0.5` | 0.5 | 3050 | Kurd | 6500 | 197.4 | 199.2 | no |
| `c3050_a1.0` | 1 | 3050 | Kurd | 6500 | 130.6 | 150.3 | no |
| `cfinal_a0.5` | 0.5 | final | Kurd | 6500 | 202.9 | 204.9 | no |
| `cfinal_a1.0` | 1 | final | Kurd | 6500 | 30.2 | 77.8 | no |
| `a0` | 0 | final | Nahawand | 7000 | 239.8 | 241.6 | no |
| `c3050_a0.5` | 0.5 | 3050 | Nahawand | 7000 | 204.6 | 216.9 | no |
| `c3050_a1.0` | 1 | 3050 | Nahawand | 7000 | 90.6 | 127.4 | no |
| `cfinal_a0.5` | 0.5 | final | Nahawand | 7000 | 184.2 | 198.6 | no |
| `cfinal_a1.0` | 1 | final | Nahawand | 7000 | 79.5 | 118.3 | no |
| `a0` | 0 | final | Ajam | 6500 | 248.0 | 234.0 | no |
| `c3050_a0.5` | 0.5 | 3050 | Ajam | 6500 | 203.8 | 203.7 | no |
| `c3050_a1.0` | 1 | 3050 | Ajam | 6500 | 29.8 | 77.5 | no |
| `cfinal_a0.5` | 0.5 | final | Ajam | 6500 | 181.3 | 185.5 | no |
| `cfinal_a1.0` | 1 | final | Ajam | 6500 | 84.5 | 116.0 | no |

No track hit the cap (`truncated` all false); failures: none.

## Smoke (cap 750, not part of the grid)

| config | maqam | duration (s) | wall (s) |
|---|---|---:|---:|
| `a0` | Hijaz | 30.0 | 67.4 |
| `c3050_a1.0` | Hijaz | 12.0 | 61.1 |

## Blinded review

`KEY.json` maps `<Maqam>_<A..E>.mp3` → config for each maqam (single `random.Random(20260924)`; shuffle per maqam in ['Hijaz', 'Kurd', 'Nahawand', 'Ajam'] order). Review zip: `pron_sweep_listen.zip` (20 mp3 @192k + `KEY_open_after_listening.txt`). mp3s are review copies only — no trim/normalize/fade; the WAVs are the untouched originals.

