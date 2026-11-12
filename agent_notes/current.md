# Current — `arabic_instrumental_lora` · 2026-11-12 · RUN COMPLETE, eval screen done, depth deferred

**Training finished 5500/5500 (3 h 36 min on A100-SXM4-80GB). All artifacts are in GCS and
verified. The 5-track checkpoint screen rendered; the 13-track depth round was deliberately
not started. Nothing is running now — the VM is safe to shut down.**

## Run — final facts

```
run        arabic_instrumental_lora · 5500/5500 · started 12:22:58 · ended ~16:08 UTC
adapter    /content/ai-toolkit/output/arabic_instrumental_lora/arabic_instrumental_lora.safetensors
sha256     cf6d44bbf4c03b28b2511e03c985e1d49894f6d4b2508a23a8f2bda3182e3584   (local == remote)
steps     129 isolated OOM skips (2.5 %) → trained on 461 effective tracks
loss       last-100 3.547 · last-250 3.538 · min 2.391 · plateaued ~4.0 from step 1000
checkpoints 21 numbered (250…5250) + final adapter + optimizer.pt, all in GCS
drift      gsutil rsync -n output → empty (no drift)
```

## GCS — everything (base = `gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/arabic_instrumental_lora/`)

```
output/     21 numbered checkpoints + arabic_instrumental_lora.safetensors + optimizer.pt
            + loss_log.db + config.yaml + tensorboard/
logs/       train.log, gpu_usage.csv, setup*.log, gcp_backup logs
agent_notes/current.md (+ this handover)
converted/  ck3000|ck4000|ck5000|ck5500 × {ar,nar}.safetensors  (558 MB, sha256 in eval/inputs/)
eval_holdout/  8 held-out tracks (mp3+txt) + HOLDOUT.json
eval/audio/    smoke_a100, screen_loRA, screen_base  (WAV + sidecars + manifests)
eval/mp3/      same batches as 192k mp3
eval/inputs/   input_{smoke,screen_*,depth_ck5500_*}.json, HOLDOUT.json,
               dataset_manifest.json, final_adapter_sha256.txt, converted_sha256.txt
```

Download everything for local listening:

```bash
gsutil -m rsync -r gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/arabic_instrumental_lora/eval ./ai_eval
```

## Eval — what exists, what is deferred

Screen (5 tracks, `P0a` = the representative prompt, seed 101, cap 6500):

```
ck3000 1:59 · ck4000 1:59 · ck5000 1:59 · ck5500 1:58   → 260 s audio, all hit the cap
base   0:35                                            → 114.7 s, ended naturally
```

The base take is **half the length** — the adapter is already changing structure, not only
timbre. Consequence: base-vs-LoRA cannot be perfectly blind (length gives it away).

Depth (deferred, 13 tracks ≈ 26 min on A100): `{P0b, H1, H2, H3, P1, P3} × {winner, base}`
plus one variance take (`P0a`, seed 202). Inputs are staged in `eval/inputs/`; only the
`ck5500` variant exists, so a different winner means regenerating the two JSONs (the pairs
are already converted and uploaded — nothing to reconvert).

Open decision: **which checkpoint** — `ck3000/4000/5000/5500`, or default to `ck5500`
(tie-break: latest).

## Docs state

```
pushed   7122d70 eval plan (18-track round, A100 budget, GCS download paths)
         + this session's final docs commit (run completion + 21-vs-22 fix)
pending  docs-reconciler pass; PROGRESS.md entry; SOURCE_OF_TRUTH row
known    plan F3's "15–16 GB" is the L4 number — v3 also ran ~79 GB on A100
         coverage gap: 13 tracks ≥ ~377 s dropped every epoch
         status.py:33 hardcodes v3 run name (mislabels this run)
         pgrep -f '<pattern>' self-matches a watcher's own cmdline (bit us twice)
```

## Restarting eval on a fresh (lower-grade) VM

1. `bash bootstrap/setup.sh --inference` (T4 sm75 staged automatically; L4 needs the
   `sm89` copy from `gs://akbar-december-2024-backup/arabmaqrock/binaries/`).
2. Pull the converted pairs: `gsutil -m rsync -r <base>/arabic_instrumental_lora/converted
   /content/converter/out` then point the JSON `loras` at each `ck*` dir.
3. Pull the audio + inputs: `gsutil -m rsync -r <base>/arabic_instrumental_lora/eval /content/eval`.
4. Depth = 13 tracks (~1.5 h on T4, ~26 min on A100); see
   `docs/ARABIC_INSTRUMENTAL_EVAL_PLAN.md` §4–§6.
