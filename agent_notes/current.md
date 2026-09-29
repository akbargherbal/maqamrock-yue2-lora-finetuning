# current

_Updated 2026-09-29. Verbatim / lyric-adherence blind round **scored and decoded**
(one track, seed 4148240095; blinding seed 20260929). Blank sheet + filled scores:
`manifests/evaluation_verbatim_hijaz/MY_EVALUATION.txt`; decoder (now open):
`manifests/evaluation_verbatim_hijaz/KEYS.txt`. Durable record:
`docs/music-cover-feasibility.md` §9. No commands this turn — analysis only._

## Decode (label -> arm)

| label | arm | what it is |
|---|---|---|
| A | `ctl_sunoblk_as-is` | baseline — the track's own raw Suno block |
| B | `mod_as-is` | "winning" prompt + `110 BPM` restored |
| C | `win_dedup` | "winning" prompt + repeats stripped from the sheet (**injection test**) |
| D | `win_as-is` | the "winning" `l2_target_off` prompt, Hijaz |
| E | `win_bare` | "winning" prompt + bare `[Verse 1]` tags (trained format) |

## Scores (as written by the listener, 5 = best)

| section | A | B | C | D | E |
|---|---:|---:|---:|---:|---:|
| intro-verse vocal | 4.5 | **5** | 4 | 4 | 4 |
| maqam rock (v2) | 4.5 | 4.5 | 4 | 4 | 4 |
| overall vocal | 4.5 | **5** | 4.5 | 4 | 4 |
| pronunciation | 4.5 | 4.5 | **5** | 4 | 4 |
| lyrics adherence | 5 | 5 | 5 | 5 | 5 |
| pace | **5** | 4.5 | 3.5 | 4 | 3.5 |
| **mean** | 4.67 | **4.75** | 4.33 | 4.17 | 4.08 |
| vocal start | 22 s | 21 s | 30 s | 19 s | 6 s |

## Verdict

- **Target question — repeats:** all five **no added repetition**; the dedup sheet (C)
  did **not** get its stripped repeats re-inserted. The "model adds unasked repeats"
  concern did **not reproduce** on this track/seed.
- Corroborated objectively (not only by ear): every rendered duration equals its
  screen-predicted frame count (5/5), and none truncated. An injected section repeat
  lengthens the plan, and the guide's natural plan (7743) sits just 7 frames under the
  7750 cap — so no arm added material. Still n=1 track / 1 seed.
- **Lyric adherence:** tied 5/5 across all arms.
- **Quality ranking:** **B > A > C > D > E.** Winner by a hair is **B = `mod_as-is`**
  (restoring `110 BPM`); **A = `ctl_sunoblk_as-is`** (baseline) is a close second and the
  listener's own "best-sounding: A OR B".
- The arm the round was built to promote, **D = `win_as-is`** (the "winning" prompt),
  came **4th** and was called "generic / meh"; **E = `win_bare`** last.
- C (`win_dedup`) had the best pronunciation (5) but worst pace (3.5) — it is the
  shortest clip (228 s vs A's 310 s), matching the screen's frame predictions.

Caveats: n=1 track, single listener, subjective 1–5 with no confidence recorded; B over A
is 0.08, i.e. noise. ("Sheet" here = the lyric text handed to the model, not music notation.)

So: no strategy change beat the baseline on the repaired defect (there was nothing to
repair); on sound quality the baseline (A) and the +110 BPM variant (B) lead, while the
"winning" prompt alone (D) and the bare-tag format (E) are not supported by this round.
