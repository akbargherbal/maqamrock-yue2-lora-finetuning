# End-to-end testing plan — Colab, GPU-light

_Status: **in progress.** Sessions 1–3 landed 2026-09-30 (T2 scaffold + J1; then
J2–J4/J6 + the provenance guard; then T3 J10–J12). Only the budgeted T5 GPU gate
remains; decisions in §12 resolved. Last revised 2026-09-30._

Goal: exercise the real user journeys end to end — as faithfully as possible —
**without renting a GPU** for the bulk of it. A GPU is allowed exactly once or
twice, as a *budgeted smoke gate* that also doubles as the recording run.

The execution environment for everything except the smoke gate is a **Colab CPU
runtime**. That is the closest free thing to the real target: it has `/content`,
the same filesystem layout, the same Python, the same repo and GCS — it is a
Colab GPU runtime with the device removed.

Authority: this doc (see `SOURCE_OF_TRUTH.md`). Ground truth while running stays
`status.py` / the artifact files (AGENTS.md §4).

---

## 1. The idea in one paragraph

A GPU is needed for exactly two things: (a) probing the device, (b) executing
CUDA kernels. Everything else — planning, validation, prompt materialization,
subprocess orchestration, sidecar writes, exit-code handling, skip/retry,
summary, PID/detach/SIGINT lifecycle, loss-log parsing, backup mirroring — is
ordinary CPU code. So the professional move is not to emulate the GPU: it is to
**cut the system at the device boundary, substitute only the two device
touchpoints, and replay recorded real artifacts through the rest of the real
pipeline.** Kernels are then confirmed once, cheaply, by a real smoke.

The corollary that makes this affordable: **the recording run is the smoke
run.** One budgeted T4 session produces both the proof that the binary runs and
the golden fixtures that let every later e2e run cost $0.

## 2. The device boundary (where to cut — verified in source)

The entire GPU surface is small and already isolated:

| Touchpoint | Where | Substitute |
|---|---|---|
| GPU probe | `INFERENCE/generate.py:520` `gpu_info()` (shells `nvidia-smi`) | return a recorded `{"name","memory_used","memory_total","compute_cap"}` |
| VRAM wait | `INFERENCE/generate.py:718` `wait_vram_free()` | no-op (already done by `tests/conftest.py:68`) |
| training guard | `INFERENCE/generate.py:503` `training_active()` | `None` (or a fake `/proc` entry) |
| generation compute | `INFERENCE/run_one.sh` invoked via `runner=` (`generate.py:660,780`) | `replay_runner` (writes recorded per-track files) |
| training compute | ai-toolkit `run.py` launched by `train_ctl.py:144` | a staging `fake_run.py` (real process, fake loss) |
| GPU logger | `gpu_logger.py` (`nvidia-smi` poll) | recorded `gpu_usage.csv` |

Everything else runs unmodified. Note `asset_fingerprint` (`generate.py:547`)
and `duration_cap.py` are pure CPU; hashing and cap math are exercised for free.

## 3. Tiers

| Tier | GPU | Proves | Where it runs | Status |
|---|---|---|---|---|
| **T0** unit/logic | no | parsing, planning, validation, cap parity | localhost + Colab CPU | **done** — `tests/test_*.py` |
| **T1** contract/fake | no | orchestration ↔ subprocess wiring | localhost + Colab CPU | **done** — `runner=`, monkeypatched probes |
| **T2** record→replay e2e | no | the *whole pipeline* on real recorded artifacts | Colab CPU | **done** — J1–J4, J6 (Sessions 1–2) |
| **T3** process/lifecycle e2e | no | real detach, PID, SIGINT stop, backup mirror | Colab CPU | **done** — J10–J12 (Session 3) |
| **T4** hosted-env e2e | no | the real Colab paths/env, minus the device | Colab CPU | **to run** |
| **T5** kernel smoke | **yes** | the binary/kernels actually run | Colab GPU *or* Kaggle T4 | **budgeted** |

The whole plan is: grow T2/T3, make T4 a real step, shrink T5 to ~1 session.

## 4. Record → replay (the core mechanism)

### 4.1 The recorded contract

`run_one.sh` + `generate.py` already define a strict per-track file set
(`run_one.sh:33-40`, `generate.py:789-832`):

```
<name>_<seed>.wav          audio
<name>_<seed>.log          CLI --log (contains `truncated=<0|1>` if it fired)
<name>_<seed>_time.txt     /usr/bin/time -v  ("Exit status: N")
<name>_<seed>_gpu.csv      1 Hz nvidia-smi (header + rows)
<name>_<seed>.json         sidecar — written by generate.py, NOT run_one.sh
_runs_status.log           START/END per run
```

