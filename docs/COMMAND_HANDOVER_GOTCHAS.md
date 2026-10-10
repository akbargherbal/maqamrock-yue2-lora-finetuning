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
  `config/LEGACY_akbar_arabic_rock_lora.yml` (run name `akbar_arabic_rock_lora`; renamed 2026-10-06). A side
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

## 2026-10-04 — CUDA-13 image: the prebuilt `audiocpp_cli` needs CUDA-12 libs on `LD_LIBRARY_PATH`

- **Fact:** the staged prebuilt binary (sm_75/T4) is built against **CUDA 12**
  (`libcublas.so.12`, `libcudart.so.12`). A Colab image whose toolkit/driver is
  **CUDA 13** (e.g. driver 580, `/usr/local/cuda-13.0`, torch cu130) does not expose
  those SONAMEs on the default loader path, so the process dies immediately with
  `error while loading shared libraries: libcublas.so.12: cannot open shared object
  file`. The CLI still says "no CUDA toolkit needed" — true for *building*, not for
  this ABI.
- **Failure prevented:** a "generation" that looks started but never loads the model.
  Symptom: the run's driver log shows `START …` and `END … exit=127` in the **same
  second**, and `<name>_time.txt` says `Command exited with non-zero status 127` (the
  launch, not the model). `pgrep audiocpp_cli` returns nothing.
- **Correct pattern:** the `.so.12` files ship in the pip `nvidia-*-cu12` packages;
  put every `nvidia/*/lib` dir on the loader path *before* any run using the binary:
  ```bash
  export LD_LIBRARY_PATH="$(find /usr/local/lib/python3.13/dist-packages/nvidia \
    -maxdepth 2 -type d \( -name lib -o -name lib64 \) | tr '\n' ':')/usr/lib64-nvidia"
  ldd /content/audiocpp_inference/bin/audiocpp_cli | grep 'not found' || echo OK
  ```
  `ldd` reporting no `not found` lines = the binary will load. (`/usr/bin/time` being
  present is a separate, already-documented prerequisite; exit 127 here is the loader.)
- **Encoded 2026-10-06 (no longer a per-session ritual):** `INFERENCE/cuda_loader_path.sh`
  resolves the pip `nvidia/*/lib` dirs; `INFERENCE/run_one.sh` — the single choke point
  every batch driver (`generate.py`, the `*_sweep.sh`, `maqam_lyric_swap.py`) goes
  through — sources it before invoking `$BIN`, and `bootstrap/setup.sh --inference`
  sources it, `pip install`s the `-cu12` wheels if absent, and **fails the verify** if
  `ldd` still shows `not found`. It also persists the path in `~/.bashrc` for
  interactive shells. The manual block above is now only for ad-hoc `ldd`/direct-CLI use;
  the run path no longer needs a hand-exported `LD_LIBRARY_PATH`.

## 2026-10-05 — CUDA-13 image: orphan cuDNN libs break VAE encode (`CUDNN_STATUS_SUBLIBRARY_VERSION_MISMATCH`)

- **Fact:** the base image preinstalls cuDNN libs under
  `.../dist-packages/nvidia/cudnn/lib` that are **not** part of the pinned
  `nvidia-cudnn-cu13==9.20.0.48` wheel (`libcudnn_engines_tensor_ir.so.9`,
  `libcudnn_ext.so.9`). pip's uninstall only removes files in the old RECORD, so a
  `--force-reinstall` leaves them; the 9.20 frontend loads the stale file and aborts.
- **Failure prevented:** training dies at step 0 during the latent-cache build, in the
  VAE `conv1d`: `RuntimeError: CUDNN_BACKEND_TENSOR_DESCRIPTOR cudnnFinalize failed …
  CUDNN_STATUS_SUBLIBRARY_VERSION_MISMATCH`. `setup.sh`'s verify (torchaudio decode)
  never exercises a cuDNN conv, so it reports all-`[ok]` on a broken box.
- **Correct pattern:** remove the libs not listed in the wheel RECORD, then verify a
  GPU conv:
  ```bash
  PIP=/usr/local/lib/python3.13/dist-packages/nvidia/cudnn/lib
  RECORD=$(ls /usr/local/lib/python3.13/dist-packages/nvidia_cudnn_cu13-*.dist-info/RECORD)
  for f in "$PIP"/libcudnn*.so.9; do grep -q "nvidia/cudnn/lib/$(basename "$f")," "$RECORD" || mv "$f" /tmp/; done
  python -c "import torch,torch.nn.functional as F; F.conv1d(torch.randn(1,64,200,device='cuda'),torch.randn(64,64,3,device='cuda'),padding=1); print('ok')"
  ```
  Permanent fix belongs in `bootstrap/setup.sh` (prune non-manifest files after the
  torch install). Files moved, not deleted, so a bad guess is reversible.

