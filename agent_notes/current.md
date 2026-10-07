# current.md — handoff surface (overwritten each turn; not a source of truth)

## ✅ DONE — `jarir_lever_probe` scale tier complete (17/17)
_2026-10-07 06:20:12Z, Colab Tesla T4, GPU idle. Driver exited `rc_total=0`; `_failed.log` empty._

Driver: `=== jarir_lever_probe done (rc_total=0) 2026-10-07T06:20:12Z ===`.
**17/17 WAVs on disk and in GCS** (8 prompt + 9 scale). The 5 arms rendered this session
(seed `20261011`, cap 8000, `cot=off`) — all **exit 0**, all **`trunc=no`**:

| arm | wall | dur |
|---|---|---|
| qa_0.0_1.0 | 10:49 | 269.9 s |
| qa_0.5_1.0_rp1.4 | 10:09 | 197.9 s |
| qa_0.5_1.0_t0.8 | 10:49 | 209.3 s |
| qa_0.5_1.0_g1.0 | 10:21 | 266.8 s |
| qa_0.5_1.0_notrigger | 10:25 | 196.1 s |

The other 4 scale arms (`v2_1.0_1.0`, `qa_1.0_1.0`, `qa_0.5_1.0`, `qa_1.0_0.5`) + the 8
prompt tracks were restored from GCS and skipped in place (unchanged).

### Where the audio is
- Scale arms: `/content/audiocpp_inference/out/jarir_lever_probe/<arm>/jlv_scale_ref_20261011.wav`
  (+ `.log`, `_time.txt`, `_gpu.csv`, `.json`; per-arm `_knob.json` records ar/nar scale + opts).
- Prompt tier (Tier 1/3): `/content/audiocpp_inference/out/jarir_lever_probe/prompt/` (8 WAVs).

### Backup / continuity (verified this turn)
- GCS mirror current: last pass **06:32:26Z, 5/5 folders synced** (after the last arm at 06:20).
- `gsutil ls .../jarir_lever_probe/**/*.wav` = **17**; every scale arm has its WAV; `_failed.log` empty.
- Sidecars still running — `backup_to_gcp.py --inference` (33786), `gpu_logger.py` (33788),
  `vm-continuity` healthy. Stop them at session end if desired.

### Next (NOT started — your call)
- Blind A/B listening eval of the 9 scale arms (`ab-blind-eval` skill / `INFERENCE/prepare_ab_eval.py`).
- Optional per-arm metrics (pronunciation accuracy, energy, truncation) if a numeric cut is wanted.

### Environment fixes this session (important)
- **OpenCode was downgraded by bootstrap**, then restored: `bootstrap/setup.sh`'s `job_opencode`
  ran `curl opencode.ai/install | bash`, replacing the VM's **2.0.24** with **1.18.35**, which cannot
  read the V2-schema DB (no `session` table) → CLI/web showed "configure provider, all grayed".
  Fixed by recovering 2.0.24 from the running server: `cp /proc/<pid>/exe` → `/root/.opencode/bin/opencode`.
  Old binary kept at `/root/.opencode/bin/opencode-1.18.35.bak`. **Do NOT re-run `bootstrap/setup.sh`**
  on this VM (it will downgrade again). Web UI = `opencode pair` (2.0.24 has no `opencode web`).
- `INFERENCE/rating_app/app.py`: `--port` is now a **preference** — if 5000 is busy it auto-picks the
  next free port (so it coexists with other local Flask apps on 5000); `--strict-port` restores the
  exact-bind behavior, `--port 0` = any free port.

### Facts / endpoints
- branch `pron-lora-long-aya` @ `3cf4f14` (clean).
- GCS prefix: `$GCP_BACKUP_BASE/audiocpp_inference/out/jarir_lever_probe/`.
- Secrets: `/root/.secrets.env` (`GCP_BACKUP_BASE=gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning`).
