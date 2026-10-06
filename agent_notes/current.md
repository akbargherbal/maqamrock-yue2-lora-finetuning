# current.md — handoff surface (overwritten each turn; not a source of truth)

## Running now
**`jarir_arnar_probe`** — AR-vs-NAR LoRA scale split, α0.1 (`qahh_a0p1`), canonical prompt,
seed `20261010`, cap 8000. 4 arms, sequential, ~45 min:

| arm | ar scale | nar scale |
|---|---:|---:|
| `ar100_nar100` | 1.0 | 1.0 | control |
| `ar050_nar100` | 0.5 | 1.0 | cut cadence, keep articulation |
| `ar100_nar050` | 1.0 | 0.5 | attribution |
| `ar050_nar050` | 0.5 | 0.5 | halve both |

- driver `/content/arnar_probe.sh` · run dir `out/jarir_arnar_probe/` · log `/content/logs/jarir_arnar_probe.log`
- detached · stop `pkill -f arnar_probe` · resume `bash /content/arnar_probe.sh`
- **If the VM is disconnected mid-run:** finished arms stay valid; the in-progress arm may be a
  partial WAV (re-run to replace). Next session prerequisite: restore the α0.1 adapter to
  `/content/converter/out/qahh_a0p1/` from `<GCS base>/quran_ahh_r8_rank32/maqamrock_merge/`
  (or rebuild: `merge_quran_lora.py --alpha 0.1` then the converter). Repo copy of the driver:
  `INFERENCE/quran_arnar_scale_probe.sh`.

## Just completed — `jarir_prompt_probe` (3 prompts × 2 takes, α0.1, cap 8000)
6/6 exit 0, no truncation, total wall **1:05:51**. Paired seeds p1=`2967871549`, p2=`2671488774`.

| take | canonical | yours | mine |
|---|---:|---:|---:|
| p1 dur_s | 213.7 | 219.6 | 225.2 |
| p2 dur_s | 208.0 | 207.1 | 217.6 |

All 6 WAVs verified on GCS (size-exact) at
`…/audiocpp_inference/out/jarir_prompt_probe/`. Listening verdict: **pending**.

## Backup
Daemon `backup_to_gcp.py --inference` live (pid 13256); mirrors `out/`+`prompts/`+`scripts/`+`logs/`+`agent_notes/`.
Recent runs confirmed on GCS: `jarir_poets_qahh` (4), `jarir_a0p2_hi` (1), `jarir_poets_qahh_rand` (4), `jarir_prompt_probe` (6).

## Open decisions
`results/jarir_qahh/OPEN_DECISIONS.md` — merge-level change (NAR-only / α 0.05, deferred),
winning prompt → re-run split, lyric tags, mood, sampler extras, git push.

## Gotcha logged
`docs/COMMAND_HANDOVER_GOTCHAS.md` — a detached chain aborted on a `pgrep -f` self-match
(the guard message contained the searched word); confirm a detached job started from its log/GPU, not a guard.
