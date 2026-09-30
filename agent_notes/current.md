# current

_Copy surface, not authority. Session end · 2026-09-30 · **T4 Colab**, branch `music-cover`._

## Where things stand

- **B2 smoke passed** — `exit=0`, wall 278.4 s, 2ch/48 kHz, 192.9 s. Awaiting your listen:
  - rescue: `/content/rescue_v2abc_batch12_winning/07-الحر-الشديد-وقطع-القفر-والوعول_rock_3781160148.wav`
  - pass-1 (same stem/seed, to compare): `/content/batch_12_rock_v2_winning/07-الحر-الشديد-وقطع-القفر-والوعول_rock_3781160148.wav`
- **Generation resumes tomorrow.** GPU idle (`Tesla T4, 0 MiB, 0%`); nothing running.
- The earlier blocker is fixed: the pass-1 dir + adapters + binary + models were missing on this VM and were
  staged from GCS/HF (logs `/content/logs/{rescue_stage,inference_stage}.log`).

## Tomorrow — 1) listen, 2) full batch

**1. Listen.** A/B the two WAVs. Gate: does the SheetSage2 melody steer the arrangement while `qfinal_a0.3`
keeps the pronunciation? Yes → go to 2. No → stop; B2 is unproven (fallback B1: `INFERENCE/v2_abc_to_qfinal.sh`).

**2. Full batch.**
terminal: detached — survives Ctrl+C / closing the tab; log: `/content/logs/rescue_winning.log`
(+ per-track `/content/rescue_v2abc_batch12_winning/<stem>.log`, `_rescue_status.log`);
stop: `pkill -f 'rescue_abc_batch.sh'`; resume: the same command (skips succeeded takes).

```bash
cd /content/maqamrock-yue2-lora-finetuning
setsid nohup bash INFERENCE/rescue_abc_batch.sh --songs-json INFERENCE/rescue_selection.batch_12_rock_v2_winning.json \
  > /content/logs/rescue_winning.log 2>&1 & disown
```

- Rescues **all 24** takes (JSON has no `songs` key). The smoke track is skipped automatically
  (`_time.txt` = `Exit status: 0`); `--force` redoes it. ~4.6 min/take ⇒ ~1 h 50 m for the remaining 23.
- To rescue only winners: add a `songs` list — a bare `<name>` = every take of that song, a full
  `<name>_<seed>` stem = exactly one.

**3. Then** Phase 5 of `docs/PRON_LORA_RESCUE.md`: blind-package rescue vs pass-1 with
`INFERENCE/prepare_ab_eval.py` (skill `ab-blind-eval`).

## GitHub

- Committed this session: refreshed `agent_notes/current.md` + two `docs/COMMAND_HANDOVER_GOTCHAS.md` entries.
- Push requires auth on this VM: `bash bootstrap/github_auth.sh` (paste a PAT at the hidden prompt), then
  `git push origin music-cover`.

## Backup / continuity — NOT current

- Sidecars are down: `backup_to_gcp.py`, `gpu_logger.py`, `vm-continuity`.
- Already on GCS (from earlier): the pass-1 24 WAVs + 24 ABCs. **Not** on GCS: today's rescue output and the
  local `/content/batch_12_rock_v2_winning` — `backup_to_gcp.py --inference` does not cover the flat `/content/…` dirs. One-shot:
  ```bash
  python backup_to_gcp.py --inference --once \
    --extra /content/batch_12_rock_v2_winning:workspace/out/batch_12_rock_v2_winning \
    --extra /content/rescue_v2abc_batch12_winning:workspace/out/rescue_v2abc_batch12_winning
  ```

## Watch-outs

- Flat `/content/…` layout is not covered by the backup daemon (above).
- The selection JSON's `_comment` still documents `/content/audiocpp_inference/out/…` while its keys are flat `/content/…` (stale comment; keys win).
- `/usr/bin/time` absent → `_time.txt` holds only `Exit status: 0`.
- `/root/.secrets.env` values are empty; the real `HF_TOKEN` / `GCP_BACKUP_BASE` are in the environment.
- `AGENTS.md` §12: the `docs-reconciler` pass for the new gotcha entries is still pending.
