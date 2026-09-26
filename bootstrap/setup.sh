#!/usr/bin/env bash
# maqamrock-yue2-lora-finetuning — Colab bootstrap
#
# Two modes, selected by flag (default: --training):
#   --training   dataset + ai-toolkit + the training HF assets
#   --inference  audio.cpp (cloned, NOT built) + ccache + the inference GGUF assets
# Both modes install opencode and log into HF. Inference deliberately skips
# the dataset download and the (slow) ai-toolkit/torch install.
#
# Run this BACKGROUNDED while you do vscode.dev tunnel auth in the
# foreground, so the auth wait and the install/download time overlap.
# Ostris's own deps (torch + its requirements.txt) take noticeably longer
# to install than FL-YuE2's did last project — budget for it.
#
#   git clone <this repo's URL>
#   cd maqamrock-yue2-lora-finetuning
#   bash bootstrap/setup.sh --training  > /content/logs/setup.log 2>&1 &
#   bash bootstrap/setup.sh --inference > /content/logs/setup.log 2>&1 &
#   /content/code tunnel
#
# Deliberately non-interactive — nothing here should prompt. HF_TOKEN is
# staged into a plain file by the notebook cell BEFORE this script runs
# (`userdata` only exists inside the notebook kernel, not in a terminal
# shell). GCP auth and the dataset's GCS location both come from that same
# cell: the path arrives as GCP_DATASET_PATH (training mode only). No bucket
# or path is hardcoded in this repo.
#
# Toolchain note (see DECISIONS.md for the full source-verified writeup):
# unlike FL-YuE2, which needed every weight staged into a specific
# ComfyUI/models/yue2/<name>/ folder, Ostris's yue2 support resolves every
# asset through plain `huggingface_hub.hf_hub_download`, which lands in the
# STANDARD HF cache (~/.cache/huggingface/hub). So this script does not
# build or merge a custom directory tree — it just pre-warms that cache with
# `hf download` for the same repos, so the first training step doesn't stall
# on a multi-GB download mid-run. SheetSage2 is deliberately NOT pre-warmed:
# it only loads when model_kwargs.cot != "off", and this config has
# cot: "off" — downloading it would just waste bandwidth and disk.
# Inference instead stages a real model dir (ggufs + sidecars) and pulls the
# converted LoRA from GCS, because `audiocpp_cli --model <dir>` reads configs
# from that dir rather than the HF cache.

set -e

# --- Mode (default: training) ---
MODE="training"
usage() {
  cat <<'USAGE'
Usage: bash bootstrap/setup.sh [--training | --inference]

  --training   (default) dataset + ai-toolkit + training HF assets
  --inference  audio.cpp clone + ccache + inference GGUF assets (no dataset, no ai-toolkit)
  -h, --help   show this message
USAGE
}
while [ "$#" -gt 0 ]; do
  case "$1" in
    --training)  MODE="training" ;;
    --inference) MODE="inference" ;;
    -h|--help)   usage; exit 0 ;;
    *) echo "[FAIL] unknown argument: $1"; usage; exit 1 ;;
  esac
  shift
done

mkdir -p /content/logs

if [ -f /root/.secrets.env ]; then
  source /root/.secrets.env
else
  echo "[WARN] /root/.secrets.env not found — HF_TOKEN must already be in the environment"
fi
if [ -z "${HF_TOKEN:-}" ]; then
  echo "[FAIL] HF_TOKEN is empty; stage /root/.secrets.env from the notebook cell first"
  exit 1
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AI_TOOLKIT="/content/ai-toolkit"
AI_TOOLKIT_REPO="https://github.com/ostris/ai-toolkit.git"
AUDIO_CPP="/content/audio.cpp"
AUDIO_CPP_REPO="https://github.com/0xShug0/audio.cpp"
GGUF_REPO="audio-cpp/Yue2-3B-GGUF"
# Not pinned to a commit on purpose: unlike FL-YuE2 (a third-party custom
# node with its own release cadence), Ostris's yue2 support is upstream and
# moving fast. The resolved commit is printed by the verify step below so
# the exact build this run used is still identifiable after the fact.

