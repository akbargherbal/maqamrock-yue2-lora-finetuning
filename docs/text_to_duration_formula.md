# Text Length → Audio Duration Cap (yue2_dataset)

How many seconds of audio a lyric of `N` Arabic letters needs, as an **upper
cap**: the length at which a generated song is very likely to have finished
singing. Fitted on the 267 `yue2_dataset/` `.txt` / `.mp3` pairs.

For lyrics-to-song generation the model may always stop early, but a truncated
song is a failure. Under-shooting costs a broken output; over-shooting costs
only a little wasted compute. The loss is **asymmetric**, so the correct target
is a high quantile of duration — not the mean.

## TL;DR

```
duration_cap_s ≈ 111.1 + 0.3126 × N_letters      # 95th percentile
```

Covers **94.8% of all 267 tracks** (14 exceed it). The ~111 s intercept is the
fixed non-vocal overhead (intro / instrumental / gaps); ~0.31 s/letter is the
sung part. For a more forgiving cap use the 97.5th percentile:
`122.9 + 0.3081 × N`.

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

Average recitation is ~2.3 letters/second, rising with `N` (~2.15 l/s at low
counts → ~2.4 l/s at high counts), which indicates a fixed non-vocal overhead
per track plus a roughly linear vocal part.

## The cap

Quantile regression (pinball loss) at the 95th percentile over all 267 tracks:

| Quantile | Fit (`s = a + b·N`) | Coverage | Tracks over cap |
|----------|----------------------|---------:|----------------:|
| 0.90     | `105.1 + 0.3059·N`   | 90.3%    | 26 / 267        |
| **0.95** | **`111.1 + 0.3126·N`** | **94.8%** | **14 / 267** |
| 0.975    | `122.9 + 0.3081·N`   | 97.8%    | 6 / 267         |

The cap slope (0.313) exceeds the central slope (0.280): spread is
heteroscedastic, so the ceiling rises faster than the middle. That is exactly
why a central fit makes a poor cap.

### Do not trim the long tracks

Robust "trim the outliers" regressions drop points with the largest absolute
residual — symmetrically, high **and** low. That is correct for estimating the
centre, but wrong for a cap: of the 13 tracks such a fit discards, 11 run
*longer* than the line. Those long tracks define the ceiling; discarding them
pulls the cap down. The 95% cap above is fit on the full data for that reason.
The only genuine anomalies are the two unusually *short* performances
(`kurd_qais_24072026_011_7176eef3` 161.9 s at N=422;
`ajam_Lamiyat_Alshanfara_16082026_005_5fcfcead` 189.6 s at N=515), and they sit
harmlessly below the cap.

## Accuracy

- `q=0.95` covers 94.8% of tracks; the 14 exceptions overshoot by ~11 s on average.
- `q=0.975` covers 97.8% (6 exceptions).

### Sanity check

`ajam_aasha_23072026_001_51a73d83`

- `N` = 389 letters
- Cap: 111.1 + 0.3126 × 389 = **232.7 s**
- Actual: **193.2 s** → comfortably under the cap, as intended.

## Reference: the centre fit (not a cap)

An earlier trimmed fit through the middle of the data:

```
duration_s ≈ 92.0 + 0.280 × N_letters      # median / centre — NOT a cap
```

It is the conditional mean (least-squares) of the symmetrically trimmed 95%,
and covers only **54.7%** of tracks. Useful to describe typical pacing, but it
under-provisions a cap by design and must not be used to size generation.

## Caveats

- The fit describes *this* corpus: 267 tracks, one style/config at 110 BPM. A
  95% cap here is a 95% cap within this distribution, not a guarantee for any
  arbitrary singer or performance. For distribution shift, prefer the 97.5%
  variant or add a headroom factor.
- Validate against a held-out set before relying on it for new material.

## Reproduce

Run from inside `yue2_dataset/`. Numpy only, no scikit-learn required.

```bash
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
    rows.append((arabic_letters(open(txt, encoding='utf-8').read()), dur))

x = np.array([r[0] for r in rows], float)
y = np.array([r[1] for r in rows], float)

def quantile_fit(x, y, tau, iters=200000, lr=0.05):
    """Pinball-loss (quantile) regression by subgradient descent."""
    xm, xs = x.mean(), x.std()
    xz = (x - xm) / xs
    a, b = np.median(y), 0.0
    for _ in range(iters):
        g = tau - (y - (a + b * xz) < 0)      # d(pinball)/d(residual)
        a += lr * np.mean(g)
        b += lr * np.mean(g * xz)
    return a - b * xm / xs, b / xs            # back to raw N

for tau in (0.50, 0.90, 0.95, 0.975):
    a, b = quantile_fit(x, y, tau)
    cover = 100 * np.mean(y <= a + b * x)
    print(f"q={tau:.3f}: dur = {a:7.2f} + {b:.5f}*N  covers {cover:5.1f}%")
PY
```
