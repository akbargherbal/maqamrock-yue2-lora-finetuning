# current

## State @ 2026-10-05 — `quran_ahh_r8` training RUNNING (L4); Phase 1 gate WAIVED to T4

Branch `pron-lora-long-aya` (do NOT merge to `main`; `main` = `ab8640d`). GPU = NVIDIA
L4 (23 GB). Training **RUNNING** (pid 34210): 1 epoch = 9,489 steps, checkpoints at
1500/3000/…/9000 + a final no-step save, auto-backed-up to GCS. Latent cache built +
banked. Phase 1 ceiling probe **WAIVED** for this session and moved to a separate T4
(see `### T4 session` below).

**Phase 1 base-model ceiling probe: WAIVED for this session (user, 2026-10-05).**
Training proceeds ungated. The probe (inference stack + `quran_only` rebuild on the native
sm_75 binary) moves to a separate T4 session — `docs/QURAN_AHH_RUN.md` §2,
`docs/QURAN_FORMAT_PROBE.md:63`.

**Plan / config audit / GPU checklist: `docs/QURAN_AHH_RUN.md`** (canonical hub;
indexed in `docs/README.md` + `SOURCE_OF_TRUTH.md`).

### Crash @ launch (2026-10-05) — fixed; not yet relaunched

First `train_ctl.py start` (pid 25921) died at **step 0** during the latent-cache build,
in the VAE `conv1d`: `CUDNN_STATUS_SUBLIBRARY_VERSION_MISMATCH`. No checkpoint, no
`loss_log.db`; `output/quran_ahh_r8/` holds only `config.yaml` + `tensorboard/`.
Cause: orphan cuDNN libs from the image (`libcudnn_engines_tensor_ir.so.9`,
`libcudnn_ext.so.9`) not in the pinned `nvidia-cudnn-cu13==9.20.0.48` wheel → moved to
`/content/cudnn_orphans_bak/`; `conv1d` now passes. Fix + recipe:
`docs/COMMAND_HANDOVER_GOTCHAS.md` (2026-10-05). Durable fix committed + pushed:
`f68f7a6` on `pron-lora-long-aya`, cherry-picked to `main` as `ab8640d` — `setup.sh` now
prunes non-manifest libs *and* verifies a cuDNN conv on a fresh VM. Relaunch was the same
`train_ctl.py start` line (config/run-name unchanged; no progress lost).

### T4 session (separate GPU) — pron eval handoff  ← READ THIS ON THE T4

Goal: the **Phase 1 base-model ceiling probe** + per-checkpoint pron eval on held-out
**2:255**, free-run, same seed. This is the gate deferred from the L4 training session.

Ready in GCS (converted on the L4 while training ran; byte-level verified):
`$GCP_BACKUP_BASE/quran_ahh_r8/convert/{base,quran_only,c1500,c3000,c4500,c6000,c7500}/`
— each dir has `quran_ahh_r8_ar.safetensors` (lone AR, α=1) + `quran_ahh_r8_nar.safetensors`
(zeros, rank 8), plus `convert/adapter_manifest.json`. New checkpoints (`c9000`, `final`)
land automatically as the run saves them; re-run the driver to pick them up.

1. Clone branch `pron-lora-long-aya`, then `bash bootstrap/setup.sh --inference`
   (T4 = the **native sm_75** binary; no arch swap).
2. Run the probe driver — it stages the arms from GCS, builds the songs JSON (exact
   training caption, `[Verse]` + ` ۝`), and calls `generate.py`:
   ```bash
   python INFERENCE/quran_pt_probe.py --dry-run    # validate + projected time
   python INFERENCE/quran_pt_probe.py              # real run (detach it; ~90+ min)
   ```
   Arms = base / `quran_only` / each checkpoint × uthmani+simple, seed 20261004.
   `base` is an all-zero adapter so it runs in the same batch; fallback if distrusted:
   `LORA_AR_SCALE=0 LORA_NAR_SCALE=0` against any arm (audio.cpp scale 0 = adapter off).
3. **CUDA-13-image gotcha:** the sm_75 binary may need the CUDA-12 libs on
   `LD_LIBRARY_PATH` (`docs/COMMAND_HANDOVER_GOTCHAS.md`, 2026-10-04).
4. **Verdict** (`docs/QURAN_PRON_REVIEW.md` §5): base **also wrong** on the hard letters
   ⇒ representational ceiling ⇒ **stop the LoRA line**; base OK but adapter wrong ⇒
   training/config issue. Listen with tashkeel visible; blind-gate (`ab-blind-eval`)
   before any merge.

The L4 run continues untouched — **do not run training or this run's config on the T4.**

Restored this session (CPU-only, verified):
- `gcloud storage cp …/quran_ahh_dataset.zip /content/` → `unzip -q … -d /content/`
- sha256 `8c68d6844d7c9ee87ca69956dfcb70419e234a3197043b41526833e81a3e9ff9` **OK**
  (3,966,504,331 B, matches the banked `.sha256`).
- Counts: **train 9,489 · val 6** (2:255 ×3 reciters ×2 scripts), **held-out 2:255
  absent from train** (0 matches); per-reciter train pairs AB 2398 · Hudhaify 4142 ·
  Husary 2949 (stratified simple/uthmani). `selection_report.json` + manifests present.
- Config `config/quran_ahh_r8.yml` parses; diffs vs `quran_long_aya_r8_s10.yml` are
  exactly the 4 documented (`name`, `log_dir`, `datasets[0].folder_path`, `steps: 9489`).

### AHH run facts (survive)

- Identity: run `quran_ahh_r8`; config `config/quran_ahh_r8.yml`; log basename
  `train_quran_ahh`; output `/content/ai-toolkit/output/quran_ahh_r8/`.
