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
#     driver calls the binary DIRECTLY with `cot=melody` + `abc_file=`, so there
#     is no duplicate option to resolve.
#
# Alignment guarantees (the point of the file):
#   * one key everywhere: <name>_<seed>  (pass-1 WAV stem == ABC folder == rescue stem)
#   * refuses to write into the pass-1 dir   -> cannot clobber the liked take
#     (run_one.sh would name the rescue <name>_<seed>.wav, identical to pass-1)
#   * seed/cap/style/lyrics come from the pass-1 batch_manifest.json + the
#     flattened prompts/  -> nothing is retyped, the ONLY variable is the guide
#   * _rescue_index.json records sha256 of every pass-1 WAV and its ABC, so the
#     pairing is proven, not assumed (use --verify to re-check before a batch)
#
# Usage:
#   bash INFERENCE/rescue_abc_batch.sh \
#       --pass1-dir /content/audiocpp_inference/out/batch_12_rock_v2 \
#       --abc-dir   /content/audiocpp_inference/out/abc_v2_batch12 \
#       --out-dir   /content/audiocpp_inference/out/rescue_v2abc_batch12 \
#       [--songs name1,name2 | --songs-file list.txt] [--smoke] [--plan] [--force] [--verify]
#
#   --plan    resolve + validate the index and print the plan; no GPU, writes nothing
#   --smoke   render only the FIRST planned track, then stop (the B2 quality smoke)
#   --force   re-render tracks whose rescue already succeeded
#   --verify  re-check index sha256 against disk, then exit (no render)
#
# Env overrides:
#   QF_AR QF_NAR   qfinal_a0.3 adapters (default: /content/converter/out/qfinal_a0.3/...)
#   GCS_BASE       for the stage hint
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT=/content/audiocpp_inference
BIN="$ROOT/bin/audiocpp_cli"
MODEL="$ROOT/models/Yue2-3B-GGUF"
QF_AR="${QF_AR:-/content/converter/out/qfinal_a0.3/akbar_arabic_rock_lora_ar.safetensors}"
QF_NAR="${QF_NAR:-/content/converter/out/qfinal_a0.3/akbar_arabic_rock_lora_nar.safetensors}"
GCS_BASE="${GCS_BASE:-gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning}"

PASS1="" ABC_DIR="" OUT_DIR="" SONGS="" SONGS_FILE=""
MODE=run   # run | plan | verify
FORCE=0 SMOKE=0

usage() { sed -n '2,40p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 2; }

while [ $# -gt 0 ]; do
  case "$1" in
    --pass1-dir)  PASS1="${2:-}"; shift 2;;
    --abc-dir)    ABC_DIR="${2:-}"; shift 2;;
    --out-dir)    OUT_DIR="${2:-}"; shift 2;;
    --songs)      SONGS="${2:-}"; shift 2;;
    --songs-file) SONGS_FILE="${2:-}"; shift 2;;
    --plan)       MODE=plan; shift;;
    --verify)     MODE=verify; shift;;
    --smoke)      SMOKE=1; shift;;
    --force)      FORCE=1; shift;;
    -h|--help)    usage;;
    *) echo "unknown arg: $1" >&2; usage;;
  esac
done
[ -n "$PASS1" ] && [ -n "$ABC_DIR" ] && [ -n "$OUT_DIR" ] || usage

if [ -n "$SONGS_FILE" ]; then
  [ -n "$SONGS" ] && { echo "use --songs xor --songs-file" >&2; exit 2; }
  SONGS="$(paste -sd, < "$SONGS_FILE")"
fi

# --- gate 1: never write into the pass-1 dir (would clobber the liked take) ----
rp_pass1="$(realpath -m "$PASS1")"
rp_out="$(realpath -m "$OUT_DIR")"
if [ "$rp_out" = "$rp_pass1" ]; then
  echo "[refuse] --out-dir == --pass1-dir ($rp_out); that would overwrite pass-1 takes" >&2
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
import hashlib, json, sys
index, songs_arg = sys.argv[1], sys.argv[2]
want = {s.strip() for s in songs_arg.split(",") if s.strip()}
d = json.load(open(index, encoding="utf-8"))
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()
bad, n, seen = 0, 0, set()
for t in d["tracks"]:
    if want and t["name"] not in want: continue
    seen.add(t["name"]); n += 1
    for key, p in (("pass1_wav_sha256", t["pass1_wav"]), ("abc_sha256", t["abc"])):
        try:
            if sha(p) != t[key]:
                print(f"MISMATCH {t['name']}: {p} changed since index"); bad += 1
        except OSError:
            print(f"MISSING  {t['name']}: {p}"); bad += 1
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
import hashlib, json, sys
from pathlib import Path
pass1, abc_dir, songs_arg, index_path = sys.argv[1:5]
pass1, abc_dir = Path(pass1), Path(abc_dir)
want = {s.strip() for s in songs_arg.split(",") if s.strip()}

man_path = pass1 / "batch_manifest.json"
if not man_path.is_file():
    sys.exit(f"[error] no batch_manifest.json under {pass1} (is this a generate.py --out-dir?)")
man = json.loads(man_path.read_text(encoding="utf-8"))

def sha(p: Path):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

