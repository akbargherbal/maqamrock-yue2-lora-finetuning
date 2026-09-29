# current

_Updated 2026-09-29 (Colab session 2, ~07:20–07:30 UTC). Purpose: the two
paste-ready prompts, the repeat cause, the dataset findings, and the test-batch
artifacts — now with the assets staged and the cheap semantic-screen driver built.
Durable record: `docs/music-cover-feasibility.md` §9._

## 0. VM state (checked, not assumed)

- Branch **`music-cover`** @ `fb071aa`, clean tree apart from this session's two new
  files (uncommitted, see §3).
- `/content` present, T4 **idle** (0 MiB / 0%). No training run active.
- `bash bootstrap/setup.sh --inference` **done**: all 8 jobs `ok`, total 35 s
  (`/content/logs/timing.txt`). Staged: main GGUF 7.26 GB, VAE, sidecars, both v2
  adapters in `/content/converter/out/`, binary in `/content/audiocpp_inference/bin/`.
- `vm-continuity status` → loop running (pid 9844), **healthy (exit 0)**.
  `backup_to_gcp.py` / `gpu_logger.py` are **down** (never started this VM).

## 1. What changed this session — read before re-planning

### 1.1 The ABC already exists (no transcription needed)

`gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/audiocpp_inference/out/abc_v2/`
— **12** `score.abc` files, written **2026-09-28 18:02–18:12 UTC** (Python SheetSage2,
route B2). Includes the guide track itself:

- GCS: `abc_v2/01-نسيب-وظعن-الحي-ونخيل-يامن-وعرائس-النعمة_4148240095/score.abc`
- Local (pulled this session):
  `/content/audiocpp_inference/out/abc_v2/01-نسيب-وظعن-الحي-ونخيل-يامن-وعرائس-النعمة_4148240095/score.abc`
  — 3701 B, `sha256 14ae1ae0f885c41b5ae312d746864daac247f2399c158e039cdb278b40540d32`,
  `K:D#m`, `Q:1/4=125`.

Do **not** confuse the prefixes: `out/sheetsage2_abc/` is the **failed** audio.cpp-route
smoke (`transcribe_manifest.json`: `n_ok: 0`, one track, `exit 1`, 3 s). `ss2_smoke/` and
`ss2_smoke2/` are earlier one-track smokes. The good output is `abc_v2/`.

### 1.2 The screen is possible — but `semantic_prefix` is not

Checked with `strings` against the **staged** binary (not just the docs):

| option | hits | meaning |
|---|---:|---|
| `stop_after` | 12 | `abc\|semantic\|audio`; `semantic` implies `export_semantic` |
| `export_semantic` | 4 | writes `semantic.json` under `--out-dir` |
| `text/vnd.abc`, `application/vnd.yue2.semantic+json` | — | the artifact MIMEs |
| `yue2.semantic.frames` / `.truncated` | — | artifact meta |
| `abc_file`, `cot`, `melody` | 6 / 18 / 6 | cover knobs present |
| `semantic_prefix` | **0** | **absent** — that one needs v0.8.2+ |

`stop_after=semantic` implies `export_semantic=true`, writes `score.abc` + `semantic.json`,
produces **no audio**, and needs `--out-dir` (`--out` writes nothing).

### 1.3 The guide render is NOT truncated — `generate.py` says otherwise

`out/batch_36_songs/01-نسيب…_4148240095` sidecar reports `"truncated": true`, but with
`"truncated_source": "duration_heuristic"`. The run's own log says:

```
[TIMING ts=20260928-112248] yue2.semantic.tokens 7743
[TIMING ts=20260928-112248] yue2.semantic.truncated 0      <- the model's own flag
[TIMING ts=20260928-112248] yue2.semantic_ms 231906.26479
```

WAV = 309.72 s = 7743/25 s; cap = 7750. It **ended on EOS, 7 frames under the cap** —
the sidecar's `true` is the WAV-near-cap heuristic firing, not truncation. Always read
the model flag, not generate.py's sidecar.

Useful consequence: the cap (7750) is only 7 frames above this sheet's natural plan
(7743), so **any injected section repeat overruns the cap and shows
`yue2.semantic.truncated 1`** — a cheap, objective repeat detector.

Cost: AR semantic = 232 s of the 423 s full render (~55%). So the screen costs ~45% of a
render and emits no 57 MB WAV; it is a pre-filter plus a truncation signal, not a
replacement for listening.

