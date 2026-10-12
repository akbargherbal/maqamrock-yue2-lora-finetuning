# current.md — Probe Q read-out (2026-10-12)

Copy/read surface only, not authority. Authority = the banked audio
`…/v3_arabmaqamrock_lora/probe_q/{,eval}` (7 files) + the run dirs under
`/content/audiocpp_inference/out/v3_probe_q/`. Design = arm table below +
`docs/INFERENCE.md`.

## Run facts (commit `4387dba`, this Colab session)

**6/6 tracks `exit=0`, none truncated, all 48 kHz stereo**, one session, one pinned
seed `2640605763`, cap `7000`. Wall 08:21:05Z → 09:18:13Z ≈ **57 min** (≈8.9 min/track;
the dry-run's 6.5 min/track was optimistic). Adapters sha256 `3531bb91…` / `a7eabcad…`
(match Probe S). Driver log:189 → `banked -> …/v3_arabmaqamrock_lora/probe_q`. GPU free
(0 MiB / 0 %) at start and end. Lyric file sha256 `8a5e9fba…`, byte-identical across all arms.

## Pull the eval package to the local machine (Windows)

Seven files, one arm per file, blind-scored:

```bat
gsutil -m rsync -r gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/v3_arabmaqamrock_lora/probe_q/eval "C:\Users\DELL\Downloads\v3_probe_q\eval"
```

(`gcloud storage rsync -r <same>/probe_q/eval "…\eval"` is the equivalent on the newer CLI.)

## Rate (Windows box, rating-app dir)

Same scorecard as Probe S so the numbers stay comparable:

```bat
cd C:\Users\DELL\Jupyter_Notebooks\ai_music_rating_app
py app.py --audio "C:\Users\DELL\Downloads\v3_probe_q\eval" --label v3_probe_q --blind --scorecard "C:\Users\DELL\Downloads\v3_spice.json"
```

## Eval folder = exactly 7 files (banked, verified)

| file | arm | style | EXTRA_REQUEST_OPTS (as applied) | ch/sr | dur |
|---|---|---|---|---|---|
| `v3q_Q0_ctm_default.wav` | `v3q_Q0_ctm_default` | CTM 41 w | — (guidance 1.01, rep-pen 1.2) | 2/48k | 217.8 s |
| `v3q_Q1_ctm_g15.wav` | `v3q_Q1_ctm_g15` | CTM | `guidance_scale=1.5` | 2/48k | 224.0 s |
| `v3q_Q2_ctm_g20.wav` | `v3q_Q2_ctm_g20` | CTM | `guidance_scale=2.0` | 2/48k | 228.0 s |
| `v3q_Q3_ctm_rp135.wav` | `v3q_Q3_ctm_rp135` | CTM | `semantic_repetition_penalty=1.35` | 2/48k | 232.4 s |
| `v3q_Q4_ctm_g15rp135.wav` | `v3q_Q4_ctm_g15rp135` | CTM | `guidance_scale=1.5 semantic_repetition_penalty=1.35` | 2/48k | 214.0 s |
| `v3q_Q5_retarget_g15.wav` | `v3q_Q5_retarget_g15` | T3 retarget 32 w | `guidance_scale=1.5` | 2/48k | 227.6 s |
| `ANCHOR_s1_core.wav` | Probe S `S1_core` | T2 26 w | free drift anchor (already rated 4) | 2/48k | 228.1 s |

Anchor = copy of the banked `…/prompt_probe/lora_on/v3pp_S1_core_2640605763.wav`
(43,791,148 B) — no GPU track spent (deterministic re-render would be byte-identical).

## Knob check — proved from the runtime trace, not the manifest

Caution: `batch_manifest.json` **does not record** `EXTRA_REQUEST_OPTS` (its `tracks[]`
schema is idx/name/take/seed/cap/quantile/n_letters/style_file/style_sha256/lyrics_file/
lyrics_sha256 only). The applied knob is proven by the audio.cpp trace in each arm's
`.log` (line 16 `yue2.request … guidance_scale=` / line 17 `yue2.sampling.semantic …
repetition_penalty=`) and the exact CLI args in each `_time.txt`. All five groups applied
the intended opts:

| arm | `guidance_scale` (log:16) | `repetition_penalty` (log:17) | intended? |
|---|---|---|---|
| `Q0` | `1.01` | `1.2` | ✅ defaults |
| `Q1` | `1.5` | `1.2` | ✅ |
| `Q5` | `1.5` | `1.2` | ✅ |
| `Q2` | `2` | `1.2` | ✅ |
| `Q3` | `1.01` | `1.35` | ✅ |
| `Q4` | `1.5` | `1.35` | ✅ |

No group silently fell back to defaults; no OOM; no truncation (`trunc=no` on all six).

## What the arms test (read-out, do not judge here)

- **Q0 vs Q1 vs Q2** — does `guidance_scale` help on the *pruned* prompt, and where is the
  knee? (Pass 1 said 1.5 good / 2.5 breaks arrangement — but against the bad template.)
- **Q3 vs Q0** — does the repetition penalty strip repeats the model *adds* on top of the text?
- **Q4** — guidance + penalty combined.
- **Q5** — the retarget wording (only above-baseline arm in Probe S) at guidance 1.5.
- **ANCHOR** — literally the audio already rated 4; any score change is listener drift.

Constraint (user): **LYRICS FROZEN.** `INFERENCE/probe_q_lyrics.txt` is byte-verbatim and
shared by every arm; no lyric edits of any kind.

## Run / stop / resume (Colab, GPU VM, detached)

```bash
cd /content/maqamrock-yue2-lora-finetuning && git pull
DRY=1 bash INFERENCE/v3_probe_q.sh                               # CPU validation, must plan 6
gcloud storage rsync -r "$GCP_BACKUP_BASE/v3_arabmaqamrock_lora/convert" /content/converter/out
bash bootstrap/setup.sh --inference > /content/logs/setup.log 2>&1
setsid nohup bash INFERENCE/v3_probe_q.sh > /content/logs/v3_probe_q.log 2>&1 < /dev/null & disown
tail -f /content/logs/v3_probe_q.log
```

Stop: `pkill -f v3_probe_q.sh` · Resume: rerun the launch line (same `OUTROOT` → succeeded
takes skip). Output: `…/out/v3_probe_q/{q0,q1_q5,q2,q3,q4}/`, one `v3q_<arm>_2640605763.wav`
each. Banks: `…/v3_arabmaqamrock_lora/probe_q/{q..,eval/}`.
