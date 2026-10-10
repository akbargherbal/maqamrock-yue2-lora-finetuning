#!/usr/bin/env python3
"""
prepare_yue2_dataset_v3.py
--------------------------
Builds a YuE2 LoRA fine-tuning dataset (audio + matching .txt captions) from
the NEW min_4stars_ai_music folder tree (438 tracks), as a superset of v2.

Difference from v2 (prepare_yue2_dataset_v2.py):
  * LYRICS ARE VERBATIM. v2's clean_lyrics() collapsed `[Section | asides]`
    tags to `[Section]` and *dropped* every non-section bracketed tag
    (e.g. `[orchestral strings swell]`). v3 keeps the lyric block exactly as
    written in the manifest -- it only removes the leading `///***///` marker
    line and collapses runs of 3+ blank lines to one blank line.
  * The style caption is UNCHANGED from v2: the Suno header
    (`[Is_MAX_MODE...] [QUALITY...] [REALISM...]` + `[START_ON...]`) is still
    stripped, and the `genre/vocals/production/instrumentation/mood` fields are
    rebuilt as one line. (Decision D2, 2026-10-10.)

Everything else (selection rule, output filenames, audio copied as-is) is
identical to v2, so the 267 tracks shared with v2 get byte-identical filenames.

Input:
    <root>/<maqam>/<workspace>/workspace_manifest.json + audio files

Output:
    <out>/<maqam>_<ws>_<idx>_<clip8>.{ext,txt}   (audio copied as-is)

Usage:
    # dry run: parse + report only, writes NO audio/caption files
    python prepare_yue2_dataset_v3.py --root <tree> --out ./v3_arabmaqamrock_dataset --dry-run
    # real build
    python prepare_yue2_dataset_v3.py --root <tree> --out ./v3_arabmaqamrock_dataset
"""

import argparse
import json
import re
import shutil
import unicodedata
from collections import Counter
from pathlib import Path

MAQAM_DIRS = {"hijaz", "nahawand", "ajam", "kurd"}
AUDIO_EXTS = {".mp3", ".wav", ".flac", ".m4a"}
TRIGGER = "arabmaqamrock"

# Suno-only header + lyric-start hint -- STRIPPED from the style caption (D2).
HEADER_RE = re.compile(r"^\[Is_MAX_MODE.*?\]\s*\n(?:\[START_ON.*?\]\s*\n?)*\s*", re.DOTALL)
FIELD_RE = re.compile(r'(\w+):\s*"((?:[^"\\]|\\.)*)"')
# The leading separation marker; covers `///***///` and the escaped `///\*\*\*///`.
MARKER_RE = re.compile(r"^[/*\\]+$")
SECTION_RE = re.compile(r"^(Intro|Verse\s*\d*|Chorus|Pre-Chorus|Bridge|Outro|Hook|Refrain)\b", re.IGNORECASE)
TAG_RE = re.compile(r"^\[([^\]]*)\]$")
BLANK_RUN_RE = re.compile(r"\n{3,}")


def normalize(name: str) -> str:
    name = unicodedata.normalize("NFC", name)
    return re.sub(r"\s+", " ", name).strip()


def ascii_safe(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "-", name).strip("-") or "ws"


def ensure_period(s: str) -> str:
    s = s.strip()
    return s if s.endswith(".") else s + "."


def parse_fields(styles: str) -> dict:
    body = HEADER_RE.sub("", styles, count=1)
    fields = {}
    for key, val in FIELD_RE.findall(body):
        fields[key.lower()] = val.replace('\\"', '"')
    return fields


def build_style_caption(fields: dict, maqam: str) -> str:
    parts = [TRIGGER]
    genre = fields.get("genre")
    if genre:
        parts.append(ensure_period(genre))
    parts.append(f"Maqam {maqam}.")
    for key in ("vocals", "production", "instrumentation"):
        val = fields.get(key)
        if val:
            parts.append(ensure_period(val))
    mood = fields.get("mood")
    if mood:
        parts.append(ensure_period(f"Mood: {mood}"))
    return " ".join(parts)


def verbatim_lyrics(lyrics: str) -> str:
    """Keep the lyric block exactly as written, minus the leading marker line
    and any run of 3+ blank lines (collapsed to one blank line)."""
    lines = lyrics.split("\n")
    if lines and MARKER_RE.match(lines[0].strip()):
        lines = lines[1:]
        if lines and lines[0].strip() == "":
            lines = lines[1:]
    text = "\n".join(line.rstrip() for line in lines)
    text = BLANK_RUN_RE.sub("\n\n", text)
    return text.strip("\n")


