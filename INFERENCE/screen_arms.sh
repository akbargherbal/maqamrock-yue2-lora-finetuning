#!/usr/bin/env bash
# Screen the lyric-adherence arms WITHOUT the NAR renderer.
#
# Companion to manifests/test_verbatim_hijaz/batch.json + INFERENCE/test_batch.sh.
# Those two always render audio (~6.5 min/track on a T4). This driver runs the
# SAME arms with `stop_after=semantic`, which stops after the AR semantic stage
# and writes, per arm, under --out-dir:
#     score.abc        (cot=melody arms only; the ABC plan)
#     semantic.json    flat JSON array of codec indices, 25 frames/s
# and NO audio. Cheap pre-filter: rank arms by planned length before paying for
# the NAR render.
#
# LIMIT (read before trusting a verdict): semantic.json is acoustic *codec*
# indices, not text. It carries no lyric<->frame alignment, so it cannot say
# WHICH line was sung. What it does give, objectively:
#   * planned length (frames/25 s) and whether it hit semantic_max_tokens
#     (`truncated`) — an injected section repeat lengthens the plan;
#   * per-arm, same seed, so arms are comparable.
# The actual "did it sing the sheet verbatim" verdict still needs the rendered
# audio (listening, or ASR of the output vs the sheet). See
# docs/music-cover-feasibility.md §4.3/§8.
#
# Usage: bash INFERENCE/screen_arms.sh <core|abc|all> [--dry-run]
#
# Env overrides:
#   SEED       default 4148240095 (the guide render's seed)
#   OUT_DIR    default /content/audiocpp_inference/out/screen_semantic
#   CAP        default auto (INFERENCE/duration_cap.py, 95th pct)
#   ABC_FILE   melody.abc for the c1/c2/c3 arms; default the v2 Hijaz guide ABC
#   LORA_AR / LORA_NAR   default the live converted v2 pair
#   STYLE / MOD_STYLE / RAW_STYLE / LYRICS / DEDUP_LYRICS / BARE_LYRICS
#              default to manifests/test_verbatim_hijaz/*
#
# FOREGROUND, sequential (never parallel: two runs can OOM the graph). For a
# long set run it detached with a log, e.g.
#   setsid nohup bash INFERENCE/screen_arms.sh all > /content/logs/tv_screen.log 2>&1 & disown
#   tail -f /content/logs/tv_screen.log        # watch
#   pkill -f 'screen_arms.sh all'              # stop (foreground: Ctrl+C)
set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ROOT=/content/audiocpp_inference
BIN="$ROOT/bin/audiocpp_cli"
MODEL="$ROOT/models/Yue2-3B-GGUF"
M_DIR="$REPO_DIR/manifests/test_verbatim_hijaz"

MODE="${1:-}"; DRY="${2:-}"
case "$MODE" in core|abc|all) ;; *) echo "usage: $0 <core|abc|all> [--dry-run]" >&2; exit 2;; esac

SEED="${SEED:-4148240095}"
STYLE="${STYLE:-$M_DIR/styles/hijaz_winning.txt}"
MOD_STYLE="${MOD_STYLE:-$M_DIR/styles/hijaz_modified.txt}"
RAW_STYLE="${RAW_STYLE:-$M_DIR/styles/hijaz_sunoblk.txt}"
LYRICS="${LYRICS:-$M_DIR/lyrics/01_nesib_as-is.txt}"
DEDUP_LYRICS="${DEDUP_LYRICS:-$M_DIR/lyrics/01_nesib_dedup.txt}"
BARE_LYRICS="${BARE_LYRICS:-$M_DIR/lyrics/01_nesib_bare.txt}"
OUT_DIR="${OUT_DIR:-$ROOT/out/screen_semantic}"
LORA_AR="${LORA_AR:-/content/converter/out/akbar_arabic_rock_lora_ar.safetensors}"
LORA_NAR="${LORA_NAR:-/content/converter/out/akbar_arabic_rock_lora_nar.safetensors}"
ABC_FILE="${ABC_FILE:-$ROOT/out/abc_v2/01-نسيب-وظعن-الحي-ونخيل-يامن-وعرائس-النعمة_4148240095/score.abc}"

preflight() {
  [ "$DRY" = "--dry-run" ] && return 0
  command -v nvidia-smi >/dev/null || { echo "no nvidia-smi; needs the Colab GPU runtime" >&2; exit 1; }
  # Bracket the dots: a plain 'run.py' / run-name literal makes pgrep match this
  # very shell's own command line and refuse every run.
  if pgrep -af 'run[.]py' | grep -q 'akbar_arabic_rock_lor[a]'; then
    echo "an ai-toolkit training run is active — refusing (AGENTS.md §8)" >&2; exit 1
  fi
  for f in "$BIN" "$MODEL" "$LORA_AR" "$LORA_NAR" "$STYLE" "$MOD_STYLE" "$RAW_STYLE" \
           "$LYRICS" "$DEDUP_LYRICS" "$BARE_LYRICS"; do
    [ -e "$f" ] || { echo "missing: $f" >&2; exit 1; }
  done
  mkdir -p "$OUT_DIR"
}

cap_for() { # $1 = lyrics file -> cap (auto) or $CAP
  if [ -n "${CAP:-}" ]; then echo "$CAP"; else python3 "$SCRIPT_DIR/duration_cap.py" "$1"; fi
}

