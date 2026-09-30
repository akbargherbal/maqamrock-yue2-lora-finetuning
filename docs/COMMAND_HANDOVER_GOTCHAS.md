# Human-terminal handover gotchas

Append-only. One entry per gotcha: the human-environment fact, the agent failure
it prevents, and the correct pattern. The procedure that uses this list is
`skills/command-handover/SKILL.md`; the always-on trigger is in `AGENTS.md`.

This list exists because the agent's shell tool is not the user's terminal.
Signals, session ownership, and where a detached process writes are obvious to a
human and invisible to the agent — so they get written down here.

## 2026-09-23 — The batch launch lacked `disown` (prompted this list)

- **Fact:** the user runs commands by hand; Ctrl+C in their terminal is a real
  risk, and a long job in the foreground dies with it.
- **Failure prevented:** the agent handed over
  `python INFERENCE/generate.py manifests/batch_songs_23092026.json` in the
  foreground, even though a ~2 h batch should be detached.
- **Correct pattern:** `setsid nohup … > /content/logs/<name>.log 2>&1 & disown`,
  with the stop command (`pkill -f …`) and the resume flag
  (`--out-dir "$(cat out/latest)"`) stated alongside.

## Detached output must be redirected to a log

- **Fact:** a detached process's stdout/stderr has no terminal; if not redirected
  it is lost.
- **Correct pattern:** `> /content/logs/<name>.log 2>&1` on every detached launch.

## A backgrounded job inherits `SIGINT=ignored` — Ctrl+C (and `kill -INT`) won't stop it

- **Fact:** a shell background job (`… &`) inherits `SIGINT=SIG_IGN`, and a
  non-interactive shell **cannot** reset it — so Ctrl+C doesn't reach it *and*
  `kill -INT <pid>` is a silent no-op. Training is launched **detached** now, so
  its clean stop has to reset SIGINT explicitly.
- **Correct pattern:** use `python train_ctl.py start` (it spawns via
  `Popen(start_new_session=True)` with a SIGINT reset) and `train_ctl.py stop`.
  For any other detached job, still state its exact stop command.

## No stop/resume line = a stuck job

- **Fact:** a detached job the user can't stop without hunting for a pid is a
  trap; a job that can't be resumed wastes the session.
- **Correct pattern:** always give `pkill -f '<pattern>'` and the exact resume
  command (e.g. `--out-dir "$(cat out/latest)"` for `generate.py`).

## vscode.dev clipboard is glitchy

- **Fact:** selecting/copying text out of the chat is slow and unreliable for the
  user.
- **Correct pattern:** put anything long the user must copy into
  `agent_notes/current.md`, not the chat.

## Env vars are staged by the launching notebook

- **Fact:** `HF_TOKEN`, `GCP_DATASET_PATH`, `GCP_BACKUP_BASE` are exported by the
  notebook, not the shell. A terminal that can't see them means the cell hasn't
  run yet (`docs/README.md`, constants).
- **Correct pattern:** check/mention this before a command that needs them.

## One shared GPU

- **Fact:** training and inference share one rented GPU; two GPU jobs at once can
  OOM the NAR graph.
- **Correct pattern:** `nvidia-smi` first; never run GPU work while training is
  active (`generate.py` refuses unless `--allow-concurrent`).

## 2026-09-25 — `pkill -f '<pattern>'` matches the launching shell too

- **Fact:** the agent's shell tool runs each command as `/bin/bash -c "<script>"`,
  so that shell's own command line contains any pattern written literally in the
  script. `pkill -f backup_to_gcp.py` therefore matches and kills the very shell
  running it, before the restart line executes.
- **Failure prevented:** two daemon-restart attempts died mid-script (empty
  output), leaving **no** backup running while the agent believed it had
  restarted one. The bracketed `[b]ackup…` trick does not help here, because the
  same command also contains the literal `backup_to_gcp.py` it is launching.
- **Correct pattern:** anchor to the real process — `pkill -f '^python.*backup_to_gcp'`
  (`^` cannot match a `/bin/bash -c …` command line). Reserve the bracket trick
  for the case where the bracketed literal is the pattern's **only** occurrence
  in the command.

## 2026-09-26 — `trap - INT` cannot un-ignore an inherited signal

- **Fact:** to keep `kill -INT` working on a detached run we first wrapped the
  launch as `setsid nohup bash -c 'trap - INT; exec …'`. It does **not** work:
  POSIX says a non-interactive shell cannot reset a signal that was ignored on
  entry, so the child keeps `SIGINT=SIG_IGN` and `kill -INT` is a silent no-op
  (verified via `/proc/<pid>/status` `SigIgn` bit `0x2` and a signal round-trip).
- **Failure prevented:** a detached training run that *looks* stoppable but
  ignores the clean stop, forcing `kill -9` and losing up to `save_every` steps.
