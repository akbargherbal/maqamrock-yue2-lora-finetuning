#!/usr/bin/env bash
# Probe S — prompt sensitivity x LoRA on/off. 6 arms, ONE pinned seed, ONE session.
# Run DETACHED on the GPU VM. Plan/thread: agent_notes/current.md ("Probe S"), docs/V3_SPICE_SWEEP.md.
#
#   arm                prompt          LoRA   question it answers
#   v3pp_S0_full       T0 full         on     control
#   v3pp_S1_core       T2 core-only    on     does the prompt move the output with the LoRA on?
#   v3pp_S2_retarget   T3 retargeted   on     does genre/groove steer?
#   v3pp_S4_prune      T1 safe prune   on     the measured-safe removal (drops "110 BPM")
#   v3pp_B1_base_full  T0 full         OFF    what the base model does with the real prompt
#   v3pp_B2_base_core  T2 core-only    OFF    does the base model respond to the prompt at all?
#
# Song: kurd_Lamiyat_Alshanfara_16082026_003_1b956cd0 (lyrics verbatim; style varies per arm).
# Seed 2640605763 for every arm, cap 7000 (duration_cap.py q0.95).
# Manifests: INFERENCE/songs.v3_prompt_probe.json       (LoRA on)
#            INFERENCE/songs.v3_prompt_probe.base.json  (LoRA off -> adapter scale 0.0)
# DRY=1 skips the GPU checks (CPU validation) and passes --dry-run to generate.py.
set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; REPO="$(cd "$SCRIPT_DIR/.." && pwd)"
CONV=/content/converter/out
OUTROOT="${OUTROOT:-/content/audiocpp_inference/out/v3_prompt_probe}"
DRY="${DRY:-}"
AR="$CONV/v3_arabmaqamrock_lora_ar.safetensors"
NAR="$CONV/v3_arabmaqamrock_lora_nar.safetensors"

if [ -z "$DRY" ]; then
  : "${GCP_BACKUP_BASE:?source /root/.secrets.env}"
  BANK="${BANK:-$GCP_BACKUP_BASE/v3_arabmaqamrock_lora/prompt_probe}"
  command -v nvidia-smi >/dev/null || { echo "no GPU"; exit 1; }
  nvidia-smi --query-compute-apps=pid --format=csv,noheader | grep -q '[0-9]' \
    && { echo "GPU busy - refusing"; exit 1; }
  { [ -f "$AR" ] && [ -f "$NAR" ]; } || { echo "[FAIL] missing adapter in $CONV"; exit 1; }
fi

cd "$REPO" || exit 1
gargs=(); [ -n "$DRY" ] && gargs+=(--dry-run)
[ -z "$DRY" ] && mkdir -p "$OUTROOT"

echo "=== [LoRA ON 1.0/1.0] S0 S1 S2 S4  $(date -u +%FT%TZ) ==="
LORA_AR_SCALE=1.0 LORA_NAR_SCALE=1.0 \
  python INFERENCE/generate.py INFERENCE/songs.v3_prompt_probe.json \
    --lora-ar "$AR" --lora-nar "$NAR" \
    --out-dir "$OUTROOT/lora_on" --label v3_prompt_probe_on "${gargs[@]}"

echo "=== [LoRA OFF 0.0/0.0] B1 B2  $(date -u +%FT%TZ) ==="
LORA_AR_SCALE=0.0 LORA_NAR_SCALE=0.0 \
  python INFERENCE/generate.py INFERENCE/songs.v3_prompt_probe.base.json \
    --lora-ar "$AR" --lora-nar "$NAR" \
    --out-dir "$OUTROOT/lora_off" --label v3_prompt_probe_off "${gargs[@]}"

if [ -z "$DRY" ]; then
  gcloud storage rsync -r "$OUTROOT" "$BANK" && echo "banked -> $BANK"
fi
