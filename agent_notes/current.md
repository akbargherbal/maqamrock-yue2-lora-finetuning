# current

_Copy surface, not authority. Pass-1 manifest is now **2 takes/song** (random seeds). Rescue
workflow: runbook `docs/PRON_LORA_RESCUE.md`; driver `INFERENCE/rescue_abc_batch.sh --help`;
design `docs/music-cover-workflow.md`. Nothing started — no GPU touched._

## The flow (12 songs → 24 takes)

```bash
# P0 setup (GPU VM): stage binary+models+both LoRAs; branch music-cover; backup sidecar up
gsutil -m cp -r gs://<base>/OSTRIS_Arabic_Suno_Finetuning/loras/audio_cpp/pron/qfinal_a0.3 /content/converter/out/

# P0 validate the manifest (no GPU, writes nothing): expect 12 songs / 24 tracks / ~156 min
python INFERENCE/generate.py manifests/batch_12_rock_v2.json --dry-run

# P1 pass-1 v2  (detached; ~156 min; stop: pkill -f 'generate.py manifests/batch_12_rock_v2.json')
python INFERENCE/generate.py manifests/batch_12_rock_v2.json \
  --out-dir /content/audiocpp_inference/out/batch_12_rock_v2

# P2 transcribe (FREE CPU; ~108 min; force CPU if on the GPU box)
CUDA_VISIBLE_DEVICES="" /content/.venv-sheetsage2/bin/python INFERENCE/sheetsage2_transcribe.py \
  --input-dir /content/audiocpp_inference/out/batch_12_rock_v2 \
  --out-dir   /content/audiocpp_inference/out/abc_v2_batch12 --all

# P3 listen: 2 takes/song; pick the better take per song; M = chosen takes that are
#    maqamrock-OK but pronunciation-bad. Write their STEMS (<name>_<seed>), one per line,
#    to fails.txt (a bare song name rescues ALL its takes; a stem rescues one).

# P4 rescue  (--plan/--verify first, then --smoke 1 track, then the M list)
R=/content/audiocpp_inference/out/rescue_v2abc_batch12
bash INFERENCE/rescue_abc_batch.sh --pass1-dir /content/audiocpp_inference/out/batch_12_rock_v2 \
  --abc-dir /content/audiocpp_inference/out/abc_v2_batch12 --out-dir $R --plan
bash INFERENCE/rescue_abc_batch.sh --pass1-dir ... --abc-dir ... --out-dir $R --smoke
bash INFERENCE/rescue_abc_batch.sh --pass1-dir ... --abc-dir ... --out-dir $R --songs-file /content/fails.txt
```

Key: `<name>_<seed>` keys every stage. Guards: fixed `--out-dir`; fresh abc dir; driver refuses
`--out-dir == pass-1`; values from `batch_manifest.json`; `--smoke` gates B2 (still unrun).
Manifest change: `defaults.repeat: 2`, per-song fixed seeds removed (random per take; recorded in
the run's `batch_manifest.json`).
