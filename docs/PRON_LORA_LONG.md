# Long-aya Quran pronunciation LoRA — runbook (canonical)

Single entry point for the **multi-day, multi-VM long-aya pronunciation LoRA**:
what the run is, where it stands, the commands that matter, and the exact prompts
to paste. The *design/why* lives in [`PRON_LORA_LONG_PLAN.md`](PRON_LORA_LONG_PLAN.md);
this doc is the *operating* surface.

> **Direction change (2026-09-27).** The full 81,006-pair set's latent-cache step
> measured **~1.1 files/s on the L4 ⇒ ~20 h** (the earlier "5–9 h" was an A100
> estimate; see plan §4.1), which does not fit a Colab session. The active run is
> now **`quran_long_aya_r8_s10`** — a frozen, seeded **10% sample of train combos**
> (8,100 pairs, ~3.0 GiB, cache ~2 h), at the scale of the working reference run
> (6,100 pairs). The full set and the `quran_long_aya_r8` identity stay reserved
> for a future high-end-hardware attempt. Selection locked in
> [`quran_long_aya_s10_manifest.json`](quran_long_aya_s10_manifest.json); built by
> `sample_pron_dataset.py` (seed 20260927).

**Canonical session prompt** (paste this at the start of any new session):
```text
quran_long_aya_r8_s10 — session prime.

If /content/maqamrock-yue2-lora-finetuning is missing, clone it and
`git checkout pron-lora-long` first.

Read, in this order:
  1. docs/PRON_LORA_LONG.md        (canonical runbook)
  2. agent_notes/current.md        (live next step)
  3. docs/PRON_LORA_LONG_PLAN.md   (design/why — only if you need to re-derive a decision)

Then verify the ACTUAL state from live sources — do not trust the docs' prose or
your memory:
  - git: branch, clean/dirty, ahead/behind, last commit
  - VM: nvidia-smi (GPU/VRAM), free disk, and what is running
    (pgrep -af 'run\.py'; pgrep -af backup_to_gcp.py; pgrep -af gpu_logger.py; vm-continuity status)
  - run: newest checkpoint in
    gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/quran_long_aya_r8_s10/output/
    and its step vs local; loss_log.db step/loss if present
  - dataset: /content/quran_long_aya_dataset_s10 present (8,100 train pairs)? cache built?
  - continuity: vm-continuity status + last ship time

Report briefly:
  - where we are: steps done, last checkpoint + when, cache built/banked or not
  - what is running right now, if anything
  - any divergence between the docs and reality (flag it)
  - the single next step, with the exact command(s) for me to type

Do not start, resume, stop, or edit anything without me typing the command. If the
state is ambiguous, ask before acting.
```

## Docs
| Doc | Answers |
|---|---|
| **this runbook** | run identity, current state, commands, session prompts |
| [`../agent_notes/current.md`](../agent_notes/current.md) | the live *next step* (updated every session close) |
| [`PRON_LORA_LONG_PLAN.md`](PRON_LORA_LONG_PLAN.md) | design + locked decisions (*why*) |
| [`quran_long_aya_s10_manifest.json`](quran_long_aya_s10_manifest.json) | frozen 10% subset (seed + 4,050 stems) |
| [`PAUSE_RESUME.md`](PAUSE_RESUME.md) · [`MONITOR.md`](MONITOR.md) · [`BACKUP_RESTORE.md`](BACKUP_RESTORE.md) | generic run mechanics |

