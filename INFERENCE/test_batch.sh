#!/usr/bin/env bash
# Companion to manifests/test_verbatim_hijaz/batch.json — the arms generate.py
# CANNOT run:
#   B. knob arms  -> run_one.sh with EXTRA_REQUEST_OPTS (cot=off)
#   C. ABC arms   -> direct audiocpp_cli with cot=melody [+ abc_file]
# (generate.py's schema is strict and run_one.sh hardcodes cot=off + has no
#  abc_file, so these have to call the binary directly.)
#
# All arms use ONE track/seed (default seed 4148240095, the guide render) so the
# only moving part is the knob / the ABC conditioning.
#
# FOREGROUND, sequential (never parallel: two runs can OOM the NAR graph).
# For a long set run it detached with a log, e.g.
#   nohup bash INFERENCE/test_batch.sh all > /content/logs/test_verbatim.log 2>&1 &
#   tail -f /content/logs/test_verbatim.log          # watch
#   pkill -f 'test_batch.sh all'                     # stop (foreground: Ctrl+C)
#
# Usage: bash INFERENCE/test_batch.sh <knobs|abc|all> [--dry-run]
#
# Env overrides:
#   SEED       default 4148240095
#   STYLE      default <repo>/manifests/test_verbatim_hijaz/styles/hijaz_winning.txt
#   MOD_STYLE  default <repo>/manifests/test_verbatim_hijaz/styles/hijaz_modified.txt
#   RAW_STYLE  default <repo>/manifests/test_verbatim_hijaz/styles/hijaz_sunoblk.txt
#              (the track's own raw Suno block = the l0_raw form that scored 5/5 MaqamRock)
#   LYRICS     default <repo>/manifests/test_verbatim_hijaz/lyrics/01_nesib_as-is.txt
#   ABC_FILE   melody.abc for the cover arms. Required for 'abc'/'all' unless
#              you only want the cot=melody-no-abc arm. Make it with
#              INFERENCE/sheetsage2_transcribe.py from the V2 guide wav
#              (docs/music-cover-feasibility.md §4.2 route B2), or export v2's own
#              plan via 'cot=full --out-dir' (route B1).
#   OUT_DIR    default $ROOT/out/test_verbatim_hijaz
#   CAP        default auto (INFERENCE/duration_cap.py, 95th pct)
#   LORA_AR/LORA_NAR  default the live converted v2 pair
set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ROOT=/content/audiocpp_inference
BIN="$ROOT/bin/audiocpp_cli"
MODEL="$ROOT/models/Yue2-3B-GGUF"

MODE="${1:-}"; DRY="${2:-}"
case "$MODE" in knobs|abc|all) ;; *) echo "usage: $0 <knobs|abc|all> [--dry-run]" >&2; exit 2;; esac

SEED="${SEED:-4148240095}"
STYLE="${STYLE:-$REPO_DIR/manifests/test_verbatim_hijaz/styles/hijaz_winning.txt}"
MOD_STYLE="${MOD_STYLE:-$REPO_DIR/manifests/test_verbatim_hijaz/styles/hijaz_modified.txt}"
RAW_STYLE="${RAW_STYLE:-$REPO_DIR/manifests/test_verbatim_hijaz/styles/hijaz_sunoblk.txt}"
LYRICS="${LYRICS:-$REPO_DIR/manifests/test_verbatim_hijaz/lyrics/01_nesib_as-is.txt}"
ABC_FILE="${ABC_FILE:-}"
OUT_DIR="${OUT_DIR:-$ROOT/out/test_verbatim_hijaz}"
LORA_AR="${LORA_AR:-/content/converter/out/akbar_arabic_rock_lora_ar.safetensors}"
LORA_NAR="${LORA_NAR:-/content/converter/out/akbar_arabic_rock_lora_nar.safetensors}"

run() { # echo unless --dry-run
  echo "  $*"
  [ "$DRY" = "--dry-run" ] || "$@"
}

preflight() {
  [ "$DRY" = "--dry-run" ] && return 0
  command -v nvidia-smi >/dev/null || { echo "no nvidia-smi; needs the Colab GPU runtime" >&2; exit 1; }
  if pgrep -af 'run.py' | grep -q akbar_arabic_rock_lora; then
    echo "an ai-toolkit training run is active — refusing (AGENTS.md §8)" >&2; exit 1
  fi
  for f in "$BIN" "$MODEL" "$LORA_AR" "$LORA_NAR" "$STYLE" "$LYRICS"; do
    [ -e "$f" ] || { echo "missing: $f" >&2; exit 1; }
  done
  mkdir -p "$OUT_DIR"
}

cap_for() { # $1 = lyrics file -> cap (auto) or $CAP
  if [ -n "${CAP:-}" ]; then echo "$CAP"; else python3 "$SCRIPT_DIR/duration_cap.py" "$1"; fi
}

