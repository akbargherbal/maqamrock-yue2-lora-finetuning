#!/usr/bin/env bash
# Phase 2 sampler / request-option knob probe.
#
# Question (docs/QURAN_PRON_REVIEW.md §2.5, §5): the held-out 2:255 blind listen
# put the adapter's two defects at generation time -- c4500_simple loops/restarts,
# c9000_simple has audible reverb -- while pronunciation is ~base. Is that the
# sampler, or the weights? Vary exactly ONE audiocpp request option per config on
# the lone-AR quran_ahh_r8 adapters and regenerate the same held-out aya.
#
# Mechanics: build the quran_pt_probe songs JSON once (exact training caption,
# seed 20261004, cap 7500), then call generate.py once per knob with a pinned
# --out-dir so a crashed run resumes (succeeded tracks are skipped). generate.py
# copies os.environ into run_one.sh, so EXTRA_REQUEST_OPTS reaches the CLI.
#
# The default-knob ANCHOR is the existing run
#   /content/audiocpp_inference/out/20261005-072738_quran_pt_probe/
# (same arms, seed, cap) -- it is NOT regenerated here.
#
# Usage (GPU VM, inference set up):
#   bash INFERENCE/quran_knob_probe.sh
#   ARMS="c4500" CFGS="rp1.4 pw100" bash INFERENCE/quran_knob_probe.sh   # subset
#   DRY=1 bash INFERENCE/quran_knob_probe.sh                            # plan only, no GPU
#
# Defaults: 2 arms x 2 scripts x 5 knobs = 20 tracks (~2 h on a T4).
set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$SCRIPT_DIR/.." && pwd)"
STAGE="${STAGE:-/content/converter/out/phase2}"
CONVERT="${GCP_BACKUP_BASE:?GCP_BACKUP_BASE is unset}/quran_ahh_r8/convert"
PROBE="${PROBE:-/content/quran_knob_probe}"
ANCHOR="${ANCHOR:-20261005-072738_quran_pt_probe}"
ARMS="${ARMS:-c4500 c9000}"
CFGS="${CFGS:-g1.0 g1.5 t0.8 rp1.4 pw100}"
DRY="${DRY:-}"

opts_for() {
  case "$1" in
    g1.0)  printf '%s' 'guidance_scale=1.0' ;;
    g1.5)  printf '%s' 'guidance_scale=1.5' ;;
    t0.8)  printf '%s' 'semantic_temperature=0.8' ;;
    rp1.4) printf '%s' 'semantic_repetition_penalty=1.4' ;;
    pw100) printf '%s' 'semantic_penalty_window=100' ;;
    *) echo "quran_knob_probe: unknown cfg '$1'" >&2; return 1 ;;
  esac
}

# 1. Stage the arms (idempotent). 17 MB each; skip if already present.
for arm in $ARMS; do
  d="$STAGE/$arm"
  if [ ! -f "$d/quran_ahh_r8_ar.safetensors" ] || [ ! -f "$d/quran_ahh_r8_nar.safetensors" ]; then
    echo "[stage] $arm <- $CONVERT/$arm"
    mkdir -p "$d"
    gsutil -m cp "$CONVERT/$arm/quran_ahh_r8_ar.safetensors" \
                  "$CONVERT/$arm/quran_ahh_r8_nar.safetensors" "$d/"
  fi
done

# 2. Build the songs JSON once (no generation) so every knob uses identical text.
JSON="$STAGE/songs.quran_pt_probe.json"
if [ ! -f "$JSON" ]; then
  python "$SCRIPT_DIR/quran_pt_probe.py" --no-stage --stage "$STAGE" --dry-run >/dev/null
fi
[ -f "$JSON" ] || { echo "quran_knob_probe: failed to build $JSON" >&2; exit 1; }

# 3. One pinned run dir per knob, sequentially (two concurrent runs can OOM the NAR graph).
cd "$REPO"
mkdir -p "$PROBE"
touch "$PROBE/_failed.log"
for cfg in $CFGS; do
  extra="$(opts_for "$cfg")" || exit 1
  out="$PROBE/quran_knob_$cfg"
  mkdir -p "$out"
  printf '{"config":"%s","extra_request_opts":"%s","anchor_run":"%s"}\n' \
    "$cfg" "$extra" "$ANCHOR" > "$out/_knob.json"

  extra_args=()
  [ -n "$DRY" ] && extra_args+=(--dry-run)
  echo "=== [knob $cfg] EXTRA_REQUEST_OPTS='$extra' out=$out $(date -u +%FT%TZ) ==="
  EXTRA_REQUEST_OPTS="$extra" python "$SCRIPT_DIR/generate.py" "$JSON" \
    --no-trigger --out-dir "$out" "${extra_args[@]}"
  rc=$?
  if [ "$rc" -ne 0 ]; then
    echo "FAIL $cfg exit=$rc $(date -u +%FT%TZ)" | tee -a "$PROBE/_failed.log"
  fi
done

echo "=== quran_knob_probe done $(date -u +%FT%TZ) ==="
