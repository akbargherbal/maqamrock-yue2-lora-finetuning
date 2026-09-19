# AGENTS.md

## What you're for

- Get a training run ready: confirm the dataset, model assets, and config are actually in place before the user launches, and sanity-check the YAML against `DECISIONS.md` (fields that look real but are dead, paths that differ from what they appear to say).
- While a run is going, answer "how's it going" by reading `loss_log.db` (via `monitor_loss.py`) and the GPU CSV — not by guessing or recalling an earlier turn.
- When a run crashes, find the cause, and — per the policy below — either hand over the exact resume command or run it yourself, depending on whether anything changed.

- When the user assigns it, carry out the **approved caption-lyrics amendment** (below) — a bounded, one-off dataset task with its own gates.

Nothing else. Not a monitor running in a loop, not a companion — a problem solver, called in when needed, plus the one narrow standing exception below.

## Durable decisions & progress

Read `DECISIONS.md` and `PROGRESS.md` (repo root) at the start of any task involving training or tooling. `DECISIONS.md` records major, cross-session decisions and non-obvious insights verified against actual `ai-toolkit` source — the things a fresh session must not re-litigate or rediscover by reading a GitHub issue thread again. `PROGRESS.md` records the milestone trail: runs and their outcomes, and what's next. Keep both short and add an entry only when losing it would cost real work; neither is a log. Routine, per-session state goes in `agent_notes/current.md`.

**Maintain `agent_notes/current.md` yourself — don't wait to be asked.** The user drives this over `vscode.dev`, where selecting and copying text out of the chat is glitchy and laggy. So keep that file current as the copy-free handoff surface: after any session that changes run state, fixes tooling, or produces a command worth re-running, write/refresh it (date, what happened, exact commands, what's next). Put anything the user might otherwise have to copy from the conversation there. It's git-ignored, but `backup_to_gcp.py` mirrors it to GCS.

## The stack, so a fresh session isn't guessing

`ostris/ai-toolkit`, launched via its real CLI: `python run.py config/akbar_arabic_rock_lora.yml -l /content/logs/train.log` — not the Web UI (see `DECISIONS.md` for why that loses nothing on observability). `job: extension` / `process[].type: diffusion_trainer`, `arch: yue2`. Everything for this job lands under one folder: `training_folder/akbar_arabic_rock_lora/` — checkpoints, `loss_log.db`, `config.yaml` (auto-saved), samples, and the `tensorboard/` subfolder all together. One GPU, shared, rented.

## Observability — the three real surfaces

1. **`loss_log.db`** — the primary source. SQLite, WAL mode, safe to read while training writes to it. Use `monitor_loss.py`, don't hand-write SQL each time. Path: `<training_folder>/akbar_arabic_rock_lora/loss_log.db`.
2. **The `-l` log file** (`/content/logs/train.log`) — stdout/stderr, including the tqdm progress line (`lr:` + per-key loss) and any traceback. This is what you tail after a crash to find the cause.
3. **GPU CSV** (`/content/logs/gpu_usage.csv`, from `gpu_logger.py`) — utilization/memory/temp/power, sampled every 10s. AI Toolkit itself logs none of this (verified, see `DECISIONS.md`) — this script is the only source, so confirm it's actually running before trusting a "the GPU looks idle" read.

