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
#     driver calls the binary DIRECTLY with `cot=<per-take cot>` + `abc_file=`, so
#     there is no duplicate option to resolve.
#
# Alignment guarantees (the point of the file):
#   * one key everywhere: <name>_<seed>  (pass-1 WAV stem == ABC folder). The
#     rescue stem is the same <name>_<seed> UNLESS a seed override is set: then the
#     guide stays keyed to <name>_<pass1seed> (recorded as abc_source_stem) and the
#     output is <name>_<newseed> — so the ABC->take pairing is explicit, not implied.
#   * refuses to write into the pass-1 dir, or anywhere under it  -> cannot clobber
#     the liked take (run_one.sh would name the rescue <name>_<seed>.wav, identical)
#   * cap/style/lyrics come from the pass-1 batch_manifest.json + the flattened
#     prompts/  -> nothing is retyped; the seed is the pass-1 take's own unless a
#     seed override is given (defaults.seed / per-song seed: an int, or "random"
#     for a FRESH seed per take — re-rolls the performance, the guide is unchanged)
#   * _rescue_index.json records sha256 of every pass-1 WAV and its ABC, so the
#     pairing is proven, not assumed (use --verify to re-check before a batch)
#
# Selection: --songs / --songs-file / --songs-json accept song NAMES and/or full
#   STEMS (<name>_<seed>). A name selects every take of that song; a stem selects
#   one. --songs-json mirrors a generate.py manifest: an optional "loras" alias
#   registry + a "defaults" block + a "songs" list, plus the three rescue dirs
#   (pass1_dir/abc_dir/out_dir). A song entry may override "lora"/"cot"/"seed".
#   Because a rescue reuses each pass-1 take's own lyrics/style/cap (G6), the ONLY
#   new input per take is its ABC guide (abc_dir/<stem>/score.abc) + an optional
#   new seed -> entries are SELECTORS, not full song specs. Example:
#   INFERENCE/rescue_selection.example.json.
#
# Env overrides:
#   ROOT BIN MODEL THREADS   workspace / runner / model dir / cpu threads
#   QF_AR QF_NAR             env-fallback adapter pair (used when no lora alias)
#   RESCUE_COT               default request cot (default: melody)
#   RESCUE_ADAPTER           fallback sidecar label (default qfinal_a0.3)
#   GCS_BASE                 for the qfinal stage hint
set -u