# The dataset's GCS location is supplied at runtime by the launching
# notebook (exported into /root/.secrets.env); it is never hardcoded here.
# Training-only: inference has nothing to download from GCS here.
DATASET_LOCAL="/content/yue2_dataset"
if [ "$MODE" = "training" ]; then
  DATASET_GCS="${GCP_DATASET_PATH:?GCP_DATASET_PATH must be set (the launching notebook exports it)}"
fi

# Inference staging (--inference). yue2 needs a concrete on-disk model dir, not
# just a warm HF cache: `audiocpp_cli --model <dir>` discovers the configs in
# that dir (docs/models/yue2.md). Paths match what INFERENCE/run_one.sh expects.
AUDIOCPP_INFERENCE="/content/audiocpp_inference"
YUE2_MODEL_DIR="$AUDIOCPP_INFERENCE/models/Yue2-3B-GGUF"
LORA_LOCAL="/content/converter/out"
# Prebuilt CUDA audiocpp_cli + the prompts/ and scripts/ trees. Staged under
# $AUDIOCPP_INFERENCE, deliberately NOT under $AUDIO_CPP: job_audio_cpp does
# `rm -rf "$AUDIO_CPP"` and re-clones it, which would race this job and delete
# anything staged there.
AUDIOCPP_BIN_LOCAL="$AUDIOCPP_INFERENCE/bin/audiocpp_cli"
AUDIOCPP_PROMPTS_LOCAL="$AUDIOCPP_INFERENCE/prompts"
AUDIOCPP_SCRIPTS_LOCAL="$AUDIOCPP_INFERENCE/scripts"
if [ "$MODE" = "inference" ]; then
  # Canonical LoRA library (docs/LORA_INVENTORY.md): the current style adapter.
  # Production v2+pron merges live under loras/audio_cpp/pron/<cfg>/ and are
  # staged per-sweep, not by the bootstrap.
  LORA_GCS="${GCP_BACKUP_BASE:?GCP_BACKUP_BASE must be set (the launching notebook exports it)}/loras/audio_cpp/style"
  CONVERTER_GCS="${GCP_BACKUP_BASE:?GCP_BACKUP_BASE must be set (the launching notebook exports it)}/audiocpp_inference/converter"
  AUDIOCPP_BIN_GCS="$GCP_BACKUP_BASE/audiocpp_inference/build/audiocpp_cli"
  AUDIOCPP_PROMPTS_GCS="$GCP_BACKUP_BASE/audiocpp_inference/prompts"
  AUDIOCPP_SCRIPTS_GCS="$GCP_BACKUP_BASE/audiocpp_inference/scripts"
fi

echo "=== $(date) — maqamrock-yue2 bootstrap starting (mode: $MODE) ==="

# --- Fast, synchronous: the `hf` CLI (>=0.34) and credentials ---
pip install -q --no-input "huggingface_hub>=0.36.0"
if ! command -v hf >/dev/null 2>&1; then
  echo "[FAIL] 'hf' CLI not found after installing huggingface_hub>=0.36 — check pip's bin dir is on PATH"
  exit 1
fi
hf auth login --token "$HF_TOKEN"

# --- Jobs (functions, so the background dispatch needs no quote gymnastics) ---

job_opencode() {
  curl -fsSL https://opencode.ai/install | bash
}

