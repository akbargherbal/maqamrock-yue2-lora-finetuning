#!/usr/bin/env python3
"""Offline rank-concatenation merge of the v2 (style) and pron (AR-only) YuE2 LoRAs.

Why this exists
---------------
ai-toolkit and audio.cpp both load exactly ONE LoRA network per expert
(`yue2.ar_lora` / `yue2.nar_lora`, one file + one scalar scale). Stacking the
v2 style adapter and the pronunciation adapter at inference is therefore not a
runtime flag -- it has to be done offline, producing one fused ai-toolkit-shaped
LoRA that `converter/convert_aitoolkit_yue2_lora.py` can split into the two
unfused adapters audio.cpp loads. See `docs/PRON_LORA_MERGE.md`.

What it does
------------
For every AR key (`text_encoders.*`) present in v2:
    (A_style, B_style) rank 32   +   (A_pron, B_pron) rank 8
        -> concatenate along the rank dimension -> rank 40.
The user's `--alpha` dial is folded into pron's **B** (the up-projection), the
side ai-toolkit applies its scale to (see SCALING below).
For every NAR key (`diffusion_model.*`): copy v2 through. The pron adapter is
AR-only (verified on load: any `diffusion_model.*` key in it is a hard error).

The dense (out x in) weight delta is never materialized: the LoRA stays in
low-rank (A, B) form throughout.

SCALING -- the exact ai-toolkit convention (verified against source)
-------------------------------------------------------------------
ai-toolkit composes a LoRA delta as `B @ A` scaled by `alpha / rank`:

    toolkit/network_mixins.py:419,434
        scale = self.scale
        ...
        weight = weight + multiplier * (up_weight @ down_weight) * scale
    # up_weight = lora_up.weight = B, down_weight = lora_down.weight = A

    toolkit/lora_special.py:115-116
        alpha = self.lora_dim if alpha is None or alpha == 0 else alpha
        self._set_runtime_scale(float(alpha) / self.lora_dim)   # self.scale

    toolkit/kohya_lora.py:237 (forward, same convention)
        return self.org_forward(x) + self.lora_up(self.lora_down(x)) * self.multiplier * self._runtime_scale

So `dW = (alpha/rank) * (B @ A)`. Both input files were trained alpha == rank
(v2 32/32, pron 8/8), so each saved adapter's delta is exactly `B @ A`. The
merged file has no alpha key, and `multiplier` is a runtime thing, so the user
dial has to be baked into a tensor. ai-toolkit applies the scalar to the
**up-projection output** (`up(down(x)) * scale`), so we fold it into B:
`(alpha * B_pron) @ A_pron == alpha * (B_pron @ A_pron)`.

Rank padding (why NAR can grow)
-------------------------------
The converter enforces a SINGLE rank across both branches
(`converter/convert_aitoolkit_yue2_lora.py`, `convert()`: `if len(ranks) != 1:
raise "mixed LoRA ranks found"`). A merged file has AR rank 40 but v2's NAR rank
32, so NAR is padded with zero rows/cols (A: zero rows to ar_rank; B: zero
columns to ar_rank) purely to satisfy that guard. The padding contributes
nothing to the NAR delta, so it is numerically a no-op. At alpha == 0 no pron
block is kept, both branches stay rank 32, and no padding happens -- that is
what makes the alpha=0 output byte-identical to v2 through the converter.

Usage
-----
    python merge_pron_lora.py --alpha 0.5 --pron-checkpoint final \
        --out output/merged/pron_a0.5_ckpt-final.safetensors

CPU only; never selects an accelerator device.
"""
import argparse
import hashlib
import sys
import time
from pathlib import Path

import torch
from safetensors import safe_open
from safetensors.torch import load_file, save_file

AR_PREFIX = "text_encoders."
NAR_PREFIX = "diffusion_model."

