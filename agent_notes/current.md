# current.md — 2026-10-11 · v3 "spice" sweep (Stage A done; Stage B on the T4)

Task (user, this session): "implement + run" the CPU-written plan — that is
**`docs/V3_SPICE_SWEEP.md`** (the 10-arm paired "spice" screen: `ref · g1.5 · g2.5 · t1.2 ·
t1.4 · rp1.4 · ar0.7 · ck4500 · ck3500 · ck2500`, pinned seed `2640605763`, cap 6500).
Context: `docs/V3_JARIR_SEED_PROBE.md` was the *earlier* plan and already ran 2026-10-10
(`…/out/20261010-142358_v3_jarir_seeds`, 4/5 good) — not re-run here.

## Stage A — DONE (CPU; committed this session)
- Converted v3 checkpoints **2500/3500/4500** with the torch-free converter (byte-verified) and
  banked `<base>/v3_arabmaqamrock_lora/convert/ck{000002500,000003500,000004500}/`.
- `INFERENCE/songs.v3_spice.json` — style+lyrics byte-identical to the v3 training caption,
  `seed 2640605763`, `cap 6500`, `defaults.repeat 1`.
- `INFERENCE/v3_spice_probe.sh` — verbatim from §7; `bash -n` clean.
- `DRY=1 bash INFERENCE/v3_spice_probe.sh` → **all 10 arms plan** (1 track each, cap 6500, q0.95). ✅

## Stage B — T4
1. `bash bootstrap/setup.sh --inference` → `/content/logs/setup.log` (in progress).
2. `gcloud storage rsync -r <base>/v3_arabmaqamrock_lora/convert /content/converter/out` — **done**
   (final + ck*/ pairs staged locally; dry-run confirmed).
3. Detached run:
```bash
cd /content/maqamrock-yue2-lora-finetuning
setsid nohup bash INFERENCE/v3_spice_probe.sh \
  > /content/logs/v3_spice_probe.log 2>&1 < /dev/null & disown
tail -f /content/logs/v3_spice_probe.log
```
Expected ~95 min (10 arms × ~9.5 min). Output `/content/audiocpp_inference/out/v3_spice_probe/<arm>/`,
self-banked to `<base>/v3_arabmaqamrock_lora/spice_probe/`.

## Notes
- Doc nit (not touched): `V3_JARIR_SEED_PROBE.md` §5 line 80 says `cap: 8000`; §7 decision 2, §3, and
  the JSON all say 6500.
- One shared GPU (T4): `nvidia-smi` before the run; never overlap. Agent judges no audio — the user
  listens.
