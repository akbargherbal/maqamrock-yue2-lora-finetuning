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

## Smoke checkpoint inspection (pending)

To be appended after the user runs the smoke command (step C):

```
cd /content/ai-toolkit
python run.py /content/maqamrock-yue2-lora-finetuning/config/pron_lora_ar_only_smoke.yml -l /content/logs/train_smoke.log
```

Expected: total tensors > 0; `diffusion_model.*` == 0; `text_encoders.*` == 224
(28 layers × 4 fused projections × 2 for A/B); literal `transformer.ar.*` and
`transformer.nar.*` == 0 (post-save prefix rewrite, see A1); LoRA rank decoded
from `text_encoders.*.lora_A` shape == 8. Per-step time and peak VRAM from
`/content/logs/train_smoke.log`.
