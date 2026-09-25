#!/usr/bin/env bash
# Request-option knob probe: pron checkpoint FIXED at 3050, alpha FIXED at 0.5,
# held-out maqams Hijaz + Kurd only. Every config uses the SAME anchor adapters
# (the Task 17/18/19 c3050_a0.5 merge); exactly ONE request-option is changed per
# config, via run_one.sh's new EXTRA_REQUEST_OPTS hook. 4 configs x 2 maqams = 8
# tracks, strictly sequential.
#
# The comparison anchor is the existing c3050_a0.5 tracks from the fine sweep
# (identical seed 20260924, identical auto cap, identical staged prompts, same
# binary) -- they are NOT regenerated here, so only the 4 knob labels are
# rendered. Same inputs as pron_fine_sweep.sh; only the request knob varies.
#
# MAQAM-MAJOR order (all 4 knobs of a maqam before moving on), matching Task 17
# and pron_fine_sweep.
#
# Resumable: a track whose WAV exists AND whose _time.txt says "Exit status: 0"
# is skipped. Failures append to $PROBE/_failed.log and do not stop the run.
# Every track also gets a full JSON sidecar (schema follows pron_ckpt_sweep.py /
# generate.py): seed, command, prompt/adapter/binary/GGUF hashes, the single knob
# under test, GPU/attention, cap, truncation, wall time and the WAV sha256.
#
# Usage: bash INFERENCE/pron_knob_probe.sh
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_ONE="$SCRIPT_DIR/run_one.sh"
PROBE=/content/pron_knob_probe
CONV=/content/converter/out
ANCHOR_CFG=c3050_a0.5
AR="$CONV/$ANCHOR_CFG/akbar_arabic_rock_lora_ar.safetensors"
NAR="$CONV/$ANCHOR_CFG/akbar_arabic_rock_lora_nar.safetensors"
SEED=20260924
MAQAMS="Hijaz Kurd"
CFGS="g1.0 g1.5 t0.8 rp1.4"
FAILED="$PROBE/_failed.log"

export SCRIPT_DIR SEED ANCHOR_CFG AR NAR

# config -> the single EXTRA_REQUEST_OPTS key=value under test.
opts_for() {
  case "$1" in
    g1.0)  printf '%s' 'guidance_scale=1.0' ;;
    g1.5)  printf '%s' 'guidance_scale=1.5' ;;
    t0.8)  printf '%s' 'semantic_temperature=0.8' ;;
    rp1.4) printf '%s' 'semantic_repetition_penalty=1.4' ;;
    *) echo "pron_knob_probe: unknown config '$1'" >&2; return 1 ;;
  esac
}

mkdir -p "$PROBE"
touch "$FAILED"

# Preflight: the anchor adapters are shared by every config. Fail loudly here,
# not silently mid-batch, if the c3050_a0.5 merge was not staged.
for f in "$AR" "$NAR"; do
  if [ ! -f "$f" ]; then
    echo "pron_knob_probe: missing anchor adapter: $f" >&2
    echo "  stage it from gs://<base>/audiocpp_inference/maqam_lyric_swap/converted/$ANCHOR_CFG/" >&2
    exit 2
  fi
done

GPU_NAME="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1 | sed 's/ *$//')"
COMPUTE_CAP="$(nvidia-smi --query-gpu=compute_cap --format=csv,noheader 2>/dev/null | head -1 | sed 's/ *$//')"
export GPU_NAME COMPUTE_CAP

