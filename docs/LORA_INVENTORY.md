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
    pron/                          # EMPTY since 2026-10-07 (qfinal_a0.* retired)
  source/                          # fused ai-toolkit finals the merges are built from

# Current pron donor + merges (NOT in loras/):
<GCP_BACKUP_BASE>/quran_ahh_r32/maqamrock_merge/{merged,convert/qahh_a0*}/   # v2 x quran_ahh_r32 (rank 32, AR+NAR)
```

Sweep/prototype adapters are **not** here — they stay under their round's prefix and
are clearly non-canonical (`audiocpp_inference/…_sweep/`, `pron_*_sweep/`, etc.).
Local paths under `/content/` are ephemeral and re-staged by `bootstrap/setup.sh`
each VM.

**2026-10-07 — the long-aya Quran donor was retired.** The 9-reciter `quran_long_aya_r8_s10`
run and its two `qfinal_a0.3`/`qfinal_a0.5` merges (the prior "current candidates") were
moved to **`<base>/archive/quran_long_aya_legacy/`** and removed from the live paths. The
current pronunciation donor is **`quran_ahh_r32`** (rank 32, AR+NAR; AHH-filtered 3 reciters,
9,489 pairs) → merges `qahh_a0*` under `<base>/quran_ahh_r32/maqamrock_merge/`.
(Earlier, 2026-09-27: the `pron_lora_ar_only_r8` family was archived to
`<base>/archive/pron_lora_ar_only_legacy/`.)

## Counts

| Class | Count | Notes |
|---|---|---|
| Current library adapters (AR+NAR pairs) | **1** | style only; `qfinal_a0.*` removed 2026-10-07 |
| Fused source adapter pinned in `loras/source/` | **1** | v2 style only |
| Current pron merges (NOT in `loras/`) | **4** | `qahh_a0/a0p1/a0p2/a0p3` under `<base>/quran_ahh_r32/maqamrock_merge/`; unlistened |
| Superseded — `pron_lora_ar_only_r8` family (archived) | **15 merges + 3 source pins** | `archive/pron_lora_ar_only_legacy/` |
| Superseded — long-aya donor + `qfinal_a*` (archived) | **2 runs + 2 merges** | `archive/quran_long_aya_legacy/` |
| Experimental adapters (in scope, α≤0.5) | **1** | `c1525_a0.5` |
| Archived (α>0.5) | **4 configs** | `c3050_a0.55`, `c3050_a0.65`, `c3050_a1.0`, `cfinal_a1.0` |
| Objects in `loras/` | **3** | style 2 + source 1 |

## Current library adapters (`loras/`, audio.cpp-loadable)

Only the **style** adapter is in the library now; `audio_cpp/pron/` is **empty** (its
`qfinal_a0.*` were retired 2026-10-07). Loadable by `audiocpp_cli` via `yue2.ar_lora` /
`yue2.nar_lora`, scale 1.0. The **converted AR sha256 is the stable identity** (see caveats).

| Config | Status | pron donor | α | AR rank | converted AR sha256 | Path in `loras/` |
|---|---|---:|---:|---:|---|---|
| style (`a0`) | base style | — | 0 | 32 | `747d5cfe2224b1bae6e582ccf5f2ee2a57e3f030c53d54e134f34a85960426fa` | `audio_cpp/style/` |
| **v3 style** | v3 final (step 5000; 438-track, verbatim lyrics) | — | 0 | 32 | `3531bb9106d2292eefe58eabe11ec08bb7dddc69554f2b016dc9f13f711fab18` | `v3_arabmaqamrock_lora/convert/` (**not** promoted into `loras/`) |

## Current pron merges (`<base>/quran_ahh_r32/maqamrock_merge/`, NOT in `loras/`)

The live candidates are the `qahh_a0*` merges of v2 + **`quran_ahh_r32`** (rank 32, AR+NAR)
at α 0 / 0.1 / 0.2 / 0.3 — see `INFERENCE/jarir_lever_probe.sh`, `results/jarir_qahh/README.md`.
Converted AR/NAR live under
`<base>/quran_ahh_r32/maqamrock_merge/convert/qahh_a0{,,p1,p2,p3}/`. **Unlistened** — no
adapter is "best" before the listen.

## Superseded — `pron_lora_ar_only_r8` donor family

The AR-only pronunciation LoRA trained on the Quran-recitation set
(`pron_lora_ar_only_r8`, 6100/6100) and its 15 merged adapters are **no longer current**:
the donor was taken over by the long-aya Quran run (`quran_long_aya_r8_s10`). Archived
2026-09-27 (md5-verified, original paths preserved):

```
<base>/archive/pron_lora_ar_only_legacy/
  loras/audio_cpp/pron/{c3050,c4575,cfinal}_a0.{1..5}/   # 15 dirs / 30 files
  loras/source/pron_lora_ar_only_r8{,_000003050,_000004575}.safetensors   # 3 pins
