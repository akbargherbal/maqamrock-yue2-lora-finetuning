#!/usr/bin/env python3
"""Cross-maqam lyric swap: one maqam's caption+tag with the other's held-out lyric.

Two swap groups x two pron configs (`a0`, `c3050_a0.5`) = 4 tracks:

  KurdStyle_HijazLyrics   Kurd caption/maqam tag  + Hijaz held-out lyric
  HijazStyle_KurdLyrics   Hijaz caption/maqam tag + Kurd held-out lyric

Same generation seed as the fine sweep (20260924) and the same auto-cap
convention: the cap is derived from the lyric file actually used, so it follows
the swapped-in lyric (Hijaz lyric -> 7250, Kurd lyric -> 6500). Strictly
sequential (two concurrent runs can OOM the NAR graph).

Reuses the canonical sidecar policy from DECISIONS.md: every track gets a full
JSON sidecar, written before generation and updated after, with the swap axes,
seed, command, prompt/adapter/model hashes, checkpoint step, GPU/attention, cap,
truncated, wall time and the WAV sha256. Everything lands under
/content/maqam_lyric_swap/ so the run is self-contained and resumable.

Usage:
    python INFERENCE/maqam_lyric_swap.py --dry-run   # print the plan, no GPU
    python INFERENCE/maqam_lyric_swap.py             # real run
"""
from __future__ import annotations

import argparse
import os
import sys
import time
import wave
from pathlib import Path

INFERENCE = Path(__file__).resolve().parent
sys.path.insert(0, str(INFERENCE))
import generate as G  # noqa: E402  (module-level constants only; main is guarded)

SEED = 20260924
WORK = Path("/content/maqam_lyric_swap")
CONVERTED = WORK / "converted"
PROMPTS = Path("/content/audiocpp_inference/prompts")
V2_RAW = Path("/content/ai-toolkit/output/akbar_arabic_rock_lora/akbar_arabic_rock_lora.safetensors")
PRON_DIR = Path("/content/ai-toolkit/output/pron_lora_ar_only_r8")
AUDIO_CPP = Path("/content/audio.cpp")

# (config, pron checkpoint, alpha). `a0` reproduces v2 verbatim; `c3050_a0.5` is
# v2 + the pron-3050 adapter at the shipped alpha 0.5.
CONFIGS = [("a0", 3050, 0.0), ("c3050_a0.5", 3050, 0.5)]

# Group-major, config-minor. `style_maqam` picks the caption+tag; `lyrics_maqam`
# picks the held-out lyric that is swapped in.
SWAPS = [
    {"group": "KurdStyle_HijazLyrics", "style_maqam": "Kurd", "lyrics_maqam": "Hijaz"},
    {"group": "HijazStyle_KurdLyrics", "style_maqam": "Hijaz", "lyrics_maqam": "Kurd"},
]


def wav_frames(path: Path) -> int | None:
    try:
        with wave.open(str(path), "rb") as w:
            return w.getnframes()
    except Exception:
        return None


