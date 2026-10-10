# Next-session prompt — T4 seed probe

_Created 2026-10-10. Task: run the 5-seed probe of the v3 final adapter on one Jarir song, on a T4._
_Copy from here (vscode.dev text selection is glitchy; this file is a copy surface, not authority)._

```text
Fresh Colab T4 VM. Repo akbargherbal/maqamrock-yue2-lora-finetuning, branch main.
Task: run the v3 FINAL adapter on ONE Jarir song with 5 fresh random seeds, and bank the output.
Full plan: docs/V3_JARIR_SEED_PROBE.md. Live state: agent_notes/current.md.

Read first, in order: AGENTS.md -> agent_notes/current.md -> docs/V3_JARIR_SEED_PROBE.md.
Then VERIFY live, never recall: `nvidia-smi` (must show a T4, nothing else on it), `git log -1`,
and the GCS `v3_arabmaqamrock_lora/convert/` prefix. Ground truth = artifacts.

Steps:
1. Notebook env cell, then `bash bootstrap/setup.sh --inference` (detached; wait for all [ok]).
2. Run the probe DETACHED (one command does staging + dry-run + 5 takes + banking):
     cd /content/maqamrock-yue2-lora-finetuning
     setsid nohup bash INFERENCE/run_v3_jarir_seed_probe.sh \
       > /content/logs/v3_jarir_probe.log 2>&1 < /dev/null & disown
3. Watch: `tail -f /content/logs/v3_jarir_probe.log`. Output lands in
   /content/audiocpp_inference/out/latest/ (5 × v3_jarir_<seed>.{wav,log,json} + batch_summary.txt)
   and is banked to <base>/v3_arabmaqamrock_lora/listening/<run>/.
Expected ~45-60 min (5 takes, sequential, on a T4).

Constraints: ONE shared GPU — `nvidia-smi` first, never overlap; do NOT edit configs/adapters;
the probe song is a TRAINED piece (2× in the 438), so it measures reproduction / seed-variance,
NOT held-out generalisation. Report from artifacts only; hand me any state-changing command.
```