- **Correct pattern:** reset in Python before `exec` —
  `signal.signal(signal.SIGINT, signal.SIG_DFL)` — which *can* override an
  inherited ignored signal. `train_ctl.py start` does exactly this.

## Related traps (not terminal-specific)

- The auto-resume trap: relaunching a run name with checkpoints present resumes
  instead of starting fresh — `docs/README.md`, "The one rule that bites people".

## 2026-09-27 — `train_ctl.py stop`/`status` need the same `--config` as the launch

- **Fact:** `stop`/`status` verify the target pid with
  `_cmdline_matches(cmdline, config, run_name)`, where `config`/`run_name` come
  from the *stop command's own args* — `--config` defaults to
  `config/akbar_arabic_rock_lora.yml` (run name `akbar_arabic_rock_lora`). A side
  run launched with `--config config/quran_long_aya_r8.yml` does not match that
  default, so `stop --log-name train_quran_long` (no `--config`) refuses with
  `refusing to signal pid N: not our training run`. Reproduced 2026-09-27 while
  stopping the full-set quran cache build.
- **Failure prevented:** a stop that silently does nothing (the run keeps burning
  GPU), or a panicked `kill -9` fallback that loses progress.
- **Correct pattern:** mirror the launch's `--config` (or `--run-name`) on
  stop/status:
  `python train_ctl.py stop --config config/<run>.yml --log-name <log>`.
- **Possible hardening (not done):** `cmd_stop`/`cmd_status` could fall back to the
  `run_name`/`config` recorded in `<log-name>_state.json` when the flags are omitted.

## 2026-09-29 — to show the user a local HTML file, serve it and hand over the tunnel URL

- **Fact:** `browser.preview` and `browser.tabs.open` both fail with
  `[browser.disconnected] No desktop browser is connected to this session` unless the
  OpenCode **desktop app** is attached — on a Colab VM it usually is not. `file://` URLs
  are rejected outright (`Paths and file:// URLs are not browser URLs`). So the agent
  cannot present a generated HTML artifact through the browser tools, however correct
  the file is.
- **Failure prevented:** concluding the artifact is broken, or retrying browser tools
  in a loop, when only the *presentation* path is unavailable.
- **Correct pattern:** serve the directory and hand over the forwarded URL.
  `cd /content/webshare && python3 -m http.server 8765 --bind 0.0.0.0` (detached; log
  `/content/logs/http.log`; stop `pkill -f 'http.server 8765'`). The running
  `code tunnel` (`/root/.vscode/cli/code_tunnel.json` → name `inference_akbar`,
  id `amusing-dog-glt654t`, cluster `asse`) forwards any localhost port at
  `https://<tunnel-id>-<port>.<cluster>.devtunnels.ms`, i.e.
  `https://amusing-dog-glt654t-8765.asse.devtunnels.ms`. Verify with
  `curl -s -o /dev/null -w '%{http_code}'` before handing it over.
- **Two traps:** (a) the URL returns **302/404 for the first few seconds** after the
  server starts while the tunnel re-registers the port — retry before declaring
  failure; (b) **killing or restarting the server breaks the page already open in the
  user's tab** — restore service in the same turn and keep the same path working
  (`curl` the tunnel URL to confirm 200, not just the local port).
- **Security note:** serve a dedicated directory (e.g. `/content/webshare`), not the
  repo root, so the tunnel does not expose the whole checkout. Checkout copies go
  stale — re-copy after editing the source file.

## 2026-09-29 — a fresh Colab clone lands on `main`, not the working branch

- **Fact:** the repo's default branch is `main`; session work lives on other
  branches (e.g. `music-cover`, 10 commits ahead on 2026-09-29). `docs/START.md:14`
  and `docs/INFERENCE.md:11` clone with no `--branch`, so a fresh VM gets `main` and
  is **missing** this session's files (`INFERENCE/test_batch.sh`,
  `manifests/test_verbatim_hijaz/`, the updated `docs/music-cover-feasibility.md`).
- **Failure prevented:** "the new files aren't there" confusion on a fresh VM, or
  silently running an older manifest.
- **Correct pattern:** clone with `--branch <name>`
  (`git clone --branch music-cover <url>`), or `git fetch origin <branch> &&
  git checkout <branch>` after a default clone. **Do not merge to `main`** —
  decision 2026-09-29: all work stays on `music-cover`; `main` is intentionally
  not updated.
- **Possible hardening (not done):** add `--branch <name>` to the clone lines in
  `START.md`/`INFERENCE.md`, or state the branch explicitly.

## 2026-09-29 — `generate.py`'s trigger test is a substring search, not a prefix test

