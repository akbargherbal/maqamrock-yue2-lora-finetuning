#!/usr/bin/env python3
"""Organize a downloaded `pron_alpha_sweep/` directory into something a human can read.

The GCS tree uses short config folder names (`a0`, `c3050_a0.5`, `cfinal_a1.0`, ...)
whose meaning isn't obvious from the name. This script reads the per-track sidecars
(`*_time.txt`, `*.log`, `_runs_status.log`) plus `sweep_manifest.json` and writes a
Markdown index (default `ORGANIZED.md`) that states, for every WAV, exactly which
parameters produced it: pronunciation checkpoint, alpha, maqam, seed, cap, exit,
wall time, duration, and whether generation hit the semantic cap (truncated).

Nothing in the input tree is modified. The GPU binary / merged build artifacts are
ignored by default (see --include-weights).

Usage:
    python organize_pron_sweep.py /path/to/pron_alpha_sweep
    python organize_pron_sweep.py /path/to/pron_alpha_sweep --md /tmp/INDEX.md
    python organize_pron_sweep.py /path/to/pron_alpha_sweep \
        --flatten /tmp/pron_listen --link      # descriptive symlink/copy set (no audio edits)
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

# Config folder -> parameters. Manifest overrides this when present.
CONFIG_SPECS: Dict[str, dict] = {
    "a0": {"alpha": 0.0, "pron_checkpoint": "final", "pron_step": 6100,
           "note": "V2 baseline; alpha=0 so output is v2 verbatim (no pron contribution)"},
    "c3050_a0.5": {"alpha": 0.5, "pron_checkpoint": "3050", "pron_step": 3050,
                   "note": "pron step 3050 at alpha 0.5"},
    "c3050_a1.0": {"alpha": 1.0, "pron_checkpoint": "3050", "pron_step": 3050,
                   "note": "pron step 3050 at alpha 1.0"},
    "cfinal_a0.5": {"alpha": 0.5, "pron_checkpoint": "final", "pron_step": 6100,
                    "note": "pron step 6100 (final) at alpha 0.5"},
    "cfinal_a1.0": {"alpha": 1.0, "pron_checkpoint": "final", "pron_step": 6100,
                    "note": "pron step 6100 (final) at alpha 1.0"},
}
CONFIG_ORDER = list(CONFIG_SPECS)
MAQAM_ORDER = ["Hijaz", "Kurd", "Nahawand", "Ajam"]
# GPU binary / regenerable build artifacts: ignored unless --include-weights.
DEFAULT_EXCLUDE = ["bin_sm89", "bin", "merged", "audiocpp_cli*", "*.safetensors"]


def human_wall(txt: str) -> Optional[float]:
    """'4:17.90' or '1:02:03' -> seconds."""
    m = re.search(r"Elapsed \(wall clock\) time \(h:mm:ss or m:ss\):\s*([\d:.]+)", txt)
    if not m:
        return None
    parts = [float(p) for p in m.group(1).split(":")]
    sec = 0.0
    for p in parts:
        sec = sec * 60 + p
    return sec


def parse_time_file(path: Path) -> dict:
    if not path.is_file():
        return {}
    txt = path.read_text(errors="ignore")
    out: dict = {}
    w = human_wall(txt)
    if w is not None:
        out["wall_s"] = w
    m = re.search(r"Exit status:\s*(\d+)", txt)
    if m:
        out["exit"] = int(m.group(1))
    m = re.search(r"Maximum resident set size \(kbytes\):\s*(\d+)", txt)
    if m:
        out["max_rss_kb"] = int(m.group(1))
    return out


def parse_status_for(path: Path, maqam: str, seed: str) -> dict:
    """cap / mode for one specific track out of a config's cumulative _runs_status.log."""
    if not path.is_file():
        return {}
    txt = path.read_text(errors="ignore")
    m = re.search(rf"=== START {re.escape(maqam)} seed={re.escape(seed)} "
                  rf"cap=(\d+) \((\w+)\)", txt)
    if not m:
        return {}
    return {"cap": int(m.group(1)), "cap_mode": m.group(2)}


def parse_log(path: Path) -> dict:
    if not path.is_file():
        return {}
    txt = path.read_text(errors="ignore")
    out: dict = {}
    m = re.search(r"yue2\.semantic\.truncated\s+(\d+)", txt)
    if m:
        out["truncated"] = bool(int(m.group(1)))
    m = re.search(r"yue2\.vae_decode\.output_frames\s+(\d+)", txt)
    if m:
        out["duration_from_frames_s"] = int(m.group(1)) / 48000.0
    return out


def ffprobe_duration(path: Path) -> Optional[float]:
    exe = shutil.which("ffprobe")
    if not exe:
        return None
    try:
        r = subprocess.run(
            [exe, "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", str(path)],
            capture_output=True, text=True, timeout=60)
        return float(r.stdout.strip()) if r.returncode == 0 and r.stdout.strip() else None
    except Exception:
        return None