def plan() -> list[dict]:
    """Resolve each track's inputs + auto cap without touching the GPU."""
    tracks = []
    for sw in SWAPS:
        style = PROMPTS / f"{sw['style_maqam']}_style.txt"
        lyrics = PROMPTS / f"{sw['lyrics_maqam']}_lyrics.txt"
        cap = G.duration_cap(G.arabic_letters(lyrics.read_text(encoding="utf-8")))[2]
        for cfg, ckpt, alpha in CONFIGS:
            out = WORK / sw["group"] / cfg
            tracks.append({
                "group": sw["group"],
                "style_maqam": sw["style_maqam"],
                "lyrics_maqam": sw["lyrics_maqam"],
                "config": cfg,
                "alpha": alpha,
                "pron_checkpoint": ckpt,
                "style_file": style,
                "lyrics_file": lyrics,
                "cap": cap,
                "out": out,
                "ar": CONVERTED / cfg / "akbar_arabic_rock_lora_ar.safetensors",
                "nar": CONVERTED / cfg / "akbar_arabic_rock_lora_nar.safetensors",
                "merged": WORK / "merged" / cfg / "akbar_arabic_rock_lora.safetensors",
            })
    return tracks


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="print the plan (caps, hashes, adapters) and exit; no GPU")
    args = ap.parse_args()

    tracks = plan()
    if args.dry_run:
        for t in tracks:
            print(f"[{t['group']} {t['config']}] style={t['style_file'].name} "
                  f"lyrics={t['lyrics_file'].name} cap={t['cap']} M={t['style_maqam']} "
                  f"out={t['out']}")
            print(f"    style_sha={G.sha256_file(t['style_file'])}")
            print(f"    lyrics_sha={G.sha256_file(t['lyrics_file'])}")
            print(f"    ar_sha={G.sha256_file(t['ar'])} nar_sha={G.sha256_file(t['nar'])}")
        return 0

    gpu = G.gpu_info()
    if gpu is None:
        G.fail("nvidia-smi did not report a GPU")
    audio_commit = G.git_commit(AUDIO_CPP)
    WORK.mkdir(parents=True, exist_ok=True)
    driver_log = open(WORK / "_driver.log", "a", encoding="utf-8")
    print(f"GPU: {gpu['name']} (CC {gpu['compute_cap']}) | audio.cpp {audio_commit}")
    print(f"seed={SEED}  work={WORK}\n")

    for t in tracks:
        M = t["style_maqam"]
        out = t["out"]
        out.mkdir(parents=True, exist_ok=True)
        wav = out / f"{M}_{SEED}.wav"
        tfile = out / f"{M}_{SEED}_time.txt"
        log = out / f"{M}_{SEED}.log"
        sidecar = out / f"{M}_{SEED}.json"

        if G._succeeded(wav, tfile):
            print(f"[skip] {t['group']} {t['config']} (already succeeded)")
            continue

        cmd_str = (
            f"OUT_DIR={out} STYLE_FILE={t['style_file']} LYRICS_FILE={t['lyrics_file']} "
            f"LORA_AR={t['ar']} LORA_NAR={t['nar']} "
            f"bash INFERENCE/run_one.sh {M} {SEED} {t['cap']}"
        )
        fields = {
            "config": t["config"],
            "alpha": t["alpha"],
            "pron_checkpoint": t["pron_checkpoint"],
            "group": t["group"],
            "style_maqam": t["style_maqam"],
            "lyrics_maqam": t["lyrics_maqam"],
            "maqam": M,  # the tag/caption actually used (what run_one.sh sees)
            "seed": SEED,
            "cap": t["cap"],
            "cap_mode": "auto",
            "command": cmd_str,
            "run_one": f"INFERENCE/run_one.sh {M} {SEED} {t['cap']}",
            "style_file": str(t["style_file"]),
            "style_sha256": G.sha256_file(t["style_file"]),
            "lyrics_file": str(t["lyrics_file"]),
            "lyrics_sha256": G.sha256_file(t["lyrics_file"]),
            "lora_ar_path": str(t["ar"]),
            "lora_ar_sha256": G.sha256_file(t["ar"]),
            "lora_nar_path": str(t["nar"]),
            "lora_nar_sha256": G.sha256_file(t["nar"]),
            "v2_raw_path": str(V2_RAW),
            "v2_raw_sha256": G.sha256_file(V2_RAW),
            "pron_ckpt_path": str(PRON_DIR / f"pron_lora_ar_only_r8_{t['pron_checkpoint']:09d}.safetensors"),
            "pron_ckpt_sha256": G.sha256_file(PRON_DIR / f"pron_lora_ar_only_r8_{t['pron_checkpoint']:09d}.safetensors"),
            "merged_path": str(t["merged"]),
            "merged_sha256": G.sha256_file(t["merged"]),
            "model_gguf": G.MODEL_GGUF,
            "model_gguf_sha256": G.sha256_file(G.MODEL_DIR / G.MODEL_GGUF),
            "vae_gguf": G.VAE_GGUF,
            "vae_gguf_sha256": G.sha256_file(G.MODEL_DIR / G.VAE_GGUF),
            "binary_path": "/content/audiocpp_inference/bin/audiocpp_cli",
            "binary_sha256": G.sha256_file(Path("/content/audiocpp_inference/bin/audiocpp_cli")),
            "attention": "flash",
            "cot": "off",
            "checkpoint_step": t["pron_checkpoint"],
            "audio_cpp_commit": audio_commit,
            "gpu": gpu["name"],
            "compute_cap": gpu["compute_cap"],
            "status": "started",
            "start_utc": G.utcnow(),
        }
        G._write_sidecar(sidecar, fields)
        print(f"=== [{t['group']} {t['config']}] cap={t['cap']} start={fields['start_utc']} ===")

        env = dict(os.environ)
        env.update({
            "OUT_DIR": str(out),
            "STYLE_FILE": str(t["style_file"]),
            "LYRICS_FILE": str(t["lyrics_file"]),
            "LORA_AR": str(t["ar"]),
            "LORA_NAR": str(t["nar"]),
        })
        t0 = time.monotonic()
        rc = G.subprocess_runner(["bash", str(G.RUN_ONE), M, str(SEED), str(t["cap"])], env, driver_log)
        wall = time.monotonic() - t0

        dur = G.wav_duration(wav)
        trunc, trunc_src = G.truncation_info(log, dur, t["cap"])
        fields.update({
            "exit": rc,
            "end_utc": G.utcnow(),
            "wall_s": round(wall, 1),
            "wav_sha256": G.sha256_file(wav) if wav.is_file() else None,
            "wav_duration_s": round(dur, 2) if dur is not None else None,
            "wav_frames": wav_frames(wav),
            "truncated": trunc,
            "truncated_source": trunc_src,
            "status": "ok" if rc == 0 else "failed",
        })
        G._write_sidecar(sidecar, fields)
        print(f"    exit={rc} wall={wall:.1f}s dur={dur} truncated={trunc}")
        if rc != 0:
            G.wait_vram_free()
    print("\n=== maqam_lyric_swap done ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
