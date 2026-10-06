# current

> **Session plan:** [`docs/QURAN_AHH_RESUME_PLAN.md`](../docs/QURAN_AHH_RESUME_PLAN.md) Phase 3b —
> T4 epoch test on Ayat al-Kursi (2:255) → blind A/B.
> **This file is a handoff copy surface, not a source of truth** — re-derive from live artifacts.

## State @ 2026-10-06 05:22 UTC — T4, env ready, **re-launch render with CUDA-12 loader path**

Fresh Colab **T4** (`COLAB_GPU=1`), GPU free. Repo `pron-lora-long-aya`, HEAD **`317399f`**.
`setup.sh --inference` done (all `[ok]`, 38 s). Probe arms staged (`c4500 c7500 c9000 c10500
c16500 c19500 final`). `vm-continuity` loop running, `state=OK`.

### Done this session (CPU-only)
Converted **c9000 / c19500 / final** from the banked ai-toolkit checkpoints with the canonical
`convert_aitoolkit_yue2_lora.py` (`--stem quran_ahh_r8`; byte-level verified, rank 32) and banked
them to `…/quran_ahh_r8_rank32/convert/`. `adapter_manifest.json` updated additively
(old copy: `/tmp/opencode/adapter_manifest.backup.json`).

### Run #1 FAILED — CUDA-12 loader (known gotcha, `COMMAND_HANDOVER_GOTCHAS.md:117`)
`setsid … quran_pt_probe.py --arms c9000,c19500,final` → all 6 tracks `exit=127` in the same
second, 0:00 each. Per-track log: `audiocpp_cli: error while loading shared libraries:
libcublas.so.12: cannot open shared object file`. Cause: staged sm_75 binary is **CUDA 12**;
Colab image is **CUDA 13**. Empty run dir: `out/20261006-051955_quran_pt_probe/` (no WAVs).

### Fix — export the CUDA-12 libs on `LD_LIBRARY_PATH` **before** launching (probe rewrites log; fresh out dir)

```bash
cd /content/maqamrock-yue2-lora-finetuning
export LD_LIBRARY_PATH="$(find /usr/local/lib/python3.13/dist-packages/nvidia \
  -maxdepth 2 -type d \( -name lib -o -name lib64 \) | tr '\n' ':')/usr/lib64-nvidia"
ldd /content/audiocpp_inference/bin/audiocpp_cli | grep 'not found' || echo "LOADER OK"
setsid nohup python INFERENCE/quran_pt_probe.py --prefix quran_ahh_r8_rank32/convert \
    --arms c9000,c19500,final > /content/logs/quran_pt_probe_r32_epochs.log 2>&1 & disown
# stop: pkill -f 'quran_pt_probe.py --prefix quran_ahh_r8_rank32'
# progress: tail -f /content/logs/quran_pt_probe_r32_epochs.log ; ls -t /content/audiocpp_inference/out/ | head
```

The `export` must be in the **same shell** as the launch (probe → `generate.py` → `run_one.sh` →
`audiocpp_cli` inherit it). ~39 min for 6 tracks; output → `out/<new-ts>_quran_pt_probe/`.

### Recommendation (not done)
`run_one.sh`/`generate.py` could set `LD_LIBRARY_PATH` themselves (or `setup.sh` export it), so
the dry-run passing doesn't mask a real run that dies at the loader. Flag for a durable fix.

## Still open
- Phase 3b render (above) → blind A/B (`ab-blind-eval`) → verdict in
  `TRAINING_ANALYSIS/quran_ahh_r8_rank32/ANALYSIS.md`.
- Phase 5: rename `quran_ahh_r8` → `quran_ahh_r32`; docs-reconciler; blind gate before any merge.
- Durable fixes: restore helper that fixes ckpt ctime; backup daemon that `wal_checkpoint`s `loss_log.db`.

## Gotchas
- **CUDA-13 image ⇒ export the CUDA-12 `LD_LIBRARY_PATH`** before any `audiocpp_cli` run
  (`COMMAND_HANDOVER_GOTCHAS.md:117`); `--dry-run` does not catch it.
- `run.py -l <log>` **appends** — verify resume with `grep 'Found step' <log> | tail -1`.
- GCS restore randomizes ckpt ctime → auto-resume picks the wrong step; `chmod` (not `touch`) fixes it.
- The probe re-rsyncs the whole convert prefix (~980 MB) each run and exposes no `--out-dir`, so a
  failed render restarts in a fresh folder rather than resuming.
