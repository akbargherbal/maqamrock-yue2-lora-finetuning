# AGENTS.md

_Last revised: 2026-09-30._

## 0. Read order — don't read everything

Authority is **one row per topic** in `SOURCE_OF_TRUTH.md` (higher row wins). Doc index is
`docs/README.md`. Identify the mode (§2) and read *only* that runbook plus its authority
row. That is the whole reading list for a task. Everything else is not in scope. A
`graphify query` (§12) is a **locator, not a read**: use it to find candidate files for a
structure question, then open the real file.

## 1. What you're for

Four jobs, plus this file's standing duties:

1. **Get a task ready** before launch — confirm the mode's prerequisites (§2); sanity-check
   any YAML against `DECISIONS.md` (dead keys, paths that differ from what they appear to say).
2. **Answer "how's it going"** from live artifacts only (§4) — never by recalling a turn.
3. **On a crash** — find the cause, then auto-resume (§8) or hand over the exact command.
4. **Stay oriented** — for structure questions (not a §2 mode), locate via `graphify query`
   (§12), then verify in source; cite `file:line`, never the graph.

Standing duties: the backup/continuity checks (§10) and the handoff surface (§6). These are
recurring, not optional. **Scope = the above + the task's runbook. In scope, be thorough;
outside it, don't invent work.**

## 2. Identify the mode and the environment — before acting

**Mode** (from the request):

| Mode | Runbook | Authority (per `SOURCE_OF_TRUTH.md`) |
|---|---|---|
| Start / pause / resume training | `docs/START.md`, `docs/PAUSE_RESUME.md` | config YAML |
| How's it going | `docs/MONITOR.md` | `loss_log.db` + `train.log` + GPU csv |
| Inference (GGUF + LoRA) | `docs/INFERENCE.md` | repo `INFERENCE/` scripts |
| Build the inference binary (new arch) | `docs/audiocpp_gpu_arch_builds.md` | `docs/audiocpp_gpu_arch_builds.md` + `bootstrap/setup.sh` (arch pin) |
| Merge v2 + pron | `docs/PRON_LORA_MERGE.md` | `merge_pron_lora.py --help` |
| Pron / long-aya training | `docs/PRON_LORA.md`, `docs/PRON_LORA_LONG.md` | its config + GCS tar |
| Verify / offline-eval pron | `docs/PRON_LORA_VERIFICATION.md` | replay script |
| Listening / blind eval | `docs/PRON_LORA_SWEEP.md`, `docs/AB_BLIND_EVAL.md` | `prepare_ab_eval.py --help` |
| Backup / restore | `docs/BACKUP_RESTORE.md` | `backup_to_gcp.py --help` |

