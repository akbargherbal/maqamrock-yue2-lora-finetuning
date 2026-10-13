# current.md — Probe Q: win recipe ("regenerate the song") — 2026-10-12

Copy/read surface only, **not authority**. Sources: `results/rating_20261012-1539.md`,
`INFERENCE/songs.v3_probe_q.*.json`, `INFERENCE/v3_probe_q.sh`, `INFERENCE/probe_q_lyrics.txt`.
(The switch inventory from the previous revision of this file is in git history.)

## The fork — decide this first

**Seed 2640605763 is pinned, and generation is deterministic (Pass 1's `ref` re-rendered
byte-identical).** So:

- **Same seed + same config ⇒ byte-identical to Q1.** You don't regenerate anything — the
  take already exists, banked at `…/v3_arabmaqamrock_lora/probe_q/eval/v3q_Q1_ctm_g15.wav`
  (rated **4 overall / keep=yes / "slightly better than the 4/5 baseline"**). Zero GPU.
- **New seed ⇒ a fresh take of the same recipe.** This is the *untested* Pass 2. It may be
  better or worse than Q1; nothing measured predicts which. This is the only reason to spend GPU.

## The recipe (best known: Q1 — pruned CTM style + `guidance_scale=1.5`)

| Item | Value |
|---|---|
| style (41 w, "CTM") | the string below, verbatim |
| lyrics | `INFERENCE/probe_q_lyrics.txt` (FROZEN; byte-verbatim, shared by all Probe Q arms) |
| `EXTRA_REQUEST_OPTS` | `guidance_scale=1.5` — **the only change** |
| rep-pen / temp / cot | `1.2` (default) / `1.0` (default) / `off` |
| adapters | v3 final pair, `/content/converter/out/v3_arabmaqamrock_lora_{ar,nar}.safetensors`, scale **1.0 / 1.0** |
| seed | `2640605763` (replay) **or** a fresh value (new take) |
| cap | `7000` (as in Probe Q; upper cap) |
| expected | ≈224 s, 2 ch / 48 kHz — Q1's measured shape |

Style (verbatim):
`arabmaqamrock dark symphonic rock, slow stately groove, 100 BPM. Maqam Kurd. deep male vocals, breath-supported melismatic runs, melismatic phrasing in Maqam Kurd, unhurried phrase-ending sustains. Distorted electric guitars, orchestral strings, weighted acoustic rock drums, tight rhythm section. Mood: solemn, ominous, grave.`

Co-equal alternative: swap the knob for `semantic_repetition_penalty=1.35` (= Q3, same scores).
Do **not** combine them (= Q4, the one rejected take). Do **not** use the T3 retarget wording (= Q5, generic).

## New one-song manifest (do NOT edit the frozen probe manifests)

`INFERENCE/songs.v3_q1_g15.json`:
```json
{ "defaults": { "repeat": 1 },
  "songs": [ { "name": "v3_q1_g15",
    "style": "arabmaqamrock dark symphonic rock, slow stately groove, 100 BPM. Maqam Kurd. deep male vocals, breath-supported melismatic runs, melismatic phrasing in Maqam Kurd, unhurried phrase-ending sustains. Distorted electric guitars, orchestral strings, weighted acoustic rock drums, tight rhythm section. Mood: solemn, ominous, grave.",
    "lyrics_file": "probe_q_lyrics.txt", "seed": 2640605763, "cap": 7000 } ] }
```
**Existing manifests to copy** (the knob is NOT in the manifest — it's `EXTRA_REQUEST_OPTS`):
- `INFERENCE/songs.v3_probe_q.rp135.json` — single song, byte-identical shape to the above
  (same CTM style, same `lyrics_file`, same seed/cap); only the `name` differs. Closest template.
- `INFERENCE/songs.v3_probe_q.g15.json` — holds the exact Q1 entry, but also Q5 (renders 2).
- `INFERENCE/songs.example.json` — **updated 2026-10-13**: now carries the pinned quality recipe
  (`kurd_quality_recipe`) + a seed-sweep form (`kurd_seed_sweep`); plan = 4 songs / 7 tracks
  (`docs/INFERENCE.md:127-160`; test updated; see `RECONCILIATION_LOG.md` 2026-10-13).

Schema notes (`docs/INFERENCE.md:160-196`): `style` **or** `style_file` (exactly one);
`lyrics` **or** `lyrics_file` (exactly one); `seed` **or** `seeds` (list), mutually exclusive
with `repeat` (N takes, **fresh random seeds** — so `"repeat": 8` is the Pass 2 seed sweep in
one line); `cap` **or** `quantile`; `lora` alias → `defaults.lora` → `--lora-ar/--lora-nar`.
Unknown keys are a hard error; adapter pairs are existence-checked in preflight (before GPU).

## Render (Colab GPU VM only — check `nvidia-smi` first; never overlap)

CPU validation (no GPU): `cd /content/maqamrock-yue2-lora-finetuning && git pull` then
`EXTRA_REQUEST_OPTS="guidance_scale=1.5" python INFERENCE/generate.py INFERENCE/songs.v3_q1_g15.json --dry-run`

terminal: **detached** — survives Ctrl+C / closing the tab;
log `/content/logs/v3_q1_g15.log`; stop `pkill -f songs.v3_q1_g15`;
resume rerun the same line (succeeded takes skip).

```bash
cd /content/maqamrock-yue2-lora-finetuning && git pull
gcloud storage rsync -r "$GCP_BACKUP_BASE/v3_arabmaqamrock_lora/convert" /content/converter/out
export EXTRA_REQUEST_OPTS="guidance_scale=1.5"
setsid nohup python INFERENCE/generate.py INFERENCE/songs.v3_q1_g15.json \
  --lora-ar /content/converter/out/v3_arabmaqamrock_lora_ar.safetensors \
  --lora-nar /content/converter/out/v3_arabmaqamrock_lora_nar.safetensors \
  --out-dir /content/audiocpp_inference/out/v3_q1_g15 --label v3_q1_g15 \
  > /content/logs/v3_q1_g15.log 2>&1 < /dev/null & disown
tail -f /content/logs/v3_q1_g15.log      # ~9 min/track
```

## Caveat

The pick is **provisional**: n=1, one song, one seed, and the in-package anchor drifted ≈0.9 pt
(same file, 4→3). "Best outcome" here means *best measured so far*, not validated.