<base>/pron_lora_ar_only_r8_obsolete/                     # renamed run prefix (was pron_lora_ar_only_r8/)
```

Kept for identity (the hashes are stable; the paths above are the archive):

| Config | pron ckpt | α | converted AR sha256 |
|---|---:|---:|---|
| `c3050_a0.1` | 3050 | 0.1 | `184bbd29b552751ded9849429a81f74165ccef13ff82d2befb2978efcbdcbb32` |
| `c3050_a0.2` | 3050 | 0.2 | `c68217ab619a9cfa992bbba650f03dd19616ea19fd0967060d0a45e9e415d34c` |
| `c3050_a0.3` | 3050 | 0.3 | `dd0d495924c3b533df2fe89cdb5ff82c5a708047c3e3b0bf6ccec42d6033c6e9` |
| `c3050_a0.4` | 3050 | 0.4 | `210daf9f1f042d13929fd3be48ebd24c9e76618ce0cf4ba1eb6e555d907c6218` |
| `c3050_a0.5` | 3050 | 0.5 | `33e824f24f1eec1ab06a45365e93a19b078a2a7cfbea724eba1b908d27360509` |
| `c4575_a0.1` | 4575 | 0.1 | `98d2d1e01dcd7ef0a6841163cf4ea9facc7780157e9efc781598d76cbff3e4fc` |
| `c4575_a0.2` | 4575 | 0.2 | `2327270db35ff9e28631bb47f2f381427e14752273d673a6f5fb7c8df1ef94e6` |
| `c4575_a0.3` | 4575 | 0.3 | `a3aa24ad27ad7bda51892b5acf760f47f379191f3239ec79637d5dd1058d9b14` |
| `c4575_a0.4` | 4575 | 0.4 | `dfdac71eaaa90da35795e171535be134ca3d96f7f1378d671a7d47c0fa8e6d9d` |
| `c4575_a0.5` | 4575 | 0.5 | `ebd22026495125e74ab48373ad0ce8a8d767cdb625e018affc38c24b1fc3e56d` |
| `cfinal_a0.1` | 6100 | 0.1 | `cebe662eab01faba193dc5781656f9f64ce02d5332c4d5505079a51d03619bb2` |
| `cfinal_a0.2` | 6100 | 0.2 | `0c14b7ba4daae1e665b9c1f43d05c0b9abe90a8e983dbe64c38c4b7da6b2cabe` |
| `cfinal_a0.3` | 6100 | 0.3 | `1c99a1c951acbf1662c5bb3e31f66ec0472dba17c8000ba1fa054a4e6c2e90ec` |
| `cfinal_a0.4` | 6100 | 0.4 | `d149360f88108f57a9861fbeace29786057f106eee016a22e0d22e376601c57f` |
| `cfinal_a0.5` | 6100 | 0.5 | `525d3af25dfcddabbd587673c36dfaecd148cf97a0dfc6d90cbede15ed700ada` |

The full 15-cell grid was completed 2026-09-26 from the then-pinned `loras/source/` inputs
with `merge_pron_lora.py` + the converter; independent reproductions matched the earlier
records exactly where they overlapped (`c3050_a0.2` `c68217ab…`, `c4575_a0.5` `ebd22026…`,
`cfinal_a0.5` `525d3af2…`). `c3050_a0.4`'s Task-19 sidecar/record is in an unpushed bundle;
its hash above is from the GCS object.

## Superseded — long-aya Quran donor (`quran_long_aya_r8_s10`) + `qfinal_a*`

Retired **2026-10-07**; archived (copy-verified, originals removed) to
`<base>/archive/quran_long_aya_legacy/{quran_long_aya_r8_s10,quran_long_aya_r8,loras/audio_cpp/pron/qfinal_a0.3,qfinal_a0.5}/`.
The 9-reciter donor is superseded by `quran_ahh_r32`. Identity (stable, for the record):

| Config | pron donor (ckpt) | α | converted AR sha256 |
|---|---|---:|---|
| `qfinal_a0.3` | `quran_long_aya_r8_s10` final (8100) | 0.3 | `0169e5a0ef7d47349bc707c10b3fbf5d937f941e3d28896e9970f0dc3894bdf6` |
| `qfinal_a0.5` | `quran_long_aya_r8_s10` final (8100) | 0.5 | `3a06265f33854825309f1cb10ab4ca5c36acf8692491186321b58c867eca90d2` |

## Fused source adapters (`loras/source/`)

Inputs to `merge_pron_lora.py`. These pinned snapshots (plus the run prefixes) rebuild
an adapter; training runs keep the full numbered checkpoint sets.

| Adapter | Rank | sha256 | Path |
|---|---|---:|---|
| v2 style (AR+NAR, final step 3000) | 32 | `b1d090987355303129a3765d257e61c983b91d48cecb8a30aa424e09cdd24cd4` | `loras/source/akbar_arabic_rock_lora.safetensors` (+ 11 numbered checkpoints in `akbar_arabic_rock_lora/output/`) |

The three `pron_lora_ar_only_r8` pins (ckpts 3050 `ead30d52…`, 4575 `c78bb5b6…`, 6100
`0d506719…`) are **archived** — see "Superseded" above. The `quran_long_aya_r8_s10` final
is **not** pinned in `loras/source/`; it lives in its run prefix
(`<base>/quran_long_aya_r8_s10/output/`, sha256 `f8c842e4…`). pron ckpt 1525
(`9d8333d9…`) stays un-pinned in the obsolete run prefix — not in any grid.

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
- **Retired:** the v1 style-only adapter (`akbar_arabic_rock_lora_v1_nolyrics_archived/`)
  is documented in `PROGRESS.md` as a GCS archive but is **absent** from the project
  prefix — no surviving copy.
- Not ours: `Mothersuperior/yue2-mothersuperior-realaudio-tokenizer-v4/nar_lora_joint_v4.pt`
  is a NAR LoRA used only if `merge_nar_lora` is set; not used or staged.

## How to stage an adapter

```bash
# style (the bootstrap default): loras/audio_cpp/style/ -> /content/converter/out/
# a current candidate, e.g. qahh_a0p1 (v2 x quran_ahh_r32, α0.1):
gcloud storage rsync -r "$GCP_BACKUP_BASE/quran_ahh_r32/maqamrock_merge/convert/qahh_a0p1" /content/converter/out/qahh_a0p1
# then run with explicit overrides (or let run_one.sh's defaults use the style pair):
LORA_AR=/content/converter/out/qahh_a0p1/akbar_arabic_rock_lora_ar.safetensors \
LORA_NAR=/content/converter/out/qahh_a0p1/akbar_arabic_rock_lora_nar.safetensors \
  bash INFERENCE/run_one.sh Hijaz <seed>
```
