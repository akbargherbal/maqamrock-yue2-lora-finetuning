# current

## 0. Resume this session on the VM (conversation continuity)
The conversation (not just the repo) is archived — the exact OpenCode session JSON:
```
gs://akbar-december-2024-backup/opencode_sessions/by_id/ses_f17ef5af2ffeK15W1EBgAHpDJT.json
```
2,323,607 B, md5 `s3fHuoDGomE0v0bcDH+Hkg==` (uploaded 2026-09-28; re-export + re-cp to refresh).

Restore on the VM (terminal: foreground, quick):
```bash
gsutil cp gs://akbar-december-2024-backup/opencode_sessions/by_id/ses_f17ef5af2ffeK15W1EBgAHpDJT.json /content/
cd /content/maqamrock-yue2-lora-finetuning          # import target = cwd (there is NO --directory flag)
opencode import /content/ses_f17ef5af2ffeK15W1EBgAHpDJT.json
opencode -s ses_f17ef5af2ffeK15W1EBgAHpDJT          # or pick it in the session list
```
Restores the **conversation** (turns + tool calls + outputs); does **not** restore the
environment — repo/model/GPU must exist on the VM, and history paths are the local box's
(`/home/akbar/…`). The repo carries the *work*; this JSON carries the *chat*. (`opencode
export --sanitize` exists if a less-private copy is ever needed.)

## 1. Smoke test — ABC extraction (SheetSage2)
Driver `INFERENCE/abc_transcribe.py` (committed on `music-cover` @ 985db9e). audio.cpp path
(`--task midi --family sheetsage2`), sequential, resumable, `--limit` + `--time-budget`;
writes `<stem>.abc` + `_timings.csv` + `transcribe_manifest.json`. `ruff check` clean;
dry-run/resume/fail-fast/budget verified locally on fakes. **Exact sheetsage2 flags are
unverified** (no upstream doc) — the smoke is the test; no ABC ⇒ prints the log tail and stops.

Prereqs on the VM:
```bash
hf download audio-cpp/SheetSage2-GGUF sheetsage2-orig.gguf \
  --local-dir /content/audiocpp_inference/models/SheetSage2-GGUF   # 2.71 GB FP32; Q8 unsafe
ls /content/audiocpp_inference/out/batch_36_songs/*.wav | wc -l    # expect 36
ls -l /content/audiocpp_inference/bin/audiocpp_cli
```
Smoke — terminal: **foreground** (Ctrl+C safe; rerun resumes):
```bash
cd /content/maqamrock-yue2-lora-finetuning
python INFERENCE/abc_transcribe.py --limit 1
```
Full batch — terminal: **detached**; stop `pkill -f abc_transcribe.py`; resume = rerun:
```bash
mkdir -p /content/logs
setsid nohup python INFERENCE/abc_transcribe.py --time-budget 1200 \
  --gcs gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/audiocpp_inference/out/sheetsage2_abc \
  > /content/logs/abc_transcribe.log 2>&1 & disown
```

## 2. Rock-forward arm for the `batch_36_songs` controls
`manifests/batch_36_rock.json` (committed): 12 songs, `qfinal_a0.3`, **same seeds+caps as the
controls**, rock-forward style. Run (detached):
```bash
setsid nohup python INFERENCE/generate.py manifests/batch_36_rock.json \
  --out-dir /content/audiocpp_inference/out/batch_36_rock \
  > /content/logs/batch_36_rock.log 2>&1 & disown
```
Stop: `pkill -f 'generate.py manifests/batch_36_rock.json'`. Resume: rerun.

## 3. Approach 2 (audio-guided) — verdict 2026-09-28
No audio2audio input exists (verified upstream). YuE2 "cover" = symbolic: audio → ABC →
`cot=melody`. SheetSage2 is now in-stack (audio.cpp v0.8.0). Forms: (①) **ABC cover**
(preferred) = v2 wav → SheetSage2 → `melody.abc` → qfinal_a0.3 `cot=melody` + `abc_file`;
(②) `semantic_prefix` token transfer — but pron is **AR-only** (`config/pron_lora_ar_only.yml:38`,
`merge_pron_lora.py:20`), so a full prefix freezes the very stream the fix lives in. Risk:
adapters trained `cot=off` → ABC off-distribution (that's what the smoke tests).

## Staging
Branch `music-cover` @ 049df65 carries: `INFERENCE/abc_transcribe.py`, `manifests/batch_36_rock.json`,
`docs/music-cover-feasibility.md` (SheetSage2-in-stack + AR-only caveat corrected), this file.
No audio downloaded locally. vm-continuity cloned to `/tmp/opencode/vm-continuity` (examined only).