job_ai_toolkit() {
  if [ ! -f "$AI_TOOLKIT/run.py" ]; then
    rm -rf "$AI_TOOLKIT" && git clone --quiet "$AI_TOOLKIT_REPO" "$AI_TOOLKIT"
  fi
  git -C "$AI_TOOLKIT" rev-parse --short HEAD
  # Torch first, pinned to ai-toolkit's own README (torch 2.13.0 / cu130).
  # Do NOT leave this unpinned: a bare `pip install torch ... cu128` resolves
  # to 2.11.0+cu128, and torchaudio 2.11 decodes audio through torchcodec —
  # whose 0.15.0 wheel links against CUDA 13 (libnvrtc.so.13). Under cu128,
  # torchaudio.load() fails on EVERY file, so latent caching never starts.
  # Colab's L4 driver (580.x) supports CUDA 13. Re-check ai-toolkit's README
  # install block at bootstrap time if this pin drifts.
  # Exact local versions (+cu130), not bare 2.11.0: PEP 440 says `==2.11.0`
  # also matches `2.11.0+cu128`, so a plain pin silently keeps a stale cu128
  # torchaudio on a re-run and torchaudio then refuses to import.
  pip install -q --no-input \
    torch==2.13.0+cu130 torchvision==0.28.0+cu130 torchaudio==2.11.0+cu130 \
    --index-url https://download.pytorch.org/whl/cu130
  # Two ai-toolkit requirement pins are stale for Colab's Python 3.13 + this
  # torch stack. Patch both before installing (idempotent seds — the clone
  # persists for the session, and the patterns stop matching after one run):
  #  - scipy==1.12.0 has no cp313 wheel and its failed source build aborts the
  #    ENTIRE requirements install, leaving every other pinned dep missing.
  #  - torchcodec==0.9.1 is ABI-incompatible with torch 2.13; upstream installs
  #    0.15.0 as an override (manager/spec.py). See DECISIONS.md.
  sed -i 's|^scipy==1\.12\.0$|scipy>=1.14|' "$AI_TOOLKIT/requirements.txt"
  sed -i 's|^torchcodec==[0-9.]*$|torchcodec==0.15.0|' "$AI_TOOLKIT/requirements_base.txt"
  pip install -q --no-input -r "$AI_TOOLKIT/requirements.txt"
}

job_dataset() {
  local marker="${DATASET_LOCAL}/.bootstrap_complete"
  if [ -f "$marker" ]; then
    echo "dataset already downloaded (marker $marker); skipping"
    return 0
  fi
  # rsync (no -d) transfers only missing/changed objects, so a re-run after a
  # partial download resumes cheaply instead of re-pulling all 267 tracks.
  mkdir -p "$DATASET_LOCAL"
  gsutil -m rsync -r "$DATASET_GCS" "$DATASET_LOCAL"
  touch "$marker"
}

# Pronunciation (AR-only) LoRA dataset -- SEPARATE from the v2 dataset above.
# Opt-in: runs only when GCP_PRON_DATASET_PATH is exported, so a v2 training
# bootstrap behaves exactly as before. The GCS prefix is a SIBLING of
# dataset/ (pron_dataset/), never inside it, so job_dataset's recursive rsync
# can never pull pron files into v2's /content/yue2_dataset. The completion
# marker lives at the /content/pron_dataset ROOT, never inside train/val/smoke
# (a marker in a subfolder would be uploaded and then skip that subtree's sync).
job_pron_dataset() {
  if [ -z "${GCP_PRON_DATASET_PATH:-}" ]; then
    echo "GCP_PRON_DATASET_PATH unset; skipping pron dataset (opt-in)"
    return 0
  fi
  local local_dir="/content/pron_dataset"
  local marker="${local_dir}/.bootstrap_complete"
  if [ -f "$marker" ]; then
    echo "pron dataset already downloaded (marker $marker); skipping"
    return 0
  fi
  mkdir -p "$local_dir"
  gsutil -m rsync -r "$GCP_PRON_DATASET_PATH" "$local_dir"
  touch "$marker"
}

# --- HF cache pre-warm: no custom directory tree, just make these a cache
# hit instead of a stall the first time training actually asks for them. ---
job_hf_yue2_backbone() {
  hf download Comfy-Org/YuE2 checkpoints/yue2_3b_int8_convrot.safetensors
}

job_hf_mert() {
  hf download m-a-p/MERT-v2-FullSong
}

job_hf_tokenizer_head() {
  hf download Mothersuperior/yue2-mothersuperior-realaudio-tokenizer-v4 \
    tokenizer_head_joint_v4.pt
  # nar_lora_joint_v4.pt is only loaded if model_kwargs.merge_nar_lora is
  # set, which this config does not set — not pre-warmed, on purpose.
}

# --- Inference (--inference) ---
# audio.cpp is only CLONED here, never built: the build is scoped and
# deliberate (see DECISIONS.md) and is left as a manual step. The yue2 model
# dir (ggufs + sidecars) is staged on disk and the converted LoRA is pulled
# from GCS, so a fresh VM is actually runnable.
#
# Both packages here are hard requirements of the build/run path, not optional
# speedups that silently no-op:
#  - ccache: the recommended build (scripts/build_linux.sh --ccache ...) hard-fails
#    when the binary is missing (verified in that script: `--ccache was passed but
#    ccache is not installed` + exit 1).
#  - GNU time: INFERENCE/run_one.sh wraps every generation in `/usr/bin/time -v -o`
#    to record wall time/max RSS/CPU%. Colab ships only the bash builtin `time`, so
#    without the package the FIRST run_one.sh invocation exits 127 before the model
#    loads (`/usr/bin/time: No such file or directory`) — confirmed on a T4 VM.
# Training has no build step, so this stays inference-only.
job_ccache() {
  apt-get install -y ccache time
}

