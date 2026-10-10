# Next-session prompt — implement the v3 "spice" sweep on Colab

_Created 2026-10-10. Paste the block below to start the Colab session. This file is a copy surface,
not authority — the authority is `docs/V3_SPICE_SWEEP.md` + the config._

```text
Fresh Colab runtime. Take care of this end to end; I am away — do not wait for me to run steps.
Stage A needs only CPU; Stage B needs a T4.

Repo: akbargherbal/maqamrock-yue2-lora-finetuning, branch main (expect d2f0744 or newer).
Task: implement docs/V3_SPICE_SWEEP.md — a "spice" sweep to lift the v3 Jarir output from 4/5 to 5/5.
GCS base: gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning

Read first, in order: AGENTS.md -> agent_notes/current.md -> docs/V3_SPICE_SWEEP.md
(companions: docs/INFERENCE.md, docs/V3_JARIR_SEED_PROBE.md).

Respect this context: v3 trained with cot:"off", so the LoRA learned STYLE/TIMBRE, not melody — a
checkpoint re-tints sound; "improvisation/spice" is the AR (composer) sampler + prompt + selection.
The seed probe (audiocpp_inference/out/20261010-142358_v3_jarir_seeds) is 5 clean takes, none
truncated. Do NOT edit the adapters, the input JSON seeds, or any config to "make it pass".

STAGE A — CPU runtime (no GPU). Do this first, then report.
1. Convert checkpoints 2500/3500/4500 with the torch-free converter
   (audiocpp_inference/converter/convert_aitoolkit_yue2_lora.py) and bank the pairs to
   <base>/v3_arabmaqamrock_lora/convert/ck<N>/ — exact commands in docs/V3_SPICE_SWEEP.md §7.
2. Create INFERENCE/songs.v3_spice.json (derive from INFERENCE/songs.v3_jarir_seed.json; one take,
   pinned seed 2640605763, cap 6500; style + lyrics verbatim) and INFERENCE/v3_spice_probe.sh
   (driver spec in §7 — it was syntax-checked; keep the arm table exactly).
3. Validate with NO GPU: `DRY=1 bash INFERENCE/v3_spice_probe.sh` -> must plan all 10 arms
   (ref, g1.5, g2.5, t1.2, t1.4, rp1.4, ar0.7, ck4500, ck3500, ck2500).
4. Commit + push the two new files (docs/V3_SPICE_SWEEP.md already exists).

STAGE B — T4 only, and only when one is free (run `nvidia-smi` first; ONE shared GPU, never overlap):
5. bash bootstrap/setup.sh --inference > /content/logs/setup.log 2>&1   # wait for all [ok]
   gcloud storage rsync -r "$GCP_BACKUP_BASE/v3_arabmaqamrock_lora/convert" /content/converter/out
6. setsid nohup bash INFERENCE/v3_spice_probe.sh \
     > /content/logs/v3_spice_probe.log 2>&1 < /dev/null & disown
   tail -f /content/logs/v3_spice_probe.log
7. It banks itself to <base>/v3_arabmaqamrock_lora/spice_probe/. Expect ~95 min (10 arms x ~9.5 min).

Report from artifacts only: per-arm wall + WAV duration + truncated flag, the run path, and whether
`ref` reproduced probe take 0 (seed 2640605763). Do NOT judge audio quality — I listen.
```
