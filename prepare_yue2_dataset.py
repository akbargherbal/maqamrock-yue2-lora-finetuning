#!/usr/bin/env python3
"""
prepare_yue2_dataset.py
------------------------
Builds an Ostris AI Toolkit-ready training dataset (audio + matching .txt
caption files) from a shortlisted "min_4stars_ai_music" folder tree and the
workspace_manifest.json files sitting alongside the audio (as produced by
the Suno generation pipeline / maqam_prompt_generator.py).

Expected input layout:

    <root>/
      hijaz/
        <workspace_name>/
          workspace_manifest.json
          <assigned_filename_1>.mp3
          <assigned_filename_2>.mp3
          ...
      nahawand/...
      ajam/...
      kurd/...

WHAT COUNTS AS "SHORTLISTED":
A workspace_manifest.json lists every take that was ever generated in that
workspace, not just the good ones -- there is no star-rating field in the
JSON itself. The 4-5 star filter is the filesystem: a track is used only if
its `assigned_filename` is BOTH listed in the manifest AND physically
present as a file in that workspace folder. Anything the manifest mentions
that isn't on disk was a lower-rated take you already filtered out, and is
skipped (and reported) rather than trained on.

WHAT GOES INTO THE CAPTION:
Each manifest entry's `styles` field mixes two different things: Suno-only
control tags + the literal lyric start ([Is_MAX_MODE...], [START_ON...]),
and the reusable sound description (genre/vocals/production/instrumentation
/mood). Only the second part is kept -- a style LoRA should learn the sound,
not memorize which poem starts with which line. `lyrics` is never used.

Usage:
    python prepare_yue2_dataset.py --root ./min_4stars_ai_music --out ./yue2_dataset
    python prepare_yue2_dataset.py --root ./min_4stars_ai_music --out ./yue2_dataset --trigger arabmaqamrock
    python prepare_yue2_dataset.py --root ./min_4stars_ai_music --out ./yue2_dataset --per-maqam
    python prepare_yue2_dataset.py --root ./min_4stars_ai_music --out ./yue2_dataset --convert-wav
"""

import argparse
import json
import re
import shutil
import subprocess
import unicodedata
from pathlib import Path

MAQAM_DIRS = {"hijaz", "nahawand", "ajam", "kurd"}
AUDIO_EXTS = {".mp3", ".wav", ".flac", ".m4a"}

# Strips "[Is_MAX_MODE...](MAX) [QUALITY...] [REALISM...]" plus any number
# of following "[START_ON: ...]" lines -- the Suno-only header + lyric hint.
HEADER_RE = re.compile(r"^\[Is_MAX_MODE.*?\]\s*\n(?:\[START_ON.*?\]\s*\n?)*\s*", re.DOTALL)
FIELD_RE = re.compile(r'(\w+):\s*"((?:[^"\\]|\\.)*)"')
MAQAM_MENTION_RE = re.compile(r"Maqam (\w+)", re.IGNORECASE)


def normalize(name: str) -> str:
    """Collapse whitespace so manifest assigned_filename and on-disk
    filenames still match even where one has doubled spaces."""
    name = unicodedata.normalize("NFC", name)
    return re.sub(r"\s+", " ", name).strip()


def safe_ascii_name(workspace: str, maqam: str, index: int, clip_id: str) -> str:
    ws = re.sub(r"[^A-Za-z0-9_-]+", "-", workspace).strip("-") or "ws"
    return f"{maqam.lower()}_{ws}_{index:03d}_{clip_id[:8]}"


def parse_fields(styles: str) -> dict:
    """Pull genre/vocals/production/instrumentation/mood out of a styles
    string, dropping the Suno-only header and the lyric-start tag."""
    body = HEADER_RE.sub("", styles, count=1)
    fields = {}
    for key, val in FIELD_RE.findall(body):
        fields[key.lower()] = val.replace('\\"', '"')
    return fields


def build_caption(fields: dict, maqam: str, trigger: str | None) -> str:
    parts = []
    if trigger:
        parts.append(trigger + ",")
    parts.append(fields.get("genre", "Full Instrumental."))
    parts.append(f"Maqam {maqam}.")
    if "vocals" in fields:
        parts.append(fields["vocals"])
    if "production" in fields:
        parts.append(fields["production"])
    if "instrumentation" in fields:
        parts.append(fields["instrumentation"])
    if "mood" in fields:
        parts.append(f"Mood: {fields['mood']}.")
    return " ".join(p.strip() for p in parts if p and p.strip())


