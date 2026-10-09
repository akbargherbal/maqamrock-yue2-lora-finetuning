#!/usr/bin/env python3
"""
prepare_ahh_quran_dataset.py
----------------------------
Build the YuE2 pronunciation dataset from the quality-filtered AHH Quran
recitation set, pairing each clip with Tanzil text (Uthmani/Simple).

Design (locked 2026-10-04, docs/QURAN_PRON_REVIEW.md):
  * Source: AHH_Quran_Long_Aya_Filtered_DATASET (9,492 clips, 3 reciters, flat
    layout <reciter>_<SSSAAA>.mp3).
  * SINGLE caption per clip, 50/50 simple/uthmani, stratified per reciter, so the
    orthography never correlates with the voice (unlike the old build, which
    wrote both variants per combo).
  * Held-out aya (default 2:255, Ayat al-Kursi) goes to val/ and is never trained.
  * 4-line caption template, aya line ending in ' \u06dd':
        <style>
        [Lyrics]
        [Verse]
        <aya text> \u06dd
  * Word-count gate is kept for parity with the long-aya plan (min 6 / max 60
    words); on the AHH set it is a no-op (0 clips outside the range).

Inputs
    --audio-root   flat dir of <reciter>_<SSSAAA>.mp3
    quran-simple.json / quran-uthmani.json   (Tanzil, NFC, no embedded \u06dd)

Output
    <out>/train/<reciter>_<SSSAAA>_<script>.{mp3,txt}
    <out>/val/...   <out>/smoke/...
    <out>/selection_report.json   <out>/captions_manifest.jsonl

Usage
    python prepare_ahh_quran_dataset.py --audio-root /content/AHH_Quran_Long_Aya_Filtered_DATASET \
        --simple quran_text/quran-simple.json --uthmani quran_text/quran-uthmani.json \
        --out /content/quran_ahh_dataset --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

AYAH_SIGN = "\u06dd"
AYAH_LINE_SUFFIX = " " + AYAH_SIGN

AUDIO_RE = re.compile(r"^(?P<reciter>.+)_(?P<key>\d{6})$")

DEFAULT_STYLE = (
    "Solo male voice, unaccompanied. Quran recitation in murattal style. "
    "Classical Arabic with tajw\u012bd, precise articulation. Spoken Words."
)


@dataclass
class Config:
    audio_root: Path
    simple: Path
    uthmani: Path
    out: Path
    style: str = DEFAULT_STYLE
    min_words: int = 6
    max_words: int = 60
    seed: int = 20261004
    jobs: int = 12
    link_mode: str = "hardlink"
    val_ayat: list[str] = field(default_factory=lambda: ["002255"])
    smoke_ayat: list[str] = field(default_factory=list)
    val_both_scripts: bool = True
    dry_run: bool = False


def load_tanzil(path: Path) -> dict[str, str]:
    raw = re.sub(r"^\s*(var\s+\w+\s*=\s*)?", "", path.read_text(encoding="utf-8")).rstrip().rstrip(";")
    data = json.loads(raw)
    if isinstance(data, dict):
        for v in data.values():
            if isinstance(v, list):
                data = v
                break
    out: dict[str, str] = {}
    for row in data:
        if not isinstance(row, dict):
            continue
        try:
            sura = int(row.get("sura") or row.get("surah") or row.get("chapter"))
            aya = int(row.get("aya") or row.get("ayah") or row.get("verse"))
        except (TypeError, ValueError):
            continue
        text = (row.get("text") or row.get("aya_text") or "").strip()
        if text:
            out[f"{sura:03d}{aya:03d}"] = text
    if not out:
        raise SystemExit(f"no ayat parsed from {path}")
    return out


def word_count(text: str) -> int:
    return len(text.replace(AYAH_SIGN, "").split())


def make_caption(style: str, aya_text: str) -> str:
    return f"{style}\n[Lyrics]\n[Verse]\n{aya_text}{AYAH_LINE_SUFFIX}\n"


def discover_audio(audio_root: Path):
    index: dict[tuple[str, str], Path] = {}
    bad: list[str] = []
    for p in sorted(audio_root.glob("*.mp3")):
        m = AUDIO_RE.match(p.stem)
        if not m:
            bad.append(p.name)
            continue
        index.setdefault((m.group("reciter"), m.group("key")), p)
    return index, bad


def split_scripts(keys: list[str], seed: int) -> dict[str, str]:
    """Stratified 50/50 assignment: exactly half simple, half uthmani."""
    ks = sorted(keys)
    rng = random.Random(seed)
    rng.shuffle(ks)
    half = len(ks) // 2
    return {k: ("simple" if i < half else "uthmani") for i, k in enumerate(ks)}


def build(cfg: Config) -> int:
    simple = load_tanzil(cfg.simple)
    uthmani = load_tanzil(cfg.uthmani)
    audio, bad_names = discover_audio(cfg.audio_root)

    reciters = sorted({r for (r, _) in audio})
    val_set, smoke_set = set(cfg.val_ayat), set(cfg.smoke_ayat)

    chosen: dict[str, str] = {}
    missing_text: set[str] = set()
    out_of_range: set[str] = set()
    for (_, key) in audio:
        text = simple.get(key) or uthmani.get(key)
        if not text:
            missing_text.add(key)
            continue
        if cfg.min_words <= word_count(text) <= cfg.max_words:
            chosen[key] = text
        else:
            out_of_range.add(key)

    train: list[tuple[str, str, str]] = []
    val: list[tuple[str, str, str]] = []
    smoke: list[tuple[str, str, str]] = []
    per_reciter: dict[str, dict] = {}

    for reciter in reciters:
        keys = [k for (r, k) in audio if r == reciter and k in chosen]
        train_keys = [k for k in keys if k not in val_set and k not in smoke_set]
        assigns = split_scripts(train_keys, cfg.seed)
        simple_n = sum(v == "simple" for v in assigns.values())
        per_reciter[reciter] = {
            "clips": len(keys),
            "train": len(train_keys),
            "simple": simple_n,
            "uthmani": len(train_keys) - simple_n,
        }
        for k in train_keys:
            train.append((reciter, k, assigns[k]))
        for k in keys:
            if k in val_set:
                scripts = ["simple", "uthmani"] if cfg.val_both_scripts else [assigns.get(k, "simple")]
                for s in scripts:
                    val.append((reciter, k, s))
            elif k in smoke_set:
                smoke.append((reciter, k, "simple"))

    counts = {
        "train": len(train),
        "val": len(val),
        "smoke": len(smoke),
        "distinct_train_ayat": len({k for _, k, _ in train}),
        "reciters": len(reciters),
    }
    report = {
        "params": {
            "audio_root": str(cfg.audio_root), "simple": str(cfg.simple),
            "uthmani": str(cfg.uthmani), "out": str(cfg.out), "style": cfg.style,
            "min_words": cfg.min_words, "max_words": cfg.max_words,
            "seed": cfg.seed, "link_mode": cfg.link_mode,
            "val_ayat": cfg.val_ayat, "smoke_ayat": cfg.smoke_ayat,
            "val_both_scripts": cfg.val_both_scripts, "dry_run": cfg.dry_run,
        },
        "source_files": len(audio) + len(bad_names),
        "source_parsed": len(audio),
        "unnamed_files": bad_names,
        "ayat_missing_tanzil": sorted(missing_text),
        "ayat_out_of_word_range": sorted(out_of_range),
        "reciters": per_reciter,
        "counts": counts,
        "val_ayat": sorted({k for _, k, _ in val}),
        "smoke_ayat": sorted({k for _, k, _ in smoke}),
    }
    print(json.dumps({k: report[k] for k in (
        "source_parsed", "unnamed_files", "ayat_missing_tanzil",
        "reciters", "counts")}, indent=2, ensure_ascii=False))

    if cfg.dry_run:
        return 0

    for split in ("train", "val", "smoke"):
        (cfg.out / split).mkdir(parents=True, exist_ok=True)

    def link(src: Path, dst: Path) -> None:
        if dst.exists():
            dst.unlink()
        if cfg.link_mode == "hardlink":
            try:
                os.link(src, dst)
                return
            except OSError:
                pass
        elif cfg.link_mode == "symlink":
            os.symlink(src.resolve(), dst)
            return
        shutil.copy2(src, dst)

    def write_one(item: tuple[str, str, str]) -> dict:
        reciter, key, script = item
        if key in val_set:
            split = "val"
        elif key in smoke_set:
            split = "smoke"
        else:
            split = "train"
        src = audio[(reciter, key)]
        stem = f"{reciter}_{key}_{script}"
        link(src, cfg.out / split / (stem + ".mp3"))
        (cfg.out / split / (stem + ".txt")).write_text(
            make_caption(cfg.style, (simple if script == "simple" else uthmani)[key]),
            encoding="utf-8")
        return {"split": split, "reciter": reciter, "key": key, "script": script,
                "audio": src.name}

    rows: list[dict] = []
    with ThreadPoolExecutor(max_workers=cfg.jobs) as ex:
        rows = list(ex.map(write_one, train + val + smoke))

    with open(cfg.out / "captions_manifest.jsonl", "w", encoding="utf-8") as fh:
        for r in sorted(rows, key=lambda r: (r["split"], r["reciter"], r["key"], r["script"])):
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    (cfg.out / "selection_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote dataset to {cfg.out}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--audio-root", required=True, type=Path)
    ap.add_argument("--simple", required=True, type=Path)
    ap.add_argument("--uthmani", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--style", default=DEFAULT_STYLE)
    ap.add_argument("--min-words", type=int, default=6)
    ap.add_argument("--max-words", type=int, default=60)
    ap.add_argument("--seed", type=int, default=20261004)
    ap.add_argument("--jobs", type=int, default=12)
    ap.add_argument("--link-mode", choices=["hardlink", "copy", "symlink"], default="hardlink")
    ap.add_argument("--val-aya", action="append", dest="val_ayat", default=None)
    ap.add_argument("--smoke-aya", action="append", dest="smoke_ayat", default=None)
    ap.add_argument("--no-val-both-scripts", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    cfg = Config(
        audio_root=args.audio_root, simple=args.simple, uthmani=args.uthmani, out=args.out,
        style=args.style, min_words=args.min_words, max_words=args.max_words, seed=args.seed,
        jobs=args.jobs, link_mode=args.link_mode, dry_run=args.dry_run,
        val_both_scripts=not args.no_val_both_scripts,
    )
    if args.val_ayat:
        cfg.val_ayat = args.val_ayat
    if args.smoke_ayat:
        cfg.smoke_ayat = args.smoke_ayat
    return build(cfg)


if __name__ == "__main__":
    sys.exit(main())
