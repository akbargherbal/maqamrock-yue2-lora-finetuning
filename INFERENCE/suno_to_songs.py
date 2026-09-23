#!/usr/bin/env python3
"""Convert a legacy Suno `workspace_manifest.json` into `INFERENCE/generate.py`
input songs.

Suno generates 2 takes per song (`_SONG_A` / `_SONG_B`) with identical prompt
content; this tool drops the duplicate by `original_title` and emits one song
per title. No audio is needed — the conditioning text lives entirely in the
manifest (`styles` + `lyrics`).

It reuses the canonical v2 code instead of re-deriving it:
  - `prepare_yue2_dataset.parse_fields` / `build_caption` build the style text
    byte-identically to the training captions (trigger left off — `generate.py`
    prepends `arabmaqamrock `). A track with no `Maqam <name>` in `styles.vocals`
    is kept, not rejected: its style omits the maqam sentence (and, for legacy
    stub entries whose `styles` is a bare genre string rather than the
    `key: "value"` block, the raw text is used as-is), and its name/report use
    the `unknown` maqam label.
  - the lyric cleaning is the binding v2 format from DECISIONS.md:174-194:
    drop `///***///`; collapse `[Section | descriptors]` to `[Section]` for the
    canonical names (Intro, Verse [n], Chorus, Pre-Chorus, Bridge, Outro, Hook,
    Refrain); drop any other bracketed aside; never touch the wording.
  - `generate.resolve_songs` validates the emitted JSON before it is written.

Usage:
    python INFERENCE/suno_to_songs.py manifests/workspace_manifest.json \
        -o INFERENCE/songs.ibn_zuraiq.json
    python INFERENCE/suno_to_songs.py a.json b.json -o songs.json --repeat 2
    python INFERENCE/suno_to_songs.py manifests/workspace_manifest.json --dry-run

Output is `{"defaults": {...}, "songs": [{"name", "style", "lyrics"}]}` plus a
`<out>.report.json` with the duplicate/filter log and a provenance map
(name -> original_title/clip_id/assigned_filename/status/maqam).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

INFERENCE_DIR = Path(__file__).resolve().parent
REPO_ROOT = INFERENCE_DIR.parent
for _p in (str(INFERENCE_DIR), str(REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import generate as gen  # noqa: E402
import prepare_yue2_dataset as pyd  # noqa: E402

SKIP_LINE = "///***///"
CANON = {
    "intro": "Intro", "verse": "Verse", "pre-chorus": "Pre-Chorus",
    "chorus": "Chorus", "bridge": "Bridge", "outro": "Outro",
    "hook": "Hook", "refrain": "Refrain",
}
SECTION_RE = re.compile(
    r"^(intro|verse(?:\s+\d+)?|pre-chorus|chorus|bridge|outro|hook|refrain)\b",
    re.IGNORECASE,
)
KEEP_MODES = ("downloaded-a", "a", "b", "first")
NO_MAQAM = "unknown"


# --- lyrics -----------------------------------------------------------------

def canonical_tag(content: str) -> str | None:
    """`Verse 1 | muted guitars` -> `[Verse 1]`; `guitars surge — Ajam` -> None."""
    m = SECTION_RE.match(content.strip())
    if not m:
        return None
    matched = m.group(1).strip()
    parts = matched.split()
    base = parts[0].lower()
    canon = CANON.get(base)
    if canon is None:
        return None
    if base == "verse" and len(parts) > 1:
        return f"[Verse {parts[1]}]"
    return f"[{canon}]"


def clean_lyrics(raw: str) -> tuple[str, list[str]]:
    """Return (cleaned lyrics, dropped bracketed asides)."""
    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    out: list[str] = []
    dropped: list[str] = []
    for line in text.split("\n"):
        s = line.strip()
        if s == SKIP_LINE:
            continue
        if s.startswith("[") and s.endswith("]"):
            canon = canonical_tag(s[1:-1])
            if canon:
                out.append(canon)
            else:
                dropped.append(s)
            continue
        out.append(line.rstrip())
    # trim edges and collapse runs of blank lines to one
    while out and not out[0].strip():
        out.pop(0)
    while out and not out[-1].strip():
        out.pop()
    collapsed: list[str] = []
    for line in out:
        if not line.strip() and collapsed and not collapsed[-1].strip():
            continue
        collapsed.append(line)
    return "\n".join(collapsed), dropped


# --- styles -----------------------------------------------------------------

def extract_maqam(track: dict) -> str | None:
    fields = pyd.parse_fields(track.get("styles", ""))
    m = pyd.MAQAM_MENTION_RE.search(fields.get("vocals", ""))
    return m.group(1) if m else None


def build_style(track: dict, maqam: str | None, trigger: str | None) -> str:
    fields = pyd.parse_fields(track.get("styles", ""))
    if fields:
        style = pyd.build_caption(fields, maqam, None)
    else:
        # Legacy/stub entries carry a bare genre string, not the key: "value"
        # block parse_fields expects; keep it verbatim rather than dropping it.
        style = str(track.get("styles", "")).strip()
    if trigger:
        style = f"{trigger} {style}"
    return style


# --- manifest parsing -------------------------------------------------------

def load_manifest(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as e:
        gen.fail(f"cannot read manifest {path}: {e}")
    except json.JSONDecodeError as e:
        gen.fail(f"{path}: invalid JSON: {e}")
    gen.check(isinstance(data, dict), f"{path}: top level must be an object")
    tracks = data.get("tracks")
    gen.check(isinstance(tracks, list), f"{path}: 'tracks' must be an array")
    return data


def collect_entries(path: Path, trigger: str | None) -> list[dict]:
    data = load_manifest(path)
    workspace = str(data.get("workspace_name") or path.stem)
    entries = []
    for i, track in enumerate(data.get("tracks", [])):
        gen.check(isinstance(track, dict), f"{path}: tracks[{i}] must be an object")
        title = str(track.get("original_title") or "").strip() \
            or str(track.get("assigned_filename") or "").strip()
        if not title:
            gen.warn(f"{path}: tracks[{i}] has no original_title/assigned_filename; skipping")
            continue
        maqam = extract_maqam(track)
        if maqam is None:
            gen.warn(f"{path}: tracks[{i}] ({title[:40]}) has no 'Maqam <name>' "
                     f"in styles.vocals; keeping it with the {NO_MAQAM!r} label")
        style = build_style(track, maqam, trigger)
        gen.check(style.strip(), f"{path}: tracks[{i}] ({title[:40]}) has no usable style text")
        lyrics, dropped = clean_lyrics(track.get("lyrics", ""))
        gen.check(lyrics.strip(), f"{path}: tracks[{i}] ({title[:40]}) has no usable lyrics")
        name = pyd.safe_ascii_name(workspace, maqam or NO_MAQAM, i,
                                   str(track.get("clip_id", "noid")))
        entries.append({
            "manifest": str(path),
            "workspace": workspace,
            "index": i,
            "title": title,
            "name": name,
            "maqam": maqam,
            "style": style,
            "lyrics": lyrics,
            "dropped_tags": dropped,
            "status": str(track.get("status") or ""),
            "clip_id": str(track.get("clip_id") or ""),
            "assigned_filename": str(track.get("assigned_filename") or ""),
        })
    return entries


def filter_entries(entries: list[dict], maqams: list[str] | None,
                   statuses: list[str] | None) -> list[dict]:
    out = entries
    if maqams:
        wanted = {m.lower() for m in maqams}
        out = [e for e in out if (e["maqam"] or "").lower() in wanted]
    if statuses:
        wanted = {s.lower() for s in statuses}
        out = [e for e in out if e["status"].lower() in wanted]
    return out


def pick_survivor(group: list[dict], keep: str) -> dict:
    if keep == "first":
        return group[0]
    if keep in ("a", "b"):
        suffix = f"_SONG_{keep.upper()}.mp3"
        return next((e for e in group if e["assigned_filename"].endswith(suffix)), group[0])
    # downloaded-a (default): prefer a downloaded take, then SONG_A, then first
    pool = [e for e in group if e["status"] == "downloaded"] or group
    return next((e for e in pool if e["assigned_filename"].endswith("_SONG_A.mp3")), pool[0])


def dedup(entries: list[dict], keep: str, keep_both: bool) -> tuple[list[dict], list[dict]]:
    """Group by (workspace, original_title); return (kept, dropped-groups)."""
    groups: dict[tuple, list[dict]] = {}
    for e in entries:
        groups.setdefault((e["workspace"], e["title"]), []).append(e)
    kept: list[dict] = []
    dropped: list[dict] = []
    for (_, title), group in groups.items():
        if keep_both:
            kept.extend(group)
            continue
        survivor = pick_survivor(group, keep)
        kept.append(survivor)
        losers = [e for e in group if e is not survivor]
        if losers:
            dropped.append({
                "workspace": survivor["workspace"],
                "original_title": title,
                "kept": {"name": survivor["name"], "clip_id": survivor["clip_id"],
                         "assigned_filename": survivor["assigned_filename"],
                         "status": survivor["status"]},
                "dropped": [{"clip_id": e["clip_id"],
                             "assigned_filename": e["assigned_filename"],
                             "status": e["status"]} for e in losers],
            })
    return kept, dropped


# --- output -----------------------------------------------------------------

def song_doc(entry: dict, style_dir: Path | None, lyrics_dir: Path | None,
             out_dir: Path) -> dict:
    song: dict = {"name": entry["name"]}
    if style_dir is not None:
        sp = style_dir / f"{entry['name']}_style.txt"
        sp.write_text(entry["style"] + "\n", encoding="utf-8")
        song["style_file"] = os.path.relpath(sp, out_dir)
    else:
        song["style"] = entry["style"]
    if lyrics_dir is not None:
        lp = lyrics_dir / f"{entry['name']}_lyrics.txt"
        lp.write_text(entry["lyrics"] + "\n", encoding="utf-8")
        song["lyrics_file"] = os.path.relpath(lp, out_dir)
    else:
        song["lyrics"] = entry["lyrics"]
    return song


def build_report(entries: list[dict], kept: list[dict], dropped: list[dict],
                 filters: dict, inputs: list[str]) -> dict:
    per_maqam: dict[str, int] = {}
    provenance: dict[str, dict] = {}
    dropped_tags: dict[str, int] = {}
    for e in kept:
        label = e["maqam"] or NO_MAQAM
        per_maqam[label] = per_maqam.get(label, 0) + 1
        provenance[e["name"]] = {
            "workspace": e["workspace"], "original_title": e["title"],
            "assigned_filename": e["assigned_filename"], "clip_id": e["clip_id"],
            "status": e["status"], "maqam": e["maqam"],
        }
    for e in entries:
        for tag in e["dropped_tags"]:
            dropped_tags[tag] = dropped_tags.get(tag, 0) + 1
    return {
        "generated_at": gen.utcnow(),
        "inputs": inputs,
        "filters": filters,
        "entries_total": len(entries),
        "songs_kept": len(kept),
        "duplicates_dropped": sum(len(d["dropped"]) for d in dropped),
        "per_maqam": per_maqam,
        "dropped_tags": dropped_tags,
        "duplicate_groups": dropped,
        "provenance": provenance,
    }


def print_summary(report: dict, out_path: Path | None, dry_run: bool) -> None:
    print(f"suno_to_songs: {len(report['inputs'])} manifest(s), "
          f"{report['entries_total']} entries -> {report['songs_kept']} song(s) "
          f"({report['duplicates_dropped']} duplicate(s) dropped)")
    print("  maqams: " + (", ".join(f"{k} {v}" for k, v in sorted(report["per_maqam"].items()))
                          or "none"))
    if report["dropped_tags"]:
        print("  tags dropped: " + ", ".join(
            f"{k} x{v}" for k, v in sorted(report["dropped_tags"].items())))
    if out_path is not None:
        print(f"  out: {out_path}" + ("   [dry-run: nothing written]" if dry_run else ""))


# --- CLI --------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="suno_to_songs.py",
        description="Convert legacy Suno workspace_manifest.json files into "
                    "INFERENCE/generate.py input (style + lyrics per song, A/B deduped).",
        epilog="See docs/INFERENCE.md ('Generate from your own JSON').",
    )
    p.add_argument("manifests", nargs="+", help="one or more workspace_manifest.json files")
    p.add_argument("-o", "--out", default=None,
                   help="output songs JSON (default: <first manifest dir>/<workspace>_songs.json)")
    p.add_argument("--report", default=None, help="report JSON (default: <out>.report.json)")
    p.add_argument("--repeat", type=int, default=None,
                   help="default takes per song in generate.py 'defaults' (default: unset)")
    p.add_argument("--quantile", type=float, default=None, choices=gen.QUANTILES,
                   help="cap quantile for generate.py 'defaults'")
    p.add_argument("--keep", choices=KEEP_MODES, default="downloaded-a",
                   help="which A/B take survives (default: downloaded-a)")
    p.add_argument("--keep-both", action="store_true",
                   help="do not dedup; emit both SONG_A and SONG_B")
    p.add_argument("--maqam", action="append", default=None,
                   help="only tracks with this maqam (repeatable, case-insensitive)")
    p.add_argument("--status", action="append", default=None,
                   help="only tracks with this status, e.g. downloaded (repeatable)")
    p.add_argument("--trigger", default=None,
                   help="bake this trigger word into the style (default: none; "
                        "generate.py prepends 'arabmaqamrock ')")
    p.add_argument("--style-dir", default=None,
                   help="write styles as files and reference them via style_file")
    p.add_argument("--lyrics-dir", default=None,
                   help="write lyrics as files and reference them via lyrics_file")
    p.add_argument("--dry-run", action="store_true",
                   help="validate + print the summary; writes nothing")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        gen.check(args.repeat is None or gen._is_pos_int(args.repeat),
                  "--repeat must be an integer >= 1")
        manifests = [Path(m) for m in args.manifests]
        for m in manifests:
            gen.check(m.is_file(), f"manifest not found: {m}")

        entries: list[dict] = []
        for m in manifests:
            entries.extend(collect_entries(m, args.trigger))
        gen.check(entries, "no usable tracks found in the given manifest(s)")

        entries = filter_entries(entries, args.maqam, args.status)
        gen.check(entries, "all tracks were filtered out (check --maqam/--status)")

        kept, dropped = dedup(entries, args.keep, args.keep_both)
        kept_by_name = {}
        for e in kept:
            gen.check(e["name"] not in kept_by_name,
                      f"duplicate song name '{e['name']}' (same workspace/index/clip_id)")
            kept_by_name[e["name"]] = e

        if args.out:
            out_path = Path(args.out)
        else:
            ws = re.sub(r"[^A-Za-z0-9_-]+", "-", entries[0]["workspace"]).strip("-") or "songs"
            out_path = Path(entries[0]["manifest"]).parent / f"{ws}_songs.json"

        filters = {"maqam": args.maqam, "status": args.status,
                   "keep": "both" if args.keep_both else args.keep}
        report = build_report(entries, kept, dropped, filters, [str(m) for m in manifests])

        if args.dry_run:
            print_summary(report, out_path, dry_run=True)
            return 0

        out_path.parent.mkdir(parents=True, exist_ok=True)
        style_dir = Path(args.style_dir) if args.style_dir else None
        lyrics_dir = Path(args.lyrics_dir) if args.lyrics_dir else None
        for d in (style_dir, lyrics_dir):
            if d is not None:
                d.mkdir(parents=True, exist_ok=True)

        doc: dict = {"songs": [song_doc(e, style_dir, lyrics_dir, out_path.parent)
                               for e in kept]}
        defaults = {}
        if args.repeat is not None:
            defaults["repeat"] = args.repeat
        if args.quantile is not None:
            defaults["quantile"] = args.quantile
        if defaults:
            doc["defaults"] = defaults

        # Self-validate against the real generate.py loader before writing.
        gen.resolve_songs(doc, out_path.parent, trigger=False)

        out_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")
        report_path = Path(args.report) if args.report \
            else out_path.with_name(out_path.stem + ".report.json")
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                               encoding="utf-8")
        print_summary(report, out_path, dry_run=False)
        print(f"  report: {report_path}")
        return 0
    except gen.PlanError as e:
        print(f"[error] {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