job_audio_cpp() {
  if [ -d "$AUDIO_CPP/.git" ]; then
    echo "audio.cpp already cloned at $AUDIO_CPP; skipping clone"
  else
    rm -rf "$AUDIO_CPP" && git clone --quiet "$AUDIO_CPP_REPO" "$AUDIO_CPP"
  fi
  git -C "$AUDIO_CPP" rev-parse --short HEAD
}

# Full model dir, not just the HF cache: `audiocpp_cli --model <dir>` reads the
# ggufs and sidecars from that dir (docs/models/yue2.md). BF16, not Q8:
# DECISIONS.md recommends BF16 when a LoRA is merged (Q8/Q4 merge into
# dequantized weights and requantize the result).
job_hf_yue2_gguf() {
  mkdir -p "$YUE2_MODEL_DIR"
  hf download "$GGUF_REPO" yue2-3b-bf16.gguf yue2-vae-f16.gguf --local-dir "$YUE2_MODEL_DIR"
}

job_hf_yue2_sidecars() {
  mkdir -p "$YUE2_MODEL_DIR"
  hf download "$GGUF_REPO" --include "sidecars/*" --local-dir "$YUE2_MODEL_DIR"
}

# Canonical style adapter (unfused, for audio.cpp) from the LoRA library
# (loras/audio_cpp/style/) plus the offline converter tool, which stays with
# the inference workspace. Same rsync pattern as the dataset pull.
job_lora_adapters() {
  mkdir -p "$LORA_LOCAL"
  gsutil -m rsync -r "$LORA_GCS" "$LORA_LOCAL"
  gsutil cp "$CONVERTER_GCS/convert_aitoolkit_yue2_lora.py" "$LORA_LOCAL/"
}

# Prebuilt CUDA audiocpp_cli (350 MiB, CUDA 12.0 / sm_75) plus the prompts/ and
# scripts/ trees, GCS-persisted under audiocpp_inference/. Skips the ~21 min CPU
# build entirely on a fresh VM. Marker mirrors job_dataset: the pulls are
# idempotent either way, but then no 350 MiB copy re-runs on every bootstrap.
job_audiocpp_binary() {
  local marker="$AUDIOCPP_INFERENCE/.audiocpp_binary_complete"
  if [ -f "$marker" ]; then
    echo "audiocpp_cli already staged (marker $marker); skipping"
    return 0
  fi
  mkdir -p "$(dirname "$AUDIOCPP_BIN_LOCAL")" \
           "$AUDIOCPP_PROMPTS_LOCAL" "$AUDIOCPP_SCRIPTS_LOCAL"
  # Single file, not a tree: plain cp, so gsutil does not hash-compare 350 MiB
  # the way `rsync -r` would.
  gsutil cp "$AUDIOCPP_BIN_GCS" "$AUDIOCPP_BIN_LOCAL"
  chmod +x "$AUDIOCPP_BIN_LOCAL"
  gsutil -m rsync -r "$AUDIOCPP_PROMPTS_GCS" "$AUDIOCPP_PROMPTS_LOCAL"
  gsutil -m rsync -r "$AUDIOCPP_SCRIPTS_GCS" "$AUDIOCPP_SCRIPTS_LOCAL"
  touch "$marker"
}

# --- Launch every independent, slow task in parallel ---
pids=()
names=()
starts=()

start_job() {
  local name="$1"; shift
  starts+=("$(date +%s)")
  ("$@") > "/content/logs/${name}.log" 2>&1 &
  pids+=("$!")
  names+=("$name")
}

