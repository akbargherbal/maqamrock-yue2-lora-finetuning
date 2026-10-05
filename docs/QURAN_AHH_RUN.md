# `quran_ahh_r8` — run hub, config audit & GPU checklist

Canonical operating surface for the AHH Quran pronunciation LoRA (`quran_ahh_r8`).
Design/why: [`QURAN_PRON_REVIEW.md`](QURAN_PRON_REVIEW.md). Build provenance:
`agent_notes/current.md` + `prepare_ahh_quran_dataset.py`. Live next step:
[`../agent_notes/current.md`](../agent_notes/current.md).

Branch: **`pron-lora-long-aya`** (do NOT merge to `main`).

> **REVISED CONFIG (2026-10-05, user), not yet retrained.** The first `quran_ahh_r8`
> training COMPLETE on 2026-10-05 07:39 UTC (9,489 steps, 1 epoch, rank-8 **AR-only**)
> and the listening verdict was that it moved recitation *prosody* (madd/waqf) but not
> the makhraj. The config has since been **replaced in place**: **AR + NAR jointly,
> rank 32/32, `ar_kl_weight: 0`, 28,467 steps (3 epochs)**. The old run is the record in
> `TRAINING_ANALYSIS/quran_ahh_r8/ANALYSIS.md`; the new L4 session starts from the revised
> config. Gate §2 is resolved; the config is the authority, not this table's stale rows.

## Canonical session prompt (paste on the GPU VM)

```text
quran_ahh_r8 — GPU session prime.

Read, in this order:
  1. docs/QURAN_AHH_RUN.md     (canonical hub: config audit + GPU checklist)
  2. agent_notes/current.md    (live next step)

Then verify the ACTUAL state from live sources — do not trust prose or memory:
  - git: branch pron-lora-long-aya, clean/dirty, HEAD vs origin
  - VM: nvidia-smi (GPU/VRAM), disk, and what is running
    (pgrep -af 'run\.py'; pgrep -af backup_to_gcp.py; pgrep -af gpu_logger.py; vm-continuity status)
  - dataset: /content/quran_ahh_dataset (9,489 train pairs) present? did setup.sh print
    "[ok] AHH dataset: 9489 train pairs"? latent cache built/banked?
  - run: newest checkpoint in GCS .../quran_ahh_r8/output/ and its step (none = fresh)
  - continuity: vm-continuity status

Report briefly: where we are; what is running right now; any doc-vs-reality divergence;
the single next step with the exact command(s) for me to type.

Do NOT launch training: the Phase 1 base-model ceiling probe (§2) gates it. Do not
start, resume, stop, or edit anything without me typing the command.
```

## Snapshot

| | |
|---|---|
| Run | `quran_ahh_r8` (1 epoch) |
| Config | `config/quran_ahh_r8.yml` — **REVISED: AR+NAR rank 32/32, `ar_kl_weight 0.0`, `steps 28467` (3 epochs)** |
| Dataset | `/content/quran_ahh_dataset/` — **9,489 train / 6 val** (2:255 ×3 reciters ×2 scripts); ~3.8 GiB |
| Banked | `$GCP_BACKUP_BASE/quran_ahh_dataset.zip` (3.69 GiB, sha256 `8c68d684…e9ff9`) |
| Notebook env | `GCP_AHH_DATASET_ZIP` → the zip above; opt-in `job_ahh_dataset` in `setup.sh` restores it |
| Run output | `/content/ai-toolkit/output/quran_ahh_r8/` → `<base>/quran_ahh_r8/output/` |
| Logs / metrics | `/content/logs/train_quran_ahh.log` · `<output>/loss_log.db` · `/content/logs/gpu_usage.csv` |
| Latent cache | `/content/quran_ahh_dataset/train/_latent_cache` (**bank** as `$GCP_BACKUP_BASE/quran_ahh_dataset/_latent_cache.tar`) |
| Launch / stop | `train_ctl.py start|stop|status --config config/quran_ahh_r8.yml --run-name quran_ahh_r8 --log-name train_quran_ahh` |

## 1. Config audit — `config/quran_ahh_r8.yml`

**Provenance: byte-identical to `config/quran_long_aya_r8_s10.yml` except 4 keys**
(verified `diff`): `config.name`, `process[].log_dir`,
`datasets[0].folder_path`, `train.steps`. The s10 config completed 0→8,100 cleanly,
so every remaining structural key is *proven in a real run* — the audit below is
"what it does / is it inert", not "will it parse".

Correct-by-construction (unchanged from the working s10 run):

