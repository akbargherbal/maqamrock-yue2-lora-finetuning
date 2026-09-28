# current

## Next session — do this

**Decision (2026-09-28):** fix the **style prompt only**; lyrics stay verbatim. Targets
`arabmaqamrock Maqam <M>. Mood: <mood>.` — drop every constant clause (rationale below).

1. Build **style-only** variant manifests for the worked track: L0–L4 from the ladder
   below (lyrics identical). Smallest test = the single smoked Maqam-Ajam track.
2. Stage `qfinal_a0.3`:
   `gsutil -m cp -r "$GCP_BACKUP_BASE/loras/audio_cpp/pron/qfinal_a0.3" /content/converter/out/`
   — check `python status.py` first (no GPU overlap).
3. Render L0–L4 at α0.3, same seed, same lyrics → blind A/B (`INFERENCE/prepare_ab_eval.py`).
4. The ladder answers one question: **does the trigger alone hold the MUST features?**
   If the arrangement stays sparse at L3/L4, it lives in the adapter → Branch B (ABC),
   not more words.

## Style prompt — classify by product features (must / should / nice)

Lyrics stay **verbatim** (as in Suno) — no tag normalization. Work is on the `style`
string only. α fixed at 0.3. Worked example: `07-الحر-الشديد…`, Maqam Ajam.

### The two rules

1. **Redundancy rule.** A clause *constant across all 267 training captions* is fully
   predicted by the trigger (`P(clause | arabmaqamrock) = 1`) ⇒ it carries **zero
   information**; restating it can only re-anchor. Only `Maqam` (4 values) and `Mood`
   (120) ever varied ⇒ the only live text levers.
2. **Truth rule (new).** Constant ≠ safe. If the clause was a *Suno instruction the
   audio ignored*, restating it anchors a **false** constraint. Proof: every caption
   says `110 BPM`; measured on a 28-track sample, the audio is **86–162 BPM, median
   123** (librosa; octave-ambiguous, but decisively not 110). Drop is not just safe
   here — it's beneficial. (Also: BPM is a Western frame, weak for this material.)

### Feature classification

| Product feature | Needed in output | Text needed? | Clause | Verdict |
|---|---|---|---|---|
| `arabmaqamrock` identity | MUST | no — trigger+LoRA | trigger | **keep** (the handle) |
| **Maqam** (mode/identity per song) | MUST | **yes** (only trained variable) | `Maqam Ajam.` | **KEEP** |
| Arabic pronunciation | MUST | no — α adapter | (lyrics) | α, not prompt |
| male melismatic vocal | MUST | no — LoRA | `vocals:` desc | drop |
| rock band (gtr/drums/bass) | MUST | no — LoRA | `instrumentation:` | drop |
| symphonic/orchestral layer | SHOULD | no — LoRA | `Symphonic…orchestral` | drop |
| mix aesthetic (centered/audiophile) | SHOULD | no — LoRA | `production:` | drop |
| **emotional arc** | SHOULD | **yes** (variable) | `Mood:` | **KEEP** (curate) |
| tempo | SHOULD | no reliable text; false anchor | `110 BPM` | **DROP** |
| "ballad / hymn-like / stately" | nice→harmful | no — LoRA; anchors slow/sparse | `genre` | **DROP** |
| "vocals pulling instrumentation down…" | nice→harmful | no — LoRA; anchors ducking | `production` | **DROP** |

### Recommended style (no lyrics change)

```
arabmaqamrock Maqam Ajam. Mood: Epic, Enduring, Triumphant.
```

### What replaces what

- The **only** output features that need prompt text are the ones the trigger can't know:
  **Maqam** (must) and **Mood** (should). Both were the only variable axes in training.
- Everything else on the MUST/SHOULD list is an output feature the trigger+adapter is
  trained to produce — re-stating it adds no information.
- **Ceiling:** if a MUST feature (e.g. full-band arrangement) turns out weak under this
  minimal style, that's evidence it is *not* held by the adapter — and more words won't
  add it; a structural lever (Branch B / ABC) would. The ablation tells us which.

### Test ladder (style only; lyrics identical)

| | style | isolates |
|---|---|---|
| L0 | as-is (raw Suno block, today) | control |
| L1 | trained flat shape, all clauses | format |
| L2 | L1 − target constants (vocals, instrumentation) | redundancy rule |
| L3 | L1 − anti-target constants (genre, production) | truth rule #1 |
| L4 | `arabmaqamrock Maqam <M>. Mood: <mood>.` | minimal |

### Later: which script to change

`akbargherbal/suno-workflow` → `scripts/maqam_prompt_generator.py`
(`GENRE_STANDARD` L66, `PRODUCTION_STANDARD` L85, `INSTRUMENTATION` L98,
`build_vocals` L205; `EXCLUDE` L107 = never trained). Output → `styles` in
`workspace_manifest.json` → `ostris_prepare_dataset/prepare_yue2_dataset_v2.py:71`.
Not touched now.

## Branch B (only if a MUST feature proves adapter-weak)

Python SheetSage2 front end DONE. 1-track cover render: existing `bin/audiocpp_cli`,
`cot=melody` + `abc_file`, seed of the v2 track; call the binary directly
(`run_one.sh:79` hardcodes `cot=off`). Do NOT rebuild audio.cpp.