start_job opencode job_opencode
if [ "$MODE" = "training" ]; then
  start_job ai_toolkit job_ai_toolkit
  start_job dataset job_dataset
  # opt-in: only when the launching notebook exported GCP_PRON_DATASET_PATH
  if [ -n "${GCP_PRON_DATASET_PATH:-}" ]; then
    start_job pron_dataset job_pron_dataset
  fi
  start_job hf_yue2_backbone job_hf_yue2_backbone
  start_job hf_mert job_hf_mert
  start_job hf_tokenizer_head job_hf_tokenizer_head
else
  start_job ccache job_ccache
  start_job audio_cpp job_audio_cpp
  start_job hf_yue2_gguf job_hf_yue2_gguf
  start_job hf_yue2_sidecars job_hf_yue2_sidecars
  start_job lora_adapters job_lora_adapters
  start_job audiocpp_binary job_audiocpp_binary
fi

echo "Launched in parallel: ${names[*]}"
echo "tail -f /content/logs/<n>.log to watch any one of these live."

fail=0
: > /content/logs/timing.txt
for i in "${!pids[@]}"; do
  if wait "${pids[$i]}"; then
    status="ok"
  else
    status="FAIL"
    fail=1
  fi
  elapsed=$(( $(date +%s) - ${starts[$i]} ))
  if [ "$status" = "ok" ]; then
    echo "[ok]   ${names[$i]} (${elapsed}s)"
  else
    echo "[FAIL] ${names[$i]} — see /content/logs/${names[$i]}.log (${elapsed}s)"
  fi
  echo "${names[$i]}	${elapsed}s	${status}" >> /content/logs/timing.txt
done
echo "total	${SECONDS}s	${MODE}" >> /content/logs/timing.txt

# --- Verify what actually landed, don't just trust exit codes ---
echo "=== Verifying setup ==="

if command -v opencode >/dev/null 2>&1 || [ -x "$HOME/.opencode/bin/opencode" ]; then
  echo "[ok]   opencode installed"
else
  echo "[WARN] opencode not found on PATH after install — check /content/logs/opencode.log"
fi

# Confirm an HF cache asset actually landed. `hf download` is idempotent
# against the cache -- a cache hit just prints the path back instantly
# instead of re-downloading -- so re-running it here is a cheap, honest check
# rather than trusting the earlier background job's exit code.
confirm_hf() {
  local repo="$1"; shift
  if hf download "$repo" "$@" >/dev/null 2>&1; then
    echo "[ok]   $repo $* present in HF cache"
  else
    echo "[FAIL] $repo $* not confirmed in HF cache — re-run hf download manually"
    fail=1
  fi
}

if [ "$MODE" = "training" ]; then
  track_count=$(find "$DATASET_LOCAL" -maxdepth 1 -name "*.mp3" 2>/dev/null | wc -l)
  if [ "$track_count" -eq 0 ]; then
    echo "[FAIL] dataset looks empty — check /content/logs/dataset.log and the GCS path"
    fail=1
  else
    echo "[ok]   dataset: $track_count tracks in $DATASET_LOCAL"
  fi

  if [ -f "$AI_TOOLKIT/run.py" ]; then
    echo "[ok]   ai-toolkit at $(git -C "$AI_TOOLKIT" rev-parse --short HEAD 2>/dev/null || echo '??') (tracking main, not pinned)"
  else
    echo "[FAIL] ai-toolkit did not clone correctly — run.py missing"
    fail=1
  fi

  confirm_hf Comfy-Org/YuE2 checkpoints/yue2_3b_int8_convrot.safetensors

  # The stack latent caching actually depends on: torch and torchaudio must
  # agree on CUDA (torchaudio refuses to import otherwise), and torchaudio —
  # which in this version routes decode through torchcodec — must be able to
  # read a real dataset file. A stale `==` pin silently kept a cu128 torchaudio
  # next to a cu130 torch and broke every decode; catch that here, not at the
  # first training step mid-cache. See DECISIONS.md.
  if python - <<PY >/dev/null 2>&1
import glob, torch, torchaudio
assert torch.version.cuda == "13.0", torch.version.cuda
torchaudio.load(sorted(glob.glob("$DATASET_LOCAL/*.mp3"))[0])
PY
  then
    echo "[ok]   torch/torchaudio cu130 + torchaudio decodes a dataset mp3"
  else
    echo "[FAIL] torch/torchaudio CUDA mismatch or audio decode failed — see DECISIONS.md 'torch/CUDA stack'"
    fail=1
  fi