# --- B. knob arms (cot=off, via run_one.sh so sidecars/status are written) ----
# Baselines (no knobs) are the win_as-is / ctl_sunoblk_as-is arms in batch.json —
# same track/seed/adapter/lyrics, so b*_* vs those isolates the knob.
_knob_one() { # $1 slug  $2 style  $3 "k=v k=v"
  local cap; cap="$(cap_for "$LYRICS")"
  run env EXTRA_REQUEST_OPTS="$3" STYLE_FILE="$2" LYRICS_FILE="$LYRICS" OUT_DIR="$OUT_DIR" \
      bash "$SCRIPT_DIR/run_one.sh" "$1" "$SEED" "$cap"
}
knobs() {
  [ -e "$RAW_STYLE" ] || { echo "missing: $RAW_STYLE" >&2; exit 1; }
  echo "== B. knob arms (cot=off) seed=$SEED out=$OUT_DIR"
  local b1="semantic_penalty_window=500 semantic_repetition_penalty=1.3"
  local b2="guidance_scale=1.3"
  _knob_one b1_window      "$STYLE"     "$b1"
  _knob_one b2_guidance    "$STYLE"     "$b2"
  _knob_one b3_both        "$STYLE"     "$b1 $b2"
  _knob_one b1raw_window   "$RAW_STYLE" "$b1"
  _knob_one b2raw_guidance "$RAW_STYLE" "$b2"
  _knob_one b3raw_both     "$RAW_STYLE" "$b1 $b2"
}

# --- C. ABC arms (cot=melody [+ abc_file]); direct binary call ---------------
_abc_one() { # $1 slug  $2 style  $3 "abc:<path>"|"noabc"
  local slug="$1" style="$2" mode="$3" cap wav log
  cap="$(cap_for "$LYRICS")"
  wav="$OUT_DIR/${slug}_${SEED}.wav"; log="$OUT_DIR/${slug}_${SEED}.log"
  local abc_opts=()
  [ "$mode" != "noabc" ] && abc_opts=(--request-option "abc_file=${mode#abc:}")
  echo "== C. $slug (cot=melody, $mode) seed=$SEED cap=$cap -> $wav"
  if [ "$DRY" = "--dry-run" ]; then
    echo "  $BIN ... --request-option cot=melody ${abc_opts[*]} --seed $SEED --out $wav"; return 0
  fi
  "$BIN" --task gen --family yue2 --model "$MODEL" --backend cuda --threads 8 \
    --session-option yue2.model_gguf=yue2-3b-bf16.gguf \
    --session-option yue2.vae_gguf=yue2-vae-f16.gguf \
    --session-option yue2.ar_lora="$LORA_AR" --session-option yue2.ar_lora_scale=1.0 \
    --session-option yue2.nar_lora="$LORA_NAR" --session-option yue2.nar_lora_scale=1.0 \
    --session-option yue2.attention=flash \
    --lyrics "$(cat "$LYRICS")" \
    --request-option style="$(cat "$style")" \
    --request-option cot=melody \
    "${abc_opts[@]}" \
    --request-option semantic_max_tokens="$cap" \
    --seed "$SEED" --out "$wav" --log > "$log" 2>&1
  echo "   exit=$? (log: $log)"
}

abc() {
  [ -e "$RAW_STYLE" ] || { echo "missing: $RAW_STYLE" >&2; exit 1; }
  if [ -z "$ABC_FILE" ] && [ "$DRY" != "--dry-run" ]; then
    echo "[warn] ABC_FILE unset — running only the cot=melody-no-abc control arms." >&2
    echo "       set ABC_FILE=<melody.abc> (see docs/music-cover-feasibility.md §4.2)." >&2
  fi
  echo "== C. ABC arms (cot=melody) seed=$SEED out=$OUT_DIR"
  _abc_one c0_cotonly    "$STYLE"     noabc
  _abc_one c0raw_cotonly "$RAW_STYLE" noabc
  [ -n "$ABC_FILE" ] && _abc_one c1_abc_win "$STYLE"     "abc:$ABC_FILE"
  [ -n "$ABC_FILE" ] && _abc_one c2_abc_mod "$MOD_STYLE" "abc:$ABC_FILE"
  [ -n "$ABC_FILE" ] && _abc_one c3_abc_raw "$RAW_STYLE" "abc:$ABC_FILE"
}

echo "test_batch.sh mode=$MODE seed=$SEED${DRY:+ ($DRY)}"
echo "style=$STYLE"
echo "lyrics=$LYRICS${ABC_FILE:+  abc=$ABC_FILE}"
preflight
[ "$MODE" = "knobs" -o "$MODE" = "all" ] && knobs
[ "$MODE" = "abc"   -o "$MODE" = "all" ] && abc
echo "done. outputs: $OUT_DIR"
echo "backup:  python3 $REPO_DIR/backup_to_gcp.py --inference --once"