## 2026-10-05 — `gsutil rsync` to a local path needs the destination directory to already exist

- **Fact:** both `gsutil rsync` and `gcloud storage rsync` require the **local destination
  directory to exist first**; a non-existent local path is parsed as a bucket/object and
  rejected with `CommandException: arg (.\pron_eval_app) does not name a directory, bucket,
  or bucket subdir.` (Observed on Windows PowerShell fetching the eval app; same on Linux.)
- **Failure prevented:** a handed-over block that ran `gsutil -m rsync -r gs://…/dir .\dir`
  without creating `.\dir` fetched **nothing** (exit 0, destructive-looking), and the follow-up
  `(Get-ChildItem …).Count` printed `0` — looks like an empty source, is really a missing dest.
- **Correct pattern:** create every local destination first, then rsync; prefer an absolute
  destination path:
  ```powershell
  New-Item -ItemType Directory -Force -Path "$Work\pron_eval_app" | Out-Null
  gsutil -m rsync -r "$Bucket/tools/pron_eval_app" "$Work/pron_eval_app"
  ```
  (`mkdir -p <dst>` on Linux. The `.\dst` form works once `dst` exists.)

## 2026-10-06 — Restoring checkpoints from GCS randomizes ctime → auto-resume picks the wrong checkpoint

- **Fact:** ai-toolkit's `get_latest_save_path` (`BaseSDTrainProcess.py:857`) selects
  `max(glob("<name>*.safetensors"), key=os.path.getctime)` — **ctime, not the step
  number**. `gcloud storage rsync` re-creates every file at restore time (in parallel),
  so all ctimes are ~identical and the "newest" pick is arbitrary. Observed: a restore of
  ckpts `_1500…_19500` resumed from **`_000009000`** instead of `_19500`.
- **Failure prevented:** a resume that silently restarts ~10,500 steps back (and would
  overwrite newer checkpoints/optimizer on the next save).
- **Correct pattern:** after restoring, force the newest checkpoint to be the max by ctime
  (both `touch` and `chmod` bump ctime — verified 2026-10-06; what matters is re-stamping in
  **ascending step order** so the newest is unambiguous), then verify with the exact glob:
  ```bash
  cd /content/ai-toolkit/output/<run>
  chmod 644 <run>_0000NNNNN.safetensors   # the highest step
  python - <<'EOF'
  import glob,os; name='<run>'
  paths=[]
  for p in [f"{name}*.safetensors",f"{name}*.pt",f"{name}*"]: paths+=glob.glob(p)
  print(max([p for p in paths if os.path.exists(p)],key=os.path.getctime))
  EOF
  ```
  (Durable fix belongs in `bootstrap/setup.sh` / a restore helper.)
- **Encoded 2026-10-06:** `bootstrap/restore_run.py` rsyncs
  `<base>/<run-name>/output` → the local output root and then re-stamps ctime order
  (same logic as `bootstrap/rename_run.py`), verifying the pick before you resume. Use it
  instead of a bare `rsync` + hand-`chmod`; it also creates the local destination first.

## 2026-10-06 — `grep -m1 'Found step'` on an appended log returns the *stale* line; the restored WAL loss_log.db can be malformed

- **Fact (part 1):** `run.py -l <log>` **appends**. After a re-run, `grep -m1 'Found step'`
  matches the *oldest* occurrence (the previous attempt), so a correct resume (19500) reads
  as a wrong one (9000). Use the **last** occurrence: `grep 'Found step' <log> | tail -1`,
  or grep the newest `#### IMPORTANT RESUMING FROM … ####` block.
- **Fact (part 2):** the backup daemon rsyncs `loss_log.db` + its `-wal`/`-shm` as three
  independent objects at slightly different times; the captured main db can be mid-checkpoint
  and restore as `database disk image is malformed`. The run then dies in
  `logging_aitk._prune_future_steps` (`DELETE FROM steps WHERE step > <resume>`).
- **Failure prevented:** a resume that appears to start then crashes on its first loss commit,
  with the "wrong step" red herring above.
