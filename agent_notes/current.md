# current.md — handoff surface (overwritten each turn; not a source of truth)

_Updated 2026-10-06 18:16Z — repo `ca10723`, branch `pron-lora-long-aya`, Colab Tesla T4._

## Running now — `jarir_lever_probe` (Jarir lever experiment, α0.1 `qahh_a0p1`)

Prepared by a CPU agent; run autonomously. One GPU job at a time.

**Stage 1 — smoke gate (in progress):** `ARMS="qa_1.0_1.0" bash INFERENCE/jarir_lever_probe.sh`
- log `/content/logs/jarir_lever_smoke.log` · out `out/jarir_lever_probe/qa_1.0_1.0/`
- started 2026-10-06T18:13:09Z, ~6 min expected on T4.

**Stage 2 — both batches sequentially (AUTO-launched by supervisor on smoke pass):**
Supervisor `/content/run_lever_supervisor.sh` (setsid, pid 17615) waits for the smoke,
validates a WAV + no `_failed.log` entry, then launches the chain below, waits for it to
drain, runs `backup_to_gcp.py --inference --once`, and writes `/content/logs/_supervisor_summary.txt`.
If the smoke fails it writes evidence to that file and stops (no chain). Chain:
```
setsid nohup bash -c 'MODE=prompt bash INFERENCE/jarir_lever_probe.sh && bash INFERENCE/jarir_lever_probe.sh' \
  > /content/logs/jarir_lever_all.log 2>&1 & disown
```
- `MODE=prompt` = Tier 1/3 matrix, `INFERENCE/songs.jarir_lever_probe.json` → 8 tracks (`out/jarir_lever_probe/prompt`)
- default = 9 scale/sampler arms, 1 track each (`out/jarir_lever_probe/<arm>`)
- ~17 tracks; ~50 min L4 / ~110 min T4.
- stop `pkill -f jarir_lever_probe` · resume = re-run same chain (generate.py skips succeeded tracks)

## Environment (verified this session)
- secrets `/root/.secrets.env` loaded (HF_TOKEN, `GCP_BACKUP_BASE=gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning`)
- `bootstrap/setup.sh --inference` done 97s; `bin/audiocpp_cli` staged (sm_75/T4)
- α0.1 adapter restored to `/content/converter/out/qahh_a0p1/`; `ar` sha256 `4b4d2103e59de6b3279088d53cb28b15df901f96e4a37a67e2306e9bfdac0ecb` ✓
- dry-run: 8 songs, seed `20261011`, cap 8000 ✓

## Sidecars
- backup daemon `python backup_to_gcp.py --inference` (pid 12015) · log `/content/logs/backup_inference.log`
- vm-continuity watch (pid 7493)

## Notes
- No config edits, no commits. Training not started. GPU idle before launch.
- Smoke-watcher tracked in OpenCode background; report on completion.
