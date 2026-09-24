# AR-only pronunciation LoRA — source verification (Task 14)

Read-only verification against `ostris/ai-toolkit` @ `460c29b` (cloned to
`/content/ai-toolkit`, source only, no run). File:line citations are for that
checkout. This is a **separate** AR-only LoRA that will be merged offline with
the frozen v2 style LoRA: `W = W_base + 1.0*dW_style + alpha*dW_pron`. v2 is
never retrained or modified.

## A0 — dataset placement

Task 13's output (`/content/arabic-phoneme-difficulty-quran/data/pron/training_set/`,
branch `pron-lora-prep` @ `df3193d`) is exposed at `/content/pron_dataset/` with
**symlinks** (same VM):

```
/content/pron_dataset/train -> .../data/pron/training_set/train
/content/pron_dataset/val   -> .../data/pron/training_set/val
/content/pron_dataset/smoke -> .../data/pron/training_set/smoke
```

Verified counts through the symlinks: **12,200** in `train` (6,100 mp3 +
6,100 txt), **360** in `val`, **32** in `smoke`. Nothing was modified or rebuilt.

## A1 — `ignore_if_contains: ["transformer.nar"]` scopes the adapter to AR

Static reading:

- `network_kwargs.ignore_if_contains` defaults to `[]`
  (`toolkit/lora_special.py:362-364`) and is matched against the **dotted**
  module name `clean_name`: `if any([word in clean_name for word in
  self.ignore_if_contains]): skip = True` (`toolkit/lora_special.py:523-525`).
- For a transformer/peft network the LoRA prefix is `transformer`
  (`toolkit/lora_special.py:466-469`), and names are built as
  `prefix + "." + module_path + "." + child` (`toolkit/lora_special.py:491-496`).
  The yue2 experts are the top-level `ar`/`nar` children of the trained module,
  so the candidate names are `transformer.ar.*` and `transformer.nar.*`. The
  filter therefore drops every `transformer.nar.*` module and keeps only
  `transformer.ar.*`.
- **Important, and different from the task brief:** the in-memory keys are
  `transformer.ar.*` / `transformer.nar.*`, but the **saved** file is rewritten
  before writing by `convert_lora_weights_before_save`
  (`extensions_built_in/audio_models/yue2/yue2_model.py:785-793`), called from
  `toolkit/network_mixins.py:637-638`:
  `transformer.nar.* -> diffusion_model.*`, `transformer.ar.* -> text_encoders.*`.
  Consequence: a literal `transformer.ar.*` / `transformer.nar.*` key count in
  the `.safetensors` is **0 for both**; the AR adapter lives under
  `text_encoders.*` and a stray NAR adapter would appear under
  `diffusion_model.*`. This is corroborated by the existing v2 adapter: the
  split files in `/content/converter/out/` were produced by
  `convert_aitoolkit_yue2_lora.py`, whose regex expects exactly
  `text_encoders.model.layers.*` (AR) and `diffusion_model.model.layers.*` (NAR)
  (`/content/converter/out/convert_aitoolkit_yue2_lora.py:40-44`).
  So the smoke assertion becomes: `diffusion_model.*` count == 0 (NAR ignored),
  `text_encoders.*` count > 0 (AR present). The literal `transformer.*` counts
  are reported too, and are 0 as saved. See the smoke section.

## A2 — exact blank `trigger_word` (nothing prepended)

`trigger_word` defaults to `None` (`toolkit/config_modules.py:933`) and is read
job-level with the same default (`jobs/process/BaseSDTrainProcess.py:135`).
Training only injects when it is not `None`
(`jobs/process/BaseSDTrainProcess.py:1079-1084`), and the injector itself only
prepends inside `if trigger.strip() != ""` (`toolkit/prompt_utils.py:736-742`).

- `trigger_word: ""` → not `None`, so the injector is called, but
  `"".strip() == ""` → nothing is prepended.
- `trigger_word: null` / omitted → `None` → injection is skipped → nothing is
  prepended.

Both are safe; **`trigger_word: ""`** is used in the config (the "blank form"
that provably no-ops through the injector rather than around it). The pron
captions carry no trigger word by design.

