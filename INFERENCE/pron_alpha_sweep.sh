#!/usr/bin/env bash
# Task 17 -- pronunciation alpha sweep: 5 configs x 4 held-out maqams = 20 songs.
#
# One shared seed, auto cap (same lyrics -> same cap across configs). MAQAM-MAJOR
# order (all 5 configs of a maqam before moving on) so an early death still leaves
# every finished maqam a complete 5-way comparison.
#
# Configs (adapters built offline by merge_pron_lora.py + the converter):
#   a0           alpha=0,           pron ckpt final   (== v2 verbatim baseline)
#   c3050_a0.5   alpha=0.5,         pron ckpt 3050
#   c3050_a1.0   alpha=1.0,         pron ckpt 3050
#   cfinal_a0.5  alpha=0.5,         pron ckpt final
#   cfinal_a1.0  alpha=1.0,         pron ckpt final
#
# Resumable: a track whose WAV exists AND whose _time.txt says "Exit status: 0"
# is skipped. Failures are appended to $SWEEP/_failed.log and do not stop the run.
#
# Usage: bash INFERENCE/pron_alpha_sweep.sh
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_ONE="$SCRIPT_DIR/run_one.sh"
SWEEP=/content/pron_sweep
CONV=/content/converter/out
SEED=20260924
MAQAMS="Hijaz Kurd Nahawand Ajam"
CFGS="a0 c3050_a0.5 c3050_a1.0 cfinal_a0.5 cfinal_a1.0"
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

echo "=== pron_alpha_sweep done $(date -u +%FT%TZ) ==="
