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

## Round 2 — fine sweep at checkpoint 3050 (2026-09-24)

After Task 17, the checkpoint was fixed at **3050** and `alpha` refined to
**{0.2, 0.3, 0.55, 0.65}**, for **Hijaz + Kurd only** (8 tracks; 4 labels per maqam).
Task 17's `a0` and `c3050_a0.5` tracks are reused as references, not regenerated, so
`alpha` is the only variable. Same held-out prompts, same generation seed `20260924`,
auto cap, same sm89 binary; new **blinding seed `20260925`** (labels only).

Driver: [`INFERENCE/pron_fine_sweep.sh`](../INFERENCE/pron_fine_sweep.sh) (same
resumable/skip contract as `pron_alpha_sweep.sh`, maqam-major). Records:
[`results/pron_fine_sweep/`](../results/pron_fine_sweep/) (config table, per-track table,
`KEY.json`). Blinded review package: `PRON_FINE_SWEEP_INPUT/` at the repo root. Raw WAVs +
adapters: `/content/pron_fine_sweep/` + `/content/converter/out/<cfg>/`.

## Round 3 — checkpoint sweep at fixed alpha 0.5 (2026-09-25)

With `alpha` fixed at the already-shipped **0.5**, this round compares the two
not-yet-shipped pron checkpoints **{1525, 4575}** (2 configs x Hijaz + Kurd = **4
tracks**). Same held-out prompts, same generation seed `20260924`, auto cap (Hijaz
7250 / Kurd 6500), binary `7ad69d1c…` (sm_75, PTX-JIT on the L4); new **blinding seed `20260926`** (labels only,
one new random label per maqam). Strictly sequential.

Driver: [`INFERENCE/pron_ckpt_sweep.py`](../INFERENCE/pron_ckpt_sweep.py) (reuses
`generate.py`'s sidecar helpers; writes a full per-track JSON sidecar before and after
generation). Records: [`results/pron_ckpt_sweep/`](../results/pron_ckpt_sweep/)
(config table, per-track table, `KEY.json`, per-track `sidecars/`). Blinded review
package: `PRON_CKPT_SWEEP_INPUT/` at the repo root. Raw WAVs + adapters:
`/content/pron_ckpt_sweep/{<cfg>,merged,converted}/`.

## Round 4 — cross-maqam lyric swap (2026-09-25)

Not an alpha/checkpoint sweep: this round crosses the held-out inputs. Each group pairs
one maqam's **caption + maqam tag** with the **other maqam's held-out lyric**, at two pron
settings — `a0` (v2 verbatim) and `c3050_a0.5` (the shipped α 0.5 merge). 2 groups x 2
configs = **4 tracks**, strictly sequential per group. The question is whether the
style/tag or the lyric text dominates the render.

| group | caption/tag | lyric | cap |
|---|---|---:|---:|
| `KurdStyle_HijazLyrics` | `Kurd_style.txt` | `Hijaz_lyrics.txt` | 7250 |
| `HijazStyle_KurdLyrics` | `Hijaz_style.txt` | `Kurd_lyrics.txt` | 6500 |

Same generation seed `20260924` as the sweeps; **auto cap follows the swapped-in lyric**
(Hijaz lyric -> 7250, Kurd lyric -> 6500). Native sm89 L4 binary (`97028a71…`); new
**blinding seed `20260927`** (labels only, one new random A/B per group — the config is
the blinded axis, the swap group is visible).

Driver: [`INFERENCE/maqam_lyric_swap.py`](../INFERENCE/maqam_lyric_swap.py) (reuses
`generate.py`'s sidecar helpers; full per-track JSON sidecar written before and updated
after). Records: [`results/maqam_lyric_swap/`](../results/maqam_lyric_swap/)
(`sweep_manifest.json`, `KEY.json`, `README.md`, per-track `sidecars/`). Blinded review
package: `MAQAM_LYRIC_SWAP_INPUT/` at the repo root. Raw WAVs + adapters:
`/content/maqam_lyric_swap/`.