Plus, per run: `prompts/`, `input.json`, `batch_manifest.json`, `_driver.log`,
`_failed_runs.log`, and `batch_summary.txt` (written by `main`).
The replay runner reproduces only the four files `run_one.sh` writes; the sidecar
is written by the code under test, so replay must **not** touch it.

### 4.2 Fixture tiers (size discipline)

- **Tier A — tracked, small, verbatim.** Sidecars, `.log`, `_time.txt`, and a
  compact `recorded_batch.json` (per-track: name, seed, cap, `duration_s`,
  `exit`, `log_text`). Text only. This is what most tests read.
- **Tier B — heavy, GCS-backed, gitignored.** Real `.wav`, `.safetensors`,
  `loss_log.db`, the sm75 binary, full `out/` dirs. Fetched by hash via
  `tests/fixtures/fetch.sh`; tests needing them carry the `fixtures_heavy` mark
  and skip when absent. Keeps the repo small.
- **Synthesized where cheap.** A valid WAV is built from the recorded
  `duration_s` with stdlib `wave` (the pattern already exists at
  `tests/test_generate.py:440`). A `loss_log.db` is built from a small
  `loss_log.spec.json` against the real schema.

**Do not golden the audio.** Generated WAV bytes are not stable across GPU,
arch, driver, or attention-kernel choice (the repo itself records T4-specific
attention behavior). Fixtures assert *structure* — file exists, valid WAV
header, duration within tolerance, sidecar keys, status transitions, exit codes,
summary lines — never `wav_sha256 == <recorded>`. The recorded hash is
**provenance metadata**, not an assertion.

### 4.3 Replay runner (sketch)

```python
# tests/e2e/replay.py
import json, wave
from pathlib import Path

def make_replay_runner(recorded_batch: Path):
    spec = json.loads(recorded_batch.read_text(encoding="utf-8"))
    by_key = {(t["name"], str(t["seed"])): t for t in spec["tracks"]}

    def runner(cmd, env, log_fh):            # matches subprocess_runner's signature
        name, seed = cmd[2], cmd[3]
        t = by_key[(name, seed)]
        out = Path(env["OUT_DIR"]); out.mkdir(parents=True, exist_ok=True)
        _synth_wav(out / f"{name}_{seed}.wav", t["duration_s"])
        (out / f"{name}_{seed}_time.txt").write_text(f"\tExit status: {t['exit']}\n")
        (out / f"{name}_{seed}.log").write_text(t.get("log_text", ""))
        (out / f"{name}_{seed}_gpu.csv").write_text("gpu_util_pct,mem_used_mib,power_draw_w,temp_c\n")
        return t["exit"]
    return runner
```

### 4.4 Provenance

Every fixture set carries a `tests/fixtures/manifest.json` recording: source GCS
path, per-fixture `sha256`, the recorded run's `batch_manifest.json` `assets`
block (LoRA/GGUF shas, `audio_cpp_commit`, `checkpoint_step`), the GPU name, and
the date. A guard test (`tests/e2e/test_inference_e2e.py::test_provenance_guard`)
fails loudly when a fixture's `checkpoint_step` no longer matches the code
constant, catching "fixture rot" instead of silently testing a stale contract.

The `audio_cpp_commit` half only becomes checkable once the **Tier B binary** is
recorded (the T5 gate): on the CPU tier `/content/audio.cpp` is an arbitrary
current clone, so a strict equality there would be a false failure. Until
`manifest.json` has a non-empty `tier_b`, that half skips with a named reason;
the `checkpoint_step` check and the manifest/`recorded_batch.json` agreement
always run.

## 5. Test matrix (journeys × tier)

`▲` = already covered at T0/T1; `＋` = net-new e2e work.

