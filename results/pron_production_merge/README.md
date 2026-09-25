# pron_production_merge — production v2 + pron LoRAs (checkpoint 3050)

Two **production** merges of the frozen v2 style adapter with the AR-only pronunciation
adapter, both at pron checkpoint **3050**:

| run | role | alpha | merged file sha256 | merged tensor digest | converted AR sha256 |
|---|---|---:|---|---|---|
| `c3050_a0.5` | **primary** | 0.5 | `cf0d69b7c27a8aa4480a46f14984747cc08d8940f20f26fffc1fb6b7dcf428e3` | `d9695b9780b96d440c61bc335de9b0b2d87a3429f9be0fa4f5bad77650bc6960` | `33e824f24f1eec1ab06a45365e93a19b078a2a7cfbea724eba1b908d27360509` |
| `c3050_a0.3` | fallback | 0.3 | `0668217e308a43c74e1b62a76bef859ec401662e6e6191133048c87785392b29` | `c564e17096f4e208971c99b8fc343f963fea3446e427569ac48cdbfa3508d481` | `dd0d495924c3b533df2fe89cdb5ff82c5a708047c3e3b0bf6ccec42d6033c6e9` |

Both converted NAR adapters are the same `7d9324bfabdfa806c600b12dfa1537501368f25a00d6f4aaf7252449414377c6`
(NAR is copied from v2; it does not depend on alpha).

This is a **merge-only** task: CPU, no GPU, no audio generation. Method and scaling
convention: [`docs/PRON_LORA_MERGE.md`](../../docs/PRON_LORA_MERGE.md) + `merge_pron_lora.py`.

## Large binaries are not committed

The merged files are **146,861,560 B (~140 MiB)** each — over GitHub's 100 MiB per-file
limit, and regenerable in under a second from published inputs. Matching the
`results/pron_sweep/` convention, this directory commits the **manifest, per-output
sidecars, and a regeneration script**; the binaries live on disk / in GCS:

- merged: `/content/pron_production_merge/merged/<run>/akbar_arabic_rock_lora.safetensors`
- converted (audio.cpp loads these): `/content/pron_production_merge/converted/<run>/`
- GCS: `<GCP_BACKUP_BASE>/pron_production_merge/`

Regenerate with [`regenerate.sh`](regenerate.sh) (downloads both inputs, verifies their
sha256, merges, converts, and checks the converted AR hashes against the table above).

## Verification performed (2026-09-25, CPU)

- Inputs hash-checked before use: v2 raw `b1d09098…`, pron 3050 `ead30d52…` (match
  `docs/PRON_LORA_MERGE.md` and both sweep manifests).
- Merge output: all 448 tensors present; AR rank 32+8→40, NAR zero-padded to rank 40
  (converter's single-rank guard); converter byte-level verification passed.
- Converted AR hashes **match the sweep records exactly** — `c3050_a0.5` =
  `33e824f2…` (`results/pron_sweep/sweep_manifest.json`), `c3050_a0.3` = `dd0d4959…`
  (`results/pron_fine_sweep/sweep_manifest.json`). Same data, same pipeline.

## Non-obvious: file-level sha256 is not reproducible (tensor digest is)

`safetensors 0.8.0` serialises the `__metadata__` map in **nondeterministic (Rust
`HashMap`) order**, so two runs of the identical command produce files that differ in the
metadata key order and **therefore in file sha256** — all tensor bytes and all parsed
metadata are identical. Verified by re-running the `c3050_a0.5` merge: two independent runs
were tensor-identical yet hashed differently (`cf0d69b7…` vs `62e084a7…`; the sweep's own
`c3050_a0.5` merge was `8a3dbdbd…` for the same tensors).

Consequences:

- The **`merged_tensor_digest`** (sha256 over sorted `key‖dtype‖shape‖raw bytes`) and the
  **converted AR/NAR sha256** are the stable identities. Use those to verify a rebuild.
- The `merged file sha256` in the table is the exact byte stream on disk here; treat it as a
  convenience, not a reproducible invariant.
- This also means the sweep manifests' `merged_sha256` values should not be used as
  equality checks — compare converted hashes or tensor digests instead.

See [`DECISIONS.md`](../../DECISIONS.md) "safetensors writes metadata in nondeterministic
order".

## Sidecars

One per output file (sidecar policy in `DECISIONS.md`), each carrying the full command,
option values, adapter sha256s, checkpoint step, and the audio.cpp commit the adapters
target:

- [`c3050_a0.5.sidecar.json`](c3050_a0.5.sidecar.json)
- [`c3050_a0.3.sidecar.json`](c3050_a0.3.sidecar.json)

Machine-readable roll-up: [`merge_manifest.json`](merge_manifest.json).