def load_specs(target: Path) -> Dict[str, dict]:
    specs = {k: dict(v) for k, v in CONFIG_SPECS.items()}
    manifest = target / "sweep_manifest.json"
    if manifest.is_file():
        try:
            data = json.loads(manifest.read_text())
            for cfg, c in (data.get("configs") or {}).items():
                specs.setdefault(cfg, {})
                specs[cfg].update({
                    "alpha": c.get("alpha"),
                    "pron_checkpoint": c.get("pron_checkpoint"),
                    "merged_sha256": c.get("merged_sha256"),
                    "converted_ar_sha256": c.get("converted_ar_sha256"),
                    "converted_nar_sha256": c.get("converted_nar_sha256"),
                })
                if "pron_step" not in specs[cfg]:
                    pc = str(c.get("pron_checkpoint"))
                    specs[cfg]["pron_step"] = 6100 if pc == "final" else (int(pc) if pc.isdigit() else None)
        except Exception as e:  # pragma: no cover
            print(f"[warn] could not read {manifest}: {e}")
    return specs


def is_excluded(rel: Path, patterns: List[str]) -> bool:
    parts = rel.parts
    for pat in patterns:
        for p in parts:
            if Path(p).match(pat):
                return True
    return False


def discover(target: Path, specs: Dict[str, dict], excludes: List[str]):
    """Return (config_ids, tracks). `_`-prefixed folders (e.g. _smoke) are flagged
    as smoke and searched one level deeper (their config subdirs)."""
    tracks: List[dict] = []
    config_ids: set = set()
    for d in sorted([p for p in target.iterdir() if p.is_dir()], key=lambda p: p.name):
        if is_excluded(d.relative_to(target), excludes):
            continue
        if any(d.glob("*.wav")):
            cfg_dirs = [d]
        else:
            cfg_dirs = [s for s in sorted(d.iterdir())
                        if s.is_dir() and any(s.glob("*.wav"))]
        for cfg_dir in cfg_dirs:
            if is_excluded(cfg_dir.relative_to(target), excludes):
                continue
            leaf = cfg_dir.name
            rel_dir = cfg_dir.relative_to(target)
            smoke = any(part.startswith("_") for part in rel_dir.parts)
            if not smoke:
                config_ids.add(leaf)
            for wav in sorted(cfg_dir.glob("*.wav")):
                stem = wav.stem
                if "_" in stem:
                    maqam, seed = stem.rsplit("_", 1)
                else:
                    maqam, seed = stem, ""
                t: dict = {"cfg": leaf, "smoke": smoke,
                           "rel": wav.relative_to(target), "wav": wav,
                           "maqam": maqam,
                           "seed": int(seed) if seed.isdigit() else None}
                t.update(parse_time_file(cfg_dir / f"{stem}_time.txt"))
                t.update(parse_log(cfg_dir / f"{stem}.log"))
                t.update(parse_status_for(cfg_dir / "_runs_status.log", maqam, seed))
                dur = ffprobe_duration(wav)
                t["duration_s"] = dur if dur is not None else t.get("duration_from_frames_s")
                tracks.append(t)
    return sorted(config_ids), tracks


def fmt(v, nd=2):
    if v is None:
        return "—"
    if isinstance(v, float):
        return f"{v:.{nd}f}"
    return str(v)


def config_label(cfg: str, spec: dict) -> str:
    a = spec.get("alpha")
    ck = spec.get("pron_checkpoint")
    a_txt = "—" if a is None else f"{float(a):g}"
    return f"{cfg} (pron={ck}, alpha={a_txt})"