usage() {
  cat <<'EOF'
usage: rescue_abc_batch.sh [--pass1-dir DIR --abc-dir DIR --out-dir DIR]
                           [--songs NAME|STEM,... | --songs-file FILE
                            | --songs-json FILE]
                           [--smoke] [--limit N] [--threads N]
                           [--plan] [--verify] [--force] [--skip-preflight]

  --pass1-dir  a generate.py --out-dir (needs batch_manifest.json + prompts/)
  --abc-dir    sheetsage2_transcribe.py --out-dir (<stem>/score.abc per take)
  --out-dir    rescue output dir; MUST differ from --pass1-dir and not sit under it
               (the three dirs are required: give them here or via --songs-json)
  --songs      comma/space/newline list of song NAMES and/or STEMS to rescue
  --songs-file one selector per line ('#' comments and blank lines ignored)
  --songs-json a JSON run config: "loras" (alias registry) + "defaults" +
               "songs" (selectors; each may override lora/cot/seed) + pass1_dir/
               abc_dir/out_dir. Precedence: per-song > env (cot) > defaults >
               built-in; the adapter pair: per-song/defaults alias > env pair;
               the three dirs: CLI flag > file. "seed" (in defaults or per song)
               is an integer in [0,2^32) or "random" (a FRESH seed per take;
               the ABC/pass-1 stay keyed to the original stem). Example:
               INFERENCE/rescue_selection.example.json
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
GCS_BASE="${GCS_BASE:-gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning}"
# Built-in fallbacks. They are applied only after the JSON "defaults" block, so
# the precedence is: per-song field > env/CLI (cot/adapter/threads) > "defaults" >
# these built-ins; the adapter pair is per-song/defaults alias > env pair (matching
# generate.py, where an alias wins over the --lora-ar/--lora-nar pair).
DEF_THREADS=8
DEF_QF_AR=/content/converter/out/qfinal_a0.3/akbar_arabic_rock_lora_ar.safetensors
DEF_QF_NAR=/content/converter/out/qfinal_a0.3/akbar_arabic_rock_lora_nar.safetensors
DEF_COT=melody
DEF_ADAPTER=qfinal_a0.3
# Detect an explicit env value BEFORE defaulting, so a JSON "defaults" only fills
# a gap that an env var / CLI flag left.
ENV_THREADS=0; [ -n "${THREADS+x}" ] && ENV_THREADS=1
ENV_COT=0;     [ -n "${RESCUE_COT+x}" ] && ENV_COT=1
ENV_ADAPTER=0; [ -n "${RESCUE_ADAPTER+x}" ] && ENV_ADAPTER=1
CLI_THREADS=0

# /usr/bin/time is preferable (run_one.sh uses it; the bootstrap installs it) but
# is not required — if absent we still write a `<stem>_time.txt` for resume.
TIME_BIN=""; [ -x /usr/bin/time ] && TIME_BIN=/usr/bin/time

PASS1="" ABC_DIR="" OUT_DIR="" SONGS="" SONGS_FILE="" SONGS_JSON=""
MODE=run   # run | plan | verify
FORCE=0 SMOKE=0 LIMIT=0 SKIP_PREFLIGHT=0

while [ $# -gt 0 ]; do
  case "$1" in
    --pass1-dir)  PASS1="${2:-}"; shift 2;;
    --abc-dir)    ABC_DIR="${2:-}"; shift 2;;
    --out-dir)    OUT_DIR="${2:-}"; shift 2;;
    --songs)      SONGS="${2:-}"; shift 2;;
    --songs-file) SONGS_FILE="${2:-}"; shift 2;;
    --songs-json) SONGS_JSON="${2:-}"; shift 2;;
    --limit)      LIMIT="${2:-0}"; shift 2;;
    --threads)    THREADS="${2:-}"; CLI_THREADS=1; shift 2;;
    --plan)       MODE=plan; shift;;
    --verify)     MODE=verify; shift;;
    --smoke)      SMOKE=1; shift;;
    --force)      FORCE=1; shift;;
    --skip-preflight) SKIP_PREFLIGHT=1; shift;;
    -h|--help)    usage;;
    *) echo "unknown arg: $1" >&2; usage;;
  esac
done
_nsel=0
[ -n "$SONGS" ] && _nsel=$((_nsel + 1))
[ -n "$SONGS_FILE" ] && _nsel=$((_nsel + 1))
[ -n "$SONGS_JSON" ] && _nsel=$((_nsel + 1))
[ "$_nsel" -le 1 ] || { echo "use only one of --songs / --songs-file / --songs-json" >&2; exit 2; }
case "$LIMIT" in ''|*[!0-9]*) echo "--limit must be an integer" >&2; exit 2;; esac
if [ -n "${THREADS:-}" ]; then
  case "$THREADS" in ''|*[!0-9]*) echo "--threads must be an integer" >&2; exit 2;; esac
fi

# Portable realpath (works for not-yet-existing paths too).
rp() { python3 -c 'import os,sys;print(os.path.realpath(sys.argv[1]))' "$1"; }

if [ -n "$SONGS_FILE" ]; then
  [ -f "$SONGS_FILE" ] || { echo "no such --songs-file: $SONGS_FILE" >&2; exit 2; }
  # strip # comments + CR, one selector per line -> comma list
  SONGS="$(sed -e 's/#.*//' -e 's/\r$//' "$SONGS_FILE" | tr '\n' ',')"
fi
# The normalized config (loras registry + defaults + songs) is written here and
# read again by the index builder; the shell only needs a few run-level values.
RESOLVED_JSON="$(mktemp)"
trap '[ -n "${RESOLVED_JSON:-}" ] && rm -f "$RESOLVED_JSON"' EXIT
if [ -n "$SONGS_JSON" ]; then
  [ -f "$SONGS_JSON" ] || { echo "no such --songs-json: $SONGS_JSON" >&2; exit 2; }
  python3 - "$SONGS_JSON" > "$RESOLVED_JSON" <<'PY' || exit 2
import json, os, re, sys
path = sys.argv[1]
try:
    doc = json.load(open(path, encoding="utf-8"))
except (OSError, ValueError) as e:
    sys.exit(f"[error] --songs-json not readable/valid JSON: {path}: {e}")
if not isinstance(doc, dict):
    sys.exit(f"[error] --songs-json must be a JSON object: {path}")