# _screen_one <slug> <style> <lyrics> <cot> <extra k=v...>
# One arm, semantic only: no --out, --out-dir collects the artifacts.
_screen_one() {
  local slug="$1" style="$2" lyrics_f="$3" cot="$4"; shift 4
  local cap tdir log rc opts=()
  cap="$(cap_for "$lyrics_f")"
  tdir="$OUT_DIR/${slug}_${SEED}"
  log="$OUT_DIR/${slug}_${SEED}.log"
  for kv in "$@"; do opts+=(--request-option "$kv"); done
  echo "== $slug (cot=$cot) seed=$SEED cap=$cap ${*:+[${*}]} -> $tdir"
  if [ "$DRY" = "--dry-run" ]; then
    echo "  $BIN ... --request-option cot=$cot ${opts[*]} --request-option stop_after=semantic --out-dir $tdir"
    return 0
  fi
  mkdir -p "$tdir"
  local line="=== START screen $slug seed=$SEED cap=$cap cot=$cot $(date -u +%FT%TZ) ==="
  echo "$line" >> "$OUT_DIR/_runs_status.log"
  /usr/bin/time -v -o "$OUT_DIR/${slug}_${SEED}_time.txt" \
    "$BIN" --task gen --family yue2 --model "$MODEL" --backend cuda --threads 8 \
    --session-option yue2.model_gguf=yue2-3b-bf16.gguf \
    --session-option yue2.vae_gguf=yue2-vae-f16.gguf \
    --session-option yue2.ar_lora="$LORA_AR" --session-option yue2.ar_lora_scale=1.0 \
    --session-option yue2.nar_lora="$LORA_NAR" --session-option yue2.nar_lora_scale=1.0 \
    --session-option yue2.attention=flash \
    --lyrics "$(cat "$lyrics_f")" \
    --request-option style="$(cat "$style")" \
    --request-option cot="$cot" \
    "${opts[@]}" \
    --request-option semantic_max_tokens="$cap" \
    --request-option stop_after=semantic \
    --seed "$SEED" \
    --out-dir "$tdir" \
    --log > "$log" 2>&1
  rc=$?
  echo "=== END screen $slug exit=$rc $(date -u +%FT%TZ) ===" >> "$OUT_DIR/_runs_status.log"
  printf '   exit=%s  semantic.json=%s (%s B)  score.abc=%s\n' "$rc" \
    "$([ -s "$tdir/semantic.json" ] && echo yes || echo NO)" \
    "$(stat -c%s "$tdir/semantic.json" 2>/dev/null || echo 0)" \
    "$([ -s "$tdir/score.abc" ] && echo yes || echo -)"
}

_B1="semantic_penalty_window=500 semantic_repetition_penalty=1.3"
_B2="guidance_scale=1.3"

# core: the minimum-sufficient arms (current.md table rows 0, A, B1, B2, D)
core() {
  _screen_one ctl_sunoblk_as-is "$RAW_STYLE" "$LYRICS"       off
  _screen_one win_as-is         "$STYLE"     "$LYRICS"       off
  _screen_one mod_as-is         "$MOD_STYLE" "$LYRICS"       off
  _screen_one b1_window         "$STYLE"     "$LYRICS"       off $_B1
  _screen_one b2_guidance       "$STYLE"     "$LYRICS"       off $_B2
  _screen_one b3_both           "$STYLE"     "$LYRICS"       off $_B1 $_B2
  _screen_one win_dedup         "$STYLE"     "$DEDUP_LYRICS" off
  _screen_one win_bare          "$STYLE"     "$BARE_LYRICS"  off
  _screen_one b1raw_window      "$RAW_STYLE" "$LYRICS"       off $_B1
  _screen_one b2raw_guidance    "$RAW_STYLE" "$LYRICS"       off $_B2
  _screen_one b3raw_both        "$RAW_STYLE" "$LYRICS"       off $_B1 $_B2
}

# abc: cot=melody controls + the abc_file arms (needs ABC_FILE)
abc() {
  if [ ! -e "$ABC_FILE" ] && [ "$DRY" != "--dry-run" ]; then
    echo "[warn] ABC_FILE not found at $ABC_FILE — running only the cot=melody-no-abc controls." >&2
  fi
  _screen_one c0_cotonly    "$STYLE"     "$LYRICS" melody
  _screen_one c0raw_cotonly "$RAW_STYLE" "$LYRICS" melody
  if [ -e "$ABC_FILE" ] || [ "$DRY" = "--dry-run" ]; then
    _screen_one c1_abc_win "$STYLE"     "$LYRICS" melody "abc_file=$ABC_FILE"
    _screen_one c2_abc_mod "$MOD_STYLE" "$LYRICS" melody "abc_file=$ABC_FILE"
    _screen_one c3_abc_raw "$RAW_STYLE" "$LYRICS" melody "abc_file=$ABC_FILE"
  fi
}

echo "screen_arms.sh mode=$MODE seed=$SEED${DRY:+ ($DRY)}"
echo "out=$OUT_DIR${ABC_FILE:+  abc=$ABC_FILE}"
preflight
[ "$MODE" = "core" -o "$MODE" = "all" ] && core
[ "$MODE" = "abc"  -o "$MODE" = "all" ] && abc
echo "done. outputs: $OUT_DIR"
if [ "$DRY" != "--dry-run" ]; then
  echo "--- summary:"
  python3 "$SCRIPT_DIR/screen_summary.py" "$OUT_DIR" || true
fi
