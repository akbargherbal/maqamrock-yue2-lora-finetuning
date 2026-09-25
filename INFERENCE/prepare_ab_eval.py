#!/usr/bin/env python3
"""Prepare a blinded A/B (or A/B/C/...) audio listening package.

Given a tree of rendered variants, this copies/encodes the audio into one flat
folder with **blinded labels** and writes two files:

    EVAL.txt   evaluator-facing instructions -- contains NO mapping.
    KEYS.txt   the secret decoder (blind file -> variant), open AFTER listening.

The public/secret split is the point: `EVAL.txt` + the audio can be handed to an
evaluator; `KEYS.txt` stays with whoever set the test up.

Source layout (either is fine; arbitrary nesting of categories is supported):

    <root>/<category>/<variant>/<track>.<ext>     # category groups comparable tracks
    <root>/<variant>/<track>.<ext>                # flat: one implicit category ""

Example:

    root/
      KurdStyle_HijazLyrics/
        a0/Hijaz_20260924.wav
        c3050_a0.5/Hijaz_20260924.wav
      HijazStyle_KurdLyrics/
        a0/Kurd_20260924.wav
        c3050_a0.5/Kurd_20260924.wav

becomes a flat package like:

    out/
      EVAL.txt
      KEYS.txt
      Hijaz_20260924_A.wav
      Hijaz_20260924_B.wav
      Kurd_20260924_A.wav
      Kurd_20260924_B.wav

Generic over scenarios: the variants are whatever leaf folders you point it at
(alpha/checkpoint/knob/baseline-vs-candidate), and the label -> variant mapping
is the only thing recorded. Nothing here assumes the `a0` / `c<ckpt>_a<alpha>`
naming of the pronunciation sweeps.

Reproducibility: `--seed` fixes the shuffle. With the default
`--shuffle-per category`, one `random.Random(seed)` walks the categories in
sorted order and gives each category a single consistent variant -> label map,
so "A" means the same variant for every track in a category (the repo's sweep
convention). `--shuffle-per pair` re-shuffles per matched pair instead.

Audio: `--audio-format copy` (default) byte-copies and keeps each file's
extension; `wav` / `mp3` re-encode via ffmpeg with NO trim/normalize/fade
(`mp3` defaults to `--bitrate 192k`), matching the review packages under
`PRON_*_INPUT/`.
"""
from __future__ import annotations

import argparse
import json
import random
import re
import shutil
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_EXTS = (".wav", ".mp3", ".flac", ".m4a", ".ogg")
LABEL_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def is_relative_to_dir(path: Path, base_dir: Path) -> bool:
    """True if `path` is inside `base_dir` (resolving symlinks)."""
    try:
        path.resolve().relative_to(base_dir.resolve())
        return True
    except ValueError:
        return False


def _slug(text: str) -> str:
    return re.sub(r"[^\w\-_.]", "_", text).strip("_") or "category"


def _ffmpeg_convert(src: Path, dst: Path, fmt: str, bitrate: str) -> None:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg is required for --audio-format wav/mp3")
    cmd = ["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-i", str(src)]
    if fmt == "mp3":
        cmd += ["-codec:a", "libmp3lame", "-b:a", bitrate]
    else:  # wav
        cmd += ["-codec:a", "pcm_s16le"]
    cmd += ["-vn", str(dst)]
    subprocess.run(cmd, check=True)


def _discover(root: Path, output_dir: Path, exts: tuple[str, ...]) -> list[dict]:
    """Every audio file under `root` (excluding `output_dir`), with its
    category + variant derived from the directory layout."""
    root = root.resolve()
    out: list[dict] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in exts:
            continue
        if is_relative_to_dir(path, output_dir):
            continue
        variant_dir = path.parent
        rel_parent = variant_dir.parent.resolve().relative_to(root)
        category = "" if rel_parent == Path(".") else rel_parent.as_posix()
        out.append({
            "path": path,
            "category": category,
            "variant": variant_dir.name,
            "stem": path.stem,
        })
    return out


