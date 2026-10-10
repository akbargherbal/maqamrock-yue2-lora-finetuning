# current.md — v3 probe 4/5 good; "spice" sweep planned, to implement on Colab (2026-10-10)

## State
- Training done (v3, 5000/5000). Final adapter converted + banked (`<base>/v3_arabmaqamrock_lora/convert/`).
- **T4 seed probe RAN** — `<base>/audiocpp_inference/out/20261010-142358_v3_jarir_seeds`.
  5 takes, **all exit 0, none truncated**, 213–234 s each, ~9.4 min/track (T4), total 47:12.
  Adapter = final/5000 (`3531bb91…` AR / `a7eabcad…` NAR), scale 1.0/1.0, `cot=off`, sampler
  defaults (guidance 1.01, temp 1.0, rep-pen 1.2), cap 6500 (q0.95).
  **User verdict: 4/5 good; the takes feel flat / "generic" — wants 5/5, asks about checkpoints.**

## Deliverable this session
- **`docs/V3_SPICE_SWEEP.md`** — the plan (written; **not started**). Implement on Colab:
  - §4 is a **Pass 1 paired single-knob screen** (10 arms, ~95 min on a T4): `ref`, `g1.5`, `g2.5`,
    `t1.2`, `t1.4`, `rp1.4`, `ar0.7`, `ck4500`, `ck3500`, `ck2500`.
  - §7 has the CPU-runtime conversion/staging commands + the input-JSON and driver-script spec
    (driver logic syntax-checked).
  - §5: Pass 2 = winning config × 8 seeds. §6: optional improvisation-cue prompt variant.
- Index updated: `docs/README.md` + `SOURCE_OF_TRUTH.md`.

## Key fact (shapes the whole plan)
v3 trained with `cot: "off"` → the LoRA learned **style/timbre**, not melody. So a **checkpoint**
re-tints *sound*; "spice / improvisation" is the **AR composer**, fixed by sampler + prompt +
selection. Checkpoints exist: `…/output/v3_arabmaqamrock_lora_000000250 … _000004750` + final.

## ⚠️ Provenance bug found (non-blocking)
`batch_manifest.json` top-level `assets.lora_ar_sha256` = `747d5cfe…` = **v2**, `assets.checkpoint_step`
= **3000** — built from the CLI-default pair (`INFERENCE/generate.py:552`), not the per-song alias.
Per-track sidecars are correct. See plan §8.

## Environment
- Agent env: **no GPU**. GCS works via `CLOUDSDK_CONFIG=/mnt/c/Users/DELL/AppData/Roaming/gcloud`
  (Windows gcloud; the WSL `~/.config/gcloud` refresh token is dead — `gcloud auth login` there if needed).
- Next: move to Colab and implement `docs/V3_SPICE_SWEEP.md` (Stage A CPU → Stage B T4).
