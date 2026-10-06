# current.md — handoff surface (overwritten each turn; not a source of truth)

## ⏸ WHERE WE STOPPED — resume here tomorrow (2026-10-07)

_Run `jarir_lever_probe`. Recorded 2026-10-06 ~20:20Z, Colab Tesla T4._

**Why it stopped:** the user asked to stop after the in-flight track. The scale-tier **driver
was killed** (pid 29639) while `qa_1.0_0.5` was rendering, so that one track finishes and the
chain halts — **no new arm will start**. Nothing else was touched (no config edits, no training).

**Exactly where:**
- Prompt tier (8 tracks) → `out/jarir_lever_probe/prompt/` — **8/8 done**, all `trunc=no`.
- Scale arms done → `v2_1.0_1.0`, `qa_1.0_1.0` (reused from the smoke), `qa_0.5_1.0`.
- **Last in-flight track:** `qa_1.0_0.5` (`out/jarir_lever_probe/qa_1.0_0.5/`) — it finishes on
  its own; treat it as done if its WAV exists, otherwise it will be redone.
- **Still pending (5 arms):** `qa_0.0_1.0`, `qa_0.5_1.0_rp1.4`, `qa_0.5_1.0_t0.8`,
  `qa_0.5_1.0_g1.0`, `qa_0.5_1.0_notrigger`.
- `out/jarir_lever_probe/_failed.log` is **empty**.
- The supervisor (`/content/run_lever_supervisor.sh`) is still alive and, when the last track
  drains, will run `backup_to_gcp.py --inference --once` and write
  `/content/logs/_supervisor_summary.txt`.

### Resume tomorrow (one command)
```bash
set -a; . /root/.secrets.env; set +a
cd /content/maqamrock-yue2-lora-finetuning
git fetch origin pron-lora-long-aya && git checkout pron-lora-long-aya && git pull --ff-only
setsid nohup bash INFERENCE/jarir_lever_probe.sh > /content/logs/jarir_lever_all.log 2>&1 & disown
```
`generate.py` **skips succeeded tracks**, so this reruns only the 5 pending scale arms
(the prompt tier is skipped automatically). Prereqs on a fresh VM:
`bash bootstrap/setup.sh --inference`, then restore the α0.1 adapter:
```bash
gsutil -m cp -r "$GCP_BACKUP_BASE/quran_ahh_r8_rank32/maqamrock_merge/convert/qahh_a0p1" /content/converter/out/
# verify ar sha256 = 4b4d2103e59de6b3279088d53cb28b15df901f96e4a37a67e2306e9bfdac0ecb
```
Stop anytime: `pkill -f jarir_lever_probe` (driver + generate.py).

## New eval app — `INFERENCE/rating_app/` (repo commit `e1f2eb6`)
General listening **rating** app (single-file Flask). Asks for the track folder (terminal + web
`/setup`), configurable criteria (`/criteria`), generic discovery, Markdown export. Delivered at
`gs://…/OSTRIS_Arabic_Suno_Finetuning/tools/rating_app/` (app.py, README.md, requirements.txt).
Windows: `py -m pip install flask; py app.py` → paste `C:\Users\DELL\Downloads\jarir_lever_probe`.
The old Quran `INFERENCE/eval_app/` is untouched.

## Environment / sidecars (verified this session)
- branch `pron-lora-long-aya`; latest commit `e1f2eb6` (pushed).
- secrets loaded (`GCP_BACKUP_BASE=gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning`).
- α0.1 adapter present at `/content/converter/out/qahh_a0p1/`; `ar` sha256 matches.
- backup daemon `backup_to_gcp.py --inference` **live** · vm-continuity watch **live**.
