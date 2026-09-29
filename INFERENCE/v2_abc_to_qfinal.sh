#!/usr/bin/env bash
# Hypothesis test: v2's own plan (exported as score.abc, route B1) used as the
# melody condition for qfinal_a0.3 -> does it keep v2's maqamrock arrangement
# while keeping qfinal's pronunciation? (docs/music-cover-feasibility.md §3, §4.2)
#
# Phase 1: v2, cot=full, stop_after=semantic, --out-dir -> writes v2's score.abc.
# Phase 2: four arms, same style/lyrics/seed, so the ONLY variable is the arm:
#   a0_cotoff        qfinal_a0.3, cot=off                       (control = current qfinal)
#   a1_cotfull_noabc qfinal_a0.3, cot=full                      (isolates the cot change)
#   a2_cotfull_abc   qfinal_a0.3, cot=full + abc_file=<v2 ABC>  (THE IDEA)
#   ref_v2_cotoff    v2, cot=off                                (arrangement/pron reference)
#
# The adapter trained cot=off, so cot=full/abc is off-distribution: a1 exists to
# separate the ABC effect from the cot effect. No training knobs are touched.
#
# FOREGROUND, sequential (never parallel: two runs can OOM the graph). For the
# full set, DETACHED:
#   setsid nohup bash INFERENCE/v2_abc_to_qfinal.sh > /content/logs/v2abc.log 2>&1 & disown
#   watch: tail -f /content/logs/v2abc.log
#   stop:  pkill -f 'v2_abc_to_qfinal.sh'      (re-runnable; overwrites its arms)
#
# Usage: bash INFERENCE/v2_abc_to_qfinal.sh [--dry-run|--stage]
#   --stage   pull qfinal_a0.3 from GCS into /content/converter/out/ (setup.sh
#             stages only the style pair), then exit. Run once per fresh VM.
# Env: SEED STYLE LYRICS TAG OUT_DIR CAP ABC_SCORE GCS_BASE V2_AR V2_NAR QF_AR QF_NAR
#   ABC_SCORE  reuse an existing score.abc (e.g. a Sheetsage2 ABC under out/abc_v2/)
#              and skip phase 1; unset -> phase 1 exports v2's own plan (route B1).
set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ROOT=/content/audiocpp_inference
BIN="$ROOT/bin/audiocpp_cli"
MODEL="$ROOT/models/Yue2-3B-GGUF"

MODE="${1:-}"
case "$MODE" in ""|--dry-run|--stage) ;; *) echo "usage: $0 [--dry-run|--stage]" >&2; exit 2;; esac

SEED="${SEED:-4148240095}"
TAG="${TAG:-hijaz_win}"
M_DIR="$REPO_DIR/manifests/test_verbatim_hijaz"
STYLE="${STYLE:-$M_DIR/styles/hijaz_winning.txt}"
LYRICS="${LYRICS:-$M_DIR/lyrics/01_nesib_as-is.txt}"
OUT_DIR="${OUT_DIR:-$ROOT/out/v2_abc_to_qfinal_seed$SEED}"

V2_AR="${V2_AR:-/content/converter/out/akbar_arabic_rock_lora_ar.safetensors}"
V2_NAR="${V2_NAR:-/content/converter/out/akbar_arabic_rock_lora_nar.safetensors}"
QF_AR="${QF_AR:-/content/converter/out/qfinal_a0.3/akbar_arabic_rock_lora_ar.safetensors}"
QF_NAR="${QF_NAR:-/content/converter/out/qfinal_a0.3/akbar_arabic_rock_lora_nar.safetensors}"
ABC_SCORE="${ABC_SCORE:-}"     # set to reuse an existing v2 score.abc and skip phase 1
GCS_BASE="${GCS_BASE:-gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning}"

preflight() {
  [ "$MODE" = "--dry-run" ] && return 0
  command -v nvidia-smi >/dev/null || { echo "no nvidia-smi; needs the Colab GPU runtime" >&2; exit 1; }
  if pgrep -af 'run[.]py' | grep -q 'akbar_arabic_rock_lor[a]'; then
    echo "an ai-toolkit training run is active — refusing (AGENTS.md §8)" >&2; exit 1
  fi
  for f in "$BIN" "$MODEL" "$STYLE" "$LYRICS" "$V2_AR" "$V2_NAR" "$QF_AR" "$QF_NAR"; do
    [ -e "$f" ] || { echo "missing: $f" >&2; exit 1; }
  done
  mkdir -p "$OUT_DIR"
}

cap_for() { if [ -n "${CAP:-}" ]; then echo "$CAP"; else python3 "$SCRIPT_DIR/duration_cap.py" "$1"; fi; }

