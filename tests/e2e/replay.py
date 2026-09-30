"""Record -> replay runner for the GPU-free e2e tiers (docs/E2E_TESTING_PLAN.md §4).

`make_replay_runner` returns a callable with the same signature as
`generate.subprocess_runner`, so it can be injected as `run_batch(..., runner=...)`
without touching `run_one.sh` or the device. It writes the per-track files that
`run_one.sh` writes, synthesized from a recorded `recorded_batch.json` (Tier A).
The WAV is rebuilt with stdlib `wave` at the recorded duration -- recorded audio
bytes are provenance, never asserted (plan §4.2).
"""
from __future__ import annotations

import json
import wave
from pathlib import Path
from typing import Callable, TextIO

GPU_CSV_HEADER = "gpu_util_pct,mem_used_mib,power_draw_w,temp_c\n"
WAV_RATE = 8000  # arbitrary; only the recorded duration matters to the pipeline


def load_recorded_batch(path: Path) -> dict:
    spec = json.loads(Path(path).read_text(encoding="utf-8"))
    if spec.get("schema") != 1:
        raise ValueError(f"{path}: unsupported recorded_batch schema {spec.get('schema')!r}")
    tracks = spec.get("tracks")
    if not isinstance(tracks, list) or not tracks:
        raise ValueError(f"{path}: 'tracks' must be a non-empty list")
    for i, t in enumerate(tracks):
        for key in ("name", "seed", "exit"):
            if key not in t:
                raise ValueError(f"{path}: tracks[{i}] missing required key {key!r}")
    return spec


def _synth_wav(path: Path, duration_s: float, rate: int = WAV_RATE) -> None:
    frames = max(1, int(round(float(duration_s) * rate)))
    with wave.open(str(path), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"\x00\x00" * frames)


def make_replay_runner(recorded_batch, *, rate: int = WAV_RATE) -> Callable:
    spec = (recorded_batch if isinstance(recorded_batch, dict)
            else load_recorded_batch(recorded_batch))
    by_key = {(t["name"], str(t["seed"])): t for t in spec["tracks"]}

    def runner(cmd: list[str], env: dict, log_fh: TextIO) -> int:
        name, seed = cmd[2], cmd[3]
        try:
            t = by_key[(name, seed)]
        except KeyError:
            raise KeyError(
                f"no recorded fixture for (name={name!r}, seed={seed!r}); add it to "
                f"tests/fixtures/recorded_batch.json") from None
        out = Path(env["OUT_DIR"])
        out.mkdir(parents=True, exist_ok=True)
        if t.get("duration_s") is not None:  # a failed run may have produced no WAV
            _synth_wav(out / f"{name}_{seed}.wav", t["duration_s"], rate)
        (out / f"{name}_{seed}_time.txt").write_text(
            f"\tExit status: {t['exit']}\n", encoding="utf-8")
        (out / f"{name}_{seed}.log").write_text(t.get("log_text", ""), encoding="utf-8")
        (out / f"{name}_{seed}_gpu.csv").write_text(GPU_CSV_HEADER, encoding="utf-8")
        with (out / "_runs_status.log").open("a", encoding="utf-8") as f:
            f.write(f"=== START {name} seed={seed} cap={t.get('cap')} (replay) ===\n")
            f.write(f"=== END {name} seed={seed} exit={t['exit']} (replay) ===\n")
        log_fh.write(f"[replay] {name} seed={seed} exit={t['exit']}\n")
        return int(t["exit"])

    return runner