| # | Journey | Entry point | Assertions | Tier |
|---|---|---|---|---|
| J1 | Inference happy path: multi-song, repeats, seeds → run dir | `generate.main` with fake GPU + replay runner | prompts, `batch_manifest.json`, sidecars' provenance, summary, `out/latest` | ＋ T2 |
| J2 | Idempotent re-run skips; `--force` redoes | same run dir twice | `skipped`, no re-invoke, force path | ＋ T2 |
| J3 | Partial failure → `_failed_runs.log` → retry recovers | replay one `exit=1` then `exit=0` | continue-on-fail, failed log, later skip | ＋ T2 |
| J4 | Per-song LoRA registry routing + provenance | `loras:` registry | per-track `lora_alias`, ar/nar shas on the sidecar | ▲＋ T2 |
| J5 | Duration-cap parity across a real batch | `duration_cap.py` vs in-code | `cap == CLI cap` (already parametrized) | ▲ T0 |
| J6 | `suno_to_songs.py` → `generate.py` round trip | both mains | manifest → songs json → batch plan | ▲＋ T2 |
| J7 | Offline AR-loss record/replay | `offline_ar_loss_replay.py` | checkpoint map, val pairing, mean losses | ▲ T1 |
| J8 | v2+pron merge + metadata round trip | `merge_pron_lora.py` | alpha semantics, tensor digests | ▲ T0 |
| J9 | Blind A/B packaging from a rendered tree | `prepare_ab_eval.py` | labels, KEYS, reproducibility | ▲ T0 |
| J10 | Training lifecycle: start→status→**SIGINT** stop | `train_ctl.py` + `fake_run.py` | detached, PID file, SIGINT reaches child, "Job stopped" | ＋ T3 |
| J11 | Monitor + status on a recorded run | `monitor_loss.py`, `status.py` | step/rate, drift, staleness | ▲＋ T3 |
| J12 | Backup mirror + manifest + restore diff | `backup_to_gcp.py` + fake `gsutil` | targets, manifest, byte-identical restore | ▲ T3 |
| J13 | Kernel smoke | real `audiocpp_cli`, real `run.py` | binary runs, 1 WAV, 10-step loss finite | ＋ T5 |

Most of J4–J12 already exist as isolated T0/T1 tests (see the test-function
inventory). The net-new value of T2/T3 is the **cross-module, process-level,
real-artifact** layer, which is exactly where integration bugs live.

### 5.1 The strongest single test

One test drives `generate.main()` through **real** `preflight`, `asset_fingerprint`,
`materialize`, `run_batch`, `render_summary`, and `out/latest` — with only two
substitutions: `gpu_info` (device probe) and the `runner` (device compute). It
reuses the workspace staging shared by the unit tests via `tests/staging.py`
(`stage_inference_tree`, used by both `tests/test_generate.py::_stub_assets` and
the e2e `staged_inference` fixture). That is the whole inference product,
GPU-free, with a real subprocess contract.

## 6. The GPU smoke gate (T5) — allowed, budgeted

One session, ~30–60 min on a T4. It records the fixtures **and** proves the
kernels. Exact, minimal steps once a GPU runtime is attached:

| Step | Command shape | Proves | Cost |
|---|---|---|---|
| S1 | `audiocpp_cli --version` | binary loads, CUDA device present | seconds |
| S2 | `bash INFERENCE/run_one.sh <Maqam> 1 auto` with `OUT_DIR /content/smoke` | one real WAV, real `_time.txt`/`.log`/`_gpu.csv` → **becomes the J1–J3 fixtures** | ~minutes |
| S3 | `python run.py config/pron_lora_ar_only_smoke.yml -l /content/logs/train_smoke.log` | 10/10 steps, finite loss, checkpoint written (precedent: `PRON_LORA_VERIFICATION.md` smoke) | ~minutes |

After S1–S3: copy the smoke artifacts to `tests/fixtures/` Tier A/B, then switch
back to the CPU runtime. Optionally record one failure path (S2b) by pointing at
a missing LoRA to capture a real `exit=1` log.

Gate host (decided 2026-09-30): **Colab free T4**. Alternatives considered:
**Kaggle** (~30 GPU-h/week free T4×2; most repeatable), **GitHub Actions GPU**
(paid per minute; gate on `workflow_dispatch`, never per-PR). All write to the
same GCS bucket, so no state is trapped in the ephemeral VM.

## 7. Running on the Colab CPU runtime (T4 tier)

The CPU runtime is the faithful host for T2/T3: `/content` exists, `nvidia-smi`
does not. That absence is itself a test — `preflight` must fail with exactly the
documented message (`generate.py:603`), not crash. `torch.cuda` is unavailable, so
the training-lifecycle test must use `fake_run.py`, never real ai-toolkit (the
"no NVIDIA driver at import" gotcha is already recorded in
`PRON_LORA_VERIFICATION.md` A3b).

Bring-up (once per fresh CPU VM):

```bash
# notebook cell exports HF_TOKEN + GCP_* into /root/.secrets.env first
git clone <repo> /content/maqamrock-yue2-lora-finetuning
cd /content/maqamrock-yue2-lora-finetuning
bash bootstrap/setup.sh --inference    # stages GGUF/LoRA/prompts; skips ai-toolkit torch
python -m pytest -q                    # the whole GPU-free suite
```

