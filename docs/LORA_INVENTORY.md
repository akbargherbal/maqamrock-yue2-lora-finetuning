# LoRA inventory

The single place that says **what LoRAs exist, how many, and where they are**.
Authority for scaling/rank mechanics stays with `docs/PRON_LORA_MERGE.md`; this
file is only the map. Update it whenever an adapter is built, shipped, or retired.

## Canonical library location

```
<GCP_BACKUP_BASE>/loras/          # GCP_BACKUP_BASE = gs://…/OSTRIS_Arabic_Suno_Finetuning
  audio_cpp/
    style/                         # current style adapter, audio.cpp-loadable (rank 32)
    pron/
      c3050_a0.5/                  # production, primary
      c3050_a0.4/                  # production
      c3050_a0.3/                  # production, fallback
  source/                          # fused ai-toolkit finals the merges are built from
```

Everything *current* lives under `loras/`. Sweep/prototype adapters are **not**
here — they stay under their round's prefix and are clearly non-canonical
(`audiocpp_inference/converter/<cfg>/`, `pron_*_sweep/`, etc.). Local paths under
`/content/` are ephemeral and re-staged by `bootstrap/setup.sh` each VM.

## Counts

| Class | Count | Notes |
|---|---|---|
| Current loadable adapters (AR+NAR pairs) | **4** | style + 3 production pron merges |
| Fused source adapters (ai-toolkit) | **2 families** | v2 style, pron AR-only r8 |
| Experimental adapters | **8** | sweeps/probes; not shipped |
| Objects in `loras/` | **10** | style 2 + pron 6 + source 2 (~758 MiB) |

## Current loadable adapters (`loras/`)

Loadable by `audiocpp_cli` via `yue2.ar_lora` / `yue2.nar_lora`, scale 1.0.
The **converted AR sha256 is the stable identity** (see caveat below).

| Config | Role | pron ckpt | α | AR rank | converted AR sha256 | converted NAR sha256 | Path in `loras/` |
|---|---|---|---:|---:|---|---|---|
| style (`a0`) | base style | — | 0 | 32 | `747d5cfe2224b1bae6e582ccf5f2ee2a57e3f030c53d54e134f34a85960426fa` | `ad2c8d8690640e8fd8fea779b57bc2c7c887b93f2bb103bbcbfea056536d7ac9` | `audio_cpp/style/` |
| `c3050_a0.5` | **primary** | 3050 | 0.5 | 40 | `33e824f24f1eec1ab06a45365e93a19b078a2a7cfbea724eba1b908d27360509` | `7d9324bfabdfa806c600b12dfa1537501368f25a00d6f4aaf7252449414377c6` | `audio_cpp/pron/c3050_a0.5/` |
| `c3050_a0.4` | current | 3050 | 0.4 | 40 | `210daf9f1f042d13929fd3be48ebd24c9e76618ce0cf4ba1eb6e555d907c6218` | `7d9324bfabdfa806c600b12dfa1537501368f25a00d6f4aaf7252449414377c6` | `audio_cpp/pron/c3050_a0.4/` |
| `c3050_a0.3` | fallback | 3050 | 0.3 | 40 | `dd0d495924c3b533df2fe89cdb5ff82c5a708047c3e3b0bf6ccec42d6033c6e9` | `7d9324bfabdfa806c600b12dfa1537501368f25a00d6f4aaf7252449414377c6` | `audio_cpp/pron/c3050_a0.3/` |

All three pron merges share the same NAR (copied from v2; independent of α).

## Fused source adapters (`loras/source/`)

Inputs to `merge_pron_lora.py`. The `loras/source/` copies are pinned snapshots;
the training runs keep the full checkpoint sets.

| Adapter | Rank | sha256 | Path |
|---|---|---:|---|
| v2 style (AR+NAR, final step 3000) | 32 | `b1d090987355303129a3765d257e61c983b91d48cecb8a30aa424e09cdd24cd4` | `loras/source/akbar_arabic_rock_lora.safetensors` (also `akbar_arabic_rock_lora/output/`, + 11 numbered checkpoints) |
| pron AR-only r8, ckpt **3050** | 8 | `ead30d5202dec368838304546d5400ce46e4a2da713a19a9236781f575178a21` | `loras/source/pron_lora_ar_only_r8_000003050.safetensors` (also `pron_lora_ar_only_r8/output/`; ckpt 1525 `9d8333d9…`, 4575 `c78bb5b6…`, final 6100 `0d506719…`) |

## Experimental adapters (NOT canonical)

Same stable-identity rule. Locations are per-round and may hold fused `merged/`
intermediates as well as converted pairs; treat none of it as the library.

| Config | pron ckpt | α | converted AR sha256 | Where |
|---|---|---:|---|---|
| `c3050_a0.2` | 3050 | 0.2 | `c68217ab619a9cfa992bbba650f03dd19616ea19fd0967060d0a45e9e415d34c` | `audiocpp_inference/converter/c3050_a0.2/`, `pron_fine_sweep/merged/` |
| `c3050_a0.55` | 3050 | 0.55 | `ba328949f995e539bc8d968eaca62b7923ff321c165ef312a2289f8c19ebf53f` | `audiocpp_inference/converter/c3050_a0.55/`, `pron_fine_sweep/merged/` |
| `c3050_a0.65` | 3050 | 0.65 | `e495beca26aa4e7922b18e03a799b45f0d48e38a2efbe6d662fe3584b17c4d00` | `audiocpp_inference/converter/c3050_a0.65/`, `pron_fine_sweep/merged/` |
| `c3050_a1.0` | 3050 | 1.0 | `b4868133ad8094f898002aa28b311f9965f44ef37ffb84afa74000f8ef90b781` | `pron_alpha_sweep/merged/` (converted pair only) |
| `cfinal_a0.5` | 6100 | 0.5 | `525d3af25dfcddabbd587673c36dfaecd148cf97a0dfc6d90cbede15ed700ada` | `pron_alpha_sweep/merged/` (converted pair only) |
| `cfinal_a1.0` | 6100 | 1.0 | `394ff2ca8dc65f464a88217eada72353400d51563a9fdbe258622cda7006f0f2` | `pron_alpha_sweep/merged/` (converted pair only) |
| `c1525_a0.5` | 1525 | 0.5 | `3324b63706a3a58ea89159250850a3bcab1fbcb851abcaffb7ae0d9d260f534c` | `audiocpp_inference/pron_ckpt_sweep/` |
| `c4575_a0.5` | 4575 | 0.5 | `ebd22026495125e74ab48373ad0ce8a8d767cdb625e018affc38c24b1fc3e56d` | `audiocpp_inference/pron_ckpt_sweep/` |

(`t08`/`t10` temperature rounds reuse these same configs — no new adapters.)

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
# a production merge, e.g. primary:
gsutil -m cp -r "$GCP_BACKUP_BASE/loras/audio_cpp/pron/c3050_a0.5" /content/converter/out/
# then run with explicit overrides (or let run_one.sh's defaults use the style pair):
LORA_AR=/content/converter/out/c3050_a0.5/akbar_arabic_rock_lora_ar.safetensors \
LORA_NAR=/content/converter/out/c3050_a0.5/akbar_arabic_rock_lora_nar.safetensors \
  bash INFERENCE/run_one.sh Hijaz <seed>
```
