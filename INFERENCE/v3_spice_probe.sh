#!/usr/bin/env bash
# Pass 1 of docs/V3_SPICE_SWEEP.md -- paired single-knob screen. Run DETACHED on the GPU VM.
set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; REPO="$(cd "$SCRIPT_DIR/.." && pwd)"
CONV=/content/converter/out
JSON="$SCRIPT_DIR/songs.v3_spice.json"
OUTROOT="${OUTROOT:-/content/audiocpp_inference/out/v3_spice_probe}"
: "${GCP_BACKUP_BASE:?source /root/.secrets.env}"
ARMS="${ARMS:-ref g1.5 g2.5 t1.2 t1.4 rp1.4 ar0.7 ck4500 ck3500 ck2500}"
DRY="${DRY:-}"
command -v nvidia-smi >/dev/null || { echo "no GPU"; exit 1; }
nvidia-smi --query-compute-apps=pid --format=csv,noheader | grep -q '[0-9]' \
  && { echo "GPU busy - refusing"; exit 1; }
cd "$REPO" || exit 1
arm_spec(){ case "$1" in
  ref)    echo "FINAL||1.0|1.0|" ;;
  g1.5)   echo "FINAL||1.0|1.0|guidance_scale=1.5" ;;
  g2.5)   echo "FINAL||1.0|1.0|guidance_scale=2.5" ;;
  t1.2)   echo "FINAL||1.0|1.0|semantic_temperature=1.2" ;;
  t1.4)   echo "FINAL||1.0|1.0|semantic_temperature=1.4" ;;
  rp1.4)  echo "FINAL||1.0|1.0|semantic_repetition_penalty=1.4" ;;
  ar0.7)  echo "FINAL||0.7|1.0|" ;;
  ck4500) echo "CK|000004500|1.0|1.0|" ;;
  ck3500) echo "CK|000003500|1.0|1.0|" ;;
  ck2500) echo "CK|000002500|1.0|1.0|" ;;
  *) return 1;; esac; }
mkdir -p "$OUTROOT"
for arm in $ARMS; do
  spec="$(arm_spec "$arm")" || { echo "unknown arm $arm" >&2; exit 2; }
  IFS='|' read -r kind n ascale nscale extra <<<"$spec"   # kind FINAL|CK ; n = ck step
  if [ "$kind" = "CK" ]; then
    ar="$CONV/ck$n/v3_arabmaqamrock_lora_${n}_ar.safetensors"
    nar="$CONV/ck$n/v3_arabmaqamrock_lora_${n}_nar.safetensors"
  else
    ar="$CONV/v3_arabmaqamrock_lora_ar.safetensors"
    nar="$CONV/v3_arabmaqamrock_lora_nar.safetensors"
  fi
  if [ ! -f "$ar" ] || [ ! -f "$nar" ]; then
    echo "[FAIL] arm=$arm missing adapter ($ar)" >&2; continue
  fi
  gargs=(); [ -n "$DRY" ] && gargs+=(--dry-run)
  echo "=== [arm $arm] ar=$ascale nar=$nscale extra='$extra' $(date -u +%FT%TZ) ==="
  LORA_AR_SCALE="$ascale" LORA_NAR_SCALE="$nscale" EXTRA_REQUEST_OPTS="$extra" \
    python INFERENCE/generate.py "$JSON" --lora-ar "$ar" --lora-nar "$nar" \
      --out-dir "$OUTROOT/$arm" --label "v3_spice_$arm" "${gargs[@]}"
done
gcloud storage rsync -r "$OUTROOT" "$GCP_BACKUP_BASE/v3_arabmaqamrock_lora/spice_probe" \
  && echo "banked -> $GCP_BACKUP_BASE/v3_arabmaqamrock_lora/spice_probe"
