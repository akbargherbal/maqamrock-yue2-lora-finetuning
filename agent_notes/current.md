# current.md — handoff surface (overwritten each turn; not a source of truth)

## NOW → launch the D-test render on the GPU VM (background)
_Written 2026-10-07. Branch `pron-lora-long-aya` @ `81df998` (pushed)._

### Where we are
- Rename + legacy-retire DONE (repo + GCS). D-test scorecard written
  (`INFERENCE/scorecards/dtest_diction.json`).
- **Next action: render the D-test audio** — v2 vs qahh `a0p1`, AR/NAR split, 4 paired seeds.

### What to render (5 arms × 4 seeds = 20 takes, ~65–70 min)
Arms: `v2_1.0_1.0` (no donor) · `qa_1.0_1.0` (both) · `qa_0.5_1.0` (AR half) ·
`qa_1.0_0.5` (NAR half) · `qa_0.0_1.0` (AR off). Fixture: `INFERENCE/songs.dtest.json`
(pinned Jarir song `jlv_dtest`, seeds 20261021–024, cap 8000).

### Launch (detached; returns immediately)
```
cd /content/maqamrock-yue2-lora-finetuning
git fetch origin pron-lora-long-aya && git checkout pron-lora-long-aya && git pull --ff-only   # -> 81df998
nvidia-smi    # GPU must be free
mkdir -p /content/logs
ARMS="v2_1.0_1.0 qa_1.0_1.0 qa_0.5_1.0 qa_1.0_0.5 qa_0.0_1.0" \
SCALE_JSON="/content/maqamrock-yue2-lora-finetuning/INFERENCE/songs.dtest.json" \
OUTROOT="/content/audiocpp_inference/out/jarir_dtest" \
setsid nohup bash INFERENCE/jarir_lever_probe.sh > /content/logs/jarir_dtest.log 2>&1 & disown
```
- **Stop:** `pkill -f jarir_lever_probe.sh; pkill -f audiocpp_cli`
- **Resume:** re-run the same command (generate.py skips tracks whose `_time.txt` says exit 0).
- **Monitor:** `tail -f /content/logs/jarir_dtest.log` · per-arm WAVs in
  `/content/audiocpp_inference/out/jarir_dtest/<arm>/jlv_dtest_<seed>.wav`.

### Prereqs (verify before launch; do NOT guess)
- v2: `/content/converter/out/akbar_arabic_rock_lora_{ar,nar}.safetensors`
- donor: `/content/converter/out/qahh_a0p1/akbar_arabic_rock_lora_{ar,nar}.safetensors`
  (restore: `gsutil -m cp "$GCP_BACKUP_BASE/quran_ahh_r32/maqamrock_merge/convert/qahh_a0p1/*" /content/converter/out/qahh_a0p1/`)
- binary `.../audiocpp_inference/bin/audiocpp_cli` + models `Yue2-3B-GGUF`

### After render
rsync `out/jarir_dtest` → GCS `audiocpp_inference/out/jarir_dtest`, download locally, point the
new rating app at it: `py app.py --audio <dir> --config configs/blind_eval.json --scorecard dtest_diction`.

### Facts
- `$GCP_BACKUP_BASE` = `gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning`
- New scorecard id: `dtest_diction`; arms = subfolder names (report groups by parent).