rows, problems, seen = [], [], set()
for t in man.get("tracks", []):
    name, seed = t["name"], t["seed"]
    if want and name not in want:
        continue
    seen.add(name)
    stem = f"{name}_{seed}"
    wav = pass1 / f"{stem}.wav"
    abc = abc_dir / stem / "score.abc"
    style = pass1 / t.get("style_file", "")
    lyrics = pass1 / t.get("lyrics_file", "")
    bad = []
    if not wav.is_file():            bad.append(f"missing pass-1 wav: {wav}")
    if not abc.is_file() or abc.stat().st_size == 0: bad.append(f"missing/empty abc: {abc}")
    if not style.is_file():          bad.append(f"missing style: {style}")
    if not lyrics.is_file():         bad.append(f"missing lyrics: {lyrics}")
    if bad:
        problems += [f"{name}: {b}" for b in bad]
        rows.append(None)
        continue
    rows.append({
        "idx": t.get("idx"), "name": name, "take": t.get("take", 0), "seed": seed,
        "cap": t["cap"], "maqam_lyrics": None,
        "stem": stem,
        "pass1_wav": str(wav), "pass1_wav_sha256": sha(wav),
        "abc": str(abc), "abc_sha256": sha(abc),
        "style_file": str(style), "lyrics_file": str(lyrics),
    })

missing = want - seen
if missing:
    problems += [f"requested song not in manifest: {m}" for m in sorted(missing)]
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
suffix=""; [ "$SMOKE" -eq 1 ] && suffix=", smoke"
echo "n     : ${#PLAN[@]}  (${MODE}${suffix})"
printf '  %s\n' "$(for l in "${PLAN[@]}"; do IFS=$'\t' read -r n s c _ _ _ _ <<<"$l"; printf '%s(%s) ' "$n" "$s"; done)"

[ "$MODE" = "plan" ] && { echo "[plan] OK — nothing written, no GPU."; exit 0; }

# --- render preflight ---------------------------------------------------------
command -v nvidia-smi >/dev/null || { echo "no nvidia-smi; needs the Colab GPU runtime" >&2; exit 1; }
if pgrep -af 'run[.]py' | grep -q 'akbar_arabic_rock_lor[a]'; then
  echo "an ai-toolkit training run is active — refusing (AGENTS.md §8)" >&2; exit 1
fi
for f in "$BIN" "$MODEL" "$QF_AR" "$QF_NAR"; do
  [ -e "$f" ] || { echo "missing: $f" >&2
    echo "  stage qfinal: gsutil -m cp -r $GCS_BASE/loras/audio_cpp/pron/qfinal_a0.3 /content/converter/out/" >&2
    exit 1; }
done

render() {  # <stem> <seed> <cap> <style> <lyrics> <abc>
  local stem="$1" seed="$2" cap="$3" style="$4" lyrics="$5" abc="$6"
  local wav="$OUT_DIR/${stem}.wav" log="$OUT_DIR/${stem}.log" tf="$OUT_DIR/${stem}_time.txt"
  if [ "$FORCE" -eq 0 ] && [ -s "$wav" ] && grep -q "Exit status: 0" "$tf" 2>/dev/null; then
    echo "== skip $stem (rescue already succeeded; --force to redo)"; return 0
  fi
  echo "== $stem seed=$seed cap=$cap abc=$abc -> $wav"
  echo "=== START rescue $stem seed=$seed $(date -u +%FT%TZ) ===" >> "$OUT_DIR/_rescue_status.log"
  /usr/bin/time -v -o "$tf" \
    "$BIN" --task gen --family yue2 --model "$MODEL" --backend cuda --threads 8 \
    --session-option yue2.model_gguf=yue2-3b-bf16.gguf \
    --session-option yue2.vae_gguf=yue2-vae-f16.gguf \
    --session-option yue2.ar_lora="$QF_AR" --session-option yue2.ar_lora_scale=1.0 \
    --session-option yue2.nar_lora="$QF_NAR" --session-option yue2.nar_lora_scale=1.0 \
    --session-option yue2.attention=flash \
    --lyrics "$(cat "$lyrics")" \
    --request-option style="$(cat "$style")" \
    --request-option cot=melody \
    --request-option abc_file="$abc" \
    --request-option semantic_max_tokens="$cap" \
    --seed "$seed" \
    --out "$wav" --log > "$log" 2>&1
  local rc=$?
  echo "=== END rescue $stem exit=$rc $(date -u +%FT%TZ) ===" >> "$OUT_DIR/_rescue_status.log"
  # sidecar: bind rescue WAV to the guide it used + the pass-1 take it derives from
  python3 - "$stem" "$seed" "$cap" "$abc" "$style" "$lyrics" "$wav" "$rc" <<'PY'
import hashlib, json, sys
from datetime import datetime, timezone
from pathlib import Path
stem, seed, cap, abc, style, lyrics, wav, rc = sys.argv[1:9]
def sha(p):
    p = Path(p)
    if not p.is_file(): return None
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()
side = Path(wav).with_suffix("").as_posix() + "_rescue.json"
json.dump({
    "name": stem.rsplit("_", 1)[0], "seed": int(seed), "cap": int(cap),
    "cot": "melody", "abc_file": abc, "abc_sha256": sha(abc),
    "style_sha256": sha(style), "lyrics_sha256": sha(lyrics),
    "wav_sha256": sha(wav), "exit": int(rc),
    "adapter": "qfinal_a0.3",
    "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
}, open(side, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
PY
  echo "   exit=$rc  wav=$( [ -s "$wav" ] && echo yes || echo NO )"
}

n=0
for line in "${PLAN[@]}"; do
  IFS=$'\t' read -r name seed cap style lyrics abc stem <<<"$line"
  render "$stem" "$seed" "$cap" "$style" "$lyrics" "$abc"
  n=$((n + 1))
  if [ "$SMOKE" -eq 1 ]; then
    echo "[smoke] rendered 1 track ($stem). Listen to it, then re-run without --smoke."
    break
  fi
done

echo "done: $n rendered -> $OUT_DIR"
echo "next: listen (pass-1 vs rescue, same seed); package with INFERENCE/prepare_ab_eval.py (skill ab-blind-eval)."