def write_markdown(target: Path, md_path: Path, specs, config_ids, tracks, excludes):
    normal = [t for t in tracks if not t.get("smoke")]
    smoke = [t for t in tracks if t.get("smoke")]
    L: List[str] = []
    L.append("# pron_alpha_sweep — index\n")
    L.append(f"Generated by `organize_pron_sweep.py` from `{target}` on "
             f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}.\n")
    L.append("Naming: `alpha` is the pronunciation-adapter strength folded into the merged "
             "AR LoRA; foldered as `<pron-ckpt>_a<alpha>`. `a0` is the alpha=0 baseline, "
             "which reproduces v2 verbatim.\n")
    L.append("## What the config folder names mean\n")
    L.append("| folder | pron checkpoint | pron step | alpha | meaning |")
    L.append("|---|---|---:|---:|---|")
    for cfg in CONFIG_ORDER + [c for c in config_ids if c not in CONFIG_ORDER]:
        if cfg not in specs:
            continue
        s = specs[cfg]
        note = s.get("note", "")
        if not note:
            note = f"pron step {s.get('pron_step')} at alpha {s.get('alpha')}"
        L.append(f"| `{cfg}` | {s.get('pron_checkpoint','—')} | "
                 f"{s.get('pron_step','—')} | {fmt(s.get('alpha'),2)} | {note} |")
    L.append("")
    L.append("## Tracks\n")
    L.append("| config | alpha | pron ckpt | maqam | seed | cap | duration (s) | wall (s) | "
             "exit | truncated | file |")
    L.append("|---|---:|---|---|---:|---:|---:|---:|---:|:--:|---|")
    for t in normal:
        cfg = t["cfg"]
        s = specs.get(cfg, {})
        L.append(
            f"| `{cfg}` | {fmt(s.get('alpha'),2)} | {s.get('pron_checkpoint','—')} | "
            f"{t.get('maqam','—')} | {t.get('seed','—')} | {t.get('cap','—')} | "
            f"{fmt(t.get('duration_s'),1)} | {fmt(t.get('wall_s'),1)} | "
            f"{t.get('exit','—')} | {'YES' if t.get('truncated') else 'no'} | "
            f"`{t['rel']}` |")
    if smoke:
        L.append("\n## Smoke (cap 750, not part of the 20-song grid)\n")
        L.append("| config | maqam | seed | duration (s) | wall (s) | exit | file |")
        L.append("|---|---|---:|---:|---:|---:|---|")
        for t in smoke:
            L.append(f"| `{t['cfg']}` | {t.get('maqam','—')} | {t.get('seed','—')} | "
                     f"{fmt(t.get('duration_s'),1)} | {fmt(t.get('wall_s'),1)} | "
                     f"{t.get('exit','—')} | `{t['rel']}` |")
    L.append("\n## Excluded from this index (by default)\n")
    L.append("Ignored: " + ", ".join(f"`{p}`" for p in excludes) +
             " — GPU binary and regenerable merged/build artifacts "
             "(use `--include-weights` to list them).\n")
    md_path.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {md_path}")


def flatten(target: Path, out_dir: Path, tracks, link: bool, specs):
    out_dir.mkdir(parents=True, exist_ok=True)
    n = 0
    for t in tracks:
        cfg = t["cfg"]
        s = specs.get(cfg, {})
        a = "—" if s.get("alpha") is None else f"{float(s['alpha']):g}"
        ck = s.get("pron_checkpoint", "?")
        name = (f"{t.get('maqam','?')}__alpha{a}__pron{ck}__"
                f"seed{t.get('seed','?')}__{cfg}.wav")
        dest = out_dir / name
        if dest.exists():
            continue
        if link:
            dest.symlink_to(t["wav"].resolve())
        else:
            shutil.copy2(t["wav"], dest)
        n += 1
    verb = "symlinked" if link else "copied"
    print(f"{verb} {n} WAVs -> {out_dir}")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("target", type=Path, help="path to a downloaded pron_alpha_sweep/ dir")
    p.add_argument("--md", type=Path, default=None,
                   help="markdown output (default: <target>/ORGANIZED.md)")
    p.add_argument("--json", type=Path, default=None,
                   help="machine-readable config map (default: <target>/config_map.json)")
    p.add_argument("--flatten", type=Path, default=None,
                   help="also write descriptively-named WAVs here (audio untouched)")
    p.add_argument("--link", action="store_true",
                   help="with --flatten, symlink instead of copy")
    p.add_argument("--include-weights", action="store_true",
                   help="do not skip bin_*/merged/*.safetensors")
    p.add_argument("--exclude", action="append", default=None,
                   help="extra exclude glob (repeatable)")
    args = p.parse_args()

    target = args.target.resolve()
    if not target.is_dir():
        print(f"[error] not a directory: {target}")
        return 1

    excludes = [] if args.include_weights else list(DEFAULT_EXCLUDE)
    if args.exclude:
        excludes += args.exclude

    specs = load_specs(target)
    configs, tracks = discover(target, specs, excludes)
    if not tracks:
        print(f"[error] no .wav files found under {target} (excluding {excludes})")
        return 1
    grid = [t for t in tracks if not t.get("smoke")]
    smoke = [t for t in tracks if t.get("smoke")]

    md_path = args.md or (target / "ORGANIZED.md")
    json_path = args.json or (target / "config_map.json")
    write_markdown(target, md_path, specs, configs, tracks, excludes)

    config_map = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_dir": str(target),
        "configs": {c: specs.get(c, {}) for c in configs},
        "tracks": [
            {"config": t["cfg"], "maqam": t.get("maqam"), "seed": t.get("seed"),
             "cap": t.get("cap"), "duration_s": t.get("duration_s"),
             "wall_s": t.get("wall_s"), "exit": t.get("exit"),
             "truncated": t.get("truncated"), "smoke": t.get("smoke", False),
             "file": str(t["rel"])}
            for t in tracks
        ],
    }
    json_path.write_text(json.dumps(config_map, indent=2), encoding="utf-8")
    print(f"wrote {json_path}")

    if args.flatten:
        flatten(target, args.flatten, grid, args.link, specs)

    n_bad = sum(1 for t in grid if t.get("exit") not in (0, None))
    n_trunc = sum(1 for t in grid if t.get("truncated"))
    print(f"{len(grid)} grid tracks indexed ({len(smoke)} smoke); "
          f"exit!=0: {n_bad}; truncated: {n_trunc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
