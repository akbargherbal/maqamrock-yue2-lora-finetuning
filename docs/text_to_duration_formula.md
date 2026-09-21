# Text Length → Audio Duration Formula (yue2_dataset)

Derived the relationship between the number of Arabic letters in each lyric
`.txt` and the duration of the matching `.mp3`, generalizing over 95% of the
tracks (outliers excluded).

## Data

- 267 `.mp3` / `.txt` pairs in `yue2_dataset/`.
- Duration: `ffprobe -v error -show_entries format=duration -of csv=p=0 <file>.mp3`
- Letters: count of Unicode `Lo` characters in the Arabic block U+0600–U+06FF.

### Counting rule

Arabic **letters** only. Included: `أ إ آ ا ء ؤ ئ ب ت ث ج ح خ د ذ ر ز س ش ص ض ط ظ ع غ ف ق ك ل م ن ه و ة ى ي`.

Excluded:
- Diacritics / marks U+064B–U+0652 (fatha, damma, kasra, shadda, sukun, tanwin)
- Tatweel U+0640
- Digits, spaces, punctuation, Latin / non-Arabic characters
- Section tags such as `[Verse 1]`, `[Intro]`

The first (English prompt) line of every file contains **0** Arabic letters, and
all 267 prompts specify **110 BPM**, so the letter count equals the sung lyric
content.

## Observed ranges

| Quantity      | Min | Median | Max |
|---------------|----:|-------:|----:|
| Letters `N`   | 328 | 571    | 829 |
| Duration (s)  | 162 | 253    | 370 |

Average recitation rate is ~2.3 letters/second, but it rises with `N`
(~2.15 l/s at low counts → ~2.4 l/s at high counts), which indicates a fixed
non-vocal overhead (intro / instrumental / gaps) per track plus a roughly linear
vocal part.

## Formula

Trimmed (least-trimmed-squares style) linear regression fit on the best 95% of
tracks (254/267), outliers excluded:

```
duration_s ≈ 92.0 + 0.280 × N_letters
```

Inverse:

```
N_letters ≈ (duration_s − 92.0) / 0.280
```

### Accuracy

- Coverage: 94.4% of all tracks within ±35 s (1.96σ)
- MAE: 16.1 s, RMSE: 20.8 s
- Marginal rate ≈ 3.6 letters/second; average ≈ 2.3 letters/second

### Sanity check (example from the request)

`ajam_aasha_23072026_001_51a73d83`

- `N` = 389 letters
- Predicted: 92.0 + 0.280 × 389 = **200.8 s**
- Actual: **193.2 s**

### Alternative models

| Model                     | Fit                          | Residual σ | Notes                          |
|---------------------------|------------------------------|-----------:|--------------------------------|
| Linear (95% trimmed)      | `dur = 92.0 + 0.280·N`       | 17.7 s     | best                           |
| Huber robust (all)        | `dur = 88.0 + 0.289·N`       | 18.6 s     | covers 90.6% at 1.96σ          |
| Through-origin            | `dur = 0.442·N`              | 20.5 s     | worse; ignores fixed overhead  |
| Quadratic                 | `dur = 79.5 + 0.317·N − 2.2e−5·N²` | 20.7 s | no real gain                |

## Excluded outliers (13 of 267 ≈ 5%)

All are structural / tempo anomalies (intro-heavy, slowed, or long-poem tracks
running ~40–70 s from prediction):

| File | N | Actual (s) | Predicted (s) | Residual (s) |
|------|--:|-----------:|--------------:|-------------:|
| `ajam_Lamiyat_Alshanfara_16082026_005_5fcfcead` | 515 | 189.6 | 236.1 | −46.5 |
| `ajam_majnoon_layla_18082026_008_99dd0dab`      | 670 | 344.0 | 279.5 | +64.5 |
| `ajam_muallaqt_antra_21082026_006_504d6b9f`     | 554 | 298.1 | 247.0 | +51.1 |
| `ajam_nabigah_19072026_004_e1f451d0`            | 328 | 232.9 | 183.8 | +49.1 |
| `hijaz_short-poems_16082026_025_b9e9154b`       | 745 | 369.7 | 300.5 | +69.3 |
| `kurd_jarir_24072026_006_d0fd493c`              | 484 | 272.0 | 227.4 | +44.5 |
| `kurd_qais_24072026_011_7176eef3`               | 422 | 161.9 | 210.1 | −48.2 |
| `nahawand_amro_bin_kalthoum_20082026_022_1f09f875` | 643 | 313.1 | 271.9 | +41.2 |
| `nahawand_amro_bin_kalthoum_20082026_023_ff8033ff` | 643 | 319.7 | 271.9 | +47.8 |
| `nahawand_amro_bin_kalthoum_23072026_032_0be82bf8` | 630 | 313.0 | 268.3 | +44.8 |
| `nahawand_amro_bin_kalthoum_24072026_015_8ea19939` | 630 | 338.1 | 268.3 | +69.8 |
| `nahawand_ghayra_mujdin_19082026_001_8308a510`      | 576 | 300.3 | 253.2 | +47.1 |
| `nahawand_ghayra_mujdin_19082026_010_7666435c`      | 557 | 297.8 | 247.9 | +49.9 |

## Reproduce

```bash
cd yue2_dataset
python3 - <<'PY'
import os, glob, subprocess, unicodedata
import numpy as np

def arabic_letters(t):
    return sum(1 for c in t
               if 0x0600 <= ord(c) <= 0x06FF and unicodedata.category(c) == 'Lo')

rows = []
for txt in sorted(glob.glob('*.txt')):
    mp3 = txt[:-4] + '.mp3'
    if not os.path.exists(mp3):
        continue
    dur = float(subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
         '-of', 'csv=p=0', mp3], capture_output=True, text=True).stdout.strip())
    rows.append((txt[:-4], arabic_letters(open(txt, encoding='utf-8').read()), dur))

x = np.array([r[1] for r in rows], float)
y = np.array([r[2] for r in rows], float)
n, keep = len(x), int(round(0.95 * len(x)))

# least-trimmed-squares: drop worst residual until 95% remain
mask = np.ones(n, bool)
while mask.sum() > keep:
    b, a = np.polyfit(x[mask], y[mask], 1)
    r = np.abs(y - (a + b * x)); r[~mask] = -1
    mask[np.argmax(r)] = False
b, a = np.polyfit(x[mask], y[mask], 1)
print(f"duration_s = {a:.3f} + {b:.5f} * N_letters  (n={mask.sum()}/{n})")
PY
```
