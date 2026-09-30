# current

_Updated 2026-09-30 (localhost). Handoff — read this first. Scratch probe, not authority._

## Why we're here (context for a fresh session)
The plan under test is the **v2 → audio2sheet → qfinal rescue** flow in
`docs/music-cover-feasibility.md` (§4.2 route **B2**, §7): generate with the rock model (v2),
keep the good takes, and for takes whose **pronunciation** fails, hand their score to the
clear-singing model (`qfinal_a0.X`) so it keeps the maqamrock arrangement but sings cleanly.
Route **B1** (v2's own `score.abc`, no transcription) already won at n=1 (§7). The scaling
question for **B2**: **can the audio→ABC transcription (SheetSage2) run on CPU, or does it
need a GPU?** T4 works (established); CPU time is the unknown. That is all this probe measures.

## Run the probe (Colab; scratch)
```bash
bash INFERENCE/ss2_probe.sh /content/sample_song.mp3      # no args -> this path
# clip-first for a cheap estimate:
ffmpeg -y -i /content/sample_song.mp3 -t 60 /content/song60.wav
bash INFERENCE/ss2_probe.sh /content/song60.wav /content/sample_song.mp3
```
`ss2_probe.sh` builds `/content/.ss2` (py3.11 venv, pinned torch/transformers), warms ffmpeg,
sources `HF_TOKEN`, then runs `ss2_probe.py`. GPU vs CPU is auto-detected.

## Hand back (what I need to debug)
The `RESULT <tag>: transcribe_s=… abc_bytes=… peak_ram_GB=…` lines, plus any traceback.
`clip60` × (audio_len_s / 60) ≈ full-file estimate.

## Files
- `INFERENCE/ss2_probe.py` — probe: loads SheetSage2 by repo id, clears the module cache,
  times load+transcribe, prints peak RAM/VRAM.
- `INFERENCE/ss2_probe.sh` — venv + ffmpeg wrapper.
- `agent_notes/CPU_benchmark.ipynb` — notebook version (session state, gitignored; superseded).

## Traps already solved (baked into the probe)
1. **Load by repo id, not a local dir** — local `trust_remote_code` cached only the entry
   module and died on `chord_spelling_sheetsage2.py`.
2. Clear `~/.cache/huggingface/modules/transformers_modules` before loading.
3. Run under the venv; multi-line code lives in a file, never a `!`-cell heredoc.
4. `huggingface-cli` is deprecated → `hf`.
5. `HF_TOKEN` required for the gated `SheetSage2` + `MERT-v2-FullSong` repos.

## Facts
- SheetSage2 head 57.2M / 229 MB + backbone MERT-v2-FullSong 632M (~2.5 GB); 24 kHz mono,
  processor `window_seconds=300`. License CC BY-NC 4.0.
- T4 works (established). This measures **CPU** — F32; BF16 speedup is GPU-only.
- Box seen: High-RAM, x86_64, 8 cores, 50 GiB RAM.

## Next
- Run the probe, read `RESULT`; if CPU is prohibitive, keep audio2sheet on a GPU box.
- Open from §8: replicate §7's B1 result on the other two seeds; B2 (this ABC route) still unrun.

_Not authority — re-derive from the artifacts (`python status.py`)._