## Snapshot (facts; update each session)
| | |
|---|---|
| Active run | `quran_long_aya_r8_s10` (10% subsample) |
| Config | `config/quran_long_aya_r8_s10.yml` — steps 8,100 · `save_every` 1500 · `max_step_saves_to_keep` 24 · `cache_text_embeddings: false` · `cache_latents_to_disk: true` |
| Branch | `pron-lora-long` |
| Dataset | `/content/quran_long_aya_dataset_s10/` — **8,100 train pairs / 352 val / 14 smoke**, 3.0 GiB. **Banked** as `…/quran_long_aya_dataset_s10.tar` (2.94 GiB, sha256 `1bf11f0b…fcc24`) + `…/quran_long_aya_s10_manifest.json`. Built by `sample_pron_dataset.py`, seed 20260927. |
| Run output | `/content/ai-toolkit/output/quran_long_aya_r8_s10/` → GCS `…/quran_long_aya_r8_s10/output/` |
| Log / metrics | `/content/logs/train_quran_long_s10.log` · `<output>/loss_log.db` · `/content/logs/gpu_usage.csv` |
| Latent cache | `/content/quran_long_aya_dataset_s10/train/_latent_cache` (~0.5 GiB; bank as `…/quran_long_aya_dataset_s10/_latent_cache.tar`). Dataset must still be present — the cache only skips the encode (plan §4.1). |
| Reserved | full set `quran_long_aya_dataset` (81,006 pairs = ~20 h cache on L4) + identity `quran_long_aya_r8`, for future high-end hardware |
| Status | Subset built + archived + locked. Full-set cache build stopped. **s10 not launched.** |

## Commands that matter
```bash
cd /content/maqamrock-yue2-lora-finetuning

# launch (you type it; detached — survives Ctrl+C)
python train_ctl.py start --config config/quran_long_aya_r8_s10.yml \
  --run-name quran_long_aya_r8_s10 --log-name train_quran_long_s10

# pause cleanly (checkpoint-safe SIGINT) -- NOTE: stop/status must be given the SAME
# --config as the launch, or their run-name check won't match (see COMMAND_HANDOVER_GOTCHAS.md)
python train_ctl.py stop --config config/quran_long_aya_r8_s10.yml --log-name train_quran_long_s10
# progress / health
python train_ctl.py status --config config/quran_long_aya_r8_s10.yml --log-name train_quran_long_s10
python monitor_loss.py /content/ai-toolkit/output/quran_long_aya_r8_s10/loss_log.db
# mirror now
python backup_to_gcp.py --run-name quran_long_aya_r8_s10 --once

# restore on a fresh VM:
#  - dataset: stream the archived tar (one object, ~40 s) — faster than the ~17k-file rsync
gcloud storage cp gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/quran_long_aya_dataset_s10.tar - \
  | tar -C /content -xf -
#    loose fallback (only if the tar is absent):
#    gsutil -m rsync -r gs://.../quran_long_aya_dataset_s10 /content/quran_long_aya_dataset_s10
#  - run output prefix (checkpoints + optimizer):
mkdir -p /content/ai-toolkit/output/quran_long_aya_r8_s10
gsutil -m rsync -r gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/quran_long_aya_r8_s10/output \
  /content/ai-toolkit/output/quran_long_aya_r8_s10
#  - then launch the identical start command; the log MUST print "Found step N"
#    (not step 0) -- that line is the resume working. The start step = newest checkpoint.

# bank the latent cache once built (one-time)
tar -C /content/quran_long_aya_dataset_s10/train -cf - _latent_cache \
  | gcloud storage cp - gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/quran_long_aya_dataset_s10/_latent_cache.tar
```

## Session continuity (across VMs)

| Store | Holds | Survives VM stop? |
|---|---|---|
| GitHub (`pron-lora-long`) | code, configs, plan, this doc, `quran_long_aya_s10_manifest.json`, `agent_notes/current.md` | yes |
| GCS | s10 dataset (+ tar), banked cache, checkpoints, `loss_log.db`, **OpenCode session store** | yes |
| VM `/content` + `/root` | the live run, the conversation, HF cache | **no** |

