#!/usr/bin/env python3
"""
sample_pron_dataset.py
----------------------
Build a frozen random subsample of an existing pronunciation dataset laid out as
`<src>/{train,val,smoke}/<reciter>_<SSSAAA>_<simple|uthmani>.{mp3,txt}`.

Motivation: the full `quran_long_aya_dataset` (81,006 train pairs) has a latent
cache step that runs ~1.1 files/s on an L4 (~20 h), which does not fit a Colab
session. A ~10% subsample lands at the scale of the working reference run
(6,100 pairs) and caches in ~2 h. See docs/PRON_LORA_LONG_PLAN.md.

Sampling unit is the COMBO (one reciter x one aya), so each clip's byte-identical
`_simple` and `_uthmani` variants are kept together (the captions still differ).
The selection is seeded and written verbatim to `<out>/_sample_manifest.json` so
the subsample is locked and reproducible.

Only `train/` is subsampled; `val/` and `smoke/` are copied in full. Provenance
files (`selection_report.json`, `excluded_ayat.jsonl`) are copied too. ai-toolkit
artifacts (`.aitk_size.json`, `_latent_cache/`) and the `.bootstrap_complete`
marker are deliberately NOT copied -- the subset regenerates its own.

Usage
-----
    python sample_pron_dataset.py \
        --src /content/quran_long_aya_dataset \
        --out /content/quran_long_aya_dataset_s10 \
        --fraction 0.10 --seed 20260927

    python sample_pron_dataset.py --src ... --out ... --dry-run
"""
from __future__ import annotations

import argparse
import json
import random
import shutil
import sys
from pathlib import Path

VARIANTS = ("simple", "uthmani")
ANCILLARY = ("selection_report.json", "excluded_ayat.jsonl")
SKIP_NAMES = ("_latent_cache", ".aitk_size.json", ".bootstrap_complete")


def combos(train_dir: Path) -> list[str]:
    return sorted(p.name[: -len("_simple.mp3")] for p in train_dir.glob("*_simple.mp3"))


def copy_file(src: Path, dst: Path, link: bool) -> int:
    if not src.is_file():
        return 0
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        dst.unlink()
    except FileNotFoundError:
        pass
    if link:
        import os

        os.link(src, dst)
    else:
        shutil.copy2(src, dst)
    return src.stat().st_size


def copy_split(src_dir: Path, dst_dir: Path, link: bool) -> tuple[int, int]:
    n = 0
    size = 0
    for p in src_dir.iterdir():
        if p.name in SKIP_NAMES or p.is_dir():
            continue
        size += copy_file(p, dst_dir / p.name, link)
        n += 1
    return n, size


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", required=True, type=Path, help="existing dataset root")
    ap.add_argument("--out", required=True, type=Path, help="new subsampled dataset root")
    ap.add_argument("--fraction", type=float, default=0.10, help="fraction of train COMBOS (default 0.10)")
    ap.add_argument("--seed", type=int, default=20260927, help="RNG seed for reproducible selection")
    ap.add_argument("--link", action="store_true", help="hardlink instead of copy (same filesystem only)")
    ap.add_argument("--dry-run", action="store_true", help="report the selection without writing anything")
    args = ap.parse_args()

    src, out = args.src, args.out
    for split in ("train", "val", "smoke"):
        if not (src / split).is_dir():
            print(f"[FAIL] {src/split} not found", file=sys.stderr)
            return 1
    if out.exists() and any(out.iterdir()) and not args.dry_run:
        print(f"[FAIL] {out} exists and is non-empty; refusing to overwrite", file=sys.stderr)
        return 1

    all_combos = combos(src / "train")
    n = round(len(all_combos) * args.fraction)
    rng = random.Random(args.seed)
    selected = sorted(rng.sample(all_combos, n))

    ayat = {s.rsplit("_", 1)[1] for s in selected}
    reciters: dict[str, int] = {}
    for s in selected:
        reciters[s.rsplit("_", 1)[0]] = reciters.get(s.rsplit("_", 1)[0], 0) + 1

    print(f"source train combos : {len(all_combos)}")
    print(f"fraction / seed     : {args.fraction} / {args.seed}")
    print(f"selected combos     : {n}  -> {n*2} train pairs")
    print(f"distinct ayat       : {len(ayat)} (of {len({c.rsplit('_',1)[1] for c in all_combos})})")
    print(f"reciters            : {len(reciters)}")

    if args.dry_run:
        print("[dry-run] nothing written")
        return 0

    sizes = {"train": 0, "val": 0, "smoke": 0}
    counts = {}
    for stem in selected:
        for variant in VARIANTS:
            for ext in ("mp3", "txt"):
                f = f"{stem}_{variant}.{ext}"
                sizes["train"] += copy_file(src / "train" / f, out / "train" / f, args.link)
    train_files = 2 * 2 * n
    for split in ("val", "smoke"):
        cnt, sz = copy_split(src / split, out / split, args.link)
        counts[split] = cnt
        sizes[split] = sz
    counts["train"] = train_files
    for name in ANCILLARY:
        if (src / name).is_file():
            copy_file(src / name, out / name, args.link)

    manifest = {
        "source": str(src),
        "seed": args.seed,
        "fraction": args.fraction,
        "unit": "combo (reciter x aya; both _simple/_uthmani variants kept together)",
        "source_train_combos": len(all_combos),
        "selected_combos": n,
        "train_files": train_files,
        "train_pairs": n * 2,
        "distinct_ayat": len(ayat),
        "reciter_counts": dict(sorted(reciters.items())),
        "counts": counts,
        "sizes_bytes": sizes,
        "combos": selected,
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "_sample_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"wrote {out} -> train_pairs={n*2} val_files={counts['val']} smoke_files={counts['smoke']}")
    print(f"manifest: {out/'_sample_manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
