# RESUME PLAN — `quran_ahh_r8` (rank 32) → run to completion, then rename

_Written 2026-10-05 ~19:00 UTC for the 2026-10-06 session._
**Point the agent here first thing:** “Follow `docs/QURAN_AHH_RESUME_PLAN.md` from Phase 0.”
The agent drives top-to-bottom and executes read-only / CPU / monitoring work autonomously;
commands marked **(you type)** are the state-changing ones you run in your own terminal
(`AGENTS.md` §8 + the `command-handover` skill). The agent re-derives state from live sources —
never from this prose.

## Read order (agent)
1. `AGENTS.md` (the contract) 2. this file 3. `docs/QURAN_AHH_RUN.md` (run hub)
4. `agent_notes/current.md` (live state). Then **verify, don't recall**: git, `nvidia-smi`,
   `pgrep`, `vm-continuity status`, the run’s `loss_log.db`, and the GCS `output/` prefix.
   Report “where we are / what’s running / any divergence / the one next step” before acting.

## Expected state at handoff (end of 2026-10-05)
- Run **`quran_ahh_r8` revised** — `config/quran_ahh_r8.yml` = **AR+NAR, rank 32/32,
  `ar_kl_weight 0.0`, `steps 28467` (3 epochs)** — authority; **do not edit**. Branch
  `pron-lora-long-aya`.
- Paused **2026-10-05 20:08 UTC** at step **19,738**, last save **19,500** (13 checkpoints) — or the
  VM died overnight. Either is resumable; resume picks up from step 19,500 (≤ ~238 steps redone).
- Banked: checkpoints + `optimizer.pt` + `loss_log.db` under `…/quran_ahh_r8/output/`; dataset
  `quran_ahh_dataset.zip` (3.97 GB) + `_latent_cache.tar` (737 MB). Round-2 adapters
  `c10500` + `c16500` under `…/quran_ahh_r8_rank32/convert/`.
- Name is a **misnomer (rank 32)**; **rename deferred to Phase 5**.

## Phase 0 — verify (agent, read-only, ~2 min)
```bash
cd /content/maqamrock-yue2-lora-finetuning && git status -sb
nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv,noheader
pgrep -af 'run\.py'; pgrep -af 'backup_to_gcp.py|gpu_logger.py'; vm-continuity status
df -h /content | tail -1
grep -oE '[0-9]+/28467' /content/logs/train_quran_ahh.log 2>/dev/null | tail -1
gcloud storage ls -l "$GCP_BACKUP_BASE/quran_ahh_r8/output/" 2>/dev/null | tail
```
Decide the scenario and say it:
- **A — still running** (`run.py` alive, step advancing): sidecars present? → **Phase 2**.
- **B — VM gone** (repo/`/content` missing): → **Phase 1 fresh restore**.
- **C — dirs present, `run.py` dead**: restart sidecars, then **(you type)** start → **Phase 2**.

## Phase 1 — resume (only if Phase 0 = B or a fresh VM)
```bash
# (you type) — fresh Colab
git clone https://github.com/akbargherbal/maqamrock-yue2-lora-finetuning.git /content/maqamrock-yue2-lora-finetuning
cd /content/maqamrock-yue2-lora-finetuning && git checkout pron-lora-long-aya
bash bootstrap/setup.sh --training        # needs GCP_BACKUP_BASE, GCP_AHH_DATASET_ZIP, HF_TOKEN; wait for all-[ok]
mkdir -p /content/ai-toolkit/output/quran_ahh_r8
gcloud storage rsync -r "$GCP_BACKUP_BASE/quran_ahh_r8/output" /content/ai-toolkit/output/quran_ahh_r8
gcloud storage cp "$GCP_BACKUP_BASE/quran_ahh_dataset/_latent_cache.tar" /content/
tar -C /content/quran_ahh_dataset/train -xf /content/_latent_cache.tar
setsid nohup python backup_to_gcp.py --run-name quran_ahh_r8 > /content/logs/gcp_backup.log 2>&1 & disown
setsid nohup python gpu_logger.py --out /content/logs/gpu_usage.csv > /content/logs/gpu_logger.log 2>&1 & disown
# (you type):
python train_ctl.py start --config config/quran_ahh_r8.yml --run-name quran_ahh_r8 --log-name train_quran_ahh
grep -m1 'Found step' /content/logs/train_quran_ahh.log     # MUST be the newest step, not 0
```
Guardrails: **same config + run name**; if it prints `Found step 0`, STOP (resume would restart) —
check the newest checkpoint is in the restored dir. If the VM died mid-run and no stop was typed,
this is the AGENTS auto-resume exception — log it in `current.md`. A **deliberate** pause is a
user-typed `stop`; resume is a user-typed `start`.

## Phase 2 — monitor to completion (agent; report on request, ~every 30–60 min)
- Check: step/`%`, `loss/loss` trend (bins, not single steps), VRAM peak, `gpu_usage.csv`,
  newest checkpoint local vs GCS, sidecars alive, `vm-continuity status`, disk.
