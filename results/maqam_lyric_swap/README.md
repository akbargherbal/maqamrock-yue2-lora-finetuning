# maqam_lyric_swap — cross-maqam lyric swap (Hijaz + Kurd)

Tests one maqam's **caption + maqam tag** against the **other maqam's** held-out
lyric, at two pron settings: `a0` (v2 verbatim, no pron contribution) and
`c3050_a0.5` (v2 + pron checkpoint 3050 at alpha 0.5). 2 swap groups x 2 configs =
**4 tracks**, strictly sequential. The question is whether the style/tag or the
lyric text dominates — i.e. does the model sing the lyric it is given, under the
other maqam's caption?

Same generation seed `20260924` and the same **auto-cap convention** as the fine
sweep; the cap follows the swapped-in lyric (Hijaz lyric -> 7250, Kurd lyric -> 6500).

## Groups

| group | style/caption | lyric | cap |
|---|---|---|---:|
| `KurdStyle_HijazLyrics` | `Kurd_style.txt` | `Hijaz_lyrics.txt` | 7250 |
| `HijazStyle_KurdLyrics` | `Hijaz_style.txt` | `Kurd_lyrics.txt` | 6500 |

Staged prompts hash-match the Task 17 / fine-sweep set (Hijaz style `9e201bfb…`,
Hijaz lyric `1b8dc015…`, Kurd style `0e789bfd…`, Kurd lyric `ac29850a…`).

## Configs

| folder | pron ckpt | alpha | converted AR sha256 | AR rank |
|---|---:|---:|---|---:|
| `a0` | — | 0.0 | `747d5cfe2224b1bae6e582ccf5f2ee2a57e3f030c53d54e134f34a85960426fa` | 32 |
| `c3050_a0.5` | 3050 | 0.5 | `33e824f24f1eec1ab06a45365e93a19b078a2a7cfbea724eba1b908d27360509` | 40 |

`a0` reproduces v2 verbatim (AR `747d5cfe…` / NAR `ad2c8d86…`); `c3050_a0.5` matches the
Task 17/18/19 merge (AR `33e824f2…`, NAR `7d9324bf…`). Both converted NAR files are the
v2 NAR (`7d9324bf…`).

Binary in use: `97028a71fd4d86378161162364dc6cdc85a569461d3afb6bf78f83ea572ad3d4` (`sm_89`), GPU NVIDIA L4 (cc 8.9).

## Tracks

Wall = `/usr/bin/time -v` for the whole `audiocpp_cli` process, from `*_time.txt`.

| group | style | lyric | config | cap | duration (s) | wall (s) | truncated | label |
|---|---|---|---|---:|---:|---:|:--:|---|
| `KurdStyle_HijazLyrics` | Kurd | Hijaz | `a0` | 7250 | 243.92 | 254.1 | no | `KurdStyle_HijazLyrics_B` |
| `KurdStyle_HijazLyrics` | Kurd | Hijaz | `c3050_a0.5` | 7250 | 227.28 | 244.7 | no | `KurdStyle_HijazLyrics_A` |
| `HijazStyle_KurdLyrics` | Hijaz | Kurd | `a0` | 6500 | 229.92 | 220.0 | no | `HijazStyle_KurdLyrics_A` |
| `HijazStyle_KurdLyrics` | Hijaz | Kurd | `c3050_a0.5` | 6500 | 190.84 | 194.1 | no | `HijazStyle_KurdLyrics_B` |

Mean wall **228.2 s**, total **912.9 s (15.2 min)** — 4 tracks, one L4.

## Blinded review

`<GCP_BACKUP_BASE>/listening/MAQAM_LYRIC_SWAP_INPUT/` (GCS, not the repo): `KurdStyle_HijazLyrics_{A,B}.mp3`,
`HijazStyle_KurdLyrics_{A,B}.mp3` (ffmpeg 192k, no trim/normalize) +
`KEY_open_after_listening.txt`. Within each group the two files differ only in the
pron config (A/B blinded). Label map also at `results/maqam_lyric_swap/KEY.json`.
Per-track sidecars in `results/maqam_lyric_swap/sidecars/`. Raw WAVs + adapters:
`/content/maqam_lyric_swap/`.
