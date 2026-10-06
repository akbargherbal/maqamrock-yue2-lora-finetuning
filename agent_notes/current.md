# current.md — handoff surface (overwritten each turn; not a source of truth)

_Updated 2026-10-06 ~20:20Z — repo now at the new commit (rating app); Colab Tesla T4._

## Run status — `jarir_lever_probe` **STOPPED by request** (resume tomorrow)

User asked to stop after the in-flight track and resume tomorrow. The scale **driver was killed**
(pid 29639) while the current `generate.py` was mid-render, so `qa_1.0_0.5` is finishing and
then the chain halts — no new arm starts. `generate.py` skips succeeded tracks, so a re-run
resumes automatically.

- **Tier 1/3 prompt matrix — 8/8 done** (`out/jarir_lever_probe/prompt/`), all `trunc=no`.
- **Scale/sampler arms — done:** `v2_1.0_1.0`, `qa_1.0_1.0` (reused from smoke), `qa_0.5_1.0`;
  **`qa_1.0_0.5` finishing now** (~12/17).
- **Pending (5):** `qa_0.0_1.0`, `qa_0.5_1.0_rp1.4`, `qa_0.5_1.0_t0.8`, `qa_0.5_1.0_g1.0`,
  `qa_0.5_1.0_notrigger`.
- `_failed.log` empty. No config edits. GPU idle after the current track.

### Resume (tomorrow)
```bash
set -a; . /root/.secrets.env; set +a
cd /content/maqamrock-yue2-lora-finetuning
setsid nohup bash INFERENCE/jarir_lever_probe.sh > /content/logs/jarir_lever_all.log 2>&1 & disown
# prompt tier already done; this runs the remaining scale arms and skips successes.
```
Prereq on a fresh VM: `bootstrap/setup.sh --inference` + restore the α0.1 adapter (see below).

## Eval app — `INFERENCE/rating_app/` (new, general)

General listening **rating** app (single-file Flask), delivered to
`gs://…/OSTRIS_Arabic_Suno_Finetuning/tools/rating_app/` (app.py, README.md, requirements.txt).
- Asks for the track directory (terminal prompt **and** a web `/setup` page) — **no bundled audio**.
- Configurable criteria via the `/criteria` page or a JSON file — not hardcoded to this run.
- Generic discovery: sub-folders become the arms; flat folders work too.

Windows run:
```powershell
py -m pip install -r requirements.txt
py app.py            # paste e.g. C:\Users\DELL\Downloads\jarir_lever_probe
# open http://127.0.0.1:5000
```

## Environment / sidecars (verified this session)
- secrets loaded (`GCP_BACKUP_BASE=gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning`)
- α0.1 adapter at `/content/converter/out/qahh_a0p1/`; `ar` sha256
  `4b4d2103e59de6b3279088d53cb28b15df901f96e4a37a67e2306e9bfdac0ecb` ✓
- backup daemon `backup_to_gcp.py --inference` live · vm-continuity watch live
- supervisor `/content/run_lever_supervisor.sh` did its job (validated smoke, launched chain);
  it will run a final `backup --once` + write `/content/logs/_supervisor_summary.txt` when the
  last track drains.
- To fully stop now: `pkill -f jarir_lever_probe`.
