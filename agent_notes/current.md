# current

## State @ 2026-10-05 ~15:40 UTC — `quran_ahh_r8` REVISED training LIVE; T4 starter probe READY

Branch `pron-lora-long-aya`. Config `config/quran_ahh_r8.yml` = **AR+NAR, rank 32/32,
`ar_kl_weight 0.0`, steps 28467 (3 epochs)** — authority; do not edit.

- **Training running**: `run.py` pid **16301** (detached, started 12:35:11). Log
  `/content/logs/train_quran_ahh.log`.
- **Progress**: ~**7,767 / 28,467 (27%)**; loss/loss ~4.2 (bs=1). Median **1.247 s/step**
  (~0.73 steps/s); VRAM peak **9,150 MiB** of 23,034; **1500-step save ≈ 34 min**.
- **Checkpoints (rank 32)**: `_000001500 / _3000 / _4500 / _6000 / _7500` (**5**, 112 MiB each)
  + `optimizer.pt` — local + GCS. Next save = **9000**.
- Sidecars: `backup_to_gcp.py` (pid 13044) + `gpu_logger.py` (pid 13214).
  `vm-continuity status`: `state=OK` (pid 6120).

Live snapshot analysis of this run: `TRAINING_ANALYSIS/quran_ahh_r8_rank32/ANALYSIS.md`
(the old rank-8 analysis stays at `TRAINING_ANALYSIS/quran_ahh_r8/`).

## T4 INFERENCE STARTER — checkpoints 4500 + 7500 (ready 2026-10-05)

Converted the revised rank-32 checkpoints to audio.cpp adapters on the L4 (**CPU**, both
experts real — NOT lone-AR; byte-verified) and banked them:

`$GCP_BACKUP_BASE/quran_ahh_r8_rank32/convert/{c4500,c7500}/quran_ahh_r8_{ar,nar}.safetensors`
(+ `adapter_manifest.json`, sha256 per arm). Driver now takes `--prefix`/`--arms`.

terminal: detached — survives Ctrl+C / closing the tab.
log: `/content/logs/quran_pt_probe_r32.log`
stop: `pkill -f 'quran_pt_probe.py --prefix quran_ahh_r8_rank32'` (also kills the
`generate.py` child). ~26 min for 4 tracks; a restart re-renders (no resume dir).
resume: re-run the same `setsid nohup …` line.

```bash
# --- on a FRESH T4 Colab ---
git clone https://github.com/akbargherbal/maqamrock-yue2-lora-finetuning.git /content/maqamrock-yue2-lora-finetuning
cd /content/maqamrock-yue2-lora-finetuning && git checkout pron-lora-long-aya
bash bootstrap/setup.sh --inference > /content/logs/setup.log 2>&1   # wait for the verify block

# validate the batch (no GPU), then run it detached:
python INFERENCE/quran_pt_probe.py --prefix quran_ahh_r8_rank32/convert --arms c4500,c7500 --dry-run
setsid nohup python INFERENCE/quran_pt_probe.py \
  --prefix quran_ahh_r8_rank32/convert --arms c4500,c7500 \
  > /content/logs/quran_pt_probe_r32.log 2>&1 & disown
```

- Arms = `c4500`, `c7500` × `{uthmani, simple}` = **4 tracks**, held-out **2:255**, seed
  20261004, cap 7500. Output: `/content/audiocpp_inference/out/<ts>_quran_pt_probe/`
  (mirrored to GCS `audiocpp_inference/out/` by the backup sidecar).
- A **base (no-LoRA)** reference already exists from the morning rank-8 probe
  (`audiocpp_inference/out/20261005-072738_quran_pt_probe/base_{simple,uthmani}.wav`) — compare
  against those rather than re-rendering base.
- Needs `GCP_BACKUP_BASE` (arm staging + backup) and `HF_TOKEN` (GGUF) in env
  (`/root/.secrets.env`). T4 = native **sm_75** binary; if it faults on CUDA-13 libs see
  `docs/COMMAND_HANDOVER_GOTCHAS.md` (2026-10-04).

## GCS layout (2026-10-05)

- **Live revised run** `…/quran_ahh_r8/` = `output/` (rank-32 ckpts + optimizer + loss_log.db),
  `logs/`, `agent_notes/`, `run_manifest.json`.
- **Revised adapters** `…/quran_ahh_r8_rank32/convert/{c4500,c7500}/` (rank 32, AR+NAR).
- **Archive** `…/archive/quran_ahh_r8_rank8_aronly/` = the OLD rank-8 run's `output/` and
  `convert/` arms. Do not use any rank-8 adapter with the revised config.

## Controls (training)

terminal: detached (survives Ctrl+C / closing the tab).
log: `/content/logs/train_quran_ahh.log` (+ `_stdout.log`).
stop: `python train_ctl.py stop --config config/quran_ahh_r8.yml --run-name quran_ahh_r8 --log-name train_quran_ahh`
resume: re-run the same start line (local output prefix → auto-resumes newest checkpoint).

```bash
cd /content/maqamrock-yue2-lora-finetuning
python train_ctl.py start --config config/quran_ahh_r8.yml --run-name quran_ahh_r8 --log-name train_quran_ahh
```

Monitor: `python monitor_loss.py /content/ai-toolkit/output/quran_ahh_r8/loss_log.db --watch 30 --total-steps 28467`

## Close the session (you type these)

`train_ctl.py stop …` → `backup_to_gcp.py --run-name quran_ahh_r8 --once` → confirm newest
`*.safetensors` **and** `optimizer.pt` in GCS → `vm-continuity status` (`state=OK`) → update
this file + commit/push. No auto-resume; a pause is a user-typed `stop`.

## Open items
- Human blind gate (`ab-blind-eval`) before any merge; judge the T4 renders with tashkeel visible.
- Only 4 metric keys logged; `additional_model_loss` is byte-identical to `loss/ar_ce`, so the
  NAR term is visible only as the `loss/loss − ar_ce` residual (~0.68) — see the new ANALYSIS.md.
- `docs/QURAN_AHH_RUN.md` still points at the old rank-8 `TRAINING_ANALYSIS/quran_ahh_r8/`.
- `status.py` reports its default run name `akbar_arabic_rock_lora`; actual run is `quran_ahh_r8`.
