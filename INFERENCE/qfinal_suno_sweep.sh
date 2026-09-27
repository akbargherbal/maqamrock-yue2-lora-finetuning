#!/usr/bin/env bash
# qfinal x {Suno-native, trigger-only} x alpha {0.3, 0.5}: 4 batches x 8 songs = 32 tracks.
#
# qfinal = quran_long_aya_r8_s10 final merged with the v2 style adapter (built by
# agent_notes/current.md Phase 1); adapters live in /content/converter/out/qfinal_a{0.3,0.5}.
# Lyrics are verbatim Suno (tags kept). Arm "suno" = raw Suno styles incl. meta tags;
# arm "trigger" = style "arabmaqamrock" only. See agent_notes/current.md.
#
# Outputs land under /content/audiocpp_inference/out/qfinal_suno_sweep/ so the
# `backup_to_gcp.py --inference` daemon mirrors them.
#
# Resumable: generate.py --out-dir skips tracks whose WAV succeeded; re-run to continue.
# A 1-track smoke (trigger a0.3) gates the full sweep; on failure nothing else runs.
#
# Usage (detached):
#   setsid nohup bash INFERENCE/qfinal_suno_sweep.sh \
#     > /content/logs/qfinal_suno_sweep.log 2>&1 & disown
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$SCRIPT_DIR/.." && pwd)"
SWEEP=/content/audiocpp_inference/out/qfinal_suno_sweep
CONV=/content/converter/out
ARMS="suno trigger"
ALPHAS="0.3 0.5"

cd "$REPO" || exit 1
mkdir -p "$SWEEP"

run_batch() {  # <arm> <alpha> <outdir> [extra generate.py flags...]
  local arm="$1" a="$2" out="$3"; shift 3
  local adir="$CONV/qfinal_a$a"
  local ar="$adir/akbar_arabic_rock_lora_ar.safetensors"
  local nar="$adir/akbar_arabic_rock_lora_nar.safetensors"
  if [ ! -f "$ar" ] || [ ! -f "$nar" ]; then
    echo "[FAIL] adapter pair missing: $adir"; return 2
  fi
  echo "=== batch arm=$arm alpha=$a -> $out ($(date -u +%FT%TZ)) ==="
  python INFERENCE/generate.py "INFERENCE/songs.qfinal_${arm}.json" \
    --lora-ar "$ar" --lora-nar "$nar" \
    --out-dir "$out" --label "qfinal_${arm}_a$a" "$@"
  local rc=$?
  echo "=== batch arm=$arm alpha=$a exit=$rc $(date -u +%FT%TZ) ==="
  return $rc
}

# --- smoke gate: one track must succeed before the full sweep -----------------
echo "=== smoke: trigger a0.3, 1 track ==="
if run_batch trigger 0.3 "$SWEEP/trigger_a0.3" --limit 1; then
  echo "=== SMOKE OK ==="
else
  echo "=== SMOKE FAILED — no full batches run; fix and re-run ==="
  exit 1
fi

# --- full sweep (trigger a0.3 resumes over the smoke track) -------------------
rc_total=0
for a in $ALPHAS; do
  for arm in $ARMS; do
    run_batch "$arm" "$a" "$SWEEP/${arm}_a$a" || rc_total=1
  done
done

echo "=== qfinal_suno_sweep done (rc_total=$rc_total) $(date -u +%FT%TZ) ==="
exit $rc_total