**Not a source:** `aitk_db.db` (the config's `sqlite_db_path`). It only populates when the Web UI launches the job, and only ever holds a status string, never metrics. If a fresh session inherits a config pointing at it expecting run history, that expectation is wrong — check `DECISIONS.md`.

## Never

- **Start a new run, or resume with any changed config/hyperparameter, without the user typing the command themselves.** Give the exact command every time — vague hand-waving forces them to reconstruct settings you already know.
- **Auto-resume is the one exception**, and only when *all* of these hold: the run was already running with human approval, it stopped from an unplanned interruption (not a deliberate stop), and the resume uses the identical config and run name. In that case, resume it yourself rather than waiting for the user to come back and retype a command — that's the whole point of the exception. Log what you did in `agent_notes/current.md` either way.
- Modify the dataset (`/content/yue2_dataset`) or re-run `prepare_yue2_dataset.py` — it's already built and verified (`verification.md`); don't regenerate it "to be sure." **The one exception is the approved caption-lyrics amendment below, and only within its stated scope.**
- Edit `config/akbar_arabic_rock_lora.yml` (or any run config) on your own initiative. Config and hyperparameter decisions are the user's. Measure, report, and recommend; don't apply.
- Run anything GPU-heavy while a run might be active — check `nvidia-smi` first. One GPU, shared.

## Approved amendment: lyric-conditioned captions (dataset v2)

**Why this exists.** The first run trained on style-only captions with empty lyrics, by design (`prepare_yue2_dataset.py` docstring; `verification.md` §5). That decision came from the original style-only goal and was never revisited when the goal became "structurally coherent full songs that sing the provided lyrics correctly". Result: strong style, degraded Arabic pronunciation. Full analysis: the newest `PROGRESS.md` entry ("Listening evaluation + root cause"). Treat that as a hypothesis the v2 run will test, not as settled fact.

**What this authorizes, and nothing more.** Rewriting the caption `.txt` files so each one is `style text` + a literal `[Lyrics]` line + that clip's lyrics (the layout `parse_caption()` expects, `yue2_model.py`, `extensions_built_in/audio_models/yue2/`).

**Still forbidden:** touching audio files, filenames, or the shortlist (which tracks are in the set); re-running `prepare_yue2_dataset.py`; editing any YAML; starting any run or GPU work; overwriting the v1 dataset in GCS. This task needs no GPU.

**Procedure, in order. Stop at each gate and report to the user; don't run ahead.**

1. **Read-only investigation.** Read the newest `PROGRESS.md` entry, `prepare_yue2_dataset.py`, `verification.md`. Then inspect the raw `workspace_manifest.json` files (in the original `min_4stars_ai_music` tree, not in this repo, so ask the user where it is if it isn't on the VM). Report, in `agent_notes/current.md` and to the user:
   - whether every one of the 267 shortlisted tracks has a non-empty `lyrics` field, and any that don't;
   - the exact format: Suno control lines (e.g. `///***///`), section headers with `|`-separated production descriptors (e.g. `[Intro | single clean guitar | ...]`), trailing `...`, diacritics;
   - whether many tracks share the same lyrics text;
   - prefix token counts (style + lyrics) for the longest clips, using the model's own tokenizer on CPU. The AR context is 24576 positions and whole-song training on the longest clip (370 s) already uses most of it, so overflow is a real risk. If the tokenizer can't be loaded without the GPU, say so; don't guess.
   - **Known caveat to keep in the report:** `lyrics` is what was submitted to Suno, not a transcript of what was sung. Note it; don't try to solve it.
2. **Gate: the user decides the caption lyric format** (keep Suno section headers and descriptors, or reduce to bare `[Verse 1]`-style tags; what to do with `///***///`; what to do with over-long prefixes). Don't choose for them. Whatever is chosen must match what inference prompts will use, so flag that.
3. **Write a standalone script** (new file in the repo, e.g. `add_lyrics_to_captions.py`; import helpers from `prepare_yue2_dataset.py`, don't edit it). Dry-run by default, `--apply` to write. It reads the existing v1 `.txt` files and manifests, matches tracks using the same naming logic as the original build, and only appends the lyrics block. The v1 style text must remain byte-identical.
4. **Preserve v1 before writing anything.** Copy the v1 captions to a separate local folder and to a sibling GCS prefix. Write v2 to a **new** local directory and a **new** GCS prefix; never overwrite v1's GCS prefix. Storage is cheap; the v1 dataset is the record of the first run. Do not copy `_latent_cache` into the v2 dataset or its GCS prefix. Its text-embedding cache is stale against new captions. The audio-derived latent cache is caption-independent, but rebuilding both is the simple, safe path.
5. **Verify offline, no GPU.** Write `verification_v2.md` in the style of `verification.md`: 267 files in, 267 out; every v2 style part byte-equal to v1; `parse_caption()` round-trips on **all** captions (style equals v1, lyrics non-empty, or an explicit exception list); token-count table for the longest clips; a handful of full example captions pasted in.
6. **Commit the script, `verification_v2.md`, and a short `PROGRESS.md` entry; the user pushes** (see "GitHub pushes"). Then stop and give the user the commit hash so it can be reviewed independently before any compute is spent.
7. **Surface, don't decide:** the v2 run needs its own run name and output folder, or `python run.py` will silently auto-resume from the 3000/3000 checkpoints (see `DECISIONS.md`); `bootstrap/setup.sh` pulls the dataset from `GCP_DATASET_PATH`, so a v2 run needs that exported to the v2 prefix; `backup_to_gcp.py` `TARGETS` must cover the new run name. Note all three for the user; changing them is the user's call.

## Runtime reality — Colab is ephemeral, storage is cheap

Google Colab: strong GPUs, stateless. Losing the VM or switching runtime wipes `/content` — the repo working tree, the HF cache, everything. Only GitHub + GCS persist. Storage costs far less than compute, so bias hard toward persisting anything expensive to regenerate (the LoRA checkpoints, `loss_log.db`, the prepared dataset, logs, this repo's own notes).

**Restore on a fresh VM:**

```bash
git clone <this repo's URL>
cd maqamrock-yue2-lora-finetuning
bash bootstrap/setup.sh > /content/logs/setup.log 2>&1 &
# then authenticate vscode.dev in the foreground while setup.sh runs —
# it clones ai-toolkit, installs its (heavier) deps, pre-warms the HF
# cache for the yue2 assets, and pulls the dataset from GCS, all in parallel
```

`bootstrap/setup.sh` is idempotent: it skips the dataset download if the completion marker is present, and skips any HF asset already in the local cache. It does **not** restore checkpoints or `loss_log.db` — pull those from the run's GCS prefix (`<base>/<run-name>/output/`) before resuming.

## Backup responsibility

- `backup_to_gcp.py` mirrors `training_folder` (checkpoints, `loss_log.db`, config, samples, tensorboard), `/content/logs` (train log + GPU CSV), and `agent_notes/`. Before a run that writes a new output folder, confirm `TARGETS` actually covers it — if not, fix the script, don't work around it by hand.
- Before the user starts a run, confirm the backup daemon is actually running (`pgrep -af backup_to_gcp.py`, or freshness of `/content/logs/gcp_backup.log`) and that `gpu_logger.py` is too (`pgrep -af gpu_logger.py`). If either isn't, give the exact command — `--run-name` is required for the backup script, and the GCS base comes from `GCP_BACKUP_BASE`, exported by the launching notebook:

  ```bash
  cd /content/maqamrock-yue2-lora-finetuning
  setsid nohup python backup_to_gcp.py --run-name akbar_arabic_rock_lora \
    > /content/logs/gcp_backup_stdout.log 2>&1 & disown
  setsid nohup python gpu_logger.py --out /content/logs/gpu_usage.csv \
    > /content/logs/gpu_logger_stdout.log 2>&1 & disown
  ```

- "Is my progress backed up?" → compare GCS object timestamps under the run's configured prefix with local timestamps and report the actual drift — don't assume the last known-good state is still current.

## GitHub pushes

- Pushing needs auth the user supplies, never the agent. Ask them to run `bash bootstrap/github_auth.sh` in their own terminal and paste a PAT at the hidden prompt; it validates the token, runs `gh auth setup-git`, and prints the authenticated account. After that, `git push` works for the rest of the session. Never ask for the token in chat.
- `/content` is ephemeral — re-run it on every fresh VM.

## Repo docs & checks

- Dataset build + independent verification: `prepare_yue2_dataset.py` (already run, don't re-run; v2 captions come from the amendment above, not from this script) and `verification.md` (the audit record — read it before assuming anything about dataset format is unverified).
- Config: `config/akbar_arabic_rock_lora.yml`. Read the inline comments before "fixing" anything that looks off — several apparent issues (`log_config`, `type: diffusion_trainer`) are already resolved in `DECISIONS.md`.
- Metrics: `monitor_loss.py <path to loss_log.db>` — latest step, latest metric values, step-rate/ETA. GPU: `gpu_logger.py`.
- Operational runbooks: `docs/` — `START.md`, `PAUSE_RESUME.md`, `BACKUP_RESTORE.md`, `MONITOR.md`. Point the user there for "how do I do X" instead of re-deriving it, and keep them in sync when a procedure changes.

## Where to look before answering "what's going on"

- **Training progress:** `<training_folder>/akbar_arabic_rock_lora/loss_log.db` via `monitor_loss.py`. Don't trust `aitk_db.db` for this (see above).
- **Is it still alive:** `pgrep -af run.py`, and the tail of `/content/logs/train.log` for the most recent line / any traceback.
- **Checkpoints:** inside `<training_folder>/akbar_arabic_rock_lora/` per `save.save_format`/`save_every`/`max_step_saves_to_keep` in the config.
- **TensorBoard (secondary, redundant with loss_log.db):** `<log_dir>/akbar_arabic_rock_lora_<timestamp>/` — glob for the timestamped subfolder, don't assume `log_dir` itself holds the event file.
- **GPU:** `/content/logs/gpu_usage.csv`, if `gpu_logger.py` is running.
- **Base model / assets:** standard HF cache (`~/.cache/huggingface/hub`), not a bespoke local directory — see `DECISIONS.md`'s asset-download entry before assuming a file is missing just because it's not under the repo.
