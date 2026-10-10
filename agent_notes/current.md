# current.md — v3 run done; T4 seed-probe prepped; GPU step pending (2026-10-10)

## Done
- **v3 training complete** — `v3_arabmaqamrock_lora` 5000/5000, all artifacts banked
  (`TRAINING_ANALYSIS/ANALYSIS.md`; VRAM peaked 79.2/80 GB — see there).
- **T4 seed-probe prep (CPU only, no GPU used):**
  - Converted the v3 final adapter (converter is torch-free) and banked it:
    `<base>/v3_arabmaqamrock_lora/convert/v3_arabmaqamrock_lora_{ar,nar}.safetensors`
    (AR sha256 `3531bb9106d2292eefe58eabe11ec08bb7dddc69554f2b016dc9f13f711fab18`,
    NAR `a7eabcadb22146048bcb5e65d04828ee9454559523ca161bd38c06060deb0cae`) + `MANIFEST.json`.
  - Input JSON: `INFERENCE/songs.v3_jarir_seed.json` (1 song · `repeat: 5` · `quantile: 0.95`).
  - Runner: `INFERENCE/run_v3_jarir_seed_probe.sh` (detached; GPU-guarded; banks to GCS).
  - Plan: `docs/V3_JARIR_SEED_PROBE.md`. `docs/LORA_INVENTORY.md` updated (v3 style row).

## ⚠️ Blocker: no GPU in this agent's environment
`nvidia-smi` is absent (Hyper-V vGPU only), there is no `/content`, and no GPU VM / tunnel is
reachable. So the **5-take generation cannot be run from here** — it must run on the GPU box.

## Run it on the T4 (one detached command, after `setup.sh --inference` is clean)
```bash
cd /content/maqamrock-yue2-lora-finetuning
setsid nohup bash INFERENCE/run_v3_jarir_seed_probe.sh \
  > /content/logs/v3_jarir_probe.log 2>&1 < /dev/null & disown
tail -f /content/logs/v3_jarir_probe.log          # watch
# result: /content/audiocpp_inference/out/latest/ (5 × v3_jarir_<seed>.{wav,json,...} + batch_summary.txt)
# banked: <base>/v3_arabmaqamrock_lora/listening/<run>/
```
~45–60 min (5 takes, sequential, T4). The probe is a **trained** song (2× in the 438) — it
measures reproduction / seed-variance, not held-out generalisation.

## Open
- Held-out/eval prompts still **stale vs the 438** (regenerate before a real held-out eval).
- `docs-reconciler` pass + `docs/README.md` index update pending; knowledge graph stale.