Note the deliberate asymmetry: `--training` installs torch/cu130 and can pull the
multi-GB dataset; the CPU e2e does **not** need it. Use `--inference` on the CPU
VM and fetch only the tiny text fixtures from git.

## 8. Test-suite wiring (proposals, each small)

```
pytest.ini   markers = gpu: needs a real CUDA device
                      fixtures_heavy: needs Tier B fixtures fetched
                      live: touches network/GCS (never in the default run)
             addopts = -q -m "not gpu and not fixtures_heavy and not live"

tests/staging.py         # stage_inference_tree — shared by unit + e2e tests
tests/e2e/
  conftest.py            # replay_runner, fake_gpu, staged assets, fake gsutil, lossdb
  replay.py              # write_track_outputs, make_replay_runner, passthrough runner
  lossdb.py              # build a real loss_log.db from a spec
  fake_run.py            # a run.py that writes a loss_log.db and answers SIGINT
  fake_gsutil.py         # local gs:// mapper placed on PATH for J12
  test_inference_e2e.py  # J1–J4, J6 + the provenance guard
  test_train_lifecycle_e2e.py   # J10
  test_monitor_status_e2e.py    # J11
  test_backup_restore_e2e.py    # J12
tests/fixtures/
  README.md  manifest.json  fetch.sh  recorded_batch.json  loss_log.spec.json
  inference/  training/  gpu/   (Tier B, GCS-backed)
```

The default `pytest` must stay green and GPU-free on the CPU runtime; `pytest -m
gpu` lists the T5 checks that are deferred to the gate; `pytest -m live` is never
run automatically.

## 9. Sequencing (4 sessions)

| Session | Deliverable | Exit criterion |
|---|---|---|
| **1** | `tests/e2e/` scaffold, `replay.py`, `recorded_batch.json` schema, markers, `fake_gpu`. Fixtures harvested from **existing** GCS artifacts first (sidecars/`results/` already exist) — no GPU yet. | J1 passes on Colab CPU with a hand-authored fixture — **done 2026-09-30** (181 passed, 1 skipped) |
| **2** | T2 inference journeys J1–J4, J6; provenance guard test; `test_generate.py`'s `_stub_assets` reused. | `pytest -m "not gpu"` green; J3 failure/retry covered — **done 2026-09-30** (185 passed, 2 skipped; scaffolding shared via `tests/staging.py`) |
| **3** | T3 lifecycle/monitor/backup J10–J12 with `fake_run.py` and a fake `gsutil`; J11 from a spec-built db. | start→stop SIGINT proven with a real process; restore diff clean — **done 2026-09-30** (190 passed, 2 skipped; surfaced + fixed a `train_ctl.py stop` log/exit race) |
| **4** | T5 gate: one budgeted GPU session (S1–S3) → record fixtures → fold them into Tier A/B. | S1–S3 evidence (exit 0, WAV duration, finite loss); fixtures committed with provenance |

## 10. What this does *not* prove (be explicit)

- **Kernel numerical correctness, throughput, and real VRAM.** Only S1–S3 do,
  and only at n=1. A replay can never validate a CUDA kernel.
- **Cross-arch behavior.** The sm75 binary is not the sm89 one
  (`audiocpp_gpu_arch_builds.md:106-114`). A T4 smoke says nothing about L4/A100.
- **Bit-stability of audio.** Deliberately not asserted (see §4.2).

## 11. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Fixtures drift from code/assets | `manifest.json` + provenance guard test (§4.4); regenerate via `fetch.sh` |
| Colab CPU VM resets and loses work | fixtures + tests live in git; heavy ones in GCS; nothing durable in `/content` |
| Over-fitting to fixtures (tautology) | assert *structural* contract; keep T0 unit tests as the independent oracle |
| Tests accidentally need GPU | `-m "not gpu"` default; a `gpu_info` stub that returns `None` on the CPU VM fails any test that forgot to fake it |
| Network/GCS in unit tests | `live` mark; fake `gsutil`/`gcloud` shim on `PATH` for T3 |
| A fixture recorded on the wrong build | provenance records `audio_cpp_commit` + `checkpoint_step`; mismatch fails |

## 12. Decisions (resolved 2026-09-30)

1. **Gate host**: **Colab free T4** (see §6). Kaggle and GH Actions GPU remain
   alternatives if Colab's session/idle limits bite.
2. **Fixture home**: **Tier A in git, Tier B in GCS** (as proposed in §4.2). Heavy
   fixtures fetched by `tests/fixtures/fetch.sh` and gitignored.
3. **Scope of T3**: **fake `run.py` only** for the training-lifecycle e2e; the
   real 10-step smoke stays at the T5 gate (§6 S3), not every cycle.
