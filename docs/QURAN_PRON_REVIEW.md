# Quran pronunciation LoRA — objective, criteria & next-run review

Status: **review + plan (2026-10-04), pending user decisions.** No training, no
config edited. Written after the 6-arm probe listening verdict
([`QURAN_FORMAT_PROBE.md`](QURAN_FORMAT_PROBE.md)): recitation *style* transfers,
but **pronunciation is unusable in all six arms**. Purpose: stop repeating GPU
sessions that cannot meet the goal.

Companion / prior art: [`QURAN_ONLY_EXPERIMENT.md`](QURAN_ONLY_EXPERIMENT.md),
[`FUTURE_PRONUNCIATION_LORA.md`](FUTURE_PRONUNCIATION_LORA.md),
[`PRON_LORA_LONG.md`](PRON_LORA_LONG.md),
[`PRON_LORA_VERIFICATION.md`](PRON_LORA_VERIFICATION.md). External:
`github.com/akbargherbal/quran_recitation_training_dataset` (the `aqfilter`
quality filter).

## 0. The reframed objective (user, 2026-10-04)

- **Old frame (rejected):** "make a few letters (ح خ ض ع) clearer." Too weak — it
  was a ceiling that never asked for correctness.
- **New frame:** *given any Quranic aya, recite it with correct tajwīd, ḥarakāt,
  makhārij and waqf — essentially error-free at α=1.* The base model is already
  competent at Arabic, so the deliverable is **correct recitation**, not a few
  clearer letters.
- **Corrected symptom framing (user, 2026-10-04):** the adapter is not merely
  failing to sharpen ح/ع — it appears to have **traded word-correctness for
  recitation prosody**: it now imitates tajwīd madd/waqf (plausibly a gain) while
  **mispronouncing the words**. This looks like a mild **catastrophic
  forgetting / over-specialisation** (see §2.7), though that is a hypothesis, not
  established. Either way, **the training method itself must be re-examined**.

## 1. Acceptance criteria (proposal — needs sign-off)

The old acceptance signal was the wrong instrument, so define the new one **before**
any GPU spend.

- **Free-running, not teacher-forced.** Judge pronunciation on audio generated
  from the text alone. A teacher-forced loss cannot see exposure-bias errors (§2.1).
- **Objective per-aya error rate.** Held-out set (≥20 ayat, must include
  ح خ ع ق ط ض ظ, madd, waqf, and short/long lengths). Force-align or ASR the
  generated recitation and compare to the expected text → letter/phoneme error
  rate, reported per aya.
- **Human blind gate.** `ab-blind-eval`; hard letters judged with tashkeel visible.
- **Suggested bar:** ≥90% of held-out ayat with **zero** makhraj errors, no
  systematic error on the 7 hard letters, at α=1.

## 2. Audit — where the errors could be

### 2.1 Evaluation was teacher-forced (definite, verified)

`docs/PRON_LORA_VERIFICATION.md:98-166` accepts an adapter on `ar_ce`/`ar_kl` only,
replayed on the val set with **ground-truth prefixes**. Training runs with
`disable_sampling: true` (`config/quran_long_aya_r8_s10.yml:93`) — no generation
during the run. A falling `ar_ce` alongside bad free-running output is textbook
exposure bias. **This is the primary criteria error:** the proxy could not have
caught the failure it was used to rule out.

### 2.2 No generation gate before merge/listen

The first listening test on the pron adapter happened only after the whole
pipeline (the 2026-10-04 probe). Nothing forced a free-run listen at checkpoint
time.

### 2.3 Training data (partly addressed by the new AHH set; one residual)

- **Fixed:** the 9-reciter corpus had heterogeneous recording quality. The new
  **AHH filtered** set limits to 3 reciters (Abdul_Basit_Murattal, Hudhaify,
  Husary) and keeps **9,492 / 13,501** clips by reference-calibrated
  DNSMOS + signal filtering (`quran_recitation_training_dataset`,
  `FILTERED_DATASET_README.md`). Verified in GCS:
  `quran_dataset_AHH_long_aya/` = 13,501 mp3 / 4,650 distinct ayat;
  `AHH_Quran_Long_Aya_Filtered_DATASET.zip` = 9,492 kept + `MANIFEST.csv`.
  This is a **quality** filter — it does not dedup, trim, or re-encode.
- **Residual — two orthographies over identical audio.** The old build pairs the
  same audio with `_simple` *and* `_uthmani` text (verified: both are fully
  diacritized, e.g. `الْكِتَابُ` vs `ٱلْكِتَـٰبُ`). Likely benign text
  augmentation, but it doubles cost for one variable; a single canonical Uthmani
  is cleaner.
- **Verified artifact mismatch (old dataset).** Its own
  `selection_report.json` claims **81,006** train pairs; GCS holds **67,505**
  (`_uthmani` 40,503 + `_simple` 27,002 — `_simple` missing for 13,501 combos).
  The artifact did not match its manifest. Not yet root-caused; not assumed to be
  the cause of the listen failure.

### 2.4 Config candidates (hypotheses to test — configs are the user's; never edited on initiative)

From `config/quran_long_aya_r8_s10.yml`:

- `ar_kl_weight: 0.2` (:115) anchors the AR to the base distribution. If the base
  articulation is wrong, the anchor preserves some of it.
- `linear 8` / `linear_alpha 8` (:34-35) — rank-8 AR-only may be too small to
  remap phonemes across 28 layers.
- EMA 0.999 (:88-90) — the saved final adapter is an EMA; it may average toward base.
- int8 `convrot8` QLoRA (:106).
- Inert for an AR-only adapter: `content_or_style`, `conv`/`conv_alpha` (see
  `PRON_LORA_VERIFICATION.md` A4/A6).

### 2.5 Generation/sampler pathology (verified signal)

Looping is caption-sensitive (probe: NASHEED ×7 vs QURAN ×3 on the same poem), so
part of the failure is at generation time, not only in the weights. A cheap knob
test is already designed on branch `pron-lora-knobs-investigation`
(`docs/investigation_generation_knobs.md`): `guidance_scale` 1.0/1.5,
`semantic_temperature` 0.8, `semantic_repetition_penalty` 1.4 / `penalty_window` 100.

### 2.6 Representational ceiling (decisive, cheap)

`FUTURE_PRONUNCIATION_LORA.md:143-148`: the MERT semantic (AR) tokens may not
separate the pharyngeal/emphatic contrasts. If the **base model, no LoRA**, cannot
produce crisp ح/ع on held-out hard-letter text, no adapter or dataset fixes it.
This must be tested **before** any training.

### 2.7 Catastrophic-forgetting hypothesis (user, unverified)

Symptom: the adapter learns recitation *prosody* (madd/waqf) but degrades *word*
pronunciation. One reading is **catastrophic forgetting / over-specialisation**:
an AR-only, whole-clip, 1-epoch LoRA on a narrow domain shifts the AR toward
recitation motifs at the cost of the base model's Arabic word accuracy.

Two counter-readings must be ruled out first: it could instead be (a) the same
**representational ceiling** (§2.6), or (b) **inference-time prosody bleed** —
the added madd stretches vowels and distorts the short vowels/ḥarakāt of the
words. The `ar_kl_weight: 0.2` trust-region also argues *against* full
forgetting (it holds the AR near the base).

Cheap ways to tell them apart (no retrain):

- Base (no LoRA) vs adapter on the **same** text, free-run. Word errors only with
  the adapter ⇒ adapter/forgetting; base also wrong ⇒ ceiling.
- Check whether errors **co-occur with the added madd** (prosody corrupting
  phonemes) vs independent word errors.
- If adapter-specific: ablate `ar_kl_weight`, rank, lr, or epochs; and track a
  **general-Arabic word-accuracy** metric during training to catch drift.

## 4. Assumptions & hypotheses — re-opened

| Old assumption | Status | New position |
|---|---|---|
| Success = hearing ح/ع clearly | **retired** | correct words + prosody, free-run, error-free at α=1 (§0) |
| `ar_ce`/`ar_kl` improving ⇒ pronunciation improving | **wrong** | teacher-forced proxy; replaced by a free-run eval (§1, §2.1) |
| Recording quality wasn't the variable | **revised** | quality-filtered AHH set is the base dataset (§2.3) |
| The adapter only needs to *add* articulation | **re-opened** | adapter may add prosody while degrading words (§0, §2.7) |
| MERT tokens carry the contrasts | **untested** | decisive base-model probe (§2.6) |
| The old dataset matched its manifest | **false** | 67,505 actual vs 81,006 claimed pairs (§2.3) |

## 5. Ordered plan (cheapest first; each phase gates the next)

**Phase 0 — CPU (now).** Build the eval harness + held-out manifest; adapt
`prepare_pron_dataset.py` to pair the AHH set with Tanzil text; validate counts;
freeze §1.

**Phase 1 — GPU minutes. Ceiling / adapter probe.** base (no LoRA) vs existing
`quran_only`, same held-out hard-letter ayat, same seed, free-run. If base is also
wrong → representation ceiling; stop the LoRA line here.

**Phase 2 — GPU ~30 min. Sampler probe** on the existing adapter
(guidance/temperature/repetition). If looping persists on correct captions, it is
in the weights (§2.4), not the sampler.

**Phase 3 — GPU training on AHH, only if 1–2 justify it.** New run identity +
config (rank / lr / `ar_kl_weight` as chosen), with a **mandatory per-checkpoint
free-generation eval** and a human gate before any merge.

## 6. Open decisions (need user sign-off)

1. Single canonical Uthmani caption, or keep `simple` + `uthmani`?
2. Acceptance bar — adopt "≥90% of held-out ayat with zero makhraj errors"?
3. Which config variable to move first (§2.4): `ar_kl_weight`, rank, or lr?
4. Confirm the AHH filtered zip is the training source, and where to stage it.

## See also

- [`QURAN_FORMAT_PROBE.md`](QURAN_FORMAT_PROBE.md) — the listening verdict this audit follows.
- [`FUTURE_PRONUNCIATION_LORA.md`](FUTURE_PRONUNCIATION_LORA.md) — the ceiling-risk hypothesis.
- [`PRON_LORA_LONG.md`](PRON_LORA_LONG.md) — the run that produced `quran_only`.