- **Fact:** `INFERENCE/generate.py:316` prepends `arabmaqamrock ` iff
  `TRIGGER.strip() not in text` — a substring test over the **whole** style file, not a
  check of its leading token (`--no-trigger` disables the prepend entirely).
  `run_one.sh` never prepends; it passes `STYLE_FILE` through verbatim.
- **Why the difference is invisible for this manifest:** all three Hijaz styles contain
  `arabmaqamrock` *somewhere*. For `hijaz_sunoblk.txt` it is inside its `genre:` line
  (line 5), even though the file's **first** token is `[Is_MAX_MODE: …`. So the test
  passes and no arm is prepended — making `--no-trigger` a **no-op** here.
- **The real hazard:** the decision hinges on incidental content elsewhere in the file.
  Edit the Suno block so `arabmaqamrock` no longer appears anywhere (e.g. drop it from
  the `genre:` line) and the trigger is suddenly prepended, changing that arm with no
  visible intent. Symmetrically, a style that legitimately needs the trigger but merely
  *mentions* it in prose silently goes without.
- **Correct pattern:** don't reason about prefixes. Check the file itself
  (`grep -c 'arabmaqamrock' <style>`), and pass `--no-trigger` when you want the file
  verbatim regardless of its contents.
- **How it was found:** reading the `audiocpp_cli` command line recorded in the run's
  `_runs_status.log`, which shows the style actually sent to the model.
- **Correction (same day).** An earlier version of this entry claimed the default would
  prepend the trigger *to the control arm only*, decoupling the listening audio from the
  screen. **That was wrong** — the substring test matched the control arm too. Nothing
  was harmed: the render passed `--no-trigger`, which was a no-op, so the rendered arms
  are identical to the screened ones. Corrected in the same session it was written.
- **Related:** `generate.py` writes `batch_manifest.json` + `input.json` into the run
  dir **before** any generation, so an explicit `--out-dir` makes the batch resumable;
  `--dry-run` validates paths/caps and needs no GPU.

## 2026-09-29 — never edit a shell script while it is running

- **Fact:** bash reads script files **incrementally by byte offset**, not into memory.
  Editing the file mid-execution shifts those offsets, so the next read starts
  mid-token. Symptom seen: `run_one.sh: line 85: ession-option: command not found` — a
  fragment of `--session-option` (i.e. bash resumed partway through that token).
- **What it cost:** `run_one.sh` was edited at 09:22:40 while track 4 was executing
  (09:21:39–09:28:23). The fragment ran as its own command *carrying the trailing
  `> "$log" 2>&1` redirect*, so it **overwrote that track's CLI log** (its TIMING lines
  are gone), and the script's `rc=$?` captured `127` instead of the binary's `0`. The
  driver then reported the track FAILED in `_runs_status.log`, `_failed_runs.log` **and**
  `batch_summary.txt` (`ok: 4  failed: 1`).
- **The audio was fine.** `/usr/bin/time` had already written `Exit status: 0`, the WAV
  was byte-exact for its declared duration (48 kHz stereo 16-bit, diff 0) and matched its
  screen prediction exactly (5701 frames / 228.0 s). So: a **spurious failure**, and the
  false record nearly caused a needless 7-minute re-render.
- **Rules:** (1) never edit a script while a batch is calling it — edit between runs,
  or run a copy; (2) don't trust a log's `exit=` on its own — cross-check the artifact
  (`_time.txt`'s `Exit status`, the WAV's byte length against its declared duration).
- **A file-count check is not a success check.** Counting `*.wav` reported "5 of 5" for
  a batch whose driver called one track FAILED. Gate on exit codes, then on artifacts.

## 2026-09-30 — `generate.py`'s default run dir is timestamped; a re-run scatters the set

- **Fact:** without `--out-dir`, `generate.py:477` makes `out/<YYYYMMDD-HHMMSS>_<label>/`. A
  resumed/retried batch that omits `--out-dir` writes a **second** directory, so `*.wav` now
  spans two runs and a transcription `--input-dir` silently sees only one (or the wrong one).
- **Correct pattern:** always pass the same absolute `--out-dir`; resume then skips succeeded
  tracks (`generate.py:794`). The pass-1 flow uses
  `out/batch_12_rock_v2` (`docs/PRON_LORA_RESCUE.md`, G1).

## 2026-09-30 — `sheetsage2_transcribe.py` silently skips an existing `score.abc`

- **Fact:** the driver returns early when `<out-dir>/<stem>/score.abc` already exists
  (`sheetsage2_transcribe.py:107`) — no warning. Re-render a take with the same `name`+`seed`
  (a legitimate `--force` redo) and re-transcribe in place, and the **old** ABC is stapled to
  the **new** audio; the rescue then guides on the wrong score.
