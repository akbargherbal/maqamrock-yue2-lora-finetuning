# Inference: `audiocpp_cli` + YuE2 GGUF + the step-3000 LoRA

Task runbook for generating tracks from the fine-tuned LoRA on a fresh Colab VM.
For building the `audiocpp_cli` binary, see
[`audiocpp_gpu_arch_builds.md`](audiocpp_gpu_arch_builds.md); for *why* the
pieces are the way they are, `../DECISIONS.md`.

## TL;DR

```bash
git clone https://github.com/akbargherbal/maqamrock-yue2-lora-finetuning.git
cd maqamrock-yue2-lora-finetuning
bash bootstrap/setup.sh --inference > /content/logs/setup.log 2>&1   # wait for "done"
INFERENCE/run_one.sh Hijaz 1                                          # cap defaults to auto
```

## Where each piece comes from (provenance — read this first)

**The GGUF model is NOT in GCS.** It comes from Hugging Face. Everything else
(audio.cpp source aside) is staged from the GCS `audiocpp_inference/` prefix.

| Piece | Source | Local path | In GCS? |
|---|---|---|---|
| YuE2 GGUF main (`yue2-3b-bf16.gguf`), VAE (`yue2-vae-f16.gguf`), `sidecars/*` | **Hugging Face** `audio-cpp/Yue2-3B-GGUF` (`hf download`) | `/content/audiocpp_inference/models/Yue2-3B-GGUF/` | **No** — deliberately excluded, regenerable (`backup_to_gcp.py` comment: "models/ multi-GB GGUFs; setup.sh re-downloads them from HF") |
| `audio.cpp` **source** | GitHub `0xShug0/audio.cpp` (clone only, never built by bootstrap) | `/content/audio.cpp` | No |
| Prebuilt `audiocpp_cli` (sm_75 / T4) | GCS `audiocpp_inference/build/audiocpp_cli` | `/content/audiocpp_inference/bin/audiocpp_cli` | **Yes** |
| Converted step-3000 LoRA, unfused (`akbar_arabic_rock_lora_{ar,nar}.safetensors`) | GCS `audiocpp_inference/converter/` | `/content/converter/out/` | **Yes** |
| Prompts (one `*_style.txt` + `*_lyrics.txt` per maqam) | GCS `audiocpp_inference/prompts/` | `/content/audiocpp_inference/prompts/` | **Yes** |
| Runner + cap script (`run_one.sh`, `duration_cap.py`) | **Repo `INFERENCE/`** (canonical; the GCS `audiocpp_inference/scripts/` copy is a legacy mirror) | `/content/maqamrock-yue2-lora-finetuning/INFERENCE/` | `scripts/` still mirrored, but the repo copy is what runs |

Consequence: to "use the GGUF from GCP" you can't — there isn't one there. Either
let `setup.sh` re-fetch it from HF, or copy your local
`/content/audiocpp_inference/models/` to GCS yourself (not done by the backup
script, by design).

## Fresh VM: setup

```bash
bash bootstrap/setup.sh --inference > /content/logs/setup.log 2>&1
```

Runs these jobs in parallel (per `/content/logs/<name>.log`):
`opencode`, `ccache` (installs `ccache` **and GNU `time`**), `audio_cpp` (clone),
`hf_yue2_gguf`, `hf_yue2_sidecars`, `lora_adapters`, `audiocpp_binary`.

- `audiocpp_binary` does one `gsutil cp` of the binary (flat path) plus
  `gsutil -m rsync -r` of `prompts/` and `scripts/`; a marker skips it on re-run.
- Requires `HF_TOKEN` and `GCP_BACKUP_BASE` in the environment
  (`/root/.secrets.env`, staged by the launching notebook).
- **No CUDA toolkit is needed** for this path — the binary is prebuilt. A toolkit
  is only needed if you build from source (see below).

Verify by reading the files, not the exit code:

```bash
grep -n "\[FAIL\]" /content/logs/setup.log || echo "no failures"
cat /content/logs/timing.txt
```

The verify block checks the model dir + all four sidecars + both LoRA files, and
(added with `job_audiocpp_binary`) that the binary is executable and
`prompts/`/`scripts/` are non-empty.

## Run a generation

```bash
cd /content/maqamrock-yue2-lora-finetuning
INFERENCE/run_one.sh <Maqam> <seed> [cap|auto]
```