### 1.4 The control arm is exact

`styles/hijaz_sunoblk.txt` `sha256 300d1ae0…` == the guide's `style_sha256`;
`lyrics/01_nesib_as-is.txt` `sha256 29f46a89…` == the guide's `lyrics_sha256`. Same
seed 4148240095, same adapter (v2), same `cot=off` ⇒ `ctl_sunoblk_as-is` reproduces the
guide render.

### 1.5 Arm A is now one variable

`styles/hijaz_modified.txt` was a five-variable placeholder (added BPM + `vocals` +
`instrumentation` + `Mood`, and flipped Mood). Rewritten this session as the winning
text **with only `110 BPM` restored** — a clean single variable vs `win_as-is`.

## 2. The screen driver (new, uncommitted)

- `INFERENCE/screen_arms.sh <core|abc|all> [--dry-run]` — the same arm names as
  `batch.json` / `test_batch.sh`, but each run is `stop_after=semantic` + `--out-dir`
  (no `--out`). Refuses if a training run is active or `nvidia-smi` is missing.
  `ABC_FILE` defaults to the pulled guide ABC. Tested: `bash -n` clean, `core` dry-run
  plan correct.
- `INFERENCE/screen_summary.py <screen_dir> [--expect-wav guide.wav | --expect S]` —
  prints `frames / sec / trunc / ar_s` per arm. `trunc` is the **model** flag; `frames`
  falls back to the CLI log when `semantic.json` is absent. Tested against fakes.

**Limit (do not oversell it):** `semantic.json` is acoustic **codec** indices — there is
no lyric↔frame alignment, so it cannot say *which line* was sung. It ranks arms by planned
length + truncation. The verbatim verdict still needs the rendered audio (listening, or
ASR of the output vs the sheet).

## 3. Next commands (GPU work — check `nvidia-smi` first)

Assets are staged; nothing below needs `setup.sh` again.

```bash
cd /content/maqamrock-yue2-lora-finetuning

# 0) free pre-checks
nvidia-smi                       # confirm no other GPU work
bash INFERENCE/screen_arms.sh core --dry-run          # instant, no GPU

# 1) SEMANTIC SCREEN — the cheap pass (no audio, ~4 min/arm). DETACHED.
setsid nohup bash INFERENCE/screen_arms.sh all \
  > /content/logs/tv_screen.log 2>&1 & disown
#   watch:  tail -f /content/logs/tv_screen.log
#   stop:   pkill -f 'screen_arms.sh'
#   resume: re-run the same command (arms with artifacts are still re-run; it is cheap)
#   then:   python3 INFERENCE/screen_summary.py \
#             /content/audiocpp_inference/out/screen_semantic \
#             --expect-wav /content/audiocpp_inference/out/batch_36_songs/01-نسيب-وظعن-الحي-ونخيل-يامن-وعرائس-النعمة_4148240095.wav

# 2) RENDER the winners to audio (only after reading the screen)
setsid nohup python3 INFERENCE/generate.py manifests/test_verbatim_hijaz/batch.json \
  > /content/logs/tv_batch.log 2>&1 & disown
#   stop: pkill -f 'generate.py manifests/test_verbatim_hijaz'

# 3) B / C arms as full audio (test_batch.sh) — superseded by screen_arms.sh for screening
# ABC_FILE is already staged; test_batch.sh picks its own default, pass it explicitly:
ABC_FILE=/content/audiocpp_inference/out/abc_v2/01-نسيب-وظعن-الحي-ونخيل-يامن-وعرائس-النعمة_4148240095/score.abc \
  setsid nohup bash INFERENCE/test_batch.sh abc > /content/logs/tv_abc.log 2>&1 & disown

# backup after any run that produced audio
python3 backup_to_gcp.py --inference --once
```

## 4. Still open (unchanged from the earlier handoff)

- Which adapter for the batch — `v2` or `qfinal_a0.3`? (`batch.json` pins `v2`.)
- **Maqam clash:** the winning prompt was measured on **Ajam**; this track is **Hijaz**
  (the Hijaz copy is what the arms use).
- No-repeat arm (`win_dedup`) is the injection control; bare-tag arm (`win_bare`) tests
  the descriptor-tag mismatch.
- Two train/inference mismatches remain: the edited prompts dropped `110 BPM` (restored
  in arm A only), and training lyrics use **bare** tags while the as-is sheet carries
  `[Section | descriptors]`.