stage() {
  echo "staging qfinal_a0.3 -> /content/converter/out/  (from $GCS_BASE)"
  command -v gsutil >/dev/null || { echo "no gsutil on PATH" >&2; exit 1; }
  gsutil -m cp -r "$GCS_BASE/loras/audio_cpp/pron/qfinal_a0.3" /content/converter/out/
}

# _gen <timefile> <logfile> <ar> <nar> <cot> <out-flag-args...> -- <extra request k=v...>
_gen() {
  local tfile="$1" logf="$2" ar="$3" nar="$4" cot="$5"; shift 5
  local outargs=() opts=()
  while [ "$1" != "--" ]; do outargs+=("$1"); shift; done
  shift
  for kv in "$@"; do opts+=(--request-option "$kv"); done
  /usr/bin/time -v -o "$tfile" \
    "$BIN" --task gen --family yue2 --model "$MODEL" --backend cuda --threads 8 \
    --session-option yue2.model_gguf=yue2-3b-bf16.gguf \
    --session-option yue2.vae_gguf=yue2-vae-f16.gguf \
    --session-option yue2.ar_lora="$ar" --session-option yue2.ar_lora_scale=1.0 \
    --session-option yue2.nar_lora="$nar" --session-option yue2.nar_lora_scale=1.0 \
    --session-option yue2.attention=flash \
    --lyrics "$(cat "$LYRICS")" \
    --request-option style="$(cat "$STYLE")" \
    --request-option cot="$cot" \
    "${opts[@]}" \
    --request-option semantic_max_tokens="$(cap_for "$LYRICS")" \
    --seed "$SEED" \
    "${outargs[@]}" >"$logf" 2>&1
}

phase1_export_v2_score() {
  local d="$OUT_DIR/v2_plan_${TAG}_${SEED}"
  local t="$OUT_DIR/v2_plan_${TAG}_${SEED}_time.txt"
  local l="$OUT_DIR/v2_plan_${TAG}_${SEED}.log"
  echo "== phase 1: export v2 score.abc (cot=full, stop_after=semantic) -> $d"
  if [ "$MODE" = "--dry-run" ]; then
    echo "  $BIN ... --request-option cot=full --request-option stop_after=semantic --out-dir $d"
    ABC_SCORE="$d/score.abc"; return 0
  fi
  mkdir -p "$d"
  _gen "$t" "$l" "$V2_AR" "$V2_NAR" full --out-dir "$d" --log -- stop_after=semantic
  echo "   exit=$?  score.abc=$( [ -s "$d/score.abc" ] && echo yes || echo NO )"
  ABC_SCORE="$d/score.abc"
}

# one <slug> <ar> <nar> <cot> [extra k=v ...]
one() {
  local slug="$1" ar="$2" nar="$3" cot="$4"; shift 4
  local wav="$OUT_DIR/${slug}_${TAG}_${SEED}.wav"
  local log="$OUT_DIR/${slug}_${TAG}_${SEED}.log"
  local t="$OUT_DIR/${slug}_${TAG}_${SEED}_time.txt"
  echo "== $slug cot=$cot seed=$SEED ${*:+[${*}]} -> $wav"
  if [ "$MODE" = "--dry-run" ]; then
    echo "  $BIN ... --request-option cot=$cot ${*:+[--request-option $*]} --out $wav"
    return 0
  fi
  echo "=== START $slug cot=$cot $(date -u +%FT%TZ) ===" >> "$OUT_DIR/_runs_status.log"
  _gen "$t" "$log" "$ar" "$nar" "$cot" --out "$wav" --log -- "$@"
  local rc=$?
  echo "=== END $slug exit=$rc $(date -u +%FT%TZ) ===" >> "$OUT_DIR/_runs_status.log"
  echo "   exit=$rc  wav=$( [ -s "$wav" ] && echo yes || echo NO )"
}

echo "v2_abc_to_qfinal seed=$SEED tag=$TAG style=$STYLE${MODE:+ ($MODE)}"
echo "out=$OUT_DIR"
if [ "$MODE" = "--stage" ]; then stage; echo "done. next: bash $0 --dry-run"; exit 0; fi
preflight
[ -n "$ABC_SCORE" ] || phase1_export_v2_score
[ "$MODE" = "--dry-run" ] || [ -s "$ABC_SCORE" ] || { echo "no ABC at $ABC_SCORE — abort" >&2; exit 1; }
echo "ABC: $ABC_SCORE"

one a0_cotoff        "$QF_AR" "$QF_NAR" off
one a1_cotfull_noabc "$QF_AR" "$QF_NAR" full
one a2_cotfull_abc   "$QF_AR" "$QF_NAR" full "abc_file=$ABC_SCORE"
one ref_v2_cotoff    "$V2_AR" "$V2_NAR" off

echo "done. outputs: $OUT_DIR"
echo "next: blind the arms (INFERENCE/prepare_ab_eval.py) or listen; judge arrangement AND pronunciation."
