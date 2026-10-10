# current.md — v3 launch: verified fresh, ready to start (2026-10-10)

**State verified from artifacts this turn.** Setup **done**. Sidecars **UP** (started 10:05).
Training **LAUNCHED 2026-10-10 10:06** — pid 27341, run `v3_arabmaqamrock_lora`.
Now in the mandatory latent-cache build (before step 1).

## Verified live (artifacts, not memory)
- `python status.py` / `train_ctl.py status`: `running — pid 27341, run
  'v3_arabmaqamrock_lora', started 2026-10-10T10:06:00`; sidecars
  `backup_to_gcp.py=24944 · gpu_logger.py=24945 · vm-continuity=healthy`; `ALERTS: none`.
- `/content/logs/train.log`: `Caching latents to disk:   0%|          | 0/438` — the ~7 min
  cache build. `nvidia-smi`: `40 %, 3852 MiB / 81920 MiB`. `loss_log.db` not yet written
  (0 steps until the cache + model load finish — normal).
- `nvidia-smi`: **A100-SXM4-80GB**, `0%` util, `0MiB / 81920MiB`, `No running processes`
  → GPU is free; no overlap.
- `git log -1 --oneline`: `2b32197 main: A100 launch prep — notebook -> v3, handoff + session prompt`.
- **Fresh start confirmed**: `/content/ai-toolkit/output/v3_arabmaqamrock_lora/` does **not
  exist** (`output/` holds only `.gitkeep`); GCS prefix `.../v3_arabmaqamrock_lora/` **does
  not exist**; no `_latent_cache/`.
- **Setup complete** — `/content/logs/setup.log`:
  - L25 `[ok]   dataset: 438 tracks in /content/yue2_dataset`
  - L27 `[ok]   Comfy-Org/YuE2 checkpoints/yue2_3b_int8_convrot.safetensors present in HF cache`
  - L28 `[ok]   torch/torchaudio cu130 + decode + cuDNN conv`
  - L29 `=== setup.sh done (training) — total 197s ===`
  - Dataset on disk: `438` mp3 + `438` txt (`.bootstrap_complete` present).
- Config authority `config/v3_arabmaqamrock_lora.yml`: `steps: 5000` (L71),
  `cache_latents_to_disk: true` (L57), `disable_sampling: true` (L93),
  `train_window_frames: 0` (L129), `save_every: 250` (L46).
- `train_ctl.py` default config is already `config/v3_arabmaqamrock_lora.yml` (L40) — the
  explicit `--config` below is the same thing.

## 1. Start the two sidecars — **DONE** (running, pids 24944 / 24945)
(kept below for reference / re-run after a VM reset) — terminal: **detached**
Survives Ctrl+C / closing the tab. Confirm nothing already running first.
Logs: `/content/logs/gcp_backup_stdout.log`, `/content/logs/gpu_logger_stdout.log`
(backup pass log: `/content/logs/gcp_backup.log`).
Stop: `pkill -f 'backup_to_gcp.py --run-name v3_arabmaqamrock_lora'` and
`pkill -f 'gpu_logger.py --out /content/logs/gpu_usage.csv'`. Resume: rerun the block.

```bash
cd /content/maqamrock-yue2-lora-finetuning
pgrep -af 'backup_to_gcp.py|gpu_logger.py'   # expect no real daemons yet
setsid nohup python backup_to_gcp.py --run-name v3_arabmaqamrock_lora > /content/logs/gcp_backup_stdout.log 2>&1 & disown
setsid nohup python gpu_logger.py --out /content/logs/gpu_usage.csv > /content/logs/gpu_logger_stdout.log 2>&1 & disown
pgrep -af 'backup_to_gcp.py|gpu_logger.py'   # now 2 pids
```

## 2. Launch training (you type this) — terminal: **detached via train_ctl.py**
Own session; a stray Ctrl+C cannot kill it.
Logs: `/content/logs/train.log` (+ `/content/logs/train_stdout.log`); pid `train.pid`.
Stop: `python train_ctl.py stop` (SIGINT, checkpoint-safe — **never** bare kill/kill -9).
Resume: rerun this same start command (auto-resumes newest checkpoint).

```bash
cd /content/maqamrock-yue2-lora-finetuning
python train_ctl.py start --config config/v3_arabmaqamrock_lora.yml
```

**Expect before step 1 (normal, not a stall):** mandatory GPU latent-cache build for the 438
(~7 min on A100) + model load (~1–3 min). `loss_log.db` stays at 0 steps for several minutes.

## 3. Monitor (read-only)
```bash
cd /content/maqamrock-yue2-lora-finetuning
python train_ctl.py status
python monitor_loss.py /content/ai-toolkit/output/v3_arabmaqamrock_lora/loss_log.db --total-steps 5000
tail -f /content/logs/train.log
tail -n 10 /content/logs/gpu_usage.csv
```
(~5000 steps ≈ 4.75 h on A100 at ~3.42 s/step. `disable_sampling: true` → no inference on
the A100.)

## Open items (unchanged)
- Held-out/eval prompts are **STALE vs the 438** (3/4 contaminated) — regenerate before **any**
  evaluation.
- `sample.samples` in the config are stale and **inert** (`disable_sampling: true`).
- Graph stale (built `2f35c76`, HEAD `2b32197`) — orientation only, not a blocker.
- Working tree has a modified `opencode.json` (harness config; not training-related).
- `setup.sh`'s trailing "Next" hint cites the legacy `config/A100_akbar_arabic_rock_lora.yml`
  (setup.log L35) — that is `setup.sh` message drift; launch via `train_ctl.py` with the v3
  config above.
