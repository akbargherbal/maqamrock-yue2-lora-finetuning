#!/usr/bin/env bash
# Jarir lever probe — Tier 0 (AR/NAR adapter scale) + Tier 2 (sampler/request opts).
#
# The Tier 1/3 matrix (prompt wording, lyrics canonicalization, merge donor)
# lives in INFERENCE/songs.jarir_lever_probe.json and is run directly by
# generate.py (MODE=prompt). This driver covers the two levers generate.py
# cannot express per song -- adapter scale and audiocpp request options -- by
# running ONE pinned generate.py batch per arm over a SINGLE fixed song
# (songs.jarir_lever_scale.json), same seed, so every arm is paired.
#
# Adapter under test: the current alpha=0.1 merge of quran_ahh_r32 (AR+NAR rank32)
# into v2 -- /content/converter/out/qahh_a0p1. The v2-only arm is the style +
# diction ceiling reference (no Quran donor).
#
# Arms:
#   v2_1.0_1.0            v2 style only, both experts full        (reference)
#   qa_1.0_1.0            qahh a0.1, both experts full           (current baseline)
#   qa_0.5_1.0            cut merged-AR (prosody), keep NAR       (leading hypothesis)
#   qa_1.0_0.5            keep AR (prosody), cut NAR              (attribution)
#   qa_0.0_1.0            AR off entirely, NAR full               (base AR + quran NAR)
#   qa_0.5_1.0_rp1.4      + semantic_repetition_penalty=1.4       (attack madd/loops)
#   qa_0.5_1.0_t0.8       + semantic_temperature=0.8              (less prosodic wander)
#   qa_0.5_1.0_g1.0       + guidance_scale=1.0                    (let base voice through)
#   qa_0.5_1.0_notrigger  drop the 'arabmaqamrock ' trigger        (domain switch)
#
# Prereq: /content/converter/out/qahh_a0p1/akbar_arabic_rock_lora_{ar,nar}.safetensors
#   (restore from <GCS base>/quran_ahh_r32/maqamrock_merge/, or rebuild:
#    merge_quran_lora.py --alpha 0.1 + the converter).
#
# Usage (GPU VM, inference staged):
#   bash INFERENCE/jarir_lever_probe.sh                 # all scale/sampler arms
#   ARMS="qa_0.5_1.0 qa_1.0_0.5" bash INFERENCE/jarir_lever_probe.sh
#   MODE=prompt bash INFERENCE/jarir_lever_probe.sh     # Tier 1/3 matrix instead
#   DRY=1 bash INFERENCE/jarir_lever_probe.sh           # plan only, no GPU
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$SCRIPT_DIR/.." && pwd)"
CONV=/content/converter/out
V2_AR="$CONV/akbar_arabic_rock_lora_ar.safetensors"
V2_NAR="$CONV/akbar_arabic_rock_lora_nar.safetensors"
QA_AR="$CONV/qahh_a0p1/akbar_arabic_rock_lora_ar.safetensors"
QA_NAR="$CONV/qahh_a0p1/akbar_arabic_rock_lora_nar.safetensors"
SCALE_JSON="${SCALE_JSON:-$SCRIPT_DIR/songs.jarir_lever_scale.json}"
PROMPT_JSON="$SCRIPT_DIR/songs.jarir_lever_probe.json"
OUTROOT="${OUTROOT:-/content/audiocpp_inference/out/jarir_lever_probe}"
MODE="${MODE:-scale}"
DRY="${DRY:-}"
ARMS="${ARMS:-v2_1.0_1.0 qa_1.0_1.0 qa_0.5_1.0 qa_1.0_0.5 qa_0.0_1.0 qa_0.5_1.0_rp1.4 qa_0.5_1.0_t0.8 qa_0.5_1.0_g1.0 qa_0.5_1.0_notrigger}"

cd "$REPO" || exit 1