# --pron-checkpoint value -> file name inside --pron-dir
PRON_CHECKPOINTS = {
    "1525": "pron_lora_ar_only_r8_000001525.safetensors",
    "3050": "pron_lora_ar_only_r8_000003050.safetensors",
    "4575": "pron_lora_ar_only_r8_000004575.safetensors",
    "final": "pron_lora_ar_only_r8.safetensors",
}

# Canonical local layout of the two runs (mirrors the GCS output/ prefixes).
DEFAULT_V2 = Path(
    "/content/ai-toolkit/output/akbar_arabic_rock_lora/akbar_arabic_rock_lora.safetensors"
)
DEFAULT_PRON_DIR = Path("/content/ai-toolkit/output/pron_lora_ar_only_r8")


class MergeError(Exception):
    pass


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_metadata(path) -> dict:
    with safe_open(str(path), framework="pt") as f:
        return dict(f.metadata() or {})


def _stem(key):
    """Drop the optional safetensors '.weight' suffix."""
    return key[: -len(".weight")] if key.endswith(".weight") else key


def _ab(key):
    """'A'/'B' for a ...lora_A[.weight] key, else None."""
    stem = _stem(key)
    if stem.endswith(".lora_A"):
        return "A"
    if stem.endswith(".lora_B"):
        return "B"
    return None


def _proj(key):
    """Projection base, e.g. 'diffusion_model.model.layers.0.mlp.down_proj'."""
    stem = _stem(key)
    for suffix in (".lora_A", ".lora_B", ".alpha"):
        if stem.endswith(suffix):
            return stem[: -len(suffix)]
    return stem


def _check_alpha_keys(tensors, label):
    """ai-toolkit drops alpha on save; if a stray one is present it must equal rank.

    Mirrors the converter's rule: the saved file only encodes a correct delta if
    alpha == rank (no alpha/rank factor is applied downstream).
    """
    alphas = {k: tensors[k] for k in tensors if k.endswith(".alpha")}
    if not alphas:
        return
    ranks = {_proj(k): int(tensors[k].shape[0]) for k in tensors if _ab(k) == "A"}
    for k, v in alphas.items():
        r = ranks.get(_proj(k))
        val = float(v.reshape(-1)[0]) if v.numel() else float("nan")
        if r is None or abs(val - r) > 1e-6 * max(1.0, r):
            raise MergeError(
                f"{label}: alpha key {k}={val} != rank {r}; refusing (the "
                "converter applies no alpha/rank factor)."
            )


def _rank_of_a(tensors, label):
    """Return {base: rank} for every A tensor, checking A/B shape agreement."""
    out = {}
    for k, t in tensors.items():
        if _ab(k) != "A":
            continue
        if t.ndim != 2:
            raise MergeError(f"{label}: {k} is not rank-2 (shape {tuple(t.shape)})")
        base = _proj(k)
        b = tensors.get(base + ".lora_B.weight", tensors.get(base + ".lora_B"))
        if b is None:
            raise MergeError(f"{label}: {k} has no lora_B partner")
        if b.ndim != 2 or b.shape[1] != t.shape[0]:
            raise MergeError(
                f"{label}: {base} rank mismatch A{tuple(t.shape)} B{tuple(b.shape)}"
            )
        out[base] = int(t.shape[0])
    return out


