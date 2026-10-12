# current.md — Probe Q handoff (2026-10-12)

Copy/read surface only, not authority. Authority = the banked audio at
`…/v3_arabmaqamrock_lora/probe_q/` (+ `…/probe_q/eval/`) and the run dirs under
`/content/audiocpp_inference/out/v3_probe_q/`. Design + read-out: this file's
arm table + `docs/INFERENCE.md`.

> **STATUS: run IN PROGRESS — 5/6 tracks started, package not yet banked.**
> Last verified 2026-10-12T09:06Z: groups `default`, `g15`, `g20` done (`exit=0`);
> `rp135` generating; `g15rp135` pending. **This block is replaced with the verified
> read-out when the run + packaging finish.** Do not run the download command until
> this banner is gone.

## Pull the eval package to the local machine (Windows)

Seven files, one arm per file, blind-scored. Run after banking:

```bat
gsutil -m rsync -r gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/v3_arabmaqamrock_lora/probe_q/eval "C:\Users\DELL\Downloads\v3_probe_q\eval"
```

(`gcloud storage rsync -r <bucket>/…/probe_q/eval "…\eval"` is the equivalent if you
prefer the newer CLI.)

## Rate (Windows box, rating-app dir)

Same scorecard as Probe S so the numbers stay comparable:

```bat
cd C:\Users\DELL\Jupyter_Notebooks\ai_music_rating_app
py app.py --audio "C:\Users\DELL\Downloads\v3_probe_q\eval" --label v3_probe_q --blind --scorecard "C:\Users\DELL\Downloads\v3_spice.json"
```

## Eval folder = exactly 7 files

| file | arm | style | EXTRA_REQUEST_OPTS |
|---|---|---|---|
| `v3q_Q0_ctm_default.wav` | `v3q_Q0_ctm_default` | CTM 41 w | — (guidance 1.01, temp 1.0, rep-pen 1.2) |
| `v3q_Q1_ctm_g15.wav` | `v3q_Q1_ctm_g15` | CTM | `guidance_scale=1.5` |
| `v3q_Q2_ctm_g20.wav` | `v3q_Q2_ctm_g20` | CTM | `guidance_scale=2.0` |
| `v3q_Q3_ctm_rp135.wav` | `v3q_Q3_ctm_rp135` | CTM | `semantic_repetition_penalty=1.35` |
| `v3q_Q4_ctm_g15rp135.wav` | `v3q_Q4_ctm_g15rp135` | CTM | `guidance_scale=1.5 semantic_repetition_penalty=1.35` |
| `v3q_Q5_retarget_g15.wav` | `v3q_Q5_retarget_g15` | T3 retarget 32 w | `guidance_scale=1.5` |
| `ANCHOR_s1_core.wav` | `v3p_anchor` (Probe S `S1_core`) | T2 26 w | free drift anchor — the take already rated 4 |

All six generated arms: seed `2640605763`, cap `7000`, one session, LoRA on.
`ANCHOR_s1_core.wav` is a copy of the banked Probe S `v3pp_S1_core_2640605763.wav`
(43.79 MiB) — no GPU track spent (deterministic re-render would be byte-identical).

## What the arms test (read-out, do not judge here)

- **Q0 vs Q1 vs Q2** — does `guidance_scale` help on the *pruned* prompt, and where is
  the knee? (Pass 1 said 1.5 good / 2.5 breaks arrangement — but against the bad template.)
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
takes skip). Output: `…/out/v3_probe_q/{q0,q1_q5,q2,q3,q4}/`, one
`v3q_<arm>_2640605763.wav` each. Bank: `…/v3_arabmaqamrock_lora/probe_q`.
