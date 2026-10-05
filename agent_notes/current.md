# current

## State @ 2026-10-05 (CPU VM) — AHH dataset RESTORED + VERIFIED; GPU session staged

Branch `pron-lora-long-aya` (do NOT merge to `main`; `main` = `d345a9b`). No GPU,
no `nvcc` on this box. Training is **not launched** and stays gated by the Phase 1
base-model ceiling probe (`docs/QURAN_PRON_REVIEW.md` §5, item 4 below).

**Plan / config audit / GPU checklist: `docs/QURAN_AHH_RUN.md`** (canonical hub;
indexed in `docs/README.md` + `SOURCE_OF_TRUTH.md`).

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