base = os.path.dirname(os.path.abspath(path))
ALIAS = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
TOP = {"pass1_dir", "abc_dir", "out_dir", "loras", "defaults", "songs"}
for k in doc:
    if k not in TOP and not k.startswith("_"):
        print(f"[warn] ignoring unknown --songs-json key: {k}", file=sys.stderr)

def need_str(obj, key, where):
    v = obj.get(key)
    if not isinstance(v, str) or not v.strip():
        sys.exit(f"[error] --songs-json {where}.{key} must be a non-empty string")
    return v.strip()

def need_seed(v, where):
    # a fresh per-take random seed, or a pinned integer in [0, 2**32)
    if v == "random":
        return "random"
    if isinstance(v, bool) or not isinstance(v, int) or not (0 <= v < 2**32):
        sys.exit(f'[error] --songs-json {where}.seed must be an integer in [0,2**32) or "random"')
    return v

out = {"loras": {}, "defaults": {}, "songs": []}
for key in ("pass1_dir", "abc_dir", "out_dir"):
    if key in doc:
        out[key] = need_str(doc, key, "top-level")

# 'loras' alias registry -- same shape/semantics as generate.py resolve_loras.
loras_raw = doc.get("loras", {})
if not isinstance(loras_raw, dict):
    sys.exit("[error] --songs-json 'loras' must be an object")
for alias, spec in loras_raw.items():
    if not isinstance(alias, str) or not ALIAS.match(alias):
        sys.exit(f"[error] --songs-json loras alias invalid: {alias!r}")
    if not isinstance(spec, dict):
        sys.exit(f"[error] --songs-json loras[{alias!r}] must be an object")
    has_dir, has_pair = "dir" in spec, ("ar" in spec or "nar" in spec)
    if has_dir == has_pair:
        sys.exit(f"[error] --songs-json loras[{alias!r}]: use 'dir' xor both 'ar'+'nar'")
    if has_dir:
        d = need_str(spec, "dir", f"loras[{alias!r}]")
        d = d if os.path.isabs(d) else os.path.join(base, d)
        ar = os.path.join(d, "akbar_arabic_rock_lora_ar.safetensors")
        nar = os.path.join(d, "akbar_arabic_rock_lora_nar.safetensors")
    else:
        if "ar" not in spec or "nar" not in spec:
            sys.exit(f"[error] --songs-json loras[{alias!r}]: 'ar' and 'nar' both required")
        ar = need_str(spec, "ar", f"loras[{alias!r}]")
        nar = need_str(spec, "nar", f"loras[{alias!r}]")
        ar = ar if os.path.isabs(ar) else os.path.join(base, ar)
        nar = nar if os.path.isabs(nar) else os.path.join(base, nar)
    out["loras"][alias] = {"ar": ar, "nar": nar}

dft = doc.get("defaults", {})
if not isinstance(dft, dict):
    sys.exit("[error] --songs-json 'defaults' must be an object")
for k in dft:
    if k not in {"lora", "cot", "adapter", "threads", "limit", "seed"}:
        sys.exit(f"[error] --songs-json unknown defaults key: {k}")
for k in ("lora", "cot", "adapter"):
    if k in dft:
        out["defaults"][k] = need_str(dft, k, "defaults")
if "seed" in dft:
    out["defaults"]["seed"] = need_seed(dft["seed"], "defaults")
for k in ("threads", "limit"):
    if k in dft:
        v = dft[k]
        if not isinstance(v, int) or isinstance(v, bool) or v < 0:
            sys.exit(f"[error] --songs-json defaults.{k} must be a non-negative integer")
        out["defaults"][k] = v

songs = doc.get("songs")
if songs is not None:
    if not isinstance(songs, list):
        sys.exit(f"[error] --songs-json 'songs' must be a list: {path}")
    for e in songs:
        if isinstance(e, str):
            sel, ovr = e, {}
        elif isinstance(e, dict):
            sel = e.get("stem") or e.get("name")
            if not sel:
                sys.exit(f"[error] --songs-json entry needs 'stem' or 'name': {e!r}")
            ovr = {k: need_str(e, k, "song") for k in ("lora", "cot") if k in e}
            if "seed" in e:
                ovr["seed"] = need_seed(e["seed"], "song")
        else:
            sys.exit(f"[error] --songs-json entry must be a string or object: {e!r}")
        sel = sel.strip()
        if not sel:
            continue
        item = {"sel": sel}
        item.update(ovr)
        out["songs"].append(item)
    if not out["songs"]:
        sys.exit("no selectors in --songs-json 'songs'; omit the key to rescue every track")

