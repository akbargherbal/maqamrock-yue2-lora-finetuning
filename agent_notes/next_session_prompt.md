# Next-session prompt — run Probe S (prompt sensitivity × LoRA on/off) on Colab

_Created 2026-10-12. Paste the block below into the Colab session. This file is a copy surface, not
authority — authority is `agent_notes/current.md` ("Probe S") + `INFERENCE/v3_prompt_probe.sh`._

```text
Fresh Colab GPU runtime. Repo: akbargherbal/maqamrock-yue2-lora-finetuning, branch main
(expect 3bd25e9 or newer — it adds the probe files below).

Your job: run "Probe S" end to end, then hand me a listening command. I am present, but do not wait
on me for steps — only stop and ask if the GPU is busy, or if something looks wrong.

Why (short): v3's sound is anchored but generic. Probe S measures whether the STYLE PROMPT actually
moves the output, and how much the LoRA is carrying, by running ONE song + ONE seed with (a) four
prompt tiers and (b) the adapter switched off (scale 0).

Read first, in order:
  1. agent_notes/current.md — live state; the "Probe S" section is the spec (arm table, read-out,
     prompt tiers T0-T3, the "110 BPM" measurement).
  2. INFERENCE/v3_prompt_probe.sh — driver; its header lists the 6 arms.
  3. INFERENCE/songs.v3_prompt_probe.json + INFERENCE/songs.v3_prompt_probe.base.json
  4. docs/INFERENCE.md (runner + JSON schema), docs/V3_SPICE_SWEEP.md (background).

GCS base: gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning

Steps:
1. Env check: /content exists. Run `nvidia-smi` — if ANY compute process is running, or you cannot
   confirm the GPU is free, STOP and ask. One shared GPU; never overlap.
2. cd /content/maqamrock-yue2-lora-finetuning (git pull, or clone main if absent).
3. CPU validation, no GPU:  DRY=1 bash INFERENCE/v3_prompt_probe.sh
   -> must plan 4 (lora_on) + 2 (lora_off) arms, all seed 2640605763, cap 7000.
4. Stage inference:  bash bootstrap/setup.sh --inference > /content/logs/setup.log 2>&1
   then grep the log for [FAIL] — there must be none.
5. Stage the final adapter pair:
   gcloud storage rsync -r "$GCP_BACKUP_BASE/v3_arabmaqamrock_lora/convert" /content/converter/out
   -> require /content/converter/out/v3_arabmaqamrock_lora_{ar,nar}.safetensors
6. Sidecars (AGENTS.md §10): pgrep -af 'backup_to_gcp.py|gpu_logger.py'; vm-continuity status.
   If one is down, start it (or note it and continue rather than blocking the session).
7. Report GPU state + disk free, then launch DETACHED:
   setsid nohup bash INFERENCE/v3_prompt_probe.sh > /content/logs/v3_prompt_probe.log 2>&1 < /dev/null & disown
   tail -f /content/logs/v3_prompt_probe.log        # expect ~39 min (6 tracks x ~6.5 min)
   Do not block or tight-poll: report progress from the log, e.g. pgrep -af 'v3_prompt_probe|generate.py'.

Verify from artifacts when it finishes — quote the lines, do not paraphrase:
  - 6 WAVs, all exit 0, none truncated:
      out/v3_prompt_probe/lora_on/v3pp_{S0_full,S1_core,S2_retarget,S4_prune}_2640605763.wav
      out/v3_prompt_probe/lora_off/v3pp_{B1_base_full,B2_base_core}_2640605763.wav
  - each .log ends "Exit status: 0"; durations sane; no OOM.
  - the bank line: banked -> .../v3_arabmaqamrock_lora/prompt_probe
  - flag anything anomalous (especially if the adapter-scale-0 arms fail).

Do NOT: start a second copy; retrain; touch /content/yue2_dataset; edit the manifests, the pinned
seed, or the cap; edit the adapters. You cannot hear the audio — do not judge the takes; the read-out
is mine.

Then hand me the listening step:
  - Build a flat eval folder of 6 files, one per arm, named by arm:
      out/v3_prompt_probe/eval/{S0_full,S1_core,S2_retarget,S4_prune,B1_base_full,B2_base_core}.wav
  - Scorecard: INFERENCE/scorecards/v3_spice.json (also banked at
    <base>/v3_arabmaqamrock_lora/spice_probe/v3_spice_scorecard.json).
  - Give me exactly one rating-app command to run on my Windows box:
      py app.py --audio "<eval folder>" --label v3_prompt_probe --blind --scorecard "<v3_spice.json>"
    (from the ai_music_rating_app folder; --blind hides the arm names and shuffles, the report reveals them.)

Report back with: the log tail, the 6-file verification table, GPU state at start and end, the GCS
bank confirmation, and the rating command. State plainly what you verified vs what you assumed.
```
