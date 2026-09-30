#!/usr/bin/env bash
# Guarded B2 rescue: render qfinal_a0.3 conditioned on each v2 take's OWN
# SheetSage2 melody ABC (docs/PRON_LORA_RESCUE.md; docs/music-cover-feasibility.md
# §2.1/§10). Pass-1 stays cot=off (in-distribution v2); this adds the guide only
# where pronunciation failed.
#
# Why a separate driver (not generate.py / run_one.sh):
#   * generate.py has no cot/abc field (SONG_KEYS has none; its sidecar hardcodes
#     cot:"off") — it cannot carry a guide.
#   * run_one.sh hardcodes `--request-option cot=off` (run_one.sh:85) and relies
#     on a later EXTRA_REQUEST_OPTS cot=... to override it — UNVERIFIED. This
#     driver calls the binary DIRECTLY with `cot=<RESCUE_COT>` + `abc_file=`, so
#     there is no duplicate option to resolve.
#
# Alignment guarantees (the point of the file):
#   * one key everywhere: <name>_<seed>  (pass-1 WAV stem == ABC folder == rescue stem)
#   * refuses to write into the pass-1 dir, or anywhere under it  -> cannot clobber
#     the liked take (run_one.sh would name the rescue <name>_<seed>.wav, identical)
#   * seed/cap/style/lyrics come from the pass-1 batch_manifest.json + the
#     flattened prompts/  -> nothing is retyped, the ONLY variable is the guide
#   * _rescue_index.json records sha256 of every pass-1 WAV and its ABC, so the
#     pairing is proven, not assumed (use --verify to re-check before a batch)
#
# Selection: --songs / --songs-file accept song NAMES and/or full STEMS
#   (<name>_<seed>). A name selects every take of that song; a stem selects one.
#
# Env overrides:
#   ROOT BIN MODEL THREADS   workspace / runner / model dir / cpu threads
#   QF_AR QF_NAR             qfinal adapters (default: the qfinal_a0.3 pair)
#   RESCUE_COT               request cot (default: melody)
#   RESCUE_ADAPTER           label written to the sidecar (default qfinal_a0.3)
#   GCS_BASE                 for the qfinal stage hint
set -u

usage() {
  cat <<'EOF'
usage: rescue_abc_batch.sh --pass1-dir DIR --abc-dir DIR --out-dir DIR
                           [--songs NAME|STEM,... | --songs-file FILE]
                           [--smoke] [--limit N] [--threads N]
                           [--plan] [--verify] [--force] [--skip-preflight]

  --pass1-dir  a generate.py --out-dir (needs batch_manifest.json + prompts/)
  --abc-dir    sheetsage2_transcribe.py --out-dir (<stem>/score.abc per take)
  --out-dir    rescue output dir; MUST differ from --pass1-dir and not sit under it
  --songs      comma/space/newline list of song NAMES and/or STEMS to rescue
  --songs-file one selector per line ('#' comments and blank lines ignored)
  --plan       validate + write the index, print the plan; no GPU, no render
  --verify     re-check the stored index sha256 against disk, then exit (no render)
  --smoke      render ONLY the first planned track, then stop (the B2 quality gate)
  --limit N    render at most N planned tracks
  --threads N  cpu threads passed to the binary (default 8; env THREADS)
  --force      re-render tracks whose rescue already succeeded
  --skip-preflight  skip the nvidia-smi/training/adapter checks (tests/off-box)
EOF
  exit 2
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${ROOT:-/content/audiocpp_inference}"
BIN="${BIN:-$ROOT/bin/audiocpp_cli}"
MODEL="${MODEL:-$ROOT/models/Yue2-3B-GGUF}"
THREADS="${THREADS:-8}"
QF_AR="${QF_AR:-/content/converter/out/qfinal_a0.3/akbar_arabic_rock_lora_ar.safetensors}"
QF_NAR="${QF_NAR:-/content/converter/out/qfinal_a0.3/akbar_arabic_rock_lora_nar.safetensors}"
RESCUE_COT="${RESCUE_COT:-melody}"
RESCUE_ADAPTER="${RESCUE_ADAPTER:-qfinal_a0.3}"
GCS_BASE="${GCS_BASE:-gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning}"

# /usr/bin/time is preferable (run_one.sh uses it; the bootstrap installs it) but
# is not required — if absent we still write a `<stem>_time.txt` for resume.
TIME_BIN=""; [ -x /usr/bin/time ] && TIME_BIN=/usr/bin/time

PASS1="" ABC_DIR="" OUT_DIR="" SONGS="" SONGS_FILE=""
MODE=run   # run | plan | verify
FORCE=0 SMOKE=0 LIMIT=0 SKIP_PREFLIGHT=0

while [ $# -gt 0 ]; do
  case "$1" in
    --pass1-dir)  PASS1="${2:-}"; shift 2;;
    --abc-dir)    ABC_DIR="${2:-}"; shift 2;;
    --out-dir)    OUT_DIR="${2:-}"; shift 2;;
    --songs)      SONGS="${2:-}"; shift 2;;
    --songs-file) SONGS_FILE="${2:-}"; shift 2;;
    --limit)      LIMIT="${2:-0}"; shift 2;;
    --threads)    THREADS="${2:-}"; shift 2;;
    --plan)       MODE=plan; shift;;
    --verify)     MODE=verify; shift;;
    --smoke)      SMOKE=1; shift;;
    --force)      FORCE=1; shift;;
    --skip-preflight) SKIP_PREFLIGHT=1; shift;;
    -h|--help)    usage;;
    *) echo "unknown arg: $1" >&2; usage;;
  esac
