# current

_Updated 2026-09-30 (L4 GPU VM). **E2E Session 4 — the T5 GPU gate — is COMPLETE.**
Ran on an NVIDIA L4 (sm_89), not a T4 (L4 is deliberate; the plan's T4 rows were
stale and are now corrected). S1–S3 passed; the recording is folded into
`tests/fixtures`; `python -m pytest` -> **191 passed, 1 skipped**. Committed and
pushed as **`e953044`** on `origin/music-cover`._

## 0. What happened this session

- **Staged** the inference workspace (`bootstrap/setup.sh --inference`, 41 s) and
  swapped in the **sm89-l4** `audiocpp_cli` (`sha256 97028a71…`, matching the
  fixture's recorded `binary_sha256`; sm75 kept as `bin/audiocpp_cli.sm75`).
- **S1** `audiocpp_cli --version` -> exit 0, `backends: cpu,cuda`.
- **S2** real `run_one.sh Hijaz 1 auto` -> exit 0; 277.16 s, 48 kHz stereo,
  `truncated 0`; wall 5:20.89.
- **S3** `pron_lora_ar_only_smoke` (10 steps) -> 10/10, finite loss (final
  `loss/loss` 6.765791), checkpoint + optimizer at
  `/content/ai-toolkit/output/pron_lora_ar_only_smoke/`.
- Sidecars up: `backup_to_gcp.py --inference --extra /content/smoke`, `gpu_logger.py`.

## 1. The fold (uncommitted)

- `tests/fixtures/manifest.json`: `tier_b` populated (`inference/Hijaz_1.wav`,
  `inference/audiocpp_cli` = sm89-l4, `training/loss_log.db`); Tier A gained the
  real `inference/{Hijaz_1.log,Hijaz_1_time.txt,Hijaz_1_gpu.csv,_runs_status.log}`
  and `training/train_smoke.log`.
- `recorded_batch.json` + `manifest.json` provenance re-recorded to the gate:
  `audio_cpp_commit 30ec4596`, `checkpoint_step 3000`, L4 / 8.9, 2026-09-30.
- Tier B uploaded to GCS `…/fixtures/inference/Hijaz_1.wav` +
  `…/fixtures/training/train_smoke_loss_log.db`; the binary is referenced in place
  at `…/audiocpp_inference/tools/build/sm89-l4/audiocpp_cli`.
- **Production change** `bootstrap/setup.sh::job_audio_cpp`: pins
  `/content/audio.cpp` to `manifest.provenance.audio_cpp_commit` so the provenance
  guard is deterministic on a fresh VM (validated: `bash -n` ok, pin -> `30ec4596`).
- Docs reconciled (`docs/E2E_TESTING_PLAN.md` complete + T4->L4, fixtures README,
  `SOURCE_OF_TRUTH.md`, `RECONCILIATION_LOG.md`; reconciler 0 flagged).

## 2. Next action

1. Optional: on a **CPU runtime**, re-run `python -m pytest` to confirm the suite
   stays green with the pin in place (setup re-clones audio.cpp at the pinned commit).
2. Nothing else outstanding — Session 4 (and the E2E plan) is done.

## 3. Open item (unfixed)

`AGENTS.md` §2's "build the inference binary" row names `docs/models/yue2.md` as
authority, but that file lives in the upstream `audio.cpp` repo, not here.

## 4. Ground truth reminders

- One GPU, shared, rented — `nvidia-smi` before any GPU work (idle now).
- Tier B binaries/audio stay out of git (`tests/fixtures/**/*.wav|.safetensors|.db`,
  `**/audiocpp_cli`).
- This file is a handoff surface, not authority — re-derive with `python status.py`.
