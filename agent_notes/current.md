# current

## State @ 2026-10-04: Quran-only (α=1) first sample DONE — branch `experimental-quran-pron`

T4, host `3631c29a716b`. Nothing running except `backup_to_gcp.py --inference`. GPU idle.
Full record: **`docs/QURAN_ONLY_EXPERIMENT.md`** (authority). This file is the handoff.

### Result
First song of `manifests/batch_36_songs.json` (`07-الحر-الشديد-وقطع-القفر-والوعول`),
style replaced with the unaccompanied-recitation caption, Quran pron LoRA alone (AR 1.0,
NAR off), seed `20261004`:

- **exit 0**, wall 1:52, **52.2 s** WAV, `truncated=false`.
- wav: `/content/audiocpp_inference/out/quran_only_sample/07-الحر-الشديد-وقطع-القفر-والوعول_20261004.wav`
  (sha256 `ff21ed9f74fc2884ba5465aecfdedf0bd575a8727989887ef24738a0681464c2`); GCS-mirrored.
- **It stopped after ~one aya** (1304 semantic tokens, cap 7500, `truncated 0` = natural EOS).
  Expected: the adapter is AR-only and its training clips were single long-ayat recitations
  (~23 s avg, `max_words=60`), so it recites ~one and stops. Not a bug; raising the cap won't
  help. To do a full poem, chunk the lyrics to that length and stitch takes.

### Adapter(s) built
- Quran pron source: `/content/pron_src/quran_long_aya_r8_s10.safetensors` (sha `f8c842e4…`).
- The converter **requires both AR and NAR**; the AR-only direct convert fails. Built a fused
  `AR=pron + NAR=zeros` with `build_pron_only_fused.py`, then converted →
  `/content/converter/out/quran_only/quran_long_aya_r8_s10_{ar,nar}.safetensors`
  (AR rank 8 real, NAR rank 8 zeros).
- Controls staged: `/content/converter/out/akbar_arabic_rock_lora_{ar,nar}.safetensors`
  (v2) and, if needed, `qfinal_a0.3`/`qfinal_a0.5` (pull from `<base>/loras/audio_cpp/pron/`).

### Environment gotcha (bit us once)
On this CUDA-13 image the prebuilt sm_75 `audiocpp_cli` needs the **CUDA-12** libs that ship
in the pip `nvidia-*-cu12` packages, or it dies instantly (`exit=127`,
`libcublas.so.12: cannot open shared object file`). Always export first:
```bash
cd /content/maqamrock-yue2-lora-finetuning
export LD_LIBRARY_PATH="$(find /usr/local/lib/python3.13/dist-packages/nvidia \
  -maxdepth 2 -type d \( -name lib -o -name lib64 \) | tr '\n' ':')/usr/lib64-nvidia"
ldd /content/audiocpp_inference/bin/audiocpp_cli | grep 'not found' || echo OK
```
See `docs/COMMAND_HANDOVER_GOTCHAS.md` (2026-10-04).

### Next steps (pick up here)
1. **Listen** to the wav; judge articulation of the hard letters (ح خ ع أ ق ط).
2. Run the **comparison arms** with the SAME seed + lyrics, for a blind A/B
   (`docs/AB_BLIND_EVAL.md`, skill `ab-blind-eval`):
   - base (AR+NAR off): `LORA_AR_SCALE=0 LORA_NAR_SCALE=0`
   - quran-AR + v2-NAR: `quran_only` AR (1.0) + v2 NAR (1.0)
   - `qfinal_a0.5`: both 1.0
   `INFERENCE/run_one.sh` reads `LORA_AR_SCALE` / `LORA_NAR_SCALE` (default 1.0; 0 = off).
3. Optional: **chunked** run (2–3 verse groups, same seed) to confirm length-per-clip and to
   actually render the full poem.

### Continuity / backup
- `vm-continuity` healthy (loop running); `backup_to_gcp.py --inference` running.
- Re-run a one-shot mirror: `python backup_to_gcp.py --inference --once`.