# arm -> "pair|ar_scale|nar_scale|extra_request_opts|extra_generate_flags"
arm_spec() {
  case "$1" in
    v2_1.0_1.0)           printf '%s' "v2|1.0|1.0||" ;;
    qa_1.0_1.0)           printf '%s' "qa|1.0|1.0||" ;;
    qa_0.5_1.0)           printf '%s' "qa|0.5|1.0||" ;;
    qa_1.0_0.5)           printf '%s' "qa|1.0|0.5||" ;;
    qa_0.0_1.0)           printf '%s' "qa|0.0|1.0||" ;;
    qa_0.5_1.0_rp1.4)     printf '%s' "qa|0.5|1.0|semantic_repetition_penalty=1.4|" ;;
    qa_0.5_1.0_t0.8)      printf '%s' "qa|0.5|1.0|semantic_temperature=0.8|" ;;
    qa_0.5_1.0_g1.0)      printf '%s' "qa|0.5|1.0|guidance_scale=1.0|" ;;
    qa_0.5_1.0_notrigger) printf '%s' "qa|0.5|1.0||--no-trigger" ;;
    *) return 1 ;;
  esac
}

if [ "$MODE" = "prompt" ]; then
  echo "=== Tier 1/3 prompt/lyrics/merge matrix -> $OUTROOT/prompt ==="
  args=(); [ -n "$DRY" ] && args+=(--dry-run)
  python INFERENCE/generate.py "$PROMPT_JSON" --label jarir_lever_prompt \
    --out-dir "$OUTROOT/prompt" "${args[@]}"
  exit $?
fi

mkdir -p "$OUTROOT" && touch "$OUTROOT/_failed.log"
rc_total=0
for arm in $ARMS; do
  spec="$(arm_spec "$arm")" || { echo "jarir_lever_probe: unknown arm '$arm'" >&2; exit 2; }
  IFS='|' read -r pair ar_scale nar_scale extra genflag <<<"$spec"
  if [ "$pair" = "v2" ]; then lora_ar="$V2_AR"; lora_nar="$V2_NAR"; else lora_ar="$QA_AR"; lora_nar="$QA_NAR"; fi
  if [ ! -f "$lora_ar" ] || [ ! -f "$lora_nar" ]; then
    echo "[FAIL] adapter pair missing for arm=$arm: $lora_ar" >&2
    echo "FAIL $arm (missing adapter) $(date -u +%FT%TZ)" >> "$OUTROOT/_failed.log"
    rc_total=1; continue
  fi
  out="$OUTROOT/$arm"
  mkdir -p "$out"
  printf '{"arm":"%s","pair":"%s","ar_lora":"%s","nar_lora":"%s","ar_scale":"%s","nar_scale":"%s","extra_request_opts":"%s","generate_flags":"%s"}\n' \
    "$arm" "$pair" "$lora_ar" "$lora_nar" "$ar_scale" "$nar_scale" "$extra" "$genflag" > "$out/_knob.json"

  gargs=(); [ -n "$DRY" ] && gargs+=(--dry-run)
  [ -n "$genflag" ] && gargs+=("$genflag")

  echo "=== [arm $arm] ar=$ar_scale nar=$nar_scale extra='$extra' flags='$genflag' -> $out ($(date -u +%FT%TZ)) ==="
  LORA_AR_SCALE="$ar_scale" LORA_NAR_SCALE="$nar_scale" EXTRA_REQUEST_OPTS="$extra" \
    python INFERENCE/generate.py "$SCALE_JSON" \
      --lora-ar "$lora_ar" --lora-nar "$lora_nar" \
      --out-dir "$out" --label "jarir_lever_$arm" "${gargs[@]}"
  rc=$?
  [ "$rc" -ne 0 ] && { echo "FAIL $arm exit=$rc $(date -u +%FT%TZ)" | tee -a "$OUTROOT/_failed.log"; rc_total=1; }
done

echo "=== jarir_lever_probe done (rc_total=$rc_total) $(date -u +%FT%TZ) ==="
exit $rc_total
