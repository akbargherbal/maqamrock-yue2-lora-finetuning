# Pronunciation LoRA — alpha sweep & listening review (Task 17)

How to render the **alpha sweep**: the frozen v2 style LoRA merged with the AR-only
pronunciation LoRA at several `alpha` values, so the user can pick the checkpoint +
`alpha` **by ear**. This task produces audio + a blinded review package only — it does
**not** judge quality, pick a winner, or score substitutions.

- Merge tool + scaling convention: [`PRON_LORA_MERGE.md`](PRON_LORA_MERGE.md).
- Source verification of the pron adapter: [`PRON_LORA_VERIFICATION.md`](PRON_LORA_VERIFICATION.md).
- Training runbook: [`PRON_LORA.md`](PRON_LORA.md).

## The five configs (one per render target)

`alpha` is the pronunciation-adapter strength folded into the merged AR LoRA
(`W = W_base + 1.0·dW_style + alpha·dW_pron`). Folder name is `<pron-checkpoint>_a<alpha>`;
`a0` is the alpha=0 baseline, which reproduces v2 verbatim.

| folder | pron checkpoint | pron step | alpha |
|---|---|---:|---:|
| `a0` | final | 6100 | 0.0 |
| `c3050_a0.5` | 3050 | 3050 | 0.5 |
| `c3050_a1.0` | 3050 | 3050 | 1.0 |
| `cfinal_a0.5` | final | 6100 | 0.5 |
| `cfinal_a1.0` | final | 6100 | 1.0 |

Each config is rendered for all four held-out maqams (**Hijaz, Kurd, Nahawand, Ajam**),
one shared seed, **auto cap** (same lyrics → same cap). 5 × 4 = **20 songs**, generated
**strictly sequentially** (two concurrent runs can OOM the NAR graph). Maqam-major order,
so an early stop still leaves every finished maqam a complete 5-way comparison.

## Prerequisites

- The inference workspace + converted v2 (fresh VM): `bash bootstrap/setup.sh --inference`.
- The pron `final` + `3050` checkpoints staged under
  `/content/ai-toolkit/output/pron_lora_ar_only_r8/` (pull the run's GCS `output/` prefix).
- Input hashes must match `PRON_LORA_MERGE.md`'s "Inputs" table — mismatch is a STOP.
- On an L4, stage the **sm89-l4** binary at `/content/audiocpp_inference/bin/audiocpp_cli`
  (the flat GCS object is sm_75/T4); see [`audiocpp_gpu_arch_builds.md`](audiocpp_gpu_arch_builds.md)
  and [`INFERENCE.md`](INFERENCE.md).

## Build the five adapters (CPU)

```bash
for spec in "a0 0 final" "c3050_a0.5 0.5 3050" "c3050_a1.0 1.0 3050" \
            "cfinal_a0.5 0.5 final" "cfinal_a1.0 1.0 final"; do
  set -- $spec; cfg=$1; a=$2; ck=$3
  python merge_pron_lora.py --alpha "$a" --pron-checkpoint "$ck" \
    --out /content/pron_sweep/merged/$cfg/akbar_arabic_rock_lora.safetensors
  python /content/converter/out/convert_aitoolkit_yue2_lora.py \
    /content/pron_sweep/merged/$cfg/akbar_arabic_rock_lora.safetensors \
    --out-dir /content/converter/out/$cfg
done
```

Keep v2's basename so `a0` reproduces the live converted hashes. Checks before any
generation:

- `a0` converted **AR** == `747d5cfe…`, **NAR** == `ad2c8d86…` (v2 verbatim).
- The five converted **AR** sha256 values are all distinct (guards a config silently
  reusing another's file).
- The four non-zero configs' merge output reports **AR rank 40**.

Then write `/content/pron_sweep/sweep_manifest.json`: per config `{alpha, pron_checkpoint,
merged sha256, converted AR/NAR sha256, paths}`, plus seed, cap mode, binary sha256, GPU
info, and the sha256 of the eight staged prompt files.

## L4 smoke (before committing ~2 h)

Render `Hijaz 20260924 750` once with `a0` and once with a rank-40 config
(`c3050_a1.0`), setting `OUT_DIR` and `LORA_AR`/`LORA_NAR`. Pass = exit 0, WAV exists,
duration > 5 s, `ffmpeg volumedetect` mean clearly above −60 dB, and the rank-40 adapter
loads. Record wall times.

## Run the sweep

```bash
cd /content/maqamrock-yue2-lora-finetuning
setsid nohup bash INFERENCE/pron_alpha_sweep.sh > /content/pron_sweep/sweep.log 2>&1 &
disown
```

Detached (survives Ctrl+C / closing the tab). `INFERENCE/pron_alpha_sweep.sh` sets
`OUT_DIR`/`LORA_AR`/`LORA_NAR` per track and calls `INFERENCE/run_one.sh <Maqam> <seed>
auto` (the `LORA_AR`/`LORA_NAR` overrides are the Task 17 addition to `run_one.sh`).
Resumable: a track whose WAV exists and whose `_time.txt` says `Exit status: 0` is
skipped, so **re-running the same command resumes**. Failures are appended to
`/content/pron_sweep/_failed.log` and do not stop the run. Stop with
`pkill -f pron_alpha_sweep.sh`.

## Review package

After all 20 exist (see [`INFERENCE.md`](INFERENCE.md) for the sidecar layout):

1. Per-track table from `_time.txt` / `.log` (config, maqam, exit, duration, wall,
   `truncated`).
2. Blinded mp3 review copies (ffmpeg 192k, **no** trim/normalize/fade): per maqam shuffle
   the five configs with `random.Random(20260924)` → `<Maqam>_<A..E>.mp3`; zip with
   `KEY_open_after_listening.txt` (label → config). Same KEY at
   `results/pron_sweep/KEY.json`. WAVs stay the untouched originals.
3. Upload WAVs + logs + manifests to `<base>/pron_alpha_sweep/` (the training-side backup
   daemon does not cover `/content/pron_sweep`).

## Results

Committed under `results/pron_sweep/`: `sweep_manifest.json`, `README.md` (config table
with shas + the per-track table + smoke wall times), `KEY.json`. Numbers live there, not
in this runbook.

The eventual checkpoint/`alpha` choice (and the letter-substitution scorecard) is the
user's, informed by listening to the blinded package — not decided by this task.
