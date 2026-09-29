# Milestones

Durable, cross-session record of **what has actually been run and what it produced** — outcomes,
not narrative. One block per milestone. *Why* things are the way they are lives in
`DECISIONS.md`; per-session state lives in `agent_notes/current.md`; the full chronological
narrative lives in git — pre-rewrite history at `git show 39d1bbd:PROGRESS.md` (and `git log`).

> **Consolidate before merging to `main` — rule agreed 2026-09-29.** Anything this branch
> (`music-cover`) adds here must be **consolidated into milestones** before the final merge:
> a few outcome blocks, **not** a chronological log of every change, test or experiment we ran.
> If an entry does not change *what was run or what it produced*, it does not belong in this
> file — put it in `agent_notes/current.md`, or leave it in git. Write the branch's contribution
> as one or two milestones, in the same shape as M1–M11.
>
> **Status: the branch's milestones are deliberately unwritten.** They are to be added as
> consolidated blocks before the merge — not appended turn by turn. Per the `docs-reconciler`
> skill's consolidation mode, that runs as its own pass and needs the user's approval.

## M1 — Dataset v1 built and independently verified · 2026-09-19

- 267 audio/caption pairs (native `mp3, 48000 Hz, stereo`) from the `min_4stars_ai_music` tree;
  audit in `verification.md`. Config finalized (`config/akbar_arabic_rock_lora.yml`).
- `bootstrap/setup.sh` validated end-to-end on a fresh Colab **L4** after fixing two blockers
  (stale `scipy`/`torchcodec` pins; torch/`torchcodec` CUDA mismatch). Observability settled:
  `loss_log.db` + `gpu_logger.py`.

## M2 — v1 scope correction: killed and relaunched · 2026-09-19

- Goal clarified mid-run to **full-song structure**; `model_kwargs.train_window_frames` (60 s
  default) was the blocker. First run killed at ~step 875/3000 and archived
  (`…_crop60_killed`); relaunched with `train_window_frames: 0`.

## M3 — v1 completed 3000/3000 (A100) — pronunciation root-caused · 2026-09-19

- Whole-song run finished 3000/3000 on an A100-SXM4-80GB (~3.1 s/step). Style/timbre strong,
  but Arabic pronunciation degraded. **Root cause: the captions carried no lyrics at all**, so
  the AR expert was never rewarded for getting words right (`loss/ar_ce` rewarded style-only
  matching; `ar_kl` drifted 0.37→1.50). Superseded by v2.

## M4 — Dataset v2 (lyric-conditioned) built, verified, promoted; held-out eval set · 2026-09-20

- 267 pairs rebuilt with real lyrics in YuE2's native `[Lyrics]` format, trigger
  `arabmaqamrock `; verified against the manifest (`0` empty lyrics, 157 distinct texts) and
  promoted to the plain names (`./yue2_dataset`, GCS `dataset/`). Built offline (script not in
  repo). Held-out set (`INFERENCE/yue2_eval_heldout/`, 0 shared lines) + training samples moved
  to real lyrics at `sample.duration: 360`.

## M5 — v2 completed 3000/3000 (A100) — pronunciation ~9/10 · 2026-09-20

- Same A100, captions the only change: `loss/loss` 6.23→4.79, `ar_ce` 5.19→3.61 (vs v1
  5.17/3.97). First systematic listening pass on all four maqams: no substitutions except one
  ح→خ, materially better than v1; enjambment pauses confirmed inherited from base YuE2.
  Write-up: `TRAINING_ANALYSIS/ANALYSIS.md`.

## M6 — audio.cpp inference harness (GGUF + converted LoRA) · 2026-09-21 → 09-23

- Ad-hoc inference on `0xShug0/audio.cpp` @ `e3de8e3`. Root cause of an early OOM: the attention
  kernel under `yue2.attention=auto` on CC 7.5 — forcing `flash` halved VRAM. Built
  `INFERENCE/run_one.sh` + `INFERENCE/generate.py` (JSON batch), the text→duration cap
  (`duration_cap.py`), and the per-arch binary build method (`docs/audiocpp_gpu_arch_builds.md`;
  sm_75/T4 and sm_89/L4). Batches: **16/16** (T4) and **21/21** (T4) exit 0; benchmarks in
  `docs/INFERENCE.md`.

