#!/usr/bin/env bash
# Probe Q — pruned style x guidance_scale x repetition penalty. 6 tracks, ONE pinned seed, ONE session.
# Run DETACHED on the GPU VM. Design + read-out: agent_notes/current.md ("Probe Q").
#
#   arm                    style              EXTRA_REQUEST_OPTS
#   v3q_Q0_ctm_default     core+tempo+mood    (none -> guidance 1.01, temp 1.0, rep-pen 1.2)
#   v3q_Q1_ctm_g15         core+tempo+mood    guidance_scale=1.5
#   v3q_Q2_ctm_g20         core+tempo+mood    guidance_scale=2.0
#   v3q_Q3_ctm_rp135       core+tempo+mood    semantic_repetition_penalty=1.35
#   v3q_Q4_ctm_g15rp135    core+tempo+mood    guidance_scale=1.5 semantic_repetition_penalty=1.35
#   v3q_Q5_retarget_g15    T3 retarget        guidance_scale=1.5
#
# Song: kurd_Lamiyat_Alshanfara_16082026_003_1b956cd0. LYRICS FROZEN — no lyric edits; the text lives
# in one place, INFERENCE/probe_q_lyrics.txt, shared by every arm. Seed 2640605763, cap 7000 (as in
# Probe S, so the arms stay comparable).
#
# Free drift anchor, no GPU track spent: reuse the banked v3pp_S1_core_2640605763.wav in the eval
# folder. Generation is deterministic (Pass 1: the `ref` arm came back byte-identical), so re-rendering
# that arm would produce the same file — any rating difference is pure listener drift.
#
# DRY=1 skips the GPU checks and passes --dry-run to generate.py.
set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; REPO="$(cd "$SCRIPT_DIR/.." && pwd)"
CONV=/content/converter/out
OUTROOT="${OUTROOT:-/content/audiocpp_inference/out/v3_probe_q}"
DRY="${DRY:-}"
AR="$CONV/v3_arabmaqamrock_lora_ar.safetensors"
NAR="$CONV/v3_arabmaqamrock_lora_nar.safetensors"

if [ -z "$DRY" ]; then
  : "${GCP_BACKUP_BASE:?source /root/.secrets.env}"
  BANK="${BANK:-$GCP_BACKUP_BASE/v3_arabmaqamrock_lora/probe_q}"
  command -v nvidia-smi >/dev/null || { echo "no GPU"; exit 1; }
  nvidia-smi --query-compute-apps=pid --format=csv,noheader | grep -q '[0-9]' \
    && { echo "GPU busy - refusing"; exit 1; }
  { [ -f "$AR" ] && [ -f "$NAR" ]; } || { echo "[FAIL] missing adapter in $CONV"; exit 1; }
fi

cd "$REPO" || exit 1
gargs=(); [ -n "$DRY" ] && gargs+=(--dry-run)
[ -z "$DRY" ] && mkdir -p "$OUTROOT"

run_group() {                 # run_group <group> <out-subdir> <EXTRA_REQUEST_OPTS>
  local group="$1" sub="$2" opts="${3:-}"
  echo "=== [${group}] EXTRA_REQUEST_OPTS='${opts}'  $(date -u +%FT%TZ) ==="
  EXTRA_REQUEST_OPTS="$opts" \
    python INFERENCE/generate.py "INFERENCE/songs.v3_probe_q.${group}.json" \
      --lora-ar "$AR" --lora-nar "$NAR" \
      --out-dir "$OUTROOT/$sub" --label "v3_probe_q_${group}" "${gargs[@]}"
}

run_group default   q0                 ""
run_group g15       q1_q5              "guidance_scale=1.5"
run_group g20       q2                 "guidance_scale=2.0"
run_group rp135     q3                 "semantic_repetition_penalty=1.35"
run_group g15rp135  q4                 "guidance_scale=1.5 semantic_repetition_penalty=1.35"

if [ -z "$DRY" ]; then
  gcloud storage rsync -r "$OUTROOT" "$BANK" && echo "banked -> $BANK"
fi
