# Milestones

Durable, cross-session record of **what has actually been run and what it produced** — outcomes,
not narrative. One block per milestone. *Why* things are the way they are lives in
`DECISIONS.md`; per-session state lives in `agent_notes/current.md`; the full chronological
narrative lives in git — pre-rewrite history at `git show 39d1bbd:PROGRESS.md` (and `git log`).

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

## M12 — Quran pron LoRA **alone** (α=1) on the base model · 2026-10-04

- **First "pron-only" arm rendered** (branch `experimental-quran-pron`): the first song of
  `manifests/batch_36_songs.json` with its style replaced by the unaccompanied-recitation
  caption, Quran adapter alone (AR 1.0, NAR off), seed `20261004`. **exit 0**, 52.2 s WAV.
- **Finding: it self-terminates after ~one aya** (1304 semantic tokens; cap 7500,
  `truncated 0`). The adapter is AR-only and its training clips were single long-ayat
  recitations (~23 s avg), so it recites one passage and emits EOS. See
  `docs/QURAN_ONLY_EXPERIMENT.md`.
- **Consequence for tooling:** the audio.cpp converter needs both branches (AR-only input
  fails), and the raw pron file *is* α=1 (trained alpha==rank), so this arm needs no merge —
  `build_pron_only_fused.py` + the converter (see `DECISIONS.md`).

## M13 — `jarir_lever_probe` rendered + rated; donor merge unproven · 2026-10-07

- Rendered **17 WAVs** (9 scale arms + 8 prompt-tier tracks) on one fixed song, seed `20261011`,
  via `INFERENCE/jarir_lever_probe.sh` + `songs.jarir_lever_probe.json`; all exit 0, none
  truncated, mirrored to GCS. Adapter under test: `qahh_a0p1` (α0.1 `quran_ahh_r32` rank32 merge
  into v2); the v2-only arm is the **no-donor ceiling reference**.
- Labeled listening (single rater, `rating_app`) →
  `INFERENCE/rating_app/my_evaluations/rating_20261007-1100.md`.
- **Outcome:** the leading hypothesis — cut merged-AR to 0.5, keep NAR — is **refuted**. Cutting
  AR hurts (`qa_0.5_1.0` 3, `qa_0.0_1.0` 2/broken); cutting NAR doesn't (`qa_1.0_0.5` 4) → the
  merged-AR expert is the load-bearing one. Best arm is **v2-only (5, no Quran donor)**; every
  sampler knob (`rp1.4`/`t0.8`/`g1.0`/`notrigger`) ≤ 3. Prompt keepers: `p1_verbatim_v2`,
  `p2_articulation_qahh` (4, keep). n=1 track/arm → qualitative.
- **Diction:** the donor shows **no demonstrated benefit** and a hint of harm — diction saturated
  at 5 on nearly all arms, and "tajweed bleed" (أعددت→الشعياء, شربك→شلبك) appears specifically on
  the donor (`qahh`) arms; the paired `p1_verbatim_qahh` vs `p1_verbatim_v2` came out cleaner on
  v2. The donor's actual job (hard phonemes: ع/ش/emphatics) was **not isolated** by this rubric.
- **Bottleneck is mood/energy** ("chill / not rising to the occasion"), not intelligibility —
  recurring across the scale arms including the top take.

## M14 — Evaluation tooling moved to the external rating app · 2026-10-07

- Listening/rating now runs in **`github.com/akbargherbal/ai_music_rating_app`** (Flask;
  scorecard library, per-run frozen scorecard, `--blind`, multi-metric report). The in-repo
  single-file `INFERENCE/rating_app/` (which produced M13's report) is **superseded** — kept
  for history. Runbook + the one-line launch command: [`docs/LISTENING_EVAL.md`](docs/LISTENING_EVAL.md)
  (skill `listening-eval`).
- First evaluation under it: the **D-test** (`INFERENCE/songs.dtest.json`; 5 arms × 4 seeds =
  20 takes, seeds `20261021`–`20261024`, cap 8000) rendered on a T4 via
  `INFERENCE/jarir_lever_probe.sh`, scorecard `INFERENCE/scorecards/dtest_diction.json`.
  **Listening verdict pending.**

## Open items

- **D-test render + listening (in progress, 2026-10-07).** 20 takes (v2 vs `qahh_a0p1` on an
  AR/NAR scale grid) rendered via `INFERENCE/jarir_lever_probe.sh` + `INFERENCE/songs.dtest.json`;
  score with [`docs/LISTENING_EVAL.md`](docs/LISTENING_EVAL.md). Verdict pending.

- **Donor value in the production merge is unproven (M13).** The α0.1 Quran donor showed no
  demonstrated diction benefit (and a tajweed-bleed hint of harm) while v2-only topped the probe.
  Decide: run a powered donor-vs-no-donor diction test, or drop the donor.

- **Quran-only (α=1) listening + comparison arms.** The first sample is rendered; listen, then
  run base / quran-AR+v2-NAR at the same seed for a blind A/B (`docs/QURAN_ONLY_EXPERIMENT.md`).

- **Pick α for the current donor** `quran_ahh_r32`. Blinded listening over `qahh_a0` / `a0p1` /
  `a0p2` / `a0p3`. User's call. (The long-aya `qfinal_a*` and its checkpoints are moot — that
  donor was retired 2026-10-07 → `docs/LORA_INVENTORY.md`.)
- **Clean-VM proof** of `bootstrap/setup.sh --inference` + cold timing (warm-VM only so far).
- **Per-arch binary auto-selection** (bootstrap stages only the flat sm_75 object).
- **vm-continuity** Milestone 1 — idle-time only, never GPU-paid.
- See `docs/IMPROVEMENTS.md` for the fuller backlog.