## M7 — AR-only pronunciation LoRA trained + offline replay · 2026-09-24

- `pron_lora_ar_only_r8` (AR-only, rank 8) trained **6100/6100** (1 epoch) on an A100 — data/CPU
  bound (~0.89 s/step). Offline AR-loss replay over the 180 `val` pairs completed on an L4
  (720 passes, ~23 min; ~450× faster than CPU, int8 `torch._int_mm` confirmed). Docs:
  `docs/PRON_LORA.md`, `docs/PRON_LORA_VERIFICATION.md`; analysis
  `TRAINING_ANALYSIS/pron_lora_ar_only_r8/`.

## M8 — Merge tool, alpha/checkpoint sweeps, LoRA library · 2026-09-24 → 09-26

- `merge_pron_lora.py`: rank concatenation on the AR branch, the `--alpha` dial folded in per
  ai-toolkit's `(alpha/rank)·(B@A)` convention; alpha=0 reproduces v2 byte-for-byte
  (no-regression invariant PASS). α/checkpoint sweeps rendered on an L4 (20/20, then 8/8 fine,
  then an 8/8 request-option knob probe) with blinded listening packages
  (`INFERENCE/prepare_ab_eval.py`, `docs/AB_BLIND_EVAL.md`). LoRA library consolidated to
  `<base>/loras/` (`docs/LORA_INVENTORY.md`); α capped at 0.5, α>0.5 archived.

## M9 — Operability: run-control, backups, session recovery, docs · 2026-09-26

- `AGENTS.md` rewritten as a lean charter; training made **detached** via `train_ctl.py`
  (`start`/`status`/`stop`; SIGINT-reset so a clean stop works). Backup cadence reduced to
  5 minutes. `vm-continuity` installed and a cold-VM restore proof passed (recovered an
  interrupted OpenCode session). Docs reconciled (`RECONCILIATION_LOG.md`); `docs/EXPERIENCE_CHECKLIST.md`
  added.

## M10 — Long-aya Quran LoRA + donor supersede · 2026-09-27

- Full `quran_long_aya_dataset` (81,006 pairs) measured at ~20 h of latency-cache encode on an
  L4 (does not fit a session) → pivoted to a frozen seeded **10% subsample** (8,100 pairs;
  `sample_pron_dataset.py`, `docs/quran_long_aya_s10_manifest.json`). Run
  **`quran_long_aya_r8_s10`** completed **8100/8100** (1 epoch) in 2:46 on an L4; clean loss
  descent (`loss/loss` 6.57→5.26, `ar_ce` 5.50→3.97). Banked: dataset tar + latent-cache tar +
  checkpoints (`docs/PRON_LORA_LONG.md`).
- **Donor superseded:** the `pron_lora_ar_only_r8` family + its 15 `c3050/c4575/cfinal_a0.*`
  merges were archived (`<base>/archive/pron_lora_ar_only_legacy/`), the run prefix renamed
  `pron_lora_ar_only_r8_obsolete/`, and the two `qfinal_a*` merges (v2 style + long-aya Quran
  final, α 0.3/0.5) became the current candidates. Repo + GCS updated in lockstep
  (`DECISIONS.md`).

## M11 — BETA: consolidation onto `main` · 2026-09-27

- `pron-lora-long` consolidated onto `main` (fast-forward; all prior branches contained or kept).
  `README.md` rewritten as the statement of record; `PROGRESS.md` reduced to these milestones.
  Tag **`v0.9.0-beta`** marks the repo's state: v2 style LoRA + long-aya Quran pronunciation
  merges (unselected candidates) + the audio.cpp inference pipeline.

## Open items

- **Pick α/checkpoint** for the production adapter by blinded listening (`qfinal_a0.3` vs
  `qfinal_a0.5`; also the long-aya checkpoints). User's call.
- **Long-aya checkpoints:** evaluate the 6 on a T4 (merge/convert/generate), then decide extend
  vs conclude (`docs/PRON_LORA_LONG.md`).
- **Clean-VM proof** of `bootstrap/setup.sh --inference` + cold timing (warm-VM only so far).
- **Per-arch binary auto-selection** (bootstrap stages only the flat sm_75 object).
- **vm-continuity** Milestone 1 — idle-time only, never GPU-paid.
- See `docs/IMPROVEMENTS.md` for the fuller backlog.
