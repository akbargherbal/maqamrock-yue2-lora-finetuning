# Offline merge: v2 (style) + pron (AR-only) LoRA

Task 15. How to combine the frozen v2 style adapter and the AR-only pronunciation
adapter into one fused LoRA, and the exact scaling convention this depends on.
Tool: `merge_pron_lora.py` (repo root). Converter: `converter/convert_aitoolkit_yue2_lora.py`
(canonical copy lives in GCS `audiocpp_inference/converter/`; locally
`/content/converter/out/`). CPU-only.

## Why a file merge, not a runtime flag

audio.cpp and ai-toolkit each load exactly **one** LoRA network per expert:
`yue2.ar_lora` / `yue2.nar_lora`, one file each, one scalar scale each. There is
no second slot for a YuE2 model. So combining v2's style adapter with the pron
adapter at a chosen alpha has to happen offline, before conversion — see
`yue2-gguf-lora-findings.md` and `FUTURE_PRONUNCIATION_LORA.md` §3. Do not try to
load two adapters at once in audio.cpp.

Because v2 is a combined adapter (AR **and** NAR) while pron is AR-only, the AR
weights overlap (the subsystem pron is meant to fix) and the NAR weights do not.
v2's NAR is copied through untouched; only the AR branch is merged.

## The exact ai-toolkit scaling convention (verified against source)

ai-toolkit composes a low-rank delta as `(alpha / rank) * (B @ A)`, where
`B = lora_up` and `A = lora_down`:

```
toolkit/network_mixins.py:419        scale = self.scale
toolkit/network_mixins.py:434        weight = weight + multiplier * (up_weight @ down_weight) * scale
```
(`up_weight = self.lora_up.weight.clone().float()`, line 378;
 `down_weight = self.lora_down.weight.clone().float()`, line 379.)

```
toolkit/lora_special.py:115-116      alpha = self.lora_dim if alpha is None or alpha == 0 else alpha
                                     self._set_runtime_scale(float(alpha) / self.lora_dim)
toolkit/network_mixins.py:184        self.scale = float(value)
toolkit/kohya_lora.py:237            return self.org_forward(x) + self.lora_up(self.lora_down(x)) * self.multiplier * self._runtime_scale
```

So a module's full delta is `multiplier * (alpha/rank) * (B @ A)`; the
`alpha/rank` scalar lives on the module and is **not saved** (`.alpha` keys are
dropped for non-LoKr networks, `toolkit/network_mixins.py:615`). Both inputs were
trained `alpha == rank` (v2 `linear/linear_alpha 32/32`; pron `8/8`), so each
saved file's effective delta is exactly `B @ A`.

The user dial (`--alpha`) is a new scalar. Since the merged fused file has no
alpha key and the converter applies no alpha/rank factor, the dial is **baked
into B_pron** — the up-projection, the side ai-toolkit applies its scale to
(`up(down(x)) * scale`): `(alpha * B_pron) @ A_pron == alpha * (B_pron @ A_pron)`.
A_pron is unchanged. Folding into A would be algebraically identical; B is chosen
to mirror ai-toolkit's convention.

Pinned clone: `ostris/ai-toolkit` @ `460c29ba9c6a7885da1ec2416925c2a40e4132b8`
(2026-09-23). Line numbers may drift; re-check if behavior looks different.

## Merge method — rank concatenation, no dense delta

For every AR key (`text_encoders.*`) present in v2 (rank 32):
`A_merged = cat([A_style, A_pron], dim=0)`, `B_merged = cat([B_style, alpha*B_pron], dim=1)`
→ rank 40. The dense `(out, in)` weight delta is never materialized.

- AR key sets must match exactly between v2 and pron; a mismatch is a hard error.
- pron must contain **no** `diffusion_model.*` key (AR-only scoping) — hard error.
- NAR keys (`diffusion_model.*`) are copied from v2, independent of alpha.

`merge_pron_lora.py` accepts `--pron-checkpoint {1525,3050,4575,final}`, so any of
the four pron artifacts can be swept later.

### One non-obvious constraint: the converter wants one uniform rank

The converter accumulates rank across **both** branches and refuses mixed ranks:

```
converter/convert_aitoolkit_yue2_lora.py:207-208
    if len(ranks) != 1:
        raise ConvertError(f"mixed LoRA ranks found: {sorted(ranks)}")
```

A merged file is AR rank 40 / NAR rank 32, so at alpha != 0 the NAR branch is
zero-padded to rank 40 (A: extra zero rows; B: extra zero columns). This is a
numerical no-op on the NAR delta and exists only to satisfy that guard. At
alpha == 0 no pron block is kept, both branches stay rank 32, and **no padding
happens** — which is what makes the alpha=0 output byte-identical to v2.

## CLI

```bash
cd /content/maqamrock-yue2-lora-finetuning
python merge_pron_lora.py --alpha 0.5 --pron-checkpoint final \
    --out output/merged/pron_a0.5_ckpt-final.safetensors
python converter/convert_aitoolkit_yue2_lora.py \
    output/merged/pron_a0.5_ckpt-final.safetensors --out-dir /content/converter/out/merged
```

Defaults: `--v2 /content/ai-toolkit/output/akbar_arabic_rock_lora/akbar_arabic_rock_lora.safetensors`,
`--pron-dir /content/ai-toolkit/output/pron_lora_ar_only_r8`, `--pron-checkpoint final`,
`--alpha 1.0`. Override `--v2` / `--pron` / `--pron-dir` for other layouts.
The output preserves v2's dtype (bf16) and metadata, adding `merge_*` provenance
keys (alpha, pron checkpoint/sha256, v2 sha256, ranks).