def _validate_inputs(v2, pron):
    """Hard-fail on any structural surprise; return (ar_rank, pron_rank)."""
    pron_non_ar = sorted(k for k in pron if not k.startswith(AR_PREFIX))
    if pron_non_ar:
        raise MergeError(
            "pron adapter is not AR-only -- unexpected non-text_encoders keys "
            f"({len(pron_non_ar)}): {pron_non_ar[:5]}"
        )

    # `.alpha` keys are stripped by ai-toolkit on save; ignore any stray ones for
    # the key-set comparison and validate them separately below.
    v2_ar = {k for k in v2 if k.startswith(AR_PREFIX) and not k.endswith(".alpha")}
    pron_ar = {k for k in pron if k.startswith(AR_PREFIX) and not k.endswith(".alpha")}
    if v2_ar != pron_ar:
        only_v2 = sorted(v2_ar - pron_ar)
        only_pron = sorted(pron_ar - v2_ar)
        raise MergeError(
            "AR key sets differ (must match exactly). "
            f"in v2 only ({len(only_v2)}): {only_v2[:5]}; "
            f"in pron only ({len(only_pron)}): {only_pron[:5]}"
        )

    unknown = sorted(
        k for k in v2 if not (k.startswith(AR_PREFIX) or k.startswith(NAR_PREFIX))
    )
    if unknown:
        raise MergeError(
            f"v2 has keys under neither text_encoders nor diffusion_model: {unknown[:5]}"
        )
    if not v2_ar:
        raise MergeError("v2 has no text_encoders (AR) keys")

    _check_alpha_keys(v2, "v2")
    _check_alpha_keys(pron, "pron")

    vr = _rank_of_a(v2, "v2")
    pr = _rank_of_a(pron, "pron")
    if not vr:
        raise MergeError("v2 has no AR A/B pairs")
    if not pr:
        raise MergeError("pron has no AR A/B pairs")
    ar_ranks = set(vr.values())
    if len(ar_ranks) != 1:
        raise MergeError(f"v2 AR has mixed ranks {sorted(ar_ranks)}")
    pron_ranks = set(pr.values())
    if len(pron_ranks) != 1:
        raise MergeError(f"pron AR has mixed ranks {sorted(pron_ranks)}")
    return ar_ranks.pop(), pron_ranks.pop()


def merge(v2, pron, alpha):
    """Return (tensors_in_v2_order, stats) for the rank-concatenated fused LoRA."""
    style_rank, pron_rank = _validate_inputs(v2, pron)
    keep_pron = alpha != 0.0

    # NAR is copied from v2; the converter needs one uniform rank, so when the
    # AR branch grew we pad NAR with zeros (a no-op on the delta).
    nar_ranks = _rank_of_a(
        {k: t for k, t in v2.items() if k.startswith(NAR_PREFIX)}, "v2-nar"
    )
    nar_rank = max(nar_ranks.values()) if nar_ranks else None
    target_ar_rank = style_rank + (pron_rank if keep_pron else 0)
    pad_nar = nar_rank is not None and nar_rank != target_ar_rank
    if pad_nar and nar_rank > target_ar_rank:
        raise MergeError(f"NAR rank {nar_rank} exceeds merged AR rank {target_ar_rank}")

    merged = {}
    ar_merged = nar_passed = nar_padded = 0
    for key, t2 in v2.items():
        if key.endswith(".alpha"):
            # ai-toolkit drops alpha on save; a valid one equals rank and is
            # checked in _validate_inputs, then ignored here.
            continue
        if key.startswith(AR_PREFIX):
            if key not in pron:
                raise MergeError(f"pron is missing AR key {key}")
            tp = pron[key]
            if _ab(key) == "A":
                if keep_pron:
                    merged[key] = torch.cat([t2, tp.to(t2.dtype)], dim=0)
                else:
                    merged[key] = t2
                ar_merged += 1
            elif _ab(key) == "B":
                if keep_pron:
                    block = (tp.to(torch.float32) * alpha).to(t2.dtype)
                    merged[key] = torch.cat([t2, block], dim=1)
                else:
                    merged[key] = t2
                ar_merged += 1
            else:
                raise MergeError(f"unexpected AR key {key}")
        elif key.startswith(NAR_PREFIX):
            if not pad_nar:
                merged[key] = t2
            elif _ab(key) == "A":
                pad = torch.zeros(
                    (target_ar_rank - t2.shape[0], t2.shape[1]), dtype=t2.dtype
                )
                merged[key] = torch.cat([t2, pad], dim=0)
                nar_padded += 1
            elif _ab(key) == "B":
                pad = torch.zeros(
                    (t2.shape[0], target_ar_rank - t2.shape[1]), dtype=t2.dtype
                )
                merged[key] = torch.cat([t2, pad], dim=1)
                nar_padded += 1
            else:
                raise MergeError(f"unexpected NAR key {key}")
            nar_passed += 1
        else:
            raise MergeError(f"unsupported key {key}")

    stats = {
        "style_rank": style_rank,
        "pron_rank": pron_rank,
        "ar_rank": target_ar_rank,
        "nar_rank": target_ar_rank if pad_nar else nar_rank,
        "pron_kept": keep_pron,
        "ar_tensors_merged": ar_merged,
        "nar_tensors_passed_through": nar_passed,
        "nar_tensors_zero_padded": nar_padded,
    }
    return merged, stats


