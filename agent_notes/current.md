# current

_Copy surface, not authority. Session end · 2026-09-30 · **T4 Colab**, branch `music-cover`._

## Session result — pass-1 winning batch is COMPLETE (and safe)
- **`batch_12_rock_v2_winning`: 24/24 takes**, `ok: 24 / failed: 0`, wall 3:18:27, GPU now idle.
  Manifest `manifests/batch_12_rock_v2_winning.json`; out-dir `…/out/batch_12_rock_v2_winning`.
  Local 24 WAVs = **GCS 24** (`…/audiocpp_inference/workspace/out/batch_12_rock_v2_winning/`).
- Durations 202.9–297.0 s, 48 kHz stereo, `cot=off`.
- Also on GCS: **`batch_12_rock_v2` = 14 takes** (songs 01–07; deliberately stopped earlier) and
  **14 ABCs** in `…/out/abc_v2_batch12`.

> Correction to the earlier note: `batch_12_rock_v2` is **14/24**, not 23/24 — that count isn't
> reflected in this box or GCS. The finished 24-take run is the **winning** one.

## Backup / continuity — CURRENT
- `backup_to_gcp.py --inference` up (pid 11017); last pass **15:47:31 — 5/5 folders synced**.
- `vm-continuity` healthy. GPU idle 0% / 0 MiB. Working tree clean, `music-cover` in sync with origin.

## Next — moves to the operator's other machine (not this T4)
1. Listen to the 24 winning takes; pick which qualify.
2. Write the selection JSON (`INFERENCE/rescue_selection.example.json` → e.g. `/content/m_selection.json`).
3. **P2 transcribe** (free CPU): `bash INFERENCE/ss2_venv.sh` once, then
   `CUDA_VISIBLE_DEVICES="" /content/.venv-sheetsage2/bin/python INFERENCE/sheetsage2_transcribe.py --input-dir "$B/batch_12_rock_v2_winning" --out-dir "$B/abc_v2_batch12_winning" --all`
   (fresh abc dir — G2).
4. **P4 rescue** `qfinal_a0.3` + `cot=melody` + `abc_file` via
   `bash INFERENCE/rescue_abc_batch.sh --songs-json /content/m_selection.json --plan → --smoke → full`
   (`--smoke` first: B2 is still unproven). Full steps: `docs/PRON_LORA_RESCUE.md`.

## Housekeeping left (this VM)
- Consider stopping the Colab T4 runtime — it is now idle and billed.
- `graphify` graph is a few commits behind `HEAD` (commits landed after the refresh).
