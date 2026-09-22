#!/usr/bin/env bash
# One observed YuE2 generation (LoRA AR+NAR scale 1.0).
# Usage: run_one.sh <Maqam> <seed> [semantic_max_tokens]
#   cap defaults to "auto": derived from the lyrics via the canonical repo copy
#   INFERENCE/duration_cap.py (docs/text_to_duration_formula.md: 95th-percentile
#   cap dur_cap = 111.1 + 0.3126*N_letters, rounded to 10 s; covers 94.8%).
#   The staged GCS scripts/duration_cap.py is a mirror -- the repo copy wins.
#   For a more forgiving cap the doc's 97.5th percentile is dur = 122.9 + 0.3081*N.
# Writes everything under out/ so it can be monitored from another terminal:
#   out/<Maqam>_<seed>.wav        audio
#   out/<Maqam>_<seed>.log        CLI --log (TRACE/TIMING, errors)
#   out/<Maqam>_<seed>_time.txt   /usr/bin/time -v (wall, max RSS, CPU%)
#   out/<Maqam>_<seed>_gpu.csv    1 Hz: util, mem_used, power, temp
#   out/_runs_status.log          one START/END line per run (always)
set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT=/content/audiocpp_inference
M="${1:?usage: run_one.sh <Maqam> <seed> [cap|auto]}"
S="${2:?usage: run_one.sh <Maqam> <seed> [cap|auto]}"
CAP_ARG="${3:-auto}"
BIN="$ROOT/bin/audiocpp_cli"
MODEL="$ROOT/models/Yue2-3B-GGUF"
OUT="$ROOT/out"
mkdir -p "$OUT"

style="$ROOT/prompts/${M}_style.txt"
lyrics="$ROOT/prompts/${M}_lyrics.txt"
wav="$OUT/${M}_${S}.wav"
log="$OUT/${M}_${S}.log"
tfile="$OUT/${M}_${S}_time.txt"
csv="$OUT/${M}_${S}_gpu.csv"
status="$OUT/_runs_status.log"

if [ "$CAP_ARG" = "auto" ]; then
  CAP=$(python3 "$SCRIPT_DIR/duration_cap.py" "$lyrics")
else
  CAP="$CAP_ARG"
fi

: > "$csv"
( while :; do nvidia-smi --query-gpu=utilization.gpu,memory.used,power.draw,temperature.gpu \
    --format=csv,noheader,nounits >> "$csv" 2>/dev/null; sleep 1; done ) &
SM=$!

line="=== START ${M} seed=${S} cap=${CAP} (${CAP_ARG}) $(date -u +%FT%TZ) ==="
echo "$line"; echo "$line" >> "$status"

/usr/bin/time -v -o "$tfile" \
  "$BIN" --task gen --family yue2 --model "$MODEL" --backend cuda --threads 8 \
  --session-option yue2.model_gguf=yue2-3b-bf16.gguf \
  --session-option yue2.vae_gguf=yue2-vae-f16.gguf \
  --session-option yue2.ar_lora=/content/converter/out/akbar_arabic_rock_lora_ar.safetensors \
  --session-option yue2.ar_lora_scale=1.0 \
  --session-option yue2.nar_lora=/content/converter/out/akbar_arabic_rock_lora_nar.safetensors \
  --session-option yue2.nar_lora_scale=1.0 \
  --session-option yue2.attention=flash \
  --lyrics "$(cat "$lyrics")" \
  --request-option style="$(cat "$style")" \
  --request-option cot=off \
  --request-option semantic_max_tokens="$CAP" \
  --seed "$S" \
  --out "$wav" \
  --log > "$log" 2>&1
rc=$?
kill $SM 2>/dev/null; wait $SM 2>/dev/null

line="=== END ${M} seed=${S} exit=${rc} cap=${CAP} $(date -u +%FT%TZ) ==="
echo "$line"; echo "$line" >> "$status"
exit "$rc"