## A3 — validation / eval dataset support

`diffusion_trainer` has a validation path, but it is **image-only**:

- `ValidationConfig` / `ValidationItem` are keyed on `image_path`
  (`toolkit/config_modules.py:343-357`); the train config reads
  `validation_config` (`toolkit/config_modules.py:621-624`).
- `setup_validation()` opens each item with `PIL.Image.open(...).convert("RGB")`
  and buckets by image resolution (`jobs/process/BaseSDTrainProcess.py:1567-1617`).
- There is no audio/eval-dataset hook: no field that loads a folder of
  `(audio, caption)` pairs and runs the training loss on it.

So no in-training validation on `/content/pron_dataset/val`. **Smallest offline
alternative (not built here):** a script that, for each checkpoint, loads the
adapter through `convert_lora_weights_before_load`
(`yue2_model.py:795-802`), runs the same per-item forward/loss path as training
(`yue2_model.py:630-704`, `_ar_losses` at `506-574`) over the 180 `val` pairs,
and reports `loss/ar_ce` (and `loss/ar_kl`). That reuses the exact loss code
path without touching the trainer.

## A3b — offline AR-loss replay built + CPU benchmark (Task 16B, 2026-09-24)

Built: `offline_ar_loss_replay.py` (repo root) + `tests/test_offline_ar_loss_replay.py`
(9 tests, no model load). It builds the same `LoRASpecialNetwork` the trainer builds,
loads the saved adapter through `sd.convert_lora_weights_before_load`, and calls
`_prefix_segment` / `_item_prefix_and_abc` / `_ar_inputs` / `_ar_losses` directly.
Forward passes only: no trainer, no backward, no optimizer, no NAR flow forward (the
NAR contributes to neither `ar_ce` nor `ar_kl`).

