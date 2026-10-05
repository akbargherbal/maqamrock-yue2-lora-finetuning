# current

## State @ 2026-10-05 ~16:15 UTC — `quran_ahh_r8` REVISED training LIVE; T4 probe round 1 done

Branch `pron-lora-long-aya`. Config `config/quran_ahh_r8.yml` = **AR+NAR, rank 32/32,
`ar_kl_weight 0.0`, steps 28467 (3 epochs)** — authority; do not edit.

- **Training running**: `run.py` pid **16301** (detached, started 12:35:11). Log
  `/content/logs/train_quran_ahh.log`.
- **Progress**: ~**10,120 / 28,467 (35.5%)**; loss/loss ~4.06 (bs=1). Median **1.247 s/step**
  (~0.73 steps/s); VRAM peak **9,150 MiB** of 23,034; **1500-step save ≈ 34 min**.
- **Checkpoints (rank 32)**: `_000001500 / _3000 / _4500 / _6000 / _7500 / _9000` (**6**, 112 MiB
  each) + `optimizer.pt` (step 9000) — local + GCS. Next save = **10500**.
- Sidecars: `backup_to_gcp.py` (pid 13044) + `gpu_logger.py` (pid 13214).
  `vm-continuity status`: `state=OK` (pid 6120).

Live snapshot: `TRAINING_ANALYSIS/quran_ahh_r8_rank32/ANALYSIS.md` (old rank-8 analysis stays
at `TRAINING_ANALYSIS/quran_ahh_r8/`).

## T4 probe round 1 — LISTENING VERDICT (2026-10-05, user)

Rendered **c4500 + c7500** (real AR+NAR; converted on the L4, banked
`…/quran_ahh_r8_rank32/convert/{c4500,c7500}/`), held-out 2:255 both scripts. 4 WAVs at
`…/audiocpp_inference/out/20261005-154621_quran_pt_probe/` (GCS, 16:05Z). T4 **now disconnected**.

- All tracks "sound like Alhusary — more or less".
- **Best: `c7500_simple`** (one mistake); **simple > uthmani** for both.
- **Hard letters (ح، ع) much less of a problem than in rank-8** — still not fully correct.
- Genuine improvement vs rank-8 AR-only; still improving at 7.5k → **not a plateau**.
- **Next try ~step 18000.**

## T4 probe — how to run (repeat around 18000)

Convert the then-current checkpoint on the L4 (**CPU**; does not touch the training GPU), bank
it, then run the probe on a fresh T4. `--arms` selects the subset.

```bash
# on the L4 (or any CPU box), per checkpoint step S:
mkdir -p /content/converter/out
gcloud storage cp "$GCP_BACKUP_BASE/audiocpp_inference/converter/convert_aitoolkit_yue2_lora.py" /content/converter/out/
python /content/converter/out/convert_aitoolkit_yue2_lora.py \
  /content/ai-toolkit/output/quran_ahh_r8/quran_ahh_r8_00000<S>.safetensors \
  --out-dir /content/conversion/quran_ahh_r8_rank32/c<S> --stem quran_ahh_r8
gcloud storage rsync -r /content/conversion/quran_ahh_r8_rank32 "$GCP_BACKUP_BASE/quran_ahh_r8_rank32/convert"
```

terminal: detached — survives Ctrl+C / closing the tab.
log: `/content/logs/quran_pt_probe_r32.log`
stop: `pkill -f 'quran_pt_probe.py --prefix quran_ahh_r8_rank32'` (also kills the
`generate.py` child).
resume: re-run the `setsid nohup …` line (~26 min for 4 tracks; restart re-renders).

```bash
# on a fresh T4:
git clone https://github.com/akbargherbal/maqamrock-yue2-lora-finetuning.git /content/maqamrock-yue2-lora-finetuning
cd /content/maqamrock-yue2-lora-finetuning && git checkout pron-lora-long-aya
bash bootstrap/setup.sh --inference > /content/logs/setup.log 2>&1   # wait for verify block
python INFERENCE/quran_pt_probe.py --prefix quran_ahh_r8_rank32/convert --arms c18000 --dry-run
setsid nohup python INFERENCE/quran_pt_probe.py \
  --prefix quran_ahh_r8_rank32/convert --arms c18000 \
  > /content/logs/quran_pt_probe_r32.log 2>&1 & disown
```

- Base (no-LoRA) reference already exists: `…/out/20261005-072738_quran_pt_probe/base_*.wav`.
- Needs `GCP_BACKUP_BASE` + `HF_TOKEN` (`/root/.secrets.env`). T4 = native sm_75 binary; CUDA-13
  lib gotcha → `docs/COMMAND_HANDOVER_GOTCHAS.md` (2026-10-04).

## GCS layout (2026-10-05)

- **Live revised run** `…/quran_ahh_r8/` = `output/` (rank-32 ckpts + optimizer + loss_log.db),
  `logs/`, `agent_notes/`, `run_manifest.json`.
- **Revised adapters** `…/quran_ahh_r8_rank32/convert/{c4500,c7500}/` (rank 32, AR+NAR).
- **Archive** `…/archive/quran_ahh_r8_rank8_aronly/` = OLD rank-8 run's `output/` + `convert/`.
  Do not use any rank-8 adapter with the revised config.

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
- Human blind gate (`ab-blind-eval`) before any merge.
- Only 4 metric keys; `additional_model_loss` is byte-identical to `loss/ar_ce`, so the NAR term
  shows only as the `loss/loss − ar_ce` residual (~0.66) — see the ANALYSIS.md flag.
- `docs/QURAN_AHH_RUN.md` still points at the old rank-8 `TRAINING_ANALYSIS/quran_ahh_r8/`.
- `status.py` reports its default run name `akbar_arabic_rock_lora`; actual run is `quran_ahh_r8`.
