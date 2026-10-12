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

## Next: Probe P — "hold the tempo, drop the padding" (proposed, not built)

Cheapest path from `S1`'s 4 to 5, since `S1`'s *only* stated flaw is speed:

- `P0` T2 core, re-run → within-session drift anchor
- `P1` T2 + `stately groove, unhurried tempo`
- `P2` T2 + `110 BPM` (the number, now isolated — falsification arm)
- `P3` T2 + T1's full tempo set (`ballad, stately groove, unhurried phrase-ending sustains`)
- `P4` T2 + de-padded lyrics (drop the 2nd `[Chorus]`; Outro re-sings a *different* couplet)
- `P5` T3 + `stately groove` (the only above-baseline arm, plus tempo control)

`P4` fights the standing padding design in `workflow.md` Phase 3 / Phase 5.8 — that one is the
user's call, not the agent's. Nothing is built or run yet; no GPU touched.