| Key | Value | Verdict |
|---|---|---|
| `job` / `process[].type` | `extension` / `diffusion_trainer` | correct superset (`DECISIONS.md` plumbing) |
| `network.linear/_alpha` | 32 / 32, `conv` 16/16, `lokr_full_rank: true` | rank 32 (was 8) — capacity to remap phonemes; `conv` inert |
| `network_kwargs.ignore_if_contains` | `[]` | **AR + NAR** (was `["transformer.nar"]` = AR-only) — the NAR renders the articulation, so it must be adapted too |
| `model.name_or_path` / `qtype` | `…yue2_3b_int8_convrot.safetensors` / `convrot8` | HF-cached by bootstrap; int8 QLoRA |
| `model_kwargs.cot` / `ar_kl_weight` / `train_window_frames` | `off` / `0.0` / `0` | `ar_kl 0` (was 0.2): don't anchor the AR to the base that's wrong; whole-clip, no SheetSage2 |
| `train.batch_size` / `gradient_accumulation` | 1 / 1 | 1 step = 1 sample ⇒ `steps: 28467` = **3 epochs** |
| `train.optimizer` / `lr` / `dtype` | `adamw8bit` / 1e-4 / bf16 | unchanged |
| `ema_config` | `use_ema: true`, decay `0.999` | **saved adapters are EMA weights** |
| `datasets[0].cache_latents_to_disk` | `true` | **mandatory for YuE2**; ~2.4 h for 9,489 on an L4 before step 1 |
| `cache_text_embeddings` | `false` | correct: AR embed is a table lookup; `true` would bloat ~9× |
| `save.save_every` / `max_step_saves_to_keep` | 1500 / 24 | saves 1500…9000 + a final no-step save; 24 keeps all |
| `save.dtype` / `save_format` | bf16 / `diffusers` | matches converter expectations |

Keys that are **inert here** (not bugs — do not expect output from them):

| Key | Why inert |
|---|---|
| **entire `sample:` block** (`sample_every: 250`, `duration: 360`, …) | `train.disable_sampling: true` — no in-training samples at all |
| `train.skip_first_sample` / `force_first_sample` | moot under `disable_sampling`; **no step-0 sample** (unlike `START.md`'s v2 note) |
| `train.content_or_style`, `network.conv/_alpha` | no effect on an AR-only adapter (review §2.4) |
| `process[].log_config.log_every` | **dead key** (`LoggingConfig`), kept deliberately (`DECISIONS.md`) |
| `process[].sqlite_db_path` (`aitk_db.db`) | CLI runs never write it; metrics are in `loss_log.db` |

Flags for the user (recommendations only — configs are never edited on initiative):

1. **GPU choice is the cache lever.** L4 ~1.1 files/s ⇒ ~2.4 h one-time; A100 is
   several× faster. Decide before the first GPU session; bank the cache either way.
2. **`steps: 9489` = exactly 1 epoch.** Extending later means a **new run name**
   (`DECISIONS.md`: extending overwrites the un-suffixed final adapter).
3. **`save_every: 1500`** ⇒ session pause granularity and the ≤1500-step loss window.
   Fine for multi-day; confirm before launch.

## 2. Gate — Phase 1 base-model ceiling probe (blocks training)

`QURAN_PRON_REVIEW.md` §5: run the **base model (no LoRA) vs the existing
`quran_only` adapter** on the held-out hard-letter ayat (2:255), same seed,
**free-run**. If the base is also wrong → representational ceiling → **stop the
LoRA line**; training `quran_ahh_r8` is not justified. Do this in the first GPU
session, *before* any training. (If the user explicitly waives the gate, record it
in `current.md`.)

**Status: run 2026-10-05, then SUPERSEDED.** The probe ran (all arms `base`,
`quran_only`, `c1500…c9000`, `final` banked under `…/quran_ahh_r8/convert/`, driver
`INFERENCE/quran_pt_probe.py`); its verdict — "base also wrong ⇒ representational
ceiling" — was **rejected** as a stopping signal (the base was never trained on Quran, so
that inference is invalid). The revised config trains **AR+NAR** accordingly.

## 3. GPU session checklist

### Phase A — preflight (2 min)
- [ ] `nvidia-smi` (which GPU/VRAM) — **one GPU, shared; confirm nothing is running**
- [ ] branch = `pron-lora-long-aya`; `config/quran_ahh_r8.yml` parses
- [ ] disk free (dataset 3.8 G + cache ~0.6 G + checkpoints fit); `vm-continuity status`

### Phase B — bootstrap + restore (~parallel; see `START.md`)
- [ ] notebook cell 2 exports `GCP_AHH_DATASET_ZIP` (**not** `GCP_QURAN_LONG_DATASET_PATH`,
      which would pull the 28 GiB long-aya set). `setup.sh --training` has an opt-in
      `job_ahh_dataset` that `gcloud storage cp` + `unzip`s it to `/content/quran_ahh_dataset/`.