for a in [out["defaults"].get("lora")] + [s.get("lora") for s in out["songs"]]:
    if a and a not in out["loras"]:
        known = ", ".join(sorted(out["loras"])) or "none"
        sys.exit(f"[error] --songs-json: lora alias '{a}' not in 'loras' (known: {known})")

json.dump(out, sys.stdout, ensure_ascii=False)
PY
  _jget() { python3 -c 'import json,sys
d=json.load(open(sys.argv[1]))
c=d
for p in sys.argv[2].split("."):
    c=c.get(p) if isinstance(c,dict) else None
print("" if c is None else c)' "$RESOLVED_JSON" "$1"; }
  [ -n "$PASS1" ]   || PASS1="$(_jget pass1_dir)"
  [ -n "$ABC_DIR" ] || ABC_DIR="$(_jget abc_dir)"
  [ -n "$OUT_DIR" ] || OUT_DIR="$(_jget out_dir)"
  if [ -z "$SONGS" ]; then
    SONGS="$(python3 -c 'import json,sys; print(",".join(s["sel"] for s in json.load(open(sys.argv[1]))["songs"]))' "$RESOLVED_JSON")"
  fi
else
  printf '{ "loras": {}, "defaults": {}, "songs": [] }\n' > "$RESOLVED_JSON"
fi

# --- apply JSON "defaults" where env/CLI left a gap; then built-in fallbacks ---
_jdef() { python3 -c 'import json,sys
d=json.load(open(sys.argv[1])).get("defaults",{})
v=d.get(sys.argv[2]); print("" if v is None else v)' "$RESOLVED_JSON" "$1"; }
if [ "$ENV_THREADS" -eq 0 ] && [ "$CLI_THREADS" -eq 0 ]; then
  _v="$(_jdef threads)"; [ -n "$_v" ] && THREADS="$_v"
fi
[ -n "${THREADS:-}" ] || THREADS="$DEF_THREADS"
if [ "$LIMIT" -eq 0 ]; then _v="$(_jdef limit)"; [ -n "$_v" ] && LIMIT="$_v"; fi
if [ "$ENV_ADAPTER" -eq 0 ]; then
  _v="$(_jdef adapter)"; [ -n "$_v" ] && RESCUE_ADAPTER="$_v"
fi
[ -n "${RESCUE_ADAPTER:-}" ] || RESCUE_ADAPTER="$DEF_ADAPTER"
if [ "$ENV_COT" -eq 0 ]; then
  _v="$(_jdef cot)"; [ -n "$_v" ] && RESCUE_COT="$_v"
fi
[ -n "${RESCUE_COT:-}" ] || RESCUE_COT="$DEF_COT"
# env-only fallback pair (a per-song/defaults alias wins over this, per generate.py)
ENV_QF_AR="${QF_AR:-$DEF_QF_AR}"
ENV_QF_NAR="${QF_NAR:-$DEF_QF_NAR}"

# pass1/abc/out may come from the CLI or from --songs-json; both absent -> usage.
[ -n "$PASS1" ] && [ -n "$ABC_DIR" ] && [ -n "$OUT_DIR" ] || {
  echo "missing --pass1-dir/--abc-dir/--out-dir (give on the CLI or in --songs-json)" >&2
  usage
}
# An explicit-but-empty selector list must NOT silently mean "rescue everything".
if [ -n "$SONGS" ] && [ -z "$(printf '%s' "$SONGS" | tr -d ',[:space:]')" ]; then
  echo "no selectors in --songs/--songs-file/--songs-json; omit them to rescue every track" >&2; exit 2
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
    if want and t.get("name") not in want and t.get("stem") not in want and t.get("src_stem") not in want: continue
    seen.add(t.get("name")); seen.add(t.get("stem")); seen.add(t.get("src_stem")); n += 1
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
trap 'rm -f "$PLAN_TSV" "${RESOLVED_JSON:-}"' EXIT

python3 - "$PASS1" "$ABC_DIR" "$SONGS" "$INDEX" "$RESOLVED_JSON" \
         "$ENV_QF_AR" "$ENV_QF_NAR" "$RESCUE_COT" "$RESCUE_ADAPTER" \
         <<'PY' > "$PLAN_TSV" || { echo "[error] index build failed" >&2; exit 3; }
import hashlib, json, random, re, sys
from pathlib import Path
(pass1, abc_dir, songs_arg, index_path, resolved_json,
 fb_ar, fb_nar, fb_cot, fb_adapter) = sys.argv[1:10]
pass1, abc_dir = Path(pass1), Path(abc_dir)
want = {s for s in re.split(r"[,\s]+", songs_arg) if s}
cfg = json.loads(Path(resolved_json).read_text(encoding="utf-8"))
loras, defaults = cfg.get("loras", {}), cfg.get("defaults", {})
ov_by = {}
for s in cfg.get("songs", []):
    ov_by.setdefault(s["sel"], {k: s.get(k) for k in ("lora", "cot", "seed")})

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

# Reuse seeds drawn by a previous run in this out-dir, so "random" is drawn ONCE:
# a resume / re-plan must not re-roll (it would re-render and never converge).
prev = {}
try:
    _old = json.loads(Path(index_path).read_text(encoding="utf-8"))
    prev = {t.get("src_stem"): t for t in _old.get("tracks", []) if t.get("src_stem")}
except (OSError, ValueError):
    prev = {}

rows, problems, seen, used_out = [], [], set(), set()
for t in tracks:
    name, seed = t.get("name"), t.get("seed")
    if name is None or seed is None:
        problems.append(f"manifest track missing name/seed: {t!r}"); rows.append(None); continue
    src_stem = f"{name}_{seed}"
    if want and name not in want and src_stem not in want:
        continue
    seen.add(name); seen.add(src_stem)
    cap = t.get("cap")
    style_rel, lyrics_rel = t.get("style_file") or "", t.get("lyrics_file") or ""
    style = pass1 / style_rel if style_rel else None
    lyrics = pass1 / lyrics_rel if lyrics_rel else None
    wav = pass1 / f"{src_stem}.wav"
    abc = abc_dir / src_stem / "score.abc"
    bad = []
    if cap is None:                    bad.append("manifest has no cap")
    if not wav.is_file():              bad.append(f"missing pass-1 wav: {wav}")
    if not abc.is_file() or abc.stat().st_size == 0: bad.append(f"missing/empty abc: {abc}")
    if style is None or not style.is_file():   bad.append(f"missing style: {style}")
    if lyrics is None or not lyrics.is_file(): bad.append(f"missing lyrics: {lyrics}")
    if bad:
        problems += [f"{src_stem}: {b}" for b in bad]; rows.append(None); continue
    # adapter + cot: per-song field > defaults alias > env pair (adapter) /
    # env cot > defaults cot (cot) -- env values are already folded into fb_*.
    ov = ov_by.get(name) or ov_by.get(src_stem) or {}
    alias = ov.get("lora") or defaults.get("lora")
    if alias:
        ar, nar = loras[alias]["ar"], loras[alias]["nar"]
        label = alias
    else:
        ar, nar = fb_ar, fb_nar
        label = fb_adapter
    # Output seed: per-song 'seed' > defaults 'seed' > the pass-1 take's own seed.
    # "random" draws a FRESH seed per take. The guide (abc) and the pass-1 wav stay
    # keyed to src_stem, so the ABC is provably that take's, while the render gets a
    # new seed -> out_stem = <name>_<out_seed> (the sidecar records abc_source_stem).
    # A drawn seed is REUSED from this dir's existing index so a resume/re-plan does
    # not re-draw; delete _rescue_index.json to force a fresh draw.
    seed_ov = ov.get("seed")
    if seed_ov is None:
        seed_ov = defaults.get("seed")
    if seed_ov is None:
        seed_mode, out_seed = "pass1", seed
    elif seed_ov == "random":
        seed_mode = "random"
        prev_t = prev.get(src_stem) or {}
        out_seed = prev_t.get("seed") if prev_t.get("seed_mode") == "random" else None
        if not isinstance(out_seed, int):
            out_seed = None
            for _ in range(1000):
                cand = random.randrange(2**32)
                if f"{name}_{cand}" not in used_out:
                    out_seed = cand; break
            if out_seed is None:
                problems.append(f"{src_stem}: could not draw a unique random seed")
                rows.append(None); continue
    else:
        seed_mode, out_seed = "pinned", int(seed_ov)
    out_stem = f"{name}_{out_seed}"
    if out_stem in used_out:
        problems.append(f"{src_stem}: output stem {out_stem} already used (duplicate seed)")
        rows.append(None); continue
    used_out.add(out_stem)
    rows.append({
        "idx": t.get("idx"), "name": name, "take": t.get("take", 0), "seed": out_seed,
        "seed_mode": seed_mode, "cap": cap, "stem": out_stem,
        "src_stem": src_stem, "abc_source_stem": src_stem,
        "cot": ov.get("cot") or fb_cot,
        "ar": ar, "nar": nar, "adapter": label,
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
                     r["lyrics_file"], r["abc"], r["stem"], r["cot"], r["ar"],
                     r["nar"], r["adapter"], r["src_stem"]]))
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
  for f in "$BIN" "$MODEL"; do
    [ -e "$f" ] || { echo "missing: $f" >&2; exit 1; }
  done
  # Every adapter pair the plan actually references must be staged (per-take
  # aliases included), so a rescue can never start on a half-staged registry.
  missing_ad=0
  while IFS=$'\t' read -r _n _s _c _st _ly _ab _stem _co ar nar _ad _src; do
    [ -n "$ar" ] || continue
    for f in "$ar" "$nar"; do
      [ -e "$f" ] || { echo "missing adapter: $f" >&2; missing_ad=1; }
    done
  done < <(printf '%s\n' "${PLAN[@]}")
  if [ "$missing_ad" -eq 1 ]; then
    echo "  stage the alias dir(s): gsutil -m cp -r $GCS_BASE/loras/audio_cpp/pron/<alias> /content/converter/out/" >&2
    exit 1
  fi
fi

render() {  # <name> <stem> <seed> <cap> <style> <lyrics> <abc> <cot> <ar> <nar> <adapter> <src_stem>
  local name="$1" stem="$2" seed="$3" cap="$4" style="$5" lyrics="$6" abc="$7"
  local cot="$8" ar="$9" nar="${10}" adapter="${11}" src_stem="${12:-$2}"
  local wav="$OUT_DIR/${stem}.wav" log="$OUT_DIR/${stem}.log" tf="$OUT_DIR/${stem}_time.txt"
  if [ "$FORCE" -eq 0 ] && [ -s "$wav" ] && grep -q "Exit status: 0" "$tf" 2>/dev/null; then
    echo "== skip $stem (rescue already succeeded; --force to redo)"; return 0
  fi
  echo "== $stem seed=$seed cot=$cot adapter=$adapter cap=$cap abc=$abc -> $wav"
  echo "=== START rescue $stem seed=$seed $(date -u +%FT%TZ) ===" >> "$OUT_DIR/_rescue_status.log"
  local -a cmd=("$BIN" --task gen --family yue2 --model "$MODEL" --backend cuda --threads "$THREADS" \
    --session-option yue2.model_gguf=yue2-3b-bf16.gguf \
    --session-option yue2.vae_gguf=yue2-vae-f16.gguf \
    --session-option yue2.ar_lora="$ar" --session-option yue2.ar_lora_scale=1.0 \
    --session-option yue2.nar_lora="$nar" --session-option yue2.nar_lora_scale=1.0 \
    --session-option yue2.attention=flash \
    --lyrics "$(cat "$lyrics")" \
    --request-option style="$(cat "$style")" \
    --request-option cot="$cot" \
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
  python3 - "$name" "$stem" "$seed" "$cap" "$abc" "$style" "$lyrics" "$wav" "$rc" "$cot" "$adapter" "$src_stem" <<'PY'
import hashlib, json, sys
from datetime import datetime, timezone
from pathlib import Path
name, stem, seed, cap, abc, style, lyrics, wav, rc, cot, adapter, src_stem = sys.argv[1:13]
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
    "cot": cot, "adapter": adapter, "abc_source_stem": src_stem,
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
  IFS=$'\t' read -r name seed cap style lyrics abc stem cot ar nar adapter src_stem <<<"$line"
  if render "$name" "$stem" "$seed" "$cap" "$style" "$lyrics" "$abc" "$cot" "$ar" "$nar" "$adapter" "$src_stem"; then ok=$((ok + 1)); else fail=$((fail + 1)); fi
  n=$((n + 1))
  if [ "$SMOKE" -eq 1 ]; then
    echo "[smoke] rendered 1 track ($stem). Listen to it, then re-run without --smoke."; break
  fi
done

echo "done: $n processed -> $OUT_DIR (ok=$ok fail=$fail)"
echo "next: listen (pass-1 vs rescue, same seed); package with INFERENCE/prepare_ab_eval.py (skill ab-blind-eval)."
[ "$fail" -eq 0 ] || exit 1
