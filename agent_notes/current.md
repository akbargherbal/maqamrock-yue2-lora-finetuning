# current.md — 2026-10-11 · v3 "spice" sweep — Pass 1 COMPLETE (10/10)

Plan: `docs/V3_SPICE_SWEEP.md` (the CPU-written 10-arm "spice" screen). Ran on a T4. **All 10 arms
exit 0, none truncated**, banked to `<base>/v3_arabmaqamrock_lora/spice_probe/` (local:
`/content/audiocpp_inference/out/v3_spice_probe/<arm>/`). Total **91.3 min**, mean 9.1 min/arm.

## Results (1 track/arm, seed 2640605763, cap 6500)

| arm | knob | wall | WAV dur | truncated |
|---|---|---:|---:|:--:|
| `ref` | — (final, 1.0/1.0) | 9:25 | 232.7 s | no |
| `g1.5` | `guidance_scale=1.5` | 8:38 | 204.6 s | no |
| `g2.5` | `guidance_scale=2.5` | 8:54 | 217.7 s | no |
| `t1.2` | `semantic_temperature=1.2` | 9:18 | 227.6 s | no |
| `t1.4` | `semantic_temperature=1.4` | 9:23 | 238.0 s | no |
| `rp1.4` | `semantic_repetition_penalty=1.4` | 9:03 | 217.6 s | no |
| `ar0.7` | AR scale 0.7 | 8:19 | 198.0 s | no |
| `ck4500` | checkpoint 4500 | 9:06 | 229.2 s | no |
| `ck3500` | checkpoint 3500 | 9:29 | 234.7 s | no |
| `ck2500` | checkpoint 2500 | 9:42 | 248.4 s | no |

**Determinism check: PASS.** `ref` WAV is byte-identical to probe take 0 —
`sha256 1593f33888d76ebc9e8e2132b92d0f209fd0fbbacc467ee2db10c19a6254280e` == the banked
`…/out/20261010-142358_v3_jarir_seeds/v3_jarir_2640605763.wav`.

## Next
- **User listens/ranks** the 10 arms (agent judges no audio) → keep best 1–2 configs.
- **Pass 2:** winning config × 8 fresh seeds (cap 6500), §5 of the plan.
- Provenance bug (§8): `batch_manifest.json` top-level `assets.*` still reflects the CLI-default
  pair; per-track sidecars are correct.

## Session bookkeeping
- Stage A committed + pushed: `1dc4fc4` (`songs.v3_spice.json`, `v3_spice_probe.sh`, current.md).
- Sidecars: `backup_to_gcp.py --inference` up; `vm-continuity` healthy. One shared T4 — no overlap.
