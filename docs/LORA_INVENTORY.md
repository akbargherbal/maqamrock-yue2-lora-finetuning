# LoRA inventory

The single place that says **what LoRAs exist, how many, and where they are**.
Authority for scaling/rank mechanics stays with `docs/PRON_LORA_MERGE.md`; this
file is only the map. Update it whenever an adapter is built, promoted, or retired.

**No adapter here is "the winner".** No `alpha`/checkpoint has been selected — every
candidate is unlistened and the choice follows the blinded listening. Labels are
descriptors, not rankings. Also set: **`alpha` is capped at 0.5**; anything above it
is out of scope and archived (see the end of this file).

## Library location

```
<GCP_BACKUP_BASE>/loras/          # GCP_BACKUP_BASE = gs://…/OSTRIS_Arabic_Suno_Finetuning
  audio_cpp/
    style/                         # v2 style adapter, audio.cpp-loadable (rank 32)
    pron/
      c3050_a0.1/                  # candidate (unlistened)
      c3050_a0.2/                  # candidate (unlistened)
      c3050_a0.3/                  # candidate (unlistened)
      c3050_a0.4/                  # candidate (unlistened)
      c3050_a0.5/                  # candidate (unlistened)
  source/                          # fused ai-toolkit finals the merges are built from
```

Sweep/prototype adapters are **not** here — they stay under their round's prefix and
are clearly non-canonical (`audiocpp_inference/converter/<cfg>/`, `pron_*_sweep/`,
etc.). Local paths under `/content/` are ephemeral and re-staged by
`bootstrap/setup.sh` each VM.

## Counts

| Class | Count | Notes |
|---|---|---|
| Library adapters (AR+NAR pairs) | **6** | style + 5 pron merges (`c3050_a0.1`–`a0.5`); all unlistened |
| Fused source adapters (ai-toolkit) | **2 families** | v2 style, pron AR-only r8 |
| Experimental adapters (in scope, α≤0.5) | **3** | `c1525_a0.5`, `c4575_a0.5`, `cfinal_a0.5` |
| Archived (α>0.5) | **4 configs** | `c3050_a0.55`, `c3050_a0.65`, `c3050_a1.0`, `cfinal_a1.0` — see the archive section |
| Objects in `loras/` | **14** | style 2 + pron 10 + source 2 (~1.07 GiB) |

## Library adapters (`loras/`, audio.cpp-loadable)

Loadable by `audiocpp_cli` via `yue2.ar_lora` / `yue2.nar_lora`, scale 1.0.
The **converted AR sha256 is the stable identity** (see caveat below).

| Config | Status | pron ckpt | α | AR rank | converted AR sha256 | converted NAR sha256 | Path in `loras/` |
|---|---|---|---:|---:|---|---|---|
| style (`a0`) | base style | — | 0 | 32 | `747d5cfe2224b1bae6e582ccf5f2ee2a57e3f030c53d54e134f34a85960426fa` | `ad2c8d8690640e8fd8fea779b57bc2c7c887b93f2bb103bbcbfea056536d7ac9` | `audio_cpp/style/` |
| `c3050_a0.1` | candidate (unlistened) | 3050 | 0.1 | 40 | `184bbd29b552751ded9849429a81f74165ccef13ff82d2befb2978efcbdcbb32` | `7d9324bfabdfa806c600b12dfa1537501368f25a00d6f4aaf7252449414377c6` | `audio_cpp/pron/c3050_a0.1/` |
| `c3050_a0.2` | candidate (unlistened) | 3050 | 0.2 | 40 | `c68217ab619a9cfa992bbba650f03dd19616ea19fd0967060d0a45e9e415d34c` | `7d9324bfabdfa806c600b12dfa1537501368f25a00d6f4aaf7252449414377c6` | `audio_cpp/pron/c3050_a0.2/` |
| `c3050_a0.3` | candidate (unlistened) | 3050 | 0.3 | 40 | `dd0d495924c3b533df2fe89cdb5ff82c5a708047c3e3b0bf6ccec42d6033c6e9` | `7d9324bfabdfa806c600b12dfa1537501368f25a00d6f4aaf7252449414377c6` | `audio_cpp/pron/c3050_a0.3/` |
| `c3050_a0.4` | candidate (unlistened) | 3050 | 0.4 | 40 | `210daf9f1f042d13929fd3be48ebd24c9e76618ce0cf4ba1eb6e555d907c6218` | `7d9324bfabdfa806c600b12dfa1537501368f25a00d6f4aaf7252449414377c6` | `audio_cpp/pron/c3050_a0.4/` |
| `c3050_a0.5` | candidate (unlistened) | 3050 | 0.5 | 40 | `33e824f24f1eec1ab06a45365e93a19b078a2a7cfbea724eba1b908d27360509` | `7d9324bfabdfa806c600b12dfa1537501368f25a00d6f4aaf7252449414377c6` | `audio_cpp/pron/c3050_a0.5/` |