def _select_variants(found: list[dict], requested: list[str] | None) -> list[str]:
    detected = sorted({f["variant"] for f in found})
    if requested:
        missing = [v for v in requested if v not in detected]
        if missing:
            raise ValueError(
                f"variant(s) not found under the root: {missing}; detected: {detected}"
            )
        if len(requested) < 2:
            raise ValueError(f"need at least 2 variants to compare, got: {requested}")
        return list(requested)
    if len(detected) < 2:
        raise ValueError(
            f"expected at least 2 variants across folders, found {len(detected)}: "
            f"{detected}. Pass --variants to choose."
        )
    return detected


def _group_pairs(found: list[dict], variants: list[str],
                 categories: list[str] | None) -> list[dict]:
    """Groups keyed by (category, stem); keeps only groups complete across all
    selected variants. Returns (groups, skipped)."""
    tracks: dict[tuple[str, str], dict[str, Path]] = defaultdict(dict)
    for f in found:
        if f["variant"] not in variants:
            continue
        if categories and f["category"] not in categories:
            continue
        tracks[(f["category"], f["stem"])][f["variant"]] = f["path"]

    groups, skipped = [], []
    for (category, stem), vmap in tracks.items():
        missing = [v for v in variants if v not in vmap]
        if missing:
            skipped.append((category, stem, missing))
        else:
            groups.append({"category": category, "stem": stem, "variants": vmap})
    groups.sort(key=lambda g: (g["category"], g["stem"]))
    return groups, skipped


def _label_maps(groups: list[dict], variants: list[str], labels: str,
                seed: int | None, shuffle_per: str) -> dict:
    """variant -> label maps, keyed by category (default) or (category, stem)."""
    if len(labels) < len(variants):
        raise ValueError(f"need >= {len(variants)} labels, got {labels!r}")
    rng = random.Random(seed)

    def shuffled_map() -> dict:
        order = list(variants)
        rng.shuffle(order)
        return {v: labels[i] for i, v in enumerate(order)}

    maps: dict = {}
    if shuffle_per == "category":
        for category in sorted({g["category"] for g in groups}):
            maps[category] = shuffled_map()
    else:  # pair
        for g in groups:
            maps[(g["category"], g["stem"])] = shuffled_map()
    return maps


