# Future idea: fix Arabic pronunciation with a second (AR-only) LoRA

Status: **idea / research note — not scheduled, not a plan.** Written
2026-09-20, after the completed v2 run. Nothing here has been tried; treat it
as a starting point for a future session, not a directive. The *why* of the
current config lives in `../DECISIONS.md`; run history in `../PROGRESS.md`.

Source of the idea: the user, after listening to v2. Style/timbre/arrangement
are strong (10/10 as a match to the training data), but pronunciation is
~9/10 — specific letters soften (ح drifting toward خ/ه, ع toward أ). The
proposal was to add a small "pronunciation LoRA" trained on Quran recitation
(the strongest source of precise MSA/tajweed articulation), stacked at low
weight (e.g. style 1.0 + pronunciation 0.1) the way image multi-LoRA users
used to stack adapters.

Everything marked **(verified)** was read in a fresh clone of
`ostris/ai-toolkit` on 2026-09-20, not recalled from memory.

## Bottom line

- The instinct is **sound in principle**: LoRA deltas are additive in this
  stack, and pronunciation (AR) is a distinct subsystem from style/timbre
  (NAR), so the two *can* be composed.
- It is **not** a drop-in "style 1.0 + pron 0.1": today's tooling loads one
  adapter at a time. You would merge the two LoRAs offline (easy) rather than
  stack them live.
- **Biggest upside vs. image multi-LoRA:** if the two adapters are scoped to
  *different experts* (one NAR-only, one AR-only) their weights are disjoint,
  so the sum is exact and interference-free. Image LoRAs collide because they
  touch the same U-Net weights.
- **Biggest risk (could make the whole idea moot):** the MERT semantic tokens
  may not encode the ح/خ and ع/أ contrasts well enough for *any* adapter to
  fix. Test the base model first — it is free and decides whether the plan is
  worth compute.
- **Best order:** try the cheap config-level levers first (see below); build
  the pronunciation adapter only if articulation still lags.

## 1. Where pronunciation lives in YuE2 (verified)

Two experts:

- **AR ("semantic")** — picks the codec/semantic tokens, i.e. *which phonemes
  and notes*. Conditioned on the caption (style tags + lyrics).
- **NAR (acoustic/rendering)** — turns those tokens into audio: timbre, mix,
  instrumentation.

The errors above are place-of-articulation choices, i.e. the AR picked the
wrong token. So pronunciation is an **AR-side** quantity, and a pronunciation
adapter is an AR-side adapter.

Verified in source:

- `yue2_model.py:193` — `target_lora_modules = ["YuE2AR", "YuE2NAR"]`: the
  network is applied to **both** experts. The current v2 LoRA is therefore a
  combined AR+NAR adapter (why it moved both style and pronunciation).
- The AR is trained by next-token cross-entropy (`loss/ar_ce`), computed from
  the song start so lyrics and tokens stay aligned.
- An independent real YuE2 LoRA runtime (`vrgamegirl19/Yue2_Studio`,
  `docs/lora.md`) classifies adapters as *acoustic/style (NAR-only)* vs
  *semantic/artist (affects semantic generation = AR)*. That is exactly the
  intended split: pronunciation = a semantic/AR adapter.

## 2. Stacking math — and why this is better than image LoRAs (verified + judgment)

ai-toolkit merges a network as a literal linear sum
(`toolkit/lora_special.py`, `merge_in()`):

```
merged = base_weight + merge_weight * delta
```

so two adapters compose as `W = W_base + a1*dW1 + a2*dW2` ("task arithmetic").

This is the mechanism SD multi-LoRA used. In images it was unreliable because
two LoRAs both modified the **same** U-Net weights and their deltas collided.
Here:

- One adapter touching **only NAR** (style) and another **only AR**
  (pronunciation) live in **disjoint parameter sets**. The sum is then exact —
  no interference — and the pronunciation strength is a clean dial.
- If **both** are trained AR+NAR (v2's shape, and the default shape of any
  ai-toolkit YuE2 LoRA), they collide precisely in the AR — the subsystem you
  are trying to fix.

So **scoping the two adapters to different experts is the whole ballgame.**

ai-toolkit can scope: `network_kwargs.ignore_if_contains` matches the dotted
module path (`toolkit/lora_special.py:524`). Saved keys are named
`transformer.ar.*` / `transformer.nar.*` (`yue2_model.py:774-792`):

```yaml
ignore_if_contains: ["transformer.nar"]   # -> AR-only (semantic / pronunciation)
ignore_if_contains: ["transformer.ar"]    # -> NAR-only (acoustic / style)
```

## 3. Tooling reality today: you cannot just set 1.0 / 0.1 (verified)

- ai-toolkit loads exactly **one** network at inference. The extra LoRA slot
  (`assistant_lora_path` / `inference_lora_path`) is Flux-only —
  `toolkit/assistant_lora.py` raises *"Only Flux models can load assistant
  adapters currently."*
- `Yue2_Studio` states plainly: *"one Style adapter or Artist bundle at a
  time"* and *"There is no arbitrary Style + Artist stacking."* (0–2 strength
  slider, one adapter.)
