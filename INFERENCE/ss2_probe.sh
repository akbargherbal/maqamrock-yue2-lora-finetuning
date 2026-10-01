#!/usr/bin/env bash
# Scratch runner for ss2_probe.py on a fresh Colab VM (CPU or GPU).
# Builds the isolated venv (Colab's system numpy/transformers clash with SheetSage2),
# warms ffmpeg, then runs the probe. Idempotent; safe to re-run.
#
#   bash INFERENCE/ss2_probe.sh /content/sample_song.mp3
#
# Scratch artifact, not authority.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV=/content/.ss2
PY="$VENV/bin/python"

if [ -z "${HF_TOKEN:-}" ] && [ -f /root/.secrets.env ]; then
  set -a; . /root/.secrets.env; set +a
fi
[ -n "${HF_TOKEN:-}" ] && echo "HF_TOKEN: present" || echo "HF_TOKEN: MISSING (gated repos will 401)"

if [ ! -x "$PY" ]; then
  command -v uv >/dev/null 2>&1 || pip -q install uv
  uv venv "$VENV" --python 3.11
fi

if command -v nvidia-smi >/dev/null 2>&1; then
  IDX=https://download.pytorch.org/whl/cu126
else
  IDX=https://download.pytorch.org/whl/cpu
fi
echo "torch index: $IDX"
uv pip install --python "$PY" -q torch==2.8.0 torchaudio==2.8.0 --index-url "$IDX"
uv pip install --python "$PY" -q \
  transformers==4.45.2 huggingface-hub==0.36.0 safetensors==0.5.3 \
  numpy==1.24.3 scipy==1.13.1 mir_eval==0.8.2 pretty_midi==0.2.10 \
  mido==1.3.3 setuptools==78.1.1

command -v ffmpeg >/dev/null 2>&1 || { apt-get -qq update && apt-get -qq install -y ffmpeg; }

exec "$PY" "$HERE/ss2_probe.py" "$@"