def find_audio_files(workspace_dir: Path) -> dict:
    return {
        normalize(p.name): p
        for p in workspace_dir.iterdir()
        if p.suffix.lower() in AUDIO_EXTS
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--dry-run", action="store_true",
                    help="parse + report only; write NO audio/caption files")
    ap.add_argument("--overrides", default=None,
                    help="optional JSON: {out_name: {\"skip\": true} | "
                         "{\"lyrics_override\": \"...\"} | {\"caption_override\": \"...\"}}")
    args = ap.parse_args()

    root = Path(args.root)
    out_dir = Path(args.out)
    overrides = {}
    if args.overrides:
        overrides = json.loads(Path(args.overrides).read_text(encoding="utf-8"))

    if not args.dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)

    total_tracks = 0
    written = []          # dicts
    empty_lyrics = []
    skipped_missing = []
    kept_tags = Counter()  # non-section tags now KEPT (v2 dropped these)
    per_maqam = Counter()

    for maqam_dir in sorted(root.iterdir()):
        if not maqam_dir.is_dir() or maqam_dir.name.lower() not in MAQAM_DIRS:
            continue
        maqam = maqam_dir.name.capitalize()

        for ws in sorted(maqam_dir.iterdir()):
            if not ws.is_dir():
                continue
            manifest_path = ws / "workspace_manifest.json"
            if not manifest_path.exists():
                continue
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            present = find_audio_files(ws)

            for i, track in enumerate(manifest.get("tracks", [])):
                total_tracks += 1
                fname = normalize(track.get("assigned_filename", ""))
                if fname not in present:
                    skipped_missing.append((ws.name, fname))
                    continue

                raw_lyrics = (track.get("lyrics") or "").strip()
                if not raw_lyrics:
                    empty_lyrics.append((ws.name, fname))

                for ln in raw_lyrics.split("\n"):
                    m = TAG_RE.match(ln.strip())
                    if m and not SECTION_RE.match(m.group(1).strip()):
                        kept_tags[ln.strip()] += 1

                clip_id = track.get("clip_id", "noid") or "noid"
                out_name = f"{maqam.lower()}_{ascii_safe(ws.name)}_{i:03d}_{clip_id[:8]}"
                ov = overrides.get(out_name, {})

                fields = parse_fields(track.get("styles", ""))
                # surgical per-track field overrides (e.g. rewrite the vocals line)
                for _k in ("genre", "vocals", "production", "instrumentation", "mood"):
                    if _k in ov:
                        fields[_k] = ov[_k]
                style = build_style_caption(fields, maqam)
                lyrics = verbatim_lyrics(raw_lyrics)
                caption = f"{style}\n[Lyrics]\n{lyrics}"

                if ov.get("caption_override"):
                    caption = ov["caption_override"]
                elif ov.get("lyrics_override"):
                    caption = f"{style}\n[Lyrics]\n{ov['lyrics_override']}"

                rec = dict(out_name=out_name, maqam=maqam, ws=ws.name,
                           source=fname, clip_id=clip_id, skipped=bool(ov.get("skip")))
                written.append(rec)

                if ov.get("skip"):
                    continue

                if not args.dry_run:
                    src = present[fname]
                    dst_audio = out_dir / (out_name + src.suffix.lower())
                    dst_caption = out_dir / (out_name + ".txt")
                    shutil.copy2(src, dst_audio)
                    dst_caption.write_text(caption, encoding="utf-8")

                per_maqam[maqam] += 1

    real = [w for w in written if not w["skipped"]]
    out_dir.parent.mkdir(parents=True, exist_ok=True)
    report = []
    report.append("# v3 dataset build report" + (" (DRY RUN)" if args.dry_run else ""))
    report.append(f"- root: `{root}`")
    report.append(f"- output: `{out_dir}`")
    report.append(f"- trigger: `{TRIGGER}`")
    report.append("")
    report.append(f"- manifest tracks scanned: **{total_tracks}**")
    report.append(f"- audio/caption pairs selected: **{len(real)}**")
    report.append(f"- per maqam: {dict(per_maqam)}")
    report.append(f"- manifest entries not on disk (lower-rated takes, skipped): **{len(skipped_missing)}**")
    report.append(f"- selected tracks with empty lyrics: **{len(empty_lyrics)}**")
    report.append(f"- non-section bracketed tags now KEPT verbatim: "
                  f"**{sum(kept_tags.values())}** occurrences / {len(kept_tags)} distinct")
    report.append("")
    report.append("## Kept non-section tags (top 20)")
    for tag, c in kept_tags.most_common(20):
        report.append(f"- {c:4d}  `{tag[:110]}`")
    report_text = "\n".join(report) + "\n"
    (out_dir.parent / "v3_arabmaqamrock_dataset_report.md").write_text(report_text, encoding="utf-8")

    map_path = out_dir.parent / "v3_arabmaqamrock_dataset_manifest.json"
    map_path.write_text(json.dumps({"count": len(real), "tracks": written}, ensure_ascii=False, indent=1),
                        encoding="utf-8")

    print(report_text)
    print(f"report  -> {out_dir.parent / 'v3_arabmaqamrock_dataset_report.md'}")
    print(f"manifest-> {map_path}")


if __name__ == "__main__":
    main()
