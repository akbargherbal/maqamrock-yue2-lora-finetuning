# current

## State @ 2026-10-04 16:06 — format/caption probe RUN DONE (6/6) + repo pulled to dfcc1e8

Branch `experimental-quran-pron`, HEAD **`dfcc1e8`** (pulled from origin this session).
The other (web) session documented the probe; run below was executed here on a T4.

### What's on GitHub since last pull

`dfcc1e8 Document the Quran format/caption probe (GPU test background)` adds
`docs/QURAN_FORMAT_PROBE.md` (background + 6-arm design) and indexes it; updates
`RECONCILIATION_LOG.md`, `SOURCE_OF_TRUTH.md`, `docs/README.md`, `agent_notes/current.md`.
That doc still says "prepared, not yet run" — **now stale** (run finished below).

### Probe run — COMPLETE

- run dir: `/content/audiocpp_inference/out/20261004-154634_quran_format_probe/`
- adapter `quran_only` (AR 1.0 / NAR 0.0), seed `20261004`, cap `7500`, `--no-trigger`.
- 6/6 exit=0, **all `semantic.truncated=no`** (EOS, never the cap), total wall 18:09.

| # | track | caption | dur_s | trunc |
|---|---|---|---|---|
| T1 | poem + `۝` | QURAN | 94.3 | no |
| T2 | poem, no `۝` | QURAN | 75.8 | no |
| T3 | poem + `۝` | NASHEED | 94.2 | no |
| T4 | poem + `۝` | KHALIJI TARAB | 106.7 | no |
| T5 | poem + `۝` | QASIDA | 107.0 | no |
| T6 | Āyat al-Kursī + `۝` | QURAN | 49.3 | no |

Objective read (durations only; quality needs listening):
the `۝` adds ~18 s (T1 94.3 vs T2 75.8); the training-layout `[Verse]` fix roughly
doubled the first sample (~52 s under song tags); T6 (in-domain aya) ≈ the first
sample's ~52 s. Caption wording moved the poem only slightly (T3/T4/T5 94–107 s).

### Next

Listen / blind A/B per `docs/QURAN_FORMAT_PROBE.md` "Reading the result"
(`ab-blind-eval` skill / `INFERENCE/prepare_ab_eval.py`); judge ح خ ع ق ط ض ظ with
tashkeel visible. Then record the result into `docs/QURAN_FORMAT_PROBE.md`.

### Sidecars / backups

`backup_to_gcp.py --inference` (pid 15109) + `vm-continuity watch` (pid 15110) running.