- **But merging offline is trivial** because the layout is simple and
  additive:

  ```
  W_merged = W_base + 1.0 * dW_style + alpha * dW_pron   (per key, ar/nar)
  ```

  Write that as a single safetensors and load it as the one network. (Or chain
  LoRA loader nodes in ComfyUI, which supports multiple.)

## 4. Is Quran recitation the right donor? (judgment; one real risk)

The premise "it's the data — ~90% of Arabic music is dialectal" is plausible
but **not proven**. History matters: v1's real bug was missing lyrics in the
caption; v2 fixed that and pronunciation is now ~9/10. What remains could be
(a) scarcity of fusha **sung** data, or (b) a representation limit — and if
(b), no LoRA helps (see the risk below).

**For a recitation donor:**

- Reciters are the strongest source of precise MSA/tajweed articulation.
- Scoped AR-only, most of recitation's "wrong" character (solo voice, no
  instruments, room sound) lives in the NAR and never transfers — so the idea
  is safer than it first looks.

**Against / risks:**

- **Domain:** recitation is unaccompanied, slow, with tajweed prosody (long
  madd). Some of that rides the semantic tokens, so at low weight you might
  hear stretched vowels / recitation cadence bleeding into singing.
- **Quran ≠ sung fusha.** A recitation adapter may push toward *recitation*,
  not *classical singing*. Fusha **sung** material (old classical /
  muwashshahat) is the closer domain; recitation is a decent second choice.
- **Ceiling risk (decisive):** the audio was encoded to MERT semantic tokens.
  If those tokens don't cleanly separate ح/خ and ع/أ, the AR cannot express
  the distinction and no weight arithmetic recovers it. Cheap test: base
  model, **no LoRA**, same seed, held-out lyrics with the hard letters
  (`INFERENCE/yue2_eval_heldout/`; the Ajam entry is a good probe). If it
  never produces a crisp ح/ع anywhere, the bottleneck is representational.
- **Licensing:** the Quran *text* is public domain; specific recitation
  *recordings* are not necessarily license-free even when widely circulated.
  Don't assume they're free to train on if this is commercial.

## 5. Cheaper levers to try first (config-level, no new dataset)

Each tests the same hypothesis (can articulation be nudged independently?)
without building anything new. One at a time, per project discipline:

- **`do_separation: true`** (verified, exists) — adds an explicit
  (lyrics-only → vocals-only) AR loss term alongside the mix term
  (`yue2_model.py` docstring lines 19–25; `separation_vocals_weight: 0.5`,
  `separation_music_weight: 1.0`). The purpose-built lever for
  lyric-conditioned articulation. **Note:** changes the cache version to
  `_sep` → delete `_latent_cache` and rebuild.
- **`sample_ar_temperature`** (default 1.0) down, and
  **`sample_ar_repetition_penalty`** (already 1.2) — inference-time
  articulation/consistency; free to A/B.
- **`ar_lr_multiplier`** (verified, exists) and **`ar_kl_weight`** — AR-specific
  knobs already in code; `ar_kl` never plateaued (1.50 → 1.54 across v1→v2), so
  it is a known-soft anchor.
- **Diacritics** — the dataset preserved tashkeel; make sure the sample/eval
  prompts are fully diacritized too (the held-out prompts appear to be). Full
  tashkeel helps the AR disambiguate letters/vowels.
- **Baseline A/B** — base model (no LoRA) vs v2, same seed + same lyrics, with
  and without diacritics. Tells you how much of the 9/10 is the model's own
  ceiling vs. the LoRA vs. the caption format.

## 6. If the pronunciation LoRA is still wanted — the clean design

1. **Train adapter B AR-only:** `network_kwargs.ignore_if_contains:
   ["transformer.nar"]`. Donor: fusha sung if available, else Quran
   recitation. It cannot touch timbre/instrumentation, so it cannot damage the
   style. Keep it small (low rank), single-purpose.
2. **Re-scope the style adapter to NAR-only**
   (`ignore_if_contains: ["transformer.ar"]`) for the truly interference-free
   sum — or keep the existing combined v2 and accept that its AR delta and the
   pronunciation delta overlap and interact.
3. **Merge at inference:** `W = W_base + 1.0*dW_style + alpha*dW_pron`, alpha
   small. With disjoint sets, alpha is a clean dial.
4. **Evaluate apples-to-apples** on `INFERENCE/yue2_eval_heldout/` plus the
   clean Ajam entry. Watch for recitation-prosody bleed (stretched vowels).

## Verdict

- Conception is right in principle: adapters are additive (verified), and
  pronunciation is a distinct subsystem (AR) from style/timbre (NAR).
- Not a drop-in "style 1.0 + Quran 0.1": one adapter at a time today — merge
  offline instead (easy).
- Biggest upside vs. image LoRAs: disjoint-expert scoping makes the
  combination exact and interference-free.
- Biggest risk: MERT semantic tokens may not encode the pharyngeal contrasts
  well enough for any adapter to fix. Test that on the base model first.
- Suggested order: (5) `do_separation` + diacritics, then (6) an AR-only
  pronunciation adapter only if articulation still lags.
