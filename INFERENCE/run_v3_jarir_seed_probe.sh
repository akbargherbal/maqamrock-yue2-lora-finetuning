#!/usr/bin/env bash
# Turnkey run: 5 random seeds × v3 final adapter × one Jarir poem.
# Plan + rationale: docs/V3_JARIR_SEED_PROBE.md
#
# Designed to be launched DETACHED on the GPU VM so it never blocks a terminal:
#   cd /content/maqamrock-yue2-lora-finetuning
#   setsid nohup bash INFERENCE/run_v3_jarir_seed_probe.sh \
#     > /content/logs/v3_jarir_probe.log 2>&1 < /dev/null & disown
#   tail -f /content/logs/v3_jarir_probe.log      # watch
#   cat /content/audiocpp_inference/out/latest/batch_summary.txt
#
# Prereq: `bash bootstrap/setup.sh --inference` finished clean, and the launching
# notebook staged /root/.secrets.env (GCP_BACKUP_BASE + HF_TOKEN).
# Idempotent: re-running resumes (generate.py skips finished tracks by WAV+exit-0).
set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO" || exit 1

: "${GCP_BACKUP_BASE:?GCP_BACKUP_BASE must be set — . /root/.secrets.env}"
JSON="INFERENCE/songs.v3_jarir_seed.json"
DEST="/content/converter/out/v3"
PROBE_PREFIX="$GCP_BACKUP_BASE/v3_arabmaqamrock_lora"
log(){ printf '[%s] %s\n' "$(date -u +%FT%TZ)" "$*"; }

# --- 0. GPU guard (AGENTS: one shared GPU, never overlap) -------------------
if ! command -v nvidia-smi >/dev/null 2>&1; then
  log "FAIL: nvidia-smi not found — no GPU on this host"; exit 1
fi
log "GPU: $(nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv,noheader | tr '\n' ' ')"
if nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null | grep -q '[0-9]'; then
  log "FAIL: another process is using the GPU — refusing to overlap"; exit 1
fi

# --- 1. stage the converted v3 adapter pair from GCS ------------------------
mkdir -p "$DEST"
log "staging $PROBE_PREFIX/convert -> $DEST"
gcloud storage rsync -r "$PROBE_PREFIX/convert" "$DEST" || { log "FAIL: adapter staging"; exit 1; }
for f in v3_arabmaqamrock_lora_ar.safetensors v3_arabmaqamrock_lora_nar.safetensors; do
  [ -f "$DEST/$f" ] || { log "FAIL: missing $DEST/$f"; exit 1; }
done
log "adapter ok: $(cd "$DEST" && sha256sum v3_arabmaqamrock_lora_ar.safetensors | awk '{print $1}')"

# --- 2. validate (no GPU, prints the 5-take plan) ---------------------------
python INFERENCE/generate.py "$JSON" --dry-run || { log "FAIL: dry-run"; exit 1; }

# --- 3. generate — 5 takes, fresh random seeds, sequential ------------------
log "generating (5 takes, expect ~45-60 min on a T4)"
python INFERENCE/generate.py "$JSON" --label v3_jarir_seeds
rc=$?
log "generate.py exit=$rc"

# --- 4. bank the run folder to GCS ------------------------------------------
RUN="$(readlink -f /content/audiocpp_inference/out/latest 2>/dev/null || true)"
if [ -n "$RUN" ] && [ -d "$RUN" ]; then
  base="$(basename "$RUN")"
  if gcloud storage rsync -r "$RUN" "$PROBE_PREFIX/listening/$base"; then
    log "banked -> $PROBE_PREFIX/listening/$base"
  else
    log "WARN: banking to GCS failed (run dir stays local: $RUN)"
  fi
  [ -f "$RUN/batch_summary.txt" ] && { echo "----- batch_summary.txt -----"; cat "$RUN/batch_summary.txt"; }
fi
log "done (rc=$rc)"
exit "$rc"