- `<Maqam>` ∈ {`Ajam`, `Hijaz`, `Kurd`, `Nahawand`} (the staged `prompts/*_style.txt`).
- `<seed>` — use a value below 2^32 (see `../DECISIONS.md`'s seeds entry).
- `cap` defaults to `auto`: derived from the lyrics by the canonical
  [`INFERENCE/duration_cap.py`](../INFERENCE/duration_cap.py), per
  [`text_to_duration_formula.md`](text_to_duration_formula.md). This is an
  **upper cap** (95th-percentile quantile regression, not a mean):
  `dur_cap = 111.1 + 0.3126·N_letters`, rounded to 10 s — covers 94.8% of the
  267 corpus tracks. The old `92 + 0.28·N` line was the *centre* (only 54.7%
  coverage) and under-provisioned the cap. For a more forgiving cap use the
  doc's 97.5th percentile, `122.9 + 0.3081·N` (97.8% coverage). Pass an integer
  to override (`semantic_max_tokens`).
- Fixed session options inside `run_one.sh`: `--family yue2`,
  `yue2.model_gguf=yue2-3b-bf16.gguf`, `yue2.vae_gguf=yue2-vae-f16.gguf`,
  `yue2.ar_lora`/`yue2.nar_lora` (both scale 1.0, from `/content/converter/out`),
  `yue2.attention=flash`, `cot=off`.
- `run_one.sh` wraps the call in `/usr/bin/time -v` — **GNU `time` must be
  installed** (the bootstrap does). Colab's builtin `time` alone gives
  `exit 127: /usr/bin/time: No such file or directory`.

Outputs, one set per run, under `$OUT` — `/content/audiocpp_inference/out/` by
default, or the folder named by the `OUT_DIR` env var when a batch driver sets
one (e.g. `out/20260922-1337_random16/`), so each run's tracks stay
self-contained:

| File | What |
|---|---|
| `<Maqam>_<seed>.wav` | the generated audio |
| `<Maqam>_<seed>.log` | CLI `--log` (TRACE/TIMING, errors) |
| `<Maqam>_<seed>_time.txt` | `/usr/bin/time -v` (wall, max RSS, CPU%) |
| `<Maqam>_<seed>_gpu.csv` | 1 Hz GPU util/mem/power/temp during the run |
| `_runs_status.log` | one START/END line per run (always written) |

## Two ways to have the binary

1. **Prebuilt (default, what `setup.sh` stages).** The flat GCS object
   `audiocpp_inference/build/audiocpp_cli` is the **sm_75 / T4** build.
2. **Build from source** for a different GPU (e.g. L4) — see
   [`audiocpp_gpu_arch_builds.md`](audiocpp_gpu_arch_builds.md). Place the result
   at `/content/audiocpp_inference/bin/audiocpp_cli` (where `run_one.sh` looks:
   `BIN="$ROOT/bin/audiocpp_cli"`).

Per-arch GCS copies exist (e.g. `audiocpp_inference/build/sm89-l4/audiocpp_cli`),
but `job_audiocpp_binary` still pulls only the flat sm_75 path; picking the arch
subdir from the live GPU's compute capability is not designed yet.

## Backup

```bash
python backup_to_gcp.py --inference            # daemon
python backup_to_gcp.py --inference --once     # single pass
```

Mirrors `/content/audiocpp_inference/{out,prompts,scripts}` + `/content/converter/out`
+ `/content/logs` + `agent_notes/` to `gs://<base>/audiocpp_inference/`. The GGUF
(`models/`) and the binary (`bin/`) are **not** mirrored — both are regenerable
via `setup.sh`.

## Worked example

T4, 2026-09-22: `setup.sh --inference` (all `[ok]`) then `INFERENCE/run_one.sh
<Maqam> 1` for all four maqams — exit 0, real 48 kHz stereo WAVs 216–240 s, under
`/content/audiocpp_inference/out/`. Full numbers in `../PROGRESS.md`.

## Benchmark — wall time per track on a T4 (2026-09-22)

Measured on the full **16-track** random-seed batch (`out/batch_20260922_seeds.tsv`,
4 maqams × 4 random seeds, all `exit=0`). Wall time is `/usr/bin/time -v`'s
`Elapsed (wall clock)` for the whole `audiocpp_cli` process — i.e. **model load +
generation**, as reported in each `out/<Maqam>_<seed>_time.txt`.

**Setup:** Tesla T4 (compute 7.5), bf16 GGUFs (`yue2-3b-bf16.gguf` +
`yue2-vae-f16.gguf`), converted step-3000 LoRA (AR + NAR, scale 1.0),
`yue2.attention=flash`, `cot=off`, `semantic_max_tokens` from
`duration_cap.py` (auto).

| Metric | Value |
|---|---|
| Tracks measured | 16 |
| **Mean** | **389.6 s (6.49 min)** |
| Median | 380.2 s (6.34 min) |
| Min / Max | 336.4 / 446.9 s |
| Total (16 tracks) | 103.9 min |

Per-maqam means (each n=4) — tracks with longer lyrics get the larger auto cap,
which dominates the difference:

| Maqam | Auto cap | Mean wall |
|---|---|---|
| Hijaz | 6500 | 424.4 s |
| Ajam | 5750 | 378.0 s |
| Nahawand | 6000 | 388.8 s |
| Kurd | 5500 | 367.3 s |

> **Cap caveat.** The "Auto cap" values above are what the staged `duration_cap.py`
> actually produced on 2026-09-22 — which used the **old centre-fit** formula
> `92.0 + 0.280·N`. This runner and `text_to_duration_formula.md` specify the
> 95th-percentile `111.1 + 0.3126·N`, so these caps were ~750–1000 tokens low and
> **5 of 16** tracks self-terminated at the cap (`truncated 1`):
> `Ajam_140828086`, `Kurd_1389690935`, `Kurd_3975969445`, `Kurd_514634212`,
> `Nahawand_441956428`.
>
> **Fixed:** `run_one.sh` now computes the cap with the canonical repo
> `INFERENCE/duration_cap.py` (95th percentile), so new runs are correctly
> capped. Re-running the 5 truncated seeds at the corrected cap is a separate
> open item.

Rule of thumb for planning a batch: **~6.5 min/track, ~9 tracks/hour on a T4**,
scaling with the cap (larger lyrics → longer track → longer wall time).

## Known stale bits / open items

- `bootstrap/setup.sh`'s **closing banner is stale**: it still says "audio.cpp
  was CLONED but NOT built, on purpose" and tells you to run `build_linux.sh`,
  which predates `job_audiocpp_binary` staging the prebuilt binary. The binary is
  in fact staged; the banner was not updated. (Flagged, not silently changed.)
- Auto-selecting the per-arch GCS binary from the live GPU's compute capability
  is not implemented; the flat path (sm_75) is what gets pulled.
- The `sm89-l4` binary is verified to *compile*; it has not been run on an L4.