def setup_ab_evaluation(
    root_dir: Path,
    output_dir: Path,
    variants: list[str] | None = None,
    seed: int | None = None,
    *,
    categories: list[str] | None = None,
    labels: str = LABEL_ALPHABET,
    extensions: tuple[str, ...] = DEFAULT_EXTS,
    audio_format: str = "copy",
    bitrate: str = "192k",
    shuffle_per: str = "category",
    title: str | None = None,
    notes: dict[str, str] | None = None,
    json_path: Path | None = None,
    dry_run: bool = False,
) -> dict:
    root_dir = Path(root_dir).resolve()
    output_dir = Path(output_dir).resolve()
    notes = notes or {}

    if not root_dir.is_dir():
        raise FileNotFoundError(f"root directory does not exist: {root_dir}")

    found = _discover(root_dir, output_dir, tuple(e.lower() for e in extensions))
    if not found:
        raise FileNotFoundError(
            f"no audio files ({', '.join(extensions)}) found under {root_dir}"
        )

    selected = _select_variants(found, variants)
    groups, skipped = _group_pairs(found, selected, categories)
    for category, stem, missing in skipped:
        where = category or "."
        print(f"[!] skipping incomplete pair '{stem}' in '{where}' (missing: {missing})")
    if not groups:
        raise FileNotFoundError(
            f"no track is present in all variants {selected}"
        )

    label_maps = _label_maps(groups, selected, labels, seed, shuffle_per)
    dup_stems = len({g["stem"] for g in groups}) != len(groups)

    def label_for(g: dict, variant: str) -> str:
        key = g["category"] if shuffle_per == "category" else (g["category"], g["stem"])
        return label_maps[key][variant]

    print(f"[*] root            : {root_dir}")
    print(f"[*] output          : {output_dir}")
    print(f"[*] variants        : {' vs '.join(selected)}")
    print(f"[*] tracks (pairs)  : {len(groups)}")
    print(f"[*] shuffle per     : {shuffle_per}  (seed={seed})")
    print(f"[*] audio format    : {audio_format}")
    print()

    records = []
    if not dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)

    for g in groups:
        stem = g["stem"]
        if dup_stems and g["category"]:
            base = f"{_slug(g['category'])}_{stem}"
        else:
            base = stem
        for variant in selected:
            label = label_for(g, variant)
            src = g["variants"][variant]
            ext = src.suffix.lower()
            if audio_format == "copy":
                dest = output_dir / f"{base}_{label}{ext}"
            else:
                dest = output_dir / f"{base}_{label}.{audio_format}"
            if not dry_run:
                if audio_format == "copy":
                    shutil.copy2(src, dest)
                else:
                    _ffmpeg_convert(src, dest, audio_format, bitrate)
            records.append({
                "category": g["category"] or "-",
                "blind_file": dest.name,
                "label": label,
                "variant": variant,
                "source_path": str(src.relative_to(root_dir)),
            })
            print(f"  -> {dest.name}   ({variant})")

    records.sort(key=lambda r: (r["category"], r["blind_file"]))
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    heading = title or "A/B BLIND AUDIO EVALUATION"

    if not dry_run:
        _write_keys(output_dir / "KEYS.txt", records, selected, seed,
                    shuffle_per, heading, generated, notes)
        _write_eval(output_dir / "EVAL.txt", records, selected, heading, generated)
        if json_path is not None:
            json_path = Path(json_path)
            json_path.parent.mkdir(parents=True, exist_ok=True)
            json_path.write_text(json.dumps({
                "generated": generated,
                "seed": seed,
                "shuffle_per": shuffle_per,
                "variants": selected,
                "audio_format": audio_format,
                "pairs": records,
                "labels": _variant_label_summary(label_maps, shuffle_per),
            }, indent=2) + "\n", encoding="utf-8")

    print(f"\n[ok] {len(records)} blinded files"
          f"{' (dry-run: nothing written)' if dry_run else f' -> {output_dir}'}")
    return {
        "output_dir": str(output_dir),
        "variants": selected,
        "records": records,
        "label_maps": label_maps,
    }


def _variant_label_summary(label_maps: dict, shuffle_per: str) -> dict:
    if shuffle_per == "category":
        return {cat: m for cat, m in label_maps.items()}
    return {f"{cat}/{stem}": m for (cat, stem), m in label_maps.items()}


