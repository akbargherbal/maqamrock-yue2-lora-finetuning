#!/usr/bin/env python3
"""Build an ai-toolkit-shaped fused LoRA whose AR branch is a pronunciation
adapter alone and whose NAR branch is all-zero.

Why this exists
---------------
`converter/convert_aitoolkit_yue2_lora.py` (the audio.cpp converter) requires
BOTH an AR and a NAR branch. Feeding it an AR-only adapter (a pron run is AR-only
by design: `network_kwargs.ignore_if_contains: ["transformer.nar"]`) fails with:

    ERROR: NAR branch: missing [...] (expected 28 layers x 4 modules)

To run a "pron-only" arm we therefore have to hand it a NAR branch. Making that
branch all-zero keeps the NAR delta a numerical no-op, i.e. the converted NAR is
"base NAR" (run it at scale 0, or leave it on -- a zero delta changes nothing).

This is the "Quran pron LoRA alone (alpha=1) on the base model" arm: since a
pron adapter is trained `alpha == rank`, its saved delta is already full strength,
so copying its AR tensors verbatim *is* alpha=1 -- no merge with the style LoRA
(which would re-introduce v2's AR and defeat the point). See
`docs/QURAN_ONLY_EXPERIMENT.md`.

What it does
------------
- AR (`text_encoders.*`): copied verbatim from `--pron` (rank R).
- NAR (`diffusion_model.*`): zero tensors at rank R, sized from `--v2`'s NAR
  shapes (only the key names/shapes are needed; the values are discarded).

CPU only.

Usage
-----
    python build_pron_only_fused.py \
        --pron /content/pron_src/quran_long_aya_r8_s10.safetensors \
        --v2   /content/v2_src/akbar_arabic_rock_lora.safetensors \
        --out  /content/quran_only_build/quran_long_aya_r8_s10_zeronar.safetensors

    python /content/converter/out/convert_aitoolkit_yue2_lora.py \
        /content/quran_only_build/quran_long_aya_r8_s10_zeronar.safetensors \
        --out-dir /content/converter/out/quran_only --stem quran_long_aya_r8_s10
"""
import argparse
import sys

import torch
from safetensors import safe_open
from safetensors.torch import load_file, save_file

AR_PREFIX = "text_encoders."
NAR_PREFIX = "diffusion_model."


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--pron", required=True, help="AR-only pron .safetensors (rank R)")
    ap.add_argument("--v2", required=True,
                    help="fused v2 style .safetensors, for NAR key names/shapes")
    ap.add_argument("--out", required=True, help="output fused .safetensors")
    args = ap.parse_args(argv)

    pron = load_file(args.pron)
    if any(k.startswith(NAR_PREFIX) for k in pron):
        print("ERROR: pron has NAR keys -- not an AR-only adapter", file=sys.stderr)
        return 2
    v2 = load_file(args.v2)

    pron_rank = next((int(t.shape[0]) for k, t in pron.items()
                      if k.startswith(AR_PREFIX) and k.endswith(".lora_A.weight")), None)
    if pron_rank is None:
        print("ERROR: pron has no AR lora_A tensors", file=sys.stderr)
        return 2

    out = dict(pron)  # AR verbatim
    nar_bases = sorted({k.rsplit(".lora_", 1)[0] for k in v2 if k.startswith(NAR_PREFIX)})
    if not nar_bases:
        print("ERROR: v2 has no NAR keys to size the zero branch from", file=sys.stderr)
        return 2
    for base in nar_bases:
        a = v2[base + ".lora_A.weight"]
        b = v2[base + ".lora_B.weight"]
        out[base + ".lora_A.weight"] = torch.zeros((pron_rank, a.shape[1]), dtype=a.dtype)
        out[base + ".lora_B.weight"] = torch.zeros((b.shape[0], pron_rank), dtype=b.dtype)

    with safe_open(args.pron, framework="pt") as f:
        meta = dict(f.metadata() or {})
    meta["build"] = "pron-only fused: AR=pron verbatim, NAR=zeros(rank R)"
    save_file(out, args.out, metadata=meta)
    print(f"wrote {args.out}: AR {sum(k.startswith(AR_PREFIX) for k in out)} tensors, "
          f"NAR {sum(k.startswith(NAR_PREFIX) for k in out)} zero tensors, rank {pron_rank}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
