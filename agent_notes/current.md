# current

_Updated 2026-09-29 (localhost). Purpose of this page: the two paste-ready style
prompts from the Ajam style ablation, the repetition cause (from the v2 dataset), the
dataset findings, and the test-batch artifacts + run commands for the next session.
Durable record: `docs/music-cover-feasibility.md` §9._

## 1. Overall winning prompt — `l2_target_off` (label D)

Best mean (4.50) and the only variant with no score below 4. In the report this is
`L1 − vocals/instrumentation` (the redundancy rule). **Overall winner.**

```
arabmaqamrock Symphonic cinematic orchestral ballad, hymn-like grand concert hall acoustics, heavy rock instrumentation, stately groove. Maqam Ajam. Audiophile recording, punchy centered mix, forward vocals pulling instrumentation down on sustained phrases then band re-enters between lines, bright presence, clean transients, large dynamic range, natural breath room between phrases. Mood: Epic, Enduring, Triumphant.
```

## 2. Prompt that scored 5 on Maqam Rock — `l0_raw` (label B)

The raw Suno block, verbatim (the control, what we send today). Maqam Rock **5**,
Overall Vocal **5**; lost points only on Lyrics Adherence (1 — outro repeated).

```
[Is_MAX_MODE: MAX](MAX) [QUALITY: MAX](MAX) [REALISM: MAX](MAX)
[START_ON: TRUE]
[START_ON: "وَيَوْمٍ مِنَ الشِّعْرَى"]

genre: "arabmaqamrock Symphonic cinematic orchestral ballad, hymn-like grand concert hall acoustics, heavy rock instrumentation, stately groove.\"
vocals: "deep male vocals, mixed-voice chest-head resonance blend on sustained notes, breath-supported melismatic runs, controlled vibrato, full-voiced commanding presence, precise Arabic diction, melismatic phrasing in Maqam Ajam with unhurried phrase-ending sustains."
production: "Audiophile recording, punchy centered mix, forward vocals pulling instrumentation down on sustained phrases then band re-enters between lines, bright presence, clean transients, large dynamic range, natural breath room between phrases."
instrumentation: "Distorted electric guitars, orchestral strings, weighted acoustic rock drums, tight rhythm section."
mood: "Epic, Enduring, Triumphant"
```

> If by "winning" you meant *best on Maqam Rock only*, that is this prompt (`l0_raw`,
> 5). The overall winner is `l2_target_off` above. Both texts are verbatim from
> `manifests/style_ablation_ajam.report.json`.

Full ladder + decoded scores: `manifests/evaluation_style_ablation_ajam/`.
Decode: A=`l1_full`, B=`l0_raw`, C=`l3_anti_off`, D=`l2_target_off`, E=`l4_min`.

## Repetition — cause confirmed: the LoRA (training-data convention)

The extra intro/outro repeat is a **learned LoRA behavior**, not the sampler and not
AR decode drift. The training songs were built with the user's `suno-workflow`
(`github.com/akbargherbal/suno-workflow`), which *prescribes* the repeats:
- `workflow.md` Phase 5 rule 8: "Buffer-in/out: repeat the first couplet across
  `[Intro]` + `[Verse 1]`; repeat the section's last couplet in `[Outro]`."
- Phase 3 rule 1 (echo the section's first verse at the start, repeat its last verse
  at the end) and rules 2 & 10 (pad short sections by repeating the best couplet as
  a `[Chorus]`, 2×).

So the training lyrics systematically carry the intro couplet twice, the outro
couplet again, and a doubled chorus. Measured over the repo's manifests: **69/69
songs** (`batch_36_songs` 36, `batch_36_rock` 12, `batch_songs_23092026` 21) have
Intro == first couplet of Verse 1, and the Outro couplet recurring earlier. The LoRA
learned "repeat the intro, repeat the outro."

**Correction to the earlier verdict:** the `cot=off` "tail collapse" framing was
over-attributed — the tail is just where the learned buffer/out convention fires.
Style/seed only tip the probability; the prior is the adapter.

Sampler exonerated (neither cause nor guard): identical `1.2 / window 50` in every
render, repeat and non-repeat alike; window = 50 frames = 2.0 s. Penalty sweep dropped.

### Measured on the v2 training set (267 tracks) — no A/B needed

`gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/dataset/` = 267
`.mp3` + `.txt`; each `.txt` is the caption (style), then `[Lyrics]`. Maqams
balanced: Nahawand 73, Ajam 72, Kurd 62, Hijaz 60.

Repetition is baked into the training target (counted over all 267 lyrics):
- **98%** `[Intro]` content == opening of `[Verse 1]` (buffer-in).
- **99%** `[Outro]` content already appears earlier (buffer-out).
- **48%** carry a duplicate `[Chorus]` block.
- **100%** contain ≥1 repeated lyric line; mean **23%** of lines are repeats.

So the extra outro read is the adapter reproducing its training convention (your
workflow Phase 3/5). No A/B needed.

Two train/inference mismatches the data exposes:
1. **BPM:** 100% of captions contain "110 BPM" (all 267, always `110`). The edited
   prompt drops it → off-distribution. Constant across the set, so it may be inert,
   but the model has never seen a caption without it.