def _write_keys(path: Path, records: list[dict], variants: list[str],
                seed: int | None, shuffle_per: str, heading: str,
                generated: str, notes: dict[str, str]) -> None:
    col_file = max([len(r["blind_file"]) for r in records] + [len("Blind Filename")])
    col_cat = max([len(r["category"]) for r in records] + [len("Category")])
    col_var = max([len(r["variant"]) for r in records] + [len("Variant")])
    col_note = max([len(notes.get(v, "")) for v in variants] + [0])
    show_note = col_note > 0

    def row(fn: str, cat: str, var: str, note: str = "") -> str:
        line = f"{fn:<{col_file}} | {cat:<{col_cat}} | {var:<{col_var}}"
        if show_note:
            line += f" | {note:<{col_note}}"
        return line

    width = len(row("Blind Filename", "Category", "Variant",
                    "Note" if show_note else ""))
    div, sub = "=" * width, "-" * width

    lines = [
        div,
        heading.center(width),
        "SECRET DECODER KEY — open only AFTER listening".center(width),
        f"Generated: {generated}".center(width),
        div,
        f"seed={seed}  shuffle_per={shuffle_per}  "
        f"variants={', '.join(variants)}",
        sub,
        row("Blind Filename", "Category", "Variant", "Note" if show_note else ""),
        sub,
    ]
    for r in records:
        lines.append(row(r["blind_file"], r["category"], r["variant"],
                         notes.get(r["variant"], "")))
    lines += [
        div,
        "",
        "DECODE: match the label the evaluator preferred for a track against the",
        "'Variant' column above.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")

    # per-variant legend (helps when a variant name is terse)
    if notes:
        lines = ["VARIANT LEGEND"]
        for v in variants:
            if notes.get(v):
                lines.append(f"  {v} = {notes[v]}")
        with path.open("a", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")


def _write_eval(path: Path, records: list[dict], variants: list[str],
                heading: str, generated: str) -> None:
    labels = sorted({r["label"] for r in records})
    n_tracks = len({(r["category"], r["blind_file"].rsplit("_", 1)[0]) for r in records})
    lines = [
        heading,
        f"Generated: {generated}",
        "",
        "You are evaluating audio blind. For each track you have one file per",
        f"label ({', '.join(labels)}), differing in configuration but with the labels",
        "randomly assigned. There is no quality key here on purpose.",
        "",
        "HOW TO EVALUATE",
        f"1. Listen to all {n_tracks} track(s); within each, compare "
        f"{' vs '.join(labels)}.",
        "2. For each track pick a preference (a label, or 'tie'), a confidence",
        "   (low/medium/high), and one or two concrete observations (e.g.",
        "   pronunciation, timbre, arrangement, artifacts).",
        "3. Do not try to infer which label is the 'baseline' -- labels are",
        "   shuffled independently per category.",
        "4. Return a table: track | preferred label | confidence | notes.",
        "",
        "Send back only that table; the organizer decodes it.",
        "",
        f"Files: {len(records)} audio file(s), {n_tracks} track(s).",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Randomize audio into a blinded A/B(/N) evaluation package.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--root", type=Path, default=Path("."),
                   help="root containing <category>/<variant>/<track>.<ext> "
                        "(default: current directory)")
    p.add_argument("--output", type=Path, default=Path("ab_eval"),
                   help="output package folder (default: ./ab_eval)")
    p.add_argument("--variants", nargs="+", default=None,
                   help="the variant folder names to compare (2+; default: all detected)")
    p.add_argument("--categories", nargs="+", default=None,
                   help="restrict to these category folders (default: all)")
    p.add_argument("--seed", type=int, default=None,
                   help="seed for reproducible label shuffling")
    p.add_argument("--labels", default=LABEL_ALPHABET,
                   help="label alphabet, one per variant (default: A B C ...)")
    p.add_argument("--shuffle-per", choices=("category", "pair"), default="category",
                   help="keep labels consistent within a category (default) or "
                        "re-shuffle each matched pair")
    p.add_argument("--extensions", nargs="+", default=list(DEFAULT_EXTS),
                   help=f"audio extensions to pick up (default: {' '.join(DEFAULT_EXTS)})")
    p.add_argument("--audio-format", choices=("copy", "wav", "mp3"), default="copy",
                   help="copy bytes as-is (default) or re-encode via ffmpeg (no "
                        "trim/normalize)")
    p.add_argument("--bitrate", default="192k",
                   help="mp3 bitrate for --audio-format mp3 (default: 192k)")
    p.add_argument("--title", default=None, help="heading for EVAL.txt / KEYS.txt")
    p.add_argument("--note", action="append", default=[], metavar="VARIANT=TEXT",
                   help="human note for a variant, added to KEYS.txt's legend "
                        "(repeatable)")
    p.add_argument("--json", type=Path, default=None,
                   help="also write a machine-readable mapping JSON here")
    p.add_argument("--dry-run", action="store_true",
                   help="discover + print the plan, write nothing")
    return p


def _parse_notes(items: list[str]) -> dict[str, str]:
    notes: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise SystemExit(f"--note expects VARIANT=TEXT, got {item!r}")
        key, _, value = item.partition("=")
        notes[key.strip()] = value.strip()
    return notes


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        setup_ab_evaluation(
            args.root, args.output, args.variants, args.seed,
            categories=args.categories, labels=args.labels,
            extensions=tuple(args.extensions), audio_format=args.audio_format,
            bitrate=args.bitrate, shuffle_per=args.shuffle_per,
            title=args.title, notes=_parse_notes(args.note),
            json_path=args.json, dry_run=args.dry_run,
        )
    except (FileNotFoundError, ValueError, RuntimeError, subprocess.CalledProcessError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