done
[ -n "$PASS1" ] && [ -n "$ABC_DIR" ] && [ -n "$OUT_DIR" ] || usage
[ -n "$SONGS_FILE" ] && [ -n "$SONGS" ] && { echo "use --songs xor --songs-file" >&2; exit 2; }
case "$LIMIT" in ''|*[!0-9]*) echo "--limit must be an integer" >&2; exit 2;; esac

# Portable realpath (works for not-yet-existing paths too).
rp() { python3 -c 'import os,sys;print(os.path.realpath(sys.argv[1]))' "$1"; }

if [ -n "$SONGS_FILE" ]; then
  [ -f "$SONGS_FILE" ] || { echo "no such --songs-file: $SONGS_FILE" >&2; exit 2; }
  # strip # comments + CR, one selector per line -> comma list
  SONGS="$(sed -e 's/#.*//' -e 's/\r$//' "$SONGS_FILE" | tr '\n' ',')"
fi
# An explicit-but-empty selector list must NOT silently mean "rescue everything".
if [ -n "$SONGS" ] && [ -z "$(printf '%s' "$SONGS" | tr -d ',[:space:]')" ]; then
  echo "no selectors in --songs/--songs-file; omit them to rescue every track" >&2; exit 2
fi

# --- gate 1: never write into (or under) the pass-1 dir ------------------------
rp_pass1="$(rp "$PASS1")"
rp_out="$(rp "$OUT_DIR")"
rp_abc="$(rp "$ABC_DIR")"
if [ "$rp_out" = "$rp_pass1" ]; then
  echo "[refuse] --out-dir == --pass1-dir ($rp_out); that would overwrite pass-1 takes" >&2
  exit 2
fi
case "$rp_out/" in
  "$rp_pass1/"*) echo "[refuse] --out-dir ($rp_out) is under --pass1-dir; rescue WAVs would be re-transcribed (G2)" >&2; exit 2;;
esac
if [ "$rp_out" = "$rp_abc" ]; then
  echo "[refuse] --out-dir == --abc-dir ($rp_out)" >&2
  exit 2
fi
if [ -f "$OUT_DIR/batch_manifest.json" ] || [ -f "$OUT_DIR/input.json" ]; then
  echo "[refuse] --out-dir ($OUT_DIR) looks like a generate.py run dir; refusing" >&2
  exit 2
fi

# --- plan / index (python: JSON + sha256); also the second gate ----------------
mkdir -p "$OUT_DIR"
INDEX="$OUT_DIR/_rescue_index.json"

# --verify re-checks the STORED index against disk. It must NOT rebuild it.
if [ "$MODE" = "verify" ]; then
  [ -f "$INDEX" ] || { echo "[error] no index at $INDEX — build it with --plan first" >&2; exit 3; }
  python3 - "$INDEX" "$SONGS" <<'PY'
import hashlib, json, re, sys
index, songs_arg = sys.argv[1], sys.argv[2]
want = {s for s in re.split(r"[,\s]+", songs_arg) if s}
d = json.load(open(index, encoding="utf-8"))
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()
bad, n, seen = 0, 0, set()
for t in d["tracks"]:
    if want and t.get("name") not in want and t.get("stem") not in want: continue
    seen.add(t.get("name")); seen.add(t.get("stem")); n += 1
    for key, p in (("pass1_wav_sha256", t["pass1_wav"]), ("abc_sha256", t["abc"])):
        try:
            if sha(p) != t[key]:
                print(f"MISMATCH {t['stem']}: {p} changed since index"); bad += 1
        except OSError:
            print(f"MISSING  {t['stem']}: {p}"); bad += 1
for m in sorted(want - seen):
    print(f"NOT IN INDEX: {m}"); bad += 1
print(f"verify: {'OK' if not bad else str(bad) + ' problem(s)'}  (n={n})")
sys.exit(1 if bad else 0)
PY
  exit $?