2. **Lyric tags:** training lyrics are 100% **bare** (`[Intro]`, `[Verse 1]`, …);
   the generation manifests feed descriptor tags (`[Intro | clean guitar | …]`) —
   tokens absent from the training lyrics. Mean 5.6 sections/song; 87% of captions
   end with `Mood:`.

### Knobs — for "follow the lyrics verbatim"

All via `--request-option k=v` (or `EXTRA_REQUEST_OPTS`; the generic
`--temperature/--top-p/…` are no-ops). Defaults below are the `cot=off` values.

**1. Prompt (conditioning text)**

| knob | default | for verbatim |
|---|---|---|
| `style` | required | flat `arabmaqamrock … 110 BPM. Maqam X. …` = the trained shape. Could carry a directive ("sing every line exactly once, no repeats") — untested. |
| `--lyrics` | required | must contain **no** repeats; trained tag format is **bare** `[Verse 1]`. Try dropping `[Outro]` — the repeat is what an Outro invites. |
| `cot` | `full` (this adapter trained `off`) | `off` = trained. `melody`/`full` are off-distribution and re-plan the song. |

**2. Settings (sampling)**

| knob | default | for verbatim |
|---|---|---|
| `guidance_scale` | `1.01` | **↑ 1.3–1.5** — CFG on the text (style+lyrics); closest thing to "obey what's written." |
| `semantic_repetition_penalty` | `1.2` | ↑ modestly (1.3–1.4). |
| `semantic_penalty_window` | `50` (=2.0 s) | **↑ the key one.** At 50 the penalty only sees 2 s back, so a section repeat tens of seconds away is invisible. Raise to cover the repeat distance (200–1000 frames = 8–40 s). |
| `semantic_temperature` | `1.0` | ↓ 0.8 — less drift/embellishment. |
| `semantic_top_p` / `top_k` | `0.95` / `100` | ↓ = more predictable. |
| `semantic_min_tokens` / `max_tokens` | `200` / `9000` | length bounds (you cap 7500). |
| `export_semantic=true` + `stop_after=semantic` | `false` / `audio` | **measure**: dump the raw token plan, align to lyrics — the objective "did it follow" test, no NAR cost. |
| `semantic_prefix[_file]` | empty | hard-force frames — the only exact-content lock. |
| `seed` / `num_inference_steps` | `1234` / `8` | fix seed; steps = NAR quality only. |

**3. Audio ref (abc)**

| knob | default | note |
|---|---|---|
| `abc` / `abc_file` | empty | symbolic melody score (**not audio**); requires `cot=melody`/`full`. Steers melody, not words. |
| `nar_noise_file` | empty | NAR noise, shaped `[frames,64]`. |
| cover route | — | SheetSage2 → `melody.abc` (`docs/music-cover-feasibility.md`). |

The symptom is a **section-length** repeat, and the default 2 s window cannot see
it — so `semantic_penalty_window` is the one knob aimed straight at it;
`guidance_scale` is the second; `semantic_prefix` is the only hard override. None
of these *guarantees* verbatim.

## Proposed batch — review & minimal design

Guide track: `01-نسيب-وظعن-الحي-ونخيل-يامن-وعرائس-النعمة_4148240095.wav`
(Hijaz, `lora: v2`, from `batch_36_songs.json`; V2 audio on GCS).

**Correction (user, 2026-09-29): the sheet's repeats are the target, not a trap.**
All 267 training songs pair a repeating sheet with audio that reproduces it
exactly (the couplet 2×, never 3×) — v2 was trained to sing the sheet *verbatim,
repeats included*. So:
- With the as-is (repeating) sheet, adherence is readable: pass = exactly 2×,
  fail = 3× / dropped / reordered.
- 2× cannot distinguish "followed the sheet" from "injected the pattern" (identical
  at 2×). To prove the adapter *adds* repeats the sheet lacks, add a **no-repeat
  sheet**: if it still echoes, the adapter injects.
- Since training adhered, an inference-time extra repeat is more likely an
  inference-side mismatch (descriptor tags / format / prompt) than the data.

**Remaining caveat:** Maqam clash — the winning prompt says **Ajam**, this track is
**Hijaz**. Real and independent of the verbatim question.

**Design gaps:** no control arm; `abc_file` forces `cot=melody|full` while the
adapter trained `cot=off` (C moves 2 variables → needs a `cot=melody`-no-abc arm);
n=1 seed and no objective metric; "modified winning prompt" unspecified.

**Minimum sufficient batch** (all `stop_after=semantic export_semantic=true`; render
only winners to audio):

| # | what | cot | extra |
|---|---|---|---|
| 0 | control | off | Hijaz winning prompt, defaults, seed S |
| A | prompt | off | modified Hijaz prompt (one variable) |
| B1 | setting | off | `semantic_penalty_window=500`, `penalty=1.3` |
| B2 | setting | off | `guidance_scale=1.3` |
| C0 | abc-control | melody | no `abc` (isolates cot vs abc) |
| C1 | abc | melody | `abc_file` = V2 Hijaz melody + winning prompt |
| C2 | abc+prompt | melody | same + modified winning prompt |
| D | injection | off | = arm 0 but a **no-repeat** sheet (does it echo unprompted?) |

