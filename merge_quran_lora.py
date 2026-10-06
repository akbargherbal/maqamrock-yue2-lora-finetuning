#!/usr/bin/env python3
"""Offline rank-concatenation merge of the v2 (style) and quran (AR+NAR) YuE2 LoRAs.

Why this exists
---------------
`merge_pron_lora.py` merges an **AR-only** pronunciation donor into v2: it keeps
v2's NAR untouched and hard-errors on any `diffusion_model.*` key in the donor.
The current Quran pronunciation donor (`quran_ahh_r8`, the revised rank-32 run)
is **AR+NAR** — the run was retrained with `ignore_if_contains: []` precisely
because "the NAR flow + VAE render the actual articulation", so the letter
(makhraj) fix it is meant to sharpen lives in the NAR branch. Merging that donor
therefore has to fold BOTH branches.

This tool is that merge: for every AR *and* NAR key, concatenate the donor block
behind v2's along the rank dimension, scaled by `--alpha`. The dense (out x in)
weight delta is never materialized.

    A_merged = cat([A_v2, A_quran], dim=0)            # (rank_v2 + rank_quran, in)
    B_merged = cat([B_v2, alpha * B_quran], dim=1)    # (out, rank_v2 + rank_quran)

The alpha dial, scaling convention, rank padding, and alpha==0 invariant mirror
`merge_pron_lora.py`/`docs/PRON_LORA_MERGE.md`:
  - ai-toolkit composes the delta as `(alpha/rank) * (B @ A)` and applies the
    scalar to the up-projection, so alpha is folded into B_quran.
  - At alpha == 0 the donor contributes nothing: the output is v2 verbatim, both
    branches stay at v2's rank, and the converted AR/NAR are byte-identical to
    the live style adapter.
  - Both inputs here are the same rank (32), so no padding is needed; the merged
    rank is `rank_v2 + rank_quran`.

Usage
-----
    python merge_quran_lora.py --alpha 0.2 \
        --v2   /content/merge_src/v2/akbar_arabic_rock_lora.safetensors \
        --quran /content/merge_src/quran/quran_ahh_r8.safetensors \
        --out  /content/merged/qahh_a0.2.safetensors

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

DEFAULT_V2 = Path("/content/merge_src/v2/akbar_arabic_rock_lora.safetensors")
DEFAULT_QURAN = Path("/content/merge_src/quran/quran_ahh_r8.safetensors")


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
    return key[: -len(".weight")] if key.endswith(".weight") else key


def _ab(key):
    stem = _stem(key)
    if stem.endswith(".lora_A"):
        return "A"
    if stem.endswith(".lora_B"):
        return "B"
    return None


def _proj(key):
    stem = _stem(key)
    for suffix in (".lora_A", ".lora_B", ".alpha"):
        if stem.endswith(suffix):
            return stem[: -len(suffix)]
    return stem


def _validate(v2, quran):
    """Hard-fail on any structural surprise; return (ar_rank, nar_rank)."""
    v2_keys = {k for k in v2 if not k.endswith(".alpha")}
    q_keys = {k for k in quran if not k.endswith(".alpha")}
    if v2_keys != q_keys:
        only_v2 = sorted(v2_keys - q_keys)
        only_q = sorted(q_keys - v2_keys)
        raise MergeError(
            "key sets differ (must match exactly). "
            f"in v2 only ({len(only_v2)}): {only_v2[:5]}; "
            f"in quran only ({len(only_q)}): {only_q[:5]}"
        )

    ranks = {}
    for label, tensors in (("v2", v2), ("quran", quran)):
        for k, t in tensors.items():
            if _ab(k) != "A":
                continue
            base = _proj(k)
            b = tensors.get(base + ".lora_B.weight", tensors.get(base + ".lora_B"))
            if b is None:
                raise MergeError(f"{label}: {k} has no lora_B partner")
            if t.ndim != 2 or b.ndim != 2 or b.shape[1] != t.shape[0]:
                raise MergeError(f"{label}: {base} bad shapes A{tuple(t.shape)} B{tuple(b.shape)}")
            ranks[(label, base)] = int(t.shape[0])

    for label in ("v2", "quran"):
        for branch in (AR_PREFIX, NAR_PREFIX):
            rs = {r for (lb, base), r in ranks.items() if lb == label and base.startswith(branch)}
            if not rs:
                raise MergeError(f"{label} has no {branch} A/B pairs")
            if len(rs) != 1:
                raise MergeError(f"{label} {branch} has mixed ranks {sorted(rs)}")

    ar = {b: r for (lb, b), r in ranks.items() if lb == "v2" and b.startswith(AR_PREFIX)}
    nar = {b: r for (lb, b), r in ranks.items() if lb == "v2" and b.startswith(NAR_PREFIX)}
    return next(iter(set(ar.values()))), next(iter(set(nar.values())))


def merge(v2, quran, alpha):
    ar_rank, nar_rank = _validate(v2, quran)
    keep = alpha != 0.0
    merged = {}
    ar_merged = nar_merged = 0
    for key, t2 in v2.items():
        if key.endswith(".alpha"):
            continue  # ai-toolkit drops alpha on save; validated rank==alpha upstream
        tq = quran[key]
        side = _ab(key)
        if side is None:
            raise MergeError(f"unexpected key {key}")
        if not keep:
            merged[key] = t2
        elif side == "A":
            merged[key] = torch.cat([t2, tq.to(t2.dtype)], dim=0)
        else:  # B
            block = (tq.to(torch.float32) * alpha).to(t2.dtype)
            merged[key] = torch.cat([t2, block], dim=1)
        if key.startswith(AR_PREFIX):
            ar_merged += 1
        else:
            nar_merged += 1

    stats = {
        "v2_ar_rank": ar_rank,
        "v2_nar_rank": nar_rank,
        "quran_ar_rank": ar_rank,
        "quran_nar_rank": nar_rank,
        "out_ar_rank": ar_rank * (2 if keep else 1),
        "out_nar_rank": nar_rank * (2 if keep else 1),
        "quran_kept": keep,
        "ar_tensors_merged": ar_merged,
        "nar_tensors_merged": nar_merged,
    }
    return merged, stats


def build_metadata(v2_meta, alpha, quran_name, v2_sha, quran_sha, stats):
    meta = dict(v2_meta)
    meta.update({
        "merge_tool": "merge_quran_lora.py",
        "merge_kind": "rank_concat_ar+nar",
        "merge_alpha": repr(float(alpha)),
        "merge_quran": quran_name,
        "merge_quran_sha256": quran_sha,
        "merge_v2_sha256": v2_sha,
        "merge_ar_rank": str(stats["out_ar_rank"]),
        "merge_nar_rank": str(stats["out_nar_rank"]),
    })
    return meta


def run(v2_path, quran_path, alpha, out_path):
    v2_path, quran_path, out_path = Path(v2_path), Path(quran_path), Path(out_path)
    for p in (v2_path, quran_path):
        if not p.is_file():
            raise MergeError(f"input not found: {p}")
    t0 = time.perf_counter()
    v2, quran = load_file(str(v2_path)), load_file(str(quran_path))
    merged, stats = merge(v2, quran, alpha)
    meta = build_metadata(read_metadata(v2_path), alpha, quran_path.name,
                          sha256_file(v2_path), sha256_file(quran_path), stats)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    save_file(merged, str(out_path), metadata=meta)
    return stats, sha256_file(out_path), out_path.stat().st_size, time.perf_counter() - t0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--alpha", type=float, default=1.0,
                    help="quran adapter strength (0 disables it; folded into B_quran)")
    ap.add_argument("--v2", type=Path, default=DEFAULT_V2, help="v2 raw fused LoRA (AR+NAR)")
    ap.add_argument("--quran", type=Path, default=DEFAULT_QURAN, help="quran raw fused LoRA (AR+NAR)")
    ap.add_argument("--out", type=Path, required=True, help="output fused .safetensors")
    args = ap.parse_args(argv)
    try:
        stats, digest, size, elapsed = run(args.v2, args.quran, args.alpha, args.out)
    except MergeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    print(f"v2    : {args.v2}")
    print(f"quran : {args.quran}")
    print(f"alpha : {args.alpha}")
    print(
        "merge: AR rank {v2_ar_rank}+{quran_ar_rank} -> {out_ar_rank} "
        "({ar_tensors_merged} tensors); "
        "NAR rank {v2_nar_rank}+{quran_nar_rank} -> {out_nar_rank} "
        "({nar_tensors_merged} tensors)".format(**stats)
    )
    if not stats["quran_kept"]:
        print("alpha=0: quran contributes nothing -> output is v2 verbatim (rank unchanged)")
    print(f"out   : {args.out}  ({size} bytes, sha256 {digest})")
    print(f"time  : {elapsed:.2f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
