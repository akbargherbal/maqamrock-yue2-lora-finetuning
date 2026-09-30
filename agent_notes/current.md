# current

_Copy surface, not authority. Rescue workflow is now implemented — runbook
`docs/PRON_LORA_RESCUE.md`; driver `INFERENCE/rescue_abc_batch.sh --help`; pass-1 manifest
`manifests/batch_12_rock_v2.json`. Findings behind it: `docs/music-cover-feasibility.md`
§2.1 (CPU ABC), §10 (workflow/economics)._

## The flow (12 songs)

```bash
# P0 setup (GPU VM): stage binary+models+both LoRAs; branch music-cover; backup sidecar up
gsutil -m cp -r gs://<base>/OSTRIS_Arabic_Suno_Finetuning/loras/audio_cpp/pron/qfinal_a0.3 /content/converter/out/

# P1 pass-1 v2  (detached; ~78 min; stop: pkill -f 'generate.py manifests/batch_12_rock_v2.json')
python INFERENCE/generate.py manifests/batch_12_rock_v2.json \
  --out-dir /content/audiocpp_inference/out/batch_12_rock_v2

# P2 transcribe (FREE CPU; ~54 min; force CPU if on the GPU box)
CUDA_VISIBLE_DEVICES="" /content/.venv-sheetsage2/bin/python INFERENCE/sheetsage2_transcribe.py \
  --input-dir /content/audiocpp_inference/out/batch_12_rock_v2 \
  --out-dir   /content/audiocpp_inference/out/abc_v2_batch12

# P4 rescue  (--plan/--verify first, then --smoke 1 track, then the M list)
R=/content/audiocpp_inference/out/rescue_v2abc_batch12
bash INFERENCE/rescue_abc_batch.sh --pass1-dir /content/audiocpp_inference/out/batch_12_rock_v2 \
  --abc-dir /content/audiocpp_inference/out/abc_v2_batch12 --out-dir $R --plan
bash INFERENCE/rescue_abc_batch.sh --pass1-dir ... --abc-dir ... --out-dir $R --smoke
bash INFERENCE/rescue_abc_batch.sh --pass1-dir ... --abc-dir ... --out-dir $R --songs-file /content/fails.txt
```

Key: `<name>_<seed>` keys every stage. Guards: fixed `--out-dir`; fresh abc dir; driver refuses
`--out-dir == pass-1`; values from `batch_manifest.json`; `--smoke` gates B2 (still unrun).
Status: ready to run; nothing started (no GPU touched).
