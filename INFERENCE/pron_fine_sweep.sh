#!/usr/bin/env bash
# Fine alpha sweep: pron checkpoint FIXED at 3050, alpha in {0.2,0.3,0.55,0.65},
# held-out maqams Hijaz + Kurd only. 4 configs x 2 maqams = 8 tracks.
#
# Single-variable comparison against Task 17's existing a0 / c3050_a0.5 tracks:
# identical held-out prompts (staged /content/audiocpp_inference/prompts/
# {Hijaz,Kurd}_{style,lyrics}.txt), identical seed (20260924), identical auto cap
# and binary; ONLY alpha varies.
#
# MAQAM-MAJOR order (all 4 alphas of a maqam before moving on), matching Task 17.
#
# Resumable: a track whose WAV exists AND whose _time.txt says "Exit status: 0"
# is skipped. Failures append to $SWEEP/_failed.log and do not stop the run.
#
# Usage: bash INFERENCE/pron_fine_sweep.sh
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_ONE="$SCRIPT_DIR/run_one.sh"
SWEEP=/content/pron_fine_sweep
CONV=/content/converter/out
SEED=20260924
MAQAMS="Hijaz Kurd"
CFGS="c3050_a0.2 c3050_a0.3 c3050_a0.55 c3050_a0.65"
FAILED="$SWEEP/_failed.log"

mkdir -p "$SWEEP"
touch "$FAILED"

for M in $MAQAMS; do
  for CFG in $CFGS; do
    OUT="$SWEEP/$CFG"
    AR="$CONV/$CFG/akbar_arabic_rock_lora_ar.safetensors"
    NAR="$CONV/$CFG/akbar_arabic_rock_lora_nar.safetensors"
    wav="$OUT/${M}_${SEED}.wav"
    tfile="$OUT/${M}_${SEED}_time.txt"

    if [ -f "$wav" ] && [ -f "$tfile" ] && grep -q "Exit status: 0" "$tfile"; then
      echo "[skip] $CFG $M (already succeeded)"
      continue
    fi

    echo "=== [$CFG $M] $(date -u +%FT%TZ) ==="
    OUT_DIR="$OUT" LORA_AR="$AR" LORA_NAR="$NAR" \
      "$RUN_ONE" "$M" "$SEED" auto
    rc=$?
    if [ "$rc" -ne 0 ]; then
      echo "FAIL $CFG $M exit=$rc $(date -u +%FT%TZ)" | tee -a "$FAILED"
    fi
  done
done

echo "=== pron_fine_sweep done $(date -u +%FT%TZ) ==="
