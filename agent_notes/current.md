# current

## 1. Smoke test — ABC extraction (SheetSage2) — **needs the script on the VM first**

New driver: `INFERENCE/abc_transcribe.py` (untracked). audio.cpp path
(`--task midi --family sheetsage2`), sequential, resumable, `--limit` +
`--time-budget`, writes `<stem>.abc` + `_timings.csv` + `transcribe_manifest.json`.
`ruff check` clean; dry-run + resume + fail-fast + budget verified locally on fakes.
**Exact sheetsage2 flags are unverified** (no upstream doc) — the smoke run is the test;
if a track yields no ABC the script prints the log tail and stops.

Prereqs on the VM (Colab):
```bash
# weights: 2.71 GB, self-contained FP32 (Q8 is NOT safe for this task)
hf download audio-cpp/SheetSage2-GGUF sheetsage2-orig.gguf \
  --local-dir /content/audiocpp_inference/models/SheetSage2-GGUF
# inputs — only if this VM did not render batch_36_songs
ls /content/audiocpp_inference/out/batch_36_songs/*.wav | wc -l   # expect 36
# binary present?
ls -l /content/audiocpp_inference/bin/audiocpp_cli
```

Smoke — terminal: **foreground** (watch it; Ctrl+C is safe, rerun resumes).
```bash
python /content/maqamrock-yue2-lora-finetuning/INFERENCE/abc_transcribe.py --limit 1
```

Full batch — terminal: **detached** (survives Ctrl+C / closing the tab); stop:
`pkill -f abc_transcribe.py`; resume: rerun same command (done ABCs are skipped).
```bash
mkdir -p /content/logs
python /content/maqamrock-yue2-lora-finetuning/INFERENCE/abc_transcribe.py \
  --time-budget 1200 \
  --gcs gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/audiocpp_inference/out/sheetsage2_abc \
  2>&1 | tee /content/logs/abc_transcribe.log
```
(Run it under `setsid nohup … & disown` for a true detach.)

## 2. Pending — rock-forward arm for the `batch_36_songs` controls
`manifests/batch_36_rock.json` (untracked, dry-run-validated): 12 songs, `qfinal_a0.3`,
**same seeds+caps as the controls**, rock-forward style. Run (detached):
```bash
setsid nohup python INFERENCE/generate.py manifests/batch_36_rock.json \
  --out-dir /content/audiocpp_inference/out/batch_36_rock \
  > /content/logs/batch_36_rock.log 2>&1 & disown
```
Stop: `pkill -f 'generate.py manifests/batch_36_rock.json'`. Resume: rerun.

## 3. Approach 2 (audio-guided) — verdict 2026-09-28
No audio2audio input exists (verified upstream). YuE2 "cover" = symbolic: audio → ABC →
`cot=melody`. SheetSage2 is now in-stack (audio.cpp v0.8.0). Two forms: (①) **ABC cover** =
existing v2 wav → SheetSage2 → `melody.abc` → qfinal_a0.3 `cot=melody` + `abc_file` — preferred;
(②) `semantic_prefix` token transfer — but pron is **AR-only** (`config/pron_lora_ar_only.yml:38`,
`merge_pron_lora.py:20`), so a full prefix freezes the very stream the fix lives in. Risk: adapters
were trained `cot=off` → ABC off-distribution (that's what the smoke tests).

## Staging
Untracked: `manifests/batch_36_rock.json`, `INFERENCE/abc_transcribe.py`. Branches: `music-cover`
has `docs/music-cover-feasibility.md` (its "SheetSage2 not ported" line is now stale — to fix).
No audio downloaded locally.