- **Restore the conversation** (if captured): `vm-continuity hosts` → `vm-continuity pull --host <H>` → `vm-continuity restore opencode -- --mode db`, then reopen the session. Only sessions captured *while the loop ran* come back; the loop is started early by `setup.sh` on every VM.
- **Cold start** (always works): the repo + GCS carry the state — paste the prime prompt above.
- **Opening:** restore the session, else paste a prompt below; ensure the notebook exported `HF_TOKEN`, `GCP_DATASET_PATH`, `GCP_QURAN_LONG_DATASET_PATH` (point it at the **`…_s10`** prefix), `GCP_BACKUP_BASE`.
- **Closing (before you disconnect)** — in order:
  1. stop cleanly: `python train_ctl.py stop --config config/quran_long_aya_r8_s10.yml --log-name train_quran_long_s10`
  2. mirror + verify: `python backup_to_gcp.py --run-name quran_long_aya_r8_s10 --once`, then confirm the newest `*.safetensors` **and** `optimizer.pt` are in GCS
  3. bank the latent cache if it was just built and not yet banked
  4. agent updates `agent_notes/current.md` and pushes
  5. **Continuity gate — do not disconnect until it reads OK.** Run `vm-continuity status`; the loop must print `loop=running … state=OK` with `last_ship_ok` under ~10 min. If it's down or stale, run `vm-continuity ship` and re-check. Stamp the result in the closing message: **continuity: OK (last ship HH:MMZ)** — or `NOT RUNNING` (then fix before disconnecting).
- **Loss window:** checkpoints every 1500 steps, mirror every 5 min → lose at most the steps since the last 1500-multiple, plus ≤5 min.
- **Never** run the same run name on two VMs; **never** edit the config mid-run; **no** auto-resume of a planned pause.

## Prompts to paste

### First GPU session only (kickstart; obsolete once a checkpoint exists)
```text
Fresh Colab GPU VM — start the GPU phase for the quran_long_aya_r8_s10 run (branch
pron-lora-long). Read docs/PRON_LORA_LONG.md + agent_notes/current.md first.

1. Preflight: confirm branch pron-lora-long + config parses; report nvidia-smi (GPU/VRAM),
   disk, and vm-continuity health.
2. bootstrap/setup.sh --training. Point GCP_QURAN_LONG_DATASET_PATH at the _s10 prefix so
   its opt-in job restores OUR subset — confirm the "[ok] quran-long dataset: 8100 train
   pairs" line, else extract /content/quran_long_aya_dataset_s10.tar. (It may also pull the
   old v2 dataset — ignore that.)
3. Start sidecars: backup_to_gcp.py --run-name quran_long_aya_r8_s10 ; gpu_logger.py.
4. The first launch builds the latent cache (~2 h for 8,100 files) before step 1. Give me
   the exact detached launch command to type (python train_ctl.py start --config
   config/quran_long_aya_r8_s10.yml --run-name quran_long_aya_r8_s10 --log-name train_quran_long_s10).
5. After I launch: watch /content/quran_long_aya_dataset_s10/train/_latent_cache/*.safetensors
   until ~8,100; the MOMENT it completes, bank it and report the tar size.
6. Once steps run, measure ~50 steps (s/step, VRAM peak, wall clock per 1500-step save).
   Do not change the config.
7. Do not edit the config or auto-resume anything; I pause with train_ctl.py stop.
8. Continuity check before I disconnect: update agent_notes/current.md, commit+push, confirm
   this session shipped (vm-continuity status; ship if needed).
```

### Resume after a pause
```text
Resume the multi-day YuE2 run quran_long_aya_r8_s10 (branch pron-lora-long); fresh VM.
Read docs/PRON_LORA_LONG.md + agent_notes/current.md first.
Before anything else, report live state: nvidia-smi, disk, vm-continuity status, and the
newest quran_long_aya_r8_s10 checkpoint in GCS with its step (if none exists yet, say so).
Then give me the exact commands to restore the dataset (stream /content/quran_long_aya_dataset_s10.tar)
+ banked latent cache + run output prefix (only what exists) and start the sidecars, followed
by the identical launch command to type. Do not auto-resume; do not edit the config.
```

