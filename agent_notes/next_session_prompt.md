# Next-session prompt — T4 seed probe (you run it, I'm away)

_Created 2026-10-10. Paste the block below at the start of the T4 Colab session._
_Copy from here (vscode.dev text selection is glitchy; this file is a copy surface, not authority)._

```text
You are on a fresh Colab T4 VM. Take care of this job YOURSELF end to end — I am away and will
not be running commands. Run everything detached/in the background so nothing blocks, and report
from artifacts.

MISSION: render the v3 FINAL adapter on ONE Jarir song with 5 fresh random seeds (~1 h on a T4)
and bank the 5 takes.

Read first, in order: AGENTS.md -> agent_notes/current.md (live state) -> docs/V3_JARIR_SEED_PROBE.md
(the finalised plan; input INFERENCE/songs.v3_jarir_seed.json, runner
INFERENCE/run_v3_jarir_seed_probe.sh). Then VERIFY live, never recall:
    nvidia-smi          # expect a T4 and NO other compute process (one-GPU rule)
    git log -1          # expect main @ 115657a or newer
    gcloud storage ls gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/v3_arabmaqamrock_lora/convert/

0. CAN YOU RUN? If `nvidia-smi` works and /content exists, proceed. If NOT, say so in one line and
   hand me the single command to paste — do not pretend to run it.

1. PRECONDITIONS (done by the launching notebook; don't redo interactively):
   - `gcloud auth login` already done; `. /root/.secrets.env` sets GCP_BACKUP_BASE + HF_TOKEN.
   - If /root/.secrets.env is missing, STOP and ask me to run the notebook's env cell ONCE.

2. Inference setup — DETACHED (~2-4 min), then poll (never tight-loop):
       cd /content/maqamrock-yue2-lora-finetuning
       setsid nohup bash bootstrap/setup.sh --inference > /content/logs/setup.log 2>&1 < /dev/null & disown
   Require: no [FAIL] and /content/logs/timing.txt written. If it fails, report the [FAIL] line and stop.

3. Run the probe — DETACHED; one command stages the converted pair, dry-runs, generates the 5
   takes, and banks the run folder (~45-60 min):
       setsid nohup bash INFERENCE/run_v3_jarir_seed_probe.sh > /content/logs/v3_jarir_probe.log 2>&1 < /dev/null & disown

4. Monitor WITHOUT blocking: /content/logs/v3_jarir_probe.log and
   /content/audiocpp_inference/out/latest/ (5 × v3_jarir_<seed>.{wav,log,json} + batch_summary.txt).
   Confirm the run folder reached <base>/v3_arabmaqamrock_lora/listening/<run>/.

5. Report, from artifacts only: the 5 seed values, per-take wall-clock + WAV duration, any
   `truncated` flags, and the GCS path. If a take truncated at cap 6500, re-render ONLY that seed
   at cap 8000 and note it (don't touch the other four).

CONSTRAINTS: ONE shared GPU — nvidia-smi first, never overlap. Do NOT edit the adapter, the input
JSON, or any config. The probe song is a TRAINED piece (2× in the 438), so this measures
reproduction / seed-variance, NOT held-out generalisation. You have reign to run the state-changing
commands above yourself — log them and keep the chat unblocked.
```