**Environment** (check, don't assume): is `/content` present (Colab) or not (localhost)?
The `/content/...` paths, GCS, `nvidia-smi`, and `vm-continuity` are **Colab-only**. On a
local box use the repo's relative paths and skip backup/continuity. Never apply Colab
paths locally. **Never assume the main run** — run name, dataset, and output paths differ
per mode (pron, long-aya). Read the constants in `docs/README.md` and the mode's runbook.

## 3. The two essentials (why this file exists)

1. **Colab is ephemeral; storage is far cheaper than GPU time.** Losing the VM wipes
   `/content`; only GitHub + GCS persist. Bias hard toward persisting anything expensive to
   regenerate.
2. **Don't block the session.** Slow work runs detached with a log. **Training is detached
   too** — a stray Ctrl+C can't kill it; stop it deliberately with `train_ctl.py stop`
   (SIGINT). Plain `kill` / `kill -9` skip the clean stop and lose progress since the last
   checkpoint — last resort. `start` refuses a second copy; `stop` verifies the PID.

## 4. Ground truth in one move

"State" means one deterministic read, never memory. **Run `python status.py`** — in one
read-only call it prints training step/rate + pid, inference batch `n/N` + failures, sidecar
pids, last backup age, local-vs-GCS drift, disk free, the current run folder, and graph
staleness (`built_at_commit` vs HEAD). It is environment-aware: on Colab it reads the full
picture; on a local checkout the `/content` surfaces report `n/a` (never apply Colab paths
locally), and it exits non-zero only when a sidecar is down while a run is active. Fallback
by hand: `train_ctl.py status`; `monitor_loss.py <run>/loss_log.db`; `tail train.log`;
`pgrep -af 'backup_to_gcp.py|gpu_logger.py'`; `vm-continuity status`.

Primary sources, mode-specific: `docs/MONITOR.md` (training), `docs/INFERENCE.md`
(inference). **Not a source:** `aitk_db.db` (Web-UI-only status row).

## 5. Handing over a command

The user runs commands by hand in a real terminal; your shell is a different session. Load
the `command-handover` skill first. **Anchors (use these, don't re-judge):** annotate a
command as *long-running* when it exceeds ~60 s, runs detached/background, touches the GPU,
or changes state. For those, state: **foreground vs detached**, output-log path, exact stop
command, and resume command. A short read-only one-liner needs no annotation. New gotchas
append to `docs/COMMAND_HANDOVER_GOTCHAS.md`.

**When you run something slow yourself** (tests, smoke, debugging): background it with a
log; don't block or tight-poll; report when it finishes. No permission needed for non-GPU
work — but see §8 for the GPU rule.

## 6. Handoff surface — `agent_notes/current.md`

It is a **copy/read surface for the user** (vscode.dev text selection is glitchy): a file
they can copy commands from and read in a browser / via TTS. **It is not documentation and
not a source of truth** — never cite it as authority, never rely on it as durable state;
re-derive from §4 / the authority docs. Overwrite it every time (never append).
**Write it when** the reply carries commands to run or is long/read-hostile; skip it for a
short plain answer. **Write it in the same turn you claim it** — saying it's written when
it isn't has recurred; treat it as a hard rule.

## 7. Reading state from artifacts (never paraphrase)

Quote the file line; don't summarise it into an assertion. Training: `loss_log.db`
(`monitor_loss.py`), `train.log`, `gpu_usage.csv`. Inference: `out/*.log`,
`_runs_status.log`, per-track JSON sidecars, `out/latest`. Checkpoint cadence from the
config's `save.*`. TensorBoard under `<log_dir>/<name>_<timestamp>/` (glob one level down).

## 8. Never — with the reason, so it generalizes

- Start a new run, or resume with a **changed** config/hyperparameter, without the user
  typing the command. A run finishing without errors is not a run being *right*.
- **Auto-resume is the only exception, and needs evidence:** run name + config unchanged,
  it looks crashed (traceback / OOM / VM reclaimed), and nothing signals a deliberate stop
  (no `Job stopped` at the end of `train.log`). Log it in `current.md`. **Can't tell crash
  from deliberate stop? Ask — don't guess.**
- Modify `/content/yue2_dataset` or re-run a dataset build. If a data change is genuinely
  needed, **stop and explain why** — don't proceed silently, don't silently accept degraded
  training.
- Edit a run config on your own initiative. Configs/hyperparameters are the user's:
  measure, report, recommend.
- **GPU rule:** one GPU, shared, rented. Before *any* GPU work run `nvidia-smi`. If a run
  is active, or you can't confirm none is, **do not start GPU work** — no overlap, ever.
  Non-GPU work (docs, backup, CPU tests) is always fine. A GPU smoke test while a run is
  active waits or gets asked about.
- Claim to have written `current.md` without writing it that turn.

## 9. Honesty and "done"

Every claim must map to an artifact the user can check. State plainly **what you verified
vs what you assumed**. **A turn is done** when the user can act on it as-is: the claim is
checkable, state is current (§4), and any uncertainty is named. Prefer a file/sidecar/log
line over prose you can't be held to.

## 10. Backup & continuity

`backup_to_gcp.py` mirrors run output + `/content/logs` + `agent_notes/` (training) or the
inference workspace (`--inference`). Before a run, confirm the sidecars: `pgrep -af
backup_to_gcp.py`, `pgrep -af gpu_logger.py`, `vm-continuity status` (exit 0 = healthy). If
one is down, give the exact start command — but if it can't be fixed in ≤1 command, note it
and continue; backup repair is not the session's work. "Is it backed up?" → compare GCS
timestamps with local and report the drift. **At session end**, re-check and state plainly
whether the last backup is current. Continuity is **idle-time** work — never spend GPU-paid
time on it. Layout/restore: `docs/BACKUP_RESTORE.md`.

## 11. GitHub pushes

Auth comes from the user, never the agent: ask them to run `bash bootstrap/github_auth.sh`
and paste a PAT at the hidden prompt. Never ask for the token in chat. `/content` is
ephemeral — re-run per fresh VM.

## 12. Self-maintenance (the loop that keeps this file true)

The contract is only as good as its freshness. After any change to a live doc, config, or
script: run the `docs-reconciler` skill, record the pass in `RECONCILIATION_LOG.md`, and
keep `SOURCE_OF_TRUTH.md` + the `docs/README.md` index current. **`AGENTS.md` is itself
reconciled:** when its claims drift, fix it in the same change and bump the revision line.
Persistence rule: an experience lesson only survives if it lands here (or in a skill) in
the same turn — otherwise the next session re-earns it. Skills: `crash-diagnose-and-resume`,
`inference-batch-run`, `command-handover`, `docs-reconciler`, `ab-blind-eval`; the runbooks
stay the source of truth. Knowledge graph — **orientation only, never authority** (not in §4's ground-truth set;
never outranks the config, code, or docs). For "how does X relate to Y", prefer
`graphify query "<q>" --budget 1500` over reading the tree. `graphify-out/GRAPH_REPORT.md`
is a dated snapshot — quote its `built_at_commit`, never cite it as fact. Refresh is
**two-tier**: `graphify update .` is free but code/AST-only; doc/semantic edges need
`/graphify --update` (LLM) — free tier after code changes, semantic tier before merges
(portability: `docs/GRAPHIFY.md`).
