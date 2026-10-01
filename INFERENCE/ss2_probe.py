#!/usr/bin/env python3
"""Scratch probe: time SheetSage2 audio -> ABC on one or more files, CPU or GPU.

Run under the isolated venv (see ss2_probe.sh):
    /content/.ss2/bin/python INFERENCE/ss2_probe.py /content/sample_song.mp3

Traps handled here (each cost us a round-trip):
  * loads by REPO ID, not a local dir -- loading trust_remote_code from a local
    dir caches only the entry module and dies on a sibling import
    (chord_spelling_sheetsage2.py).
  * clears ~/.cache/huggingface/modules/transformers_modules before loading.
  * token from HF_TOKEN env (or --token). Gated: needs access to SheetSage2 and
    MERT-v2-FullSong.
  * prints device, load_s, transcribe_s, peak RAM/VRAM, abc size; on failure it
    dumps the full traceback so the real cause is visible.

This is a scratch artifact, not authority.
"""
from __future__ import annotations

import argparse
import os
import resource
import shutil
import sys
import time
import traceback
from pathlib import Path

REPO_ID = "m-a-p/SheetSage2"
DEFAULT_AUDIO = "/content/sample_song.mp3"


def gb(nbytes: float) -> float:
    return round(nbytes / 1e9, 2)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("audio", nargs="*", default=None)
    ap.add_argument("--out-dir", default="/content/out_ss2_probe")
    ap.add_argument("--model", default=REPO_ID)
    ap.add_argument("--token", default=os.environ.get("HF_TOKEN", ""))
    ap.add_argument("--no-clear-cache", action="store_true")
    ap.add_argument("--no-melody-only", action="store_true",
                    help="default is melody_only=True (cover front end)")
    args = ap.parse_args(argv)

    print("== env ==")
    print("python", sys.version.split()[0], "| cwd", os.getcwd())
    if args.token:
        os.environ["HF_TOKEN"] = args.token

    torch = None
    for name in ("torch", "transformers", "huggingface_hub"):
        try:
            mod = __import__(name)
            print(name, getattr(mod, "__version__", "?"))
        except Exception as exc:  # noqa: BLE001
            print(name, "IMPORT FAIL:", repr(exc))
    try:
        import torch  # noqa: PLC0415
        has_cuda = torch.cuda.is_available()
        print("cuda", has_cuda, torch.cuda.get_device_name(0) if has_cuda else "(cpu)")
    except Exception:  # noqa: BLE001
        has_cuda = False

    try:
        from huggingface_hub import whoami  # noqa: PLC0415
        print("hf user:", whoami().get("name"))
    except Exception as exc:  # noqa: BLE001
        print("hf auth WARN (gated repos will 401):", repr(exc))

    if not args.no_clear_cache:
        cache = Path.home() / ".cache/huggingface/modules/transformers_modules"
        if cache.exists():
            shutil.rmtree(cache, ignore_errors=True)
            print("cleared dynamic-module cache:", cache)

    from transformers import AutoModel  # noqa: PLC0415
    print(f"== loading {args.model} ==")
    t0 = time.perf_counter()
    try:
        model = AutoModel.from_pretrained(args.model, trust_remote_code=True).eval()
        if torch is not None:
            model = model.to("cuda" if has_cuda else "cpu")
            if not has_cuda:
                model = model.float()
        load_s = time.perf_counter() - t0
        dtype = next(model.parameters()).dtype
        print(f"loaded in {load_s:.1f}s  dtype={dtype}  device={'cuda' if has_cuda else 'cpu'}")
    except Exception:  # noqa: BLE001
        print("LOAD FAILED")
        traceback.print_exc()
        return 2

    audios = args.audio or ([DEFAULT_AUDIO] if os.path.isfile(DEFAULT_AUDIO) else [])
    if not audios:
        print(f"no audio given and default {DEFAULT_AUDIO} absent", file=sys.stderr)
        return 3

    for audio in audios:
        audio = str(Path(audio).expanduser())
        if not os.path.isfile(audio):
            print(f"[skip] not a file: {audio}")
            continue
        tag = Path(audio).stem
        out = Path(args.out_dir) / tag
        print(f"== transcribe {audio} -> {out} ==")
        t0 = time.perf_counter()
        try:
            model.transcribe(audio, output_dir=str(out), melody_only=not args.no_melody_only)
        except Exception:  # noqa: BLE001
            print("TRANSCRIBE FAILED")
            traceback.print_exc()
            continue
        dt = time.perf_counter() - t0
        abc = out / "score.abc"
        n = abc.stat().st_size if abc.is_file() else 0
        line = (f"RESULT {tag}: transcribe_s={dt:.1f}  abc_bytes={n}  "
                f"peak_ram_GB={gb(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024)}")
        if torch is not None and has_cuda:
            line += f"  peak_vram_GB={gb(torch.cuda.max_memory_allocated())}"
        print(line)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
