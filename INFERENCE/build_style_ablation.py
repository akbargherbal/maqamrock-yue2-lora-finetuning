#!/usr/bin/env python3
"""Build a style-only ablation ladder (L0-L4) for one worked track.

The style text is the only variable; **lyrics are copied byte-for-byte** from the
source track, so a render at one fixed seed isolates the style string. The ladder
comes from `agent_notes/current.md` (2026-09-28 decision):

    L0  raw Suno block, verbatim (control -- what we send today)
    L1  trained flat shape, every clause (build_caption: genre+maqam+vocals+
        production+instrumentation+mood)
    L2  L1 - target constants   (drop vocals, instrumentation -- the redundancy rule)
    L3  L1 - anti-target constants (drop genre, production -- the truth rule)
    L4  minimal: `arabmaqamrock Maqam <M>. Mood: <mood>.`

L2 and L3 are each a single removal from L1 (not cumulative); L4 is the floor.
The `arabmaqamrock` trigger is present in every level (L3/L4 spell it in; the
others carry it inside genre), so `generate.py` never doubles it.

Usage:
    python INFERENCE/build_style_ablation.py --dry-run          # print the ladder
    python INFERENCE/build_style_ablation.py                    # write the manifest
    python INFERENCE/build_style_ablation.py \
        --source manifests/batch_36_songs.json --track الحر \
        --maqam Ajam --seed 298970020 --lora qfinal_a0.3 \
        -o manifests/style_ablation_ajam.json

Output is `{"loras", "defaults", "songs": [{name, style, lyrics, lora, seed, cap}]}`
plus a `<out>.report.json` recording every level's full style text (for the blind
A/B keys) and the source track's provenance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

INFERENCE_DIR = Path(__file__).resolve().parent
REPO_ROOT = INFERENCE_DIR.parent
for _p in (str(INFERENCE_DIR), str(REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import generate as gen  # noqa: E402
import prepare_yue2_dataset as pyd  # noqa: E402

DEFAULT_SOURCE = REPO_ROOT / "manifests" / "batch_36_songs.json"
DEFAULT_TRACK = "07-الحر-الشديد-وقطع-القفر-والوعول"
DEFAULT_MAQAM = "Ajam"
DEFAULT_SEED = 298970020
DEFAULT_LORA_DIR = "/content/converter/out"
LEVELS = ("l0_raw", "l1_full", "l2_target_off", "l3_anti_off", "l4_min")


def select_track(source: Path, title: str, index: int) -> tuple[dict, dict]:
    data = json.loads(source.read_text(encoding="utf-8"))
    songs = data.get("songs")
    gen.check(isinstance(songs, list) and songs, f"{source}: 'songs' must be a non-empty array")
    matches = [s for s in songs if title in str(s.get("name", ""))]
    gen.check(matches, f"{source}: no song name contains {title!r}")
    gen.check(index < len(matches), f"{source}: only {len(matches)} match {title!r}")
    return data, matches[index]


def build_levels(style: str, maqam: str) -> dict[str, str]:
    fields = pyd.parse_fields(style)
    gen.check(fields, "source track has no parseable genre/vocals/... block")
    g = fields.get("genre", "")
    voc, prod, ins = fields.get("vocals", ""), fields.get("production", ""), fields.get("instrumentation", "")
    mood = fields.get("mood", "")
    head = f"{g} Maqam {maqam}."
    mood_part = f"Mood: {mood}."
    trigger = gen.TRIGGER.strip()
    return {
        "l0_raw": style.strip(),
        "l1_full": " ".join(p for p in (head, voc, prod, ins, mood_part) if p.strip()),
        "l2_target_off": " ".join(p for p in (head, prod, mood_part) if p.strip()),
        "l3_anti_off": " ".join(p for p in (f"{trigger} Maqam {maqam}.", voc, ins, mood_part) if p.strip()),
        "l4_min": f"{trigger} Maqam {maqam}. {mood_part}",
    }


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="build_style_ablation.py",
        description="Build the L0-L4 style-only ablation ladder for one worked track "
                    "(lyrics verbatim; one fixed seed).",
    )
    p.add_argument("--source", type=Path, default=DEFAULT_SOURCE,
                   help=f"source songs manifest (default: {DEFAULT_SOURCE.name})")
    p.add_argument("--track", default=DEFAULT_TRACK, help="substring of the source song name")
    p.add_argument("--entry", type=int, default=0, help="which match to use when several share a name")
    p.add_argument("--maqam", default=DEFAULT_MAQAM, help="maqam for the style tag")
    p.add_argument("--seed", type=int, default=DEFAULT_SEED, help="fixed seed for every level")
    p.add_argument("--lora", default="qfinal_a0.3", help="lora alias into the output 'loras' registry")
    p.add_argument("--lora-dir", default=DEFAULT_LORA_DIR,
                   help="directory holding akbar_arabic_rock_lora_{ar,nar}.safetensors")
    p.add_argument("--quantile", type=float, default=0.95, choices=gen.QUANTILES,
                   help="cap quantile used to derive the shared cap from the lyrics")
    p.add_argument("-o", "--out", type=Path, default=None,
                   help="output manifest (default: manifests/style_ablation_<maqam>.json)")
    p.add_argument("--dry-run", action="store_true", help="print the ladder; write nothing")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        gen.check(args.source.is_file(), f"source not found: {args.source}")
        _, track = select_track(args.source, args.track, args.entry)
        lyrics = track.get("lyrics", "")
        gen.check(lyrics.strip(), "source track has no lyrics")
        n_letters = gen.arabic_letters(lyrics)
        cap = gen.duration_cap(n_letters, args.quantile)[2]

        levels = build_levels(str(track.get("style", "")), args.maqam)
        for name, style in levels.items():
            gen.check(style.strip(), f"level {name} is empty")
            gen.check(gen.TRIGGER.strip() in style, f"level {name} is missing the trigger")

        out_path = args.out or (REPO_ROOT / "manifests" / f"style_ablation_{args.maqam.lower()}.json")
        doc = {
            "loras": {args.lora: {"dir": args.lora_dir}},
            "defaults": {"lora": args.lora},
            "songs": [
                {"name": name, "style": levels[name], "lyrics": lyrics,
                 "seed": args.seed, "cap": cap}
                for name in LEVELS
            ],
        }
        gen.resolve_songs(doc, out_path.parent, trigger=True, loras=gen.resolve_loras(doc, out_path.parent))

        if args.dry_run:
            print(f"style ablation: {len(LEVELS)} levels, seed={args.seed}, cap={cap} "
                  f"(q{args.quantile}, {n_letters} ar letters), lora={args.lora}")
            for name in LEVELS:
                print(f"\n[{name}]\n{levels[name]}")
            print(f"\nout: {out_path}   [dry-run: nothing written]")
            return 0

        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        report = {
            "generated_at": gen.utcnow(),
            "source": str(args.source),
            "source_track": str(track.get("name", "")),
            "source_lora": str(track.get("lora", "")),
            "maqam": args.maqam,
            "seed": args.seed,
            "quantile": args.quantile,
            "cap": cap,
            "arabic_letters": n_letters,
            "lyrics_sha256": hashlib.sha256(lyrics.encode("utf-8")).hexdigest(),
            "levels": levels,
        }
        report_path = out_path.with_name(out_path.stem + ".report.json")
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {out_path} ({len(LEVELS)} levels, seed={args.seed}, cap={cap})")
        print(f"report: {report_path}")
        return 0
    except gen.PlanError as e:
        print(f"[error] {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
