#!/usr/bin/env bash
# Regenerate the two production merges (v2 + pron ckpt 3050, alpha 0.5 / 0.3).
#
# CPU-only. Reproduces the converted AR/NAR adapter sha256 values recorded in
# results/pron_production_merge/README.md, which are the stable identities.
#
# The merged *file* sha256 is NOT reproducible: safetensors 0.8.0 writes
# __metadata__ in nondeterministic HashMap order, so the raw bytes differ while
# every tensor (and all parsed metadata) is identical. Compare the printed
# converted AR hashes and the tensor digests, not the merged file hash.
#
# Usage (from the repo root, on a VM with gcloud auth):
#   bash results/pron_production_merge/regenerate.sh
#
# Optional overrides:
#   WORKDIR=/some/dir        scratch root (default: /content/pron_production_merge)
#   CONVERTER=/path/to/convert_aitoolkit_yue2_lora.py
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
WORKDIR="${WORKDIR:-/content/pron_production_merge}"
BASE="${GCP_BACKUP_BASE:?GCP_BACKUP_BASE is not set (export it from the notebook)}"
CONVERTER="${CONVERTER:-/content/converter/out/convert_aitoolkit_yue2_lora.py}"

V2_DIR="/content/ai-toolkit/output/akbar_arabic_rock_lora"
V2="$V2_DIR/akbar_arabic_rock_lora.safetensors"
PRON_DIR="/content/ai-toolkit/output/pron_lora_ar_only_r8"
PRON="$PRON_DIR/pron_lora_ar_only_r8_000003050.safetensors"

V2_SHA="b1d090987355303129a3765d257e61c983b91d48cecb8a30aa424e09cdd24cd4"
PRON_SHA="ead30d5202dec368838304546d5400ce46e4a2da713a19a9236781f575178a21"

# run name -> alpha ; expected converted AR sha256 (stable identity)
RUNS=("c3050_a0.5:0.5:33e824f24f1eec1ab06a45365e93a19b078a2a7cfbea724eba1b908d27360509"
      "c3050_a0.3:0.3:dd0d495924c3b533df2fe89cdb5ff82c5a708047c3e3b0bf6ccec42d6033c6e9")
NAR_SHA="7d9324bfabdfa806c600b12dfa1537501368f25a00d6f4aaf7252449414377c6"

sha256_of() { sha256sum "$1" | cut -d' ' -f1; }

fetch() {  # fetch <gcs-url> <dest> <expected-sha>
  local url="$1" dest="$2" want="$3"
  if [ ! -f "$dest" ]; then
    mkdir -p "$(dirname "$dest")"
    gcloud storage cp "$url" "$dest"
  fi
  local got; got="$(sha256_of "$dest")"
  if [ "$got" != "$want" ]; then
    echo "[FAIL] $dest sha256 $got != expected $want" >&2
    exit 1
  fi
  echo "[ok] $(basename "$dest")  $got"
}

echo "== inputs =="
fetch "$BASE/akbar_arabic_rock_lora/output/akbar_arabic_rock_lora.safetensors" "$V2" "$V2_SHA"
fetch "$BASE/pron_lora_ar_only_r8/output/pron_lora_ar_only_r8_000003050.safetensors" "$PRON" "$PRON_SHA"

if [ ! -f "$CONVERTER" ]; then
  echo "[FAIL] converter not found: $CONVERTER" >&2
  echo "       fetch it: gcloud storage cp $BASE/audiocpp_inference/converter/convert_aitoolkit_yue2_lora.py $CONVERTER" >&2
  exit 1
fi

cd "$REPO_ROOT"
rc=0
for entry in "${RUNS[@]}"; do
  IFS=: read -r run alpha want_ar <<<"$entry"
  echo "== $run (alpha=$alpha) =="
  merged="$WORKDIR/merged/$run/akbar_arabic_rock_lora.safetensors"
  conv="$WORKDIR/converted/$run"
  python merge_pron_lora.py --alpha "$alpha" --pron-checkpoint 3050 --out "$merged"
  python "$CONVERTER" "$merged" --out-dir "$conv" >/dev/null
  got_ar="$(sha256_of "$conv/akbar_arabic_rock_lora_ar.safetensors")"
  got_nar="$(sha256_of "$conv/akbar_arabic_rock_lora_nar.safetensors")"
  echo "   converted AR  $got_ar"
  echo "   converted NAR $got_nar"
  [ "$got_ar" = "$want_ar" ] || { echo "   [FAIL] AR mismatch (want $want_ar)" >&2; rc=1; }
  [ "$got_nar" = "$NAR_SHA" ] || { echo "   [FAIL] NAR mismatch (want $NAR_SHA)" >&2; rc=1; }
done

if [ "$rc" -eq 0 ]; then
  echo "== PASS: converted AR/NAR match the recorded stable identities =="
else
  echo "== FAIL: see mismatches above ==" >&2
fi
exit "$rc"
