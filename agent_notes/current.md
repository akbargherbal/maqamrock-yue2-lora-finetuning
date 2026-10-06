# current

> **Session plan:** [`docs/QURAN_AHH_RESUME_PLAN.md`](../docs/QURAN_AHH_RESUME_PLAN.md) Phase 3b —
> T4 epoch test on Ayat al-Kursi (2:255) → blind A/B.
> **This file is a handoff copy surface, not a source of truth** — re-derive from live artifacts.

## State @ 2026-10-06 05:45 UTC — Phase 3b **rendered + blind package banked; verdict pending**

Repo `pron-lora-long-aya`, HEAD **`47f1575`** (all pushed to origin). Fresh Colab **T4**.

### Done this session
1. **Converted c9000 / c19500 / final** (canonical converter, `--stem quran_ahh_r8`, rank 32,
   byte-level verified) → banked to `…/quran_ahh_r8_rank32/convert/`; manifest updated.
2. **Rendered all 6 tracks** on held-out 2:255 (`quran_pt_probe.py --arms c9000,c19500,final`,
   seed 20261004, cap 7500): all `exit=0`, no truncation, 14:12 total.
   Run dir `…/audiocpp_inference/out/20261006-052626_quran_pt_probe/` (banked).
3. **Blind A/B/C package** built (seed 20261006) and banked to
   `$GCP_BACKUP_BASE/listening/QURAN_AHH_EPOCHS_INPUT/` (6 mp3 + `EVAL.txt` + `KEYS.txt`).
   Round record: `results/quran_ahh_epochs/` (`README.md`, `KEY.json`).
   **A=final, B=c9000, C=c19500.**
4. **Three recurring gotchas encoded in code** (all pushed):
   - `72297f0` — CUDA-12 loader path (`INFERENCE/cuda_loader_path.sh` + `run_one.sh` + `setup.sh`).
   - `47f1575` — ctime restore (`bootstrap/restore_run.py`) + WAL checkpoint (`backup_to_gcp.py`).
   - Corrected the wrong "touch does not bump ctime" gotcha claim.

### Next — the listener (you)
1. Get the package: `gcloud storage cp -r "$GCP_BACKUP_BASE/listening/QURAN_AHH_EPOCHS_INPUT" /content/ab/`
   (or `gcloud storage ls "$GCP_BACKUP_BASE/listening/QURAN_AHH_EPOCHS_INPUT/"`).
2. Listen to 002255_{uthmani,simple}_{A,B,C}.mp3; **do not open `KEYS.txt` first**.
3. Send back a table: track | preferred label | confidence | notes.
4. Agent decodes from `KEY.json`, records the verdict in
   `TRAINING_ANALYSIS/quran_ahh_r8_rank32/ANALYSIS.md`.

### Still open
- Phase 3b listener verdict (above).
- Phase 5: rename `quran_ahh_r8` → `quran_ahh_r32`; docs-reconciler; blind gate before any merge.
- Round-2 `c10500` vs `c16500` adapters remain banked and untested.

## Gotchas
- **CUDA-12 loader path, ctime-restore, and WAL-checkpoint are now automatic** (commits `72297f0`,
  `47f1575`) — no per-session `export`/`chmod`/salvage. Preflight the loader with
  `bash INFERENCE/cuda_loader_path.sh --check /content/audiocpp_inference/bin/audiocpp_cli`.
- Restore a run with `python bootstrap/restore_run.py --run-name <run> --apply` (rsyncs **and**
  fixes resume ctime order) — not a bare `rsync` + hand-`chmod`.
- The probe re-rsyncs the whole convert prefix (~980 MB) each run and exposes no `--out-dir`, so a
  failed render restarts in a fresh folder rather than resuming.