- **Assets** (resolved from the HF cache already pre-warmed by `bootstrap/setup.sh
  --training`; auto-materialized on load into `/content/ai-toolkit/models/`):
  `Comfy-Org/YuE2/checkpoints/yue2_3b_int8_convrot.safetensors`, `m-a-p/MERT-v2-FullSong`,
  `Mothersuperior/yue2-mothersuperior-realaudio-tokenizer-v4/tokenizer_head_joint_v4.pt`.
  **Val path: `/content/pron_dataset/val`** (180 mp3 + 180 txt; audio is 44.1 kHz and is
  resampled to MERT's 24 kHz inside `SemanticTokenizer.tokenize`).
- **CPU works, with a numeric caveat.** On the CPU-only benchmark VM, ai-toolkit prints
  `ConvRot: int8 matmul (torch._int_mm) is not usable on this device (cpu). Inference
  falls back to dequantized bf16 matmuls ... W8A16 numerics instead of W8A8`. Nothing
  blocked the run; the fallback is correct output but slower, and its numerics are not
  bit-identical to training's W8A8 path.
- **Benchmark — `python offline_ar_loss_replay.py --checkpoint final --limit 8` (CPU),
  38.2 min wall incl. 72.6 s model load.** Per-item mean **tokenize 3.70 s, AR-loss
  forward 272.79 s, total 276.49 s**. Loss scales with target-token count (~0.69 s/token:
  594 tok → 409 s, 442 → 298 s, 276 → 198 s). Mean over the 8 items: **`loss/ar_ce`
  4.0652, `loss/ar_kl` 1.3636** (range `ar_ce` 3.75–4.31, `ar_kl` 1.25–1.53) — the same
  neighborhood as the training last-50 means (`ar_ce` 4.397, `ar_kl` 1.533), finite, not
  NaN.
- **Extrapolation:** **720** forward passes (180 pairs × **4** checkpoints — there is no
  `_000006100` numbered file; the post-loop no-step save *is* step 6100, see
  `docs/L4_HANDOFF_TASK14C.md` §2) × 272.79 s = 196,409 s ≈ **54.6 h** on this CPU box,
  plus tokenization (~0.9 h per full pass if recomputed; cacheable to ~0.2 h once).
  *(Corrected 2026-09-24: this line read "900 … × 5 checkpoints ≈ 68.2 h", counting a
  fifth checkpoint that does not exist.)*
- **STOP (deliberate):** the sweep was **not** run on CPU, checkpoints were **not**
  compared there, and no pronunciation conclusion is drawn. Whether to run the full sweep
  on CPU or wait for an L4 was the user's call — **resolved: run it on the L4, below.**
- **Gotcha:** on a CPU-only host `toolkit.util.get_model.get_model_class()` raises
  `RuntimeError: Found no NVIDIA driver` — an unrelated extension (omnigen2) calls
  `torch.cuda.current_device()` at import time and `get_all_models()` only catches
  `ImportError`. The replay imports `YuE2AudioModel` directly to avoid this.

### A3b (L4) — full 720-pass sweep run on GPU, 2026-09-24

The sweep the CPU benchmark deliberately stopped short of was run on a Colab **L4**
(sm_89). The target was to confirm the int8 path actually engages on CUDA first, since
the CPU VM fell back to dequantized bf16 (W8A16).

- **Kernel smoke (`--checkpoint final --limit 8 --device cuda`): PASS.** Per-item AR-loss
  forward **0.61 s mean / 0.23 s steady-state** vs the CPU's **272.79 s/item** — ~450×, a
  *qualitative* jump, not the proportional gain more CPU cores could give. The CPU
  fallback warning (`torch._int_mm … not usable on this device`) is **absent** from the L4
  log, i.e. the W8A8 int8 path ran (compute capability 8.9 has a CUDA `torch._int_mm`
  kernel; the CPU has none). Loss means match the CPU benchmark to 4 dp (`ar_ce` 4.0652,
  `ar_kl` 1.3653/1.3636), confirming the same loss path.
- **Full sweep: 4 checkpoints × 180 val pairs = 720 forward passes**, ~23 min wall, zero
  errors. Raw JSON in `results/replay_l4_full_<ckpt>.json`; full stdout
  `results/replay_l4_full_sweep.log`; summary `results/README.md`.

| checkpoint | step | mean `ar_ce` | mean `ar_kl` |
|---|---|---:|---:|
| `_000001525` | 1525 | 5.1157 | 0.7180 |
| `_000003050` | 3050 | 4.6202 | 1.2715 |
| `_000004575` | 4575 | 4.5053 | 1.4241 |
| `final` | 6100 | **4.4507** | **1.4828** |

`ar_ce` falls monotonically (5.12 → 4.45) while `ar_kl` rises monotonically (0.72 → 1.48),
with strongly diminishing `ar_ce` returns after 3050 (4575→final: −0.05 `ar_ce` for
+0.06 `ar_kl`). This is a held-out loss report only; it does **not** pick the merge
checkpoint/alpha, and no merge has been run.

## A4 — what `loss/ar_kl` measures; what changes when only AR is trainable

- `ar_loss_weight` defaults to `1.0` (`yue2_model.py:200`); the added loss is
  `ar_ce * ar_loss_weight` and, when `ar_kl_weight > 0`, `+ ar_kl * ar_kl_weight`
  (`yue2_model.py:701-703`). This config keeps `ar_kl_weight: 0.2`.
- `ar_kl` is a trust region measured as **KL(base ‖ lora)** on the AR
  next-token distributions, where "base" runs the AR with the network switched
  off (`net.is_active = False`, `yue2_model.py:515-526`, KL computed at
  `536-539`). It constrains how far the AR drifts from the frozen base.
- With `transformer.nar` excluded, the NAR has **no trainable params**. The flow
  (MSE) loss still runs and is logged, but its input KV cache is explicitly
  detached (`cache = [(k.detach(), v.detach()) ...]`, `yue2_model.py:687-689`)
  and the NAR weights are frozen, so it produces no gradient. Only `ar_ce` and
  `ar_kl` train anything.
- `content_or_style` (`TrainConfig`, `toolkit/config_modules.py:381`) only
  controls the timestep sampler for the flow loss. With the NAR frozen and the
  AR decoupled from the flow loss, it no longer affects what is trained; it is
  kept set (to v2's value) but is inert for this adapter.
- The **NAR forward still runs** every step (`model.nar(...)`,
  `yue2_model.py:689`), and the AR `prefill` runs for both CE and the KL base,
  so the per-step compute cost is essentially the same as v2 except the
  AR-only backward. Nothing was changed.

## A5 — latent cache location and non-collision with v2

Cache files are written next to the media as
`<dirname(media)>/_latent_cache/<stem>_<hash>.safetensors`
(`toolkit/dataloader_mixins.py:1886-1901`). For this run that is
`/content/pron_dataset/train/_latent_cache/` (resolving through the symlink to
the Task 13 folder). v2's cache is `/content/yue2_dataset/_latent_cache/`.
Different directories, so no collision and no reuse. The per-file hash includes
the model's latent-space/text-embedding space version
(`yue2_model.py:308-321`, used at `toolkit/data_loader.py:508-509`), so even the
same file cannot silently reuse a stale cache. No action needed.

## A6 — `train.steps` semantics; conv effect on an AR-only linear LoRA

- The loop is `for step in range(start_step_num, self.train_config.steps)`
  (`jobs/process/BaseSDTrainProcess.py:2528`); each iteration fetches
  `gradient_accumulation` micro-batches (`:2560`) and calls
  `self.accelerator.accumulate(...)` once (`:2619`). `steps` therefore counts
  **loop iterations (micro-batch rounds)**, not micro-batches individually; the
  number of optimizer steps is governed by `gradient_accumulation` /
  `gradient_accumulation_steps` (`toolkit/config_modules.py:458-465`). With
  **batch_size 1 and gradient_accumulation 1**, one iteration = one optimizer
  step = one sample, so `steps: 6100` = 6,100 samples = exactly **1 epoch**.
  (Also: a final no-step checkpoint is always saved after the loop,
  `jobs/process/BaseSDTrainProcess.py:2813-2814`.)
- `conv` / `conv_alpha` size the LoRA only for **3×3 Conv2d** children: linear
  (and 1×1 conv) modules use `lora_dim`/`alpha`, and only non-1×1 conv children
  use `conv_lora_dim`/`conv_alpha`
  (`toolkit/lora_special.py:585-590`). yue2's target modules are the
  `YuE2AR`/`YuE2NAR` experts (`yue2_model.py:197`) whose projections are Linear,
  so `conv`/`conv_alpha` create no modules and have no effect. They are kept at
  v2's `16/16` so the only differences are the intended ones.

## A7 — training-mode `setup.sh` always downloads the v2 dataset too

- `bootstrap/setup.sh:93` hard-requires `GCP_DATASET_PATH` in training mode
  (`DATASET_GCS="${GCP_DATASET_PATH:?…}"`), and `start_job dataset job_dataset`
  (`:302`) runs unconditionally in training mode. So a VM used only for the pron
  run still downloads the v2 dataset into `/content/yue2_dataset` in the
  background.
- This is **harmless** for the pron run: it is a separate directory, the pron
  adapter reads only `/content/pron_dataset/*`, and the two GCS prefixes are
  siblings (`dataset/` vs `pron_dataset/`), so `job_dataset`'s recursive rsync
  can never pull pron files into `/content/yue2_dataset` (or vice versa) —
  provided `GCP_DATASET_PATH` actually points at `.../dataset`.
- **Not modified on purpose.** Making `job_dataset`/line 93 conditional was
  deliberately avoided; the fix belongs in the launching notebook, which must
  export `GCP_DATASET_PATH=.../dataset` **and** `GCP_PRON_DATASET_PATH=.../pron_dataset`
  (see `docs/PRON_LORA.md`).
- Failure mode actually observed on the 2026-09-24 L4 smoke VM: the notebook set
  `GCP_DATASET_PATH=.../pron_dataset` and omitted `GCP_PRON_DATASET_PATH`. Then
  `job_dataset` downloaded the pron set into `/content/yue2_dataset` and
  `job_pron_dataset` was skipped, so `/content/pron_dataset` did not exist. The
  smoke was blocked until the pron set was re-pulled from GCS; the notebook was
  then corrected (both variables, plus the branch checkout).

## Smoke checkpoint inspection (PASS) — L4, 2026-09-24

Command (user-typed, foreground):

```
cd /content/ai-toolkit
python run.py /content/maqamrock-yue2-lora-finetuning/config/pron_lora_ar_only_smoke.yml -l /content/logs/train_smoke.log
```

Result: 10/10 steps, clean exit, checkpoint + optimizer written, no traceback
and no OOM. One preflight issue (the notebook env misconfiguration above) was
corrected before the run; `setup.sh`'s two `[FAIL]` verify lines on this VM were
false negatives (the v2-layout verify globbed `/content/yue2_dataset/*.mp3`,
which is empty because the data that landed is nested; torch itself is fine:
`torch 2.13.0+cu130`, `cuda 13.0`, real mp3 decode OK).

Artifact `output/pron_lora_ar_only_smoke/pron_lora_ar_only_smoke.safetensors`:

- total tensors: **224**
- by prefix: `text_encoders.*` **224**, `diffusion_model.*` **0**, literal
  `transformer.*` **0**, any other prefix **0** (the post-save rewrite in A1
  moved every AR key to `text_encoders.*`; nothing landed under
  `diffusion_model.*`)
- structure: **28 layers** × 4 fused projections (down_proj, gate_up_proj,
  o_proj, qkv_proj) × 2 (A/B) = 224
- LoRA rank: **{8}** — every `lora_A` first dim == 8 and every `lora_B` second
  dim == 8
- dtype: **BF16** (all 224 tensors); file size **14,709,672 bytes (14.03 MiB)**

Losses (all finite, no NaN/inf):

- `loss/loss` 6.8851 → 7.0047, `loss/ar_ce` 5.6370 → 5.9339,
  `additional_model_loss` 5.6372 → 5.9343, `loss/ar_kl` 0.0011 → 0.0019.
- `loss_log.db` records steps 1–9 (9 rows); the 10-step tqdm prints 10 distinct
  finite `loss:` values. `ar_kl` is tiny because this is a 10-step AR-only run
  and the KL anchor starts near zero — not comparable to a full run's drift.

Step time / VRAM — **L4 numbers, warmup-inflated, NOT an A100 estimate**:

- tqdm: 10 steps in ~14 s; first step **5.29 s** (warmup), steady-state
  **~1.0 s/step**; `monitor_loss.py` reports ~0.943 steps/s. Latent cache for
  the 16 smoke clips built in ~21 s.
- Peak VRAM from `gpu_usage.csv`: **8,060 MiB** of 23,034 MiB (max util 40 %,
  peak power 50.4 W, max temp 46 °C). The 10 s CSV sampling can miss a transient
  peak — treat 8,060 MiB as a lower bound. Far below the whole-song music peak
  (~15.8 GB) because the smoke set is short recitation clips.

Latent cache: written to **`/content/pron_dataset/smoke/_latent_cache`** (16
files), alongside `/content/pron_dataset/smoke/_t_e_cache`. `/content/yue2_dataset`
was **not modified** (mtime unchanged; no cache written under it).

### Verdict: **PASS**

All criteria hold: `text_encoders.*` count > 0 (224), `diffusion_model.*` count
== 0, no unexpected prefixes, every LoRA rank == 8, all losses finite, run
completed with no OOM or crash.

## A100 preflight — 2026-09-24 (fresh A100 VM, real run)

Target: `config/pron_lora_ar_only.yml`, run name `pron_lora_ar_only_r8`, 6,100
steps (1 epoch over 6,100 train pairs), `save.save_every: 1525`.

- **(a) setup.sh** finished cleanly: `/content/logs/setup.log` ends
  `=== setup.sh done (training) — total 225s ===` (exit 0). All verify lines are
  `[ok]` — **no `[FAIL]` lines** (unlike the L4 smoke VM, whose two `[FAIL]`s
  were confirmed false negatives). Parallel jobs all `[ok]` (`ai_toolkit`,
  `dataset`, `pron_dataset`, HF caches).
- **(b) dataset** `/content/pron_dataset/`: `train` has **12,200** entries
  (**6,100** `.mp3` + **6,100** `.txt`, every mp3 has a matching txt), `val`
  **360**, `smoke` **32**; `.bootstrap_complete` present. All entries are **real
  files** (0 symlinks in any split — this is a fresh VM pulling from GCS, not the
  old same-VM symlink exposure). **No `_latent_cache`** exists under any split
  (fresh VM). The first minutes of the real run (before step 1) are latent
  caching, not a hang.
- **(c) runtime**: `/content/ai-toolkit` exists at `460c29b`. `nvidia-smi`:
  **NVIDIA A100-SXM4-80GB**, **81,920 MiB** total VRAM, **0 MiB used**, 0 %
  util, no running processes — **GPU free**. No `run.py` process.
- **(d) sidecars**: neither `backup_to_gcp.py` nor `gpu_logger.py` was running;
  both start commands were handed to the user (see below). `GCP_BACKUP_BASE` is
  exported: `gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning`
  (printed by `echo`). `backup_to_gcp.py`'s `training_targets("pron_lora_ar_only_r8")`
  maps `/content/ai-toolkit/output/pron_lora_ar_only_r8 -> <base>/pron_lora_ar_only_r8/output`,
  so the new output folder **is** covered by `TARGETS` — no script change needed.
  (`gcp_backup.log` is absent until the daemon is launched; not a failure.)
- **(e) config on disk == branch tip**: `git status --porcelain config/` empty;
  `sha256sum config/pron_lora_ar_only.yml` =
  `15a27a4d204438398787a4c71f547e30c7e15a272fa331b106951e235d04c3bc`, identical
  to `git show HEAD:config/pron_lora_ar_only.yml`.

**A100 preflight verdict: PASS.** Real-run command handed to the user
(foreground, `Ctrl+C` stops). No A100 step-time estimate is given up front:
the L4 smoke number does not transfer to the short pron clips, and the old
~3.10 s/step A100 figure is for whole songs. Measure via `monitor_loss.py`
after ~50 steps.

## Real run results (A100) — COMPLETE, 2026-09-24

`pron_lora_ar_only_r8` finished **6100/6100 (1 epoch)** at ~07:27 UTC. Clean
exit: final adapter + optimizer written, **no traceback, no OOM**. Final
adapter metadata `training_info = {"step": 6100, "epoch": 1}`.

Artifacts (local `/content/ai-toolkit/output/pron_lora_ar_only_r8/` **and** GCS
`gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/pron_lora_ar_only_r8/output/`,
9 objects / 73.27 MiB total, verified with `gcloud storage ls -l`):

| file | bytes |
|---|---|
| `pron_lora_ar_only_r8_000001525.safetensors` | 14,709,664 |
| `pron_lora_ar_only_r8_000003050.safetensors` | 14,709,664 |
| `pron_lora_ar_only_r8_000004575.safetensors` | 14,709,664 |
| `pron_lora_ar_only_r8.safetensors` (final, step 6100) | 14,709,664 |
| `optimizer.pt` | 15,174,731 |
| `loss_log.db` (+`-shm`/`-wal`) | 2,785,280 |
| `config.yaml`, `tensorboard/` | present |

**Note:** there is **no `_000006100` numbered file** — numbered saves occur at
1525/3050/4575 (the loop runs steps 0–6099); the post-loop no-step save *is* the
step-6100 artifact (metadata-verified). Four trainable artifacts total, not five.

Losses at the end (step 6099): `loss/loss` **5.412**, `loss/ar_ce` **4.163**,
`loss/ar_kl` **1.531**. Last-50 means: `loss/loss` 5.815, `loss/ar_ce` 4.397,
`loss/ar_kl` 1.533. First-50 → last-50: `ar_ce` 6.13 → 4.40 (−1.73). `ar_kl`
rose monotonically all run (0.21 → 1.53, bounded, max 2.19) — same shape as the
v1/v2 whole-song runs. Median step time **0.886 s**; 1.52 h logged. GPU peak
10.5 GB / 80 GB, util p50 22 % (data/CPU-bound, not compute-bound). Full charts
and discussion: `TRAINING_ANALYSIS/pron_lora_ar_only_r8/ANALYSIS.md`.

No in-training validation and no samples (`disable_sampling: true`), so this is
a loss report only; articulation quality needs the offline `val`-replay audit
(A3) before any merge.