- Expected: save every **1500 steps (~34 min)**; ~0.73 steps/s; completion ~**02:26 Bahrain**
  if it keeps running. Regenerate `TRAINING_ANALYSIS/quran_ahh_r8_rank32/` at checkpoints and
  commit/push when the user asks.
- If the backup sidecar dies: give the exact one-line restart (don’t turn the session into
  backup repair). If loss spikes or VRAM climbs abnormally: **report, don’t touch the config.**
- **Never edit the config/hyperparameters.** Don’t stop/start unless the user types it.

## Phase 3 — T4 round 2 (`c10500` vs `c16500`), separate GPU — can run in parallel
Adapters are already banked; hand the user this T4 handover (detached; ~26 min for 4 tracks):
```bash
# fresh T4 Colab
git clone https://github.com/akbargherbal/maqamrock-yue2-lora-finetuning.git /content/maqamrock-yue2-lora-finetuning
cd /content/maqamrock-yue2-lora-finetuning && git checkout pron-lora-long-aya
bash bootstrap/setup.sh --inference > /content/logs/setup.log 2>&1
python INFERENCE/quran_pt_probe.py --prefix quran_ahh_r8_rank32/convert --arms c10500,c16500 --dry-run
setsid nohup python INFERENCE/quran_pt_probe.py --prefix quran_ahh_r8_rank32/convert --arms c10500,c16500 \
  > /content/logs/quran_pt_probe_r32.log 2>&1 & disown
# stop: pkill -f 'quran_pt_probe.py --prefix quran_ahh_r8_rank32'
```
Record the user’s verdict in `TRAINING_ANALYSIS/quran_ahh_r8_rank32/ANALYSIS.md` + `current.md`;
compare against `base_*` and round-1 `c7500_simple`. Never run GPU work on the L4 while training
runs (one GPU); the T4 is separate.

## Phase 4 — the moment training reaches step 28,467
- Wait for the **final un-suffixed** `quran_ahh_r8.safetensors` (the no-step save) + `optimizer.pt`;
  confirm `run.py` self-stopped with **no traceback**.
- **(you type)** `python backup_to_gcp.py --run-name quran_ahh_r8 --once`; verify the final adapter
  + optimizer + `loss_log.db` in GCS.
- Finalize `TRAINING_ANALYSIS/quran_ahh_r8_rank32/ANALYSIS.md` (drop the LIVE banner, add final
  bins); commit/push.
- **(you type)** stop the sidecars; `vm-continuity status` = OK.

## Phase 5 — post-training: rename, blind eval, docs
1. **Rename** (offline; training must be stopped):
   `python bootstrap/rename_run.py --old quran_ahh_r8 --new quran_ahh_r32 --apply` → then restart
   the backup sidecar on `--run-name quran_ahh_r32`. Verify the printed `ctime check` line.
2. **Docs-reconciler pass** over the ~10 files referencing `quran_ahh_r8` (`docs/QURAN_AHH_RUN.md`,
   `docs/README.md`, `SOURCE_OF_TRUTH.md`, `bootstrap/setup.sh`, `INFERENCE/*`, the two
   `TRAINING_ANALYSIS/` dirs); rename `TRAINING_ANALYSIS/quran_ahh_r8_rank32/` → `…/quran_ahh_r32/`.
3. **Human blind gate** (`ab-blind-eval`) on the final checkpoint(s) vs the base before any merge —
   no adapter is “best” before the listen.

## Definition of done
- Step **28,467** reached; final adapter + optimizer + metrics banked in GCS; `run.py` clean.
- `TRAINING_ANALYSIS/` finalized; `agent_notes/current.md` current; everything pushed.
- Rename to `quran_ahh_r32` applied + docs reconciled; blind-eval package prepared.

## Guardrails (from `AGENTS.md` — non-negotiable)
- Configs/hyperparameters are the user’s: **measure, report, recommend — never edit.**
- No start/resume/stop without the user’s typed command (the auto-resume exception needs evidence:
  same name+config, looks crashed, no deliberate stop — else **ask**).
- **One GPU, shared:** `nvidia-smi` before any GPU work; never overlap; the T4 is separate.
- Long jobs run **detached** with a log; stop with the exact command (never Ctrl+C a batch).
- Keep backups current; `vm-continuity` is idle-time work. Persist lessons the same turn.

## Commands the user types tomorrow (summary)
| Step | Command |
|---|---|
| Restore env (fresh VM) | `bash bootstrap/setup.sh --training` |
| Resume training (C/B) | `python train_ctl.py start --config config/quran_ahh_r8.yml --run-name quran_ahh_r8 --log-name train_quran_ahh` |
| Pause | `python train_ctl.py stop --config config/quran_ahh_r8.yml --run-name quran_ahh_r8 --log-name train_quran_ahh` |
| Force backup | `python backup_to_gcp.py --run-name quran_ahh_r8 --once` |
| Rename (post) | `python bootstrap/rename_run.py --old quran_ahh_r8 --new quran_ahh_r32 --apply` |