### Status check while running
```text
Check quran_long_aya_r8_s10 (branch pron-lora-long). Read docs/PRON_LORA_LONG.md +
agent_notes/current.md first. Answer from live artifacts only: latest step + loss
(monitor_loss.py on the run's loss_log.db), GPU util/mem (gpu_usage.csv), newest checkpoint
local vs GCS and the drift, and whether backup_to_gcp.py + gpu_logger.py are running.
Make no changes.
```

### Checkpoint-eval on a second (T4) VM — while training runs
Use this to try checkpoints as they land, without waiting for the run to finish.
A T4 is the right box (the staged `audiocpp_cli` is sm_75/T4). Training continues
untouched on the other VM; **never** run the same training run on two VMs. A
paste-ready copy also lives at `/content/checkpoint_eval_prompt.md`.
```text
Second-VM checkpoint-eval session for the long-aya Quran pronunciation LoRA
(branch pron-lora-long, run quran_long_aya_r8_s10).

SITUATION: training is STILL RUNNING on another Colab (L4). Do NOT train here, and
do NOT start/stop/resume that run — never run the same run name on two VMs. This VM
only watches checkpoints appear and tries them: pull -> merge -> convert -> generate.

READ FIRST (in this order):
  1. docs/PRON_LORA_LONG.md   2. docs/PRON_LORA_MERGE.md
  3. docs/PRON_LORA_SWEEP.md  4. agent_notes/current.md

SETUP:
  - git clone https://github.com/akbargherbal/maqamrock-yue2-lora-finetuning.git
      && cd maqamrock-yue2-lora-finetuning && git checkout pron-lora-long
  - export HF_TOKEN and GCP_BACKUP_BASE (from the training VM's notebook).
  - bootstrap/setup.sh --inference     # audiocpp_cli (sm_75) + GGUF model + style LoRA + converter

PROCEDURE (per new checkpoint):
  1. gcloud storage ls -l gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/quran_long_aya_r8_s10/output/quran_long_aya_r8_s10_*.safetensors
     (checkpoints every 1,500 steps; empty list = none yet, just say so)
  2. Pull the newest checkpoint locally; note its step.
  3. `python merge_pron_lora.py` — merge with the style adapter at the chosen alpha
     (CPU-only; exact flags/scaling in docs/PRON_LORA_MERGE.md — do not guess).
  4. `converter/convert_aitoolkit_yue2_lora.py` (staged at /content/converter/out).
  5. Generate held-out prompts: `INFERENCE/run_one.sh <Maqam> <seed>` (or pron_ckpt_sweep.py).
  6. Report from live artifacts: step + filename, alpha, output paths, errors. Compare
     across steps — do not judge quality from one checkpoint.

CONSTRAINTS: do not edit training configs/dataset; do not touch the training run; long
jobs detached with a log; --help outranks the prose.
```

## Progress log (append one row per session)
| Date | Session | Steps (from→to) | Approx wall | How it ended | Notes |
|---|---|---|---|---|---|
| 2026-09-27 | planning/recovery | 0 → 0 | — | n/a | recovered builder+config+plan after VM loss; full dataset uploaded; decisions locked |
| 2026-09-27 | pivot to 10% subsample | 0 → 0 | — | n/a | full-set L4 cache measured ~1.1 files/s (~20 h) → not session-feasible; built locked 10% combo sample (8,100 pairs), archived; new run `quran_long_aya_r8_s10`; full set reserved |
| 2026-09-27 | s10 GPU run | 0 → 8100 | 2:46 | completed (self-stop at target) | first full epoch on the 10% set; cache built+banked (541.69 MiB); 6 ckpts (1500–7500 + final) + optimizer in GCS; loss/loss 50-mean 6.57→5.26, ar_ce 5.50→3.97, ar_kl rose 0.17→1.38 (analysis in `TRAINING_ANALYSIS/quran_long_aya_r8_s10/`) |

The progress log is the durable "how much training have we done" record;
`agent_notes/current.md` holds only the live next step.
