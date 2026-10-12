# current.md — Probe S read-out (2026-10-12)

Copy/read surface only, not authority. Authority = `results/rating_20261012-1008.md` (raw rating,
blind, revealed) + the audio banked at `…/v3_arabmaqamrock_lora/prompt_probe`.

## Run facts (commit `7fbc3ef`, the Colab session)
6/6 exit 0, none truncated, 48 kHz stereo, ~52 min wall (≈8.8 min/track). Adapter sha256
`3531bb91…` / `a7eabcad…`; off-arms logged `scale=0.000000`. Banked. GPU free at start and end.

## Rating — one song, one seed (`2640605763`), one take per arm

| arm | prompt | LoRA | ovr | spice | mel | voc | arr | coh | dic | vs_ref | keep |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `S0_full` | T0 (95 w) | on | 2 | 4 | 1 | 2 | 3 | 5 | 3 | worse | no |
| `S1_core` | T2 (26 w) | on | **4** | 4 | 4 | **5** | **5** | 5 | 4 | same | **yes** |
| `S2_retarget` | T3 (32 w) | on | 4 | 4 | 4 | 4 | 4 | 3 | 4 | **slightly** | no |
| `S4_prune` | T1 (48 w) | on | **4** | 3 | 4 | 4 | **5** | 5 | 4 | same | **yes** |
| `B1_base_full` | T0 (95 w) | OFF | 2 | 5 | 1 | 2 | 3 | 5 | 3 | worse | no |
| `B2_base_core` | T2 (26 w) | OFF | – | 4 | – | 3 | – | 2 | 3 | worse | no |

## Read-out

1. **The prompt is a live lever.** `S0` vs `S1` differ *only* in the style string — same song, seed,
   adapter, session, blind — and score 2 vs 4 overall. ⇒ **prune**; prompt editing pays.
2. **The base responds too** (`B1` ≠ `B2`: spice 5/4, voc 2/3, coh 5/2), so the LoRA is not
   suppressing prompt-sensitivity. But **both base arms were rejected** (worse / keep=no) ⇒ the LoRA
   carries identity; the base is not a fallback.
3. **The as-trained template is the worst arm, and its failure is a mood inversion** — celebratory
   music on a grim poem (Lamiyat al-Shanfara). `S0` (LoRA on) and `B1` (LoRA off) scored **the same on
   6 of 7 axes** ⇒ the inversion comes from the template's wording, not the adapter. Prime suspect:
   `hymn-like grand concert hall acoustics` + the production paragraph + the `Mood:` clause.
   `Symphonic cinematic orchestral ballad` is **exonerated** — T1 keeps it and scores 4.
4. **`110 BPM` was never the tempo control.** T2 dropped *every* tempo-holding word → `S1` was the
   only arm flagged "faster than I want". T1 keeps `stately groove` → no speed complaint.
5. **The repetition complaint is our own input.** The probe lyrics contain the final couplet **3×**
   (2× `[Chorus]` + `[Outro]`) — exactly the count heard. Dataset-wide (438 captions): **92 %** repeat
   the final hemistich ≥2×, **11 %** ≥3×, 22 % have some hemistich ≥3×, 49 % have ≥2 `[Chorus]` blocks,
   13 % have an `[Outro]` that re-sings a chorus line. The LoRA is reproducing a baked-in habit.
6. **Pruning restored the baseline, it did not beat it** — `S1`/`S4` are `vs_ref = same`. The only
   arm rated better than the baseline was `S2`, and it was rejected for the repetition in (5).
7. **Diction: pruned arms 4 > template 3.** The Uthmani doubled-lam rule is applied inconsistently —
   this file writes `وَٱلَّيۡلُ` in Uthmani but leaves `اللَّاتِي` plain (14 occurrences dataset-wide);
   only 172/438 captions carry any `ٱ`.
8. **N = 1 per arm, one poem, one seed.** Session drift measured earlier is large (identical bytes
   rated 5 unblinded vs 3 blind). Treat the 2-vs-4 gap as real; treat the spice/tempo micro-deltas as
   hypotheses.

## Constraint (user, 2026-10-12): LYRICS FROZEN

No lyric edits — not even dropping a verse. The desired behaviour must come from **style/prompt +
generation parameters** only. Consequence: the written 3× couplet stays. A repetition penalty can
only remove repeats the model *adds* (B2 sang it 4×) — it can never drop a line the text asks for.

## Next: Probe Q — cross the two levers that were never crossed

Pass 1 measured `guidance_scale` against the **full template** (a prompt Probe S now shows is the
*worst* one). Probe S measured prompt tiers at the **default guidance 1.01**. Neither measured the
interaction — so both are re-opened.

Candidate style string — "core + tempo + mood", **~41 w** (the band that scored 4; not 95):

```
arabmaqamrock dark symphonic rock, slow stately groove, ~100 BPM. Maqam Kurd. deep male vocals,
breath-supported melismatic runs, melismatic phrasing in Maqam Kurd, unhurried phrase-ending
sustains. Distorted electric guitars, orchestral strings, weighted acoustic rock drums, tight
rhythm section. Mood: solemn, ominous, grave.
```

Drops `hymn-like grand concert hall acoustics`, the whole production paragraph, and `110 BPM`.
Adds an explicit slow/groove clause and a solemn mood clause.

| what you heard | knob | from → to |
|---|---|---|
| celebratory on a grim poem | style string (− grand/acoustics, − production paragraph) | 95 w → ~41 w |
| celebratory, part 2 | `guidance_scale` | 1.01 → 1.5 |
| "too fast" | style string: slow/groove clause | added |
| repeats beyond the written text | `semantic_repetition_penalty` | 1.2 → 1.35 |
| flat / generic | `guidance_scale` (the only knob that ever moved this) | 1.01 → 1.5 (2.5 breaks structure) |
| flat / generic, axis 2 | seed selection (N = 1 today) | 1 → 8 |

6 arms, pinned seed `2640605763`, cap 7000, one session (~55 min):

- `Q0` core+tempo+mood, `guidance_scale=1.01` → control + within-session drift anchor
- `Q1` core+tempo+mood, `guidance_scale=1.5`
- `Q2` core+tempo+mood, `guidance_scale=2.0`
- `Q3` core+tempo+mood, `semantic_repetition_penalty=1.35`
- `Q4` core+tempo+mood, `guidance_scale=1.5` + `semantic_repetition_penalty=1.35`
- `Q5` retarget wording + `guidance_scale=1.5` (the only above-baseline wording × guidance)

Isolation arms if budget allows: core + `hymn-like grand concert hall acoustics` only; core +
production paragraph only — that separates the three T0 suspects.

Deprioritised (evidence weak in Pass 1): `LORA_AR_SCALE=0.7` (scored 20/30), `semantic_temperature`
1.2/1.4 (indistinguishable from ref), checkpoint swaps. `cot` is off, so melody/improvisation is a
sampler + prompt + selection question, not a checkpoint question.

Nothing built or run yet; no GPU touched.
