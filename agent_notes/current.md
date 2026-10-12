# current.md — v3 spice: Suno control inventory (live) + `g1.5` shortlist win (2026-10-11)

Copy/read surface only — not documentation, not authority. Plan: `docs/V3_SPICE_SWEEP.md`.
Reports: `results/rating_20261011-1825.md` (unblinded), `results/rating_20261011-2007.md` (**blind**).

## Suno create panel — control inventory (verified live via CDP, Chrome :9222)

Tab: `suno.com/create`, model **v6-mini**, **Advanced** mode, account `spinningprelude2023`.

| Suno control | range | Suno's own wording at current value |
|---|---|---|
| **Style Influence** | 0–100 | "Moderate" (at 50) |
| **Weirdness** | 0–100 | "Expected results" (at 50) |
| **Variety** | 0–4 | "Balanced variety" / aria-valuetext "Normal" |
| Vocal Gender | Male / Female | — |
| Duration | Custom / Auto | — |
| Max Mode | Off / On | — |
| Personalize (My Taste) | Off / On | — |
| Attachment buttons | — | **Audio** = "Add audio — Browse, upload, or record audio"; Voice = "Add Voice"; Inspo = "Add inspiration from a playlist" |

Finding: **Suno does expose CFG-like controls** (Style Influence, Weirdness, Variety). The earlier
line "Suno never gave you this dial" was an over-statement and is retracted. No hover tooltips —
Suno shows only the one-word descriptor under each slider. "Audio Influence" was **not** visible
(it appears only once source audio is attached, in the cover flow); we did not upload anything.

### Mapping (interpretation, not Suno-documented)

| Suno | ≈ our knob |
|---|---|
| Style Influence | `guidance_scale` (CFG / prompt adherence) |
| Weirdness | `semantic_temperature` (closest) |
| Variety | running multiple seeds (our "Pass 2") |
| Max Mode | quality anchor / `cap` |
| Vocal Gender | style-prompt wording |
| Personalize (My Taste) | **the LoRA itself** |
| Audio (add audio) | no direct equivalent (cover conditioning) |

## State: shortlist blind result

Blind 4-way (`v3_spice` card): `g1.5` won marginally (ovr 4, only "slightly better than ref",
keep=yes; ties ref on the 7-axis sum). `g2.5` = spiciest (spice 4) but broken (arr 2, coh 3, keep=no).
`t1.4` = indistinguishable from default. `ref` = "generic" — reproduces the original complaint.
Calibration: same `ref` bytes scored ovr 5 unblinded vs ovr 3 blind → trust the blind run.

## Focus: prompt influence (user decision) — why CFG, and where the leverage is

1. **CFG = Style Influence** = prompt adherence. ✔ confirmed against the live Suno panel.
2. **CFG does not push *against* the LoRA.** The adapter is in the weights, so it applies to *both*
   CFG branches; the difference CFG amplifies is the text-conditional one, so the LoRA's pull largely
   cancels out. The direct control for "how much LoRA" is the **adapter scale** — and our one data
   point says loosening it costs maqam (AR 0.7 → melody/maqam fit 3/5).
3. **CFG is a multiplier, not a source.** It amplifies whatever specificity the prompt has. The style
   text is the frozen template the LoRA was trained on → amplifying it mostly amplifies *sameness*,
   then breaks (g2.5: "tries a new style… too much", arrangement 2/5). Variety must be *named* in the
   prompt first.
4. **"Generic" is partly a dataset property.** v3 was curated for **consistency** (438/2,281, 4★+,
   consistent vocal character) — consistency was the selection criterion, so the LoRA outputs the
   mode of that subset. Sampler knobs add variation *around* the mode, not new modes.

## Prompt anatomy, measured (2026-10-12) — 438 v3 captions