All five pron merges share the same NAR (copied from v2; independent of α).
`c3050_a0.1`/`c3050_a0.2` were built 2026-09-26 from the pinned `loras/source/`
inputs (v2 `b1d09098…`, pron 3050 `ead30d52…`) with `merge_pron_lora.py` + the
converter; `c3050_a0.2` reproduces the pre-existing experiment byte-for-byte
(converted AR `c68217ab…`).

## Fused source adapters (`loras/source/`)

Inputs to `merge_pron_lora.py`. The `loras/source/` copies are pinned snapshots;
the training runs keep the full checkpoint sets.

| Adapter | Rank | sha256 | Path |
|---|---|---:|---|
| v2 style (AR+NAR, final step 3000) | 32 | `b1d090987355303129a3765d257e61c983b91d48cecb8a30aa424e09cdd24cd4` | `loras/source/akbar_arabic_rock_lora.safetensors` (also `akbar_arabic_rock_lora/output/`, + 11 numbered checkpoints) |
| pron AR-only r8, ckpt **3050** | 8 | `ead30d5202dec368838304546d5400ce46e4a2da713a19a9236781f575178a21` | `loras/source/pron_lora_ar_only_r8_000003050.safetensors` (also `pron_lora_ar_only_r8/output/`; ckpt 1525 `9d8333d9…`, 4575 `c78bb5b6…`, final 6100 `0d506719…`) |

## Experimental adapters (in scope, α≤0.5 — NOT the library)

Same stable-identity rule. Locations are per-round and may hold fused `merged/`
intermediates as well as converted pairs; treat none of it as the library. These
are the other-checkpoint alternatives at α 0.5; nothing here is a winner.

| Config | pron ckpt | α | converted AR sha256 | Where |
|---|---|---:|---|---|
| `c1525_a0.5` | 1525 | 0.5 | `3324b63706a3a58ea89159250850a3bcab1fbcb851abcaffb7ae0d9d260f534c` | `audiocpp_inference/pron_ckpt_sweep/` |
| `c4575_a0.5` | 4575 | 0.5 | `ebd22026495125e74ab48373ad0ce8a8d767cdb625e018affc38c24b1fc3e56d` | `audiocpp_inference/pron_ckpt_sweep/` |
| `cfinal_a0.5` | 6100 | 0.5 | `525d3af25dfcddabbd587673c36dfaecd148cf97a0dfc6d90cbede15ed700ada` | `pron_alpha_sweep/merged/` (converted pair only) |

(`t08`/`t10` temperature rounds reuse these same configs — no new adapters. The
`c3050_a0.1`–`a0.5` adapters now live in the library, above.)

## Archived — α>0.5 (out of scope)

`alpha` above 0.5 is not useful for this work, so every artifact for those configs
was moved (2026-09-26) to `<base>/archive/alpha_gt_0.5/`, preserving each original
path: `c3050_a0.55`, `c3050_a0.65` (converted pairs + fused merged intermediates),
and `c3050_a1.0`, `cfinal_a1.0` (renders + fused merged). Their converted AR sha256
values remain in the historical records (`results/pron_fine_sweep/`,
`results/pron_sweep/`); they are **not candidates** and should not be rebuilt.

## Caveats

- **Stable identity:** verify with the **converted AR/NAR sha256** or the merged
  tensor digest — never the merged *file* sha256 (`safetensors 0.8.0` writes
  `__metadata__` in nondeterministic order). See `DECISIONS.md`.
- `c3050_a0.4`'s Task-19 sidecar/record is in the unpushed bundle; its binaries
  are canonical in `loras/` and the hash above is from the GCS object.
- **Retired:** the v1 style-only adapter (`akbar_arabic_rock_lora_v1_nolyrics_archived/`)
  is documented in `PROGRESS.md` as a GCS archive but is **absent** from the
  project prefix — no surviving copy.
- Not ours: `Mothersuperior/yue2-mothersuperior-realaudio-tokenizer-v4/nar_lora_joint_v4.pt`
  is a NAR LoRA used only if `merge_nar_lora` is set; not used or staged.

## How to stage an adapter

```bash
# style (the bootstrap default): loras/audio_cpp/style/ -> /content/converter/out/
# a library candidate, e.g. c3050_a0.5:
gsutil -m cp -r "$GCP_BACKUP_BASE/loras/audio_cpp/pron/c3050_a0.5" /content/converter/out/
# then run with explicit overrides (or let run_one.sh's defaults use the style pair):
LORA_AR=/content/converter/out/c3050_a0.5/akbar_arabic_rock_lora_ar.safetensors \
LORA_NAR=/content/converter/out/c3050_a0.5/akbar_arabic_rock_lora_nar.safetensors \
  bash INFERENCE/run_one.sh Hijaz <seed>
```