fi

PLAN_TSV="$(mktemp)"
trap 'rm -f "$PLAN_TSV"' EXIT

python3 - "$PASS1" "$ABC_DIR" "$SONGS" "$INDEX" <<'PY' > "$PLAN_TSV" || { echo "[error] index build failed" >&2; exit 3; }
import hashlib, json, re, sys
from pathlib import Path
pass1, abc_dir, songs_arg, index_path = sys.argv[1:5]
pass1, abc_dir = Path(pass1), Path(abc_dir)
want = {s for s in re.split(r"[,\s]+", songs_arg) if s}

def sha(p: Path):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()

man_path = pass1 / "batch_manifest.json"
if not man_path.is_file():
    sys.exit(f"[error] no batch_manifest.json under {pass1} (is this a generate.py --out-dir?)")
man = json.loads(man_path.read_text(encoding="utf-8"))
tracks = man.get("tracks") or []
if not tracks:
    sys.exit(f"[error] batch_manifest.json has no tracks: {man_path}")

rows, problems, seen = [], [], set()
for t in tracks:
    name, seed = t.get("name"), t.get("seed")
    if name is None or seed is None:
        problems.append(f"manifest track missing name/seed: {t!r}"); rows.append(None); continue
    stem = f"{name}_{seed}"
    if want and name not in want and stem not in want:
        continue
    seen.add(name); seen.add(stem)
    cap = t.get("cap")
    style_rel, lyrics_rel = t.get("style_file") or "", t.get("lyrics_file") or ""
    style = pass1 / style_rel if style_rel else None
    lyrics = pass1 / lyrics_rel if lyrics_rel else None
    wav = pass1 / f"{stem}.wav"
    abc = abc_dir / stem / "score.abc"
    bad = []
    if cap is None:                    bad.append("manifest has no cap")
    if not wav.is_file():              bad.append(f"missing pass-1 wav: {wav}")
    if not abc.is_file() or abc.stat().st_size == 0: bad.append(f"missing/empty abc: {abc}")
    if style is None or not style.is_file():   bad.append(f"missing style: {style}")
    if lyrics is None or not lyrics.is_file(): bad.append(f"missing lyrics: {lyrics}")
    if bad:
        problems += [f"{stem}: {b}" for b in bad]; rows.append(None); continue
    rows.append({
        "idx": t.get("idx"), "name": name, "take": t.get("take", 0), "seed": seed, "cap": cap,
        "stem": stem,
        "pass1_wav": str(wav), "pass1_wav_sha256": sha(wav),
        "abc": str(abc), "abc_sha256": sha(abc),
        "style_file": str(style), "lyrics_file": str(lyrics),
    })

missing = want - seen
if missing:
    problems += [f"requested selector not in manifest: {m}" for m in sorted(missing)]
if problems:
    print("[gate] would not run:", file=sys.stderr)
    for p in problems:
        print("  - " + p, file=sys.stderr)
    sys.exit(3)