Score every arm against the sheet **as-is** (exact match: count insertions beyond the
sheet, deletions, reorders); arm D is the injection control. Then
render winners ×3 seeds, blind A/B. Per goal: A+B test lyric adherence; C tests only
the v2 **arrangement import** — ABC steers melody, not words.

### Ready artifacts (2026-09-29) — built for the next Colab session

> **Fresh VM:** all work is on branch **`music-cover`** (decision 2026-09-29 — `main`
> is intentionally not updated). Clone with `git clone --branch music-cover <url>`,
> or `git fetch origin music-cover && git checkout music-cover` after a default clone.

- `manifests/test_verbatim_hijaz/batch.json` — `generate.py` manifest, **validated**
  (`--dry-run`: 5 songs → 15 tracks, ~97 min T4). `lora: v2`, seeds
  `4148240095 / 1029169725 / 1938238049`, cap auto (q=0.95). Arms:
  `ctl_sunoblk_as-is` (track's own Suno block = v2 positive control),
  `win_as-is`, `mod_as-is`, `win_dedup` (injection test), `win_bare` (tag-mismatch test).
- **Prompt text:** `styles/hijaz_winning.txt` = the winning `l2_target_off` with
  `Maqam Ajam`→`Hijaz`; `styles/hijaz_sunoblk.txt` = the track's own block;
  `styles/hijaz_modified.txt` = **placeholder to revise** (Hijaz + `110 BPM` restored +
  all five training fields — swap in the agreed modification before running).
- **Lyrics:** `lyrics/01_nesib_as-is.txt` (verbatim from `batch_36_songs.json`),
  `_dedup.txt` (Intro/Outro buffer sections dropped), `_bare.txt` (descriptor tags
  stripped, = the trained tag format).
- `INFERENCE/test_batch.sh <knobs|abc|all>` — the arms `generate.py` can't express:
  - **B (knobs, cot=off, via `run_one.sh`), each on the winning *and* raw style:**
    `b1_window`/`b1raw_window` (`semantic_penalty_window=500
    semantic_repetition_penalty=1.3`), `b2_guidance`/`b2raw_guidance`
    (`guidance_scale=1.3`), `b3_both`/`b3raw_both`. Baselines (no knobs) are the
    `win_as-is` / `ctl_sunoblk_as-is` arms in `batch.json` (same track/seed/adapter).
  - **C (ABC, cot=melody, direct binary):** `c0_cotonly` (winning, no abc) and
    `c0raw_cotonly` (raw, no abc) as cot controls; with
    `ABC_FILE=<melody.abc>`: `c1_abc_win`, `c2_abc_mod`, and `c3_abc_raw` (**the raw
    Suno block = the `l0_raw` form that scored 5/5 MaqamRock**). Make the abc with
    `INFERENCE/sheetsage2_transcribe.py` from the V2 guide wav, or export v2's own
    `score.abc` via `cot=full --out-dir`.
  - Foreground & sequential; `SEED`/`STYLE`/`LYRICS`/`ABC_FILE`/`OUT_DIR` env-overridable;
    refuses if a training run is active and if `nvidia-smi` is absent.

## Run (next Colab session)

Branch `music-cover` (see the Fresh VM note above). GPU work — check `nvidia-smi` first.

```bash
# assets: prebuilt binary (sm_75/T4) + v2 LoRA -> /content/converter/out + GGUFs from HF
bash bootstrap/setup.sh --inference > /content/logs/setup.log 2>&1   # wait for "done"

# 1) generate.py arms (cot=off) — DETACHED, ~97 min, 15 tracks
python3 INFERENCE/generate.py manifests/test_verbatim_hijaz/batch.json --dry-run   # instant
setsid nohup python3 INFERENCE/generate.py manifests/test_verbatim_hijaz/batch.json \
  > /content/logs/tv_batch.log 2>&1 & disown
#   watch:  tail -f /content/logs/tv_batch.log ; cat /content/audiocpp_inference/out/latest
#   stop:   pkill -f 'generate.py manifests/test_verbatim_hijaz'
#   resume: re-run the same command (skips tracks already done)

# 2) B knob arms — DETACHED
setsid nohup bash INFERENCE/test_batch.sh knobs > /content/logs/tv_knobs.log 2>&1 & disown
#   stop:   pkill -f 'test_batch.sh knobs'

# 3) C ABC arms — needs the SheetSage2 env (NOT staged by setup.sh) + ABC_FILE
ABC_FILE=/path/to/melody.abc setsid nohup bash INFERENCE/test_batch.sh abc \
  > /content/logs/tv_abc.log 2>&1 & disown
#   stop:   pkill -f 'test_batch.sh abc'
```

Before the `mod_*` / `c2_abc_mod` arms: revise
`manifests/test_verbatim_hijaz/styles/hijaz_modified.txt`.