- Data: AHH filtered set, 9,492 clips / 3 reciters, paired with Tanzil (NFC, no
  embedded `۝`; builder appends it). Single caption/clip, 50/50 simple/uthmani
  stratified per reciter. Style line: `Solo male voice, unaccompanied. Quran
  recitation in murattal style. Classical Arabic with tajwīd, precise articulation.
  Spoken Words.` Banked: `$GCP_BACKUP_BASE/quran_ahh_dataset.zip` (sha `8c68d684…e9ff9`).
- Hyperparameters deliberately UNCHANGED from s10 (rank 8/8, lr 1e-4, adamw8bit,
  EMA 0.999, cot off, `ar_kl_weight` 0.2, bf16). Change only data + eval per review §6.3.
- Eval is an OFFLINE per-checkpoint free-run on held-out 2:255; `disable_sampling: true`.

### Staged GPU session (paste in order; exact flags source-verified)

```bash
# 0. code — this long-aya work lives on the branch, not main
git clone https://github.com/akbargherbal/maqamrock-yue2-lora-finetuning.git /content/maqamrock-yue2-lora-finetuning
cd /content/maqamrock-yue2-lora-finetuning && git checkout pron-lora-long-aya
```

```bash
# 1. bootstrap: ai-toolkit + pinned torch + HF assets. The notebook exports
#    GCP_AHH_DATASET_ZIP, so setup.sh's opt-in job_ahh_dataset restores the AHH zip
#    during setup. Ensure the long-aya/pron sets are NOT requested.
unset GCP_QURAN_LONG_DATASET_PATH GCP_PRON_DATASET_PATH
mkdir -p /content/logs
```
terminal: detached — survives Ctrl+C / closing the tab;
log: `/content/logs/setup.log`; stop: `pkill -f 'bootstrap/setup.sh'` (re-runnable);
resume: re-run the same `setsid nohup …` line.
```bash
setsid nohup bash bootstrap/setup.sh --training > /content/logs/setup.log 2>&1 & disown
tail -n 25 /content/logs/setup.log          # wait for the all-[ok] verify block (torch/CUDA + decode)
```

```bash
# 2. confirm AHH restored (setup.sh prints "[ok] AHH dataset: 9489 train pairs").
#    Manual fallback only if the job was skipped/failed:
gcloud storage cp "$GCP_AHH_DATASET_ZIP" /content/ && unzip -q /content/quran_ahh_dataset.zip -d /content/
find /content/quran_ahh_dataset/train -maxdepth 1 -name '*.txt' | wc -l   # expect 9489
```

```bash
# 3. sidecars — both detached; start AFTER /content/logs exists
cd /content/maqamrock-yue2-lora-finetuning
```
terminal: detached ×2 — survive Ctrl+C / closing the tab;
logs: `/content/logs/gcp_backup_stdout.log`, `/content/logs/gpu_logger_stdout.log`;
stop: `pkill -f backup_to_gcp.py` / `pkill -f gpu_logger.py`;
resume: re-run the same lines.
```bash
setsid nohup python backup_to_gcp.py --run-name quran_ahh_r8 > /content/logs/gcp_backup_stdout.log 2>&1 & disown
setsid nohup python gpu_logger.py --out /content/logs/gpu_usage.csv > /content/logs/gpu_logger_stdout.log 2>&1 & disown
pgrep -af 'backup_to_gcp.py|gpu_logger.py'
```

```bash
# 4. GATED: do NOT launch training until the Phase 1 base-model ceiling probe verdict
#    (docs/QURAN_PRON_REVIEW.md §5). Probe first: base (no LoRA) vs quran_only on
#    held-out 2:255, same seed, free-run.
```

terminal: detached (via train_ctl — a stray Ctrl+C cannot kill it); YOU type the start;
logs: `/content/logs/train_quran_ahh.log`; stop: the `train_ctl.py stop` line below (do NOT `kill`);
resume: the identical `train_ctl.py start` line (auto-resumes from the newest checkpoint).
```bash
python train_ctl.py start --config config/quran_ahh_r8.yml --run-name quran_ahh_r8 --log-name train_quran_ahh
```
First launch builds the latent cache (~2.4 h for 9,489 files on an L4) before step 1 —
`loss_log.db` at 0 steps for a while is normal. Bank the cache when complete:
`tar -C /content/quran_ahh_dataset/train -cf - _latent_cache | gcloud storage cp - "$GCP_BACKUP_BASE/quran_ahh_dataset/_latent_cache.tar"`.
Stop/status MUST pass the same `--config` + `--run-name` (see `docs/COMMAND_HANDOVER_GOTCHAS.md`):
```bash
python train_ctl.py stop   --config config/quran_ahh_r8.yml --run-name quran_ahh_r8 --log-name train_quran_ahh
python train_ctl.py status --config config/quran_ahh_r8.yml --run-name quran_ahh_r8 --log-name train_quran_ahh
python monitor_loss.py /content/ai-toolkit/output/quran_ahh_r8/loss_log.db
```

### Next / open

1. **Phase 1 base-model ceiling probe** (GPU minutes) gates any training (§5). No verdict yet.
2. **Offline eval**: adapt `INFERENCE/pron_ckpt_sweep.py` to free-run held-out 2:255 per
   checkpoint (run has `disable_sampling: true`).
3. After the verdict only: launch `quran_ahh_r8` (step 4 above); measure ~50 steps; do not edit config mid-run.
4. Residual: 91 `aya-1` clips (sura≠1,9) may carry a recited basmala not in the caption.
5. Docs: run hub `docs/QURAN_AHH_RUN.md` added + indexed; `prepare_ahh_quran_dataset.py`
   still not in `docs/README.md`; 3 docs still say `experimental-quran-pron`;
   `docs-reconciler` pass outstanding.
