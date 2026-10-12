# Next-session prompt — run Probe Q (pruned style × guidance × rep-penalty) on Colab

_Created 2026-10-12. Paste the block below into the Colab session. Copy surface, not authority —
authority is `agent_notes/current.md` ("Probe Q") + `INFERENCE/v3_probe_q.sh`._

```text
Fresh Colab GPU runtime. Repo: akbargherbal/maqamrock-yue2-lora-finetuning, branch main
(expect d7759bf or newer — it adds the Probe Q manifests).

Your job: run "Probe Q" end to end, then hand me ONE rating command for my Windows box. I am present,
but do not wait on me for steps — stop and ask only if the GPU is busy, or if something looks wrong.

Context in two lines: Probe S proved the style prompt is a live lever, and that the as-trained 95-word
template is the WORST one (it inverts the mood — celebratory music on a grim poem, with the LoRA on AND
off). Probe Q crosses the pruned ~41-word style with the sampler knobs that were never crossed:
guidance_scale (Pass 1 measured it only against the bad template) and the repetition penalty.

READ FIRST, in order:
  1. agent_notes/current.md      — live state; the "Probe Q" section is the spec (arm table, knobs,
                                   artifact list, run + eval commands).
  2. INFERENCE/v3_probe_q.sh     — driver; its header lists the 6 arms.
  3. INFERENCE/songs.v3_probe_q.*.json + INFERENCE/probe_q_lyrics.txt
  4. docs/INFERENCE.md (runner + JSON schema; lines ~98-112 for the sampler knobs / EXTRA_REQUEST_OPTS).

GCS base: gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning

HARD CONSTRAINTS — the user's, do not touch:
  - LYRICS ARE FROZEN. No lyric edits, not even dropping a verse, not even "just one line".
    INFERENCE/probe_q_lyrics.txt is byte-verbatim and shared by every arm.
  - Do not edit the manifests, the pinned seed (2640605763), or the cap (7000).
  - Do not edit the adapters. Do not retrain. Do not touch /content/yue2_dataset.
  - You cannot hear audio. Do not judge the takes — the read-out is mine.

Steps:
1. Env: /content exists. Run `nvidia-smi`. If ANY compute process is running, or you cannot confirm the
   GPU is free, STOP and ask. One shared GPU; never overlap.
2. cd /content/maqamrock-yue2-lora-finetuning && git pull   (or clone main if absent)
3. CPU validation, no GPU:   DRY=1 bash INFERENCE/v3_probe_q.sh
   -> must print 5 groups and plan 6 tracks, all seed 2640605763, cap 7000. If it does not match, stop
      and report; do not "fix" it.
4. Stage inference:  bash bootstrap/setup.sh --inference > /content/logs/setup.log 2>&1
   then grep the log for [FAIL] — there must be none.
5. Stage the final adapter pair:
   gcloud storage rsync -r "$GCP_BACKUP_BASE/v3_arabmaqamrock_lora/convert" /content/converter/out
   -> require /content/converter/out/v3_arabmaqamrock_lora_{ar,nar}.safetensors
6. Sidecars (AGENTS.md §10): pgrep -af 'backup_to_gcp.py|gpu_logger.py'; vm-continuity status.
   Start what's missing — or note it and continue; do not block the session on it.
7. Report GPU state + disk free, then launch DETACHED:
   setsid nohup bash INFERENCE/v3_probe_q.sh > /content/logs/v3_probe_q.log 2>&1 < /dev/null & disown
   tail -f /content/logs/v3_probe_q.log     # budget ~53 min (measured 8.8 min/track x 6; last time the
                                            # dry-run's 6.5 min/track projection was 35% optimistic)
   Do not block or tight-poll; report progress from the log.

VERIFY from artifacts when it finishes — quote the lines, do not paraphrase:
  - 6 WAVs, each .log ending "Exit status: 0", none truncated, 48 kHz stereo, durations sane:
      out/v3_probe_q/q0/v3q_Q0_ctm_default_2640605763.wav
      out/v3_probe_q/q1_q5/v3q_Q1_ctm_g15_2640605763.wav
      out/v3_probe_q/q1_q5/v3q_Q5_retarget_g15_2640605763.wav
      out/v3_probe_q/q2/v3q_Q2_ctm_g20_2640605763.wav
      out/v3_probe_q/q3/v3q_Q3_ctm_rp135_2640605763.wav
      out/v3_probe_q/q4/v3q_Q4_ctm_g15rp135_2640605763.wav
  - EACH of the 5 run dirs' batch_manifest.json shows the intended EXTRA_REQUEST_OPTS for its group
    (q0 = defaults). This is the only proof the knobs were actually applied — check it, don't assume it.
  - the bank line: banked -> .../v3_arabmaqamrock_lora/probe_q
  - flag anything anomalous: a group that silently fell back to defaults, an OOM, a truncated take.

THEN build the listening package — a flat folder of exactly 7 files, named by arm:
  - Copy the 6 new takes out of the 5 run dirs into out/v3_probe_q/eval/ as
      v3q_Q0_ctm_default.wav, v3q_Q1_ctm_g15.wav, v3q_Q2_ctm_g20.wav, v3q_Q3_ctm_rp135.wav,
      v3q_Q4_ctm_g15rp135.wav, v3q_Q5_retarget_g15.wav
  - 7th file = the FREE DRIFT ANCHOR, from the banked Probe S run. Generation is deterministic, so
    re-rendering that arm would be byte-identical — do NOT spend a GPU track on it:
      gcloud storage cp "$GCP_BACKUP_BASE/v3_arabmaqamrock_lora/prompt_probe/lora_on/v3pp_S1_core_2640605763.wav" \
        out/v3_probe_q/eval/ANCHOR_s1_core.wav
    If that exact object 404s, `gcloud storage ls -r "$GCP_BACKUP_BASE/v3_arabmaqamrock_lora/prompt_probe"`
    to locate it, and say so rather than skipping the anchor. Confirm non-empty + 48 kHz stereo.
  - Bank the package:  gcloud storage rsync -r out/v3_probe_q/eval "$GCP_BACKUP_BASE/v3_arabmaqamrock_lora/probe_q/eval"

Report back with: the log tail, the 6-file + anchor verification table, the batch_manifest knob check,
GPU state at start and end, the bank confirmation, and the rating command below. State plainly what you
verified vs what you assumed.

Rating command for my Windows box (7 files, blind, same scorecard as Probe S so the numbers stay
comparable):
  cd C:\Users\DELL\Jupyter_Notebooks\ai_music_rating_app
  py app.py --audio "C:\Users\DELL\Downloads\v3_probe_q\eval" --label v3_probe_q --blind --scorecard "C:\Users\DELL\Downloads\v3_spice.json"

What the arms test (for MY read-out — you do not judge):
  Q0 vs Q1 vs Q2  -> does guidance_scale help on the PRUNED prompt, and where is the knee?
                     (Pass 1 said 1.5 good, 2.5 breaks arrangement/coherence — but that was against the bad template.)
  Q3 vs Q0        -> does the repetition penalty strip repeats the model ADDS on top of the written text?
  Q4              -> guidance + penalty combined
  Q5              -> the retarget wording (the only above-baseline arm in Probe S) at guidance 1.5
  ANCHOR          -> literally the audio already rated 4; any score change in it is listener drift.
```