else
  if [ -d "$AUDIO_CPP/.git" ]; then
    echo "[ok]   audio.cpp at $(git -C "$AUDIO_CPP" rev-parse --short HEAD 2>/dev/null || echo '??') (tracking main, not pinned; NOT built)"
  else
    echo "[FAIL] audio.cpp did not clone correctly — $AUDIO_CPP/.git missing"
    fail=1
  fi

  if command -v ccache >/dev/null 2>&1; then
    echo "[ok]   ccache installed: $(ccache --version | head -n1)"
  else
    echo "[FAIL] ccache not found after install — the --ccache build would exit 1; see /content/logs/ccache.log"
    fail=1
  fi

  if [ -x "$AUDIOCPP_BIN_LOCAL" ]; then
    echo "[ok]   $AUDIOCPP_BIN_LOCAL"
  else
    echo "[FAIL] $AUDIOCPP_BIN_LOCAL missing — see /content/logs/audiocpp_binary.log"
    fail=1
  fi

  for d in "$AUDIOCPP_PROMPTS_LOCAL" "$AUDIOCPP_SCRIPTS_LOCAL"; do
    if [ -d "$d" ] && [ -n "$(ls -A "$d" 2>/dev/null)" ]; then
      echo "[ok]   $d ($(find "$d" -type f | wc -l) files)"
    else
      echo "[FAIL] $d missing or empty — see /content/logs/audiocpp_binary.log"
      fail=1
    fi
  done

  for f in yue2-3b-bf16.gguf yue2-vae-f16.gguf \
           sidecars/yue2-model-config.json sidecars/yue2-generation-config.json \
           sidecars/yue2-qwen.tiktoken sidecars/yue2-vae-config.json; do
    if [ -f "$YUE2_MODEL_DIR/$f" ]; then
      echo "[ok]   $YUE2_MODEL_DIR/$f"
    else
      echo "[FAIL] $YUE2_MODEL_DIR/$f missing — yue2 cannot load"
      fail=1
    fi
  done

  for f in akbar_arabic_rock_lora_ar.safetensors akbar_arabic_rock_lora_nar.safetensors; do
    if [ -f "$LORA_LOCAL/$f" ]; then
      echo "[ok]   $LORA_LOCAL/$f"
    else
      echo "[FAIL] $LORA_LOCAL/$f missing — see /content/logs/lora_adapters.log"
      fail=1
    fi
  done
fi

if [ "$fail" -eq 1 ]; then
  echo "=== setup.sh finished WITH FAILURES — check the [FAIL] lines above (total ${SECONDS}s) ==="
  exit 1
fi

if [ "$MODE" = "training" ]; then
  cat <<EOF
=== setup.sh done (training) — total ${SECONDS}s ===
Next (in a terminal):
  cd $REPO_ROOT
  # 1. start the backup daemon + GPU logger (see AGENTS.md for the exact commands)
  # 2. launch training:
  cd $AI_TOOLKIT
  python run.py $REPO_ROOT/config/akbar_arabic_rock_lora.yml -l /content/logs/train.log
EOF
else
  cat <<EOF
=== setup.sh done (inference) — total ${SECONDS}s ===
Prebuilt audiocpp_cli staged (no build needed), plus the yue2 model dir + LoRA:
  binary:    $AUDIOCPP_BIN_LOCAL  (sm_75 / T4)
  model dir: $YUE2_MODEL_DIR
  LoRA:      $LORA_LOCAL
  prompts:   $AUDIOCPP_PROMPTS_LOCAL
  scripts:   $AUDIOCPP_SCRIPTS_LOCAL
Next (in a terminal):
  # 1. generate with the repo runner (canonical duration_cap.py, bf16, flash attn):
  bash $REPO_ROOT/INFERENCE/run_one.sh <Maqam> <seed>
Only rebuild audio.cpp if this GPU's arch differs from the staged binary
(flat binary above is sm_75/T4; see docs/audiocpp_gpu_arch_builds.md):
  cd $AUDIO_CPP
  scripts/build_linux.sh --backend cuda --cuda-arch <75|80|89> --ccache \\
    --model-set custom --models yue2 --target audiocpp_cli
EOF
fi