def find_audio_files(workspace_dir: Path) -> dict:
    """normalized filename -> Path, for every audio file physically present
    in this workspace folder (i.e. the shortlisted 4-5* takes)."""
    return {
        normalize(p.name): p
        for p in workspace_dir.iterdir()
        if p.suffix.lower() in AUDIO_EXTS
    }


def process_workspace(workspace_dir: Path, maqam: str, out_dir: Path,
                       trigger, convert_wav: bool, log: dict) -> None:
    manifest_path = workspace_dir / "workspace_manifest.json"
    if not manifest_path.exists():
        log["no_manifest"].append(str(workspace_dir))
        return

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    present = find_audio_files(workspace_dir)
    used = set()

    for i, track in enumerate(manifest.get("tracks", [])):
        fname = normalize(track.get("assigned_filename", ""))
        if fname not in present:
            continue  # a lower-rated take that was already filtered out
        used.add(fname)

        fields = parse_fields(track.get("styles", ""))

        mentioned = None
        m = MAQAM_MENTION_RE.search(fields.get("vocals", ""))
        if m:
            mentioned = m.group(1)
            if mentioned.lower() != maqam.lower():
                log["maqam_mismatch"].append(
                    f"{workspace_dir / fname}: folder says {maqam}, styles text says {mentioned}"
                )

        caption = build_caption(fields, maqam, trigger)
        out_name = safe_ascii_name(workspace_dir.name, maqam, i, track.get("clip_id", "noid"))
        src_audio = present[fname]
        dst_ext = ".wav" if convert_wav else src_audio.suffix.lower()
        dst_audio = out_dir / (out_name + dst_ext)
        dst_caption = out_dir / (out_name + ".txt")

        if convert_wav:
            subprocess.run(
                ["ffmpeg", "-y", "-i", str(src_audio), "-ar", "44100", str(dst_audio)],
                check=True, capture_output=True,
            )
        else:
            shutil.copy2(src_audio, dst_audio)

        dst_caption.write_text(caption, encoding="utf-8")
        log["written"].append(out_name)

    for unmatched in set(present) - used:
        log["present_not_in_manifest"].append(str(workspace_dir / unmatched))


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--root", required=True, help="Path to the min_4stars_ai_music folder")
    ap.add_argument("--out", required=True, help="Output dataset folder for AI Toolkit")
    ap.add_argument("--trigger", default=None,
                     help='Optional trigger word/phrase prepended to every caption, e.g. "arabmaqamrock"')
    ap.add_argument("--per-maqam", action="store_true",
                     help="Write 4 separate dataset subfolders (one per maqam) instead of one combined folder")
    ap.add_argument("--convert-wav", action="store_true",
                     help="Transcode to 44.1kHz WAV via ffmpeg instead of copying the source audio as-is")
    args = ap.parse_args()

    root = Path(args.root)
    out_root = Path(args.out)
    out_root.mkdir(parents=True, exist_ok=True)

    log = {"written": [], "no_manifest": [], "present_not_in_manifest": [], "maqam_mismatch": []}

    for maqam_dir in sorted(root.iterdir()):
        if not maqam_dir.is_dir() or maqam_dir.name.lower() not in MAQAM_DIRS:
            continue
        maqam = maqam_dir.name.capitalize()
        out_dir = (out_root / maqam) if args.per_maqam else out_root
        out_dir.mkdir(parents=True, exist_ok=True)

        for workspace_dir in sorted(maqam_dir.iterdir()):
            if workspace_dir.is_dir():
                process_workspace(workspace_dir, maqam, out_dir, args.trigger, args.convert_wav, log)

    print(f"Wrote {len(log['written'])} audio/caption pairs to {out_root}")

    if log["no_manifest"]:
        print(f"\n{len(log['no_manifest'])} workspace folder(s) had NO workspace_manifest.json (skipped):")
        for w in log["no_manifest"]:
            print(f"  - {w}")

    if log["present_not_in_manifest"]:
        print(f"\n{len(log['present_not_in_manifest'])} file(s) on disk but not referenced in their manifest (skipped):")
        for w in log["present_not_in_manifest"]:
            print(f"  - {w}")

    if log["maqam_mismatch"]:
        print(f"\n{len(log['maqam_mismatch'])} maqam mismatch(es) between folder and styles text -- worth checking:")
        for w in log["maqam_mismatch"]:
            print(f"  - {w}")


if __name__ == "__main__":
    main()
