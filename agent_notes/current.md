# current.md — handoff surface (overwritten each turn; not a source of truth)

## Next action — run the lever probe on the GPU VM

New files (commit `jarir_lever_probe`):
- `INFERENCE/songs.jarir_lever_probe.json` — 8-song Tier1(prompt/lyrics) × Tier3(merge) matrix,
  seed `20261011`, cap 8000, Maqam Kurd, Jarir poem (verbatim + canonical lyrics variants).
- `INFERENCE/songs.jarir_lever_scale.json` — 1 fixed song `jlv_scale_ref` for the scale/sampler arms.
- `INFERENCE/jarir_lever_probe.sh` — driver for the 9 Tier0(AR/NAR scale) + Tier2(sampler) arms.

Driver arms (all on `jlv_scale_ref`, paired seed):
`v2_1.0_1.0`(ref) · `qa_1.0_1.0`(baseline) · `qa_0.5_1.0` · `qa_1.0_0.5` · `qa_0.0_1.0` ·
`qa_0.5_1.0_rp1.4` · `qa_0.5_1.0_t0.8` · `qa_0.5_1.0_g1.0` · `qa_0.5_1.0_notrigger`.
Budget: 8 + 9 = 17 tracks ≈ ~110 min T4 / ~50 min L4.

### Prereqs
- `bash bootstrap/setup.sh --inference` done; GPU idle (`nvidia-smi`).
- Stage the α0.1 merge (`qahh_a0p1` = quran_ahh_r8 AR+NAR rank32 merged into v2):
  ```
  gsutil -m cp -r "$GCP_BACKUP_BASE/quran_ahh_r8_rank32/maqamrock_merge/convert/qahh_a0p1" \
    /content/converter/out/
  sha256sum /content/converter/out/qahh_a0p1/*_ar.safetensors   # expect 4b4d2103…dac0ecb
  ```

### Commands
```
cd /content/maqamrock-yue2-lora-finetuning
# smoke gate (1 track, ~6-11 min, foreground)
ARMS="qa_1.0_1.0" bash INFERENCE/jarir_lever_probe.sh
# Tier 1/3 prompt/lyrics/merge matrix (detached)
MODE=prompt setsid nohup bash INFERENCE/jarir_lever_probe.sh > /content/logs/jarir_lever_prompt.log 2>&1 & disown
# Tier 0/2 scale + sampler arms (detached)
setsid nohup bash INFERENCE/jarir_lever_probe.sh > /content/logs/jarir_lever_scale.log 2>&1 & disown
```
stop `pkill -f jarir_lever_probe`; resume = same command (fixed `--out-dir`).
Output: `/content/audiocpp_inference/out/jarir_lever_probe/{prompt,<arm>}/`.

## Branch / push
This commit is on `pron-lora-long-aya`. Remote default is `main` — the VM must be on
`pron-lora-long-aya` (fetch + checkout) or the new files will be absent.

## Open decisions
- 2nd seed / `repeat:2` for robustness (single seed isolates levers only).
- NAR-only quran merge (Tier3 option a) — NOT built; CPU step (variant of `merge_quran_lora.py`).

## Backup
After the batch: `python backup_to_gcp.py --inference --once`.
