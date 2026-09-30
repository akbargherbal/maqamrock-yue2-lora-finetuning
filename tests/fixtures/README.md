# e2e fixtures

Fixtures for the GPU-free e2e tiers in `docs/E2E_TESTING_PLAN.md` (§4). Two tiers:

- **Tier A — tracked, small, verbatim.** `recorded_batch.json` plus text sidecars /
  `.log` / `_time.txt`. Cheap enough for git; most tests read only these.
- **Tier B — heavy, GCS-backed, gitignored.** Real `.wav`, `.safetensors`,
  `loss_log.db`, the sm75 binary, full `out/` dirs. Declared under `tier_b` in
  `manifest.json` and fetched with `bash tests/fixtures/fetch.sh`. Tests that need
  them carry the `fixtures_heavy` marker and skip when absent.

## `recorded_batch.json` (schema 1)

```
{
  "schema": 1,
  "provenance": { "gpu", "compute_cap", "audio_cpp_commit", "checkpoint_step", ... },
  "tracks": [
    { "name", "seed", "take", "cap", "duration_s", "exit", "log_text" }
  ]
}
```

`tests/e2e/replay.py::make_replay_runner` keys tracks by `(name, seed)`, then — in
place of `INFERENCE/run_one.sh` — writes the per-track files the real runner
writes: a WAV rebuilt from `duration_s` with stdlib `wave`, `<name>_<seed>.log`,
`<name>_<seed>_time.txt` (`Exit status: <exit>`), `<name>_<seed>_gpu.csv`, and
`_runs_status.log`. Set `duration_s: null` for a failed run that produced no audio.
The per-track sidecar `<name>_<seed>.json` is written by `generate.py`, so replay
must not touch it.

Audio bytes are never asserted (not stable across GPU/arch/driver — plan §4.2).
Recorded `wav_sha256` is provenance metadata only.

## Provenance guard

`manifest.json` records the `audio_cpp_commit` and `checkpoint_step` of the run
that produced these fixtures. A guard test (plan §4.4) fails loudly when they no
longer match what the code computes today, so a stale fixture cannot silently keep
testing an old contract. Regenerate via `fetch.sh`, or re-record at the T5 gate.
