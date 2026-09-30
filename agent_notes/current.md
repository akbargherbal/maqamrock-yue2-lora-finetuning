# current

_Copy surface, not authority. 2026-09-30 · Colab **CPU-only** (no `nvidia-smi`, 2 vCPU/12 GiB), branch `music-cover` @ `ad5c338`._

## Rehearsed the rescue workflow (CPU `--plan`/`--verify`, no GPU) — verdict: mechanics READY
Driver `INFERENCE/rescue_abc_batch.sh` (`docs/PRON_LORA_RESCUE.md` phase 4). It renders **qfinal_a0.3 + `cot=melody` + `abc_file`**, seeded from the pass-1 `batch_manifest.json` + `prompts/`. Verified here:
- **Bulk** — a 14-stem selection → `n=14`, index + sha256 pairing OK, `--verify` OK.
- **Bulk w/ no selectors** over this partial batch → **aborts** (gate G3 validates every one of the 24 manifest tracks; 10 have no WAV/ABC) — expected; enumerate instead.
- **Pick** — `--songs <stem>` → 1 track; `--songs <name>` → both takes → `n=2`. Both OK.
- **New selector input `--songs-json FILE`** (edit a copy of `INFERENCE/rescue_selection.example.json`):
  `{"songs": [<name-or-stem> | {"stem"|"name", "note"}]}`. Verified `n=5` on the example.
- Preconditions proven: pass-1 dir needs `batch_manifest.json` + `prompts/` (staged 24 files) and `--abc-dir/<stem>/score.abc` (14/14 done).
- Bulk stem list at `/content/rescue_stems.txt` (14 stems).

## NOT proven / gaps
- **B2 guide quality is unrun** (§8) — `--smoke` one track first on the T4.
- Render needs a GPU; `--plan`/`--verify` are CPU-only.
- `generate.py` (arbitrary-manifest bulk) still has **no cot/abc field** — qfinal+ABC bulk only via the rescue driver, only for tracks already in a pass-1 manifest.
- Selection is a filter over the pass-1 manifest; it cannot pull in songs that were never pass-1 rendered.

## T4 recipe (fresh VM, GPU free)
```bash
# 0. stage: binary+models+v2 (setup.sh --inference); then qfinal (setup stages v2 only)
bash bootstrap/setup.sh --inference
for a in qfinal_a0.3 qfinal_a0.5; do gsutil -m cp -r \
  gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/loras/audio_cpp/pron/$a /content/converter/out/; done
# 1. bring the pass-1 set + ABCs local (GCS mirrors of this VM's out/)
gsutil -m cp -r gs://…/audiocpp_inference/workspace/out/batch_12_rock_v2 /content/audiocpp_inference/out/
gsutil -m cp -r gs://…/audiocpp_inference/workspace/out/abc_v2_batch12 /content/audiocpp_inference/out/
# 2. plan (no GPU) -> smoke -> full (all stems, or a hand-picked selection file)
cp maqamrock-yue2-lora-finetuning/INFERENCE/rescue_selection.example.json /content/m_selection.json  # edit
B=/content/audiocpp_inference/out
bash INFERENCE/rescue_abc_batch.sh --pass1-dir $B/batch_12_rock_v2 --abc-dir $B/abc_v2_batch12 \
  --out-dir $B/rescue_v2abc_batch12 --songs-json /content/m_selection.json --plan
bash INFERENCE/rescue_abc_batch.sh … --smoke     # listen before committing the batch
bash INFERENCE/rescue_abc_batch.sh … --songs-json /content/m_selection.json
```
Stop: `pkill -f rescue_abc_batch.sh` · resume: same command (skips succeeded). Then P5 `prepare_ab_eval.py`.

## Backup — up
`backup_to_gcp.py --inference` (every 5 min); ABCs at `…/workspace/out/abc_v2_batch12/` (14/14).
