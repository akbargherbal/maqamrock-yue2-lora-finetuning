# Blinded A/B audio evaluation packaging

How to turn rendered variants into a label-blind listening package with a secret
decoder. The agent-facing procedure is the
[`ab-blind-eval` skill](../skills/ab-blind-eval/SKILL.md); the tool is
[`INFERENCE/prepare_ab_eval.py`](../INFERENCE/prepare_ab_eval.py); tests are
`tests/test_prepare_ab_eval.py`.

## What it produces

```
<output>/
  EVAL.txt                 evaluator instructions -- NO mapping, safe to hand over
  KEYS.txt                 secret decoder: blind file -> variant; open AFTER listening
  <stem>_<label>.<ext>     Hijaz_20260924_A.wav, Hijaz_20260924_B.wav, ...
  <optional> key.json      machine-readable mapping (--json)
```

The public/secret split is the point: send the evaluator the audio + `EVAL.txt`
only.

## Input layout

One leaf folder per **variant**, optional category folders grouping comparable
tracks (any depth):

```
<root>/<category>/<variant>/<track>.<ext>
<root>/<variant>/<track>.<ext>          # flat -> implicit category ""
```

This matches every sweep workspace already in use, e.g.
`/content/maqam_lyric_swap/<group>/<cfg>/<Track>.wav`.

## Usage

```bash
# inspect first: discovery + label plan, writes nothing
python INFERENCE/prepare_ab_eval.py --root /content/pron_knob_probe \
  --output /tmp/ab --audio-format mp3 --seed 20260928 --dry-run

# real package, listening convention (192k mp3, no trim/normalize); mirror to GCS after
python INFERENCE/prepare_ab_eval.py --root /content/pron_knob_probe \
  --output /content/listening/PRON_KNOB_PROBE_INPUT --audio-format mp3 --bitrate 192k \
  --seed 20260928 --json /tmp/key.json \
  --note g1.5=guidance_scale=1.5 --note t0.8=semantic_temperature=0.8
```

Flags: `--variants` (2+; default = all detected), `--categories`, `--labels`,
`--shuffle-per {category,pair}` (default `category`), `--extensions`,
`--audio-format {copy,wav,mp3}`, `--seed`, `--json`, `--dry-run`.

## Conventions

- **New blinding seed each round** (`20260925` fine sweep, `20260926` ckpt sweep,
  `20260927` lyric swap -> next unused integer).
- **Per-category consistent labels** so "A" is the same variant across a
  category's tracks, matching `PRON_FINE_SWEEP_INPUT/` and
  `MAQAM_LYRIC_SWAP_INPUT/`.
- **Mirror the mp3s + key text to GCS `<base>/listening/<PACKAGE>/`; do not commit
  them** — audio is not repo content (`.gitignore` has `*_INPUT/`). Keep raw WAVs
  under `/content/...` (GCS-mirrored).
- **Generated listening packages live in GCS, not the repo.** The mp3 A/B packages
  are audio artifacts; they are mirrored to `<base>/listening/` and git-ignored.
  (They remain in git *history* — removing them from the index does not rewrite
  history; purging history is a separate SHA-rewriting decision, not done here.)
- Mirror the label map into `results/<round>/KEY.json`, with a `README.md` of the
  config/per-track tables and the provenance hashes.