- **Correct pattern:** repair by salvaging the readable prefix (steps ≤ resume are usually
  intact; only the "future" rows are corrupt), rebuild, install:
  ```bash
  sqlite3 bad.db ".recover" >/dev/null 2>&1 || true   # may lack sqlite_dbpage vtab
  sqlite3 clean.db <<'SQL'
  CREATE TABLE steps(step INTEGER PRIMARY KEY, wall_time REAL NOT NULL);
  CREATE TABLE metric_keys(key TEXT PRIMARY KEY, first_seen_step INTEGER, last_seen_step INTEGER);
  CREATE TABLE metrics(step INTEGER NOT NULL,key TEXT NOT NULL,value_real REAL,value_text TEXT,
                       PRIMARY KEY(step,key), FOREIGN KEY(step) REFERENCES steps(step) ON DELETE CASCADE);
  CREATE INDEX idx_metrics_key_step ON metrics(key,step);
  ATTACH 'bad.db' AS src;
  INSERT INTO steps SELECT * FROM src.steps WHERE step<=<resume>;
  INSERT INTO metrics SELECT * FROM src.metrics WHERE step<=<resume>;
  INSERT INTO metric_keys SELECT key,first_seen_step,<resume> FROM src.metric_keys;
  SQL
  sqlite3 clean.db "PRAGMA journal_mode=WAL; PRAGMA wal_checkpoint(TRUNCATE); PRAGMA integrity_check;"
  # swap in: mv bad.db{,-shm,-wal} aside; cp clean.db <output>/loss_log.db
  ```
  Loss history is also in `<output>/tensorboard/<run>_<ts>/events.out.tfevents.*` (`loss`, `lr`)
  as a cross-check. A durable fix is for the backup daemon to `PRAGMA wal_checkpoint(TRUNCATE)`
  (or copy via the SQLite backup API) before syncing `loss_log.db`.
- **Encoded 2026-10-06:** `backup_to_gcp.py` now runs `PRAGMA wal_checkpoint(TRUNCATE)` on every
  `*.db` under each synced folder (`checkpoint_sqlite_dbs`, called in the pass loop before
  `sync`), so the main `loss_log.db` alone is a consistent snapshot. The salvage procedure above
  remains the repair path for a capture torn before this fix.

## 2026-10-06 — `gcloud storage cp -r <dir> <gs://bucket/prefix>` nests when the prefix exists

- **Fact:** when the destination prefix already holds objects, `gcloud storage cp -r <localdir>
  <gs://bucket/prefix>` copies the directory *into* the prefix (`<prefix>/<localdir>/…`) rather than
  merging its contents flat. A first upload looks correct because the prefix does not exist yet.
- **Failure prevented:** a re-blinded listening package landed nested under
  `…/listening/JARIR_QAHH_INPUT/JARIR_QAHH_INPUT/`, while the top level kept serving the superseded
  files — silently, because `cp` still exited 0.
- **Correct pattern:** to mirror a directory's **contents** flatly, glob them and keep a trailing
  slash on the destination: `gcloud storage cp -r /path/dir/* gs://bucket/prefix/`. To replace a
  package, `gcloud storage rm -r <prefix>` first, then copy the contents. Verify with
  `gcloud storage ls -l` **and** per-file hashes (`gcloud storage cat <obj> | sha256sum` vs local) —
  never trust the exit code alone.

## 2026-10-06 — `pgrep -f <pattern>` self-matches the launcher when the pattern text appears elsewhere in the same command line

- **Fact:** a detached auto-chain that guards on `pgrep -f "<pattern>"` while **also echoing the
  pattern word** (e.g. the guard message `ABORT: audiocpp_cli already active`) matches its *own*
  shell command line. The `[x]` bracket trick only protects the pattern *as written* — it does not
  help when the raw word appears somewhere else in the same command string.
- **Failure prevented:** the AR-vs-NAR auto-chain printed a false `ABORT: … already active` and
  silently never launched; the mistake was visible only by checking that the probe had actually
  started (its log line + GPU memory), not by the chain's own exit.
- **Correct pattern:** never put the literal pattern (or a message containing it) into the same
  shell invocation as the `pgrep -f`. Use the bracketed form *and* keep the unbracketed word out of
  every other string in the command; after launching a detached job, confirm it started from an
  independent signal (a fresh log line, rising `nvidia-smi` memory), not from a "not running" guard.

## 2026-10-10 — `pkill -f <pattern>` kills the *invoking* shell when the pattern text is in that shell's own command line

- **Fact:** the kill-side twin of the gotcha above. Running `pkill -f train_watchdog.py` from a shell
  whose command line *also* contains `train_watchdog.py` (e.g. an agent's `bash -c '… pkill -f
  train_watchdog.py; setsid nohup python train_watchdog.py …'`) sends SIGTERM to that bash itself.
  `pkill` excludes only **its own** PID, not its parent shell. Everything after the `pkill` in the
  same invocation never runs.
- **Failure prevented:** a "stop the old watchdog then start the new one" one-liner died at the
  `pkill`, so the replacement watchdog was never launched — leaving *no* watcher, silently, exactly
  when unattended coverage was the goal.
- **Correct pattern:** split it — kill in one invocation that contains no other reference to the
  pattern (or `kill "$(cat /path/pid)"`), then launch in a separate invocation. The `[x]` bracket
  trick does not help here because the unbracketed word appears in the launch half of the same
  command line. Verify the new watcher started from an independent signal (`pgrep -af '[t]rain_watchdog.py'`).
  Note: an **interactive** user typing `pkill -f X` is unaffected (the interactive shell's cmdline is
  just `-bash`); this bites the **agent's long `bash -c` one-liners**.

