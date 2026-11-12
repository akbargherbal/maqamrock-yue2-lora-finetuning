#!/usr/bin/env python3
"""
prepare_arabic_instrumental_dataset.py
--------------------------------------
Compiles a YuE2/OSTRIS-ready dataset (flat ``<name>.mp3`` + ``<name>.txt``) from
the two instrumental source sets:

  * gs://.../DATASET/yt500_instrumental               (460 takes)
  * gs://.../DATASET/fadhl_shaker_instrumental_18_shortlist (22 takes)

Output format matches ``v3_arabmaqamrock_dataset.zip``: one audio file and one
caption file per track, both at the archive root. The caption is::

    Middle Eastern fusion, instrumental. <caption.txt>\n[Lyrics]\n<lyrics.txt>

where ``lyrics.txt`` is the source section-tag plan (``[intro]``, ``[verse]``,
...). Source files are never modified; the audio is hardlinked (copied only if
the filesystem refuses a link).

The script also writes, next to the output directory:

  <out>.parent/arabic_instrumental_dataset_manifest.json   per-track records
  <out>.parent/arabic_instrumental_dataset_report.md       build report

Usage:
    # sources already fetched with:
    #   gsutil -m cp -r <uri>/tracks <src>/<key>/
    python3 prepare_arabic_instrumental_dataset.py \
        --src /content/arabic_instrumental_build/src \
        --out /content/arabic_instrumental_build/arabic_instrumental_dataset

    # then zip (see docs/ARABIC_INSTRUMENTAL_DATASET.md):
    cd <out> && zip -0 -X -q ../arabic_instrumental_dataset.zip *.mp3 *.txt
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

DATASET_NAME = "arabic_instrumental_dataset"
PREFIX = "Middle Eastern fusion, instrumental."
LYRICS_MARKER = "[Lyrics]"
TAG_RE = re.compile(r"^\[[^\[\]]+\]$")
NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

SOURCES = [
    {
        "key": "yt500",
        "uri": "gs://akbar-december-2024-backup/DATASET/yt500_instrumental",
        "local": "yt500",
    },
    {
        "key": "fadhl_shaker_shortlist",
        "uri": "gs://akbar-december-2024-backup/DATASET/fadhl_shaker_instrumental_18_shortlist",
        "local": "fadhl",
    },
]

# Experimental lexicon (same categories the source datasets document). Used
# only to annotate the manifest -- it never edits a caption.
VOCAL_PATTERNS = {
    "spoken": re.compile(r"spoken[- ](?:word|sample|passage)|\bspoken\b", re.I),
    "vocal_sample": re.compile(r"vocal sample", re.I),
    "vocalise": re.compile(r"vocali[sz]", re.I),
    "male_vocal": re.compile(r"male vocal", re.I),
    "female_vocal": re.compile(r"female vocal", re.I),
    "vocals": re.compile(r"\bvocals\b", re.I),
    "singing": re.compile(r"\bsing(?:ing|er|s)?\b|\bsung\b", re.I),
    "chant": re.compile(r"\bchant", re.I),
    "choir": re.compile(r"\bchoir\b", re.I),
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def probe_audio(path: Path) -> float:
    """Return duration in seconds; raise if ffprobe cannot read an audio stream."""
    out = subprocess.run(
        [
            "ffprobe", "-v", "error", "-select_streams", "a:0",
            "-show_entries", "stream=codec_name:format=duration",
            "-of", "json", str(path),
        ],
        capture_output=True, text=True,
    )
    if out.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {out.stderr.strip()[:200]}")
    info = json.loads(out.stdout or "{}")
    streams = info.get("streams") or []
    if not streams:
        raise RuntimeError("no audio stream")
    codec = streams[0].get("codec_name", "")
    if codec not in ("mp3", "mp2"):
        raise RuntimeError(f"unexpected audio codec {codec!r}")
    duration = float((info.get("format") or {}).get("duration") or 0.0)
    if duration <= 0:
        raise RuntimeError("non-positive duration")
    return duration


def strip_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def build_prompt(caption: str, lyrics: str) -> str:
    return f"{PREFIX} {caption}\n{LYRICS_MARKER}\n{lyrics}"


def validate_prompt(prompt: str, where: str) -> None:
    if not prompt.startswith(PREFIX + " "):
        raise ValueError(f"{where}: prompt does not start with the prefix")
    if prompt.count(LYRICS_MARKER) != 1:
        raise ValueError(f"{where}: expected exactly one {LYRICS_MARKER}")
    style, lyrics = prompt.split("\n" + LYRICS_MARKER + "\n", 1)
    if style.strip() == PREFIX:
        raise ValueError(f"{where}: empty caption")
    lines = [ln.strip() for ln in lyrics.split("\n") if ln.strip()]
    if not lines:
        raise ValueError(f"{where}: empty lyrics block")
    bad = [ln for ln in lines if not TAG_RE.match(ln)]
    if bad:
        raise ValueError(f"{where}: non-tag lyric line {bad[0]!r}")


def collect_tracks(src: Path):
    tracks = []
    for source in SOURCES:
        root = src / source["local"] / "tracks"
        if not root.is_dir():
            sys.exit(f"[FAIL] missing source tree: {root}")
        for d in sorted(p for p in root.iterdir() if p.is_dir()):
            tracks.append((source, d))
    return tracks


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", required=True, type=Path,
                    help="directory holding <local>/tracks/ trees")
    ap.add_argument("--out", required=True, type=Path,
                    help="flat output directory (must not exist unless --force)")
    ap.add_argument("--force", action="store_true", help="allow a non-empty --out")
    args = ap.parse_args()

    out: Path = args.out
    if out.exists() and any(out.iterdir()) and not args.force:
        sys.exit(f"[FAIL] {out} exists and is not empty (use --force)")
    out.mkdir(parents=True, exist_ok=True)

    tracks = collect_tracks(args.src)
    print(f"tracks discovered: {len(tracks)}")
    names = Counter(d.name for _, d in tracks)
    dupes = {n: c for n, c in names.items() if c > 1}
    if dupes:
        sys.exit(f"[FAIL] duplicate track dir names: {dupes}")
    for _, d in tracks:
        if not NAME_RE.match(d.name):
            sys.exit(f"[FAIL] unsafe track name: {d.name!r}")

    records = []
    caption_para = Counter()
    status = Counter()
    vocal = Counter()
    total_audio = 0
    total_seconds = 0.0
    empty_caption = 0

    for i, (source, d) in enumerate(tracks, 1):
        audio = d / "audio.mp3"
        cap_f = d / "caption.txt"
        lyr_f = d / "lyrics.txt"
        for f in (audio, cap_f, lyr_f):
            if not f.is_file() or f.stat().st_size == 0:
                sys.exit(f"[FAIL] missing/empty required file: {f}")

        caption = strip_text(cap_f)
        lyrics = strip_text(lyr_f)
        if not caption:
            empty_caption += 1
        prompt = build_prompt(caption, lyrics)
        validate_prompt(prompt, d.name)

        dst_audio = out / f"{d.name}.mp3"
        dst_txt = out / f"{d.name}.txt"
        try:
            os.link(audio, dst_audio)
        except OSError:
            shutil.copy2(audio, dst_audio)
        dst_txt.write_text(prompt, encoding="utf-8")

        duration = probe_audio(dst_audio)
        audio_sha = sha256_file(dst_audio)

        try:
            meta = json.loads((d / "track.json").read_text(encoding="utf-8"))
        except Exception:
            meta = {}
        cap_meta = meta.get("caption") or {}
        status[str(cap_meta.get("rewrite_status", "unknown"))] += 1
        title = meta.get("title") or meta.get("song") or ""
        artist = meta.get("artist") or ""
        paragraphs = len([p for p in re.split(r"\n\s*\n", caption) if p.strip()])
        caption_para[paragraphs] += 1
        matched = [k for k, rx in VOCAL_PATTERNS.items() if rx.search(caption)]
        for k in matched:
            vocal[k] += 1

        records.append({
            "out_name": d.name,
            "source_dataset": source["key"],
            "source_uri": f"{source['uri']}/tracks/{d.name}",
            "title": title,
            "artist": artist,
            "audio_bytes": dst_audio.stat().st_size,
            "audio_sha256": audio_sha,
            "audio_duration_s": round(duration, 3),
            "caption_chars": len(caption),
            "caption_paragraphs": paragraphs,
            "caption_status": str(cap_meta.get("rewrite_status", "unknown")),
            "caption_vocal_terms": matched,
            "lyrics_tags": len([ln for ln in lyrics.split("\n") if ln.strip()]),
            "caption_sha256": sha256_bytes(caption.encode("utf-8")),
            "prompt_sha256": sha256_bytes(prompt.encode("utf-8")),
        })
        total_audio += dst_audio.stat().st_size
        total_seconds += duration
        if i % 100 == 0 or i == len(tracks):
            print(f"  [{i}/{len(tracks)}] {d.name}  {duration:.1f}s")

    # ---- checks -----------------------------------------------------------
    out_mp3 = sorted(out.glob("*.mp3"))
    out_txt = sorted(out.glob("*.txt"))
    checks = {
        "count_tracks": len(tracks),
        "count_mp3": len(out_mp3),
        "count_txt": len(out_txt),
        "one_to_one": len(out_mp3) == len(out_txt) == len(tracks),
        "empty_captions": empty_caption,
        "prefix_ok": all(
            (out / f"{r['out_name']}.txt").read_text(encoding="utf-8").startswith(PREFIX + " ")
            for r in records
        ),
    }
    checks["all_passed"] = bool(
        checks["one_to_one"] and checks["empty_captions"] == 0 and checks["prefix_ok"]
    )
    print(json.dumps(checks, indent=2))
    if not checks["all_passed"]:
        sys.exit("[FAIL] checks failed")

    built_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    by_source = Counter(r["source_dataset"] for r in records)
    bytes_by_source = Counter()
    for r in records:
        bytes_by_source[r["source_dataset"]] += r["audio_bytes"]

    manifest = {
        "dataset": DATASET_NAME,
        "built_at": built_at,
        "prompt_template": f"{PREFIX} {{caption}}\\n{LYRICS_MARKER}\\n{{lyrics}}",
        "prefix": PREFIX,
        "count": len(records),
        "audio_bytes": total_audio,
        "audio_hours": round(total_seconds / 3600, 2),
        "sources": [
            {
                "key": s["key"],
                "uri": s["uri"],
                "tracks": by_source[s["key"]],
                "audio_bytes": bytes_by_source[s["key"]],
            }
            for s in SOURCES
        ],
        "checks": checks,
        "tracks": records,
    }
    manifest_path = out.parent / f"{DATASET_NAME}_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n",
                             encoding="utf-8")

    # ---- report -----------------------------------------------------------
    cap_chars = sorted(r["caption_chars"] for r in records)
    source_counts = ", ".join(f"{s['key']} {by_source[s['key']]}" for s in SOURCES)
    bar = "=" * 72
    lines = [
        f"# {DATASET_NAME} build report",
        "",
        f"- built_at: **{built_at}**",
        f"- output: `{out}`",
        f"- tracks: **{len(records)}** ({source_counts})",
        f"- audio: **{total_audio:,} bytes** ({total_audio / 2**30:.2f} GiB), "
        f"**{total_seconds / 3600:.2f} h**",
        f"- caption chars: min {cap_chars[0]}, median {cap_chars[len(cap_chars) // 2]}, "
        f"max {cap_chars[-1]}",
        f"- caption paragraphs: {dict(sorted(caption_para.items()))}",
        f"- caption rewrite status: {dict(status.most_common())}",
        "",
        "## Prompt template",
        "",
        "```",
        f"{PREFIX} <caption.txt>",
        f"{LYRICS_MARKER}",
        "<lyrics.txt (section tags)>",
        "```",
        "",
        "Section tags are kept verbatim; captions are copied verbatim (only leading/trailing "
        "whitespace stripped) and the prefix is added. Source files are never modified.",
        "",
        "## Checks",
        "",
        "| check | result |",
        "|---|---|",
        f"| 482-style one-to-one mp3/txt | {checks['one_to_one']} ({checks['count_mp3']}/{checks['count_txt']}) |",
        f"| every prompt starts with prefix | {checks['prefix_ok']} |",
        f"| every prompt has exactly one [Lyrics] and tag-only lines | PASS (enforced per track) |",
        f"| every mp3 decodes (ffprobe, codec mp3) | PASS ({len(records)}/{len(records)}) |",
        f"| empty captions | {checks['empty_captions']} |",
        f"| duplicate track names | 0 |",
        "",
        "## Caption vocal-term annotation (experimental)",
        "",
        "The source captioner sometimes describes vocal material even for instrumental takes. "
        "Counts below are regex matches over the final captions; the manifest records the "
        "matched terms per track (`caption_vocal_terms`). Captions are not edited.",
        "",
        "| term | tracks |",
        "|---|---:|",
    ]
    for k, c in vocal.most_common():
        lines.append(f"| `{k}` | {c} |")
    lines += [
        "",
        f"Any-vocal-term tracks: **{sum(1 for r in records if r['caption_vocal_terms'])}"
        f"/{len(records)}**",
        "",
        "## Samples",
        "",
    ]
    sample_names = [records[0]["out_name"]]
    fadhl_rec = next((r for r in records if r["source_dataset"] == "fadhl_shaker_shortlist"), None)
    if fadhl_rec:
        sample_names.append(fadhl_rec["out_name"])
    for name in sample_names:
        prompt = (out / f"{name}.txt").read_text(encoding="utf-8")
        style, lyr = prompt.split("\n[Lyrics]\n", 1)
        lines += [
            f"### `{name}`",
            "",
            "```",
            style[:400] + ("..." if len(style) > 400 else ""),
            LYRICS_MARKER,
            lyr,
            "```",
            "",
        ]
    lines += [
        "## Provenance",
        "",
        "Per-track source URI, title, artist, sizes, SHA-256 of audio/caption/prompt, duration, "
        "lyrics tag count and caption status are in "
        f"`{manifest_path.name}`. The zip is stored (`zip -0`) with 482 mp3 + 482 txt at the "
        "archive root, matching `v3_arabmaqamrock_dataset.zip`.",
        "",
    ]
    report_path = out.parent / f"{DATASET_NAME}_report.md"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(bar)
    print(f"out      -> {out}")
    print(f"manifest -> {manifest_path}")
    print(f"report   -> {report_path}")
    print(f"audio    -> {total_audio:,} bytes / {total_seconds / 3600:.2f} h")
    print(bar)
    return 0


if __name__ == "__main__":
    sys.exit(main())
