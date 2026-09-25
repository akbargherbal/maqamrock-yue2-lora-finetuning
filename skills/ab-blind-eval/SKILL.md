---
name: ab-blind-eval
description: Prepare a blinded A/B(/N) audio listening package from rendered variant folders -- flat output with EVAL.txt (public), KEYS.txt (secret decoder), and randomized A/B/C labels. Use when asked to blind-test, A/B test, or set up a listening evaluation of generated audio; trigger words - blind, A/B, A/B test, evaluation package, listening test, EVAL.txt, KEYS.txt, decoder key, shuffle labels, prepare eval.
---

# A/B blind evaluation packaging

Turn a tree of rendered variants into one flat, label-blind listening folder plus
a secret decoder. This is the reusable procedure; the tool is
[`INFERENCE/prepare_ab_eval.py`](../../INFERENCE/prepare_ab_eval.py)
(tests: `tests/test_prepare_ab_eval.py`).

## Input contract

Audio under a root, one leaf folder per **variant**, optional category folders
that group comparable tracks:

```
<root>/<category>/<variant>/<track>.<ext>     # category groups tracks (any depth)
<root>/<variant>/<track>.<ext>                # flat -> one implicit category ""
```

Examples in this repo: `/content/maqam_lyric_swap/<group>/<cfg>/<Track>.wav`,
`/content/pron_fine_sweep/<cfg>/<Maqam>_<seed>.wav`, `/content/pron_knob_probe/<cfg>/...`.

## Output contract

```
out/
  EVAL.txt                     # evaluator instructions -- NO mapping, safe to share
  KEYS.txt                     # secret: blind file -> variant; open AFTER listening
  <stem>_<label>.<ext>         # e.g. Hijaz_20260924_A.wav, Kurd_20260924_B.wav
  <optional> --json key.json   # machine-readable mapping
```

`EVAL.txt` and `KEYS.txt` are deliberately separate. Hand the evaluator the audio
+ `EVAL.txt` only; never `KEYS.txt`.

## Command

```bash
# copy bytes as-is (fast, no ffmpeg); default per-category consistent labels
python INFERENCE/prepare_ab_eval.py --root /content/maqam_lyric_swap \
  --output /content/ab_maqam_lyric_swap --variants a0 c3050_a0.5 --seed 20260928

# repo review convention: 192k mp3 copies (no trim/normalize), JSON key too
python INFERENCE/prepare_ab_eval.py --root /content/pron_knob_probe \
  --output <repo>/PRON_KNOB_PROBE_INPUT --audio-format mp3 --bitrate 192k \
  --seed 20260928 --json /content/ab_knob_key.json \
  --title "PRON_KNOB_PROBE_INPUT" \
  --note g1.5=guidance_scale=1.5 --note t0.8=semantic_temperature=0.8
```

Key flags: `--variants` (2+; default = all detected leaf folders), `--categories`,
`--labels` (default `A B C ...`), `--shuffle-per {category,pair}` (default
`category`), `--extensions`, `--audio-format {copy,wav,mp3}`, `--seed`,
`--dry-run`, `--json`.

## Repo conventions (follow these)

- **New blinding seed every round.** Prior rounds: `20260925` fine sweep,
  `20260926` ckpt sweep, `20260927` lyric swap. Take the next unused integer.
- **Per-category labels are consistent** (`--shuffle-per category`): "A" is the
  same variant for every track in a category, which matches the sweep packages
  (`PRON_FINE_SWEEP_INPUT/`, `MAQAM_LYRIC_SWAP_INPUT/`). Use `pair` only when
  that consistency is not wanted.
- **mp3 review copies** (`--audio-format mp3 --bitrate 192k`), never trimmed,
  normalized, or faded. Commit the mp3s + `EVAL.txt`/`KEY` text; keep the raw
  WAVs under `/content/...` (GCS-mirrored), not in git.
- **Commit the decoder.** Mirror the label map into `results/<round>/KEY.json`
  and keep `KEY_open_after_listening.txt` alongside the mp3s; write a
  `results/<round>/README.md` with the config/per-track tables.
- **Record provenance next to the key** (seed, variant hashes, binary sha256) so
  the round is reproducible -- see `results/pron_fine_sweep/`,
  `results/maqam_lyric_swap/`.

## Verify

- `pytest tests/test_prepare_ab_eval.py` (GPU-free, no ffmpeg needed for `copy`).
- After a real run: `ls out/`, and confirm `EVAL.txt` contains none of the
  variant names while `KEYS.txt` decodes every `_<label>` back to its variant.
