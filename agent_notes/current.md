# agent_notes / current

**Date:** 2026-09-28 · **State:** no run active. Local machine (DELL), not Colab.
**Changed:** `INFERENCE/generate.py` now supports **per-song LoRA** via a top-level `loras`
alias registry + a per-song `lora` key. Preflight **existence-checks every referenced
pair** before any GPU work (plain `is_file` — no checksums). `docs/INFERENCE.md` updated.
Tests: `python -m pytest tests/test_generate.py` green (146 total green; torch modules excluded locally).

**JSON (e.g. `INFERENCE/songs.mixed_lora.json`):**
```json
{
  "loras": {
    "v2":          { "dir": "/content/converter/out" },
    "qfinal_a0.3": { "dir": "/content/converter/out/qfinal_a0.3" },
    "qfinal_a0.5": { "dir": "/content/converter/out/qfinal_a0.5" }
  },
  "defaults": { "lora": "v2" },
  "songs": [
    { "name": "pure", "lora": "v2",          "style_file": "...", "lyrics_file": "..." },
    { "name": "p03",  "lora": "qfinal_a0.3", "style_file": "...", "lyrics_file": "..." },
    { "name": "p05",  "lora": "qfinal_a0.5", "style_file": "...", "lyrics_file": "..." }
  ]
}
```
`dir` -> `<dir>/akbar_arabic_rock_lora_{ar,nar}.safetensors`, or explicit `"ar"`+`"nar"`.
Precedence for `lora`: song > `defaults.lora` > `--lora-ar`/`--lora-nar` (or built-in).
Full runnable template on the VM: **`manifests/manifest.example`** (copy + edit).

All commands run on the **Colab VM** (vscode.dev terminal), not the local DELL.

**1. Stage the adapters** (`/content` is ephemeral):
```
terminal: foreground — downloads ~tens of MiB; a few seconds.
```
```bash
B=gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning
mkdir -p /content/converter/out
gsutil -m rsync -r "$B/loras/audio_cpp/style"            /content/converter/out/   # α0 (setup.sh also does this)
gsutil -m cp -r    "$B/loras/audio_cpp/pron/qfinal_a0.3" /content/converter/out/
gsutil -m cp -r    "$B/loras/audio_cpp/pron/qfinal_a0.5" /content/converter/out/
```

**2. Dry-run** (validate JSON + print the plan incl. the per-track `lora`; no GPU, writes nothing):
```
terminal: foreground — instant.
```
```bash
cd /content/maqamrock-yue2-lora-finetuning
python INFERENCE/generate.py INFERENCE/songs.mixed_lora.json --dry-run
```

**3. Real run** (detached — Ctrl+C / closing the tab will NOT stop it):
```
terminal: detached — survives Ctrl+C / closing the tab.
  log:    /content/logs/generate_mixed.log
  stop:   pkill -f 'INFERENCE/generate.py'; pkill -f audiocpp_cli
  resume: re-run the SAME command (same --out-dir); succeeded tracks are skipped.
```
```bash
cd /content/maqamrock-yue2-lora-finetuning
pgrep -af 'INFERENCE/generate.py'        # must print nothing
setsid nohup python INFERENCE/generate.py INFERENCE/songs.mixed_lora.json \
  --out-dir /content/audiocpp_inference/out/mixed_lora \
  > /content/logs/generate_mixed.log 2>&1 < /dev/null & disown
```

**4. Confirm it survived preflight (any missing pair fails within seconds):**
```bash
sleep 10; pgrep -af 'INFERENCE/generate.py' && tail -n 5 /content/logs/generate_mixed.log
```
No PID printed = it died; the log has `[error] preflight failed: missing …`.
Progress/results: `tail -f /content/logs/generate_mixed.log`;
`cat "$(cat /content/audiocpp_inference/out/latest)/batch_summary.txt"`.
Per-track adapter is in each `<name>_<seed>.json` (`lora_alias`, `lora_*_sha256`).
Plan ~6.5 min/track on a T4.
