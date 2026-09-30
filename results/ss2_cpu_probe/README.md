# ss2_cpu_probe — SheetSage2 audio→ABC on CPU (2026-09-30)

Feasibility measurement: can the **B2** transcription step (`m-a-p/SheetSage2`,
melody-only audio → ABC) run on a **CPU-only** Colab box, and how slow is it?
No GPU in the box; this is the free/High-RAM CPU-runtime path, not a T4 run.

## Box

| | |
|---|---|
| Runtime | Colab **High-RAM CPU** runtime, `accelerator=None` |
| GPU | none (`nvidia-smi` absent) |
| CPU / RAM | x86_64, **8 cores**, **50 GiB** |
| Python | 3.11.16 |
| Torch / HF | `torch 2.8.0+cpu`, `transformers 4.45.2`, `huggingface_hub 0.36.0` |
| Model | `m-a-p/SheetSage2` by repo id, F32, `melody_only=True`; load 10.3 s |

## Command

```bash
ffmpeg -y -i /content/sample_song.mp3 -t 60 /content/song60.wav
bash INFERENCE/ss2_probe.sh /content/song60.wav /content/sample_song.mp3
```

`sample_song.mp3` is a Suno-made track (`comment=made with suno`), 48 kHz stereo,
316.6 s (5:17). `song60.wav` is its first 60 s.

## Results (raw `RESULT` lines)

```
RESULT song60: transcribe_s=93.3  abc_bytes=589  peak_ram_GB=3.74
RESULT sample_song: transcribe_s=235.5  abc_bytes=2937  peak_ram_GB=4.31
```

| audio | length | transcribe_s | abc_bytes | peak_ram_GB |
|---|---|--:|--:|--:|
| `song60.wav` | 60.0 s | 93.3 | 589 | 3.74 |
| `sample_song.mp3` | 316.6 s | 235.5 | 2937 | 4.31 |

Full log: [`ss2_probe.log`](ss2_probe.log).

## Core scaling

Same 60 s clip, one warm process, `torch.set_num_threads` varied
([`ss2_threads.log`](ss2_threads.log)); torch's own default on the 8-core box was 4.

| threads | clip transcribe_s | peak_ram_GB |
|--:|--:|--:|
| 8 | 96.1 | 3.95 |
| 4 | 101.3 | 4.10 |
| 2 | 139.6 | 4.11 |
| 1 | 261.5 | 4.16 |

Full 5:17 file at **2 threads** ([`ss2_t2_full.log`](ss2_t2_full.log)):

```
RESULT sample_song_t2: transcribe_s=347.6  peak_ram_GB=4.30
```

## Reading

- CPU is **viable for one ≤10-min track**: peak RAM ~4.3 GB and the 5:17 file transcribed
  in 0.74× realtime. A free 2-vCPU / 12 GB runtime suffices; the 50 GiB High-RAM tier is
  unnecessary. 8 cores are not needed — throughput saturates near 4 threads (8→4 was 5%),
  and 2 vCPU is ~1.5× slower than 4.
- Note the fixed per-call cost (~70 s at 4 threads, ~90 s at 2): short clips look
  disproportionately slow, so `clip × len/60` overestimates long tracks. Fitting the two
  measured points gives `t ≈ 91 + 0.81·len` at 2 threads (~10 min for a 600 s track).
- Scope: this measures the **transcription step only**. Whether the melody-only SheetSage2
  ABC steers arrangement as well as v2's full plan (the B2 guide round) remains unrun
  (`docs/music-cover-feasibility.md` §4.2, §8).

## Provenance

Scratch probe, run 2026-09-30. Driver `INFERENCE/ss2_probe.sh` + `ss2_probe.py`; thread
and free-tier follow-ups were ad-hoc (`/content/ss2_threads.py`, `/content/ss2_t2_full.py`).
Environment/traps: load by repo id, clear the `transformers_modules` cache, run under the
`/content/.ss2` venv, `hf` not `huggingface-cli`, gated repos need `HF_TOKEN`.
