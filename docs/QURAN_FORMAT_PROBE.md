# Quran adapter — format/caption probe (GPU test)

Status: **run 2026-10-04 — 6/6 rendered; listening verdict pending** (branch
`experimental-quran-pron`). The input
manifest is [`INFERENCE/songs.quran_format_probe.json`](../INFERENCE/songs.quran_format_probe.json);
the live copy-paste handoff is `agent_notes/current.md`. Companion to
[`QURAN_ONLY_EXPERIMENT.md`](QURAN_ONLY_EXPERIMENT.md) (the α=1 first sample this follows up on).

## Background

The α=1 Quran adapter (Quran pron LoRA alone, no v2 style LoRA) rendered one **~52 s**
passage and stopped, with a model-chosen EOS (`semantic.truncated 0`), not the 7500 cap —
see `QURAN_ONLY_EXPERIMENT.md:54-90`. That sample was generated with the **song** section
tags (`[Intro]`, `[Verse 1]`, `[Chorus]`, `[Outro]`), but the adapter has only ever seen a
single, bare `[Verse]` line.

Training layout (exact, from the dataset builders):

- `prepare_pron_dataset.py:208-210` — `make_caption` writes
  `f"{prompt}\n[Lyrics]\n[Verse]\n{aya_line}\n"`.
- `append_ayah_symbol.py:5-9` — the template is 4 non-empty lines; only the aya line is
  touched, appending ` ۝` (U+06DD, ARABIC END OF AYAH).
- `docs/PRON_LORA_LONG_PLAN.md:36,40-43` — clips are **single** ayat, `min_words=6 …
  max_words=60`; the prompt is
  `Solo male voice, unaccompanied. Quran recitation. Clear precise classical Arabic diction. Spoken Words.`

So the in-domain input is: **one aya, under `[Verse]`, ending in ` ۝`**, under that one
caption. The first sample was out-of-domain in its section tags and section count. The
known length finding (an AR-only adapter governs sequence length; its clips averaged ~23 s)
is a *separate* hypothesis this test also bears on.

## Questions this probe answers

1. Does conforming to the training layout (single `[Verse]`) change the output vs. the
   section-tagged first sample?
2. Does the ` ۝` true-end marker change when/if it stops, vs. its absence?
3. Does caption/style wording move articulation at all (Quran vs nasheed vs tarab vs qasida)?
4. In-domain yardstick: how good is a raw ayah (open-source text) vs. non-Quran poetry?

## Arms (6)

All arms: adapter `quran_only` (AR scale 1.0, NAR scale 0.0), seed `20261004`, cap `7500`,
run with `generate.py --no-trigger`. Uniform cap means **EOS is the only intended stop**, so
durations are comparable across arms.

| Song | Lyrics | Caption | Isolates |
|---|---|---|---|
| `T1_poem_endmark` | 8-couplet poem, single `[Verse]`, ` ۝` at the very end | QURAN | format baseline |
| `T2_poem_nomark` | same poem, **no** `۝` | QURAN | `۝` effect (vs T1) |
| `T3_poem_nasheed` | poem + `۝` | NASHEED | caption |
| `T4_poem_khaliji` | poem + `۝` | KHALIJI TARAB | caption |
| `T5_poem_qasida` | poem + `۝` | QASIDA | caption |
| `T6_anchor_ayat_kursi` | **Āyat al-Kursī** (al-Baqarah 2:255, 58 words) + ` ۝` | QURAN | in-domain fidelity |

The poem is one song's 8 couplets from `manifests/batch_36_songs.json`, deduped and without
section markers. The T6 ayah is sourced from the **open** Quran API
(`api.alquran.cloud/v1/ayah/2:255/quran-uthmani`), not from the training set.

## Run on the GPU VM

Prerequisites (details in the linked docs):

1. **Rebuild the `quran_only` adapter** — it is not GCS-mirrored; rebuild from the backed-up
   pron source per `QURAN_ONLY_EXPERIMENT.md:35-52` (`build_pron_only_fused.py` → converter →
   `/content/converter/out/quran_only/`).
2. **CUDA-12 loader path** — the prebuilt sm_75 `audiocpp_cli` dies `exit=127` on a CUDA-13
   image without it (`docs/COMMAND_HANDOVER_GOTCHAS.md`, 2026-10-04).
3. **GPU idle** — `nvidia-smi` before starting.

```bash
cd /content/maqamrock-yue2-lora-finetuning
setsid nohup python INFERENCE/generate.py \
  INFERENCE/songs.quran_format_probe.json --no-trigger \
  --label quran_format_probe > /content/logs/quran_format_probe.log 2>&1 & disown
```

Detached: survives Ctrl+C / closing the tab. Stop with `pkill -f quran_format_probe`.
Progress in `out/latest` + `_runs_status.log`. Projected worst case ~39 min on a T4.

## Reading the result

- **Per-track JSON / `_runs_status.log`:** `semantic.tokens` and `truncated` (0 = EOS, 1 =
  hit cap). Duration differences between T1/T2 and the first sample are the signal.
- **Listening:** judge the hard letters ح خ ع ق ط ض ظ with the tashkeel text visible.
  T1-vs-T2 = the `۝`; T2-vs-first-sample = the tags; T3/T4/T5-vs-T1 = the caption; T6 =
  in-domain ceiling.
- Package a blind A/B with the `ab-blind-eval` skill / `INFERENCE/prepare_ab_eval.py`
  (`docs/AB_BLIND_EVAL.md`).

## Run result (2026-10-04, T4)

Run dir `out/20261004-154634_quran_format_probe/`. 6/6 `exit=0`, **all
`semantic.truncated=no`** (every track stopped on a model-chosen EOS, never the
7500 cap), total wall 18:09.

| # | track | caption | dur_s | trunc |
|---|---|---|---|---|
| T1 | poem + `۝` | QURAN | 94.3 | no |
| T2 | poem, no `۝` | QURAN | 75.8 | no |
| T3 | poem + `۝` | NASHEED | 94.2 | no |
| T4 | poem + `۝` | KHALIJI TARAB | 106.7 | no |
| T5 | poem + `۝` | QASIDA | 107.0 | no |
| T6 | Āyat al-Kursī + `۝` | QURAN | 49.3 | no |

Objective duration reads only (quality/articulation verdict requires listening):
`۝` adds ~18 s (T1 94.3 vs T2 75.8); the training-layout `[Verse]` fix roughly
doubled the earlier ~52 s first sample; T6 (in-domain aya) ≈ that old ~52 s;
caption wording moved the poem only slightly (T3/T4/T5 94–107 s).

## See also

- [`QURAN_ONLY_EXPERIMENT.md`](QURAN_ONLY_EXPERIMENT.md) — the α=1 experiment and first sample.
- [`PRON_LORA_LONG.md`](PRON_LORA_LONG.md) — the training run this adapter came from.
- [`text_to_duration_formula.md`](text_to_duration_formula.md) — how the cap is derived.
