#!/usr/bin/env python3
"""Pron checkpoint sweep: v2 + pron ckpt {1525, 4575} at alpha 0.5, Hijaz + Kurd.

Renders the two new pron checkpoints at the already-shipped `alpha=0.5`, on the
same held-out inputs as `results/pron_fine_sweep/` (same staged prompts, same
generation seed 20260924, same auto cap). 2 configs x 2 maqams = 4 tracks,
strictly sequential (two concurrent runs can OOM the NAR graph).

Reuses the canonical sidecar policy from DECISIONS.md: every track gets a full
JSON sidecar, written before generation and updated after, with seed, command,
prompt/adapter/model hashes, checkpoint step, GPU/attention, cap, truncated,
wall time and the WAV sha256. Writes everything under /content/pron_ckpt_sweep/
so each config's tracks stay self-contained and the run is resumable.

Usage: python INFERENCE/pron_ckpt_sweep.py
"""
from __future__ import annotations

import json
import os
import sys
import time
import wave
from pathlib import Path

INFERENCE = Path(__file__).resolve().parent
sys.path.insert(0, str(INFERENCE))
import generate as G  # noqa: E402  (module-level constants only; main is guarded)

SEED = 20260924
WORK = Path("/content/pron_ckpt_sweep")
CONVERTED = WORK / "converted"
PROMPTS = Path("/content/audiocpp_inference/prompts")
V2_RAW = Path("/content/ai-toolkit/output/akbar_arabic_rock_lora/akbar_arabic_rock_lora.safetensors")
PRON_DIR = Path("/content/ai-toolkit/output/pron_lora_ar_only_r8")
AUDIO_CPP = Path("/content/audio.cpp")

# Maqam-major (all configs of Hijaz before Kurd), matching the prior sweeps.
MAQAMS = ["Hijaz", "Kurd"]
CONFIGS = [("c1525_a0.5", 1525, 0.5), ("c4575_a0.5", 4575, 0.5)]


def wav_frames(path: Path) -> int | None:
    try:
        with wave.open(str(path), "rb") as w:
            return w.getnframes()
    except Exception:
        return None


def main() -> int:
    gpu = G.gpu_info()
    if gpu is None:
        G.fail("nvidia-smi did not report a GPU")
    audio_commit = G.git_commit(AUDIO_CPP)
    WORK.mkdir(parents=True, exist_ok=True)
    driver_log = open(WORK / "_driver.log", "a", encoding="utf-8")
    print(f"GPU: {gpu['name']} (CC {gpu['compute_cap']}) | audio.cpp {audio_commit}")
    print(f"seed={SEED}  work={WORK}\n")

    for M in MAQAMS:
        style = PROMPTS / f"{M}_style.txt"
        lyrics = PROMPTS / f"{M}_lyrics.txt"
        cap = G.duration_cap(G.arabic_letters(lyrics.read_text(encoding="utf-8")))[2]
        style_sha = G.sha256_file(style)
        lyrics_sha = G.sha256_file(lyrics)

        for cfg, ckpt, alpha in CONFIGS:
            out = WORK / cfg
            out.mkdir(parents=True, exist_ok=True)
            ar = CONVERTED / cfg / "akbar_arabic_rock_lora_ar.safetensors"
            nar = CONVERTED / cfg / "akbar_arabic_rock_lora_nar.safetensors"
            merged = WORK / "merged" / cfg / "akbar_arabic_rock_lora.safetensors"
            wav = out / f"{M}_{SEED}.wav"
            tfile = out / f"{M}_{SEED}_time.txt"
            log = out / f"{M}_{SEED}.log"
            sidecar = out / f"{M}_{SEED}.json"

            if G._succeeded(wav, tfile):
                print(f"[skip] {cfg} {M} (already succeeded)")
                continue

            cmd_str = (
                f"OUT_DIR={out} STYLE_FILE={style} LYRICS_FILE={lyrics} "
                f"LORA_AR={ar} LORA_NAR={nar} "
                f"bash INFERENCE/run_one.sh {M} {SEED} {cap}"
            )
            fields = {
                "config": cfg,
                "alpha": alpha,
                "pron_checkpoint": ckpt,
                "maqam": M,
                "seed": SEED,
                "cap": cap,
                "cap_mode": "auto",
                "command": cmd_str,
                "run_one": f"INFERENCE/run_one.sh {M} {SEED} {cap}",
                "style_file": str(style),
                "style_sha256": style_sha,
                "lyrics_file": str(lyrics),
                "lyrics_sha256": lyrics_sha,
                "lora_ar_path": str(ar),
                "lora_ar_sha256": G.sha256_file(ar),
                "lora_nar_path": str(nar),
                "lora_nar_sha256": G.sha256_file(nar),
                "v2_raw_path": str(V2_RAW),
                "v2_raw_sha256": G.sha256_file(V2_RAW),
                "pron_ckpt_path": str(PRON_DIR / f"pron_lora_ar_only_r8_{ckpt:09d}.safetensors"),
                "pron_ckpt_sha256": G.sha256_file(PRON_DIR / f"pron_lora_ar_only_r8_{ckpt:09d}.safetensors"),
                "merged_path": str(merged),
                "merged_sha256": G.sha256_file(merged),
                "model_gguf": G.MODEL_GGUF,
                "model_gguf_sha256": G.sha256_file(G.MODEL_DIR / G.MODEL_GGUF),
                "vae_gguf": G.VAE_GGUF,
                "vae_gguf_sha256": G.sha256_file(G.MODEL_DIR / G.VAE_GGUF),
                "attention": "flash",
                "cot": "off",
                "checkpoint_step": ckpt,
                "audio_cpp_commit": audio_commit,
                "gpu": gpu["name"],
                "compute_cap": gpu["compute_cap"],
                "status": "started",
                "start_utc": G.utcnow(),
            }
            G._write_sidecar(sidecar, fields)
            print(f"=== [{cfg} {M}] cap={cap} start={fields['start_utc']} ===")

            env = dict(os.environ)
            env.update({
                "OUT_DIR": str(out),
                "STYLE_FILE": str(style),
                "LYRICS_FILE": str(lyrics),
                "LORA_AR": str(ar),
                "LORA_NAR": str(nar),
            })
            t0 = time.monotonic()
            rc = G.subprocess_runner(["bash", str(G.RUN_ONE), M, str(SEED), str(cap)], env, driver_log)
            wall = time.monotonic() - t0

            dur = G.wav_duration(wav)
            trunc, trunc_src = G.truncation_info(log, dur, cap)
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
    print("\n=== pron_ckpt_sweep done ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
