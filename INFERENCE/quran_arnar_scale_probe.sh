#!/usr/bin/env bash
# AR-vs-NAR LoRA scale split on the alpha=0.1 quran-merged adapter (qahh_a0p1).
#
# Diagnostic: the user's "overcorrection" = tajweed prosody (madd/waqf/idgham/
# iqlab) bleeding into singing. config/quran_ahh_r8.yml:5-9 says the AR branch
# moves recitation prosody (madd/waqf) while the NAR branch renders actual
# articulation (makhraj). This splits the two scales at runtime to attribute
# the bleed. Same prompt (in-distribution canonical), same seed -> paired.
#
#   ar100_nar100  control (= current alpha0.1 render)
#   ar050_nar100  cut recitation cadence, keep articulation
#   ar100_nar050  keep cadence, cut articulation (attribution)
#   ar050_nar050  halve both
#
# Stop:   pkill -f jarir_arnar_probe   (or pkill -f arnar_probe.sh)
# Resume: bash /content/arnar_probe.sh  (re-runs all arms; per-arm outputs overwrite)
set -u
REPO=/content/maqamrock-yue2-lora-finetuning
OUT=/content/audiocpp_inference/out/jarir_arnar_probe
STYLE=/content/prompts/jarir_canonical_style.txt
LYRICS=/content/prompts/jarir_lyrics.txt
QA=/content/converter/out/qahh_a0p1
SEED=20261010
mkdir -p "$OUT"
cd "$REPO"

run() {  # name ar_scale nar_scale
  echo "=== ARM $1  ar_lora_scale=$2 nar_lora_scale=$3  $(date -u +%FT%TZ) ==="
  OUT_DIR="$OUT" STYLE_FILE="$STYLE" LYRICS_FILE="$LYRICS" \
    LORA_AR="$QA/akbar_arabic_rock_lora_ar.safetensors" \
    LORA_NAR="$QA/akbar_arabic_rock_lora_nar.safetensors" \
    LORA_AR_SCALE="$2" LORA_NAR_SCALE="$3" \
    bash INFERENCE/run_one.sh "$1" "$SEED" 8000
  echo "=== ARM $1 exit=$? $(date -u +%FT%TZ) ==="
}

run ar100_nar100 1.0 1.0
run ar050_nar100 0.5 1.0
run ar100_nar050 1.0 0.5
run ar050_nar050 0.5 0.5
echo "=== ALL DONE $(date -u +%FT%TZ) ==="