`output/` is git-ignored (merged files are ~117–147 MB, regenerable).

## Inputs (sha256 recomputed 2026-09-24, not copied from any doc)

Base: `gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/`
(note: **`OSTRIS_Arabic_Suno_Finetuning`**, not `OSTRIS_Suno_Finetuning`).

| File | sha256 |
|---|---|
| `akbar_arabic_rock_lora/output/akbar_arabic_rock_lora.safetensors` (v2, rank 32, AR+NAR) | `b1d090987355303129a3765d257e61c983b91d48cecb8a30aa424e09cdd24cd4` |
| `pron_lora_ar_only_r8/output/pron_lora_ar_only_r8.safetensors` (final, rank 8, AR-only) | `0d506719af3b8d5fc7af8dc211baf2767b169d7596d9239f4a2850a4d2d37bf5` |
| `…_000001525.safetensors` | `9d8333d95b592a06e4f8b48d4dc65276f661e0bd76848a06344422ba4e088a09` |
| `…_000003050.safetensors` | `ead30d5202dec368838304546d5400ce46e4a2da713a19a9236781f575178a21` |
| `…_000004575.safetensors` | `c78bb5b6ea5abf551a209529bdee4e1b0f5d1ea87f14c3373b2165b1325ea201` |
| converted v2 AR currently loaded by audio.cpp (`loras/audio_cpp/style/akbar_arabic_rock_lora_ar.safetensors`) | `747d5cfe2224b1bae6e582ccf5f2ee2a57e3f030c53d54e134f34a85960426fa` |
| converted v2 NAR (`…_nar.safetensors`) | `ad2c8d8690640e8fd8fea779b57bc2c7c887b93f2bb103bbcbfea056536d7ac9` |

v2 and pron each carry 448 / 224 tensors; the pron file has 224 `text_encoders.*`
and **0** `diffusion_model.*`.

## Verification (2026-09-24, CPU)

- **Re-verified live, session 11, 2026-09-24: PASS.** `pytest tests/test_merge_pron_lora.py -v -s`
  → `12 passed in 2.62s`; `test_alpha_zero_reproduces_live_converted_v2` ran (not skipped)
  and passed. Both staged converted-v2 inputs were hash-checked before the run and match
  the table above: AR `747d5cfe2224b1bae6e582ccf5f2ee2a57e3f030c53d54e134f34a85960426fa`,
  NAR `ad2c8d8690640e8fd8fea779b57bc2c7c887b93f2bb103bbcbfea056536d7ac9`.
- **alpha=0 invariant — PASS.** Merged tensors are byte-identical to v2 (all 448),
  no padding. Through the converter, the resulting `_ar`/`_nar` files reproduce
  the live converted v2 adapters' sha256 **exactly** when the merged input keeps
  v2's basename: `747d5cfe…` (AR) and `ad2c8d86…` (NAR). With a different merged
  filename the only difference is the converter's embedded `source_file`
  metadata; all 392 tensors and all tensor headers are still byte-identical.
- **alpha=1.0 — PASS.** All 224 AR tensors are rank 40 with the expected
  `(40, in)` / `(out, 40)` shapes; NAR zero-padded to rank 40 with the first 32
  rows/cols equal to v2. Numeric check on 4 sampled AR projections:
  `B@A == B_style@A_style + 1.0·B_pron@A_pron`. Converter accepts it.
- **alpha=0.5 / checkpoint 4575 — PASS** end-to-end.
- Counts per merge: **224 AR tensors merged (112 A + 112 B)**, **224 NAR passed
  through** (224 zero-padded when rank 40). File sizes: alpha=0 merged
  117,501,256 B → converted AR 69,771,136 B / NAR 69,772,704 B; alpha=1.0 merged
  146,861,544 B → converted AR 87,203,736 B / NAR 87,205,304 B.
- **Wall clock per merge+convert cycle: ~3.4–3.7 s** (merge ~3.0–3.3 s, convert
  ~0.35–0.41 s). An N-point alpha sweep is cheap and needs no batching.
- Unit tests: `tests/test_merge_pron_lora.py` (12 tests, CPU-only; the alpha=0
  end-to-end invariant runs when the real v2/pron/converter artifacts are staged
  and skips on a clean clone).

## Production merges

The shipped production merges are v2 + pron **checkpoint 3050**, `alpha` **0.5** (primary),
**0.3** (fallback) and **0.4** — built 2026-09-25. Records (manifest, one sidecar per output,
regeneration script) live in `results/pron_production_merge/`; the converted binaries are in
the canonical LoRA library under `<base>/loras/audio_cpp/pron/<cfg>/` (see
`docs/LORA_INVENTORY.md`), and the fused merge intermediates under
`<base>/pron_production_merge/merged/` (not committed: over GitHub's 100 MiB per-file limit,
and regenerable in <1 s). `regenerate.sh` reproduces the converted AR/NAR sha256 exactly.

**Hash caveat:** `safetensors 0.8.0` writes `__metadata__` in nondeterministic HashMap
order, so a merged file's whole-file sha256 is **not** reproducible run-to-run (the tensors
and parsed metadata are). Verify with the converted AR/NAR sha256 or the tensor digest, not
`merged_sha256`. Details: `DECISIONS.md` ("Merged file sha256 is NOT reproducible").
