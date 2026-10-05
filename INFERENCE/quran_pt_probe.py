#!/usr/bin/env python3
"""T4 pron probe: base / quran_only / each `quran_ahh_r8` checkpoint, free-run on the
held-out aya (2:255), one seed. Lone-AR adapters only (no v2 merge), in the exact
training caption format.

The adapters are already converted on the training VM and banked in GCS under
`<base>/quran_ahh_r8/convert/<arm>/` (`<arm>` in {base, quran_only, c<step>, final}).
This stages them, writes a `generate.py` songs JSON, and runs it.

    python INFERENCE/quran_pt_probe.py --dry-run     # validate + print plan (no GPU)
    python INFERENCE/quran_pt_probe.py               # real run on the GPU VM

`base` is an all-zero adapter (AR+NAR) so the base arm runs in the same batch at
scale 1.0. If you distrust it, run base separately with `LORA_AR_SCALE=0
LORA_NAR_SCALE=0` against any real arm (audio.cpp: scale 0 = adapter off).
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HELDOUT = REPO / "INFERENCE/yue2_eval_heldout/quran_heldout.json"
DEFAULT_STAGE = Path("/content/converter/out/probe")
STYLE = (
    "Solo male voice, unaccompanied. Quran recitation in murattal style. "
    "Classical Arabic with tajwīd, precise articulation. Spoken Words."
)
SEED = 20261004
CAP = 7500


def dest_prefix() -> str:
    base = os.environ.get("GCP_BACKUP_BASE")
    if not base:
        sys.exit("GCP_BACKUP_BASE is unset")
    return f"{base}/quran_ahh_r8/convert"


def stage(stage_dir: Path, do_stage: bool) -> None:
    stage_dir.mkdir(parents=True, exist_ok=True)
    if do_stage:
        subprocess.run(["gcloud", "storage", "rsync", "-r", dest_prefix(), str(stage_dir)],
                       check=True)


def discover(stage_dir: Path) -> dict[str, dict[str, str]]:
    arms: dict[str, dict[str, str]] = {}
    for d in sorted(stage_dir.iterdir()):
        ar, nar = d / "quran_ahh_r8_ar.safetensors", d / "quran_ahh_r8_nar.safetensors"
        if d.is_dir() and ar.is_file() and nar.is_file():
            arms[d.name] = {"ar": str(ar), "nar": str(nar)}
    return arms


def arm_order(arms: dict) -> list[str]:
    preferred = ["base", "quran_only"]
    ckpt = sorted((a for a in arms if a.startswith("c") and a[1:].isdigit()),
                  key=lambda a: int(a[1:]))
    return [a for a in preferred if a in arms] + ckpt + (["final"] if "final" in arms else [])


def build_json(arms: dict, scripts: tuple[str, ...]) -> dict:
    aya = json.loads(HELDOUT.read_text())["ayat"][0]
    songs = []
    for arm in arm_order(arms):
        for script in scripts:
            songs.append({
                "name": f"{arm}_{script}",
                "style": STYLE,
                "lyrics": f"[Verse]\n{aya[script]} ۝",
                "seed": SEED,
                "cap": CAP,
                "lora": arm,
            })
    return {"loras": arms, "defaults": {"repeat": 1}, "songs": songs}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stage", default=str(DEFAULT_STAGE), help="local dir for staged arms")
    ap.add_argument("--no-stage", action="store_true", help="skip the GCS rsync (arms already local)")
    ap.add_argument("--scripts", default="uthmani,simple",
                    help="comma list of held-out scripts to render (default both)")
    ap.add_argument("--label", default="quran_pt_probe")
    ap.add_argument("--dry-run", action="store_true", help="pass through to generate.py")
    ap.add_argument("--limit", type=int, default=0, help="pass through to generate.py")
    args = ap.parse_args()

    stage_dir = Path(args.stage)
    stage(stage_dir, do_stage=not args.no_stage)
    arms = discover(stage_dir)
    if not arms:
        sys.exit(f"no arms found under {stage_dir}")
    scripts = tuple(s.strip() for s in args.scripts.split(",") if s.strip())
    plan = build_json(arms, scripts)
    json_path = stage_dir / "songs.quran_pt_probe.json"
    json_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))

    print(f"arms ({len(arms)}): {', '.join(arm_order(arms))}")
    print(f"songs: {len(plan['songs'])} ({len(arms)} arms x {len(scripts)} scripts); json={json_path}")

    cmd = [sys.executable, str(REPO / "INFERENCE/generate.py"), str(json_path),
           "--no-trigger", "--label", args.label]
    if args.dry_run:
        cmd.append("--dry-run")
    if args.limit:
        cmd += ["--limit", str(args.limit)]
    print("run:", " ".join(cmd))
    return subprocess.run(cmd).returncode


if __name__ == "__main__":
    raise SystemExit(main())