Caption = style half + `\n[Lyrics]\n` + tagged lyrics (built by `prepare_yue2_dataset_v3.py:79-92`
from each track's Suno `styles` fields). Style half: median **797 chars / 96 words**; lyric half
**1526 chars / 182 words**.

`arabmaqamrock` + genre + `Maqam {X}.` + vocals + production + instrumentation + [`Mood: {Y}.`]

| part | ~words | varies per track? |
|---|---:|---|
| trigger `arabmaqamrock` | 1 | no |
| genre (…, 110 BPM) | 19 | **no** |
| `Maqam {X}.` | 2 | 4 values |
| vocals | 36 | 4 wordings (1 = 330/438) |
| production / mix | 31 | **no** |
| instrumentation | 13 | **no** |
| `Mood:` | ~3 | **154 values**; 55 captions have none; 36 singletons |

- Normalise maqam+mood → **7** distinct styles; **314/438 (72%) byte-identical**.
- **Only `maqam` and `mood` vary.** Tempo pinned at 110 BPM for all 438.
- ⇒ The caption carries almost **no per-track information** → the LoRA learned "this block ≈ the
  genre", not text sensitivity. That is *why* CFG 2.5 exaggerated/broke rather than adding
  controlled nuance: there was little specific signal to amplify.
- ⇒ The one field that varies (`mood`) is the one `maqam_prompt_generator.py`'s docstring says
  caused drift — i.e. likely learned as noise (154 values, 36 singletons, 55 absent).
- ⇒ ~**half the style caption** (production 31w + decorative vocal adjectives + acoustics + mood)
  is removable decoration.

### Where "remove" applies

- **Inference (cheap, no retrain):** every removed directive is a constraining dimension released.
  Tiers — L1 −production/mix paragraph; L2 −decorative vocal adjectives (keep "deep male vocals …
  precise Arabic diction, melismatic phrasing in Maqam {X}"); L3 −mood. Core kept: trigger,
  genre+instrumentation, `Maqam {X}`, male Arabic vocal+melisma.
- **Training (a v4):** pruning cuts the other way — the caption is already ~constant, so shortening
  keeps it constant and the model still ignores it. Narrowness comes from the *audio selection*;
  prompt *influence* would need captions that vary with what is actually in each track (**the
  opposite of removal**). That is a dataset change → the user's explicit decision (AGENTS.md §8).

### Prompt tiers — clause by clause

Rule: **a clause whose absence you would not notice is a clause the LoRA already supplies.** The
user's own observations *are* the audit — "diction is excellent", "mix is the same".

Caption order is as trained (`prepare_yue2_dataset_v3.py:79-92`): do **not** reorder.
`trigger + genre + Maqam {X}. + vocals + production + instrumentation + [Mood: {Y}.]`

| # | exact clause | tier | why |
|---|---|---|---|
| 1 | `arabmaqamrock` | **KEEP** | LoRA activation token; dropping it = off-distribution |
| 2 | `Symphonic cinematic orchestral ballad` | **KEEP** | genre identity |
| 3 | `hymn-like grand concert hall acoustics` | DROP | acoustics ≈ production, duplicated |
| 4 | `heavy rock instrumentation` | **KEEP** | the rock half of the identity |
| 5 | `stately groove` | KEEP / RETARGET | carries the mid-tempo vibe *without* a number |
| 6 | `110 BPM` | **DROP** | measured: audio spans 70–140, median ~117 → a description, not a control |
| 7 | `Maqam {X}.` | **KEEP** | the variable |
| 8 | `deep male vocals` | **KEEP** | voice + gender |
| 9 | `mixed-voice chest-head resonance blend on sustained notes` | DROP | vocal-technique detail |
| 10 | `breath-supported melismatic runs` | **KEEP** | melisma = the Arabic signature |
| 11 | `controlled vibrato` | DROP | technique detail |
| 12 | `full-voiced commanding presence` | DROP | decorative |
| 13 | `precise Arabic diction` | DROP | user: diction is excellent → internalised |
| 14 | `melismatic phrasing in Maqam {X}` | **KEEP** | the only place the maqam touches the voice |
| 15 | `with unhurried phrase-ending sustains` | DROP | decorative |
| 16 | `Audiophile recording, punchy centered mix, bright presence, clean transients, large dynamic range, natural breath room between phrases` | DROP | user: mix is the same → internalised |
| 17 | `forward vocals pulling instrumentation down on sustained phrases then band re-enters between lines` | DROP? **watch dynamics** | carries *arrangement/dynamics*, not just mix — the one production clause that may be load-bearing |
| 18 | `Distorted electric guitars, orchestral strings, weighted acoustic rock drums, tight rhythm section` | **KEEP** / RETARGET | the rock+orchestra bed; retargeting moves arrangement |
| 19 | `Mood: {Y}` | **DROP** | 154 values / 36 singletons / 55 absent → noise; the generator docstring already blames mood for drift |

### The tiers (Kurd shown; swap the maqam name)

**T0 — Full** (= current control). All 19 clauses above.

**T1 — Safe prune** (drop internalised + decorative + noise; keep every load-bearing clause):
```
arabmaqamrock Symphonic cinematic orchestral ballad, heavy rock instrumentation, stately groove. Maqam Kurd. deep male vocals, breath-supported melismatic runs, melismatic phrasing in Maqam Kurd. forward vocals pulling instrumentation down on sustained phrases then band re-enters between lines. Distorted electric guitars, orchestral strings, weighted acoustic rock drums, tight rhythm section.
```

**T2 — Core** (the non-negotiable minimum):
```
arabmaqamrock Symphonic rock, male Arabic vocal in Maqam Kurd, melismatic phrasing in Maqam Kurd. Distorted electric guitars, orchestral strings, weighted acoustic rock drums, tight rhythm section.
```

**T3 — Retarget** (T1 with arrangement pushed, per the "symphonic rock" idea):
```
arabmaqamrock Symphonic rock, driving groove, heavier guitars. Maqam Kurd. deep male vocals, breath-supported melismatic runs, melismatic phrasing in Maqam Kurd. Distorted electric guitars, orchestral strings, weighted acoustic rock drums, tight rhythm section.
```

Map to probe S: S0=T0 · S1=T2 · S2=T3 · S4=T1 (T1 already drops `110 BPM`).

### `110 BPM` — measured (48-file stratified sample, librosa tempogram, no BPM prior)

Dominant peak, folded into [70,140) to remove octave ambiguity: **median 117.5, mean 111.9,
stdev 23.4**. Bin histogram (10 BPM): 70→8, 80→3, 90→1, 100→1, **110→9, 120→5, 130→11, 140→10**.
Only **19%** of files fall within 5% of 110 (38% near 130, 17% near 72). Folding *all* peaks: the
110 bin is the single tallest (23) but 130 (19), 70 (15), 90 (13) are right behind — broad.

⇒ **"110 BPM" was not a literal constraint in the training audio.** It sits near the *centre* of a
wide spread, i.e. it is a *description*, not a *control* — so the LoRA cannot have learned it as a
timing fact. Dropping it is therefore the **safe** kind of removal, and it frees the tempo/motion
dimension — the one worth loosening. Keep or drop "stately groove" as a separate decision (that
phrasing carries the mid-tempo vibe independently of the number).
Caveat: tempo estimation is rough (half/double, log-spaced bins, dense orchestral-rock mixes) —
suggestive, not definitive.

### Viability — and the unknown that decides it

Two regimes, and which one holds is measurable:

- **LoRA-dominant** (rank-32 adapter over the full sentence was trained to reproduce this exact
  sound): the prompt is decorative → prompt edits move little, and CFG (which amplifies the prompt)
  has little to amplify → then the honest answer is seed selection.
- **Base-dominant** (YuE2-3B responds to language; the LoRA is a thin style bias): the prompt is a
  real control → prune + retarget is high-leverage.

Falsifiable prediction from the user's own listening: prompt edits will move **arrangement / tempo /
instrumentation** more than **vocal timbre / mix** (the latter being the internalised parts).

### Probe S — 2×2: *who is carrying the sound?* (decides everything downstream)

Pinned seed `2640605763`. Adapter **scale 0 = "adapter off / base weights"** (`docs/INFERENCE.md:98-101`,
already used for base-model arms). ~6 arms, ~55 min, one session.

| arm | LoRA | prompt | question it answers |
|---|---|---|---|
| **S0** | on | full (= current) | control |
| **S1** | on | core-only | does the prompt move the output *with* the LoRA? |
| **B1** | **off** | full | what does the base model do with your real prompt? |
| **B2** | **off** | core-only | does the base model respond to the prompt **at all**? |
| **S2** | on | genre retargeted (e.g. "Symphonic rock, driving 125 BPM") | does genre/tempo steer? |
| **S4** | on | full − `"110 BPM"` | the measured-safe removal |

Read-out (this is the whole point — the off-arms turn a hunch into a measurement):

- **B1 ≠ B2** ⇒ the base model *does* respond to the prompt (the prompt is a real language input).
- **S0 ≈ S1 while B1 ≠ B2** ⇒ the **LoRA is suppressing prompt responsiveness** ⇒ LoRA-dominant —
  *direct* evidence, not inference.
- **S0 ≠ S1** ⇒ the prompt stays live even with the LoRA on ⇒ base-dominant ⇒ prune/retarget pays.
- **B1 vs S0** ⇒ how much of the sound is the LoRA at all.
- Per-dimension prediction: arrangement/tempo moves; timbre/mix does not.

Caveat: with the adapter off the trigger `arabmaqamrock` is a meaningless token to the base model —
interpret B1/B2 as "how the base reads the *rest* of the text", not as a quality benchmark.

Decision rule: **S0≈S1 and B1≈B2** → stop prompt work, go to seeds. **S0≠S1** → prune, retarget, then CFG.

⇒ Order: **Probe S (2×2)** → pruning ladder → CFG curve. CFG last: it only amplifies what the prompt
turns out to contribute.

### Probe S — artifacts (written 2026-10-12, dry-run validated, NOT run)

- `INFERENCE/songs.v3_prompt_probe.json` — S0 `T0`, S1 `T2`, S2 `T3`, S4 `T1` (LoRA on)
- `INFERENCE/songs.v3_prompt_probe.base.json` — B1 `T0`, B2 `T2` (run at adapter scale 0)
- `INFERENCE/v3_prompt_probe.sh` — driver; `DRY=1` skips GPU checks
- Song: `kurd_Lamiyat_Alshanfara_16082026_003_1b956cd0` (lyrics verbatim), seed `2640605763`,
  cap `7000` (duration_cap q0.95, N_letters=533 → 280 s). Style word counts: T0 95 / T1 48 / T2 26 / T3 32.
- Dry-run: 4 + 2 arms planned; projected **~26 + ~13 = ~39 min** on a T4.

Run (Colab, GPU VM, detached):
```bash
cd /content/maqamrock-yue2-lora-finetuning
DRY=1 bash INFERENCE/v3_prompt_probe.sh                  # CPU validation first
bash bootstrap/setup.sh --inference > /content/logs/setup.log 2>&1   # require no [FAIL]
gcloud storage rsync -r "$GCP_BACKUP_BASE/v3_arabmaqamrock_lora/convert" /content/converter/out
setsid nohup bash INFERENCE/v3_prompt_probe.sh > /content/logs/v3_prompt_probe.log 2>&1 < /dev/null & disown
tail -f /content/logs/v3_prompt_probe.log
```
Stop: `pkill -f v3_prompt_probe.sh` · Resume: rerun the launch line (same `OUTROOT` → succeeded
takes skip). Output: `…/out/v3_prompt_probe/{lora_on,lora_off}/` → one `v3pp_<arm>_2640605763.wav` each.

## Next options (no GPU runs until the user's command)

1. **Interaction grid** — guidance {ref 1.01, 1.5, 2.0} × prompt {frozen, + improvisation cues}
   = 6 arms, one session ~55 min, blind-rated together. Hypothesis: the improv prompt gives CFG
   something to commit to → g2.5-style novelty *without* the breakage. The improv text is the
   user's artifact — draft + approve first.
2. **Pure guidance curve** (frozen prompt) — `ref g1.5 g1.75 g2.0 g2.25 g2.5`, ~55 min; we half-know
   the shape already (1.5 mild, 2.5 broken).
3. **8 takes of `g1.5`** — reliability / selectable takes (~75 min).
4. Consider **Weirdness ≈ temperature** at wider values (1.2 / 1.4 were ~no-op; range may be narrow).

## Untracked here
- `results/rating_20261011-1825.md`, `results/rating_20261011-2007.md`, `SUCCESS_STORY.md`.
