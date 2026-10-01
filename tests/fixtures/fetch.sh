#!/usr/bin/env bash
# Fetch the Tier B (heavy) e2e fixtures from GCS and verify their hashes.
#
# Tier A fixtures (sidecars, .log, _time.txt, recorded_batch.json) are small text
# and tracked in git. Tier B (.wav, .safetensors, loss_log.db, the sm75 binary,
# full out/ dirs) is gitignored and lives in GCS; this script is the only way to
# materialize it. Entries come from manifest.json -> "tier_b".
#
# Usage: bash tests/fixtures/fetch.sh [--check]
#   --check   verify existing files only; do not download
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFEST="$HERE/manifest.json"
CHECK_ONLY=0
[ "${1:-}" = "--check" ] && CHECK_ONLY=1

command -v gsutil >/dev/null 2>&1 || { echo "gsutil not on PATH" >&2; exit 1; }
command -v sha256sum >/dev/null 2>&1 || { echo "sha256sum not on PATH" >&2; exit 1; }

mapfile -t entries < <(python3 - "$MANIFEST" <<'PY'
import json, sys
m = json.load(open(sys.argv[1], encoding="utf-8"))
for name, spec in (m.get("tier_b") or {}).items():
    print(f"{name}\t{spec['gcs']}\t{spec['sha256']}")
PY
)

if [ "${#entries[@]}" -eq 0 ]; then
  echo "no Tier B fixtures declared in $MANIFEST (nothing to fetch)"
  exit 0
fi

rc=0
for e in "${entries[@]}"; do
  IFS=$'\t' read -r name gcs sha <<<"$e"
  dest="$HERE/$name"
  if [ "$CHECK_ONLY" -eq 1 ] || [ -f "$dest" ]; then
    if [ ! -f "$dest" ]; then
      echo "MISSING  $name" >&2; rc=1; continue
    fi
  else
    mkdir -p "$(dirname "$dest")"
    echo "fetch    $name <- $gcs"
    gsutil -q cp "$gcs" "$dest"
  fi
  got="$(sha256sum "$dest" | awk '{print $1}')"
  if [ "$got" = "$sha" ]; then
    echo "ok       $name"
  else
    echo "SHA MISMATCH $name: expected $sha got $got" >&2
    rc=1
  fi
done
exit "$rc"
