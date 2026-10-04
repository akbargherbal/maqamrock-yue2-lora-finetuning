# current

## State @ 2026-10-04 (CPU VM) — Quran-pron review done; 4 decisions open

Branch `experimental-quran-pron`, HEAD `2299571`. Probe verdict recorded
(`docs/QURAN_FORMAT_PROBE.md`). Comprehensive review written:
**`docs/QURAN_PRON_REVIEW.md`** (objective + acceptance criteria + audit + ordered plan).
No config edited; no GPU work.

### The reframed objective (user)

Given any aya → recite with correct tajwīd/ḥarakāt/makhārij/waqf, error-free at α=1.
(Old "make a few letters clearer" ceiling is rejected.)

**Corrected symptom (user, unverified):** the adapter gained recitation *prosody*
(madd/waqf) but now **mispronounces words** — possibly mild catastrophic forgetting
or prosody bleeding into phonemes. Not established; see review §2.7. The training
method itself must be re-examined.

### Headline audit findings

- **Criteria error:** the adapter was accepted on teacher-forced `ar_ce`/`ar_kl` only
  (`PRON_LORA_VERIFICATION.md:98-166`), with `disable_sampling: true` — a proxy that
  cannot see free-running pronunciation errors. → define a free-run eval first.
- **Data:** old set = 9 reciters, uneven quality; new **AHH filtered** = 3 reciters
  (Abdul_Basit, Hudhaify, Husary), 9,492/13,501 kept, audio-only (pair with Tanzil).
- **Data counts (corrected):** the trained set was the **`quran_long_aya_dataset_s10.tar`
  subsample = 8,100 pairs** (10 %), NOT 81k/67.5k. `quran_long_aya_dataset/train` now
  holds 67,505 pairs because the three AHH reciters (Abdul_Basit, Hudhaify, Husary)
  were carved out as the new high-quality corpus, leaving them `_uthmani`-only
  (verified per reciter) — by design, not a bug.
- **Ceiling:** base-model / no-LoRA hard-letter test must run **before** any retrain
  (`FUTURE_PRONUNCIATION_LORA.md:143-148`).

### Open decisions (need user) — review §4

1. Single Uthmani caption vs keep `simple`+`uthmani`?
2. Accept "≥90% of held-out ayat with zero makhraj errors"?
3. Move `ar_kl_weight`, rank, or lr first?
4. Confirm AHH zip is the training source + where to stage it.

### Standing

`docs-reconciler` pass still outstanding (deferred from the GPU commit).