- [ ] `setsid nohup bash bootstrap/setup.sh --training > /content/logs/setup.log 2>&1 & disown`
      → wait for the all-`[ok]` verify block; it must show `[ok] AHH dataset: 9489 train pairs`
      (else read `/content/logs/ahh_dataset.log`)
- [ ] manual fallback: `gcloud storage cp "$GCP_AHH_DATASET_ZIP" /content/ && unzip -q /content/quran_ahh_dataset.zip -d /content/`
      → `find /content/quran_ahh_dataset/train -name '*.txt' | wc -l` = **9489**
- [ ] if a banked cache exists: untar it into `/content/quran_ahh_dataset/train/`
      (skips the ~2.4 h encode)

### Phase C — run the Phase 1 probe (§2), record verdict → **decision gate**

### Phase D — sidecars + launch (only if the gate passes)
- [ ] sidecars detached (backup + gpu logger); `pgrep -af 'backup_to_gcp.py|gpu_logger.py'`
- [ ] launch (user types it, detached): `python train_ctl.py start --config config/quran_ahh_r8.yml --run-name quran_ahh_r8 --log-name train_quran_ahh`
- [ ] first-launch latent-cache build runs **before step 1** — `loss_log.db` at 0
      steps for ~2.4 h is normal (no step-0 sample to mask it)
- [ ] **the moment the cache completes**, bank it:
      `tar -C /content/quran_ahh_dataset/train -cf - _latent_cache | gcloud storage cp - "$GCP_BACKUP_BASE/quran_ahh_dataset/_latent_cache.tar"`
- [ ] measure ~50 steps: s/step, VRAM peak, wall clock per 1500-step save
      (`monitor_loss.py <output>/loss_log.db --watch 30 --total-steps 9489` +
      `/content/logs/gpu_usage.csv`). **Do not edit the config.**

### Phase E — per-checkpoint offline eval
- [ ] free-run held-out 2:255 per checkpoint (adapt `INFERENCE/pron_ckpt_sweep.py`;
      the run has `disable_sampling: true`, so loss alone says nothing)
- [ ] human blind gate (`ab-blind-eval`) before any merge — no adapter is "best"
      before the listen

### Phase F — close each session
- [ ] `train_ctl.py stop --config config/quran_ahh_r8.yml --run-name quran_ahh_r8 --log-name train_quran_ahh`
- [ ] `backup_to_gcp.py --run-name quran_ahh_r8 --once` → confirm newest
      `*.safetensors` **and** `optimizer.pt` in GCS
- [ ] `vm-continuity status` (must read `state=OK`); update `current.md`

## 4. Continuity & hazards

- **Auto-resume trap:** `ai-toolkit` resumes from the newest checkpoint in
  `output/quran_ahh_r8/`. For a **fresh** start the folder must be empty; a resume
  is the **identical** config + run name with the output prefix restored first.
  For the revised run: the existing checkpoints are rank-8 **AR-only** and incompatible
  with the rank-32 **AR+NAR** network — do **not** restore the old output prefix.
- **Latent cache is adapter-independent** — the banked `…/quran_ahh_dataset/_latent_cache.tar`
  (703 MiB) is still valid for the revised config (rank/scope/KL/steps do not change the
  cache key); untar it to skip the ~50 min encode.
- **Cache is not backed up by the daemon** — bank it by hand (§Phase D). The dataset
  is still required every VM (the loader enumerates filenames); cache alone is not enough.
- **EMA restarts a fresh average on resume** (known, accepted). Saved adapters are EMA.
- **Dataset must be immutable once training starts** — changes desync the cache.
- **Never** run the same run name on two VMs; **never** edit the config mid-run; a
  planned pause is always a user-typed `stop`, not auto-resume.
- **Extending past 9489** overwrites the final adapter — new run name + copy the
  checkpoint/optimizer in (`DECISIONS.md`).

## 5. Decisions taken

1. **Phase 1 gate — run, verdict rejected** (2026-10-05). "Base also wrong" does not imply a
   representational ceiling; it only means the music base was never trained on Quran.
2. **Target GPU — L4** (23 GB). Cache build measured **~50 min** for 9,489 (not ~2.4 h);
   reuse the banked cache for the revised run.
3. **Acceptance bar** (`QURAN_PRON_REVIEW.md` §1): ≥90 % held-out ayat zero-makhraj at α=1.
4. **Config revision (user, 2026-10-05):** AR-only/rank-8 could move only prosody; train
   **AR+NAR jointly at rank 32, `ar_kl_weight 0.0`, 3 epochs** (v2's shape). Evaluate with
   the trained NAR, not a lone-AR render.