def build_metadata(v2_meta, alpha, pron_name, v2_sha, pron_sha, stats):
    meta = dict(v2_meta)  # preserve v2's ai-toolkit conventions
    meta.update(
        {
            "merge_tool": "merge_pron_lora.py",
            "merge_kind": "rank_concat_ar_only",
            "merge_alpha": repr(float(alpha)),
            "merge_pron_checkpoint": pron_name,
            "merge_pron_sha256": pron_sha,
            "merge_v2_sha256": v2_sha,
            "merge_ar_rank": str(stats["ar_rank"]),
            "merge_nar_rank": str(stats["nar_rank"]),
        }
    )
    return meta


def run(v2_path, pron_path, alpha, out_path, pron_name):
    v2_path, pron_path, out_path = Path(v2_path), Path(pron_path), Path(out_path)
    for p in (v2_path, pron_path):
        if not p.is_file():
            raise MergeError(f"input not found: {p}")
    t0 = time.perf_counter()
    v2 = load_file(str(v2_path))
    pron = load_file(str(pron_path))
    merged, stats = merge(v2, pron, alpha)
    meta = build_metadata(
        read_metadata(v2_path),
        alpha,
        pron_name,
        sha256_file(v2_path),
        sha256_file(pron_path),
        stats,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    save_file(merged, str(out_path), metadata=meta)
    elapsed = time.perf_counter() - t0
    return stats, meta, sha256_file(out_path), out_path.stat().st_size, elapsed


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--alpha", type=float, default=1.0,
                    help="pronunciation adapter strength (0 disables it; folded into B_pron)")
    ap.add_argument("--pron-checkpoint", choices=list(PRON_CHECKPOINTS), default="final",
                    help="which pron checkpoint to merge (default: final)")
    ap.add_argument("--pron", type=Path, default=None,
                    help="explicit pron .safetensors (overrides --pron-dir/--pron-checkpoint)")
    ap.add_argument("--pron-dir", type=Path, default=DEFAULT_PRON_DIR,
                    help="directory holding the pron_lora_ar_only_r8*.safetensors files")
    ap.add_argument("--v2", type=Path, default=DEFAULT_V2, help="v2 raw fused LoRA")
    ap.add_argument("--out", type=Path, required=True, help="output fused .safetensors")
    args = ap.parse_args(argv)

    pron_path = args.pron or (args.pron_dir / PRON_CHECKPOINTS[args.pron_checkpoint])
    try:
        stats, _meta, digest, size, elapsed = run(
            args.v2, pron_path, args.alpha, args.out, pron_path.name
        )
    except MergeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    print(f"v2   : {args.v2}")
    print(f"pron : {pron_path}  (checkpoint {args.pron_checkpoint})")
    print(f"alpha: {args.alpha}")
    print(
        "merge: AR rank {style_rank}+{pron_rank} -> {ar_rank} "
        "({ar_tensors_merged} AR tensors), "
        "NAR {nar_tensors_passed_through} passed through"
        "{pad}".format(pad=(f", {stats['nar_tensors_zero_padded']} zero-padded to rank {stats['nar_rank']}"
                            if stats["nar_tensors_zero_padded"] else ""), **stats)
    )
    if not stats["pron_kept"]:
        print("alpha=0: pron contributes nothing -> output is v2 verbatim (rank unchanged)")
    print(f"out  : {args.out}  ({size} bytes, sha256 {digest})")
    print(f"time : {elapsed:.2f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