- **Correct pattern:** transcribe into a **fresh** `--abc-dir` (or re-run with `--force`)
  whenever a source WAV changed. `rescue_abc_batch.sh --plan/--verify` records and re-checks
  the ABC sha256 so a mismatch halts before any render.

## 2026-09-30 — transcription auto-selects CUDA on the GPU box (not "free CPU")

- **Fact:** `sheetsage2_transcribe.py:100` moves to `cuda` whenever `torch.cuda.is_available()`.
  On the GPU VM the "free CPU" step therefore holds the rented GPU, and can OOM a queued
  render (`run_one.sh`/rescue) because two jobs share one GPU.
- **Correct pattern:** run it on a **free CPU runtime**, or force CPU on the GPU box with
  `CUDA_VISIBLE_DEVICES="" /content/.venv-sheetsage2/bin/python INFERENCE/sheetsage2_transcribe.py …`.

## 2026-09-30 — a rescue render has the *same WAV filename* as the pass-1 take it guides

- **Fact:** `run_one.sh:42` names output `$OUT/<name>_<seed>.wav` — identical to the pass-1
  filename. Point a rescue at the pass-1 dir (one `OUT_DIR` slip) and it **overwrites the liked
  v2 take**, same name, no warning.
- **Correct pattern:** render rescues into a dedicated dir; `rescue_abc_batch.sh` refuses when
  `--out-dir == --pass1-dir` or when the target holds a `batch_manifest.json`.

## 2026-09-30 — `sheetsage2_transcribe.py` silently skips stems matching `_[23]_`

- **Fact:** the default exclusion is `VARIANT_MARKER = re.compile(r"_[23]_")`
  (`sheetsage2_transcribe.py:34`), meant to drop the old `_2_`/`_3_` duplicate takes. A legit
  stem whose name/slug happens to contain `_2_`/`_3_` is dropped with **no error** — that take
  gets no ABC, so the rescue silently omits it.
- **Correct pattern:** pass `--all` (or an explicit `--exclude`) for a batch whose stems are not
  the legacy `_2_`/`_3_` variants; the rescue flow now uses `--all`
  (`docs/PRON_LORA_RESCUE.md`, phase 2).

## 2026-09-30 — pass-1 preflight wants the manifest's *whole* `loras` registry, not just the used adapter

- **Fact:** `generate.py` preflight existence-checks **every** alias in `input.loras`
  (`generate.py:581` iterating `resolve_loras`, `:253`), regardless of which `lora` the songs
  reference. `manifests/batch_12_rock_v2.json` carries the shared 4-alias registry (v2,
  qfinal_a0.3, qfinal_a0.5, qfinal_a0.5_explicit), so a **pass-1 v2** batch refuses to start
  unless **all four** adapter pairs are on disk.
- **Failure prevented:** the handed-over pass-1 command dies in preflight with
  `missing AR LoRA adapter [qfinal_a0.5]: /content/converter/out/qfinal_a0.5/…` even though
  pass-1 only ever uses `v2`. `docs/PRON_LORA_RESCUE.md` Phase 0 stages only v2 + qfinal_a0.3,
  so following the runbook literally reproduces the failure. No `--skip-preflight` exists on
  `generate.py` (unlike `rescue_abc_batch.sh`).
- **Correct pattern:** stage every alias the manifest declares before the batch —
  `gsutil -m cp -r "$GCP_BACKUP_BASE/loras/audio_cpp/pron/qfinal_a0.5" /content/converter/out/`
  (`qfinal_a0.5_explicit` aliases into that same dir, so this satisfies both). Alternative:
  trim the derived `batch_12_rock_v2.json`'s `loras` block to the adapters its songs actually reference.

## 2026-09-30 — the inference test suite fails while a real render is running (host-wide liveness)

- **Fact:** `status.py:158` `section_inference` decides RUNNING via `_pgrep("generate.py")` — a
  **host-wide** process check, not scoped to the `INFER_OUT` directory it prints. So while any
  real `generate.py` runs, `tests/e2e/test_monitor_status_e2e.py::test_j11_status_inference_section_from_real_run`
  (which monkeypatches `INFER_OUT` to a tmp run and asserts `inference: idle`) fails with
  `inference: RUNNING · j11 · 1/1 wavs` — the assertion, not the code, is wrong.
- **Failure prevented:** reading that as a regression (it is not; the test is not isolated from a
  concurrent run), and re-running the suite mid-batch — its e2e path spawns a real `generate.py`
  that hashes the 3.9 GB GGUF, competing with the live render for CPU/disk.
- **Correct pattern:** run the suite with no inference run active, or deselect that case:
  `python -m pytest tests/ -q -k 'not test_j11_status_inference_section_from_real_run'`.
  (Hardening not done: scope the liveness probe to `INFER_OUT`, or xfail the case when a live run
  exists.)
