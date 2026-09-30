#!/usr/bin/env bash
# Build the isolated SheetSage2 env that the batch transcriber expects:
#
#     /content/.venv-sheetsage2/bin/python
#
# Why this file exists: `INFERENCE/sheetsage2_transcribe.py` (its own header) and
# `docs/PRON_LORA_RESCUE.md` phase 2 both RUN under `/content/.venv-sheetsage2`,
# but nothing in the repo BUILT it. The only recipe was the scratch
# `INFERENCE/ss2_probe.sh` (header: "Scratch artifact, not authority"), which
# builds `/content/.ss2` and then immediately runs a probe. This is the
# build-only, idempotent equivalent, at the path the runbook names.
#
#   bash INFERENCE/ss2_venv.sh          # build (or reuse) the venv
#
# Pins mirror ss2_probe.sh, the env measured CPU-viable for one <=10-min track in
# `docs/music-cover-feasibility.md` section 2.1. System Python (3.13 /
# transformers 5.x) is incompatible with SheetSage2's custom code, hence the
# separate 3.11 venv. Idempotent: an existing venv is reused as-is.
#
# Build it on the box that will transcribe. The transcription step is CPU work
# and should run on a free CPU runtime (WAVs over GCS); if run on the GPU box,
# force CPU with `CUDA_VISIBLE_DEVICES=""` (SS2 auto-selects CUDA otherwise --
# docs/COMMAND_HANDOVER_GOTCHAS.md, 2026-09-30).
set -euo pipefail

VENV="${SS2_VENV:-/content/.venv-sheetsage2}"
PY="$VENV/bin/python"

if [ -z "${HF_TOKEN:-}" ] && [ -f /root/.secrets.env ]; then
  set -a; . /root/.secrets.env; set +a
fi
[ -n "${HF_TOKEN:-}" ] && echo "[info] HF_TOKEN: present" || echo "[warn] HF_TOKEN missing (gated repos will 401)"

command -v uv >/dev/null 2>&1 || { echo "[fail] uv not found on PATH (pip install uv)"; exit 1; }

if [ ! -x "$PY" ]; then
  echo "[info] creating $VENV (python 3.11)"
  uv venv "$VENV" --python 3.11
else
  echo "[info] reusing existing $VENV"
fi

# cu126 wheels on a GPU box (matches the transcriber header), cpu wheels otherwise.
# Either imports fine under CUDA_VISIBLE_DEVICES="" -- the transcription is CPU.
if command -v nvidia-smi >/dev/null 2>&1; then
  IDX=https://download.pytorch.org/whl/cu126
else
  IDX=https://download.pytorch.org/whl/cpu
fi
echo "[info] torch index: $IDX"
uv pip install --python "$PY" -q torch==2.8.0 torchaudio==2.8.0 --index-url "$IDX"
uv pip install --python "$PY" -q \
  transformers==4.45.2 huggingface-hub==0.36.0 safetensors==0.5.3 \
  numpy==1.24.3 scipy==1.13.1 mir_eval==0.8.2 pretty_midi==0.2.10 \
  mido==1.3.3 setuptools==78.1.1

# SheetSage2 decodes audio through ffmpeg.
command -v ffmpeg >/dev/null 2>&1 || { apt-get -qq update && apt-get -qq install -y ffmpeg; }

"$PY" - <<'PYCHECK'
import torch, transformers
print(f"[ok] torch {torch.__version__} · transformers {transformers.__version__}")
PYCHECK

echo "[done] $VENV ready — run phase 2 with:"
echo "  CUDA_VISIBLE_DEVICES=\"\" $PY INFERENCE/sheetsage2_transcribe.py \\"
echo "      --input-dir <pass1-dir> --out-dir <abc-dir> --all"
