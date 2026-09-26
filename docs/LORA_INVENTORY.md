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
      c3050_a0.1 … c3050_a0.5/     # pron ckpt 3050 x alpha 0.1-0.5
      c4575_a0.1 … c4575_a0.5/     # pron ckpt 4575 x alpha 0.1-0.5
      cfinal_a0.1 … cfinal_a0.5/   # pron ckpt 6100 (final) x alpha 0.1-0.5
  source/                          # fused ai-toolkit finals the merges are built from
```

Sweep/prototype adapters are **not** here — they stay under their round's prefix and
are clearly non-canonical (`audiocpp_inference/…_sweep/`, `pron_*_sweep/`, etc.).
Local paths under `/content/` are ephemeral and re-staged by `bootstrap/setup.sh`
each VM.

## Counts

| Class | Count | Notes |
|---|---|---|
| Library adapters (AR+NAR pairs) | **16** | style + 15 pron merges (`{3050,4575,6100}` × α 0.1–0.5); all unlistened |
| Fused source adapters (ai-toolkit) | **2 families** | v2 style; pron AR-only r8 (ckpts 3050/4575/6100 pinned) |
| Experimental adapters (in scope, α≤0.5) | **1** | `c1525_a0.5` |
| Archived (α>0.5) | **4 configs** | `c3050_a0.55`, `c3050_a0.65`, `c3050_a1.0`, `cfinal_a1.0` |
| Objects in `loras/` | **36** | style 2 + pron 30 + source 4 (~2.72 GiB) |

## Library adapters (`loras/`, audio.cpp-loadable)

Loadable by `audiocpp_cli` via `yue2.ar_lora` / `yue2.nar_lora`, scale 1.0. The
**converted AR sha256 is the stable identity** (see caveats). Every pron merge shares
the same NAR — `7d9324bfabdfa806c600b12dfa1537501368f25a00d6f4aaf7252449414377c6`
(copied from v2, independent of α); the style adapter's NAR is `ad2c8d86…`.

| Config | Status | pron ckpt | α | AR rank | converted AR sha256 | Path in `loras/` |
|---|---|---:|---:|---:|---|---|
| style (`a0`) | base style | — | 0 | 32 | `747d5cfe2224b1bae6e582ccf5f2ee2a57e3f030c53d54e134f34a85960426fa` | `audio_cpp/style/` |
| `c3050_a0.1` | candidate (unlistened) | 3050 | 0.1 | 40 | `184bbd29b552751ded9849429a81f74165ccef13ff82d2befb2978efcbdcbb32` | `audio_cpp/pron/c3050_a0.1/` |
| `c3050_a0.2` | candidate (unlistened) | 3050 | 0.2 | 40 | `c68217ab619a9cfa992bbba650f03dd19616ea19fd0967060d0a45e9e415d34c` | `audio_cpp/pron/c3050_a0.2/` |
| `c3050_a0.3` | candidate (unlistened) | 3050 | 0.3 | 40 | `dd0d495924c3b533df2fe89cdb5ff82c5a708047c3e3b0bf6ccec42d6033c6e9` | `audio_cpp/pron/c3050_a0.3/` |
| `c3050_a0.4` | candidate (unlistened) | 3050 | 0.4 | 40 | `210daf9f1f042d13929fd3be48ebd24c9e76618ce0cf4ba1eb6e555d907c6218` | `audio_cpp/pron/c3050_a0.4/` |
| `c3050_a0.5` | candidate (unlistened) | 3050 | 0.5 | 40 | `33e824f24f1eec1ab06a45365e93a19b078a2a7cfbea724eba1b908d27360509` | `audio_cpp/pron/c3050_a0.5/` |
| `c4575_a0.1` | candidate (unlistened) | 4575 | 0.1 | 40 | `98d2d1e01dcd7ef0a6841163cf4ea9facc7780157e9efc781598d76cbff3e4fc` | `audio_cpp/pron/c4575_a0.1/` |
| `c4575_a0.2` | candidate (unlistened) | 4575 | 0.2 | 40 | `2327270db35ff9e28631bb47f2f381427e14752273d673a6f5fb7c8df1ef94e6` | `audio_cpp/pron/c4575_a0.2/` |
| `c4575_a0.3` | candidate (unlistened) | 4575 | 0.3 | 40 | `a3aa24ad27ad7bda51892b5acf760f47f379191f3239ec79637d5dd1058d9b14` | `audio_cpp/pron/c4575_a0.3/` |
| `c4575_a0.4` | candidate (unlistened) | 4575 | 0.4 | 40 | `dfdac71eaaa90da35795e171535be134ca3d96f7f1378d671a7d47c0fa8e6d9d` | `audio_cpp/pron/c4575_a0.4/` |
| `c4575_a0.5` | candidate (unlistened) | 4575 | 0.5 | 40 | `ebd22026495125e74ab48373ad0ce8a8d767cdb625e018affc38c24b1fc3e56d` | `audio_cpp/pron/c4575_a0.5/` |
| `cfinal_a0.1` | candidate (unlistened) | 6100 | 0.1 | 40 | `cebe662eab01faba193dc5781656f9f64ce02d5332c4d5505079a51d03619bb2` | `audio_cpp/pron/cfinal_a0.1/` |
| `cfinal_a0.2` | candidate (unlistened) | 6100 | 0.2 | 40 | `0c14b7ba4daae1e665b9c1f43d05c0b9abe90a8e983dbe64c38c4b7da6b2cabe` | `audio_cpp/pron/cfinal_a0.2/` |
| `cfinal_a0.3` | candidate (unlistened) | 6100 | 0.3 | 40 | `1c99a1c951acbf1662c5bb3e31f66ec0472dba17c8000ba1fa054a4e6c2e90ec` | `audio_cpp/pron/cfinal_a0.3/` |
| `cfinal_a0.4` | candidate (unlistened) | 6100 | 0.4 | 40 | `d149360f88108f57a9861fbeace29786057f106eee016a22e0d22e376601c57f` | `audio_cpp/pron/cfinal_a0.4/` |
| `cfinal_a0.5` | candidate (unlistened) | 6100 | 0.5 | 40 | `525d3af25dfcddabbd587673c36dfaecd148cf97a0dfc6d90cbede15ed700ada` | `audio_cpp/pron/cfinal_a0.5/` |

The full 15-cell grid was completed 2026-09-26 from the pinned `loras/source/` inputs
with `merge_pron_lora.py` + the converter. Independent reproductions matched the
earlier records exactly where they overlapped: `c3050_a0.2` `c68217ab…`,
`c4575_a0.5` `ebd22026…`, `cfinal_a0.5` `525d3af2…` — same data, same pipeline.

## Fused source adapters (`loras/source/`)

Inputs to `merge_pron_lora.py`. These pinned snapshots (plus the run prefixes) rebuild
the grid; training runs keep the full numbered checkpoint sets.

| Adapter | Rank | sha256 | Path |
|---|---|---:|---|
| v2 style (AR+NAR, final step 3000) | 32 | `b1d090987355303129a3765d257e61c983b91d48cecb8a30aa424e09cdd24cd4` | `loras/source/akbar_arabic_rock_lora.safetensors` (+ 11 numbered checkpoints in `akbar_arabic_rock_lora/output/`) |
| pron AR-only r8, ckpt 3050 | 8 | `ead30d5202dec368838304546d5400ce46e4a2da713a19a9236781f575178a21` | `loras/source/pron_lora_ar_only_r8_000003050.safetensors` |
| pron AR-only r8, ckpt 4575 | 8 | `c78bb5b6ea5abf551a209529bdee4e1b0f5d1ea87f14c3373b2165b1325ea201` | `loras/source/pron_lora_ar_only_r8_000004575.safetensors` |
| pron AR-only r8, ckpt 6100 (final) | 8 | `0d506719af3b8d5fc7af8dc211baf2767b169d7596d9239f4a2850a4d2d37bf5` | `loras/source/pron_lora_ar_only_r8.safetensors` |

(pron ckpt 1525 `9d8333d9…` stays un-pinned in `pron_lora_ar_only_r8/output/` — not in
the grid.)

## Experimental adapters (in scope, α≤0.5 — NOT the library)

| Config | pron ckpt | α | converted AR sha256 | Where |
|---|---|---:|---|---|
| `c1525_a0.5` | 1525 | 0.5 | `3324b63706a3a58ea89159250850a3bcab1fbcb851abcaffb7ae0d9d260f534c` | `audiocpp_inference/pron_ckpt_sweep/` |

(`t08`/`t10` temperature rounds reuse library configs — no new adapters.)

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
- `c3050_a0.4`'s Task-19 sidecar/record is in the unpushed bundle; its binaries are
  canonical in `loras/` and the hash above is from the GCS object.
- **Retired:** the v1 style-only adapter (`akbar_arabic_rock_lora_v1_nolyrics_archived/`)
  is documented in `PROGRESS.md` as a GCS archive but is **absent** from the project
  prefix — no surviving copy.
- Not ours: `Mothersuperior/yue2-mothersuperior-realaudio-tokenizer-v4/nar_lora_joint_v4.pt`
  is a NAR LoRA used only if `merge_nar_lora` is set; not used or staged.

## How to stage an adapter

```bash
# style (the bootstrap default): loras/audio_cpp/style/ -> /content/converter/out/
# a library candidate, e.g. c4575_a0.3:
gsutil -m cp -r "$GCP_BACKUP_BASE/loras/audio_cpp/pron/c4575_a0.3" /content/converter/out/
# then run with explicit overrides (or let run_one.sh's defaults use the style pair):
LORA_AR=/content/converter/out/c4575_a0.3/akbar_arabic_rock_lora_ar.safetensors \
LORA_NAR=/content/converter/out/c4575_a0.3/akbar_arabic_rock_lora_nar.safetensors \
  bash INFERENCE/run_one.sh Hijaz <seed>
```