# Full sidecar writer, called with the run status as $1 ("started" before
# generation, "ok"/"failed" after). Inputs come from the exported env so the
# same function serves both writes. Reuses generate.py's tested hashing /
# duration / truncation helpers, so the schema matches the prior sweeps.
emit_sidecar() {
  STATUS="$1" python3 - <<'PY'
import json
import os
import sys
import wave
from pathlib import Path

sys.path.insert(0, os.environ["SCRIPT_DIR"])
import generate as G

d = os.environ
wav = Path(d["OUT"]) / f'{d["M"]}_{d["SEED"]}.wav'
cap = int(d["CAP"])
dur = G.wav_duration(wav)
trunc, trunc_src = G.truncation_info(wav.with_suffix(".log"), dur, cap)
frames = None
if wav.is_file():
    try:
        with wave.open(str(wav), "rb") as w:
            frames = w.getnframes()
    except Exception:
        pass


def _parse_time_txt(p):
    out = {}
    if p.is_file():
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            m = re.match(r"\s*(.+?):\s+(.+)$", line)
            if m:
                out[m.group(1).strip()] = m.group(2).strip()
    return out


def _gpu_stats(p):
    """Peak/mean of run_one.sh's 1 Hz per-track nvidia-smi CSV."""
    cols = [[], [], [], []]
    if p.is_file():
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            parts = [x.strip() for x in line.split(",")]
            if len(parts) != 4:
                continue
            try:
                for i, v in enumerate(parts):
                    cols[i].append(float(v))
            except ValueError:
                pass
    if not cols[1]:
        return None
    return {
        "peak_util_pct": max(cols[0]),
        "peak_vram_mib": max(cols[1]),
        "mean_vram_mib": round(sum(cols[1]) / len(cols[1]), 1),
        "peak_power_w": max(cols[2]),
        "peak_temp_c": max(cols[3]),
        "gpu_samples": len(cols[1]),
    }


bin_path = Path("/content/audiocpp_inference/bin/audiocpp_cli")
fields = {
    "config": d["CFG"],
    "anchor_config": d["ANCHOR_CFG"],
    "pron_checkpoint": 3050,
    "alpha": 0.5,
    "knob": d["EXTRA"],
    "extra_request_opts": d["EXTRA"],
    "maqam": d["M"],
    "seed": int(d["SEED"]),
    "cap": cap,
    "cap_mode": "auto",
    "command": d["CMD_STR"],
    "run_one": f'INFERENCE/run_one.sh {d["M"]} {d["SEED"]} {cap}',
    "style_file": d["STYLE"],
    "style_sha256": G.sha256_file(Path(d["STYLE"])),
    "lyrics_file": d["LYRICS"],
    "lyrics_sha256": G.sha256_file(Path(d["LYRICS"])),
    "lora_ar_path": d["AR"],
    "lora_ar_sha256": G.sha256_file(Path(d["AR"])),
    "lora_nar_path": d["NAR"],
    "lora_nar_sha256": G.sha256_file(Path(d["NAR"])),
    "binary_path": str(bin_path),
    "binary_sha256": G.sha256_file(bin_path),
    "model_gguf": G.MODEL_GGUF,
    "model_gguf_sha256": G.sha256_file(G.MODEL_DIR / G.MODEL_GGUF),
    "vae_gguf": G.VAE_GGUF,
    "vae_gguf_sha256": G.sha256_file(G.MODEL_DIR / G.VAE_GGUF),
    "attention": "flash",
    "cot": "off",
    "checkpoint_step": 3050,
    "audio_cpp_commit": G.git_commit(G.AUDIO_CPP),
    "gpu": d.get("GPU_NAME", ""),
    "compute_cap": d.get("COMPUTE_CAP", ""),
    "status": d["STATUS"],
    "start_utc": d["START_UTC"],
}
if d["STATUS"] != "started":
    ttxt = _parse_time_txt(Path(d["OUT"]) / f'{d["M"]}_{d["SEED"]}_time.txt')
    try:
        rss_kib = int(ttxt.get("Maximum resident set size (kbytes)", "").strip()) or None
    except ValueError:
        rss_kib = None
    fields.update({
        "exit": int(d["EXIT_CODE"]),
        "end_utc": d["END_UTC"],
        "wall_s": float(d["WALL_S"]),
        "wav_sha256": G.sha256_file(wav) if wav.is_file() else None,
        "wav_duration_s": round(dur, 2) if dur is not None else None,
        "wav_frames": frames,
        "truncated": trunc,
        "truncated_source": trunc_src,
        "resources": {
            "elapsed_s": ttxt.get("Elapsed (wall clock) time (h:mm:ss or m:ss)"),
            "max_rss_kib": rss_kib,
            "max_rss_gib": round(rss_kib / 1024 ** 2, 2) if rss_kib else None,
            "cpu_pct": ttxt.get("Percent of CPU this job got"),
            "user_s": ttxt.get("User time (seconds)"),
            "sys_s": ttxt.get("System time (seconds)"),
            "gpu": _gpu_stats(Path(d["OUT"]) / f'{d["M"]}_{d["SEED"]}_gpu.csv'),
        },
    })
sidecar = Path(d["OUT"]) / f'{d["M"]}_{d["SEED"]}.json'
sidecar.write_text(json.dumps(fields, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f'    sidecar[{d["STATUS"]}] {sidecar}')
PY
}

for M in $MAQAMS; do
  style="/content/audiocpp_inference/prompts/${M}_style.txt"
  lyrics="/content/audiocpp_inference/prompts/${M}_lyrics.txt"
  CAP="$(python3 "$SCRIPT_DIR/duration_cap.py" "$lyrics")"
  export M CAP STYLE="$style" LYRICS="$lyrics"

  for CFG in $CFGS; do
    OUT="$PROBE/$CFG"
    wav="$OUT/${M}_${SEED}.wav"
    tfile="$OUT/${M}_${SEED}_time.txt"
    EXTRA="$(opts_for "$CFG")" || exit 1
    CMD_STR="OUT_DIR=$OUT EXTRA_REQUEST_OPTS=\"$EXTRA\" LORA_AR=$AR LORA_NAR=$NAR bash INFERENCE/run_one.sh $M $SEED $CAP"
    export OUT CFG EXTRA CMD_STR

    if [ -f "$wav" ] && [ -f "$tfile" ] && grep -q "Exit status: 0" "$tfile"; then
      echo "[skip] $CFG $M (already succeeded)"
      continue
    fi

    mkdir -p "$OUT"
    START_UTC="$(date -u +%FT%TZ)"
    export START_UTC
    echo "=== [$CFG $M] knob='$EXTRA' cap=$CAP start=$START_UTC ==="
    emit_sidecar started

    t0="$(date +%s)"
    OUT_DIR="$OUT" EXTRA_REQUEST_OPTS="$EXTRA" LORA_AR="$AR" LORA_NAR="$NAR" \
      "$RUN_ONE" "$M" "$SEED" "$CAP"
    rc=$?
    WALL_S="$(( $(date +%s) - t0 ))"
    END_UTC="$(date -u +%FT%TZ)"
    EXIT_CODE="$rc"
    export WALL_S END_UTC EXIT_CODE
    emit_sidecar "$([ "$rc" -eq 0 ] && echo ok || echo failed)"

    if [ "$rc" -ne 0 ]; then
      echo "FAIL $CFG $M exit=$rc $END_UTC" | tee -a "$FAILED"
    fi
  done
done

echo "=== pron_knob_probe done $(date -u +%FT%TZ) ==="