rows = [r for r in rows if r]
json.dump({"tool": "rescue_abc_batch", "pass1_dir": str(pass1), "abc_dir": str(abc_dir),
           "n": len(rows), "tracks": rows}, open(index_path, "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
for r in rows:
    print("\t".join([r["name"], str(r["seed"]), str(r["cap"]), r["style_file"],
                     r["lyrics_file"], r["abc"], r["stem"]]))
PY
mapfile -t PLAN < "$PLAN_TSV"

echo "pass1 : $PASS1"
echo "abc   : $ABC_DIR"
echo "out   : $OUT_DIR"
echo "index : $INDEX"
suffix=""; [ "$SMOKE" -eq 1 ] && suffix=", smoke"; [ "$LIMIT" -gt 0 ] && suffix="$suffix, limit=$LIMIT"
echo "n     : ${#PLAN[@]}  (${MODE}${suffix})"
printf '  %s\n' "$(for l in "${PLAN[@]}"; do IFS=$'\t' read -r n s c _ _ _ _ <<<"$l"; printf '%s(%s) ' "$n" "$s"; done)"

[ "$MODE" = "plan" ] && { echo "[plan] OK — index written, no render/GPU."; exit 0; }

# --- render preflight ---------------------------------------------------------
if [ "$SKIP_PREFLIGHT" -eq 0 ]; then
  command -v nvidia-smi >/dev/null || {
    echo "no nvidia-smi; needs the Colab GPU runtime (or --skip-preflight for tests/off-box)" >&2; exit 1; }
  if pgrep -af 'run[.]py' | grep -q 'akbar_arabic_rock_lor[a]'; then
    echo "an ai-toolkit training run is active — refusing (AGENTS.md §8)" >&2; exit 1
  fi
  for f in "$BIN" "$MODEL" "$QF_AR" "$QF_NAR"; do
    [ -e "$f" ] || { echo "missing: $f" >&2
      echo "  stage qfinal: gsutil -m cp -r $GCS_BASE/loras/audio_cpp/pron/qfinal_a0.3 /content/converter/out/" >&2
      exit 1; }
  done
fi

render() {  # <name> <stem> <seed> <cap> <style> <lyrics> <abc>
  local name="$1" stem="$2" seed="$3" cap="$4" style="$5" lyrics="$6" abc="$7"
  local wav="$OUT_DIR/${stem}.wav" log="$OUT_DIR/${stem}.log" tf="$OUT_DIR/${stem}_time.txt"
  if [ "$FORCE" -eq 0 ] && [ -s "$wav" ] && grep -q "Exit status: 0" "$tf" 2>/dev/null; then
    echo "== skip $stem (rescue already succeeded; --force to redo)"; return 0
  fi
  echo "== $stem seed=$seed cap=$cap abc=$abc -> $wav"
  echo "=== START rescue $stem seed=$seed $(date -u +%FT%TZ) ===" >> "$OUT_DIR/_rescue_status.log"
  local -a cmd=("$BIN" --task gen --family yue2 --model "$MODEL" --backend cuda --threads "$THREADS" \
    --session-option yue2.model_gguf=yue2-3b-bf16.gguf \
    --session-option yue2.vae_gguf=yue2-vae-f16.gguf \
    --session-option yue2.ar_lora="$QF_AR" --session-option yue2.ar_lora_scale=1.0 \
    --session-option yue2.nar_lora="$QF_NAR" --session-option yue2.nar_lora_scale=1.0 \
    --session-option yue2.attention=flash \
    --lyrics "$(cat "$lyrics")" \
    --request-option style="$(cat "$style")" \
    --request-option cot="$RESCUE_COT" \
    --request-option abc_file="$abc" \
    --request-option semantic_max_tokens="$cap" \
    --seed "$seed" \
    --out "$wav" --log)
  local rc=0
  if [ -n "$TIME_BIN" ]; then
    "$TIME_BIN" -v -o "$tf" "${cmd[@]}" > "$log" 2>&1 || rc=$?
  else
    "${cmd[@]}" > "$log" 2>&1 || rc=$?
    printf 'Exit status: %d\n' "$rc" > "$tf"
  fi
  echo "=== END rescue $stem exit=$rc $(date -u +%FT%TZ) ===" >> "$OUT_DIR/_rescue_status.log"
  [ -s "$wav" ] || rc=1   # a "success" that produced no audio is a failure
  # sidecar: bind the rescue WAV to the guide it used + the pass-1 take it derives from
  python3 - "$name" "$stem" "$seed" "$cap" "$abc" "$style" "$lyrics" "$wav" "$rc" "$RESCUE_COT" "$RESCUE_ADAPTER" <<'PY'
import hashlib, json, sys
from datetime import datetime, timezone
from pathlib import Path
name, stem, seed, cap, abc, style, lyrics, wav, rc, cot, adapter = sys.argv[1:12]
def sha(p):
    p = Path(p)
    if not p.is_file(): return None
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()
side = Path(wav).with_suffix("").as_posix() + "_rescue.json"
json.dump({
    "name": name, "stem": stem, "seed": int(seed), "cap": int(cap),
    "cot": cot, "adapter": adapter,
    "abc_file": abc, "abc_sha256": sha(abc),
    "style_sha256": sha(style), "lyrics_sha256": sha(lyrics),
    "wav_sha256": sha(wav), "exit": int(rc),
    "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
}, open(side, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
PY
  echo "   exit=$rc  wav=$( [ -s "$wav" ] && echo yes || echo NO )"
  return "$rc"
}

n=0 ok=0 fail=0
for line in "${PLAN[@]}"; do
  if [ "$LIMIT" -gt 0 ] && [ "$n" -ge "$LIMIT" ]; then break; fi
  IFS=$'\t' read -r name seed cap style lyrics abc stem <<<"$line"
  if render "$name" "$stem" "$seed" "$cap" "$style" "$lyrics" "$abc"; then ok=$((ok + 1)); else fail=$((fail + 1)); fi
  n=$((n + 1))
  if [ "$SMOKE" -eq 1 ]; then
    echo "[smoke] rendered 1 track ($stem). Listen to it, then re-run without --smoke."; break
  fi
done

echo "done: $n processed -> $OUT_DIR (ok=$ok fail=$fail)"
echo "next: listen (pass-1 vs rescue, same seed); package with INFERENCE/prepare_ab_eval.py (skill ab-blind-eval)."
[ "$fail" -eq 0 ] || exit 1
