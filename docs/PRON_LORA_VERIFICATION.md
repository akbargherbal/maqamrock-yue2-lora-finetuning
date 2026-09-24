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
