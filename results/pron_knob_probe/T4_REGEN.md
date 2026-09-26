# T4 re-render of the two lost Kurd WAVs (2026-09-25)

Follow-up to Round 5 (`docs/PRON_LORA_SWEEP.md`). Two Kurd raw artifacts never
reached GCS: the inference backup daemon's last pass was ~15:12:26Z, and the VM
ended before the next pass, so `t0.8/Kurd` (finished 15:12:57) and `rp1.4/Kurd`
(ran 15:13:20–15:17:15) were never mirrored. `/content` is ephemeral, so the
originals are gone.

Because the VM available for the fix is a **Tesla T4 (sm_75)** and the originals
were rendered on an **NVIDIA L4 (sm_89)** with the native sm89 binary, these are
**re-renders, not recoveries**. Inputs are byte-identical to the originals: seed
`20260924`, cap `6500`, `c3050_a0.5` adapters (`33e824f2…` / `7d9324bf…`), Kurd
prompts (`0e789bfd…` / `ac29850a…`), BF16 GGUF (`e37c4613…` / `d4f4a05d…`).
Only two things changed: GPU (L4→T4) and binary (`97028a71…`→`7ad69d1c…`).

## Result — the outputs differ

| track | L4 original | T4 re-render | Δ |
|---|---|---|---|
| `t0.8/Kurd` | `d783a3bb…` / 192.92 s | `37c252c2…` / 204.92 s | +12.0 s |
| `rp1.4/Kurd` | `01e903ed…` / 215.80 s | `ddae993e…` / 187.44 s | −28.4 s |

Both T4 renders `exit=0`, no cap-truncation. This settles the open hypothesis in
`DECISIONS.md` §"audio.cpp seeds and reproducibility": the seed alone does **not**
reproduce a track across GPU/attention architectures.

## Where

- Sidecars: `sidecars_t4_regen/{t0.8,rp1.4}__Kurd.json` (here) — each carries a
  `regen` block naming the L4 original it stands in for, and its `gpu`/
  `compute_cap`/`binary_sha256` fields identify it as T4/sm75.
- Raw output + README: GCS `…/audiocpp_inference/pron_knob_probe/t4_regen/`
  (deliberately a **separate prefix**, so the surviving original L4 `t0.8/Kurd`
  json/log/gpu.csv/time.txt at the canonical path are not overwritten).
- The GCS `listening/PRON_KNOB_PROBE_INPUT/Kurd_C.mp3` (rp1.4) and `Kurd_D.mp3` (t0.8)
  are from the L4 originals and remain the canonical listening copies.

## Caveats

- `audio_cpp_commit` in these sidecars (`9d161964`) is the fresh `bootstrap` clone's
  HEAD, **not** the build commit of the prebuilt binary; `binary_sha256` is the
  authoritative artifact identity.
- `INFERENCE/pron_knob_probe.sh` gained `import re` (its sidecar writer used
  `re.match` without importing `re`, so every run's completion sidecar silently
  failed to write) and `MAQAMS`/`CFGS` env overrides (so a partial regeneration can
  target only the missing tracks).
