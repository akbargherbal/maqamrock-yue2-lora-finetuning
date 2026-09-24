#!/usr/bin/env python3
"""Generate training-progress charts for a YuE2 LoRA run.

Reads the run's `loss_log.db` (WAL mode -- opened read-only, safe while the
run is writing) and `gpu_usage.csv`, and writes PNGs next to this script.

    # default: the v2 akbar_arabic_rock_lora run (3000 steps, save every 250)
    python TRAINING_ANALYSIS/generate_plots.py

    # a different run / cadence, writing into its own subdirectory
    python TRAINING_ANALYSIS/generate_plots.py \
        --db /content/ai-toolkit/output/pron_lora_ar_only_r8/loss_log.db \
        --total-steps 6100 --save-every 1525 \
        --outdir TRAINING_ANALYSIS/pron_lora_ar_only_r8 \
        --title "pron_lora_ar_only_r8 (AR-only pronunciation LoRA)" \
        --event-label "checkpoint save"

Pure analysis tooling: it only reads, never touches the run.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import sqlite3
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent

# Defaults describe the v2 akbar_arabic_rock_lora run; overridden by argparse.
DB = Path("/content/ai-toolkit/output/akbar_arabic_rock_lora/loss_log.db")
GPU_CSV = Path("/content/logs/gpu_usage.csv")
TOTAL_STEPS = 3000
SAVE_EVERY = 250
OUTDIR = HERE
TITLE = "akbar_arabic_rock_lora"
EVENT_LABEL = "sample/eval"

plt.rcParams.update(
    {
        "figure.dpi": 130,
        "savefig.dpi": 130,
        "font.size": 9,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "axes.axisbelow": True,
        "figure.facecolor": "white",
    }
)


def read_metrics() -> dict:
    if not DB.exists():
        raise SystemExit(f"no loss_log.db at {DB} -- has the run started?")
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=10.0)
    try:
        steps = con.execute("SELECT step, wall_time FROM steps ORDER BY step").fetchall()
        keys = [r[0] for r in con.execute("SELECT key FROM metric_keys ORDER BY key")]
        data: dict[str, np.ndarray] = {}
        for k in keys:
            rows = con.execute(
                "SELECT step, value_real FROM metrics WHERE key = ? AND value_real IS NOT NULL ORDER BY step",
                (k,),
            ).fetchall()
            data[k] = rows
    finally:
        con.close()
    return {"steps": steps, "keys": keys, "data": data}


def rolling(y: np.ndarray, w: int) -> np.ndarray:
    w = max(1, min(w, len(y)))
    if w == 1:
        return y.copy()
    kernel = np.ones(w) / w
    # 'same' keeps x-alignment; edge values are biased by zero-padding, so only
    # trust the interior of the smoothed line.
    pad = w // 2
    ypad = np.pad(y, pad, mode="edge")
    return np.convolve(ypad, kernel, mode="valid")[: len(y)]


def series(rows):
    return (np.asarray([r[0] for r in rows]), np.asarray([r[1] for r in rows], dtype=float))


def plot_loss_curves(m: dict):
    fig, axes = plt.subplots(2, 2, figsize=(12, 7), sharex=True)
    axes = axes.ravel()
    order = ["loss/loss", "loss/ar_ce", "loss/ar_kl", "additional_model_loss"]
    for ax, key in zip(axes, order):
        if key not in m["data"] or len(m["data"][key]) == 0:
            ax.set_visible(False)
            continue
        x, y = series(m["data"][key])
        ysm = rolling(y, 25)
        ax.plot(x, y, color="#9ecae1", lw=0.7, alpha=0.8, label="raw")
        ax.plot(x, ysm, color="#08519c", lw=1.8, label="25-step mean")
        for s in range(SAVE_EVERY, int(x.max()) + 1, SAVE_EVERY):
            ax.axvline(s, color="#bbb", lw=0.5, zorder=0)
        ax.set_title(key)
        ax.set_ylabel("loss")
        ax.legend(fontsize=7, loc="upper right")
    for ax in axes[-2:]:
        ax.set_xlabel("step")
    fig.suptitle(
        f"{TITLE} — per-step loss (grey verticals = {EVENT_LABEL} every {SAVE_EVERY} steps)",
        fontsize=11,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(OUTDIR / "01_loss_curves.png")
    plt.close(fig)


def plot_loss_main(m: dict):
    fig, ax = plt.subplots(figsize=(11, 4.5))
    if "loss/loss" in m["data"] and len(m["data"]["loss/loss"]) > 0:
        x, y = series(m["data"]["loss/loss"])
        ax.plot(x, y, color="#9ecae1", lw=0.7, alpha=0.85, label="raw")
        ax.plot(x, rolling(y, 50), color="#08519c", lw=2.0, label="50-step mean")
        # linear fit on the smoothed trend, to make the direction obvious
        xs = x[len(x) // 10 :]
        ys = rolling(y, 50)[len(x) // 10 :]
        if len(xs) > 2:
            slope, intercept = np.polyfit(xs, ys, 1)
            ax.plot(xs, slope * xs + intercept, "r--", lw=1.5,
                    label=f"trend ({slope:+.2e}/step)")
        ax.set_xlabel("step")
        ax.set_ylabel("loss/loss")
        ax.legend()
    ax.set_title(f"{TITLE} — primary loss (loss/loss); lower is better, early noise is normal")
    fig.tight_layout()
    fig.savefig(OUTDIR / "02_loss_main.png")
    plt.close(fig)


def plot_lr(m: dict):
    fig, ax = plt.subplots(figsize=(11, 3.5))
    if "learning_rate" in m["data"] and len(m["data"]["learning_rate"]) > 0:
        x, y = series(m["data"]["learning_rate"])
        ax.plot(x, y, color="#31a354", lw=1.6)
        ax.set_xlabel("step")
        ax.set_ylabel("learning rate")
    ax.set_title(f"{TITLE} — learning rate schedule")
    fig.tight_layout()
    fig.savefig(OUTDIR / "03_learning_rate.png")
    plt.close(fig)


def plot_throughput(m: dict):
    st = np.asarray([s for s, _ in m["steps"]], dtype=float)
    wt = np.asarray([w for _, w in m["steps"]], dtype=float)
    if len(st) < 3:
        return
    elapsed_h = (wt - wt[0]) / 3600.0
    dt_step = np.diff(wt) / np.diff(st)  # sec per step
    x_rate = st[1:]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 4.2))
    ax1.plot(x_rate, dt_step, color="#fdae6b", lw=0.7, alpha=0.7, label="raw")
    ax1.plot(x_rate, rolling(dt_step, 50), color="#e6550d", lw=1.8, label="50-step mean")
    for s in range(SAVE_EVERY, int(st.max()) + 1, SAVE_EVERY):
        ax1.axvline(s, color="#e0e0e0", lw=0.6, zorder=0)
    ax1.set_xlabel("step")
    ax1.set_ylabel("seconds / step")
    ax1.set_title(f"Throughput (spikes = {EVENT_LABEL} every {SAVE_EVERY})")
    ax1.legend(fontsize=8)

    ax2.plot(elapsed_h, st, color="#08519c", lw=1.8)
    ax2.set_xlabel("wall-clock hours since first logged step")
    ax2.set_ylabel("step")
    ax2.set_title("Progress vs wall-clock (slope = sustained rate)")
    fig.tight_layout()
    fig.savefig(OUTDIR / "04_throughput.png")
    plt.close(fig)


def read_gpu():
    if not GPU_CSV.exists():
        return None
    ts, util, mem, temp, power = [], [], [], [], []
    with GPU_CSV.open() as f:
        for row in csv.DictReader(f):
            try:
                t = dt.datetime.strptime(row["timestamp"], "%Y-%m-%d %H:%M:%S").replace(
                    tzinfo=dt.timezone.utc
                ).timestamp()
                ts.append(t)
                util.append(float(row["gpu_util_pct"]))
                mem.append(float(row["mem_used_mib"]))
                temp.append(float(row["temp_c"]))
                power.append(float(row["power_draw_w"]))
            except (KeyError, ValueError):
                continue
    if not ts:
        return None
    return {
        "t": (np.asarray(ts) - ts[0]) / 3600.0,
        "util": np.asarray(util),
        "mem": np.asarray(mem),
        "temp": np.asarray(temp),
        "power": np.asarray(power),
    }


def plot_gpu(g):
    if not g:
        return
    fig, axes = plt.subplots(4, 1, figsize=(11, 8), sharex=True)
    specs = [
        ("util", "GPU util %", "#08519c"),
        ("mem", "GPU memory (MiB)", "#31a354"),
        ("temp", "temperature (C)", "#e6550d"),
        ("power", "power (W)", "#756bb1"),
    ]
    for ax, (k, label, color) in zip(axes, specs):
        ax.plot(g["t"], g[k], color=color, lw=1.2)
        ax.set_ylabel(label)
    axes[-1].set_xlabel("hours since GPU logger start")
    fig.suptitle(
        f"{TITLE} — GPU telemetry (gpu_logger.py, 10 s samples); flat regions = caching/eval/idle",
        fontsize=11,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(OUTDIR / "05_gpu_usage.png")
    plt.close(fig)


def summary(m: dict) -> str:
    st = np.asarray([s for s, _ in m["steps"]], dtype=float)
    wt = np.asarray([w for _, w in m["steps"]], dtype=float)
    lines = []
    if len(st) == 0:
        return "no steps logged yet"
    elapsed = wt[-1] - wt[0]
    span = max(st[-1] - st[0], 1)
    avg_rate = span / elapsed if elapsed > 0 else 0
    n = min(100, len(st) - 1)
    if n > 0:
        recent_rate = (st[-1] - st[-1 - n]) / (wt[-1] - wt[-1 - n])
    else:
        recent_rate = avg_rate
    remaining = TOTAL_STEPS - st[-1]
    eta_min = remaining / recent_rate / 60 if recent_rate > 0 else float("nan")
    lines.append(f"steps logged: {int(st[-1])} / {TOTAL_STEPS} ({100*st[-1]/TOTAL_STEPS:.1f}%)")
    lines.append(f"elapsed (logged span): {elapsed/3600:.2f} h")
    lines.append(f"avg rate: {avg_rate:.4f} steps/s ({60*avg_rate:.2f} steps/min)")
    lines.append(f"recent rate (last {n}): {recent_rate:.4f} steps/s")
    lines.append(f"ETA at recent rate: {eta_min:.0f} min ({eta_min/60:.2f} h)")
    lines.append("")
    for k in m["keys"]:
        x, y = series(m["data"][k])
        if len(y) < 10:
            continue
        w = max(1, min(50, len(y) // 5))
        first, last = y[:w].mean(), y[-w:].mean()
        lines.append(
            f"{k:24s} first{w}: {first:.4f}  last{w}: {last:.4f}  "
            f"delta: {last-first:+.4f}  min: {y.min():.4f} @ step {int(x[y.argmin()])}"
        )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--db", default=str(DB), help="path to the run's loss_log.db")
    p.add_argument("--gpu-csv", default=str(GPU_CSV), help="path to gpu_usage.csv")
    p.add_argument("--total-steps", type=int, default=TOTAL_STEPS,
                   help="planned total steps (for the progress/ETA summary)")
    p.add_argument("--save-every", type=int, default=SAVE_EVERY,
                   help="checkpoint cadence (vertical lines / spacing)")
    p.add_argument("--outdir", default=str(OUTDIR),
                   help="directory for the PNGs (created if missing)")
    p.add_argument("--title", default=TITLE, help="run name / chart title prefix")
    p.add_argument("--event-label", default=EVENT_LABEL,
                   help="what the grey verticals mark (e.g. 'sample/eval', 'checkpoint save')")
    return p.parse_args()


def main():
    global DB, GPU_CSV, TOTAL_STEPS, SAVE_EVERY, OUTDIR, TITLE, EVENT_LABEL
    args = parse_args()
    DB = Path(args.db)
    GPU_CSV = Path(args.gpu_csv)
    TOTAL_STEPS = args.total_steps
    SAVE_EVERY = args.save_every
    OUTDIR = Path(args.outdir)
    if not OUTDIR.is_absolute():
        OUTDIR = Path.cwd() / OUTDIR
    OUTDIR.mkdir(parents=True, exist_ok=True)
    TITLE = args.title
    EVENT_LABEL = args.event_label

    m = read_metrics()
    plot_loss_curves(m)
    plot_loss_main(m)
    plot_lr(m)
    plot_throughput(m)
    plot_gpu(read_gpu())
    print(summary(m))
    print("\nwrote PNGs to", OUTDIR)


if __name__ == "__main__":
    main()
