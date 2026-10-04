# current

## DONE: Quran-only first sample — branch `experimental-quran-pron` (2026-10-04, T4)

**Result:** exit 0, wall 1:52, **52.2 s** WAV, `truncated=false`. The model **self-terminated
early** — 1304 semantic tokens (cap 7500, min 200) — so only the first part of the qasida
was rendered. Worth noting for the listening: the Quran-only adapter + unaccompanied caption
stopped well before the lyrics ran out (vs the ~220 s tracks the v2 benchmark produces).
- wav: `/content/audiocpp_inference/out/quran_only_sample/07-الحر-الشديد-وقطع-القفر-والوعول_20261004.wav`
- sha256 `ff21ed9f74fc2884ba5465aecfdedf0bd575a8727989887ef24738a0681464c2`
- backed up to GCS `…/audiocpp_inference/out/quran_only_sample/` (11 objects, 9.57 MiB)


Generating **one** sample from the first song of `manifests/batch_36_songs.json`
(`07-الحر-الشديد-وقطع-القفر-والوعول`), using the **Quran pron LoRA alone (α=1)** with the
style/caption replaced by:

> `Solo male voice, unaccompanied. Quran recitation. Clear precise classical Arabic diction. Spoken Words.`

`[Intro]/[Verse]/[Chorus]/[Outro]` tags kept; the batch's `[Section | …]` descriptors and
`///***///` stripped by the repo's own `suno_to_songs.clean_lyrics`. Seed `20261004`, cap
7500 (auto, q0.95), lora alias `quran_only`.

**terminal: detached** — survives Ctrl+C / closing the tab.
- log: `/content/logs/quran_only_sample.log`
- progress: `tail -f /content/audiocpp_inference/out/quran_only_sample/_driver.log`
- stop: `pkill -f 'INFERENCE/generate.py'`
- resume: re-run the same command (completed tracks are skipped)
- output: `/content/audiocpp_inference/out/quran_only_sample/07-الحر-الشديد-وقطع-القفر-والوعول_20261004.wav`
  (sidecars: `.log`, `_time.txt`, `_gpu.csv`, `.json`)

### Why this adapter (the plan's open question, now resolved)
The audio.cpp converter **requires both AR and NAR branches** — a direct AR-only convert
fails (`ERROR: NAR branch: missing […] expected 28 layers x 4 modules`). Fix used:
- built a fused file = **AR = quran pron (rank 8)** + **NAR = zeros (rank 8)** with
  `/content/quran_only_build/build_fused.py` (zero NAR = no-op → base NAR);
- converted it → `/content/converter/out/quran_only/quran_long_aya_r8_s10_{ar,nar}.safetensors`
  (AR rank 8, nonzero; NAR rank 8, all-zero; converter's byte-level check OK).
- source pron sha256 `f8c842e4…`; fused v2 source sha256 `b1d09098…` (both verified).

Launch command (running now) — **note the `LD_LIBRARY_PATH`**: on this CUDA-13 image the
prebuilt sm_75 binary needs the CUDA-12 libs that ship in the pip `nvidia-*-cu12`
packages (without it the CLI dies instantly with `libcublas.so.12 … exit=127` — see
`docs/COMMAND_HANDOVER_GOTCHAS.md`, 2026-10-04):
```bash
cd /content/maqamrock-yue2-lora-finetuning
export LD_LIBRARY_PATH="$(find /usr/local/lib/python3.13/dist-packages/nvidia \
  -maxdepth 2 -type d \( -name lib -o -name lib64 \) | tr '\n' ':')/usr/lib64-nvidia"
export LORA_AR_SCALE=1.0 LORA_NAR_SCALE=0.0
setsid nohup python INFERENCE/generate.py /content/quran_only_build/song_quran_only.json \
  --no-trigger --out-dir /content/audiocpp_inference/out/quran_only_sample \
  > /content/logs/quran_only_sample.log 2>&1 & disown
```
(`--no-trigger` so `arabmaqamrock ` is NOT prepended to the Quran caption. The one-song
JSON is at `/content/quran_only_build/song_quran_only.json`.)

### Next (after listening)
The full arm matrix (from the earlier plan) still stands — base (AR+NAR off), quran-alone
(shown here), quran-AR + v2-NAR, and `qfinal_a0.5`. `INFERENCE/run_one.sh` gained
`LORA_AR_SCALE`/`LORA_NAR_SCALE` (default 1.0; 0 = off) for exactly these arms.

## Continuity (this session = host 3631c29a716b)
- `vm-continuity` healthy; `backup_to_gcp.py --inference` running (mirrors `out/`).
- CPU-session notes (host 365ac80abf49) are in the shell store, not here.
