# Repo audit — stale docs, correctness drift & workflow efficiency

*Read-only audit, 2026-09-22. Three passes: (1) documentation vs current code/layout,
(2) scripts/configs for path drift and dead keys, (3) the documented workflow for
efficiency gaps. Findings are ranked by **impact ÷ effort**; every item has the
evidence and a one-line fix. Nothing here was applied unless noted — items that need
a config/script/GPU decision are the user's call.*

Legend: **S** ≈ minutes, **M** ≈ ~an hour, **L** ≈ days. Impact: High / Med / Low.

## Priority summary

| # | Item | Type | Impact | Effort |
|---|---|---|---|---|
| 2 | Staged `scripts/` drifted from the repo and self-perpetuates (marker-gated) | correctness | **High** | S–M |
| 3 | `INFERENCE/run_one.sh` committed non-executable but docs call it directly | correctness | Med | S |
| 4 | `verification.md` audits v1 (style-only) and has no archive banner | stale doc | **High** | S |
| 5 | `docs/investigation.md` is superseded and unindexed | stale doc | Med | S |
| 6 | `docs/yue2-gguf-lora-findings.md` says no LoRA conversion is needed — wrong | stale doc | **High** | S |
| 7 | `README.md` `--inference` description predates binary/LoRA/scripts staging | stale doc | Med | S |
| 8 | `docs/FINAL_BACKUP.md` calls GCS "append-only" for the final adapter | stale doc | Med | S |
| 9 | No documented way to restore `agent_notes/current.md` on a fresh VM | workflow | **High** | S |
| 10 | `AGENTS.md` has no inference operating contract | workflow | **High** | S |
| 11 | No single "status" command across training + inference + backup | workflow | **High** | S–M |
| 12 | Batch driver uncommitted/undocumented; `PROGRESS.md` calls it a proposal | workflow | **High** | S |
| 13 | "Bring your own lyrics" has no input path and no doc section | workflow | **High** | S (doc) |
| 14 | `docs/GPU_L4_VS_A100.md` headline table still says A100 40 GB | stale doc | Low–Med | S |
| 15 | `docs/README.md` index omits 4 docs; constants table omits inference paths | stale doc | Med | S |
| 16 | No listening/evaluation runbook (protocol lives only in PROGRESS prose) | workflow | Med–High | S–M |
| 17 | `run_one.sh` alone writes no JSON sidecar (policy says every track does) | workflow | Med | S–M |
| 18 | No batch summary / truncation report | workflow | Med | M |
| 19 | `DECISIONS.md` sample-event count 12 vs 13; file:line citations drifted | stale doc | Low | S |
| 20 | `setup.sh --inference` closing banner tells you to do an unneeded build | stale doc | Med | S |
| 21 | All inference outputs dump into one flat `out/` — partition by run (datetime folder) | workflow | Med–High | S–M |

---

## P0 — Correctness (fix before the next GPU run)

### 2. Staged `scripts/` has drifted from the repo and self-perpetuates
- **Evidence.** `/content/audiocpp_inference/scripts/` (staged by `setup.sh` from GCS
  `audiocpp_inference/scripts/`, `setup.sh:113,259`) holds stale copies:
  - `run_one.sh:13,17` — `ROOT=/content/audiocpp_test` (dead path) and
    `BIN=/content/audio.cpp/build/linux-cuda-release/bin/audiocpp_cli` (not where the
    binary is staged: `setup.sh:106`).
  - `run_batch16.sh:7` / `run_batch16_resilient.sh:10` — same dead root, plus fixed
    seeds `1000-1003` that no longer match any documented batch.
  - `backup_live.py:31` — `/content/audiocpp_test`, GCS `audiocpp_gguf_test`
    (retired prefix); it is superseded by `backup_to_gcp.py --inference`.
  - `duration_cap.py` — the old, superseded centre fit. Fixed at the source:
    `INFERENCE/duration_cap.py` is now canonical in the repo and `run_one.sh`
    calls it, so the staged copy is no longer consulted (2026-09-22).
- **Why it persists.** `job_audiocpp_binary` is marker-gated (`setup.sh:247-260`), so
  on a warm VM *nothing* re-stages — the cheap `prompts/`/`scripts/` rsyncs are
  skipped too, and the repo's canonical `INFERENCE/run_one.sh` is never the staged
  copy. `backup_to_gcp.py:107` then mirrors the stale `scripts/` back to GCS.
- **Fix (S–M).** Pick one source of truth: the repo `INFERENCE/` wins, GCS
  `scripts/` is a mirror. Split the marker so `prompts/`+`scripts/` always rsync and
  only the 350 MiB binary is marker-gated; regenerate the GCS `scripts/` prefix
  (keep `run_batch_random.sh`; delete `run_one.sh`, `run_batch16*.sh`,
  `backup_live.py`, `duration_cap.py` — the repo `INFERENCE/` copy is now canonical).

### 3. `INFERENCE/run_one.sh` is committed non-executable
- **Evidence.** `git ls-files -s INFERENCE/run_one.sh` → mode `100644`; the working
  tree is `-rw-r--r--`. Docs invoke it directly (`docs/INFERENCE.md:14,68`), which
  fails with `Permission denied` (the batch masks this by calling `bash "$RUN"`).
  Same for `bootstrap/setup.sh`, `bootstrap/github_auth.sh`.
- **Fix (S).** `git update-index --chmod=+x` those files, or document `bash …`.

---

## P1 — Stale documentation (add a banner or correct)

### 4. `verification.md` audits v1 and reads as current
- `verification.md:3,44` describe `./yue2_dataset` as style-only with empty lyrics —
  that is **v1**, archived as `yue2_dataset_v1_style_only_obsolete`. The live dataset
  is v2 (lyric-conditioned). A fresh agent would mis-diagnose any lyric issue.
- **Fix (S).** Add an `ARCHIVED — audits the v1 style-only build` banner (mirror
  `TRAINING_ANALYSIS/v1_nolyrics_archived/ANALYSIS.md:3-10`). *(Applied in this commit.)*

### 5. `docs/investigation.md` is superseded and unindexed
- `docs/investigation.md:15-17,76-77` conclude "prefer ccache over a prebuilt binary"
  and `:90,116` cite `/content/audiocpp_test`. The adopted path is the **prebuilt
  binary** (`setup.sh:246-261`, `docs/INFERENCE.md:100-107`), and the path bugs it
  listed were fixed in the same commit that added the file.
- **Fix (S).** Mark `SUPERSEDED`, point at `docs/INFERENCE.md` +
  `docs/audiocpp_gpu_arch_builds.md`. *(Applied in this commit.)*

### 6. `docs/yue2-gguf-lora-findings.md` says no LoRA conversion is needed
- `:7-8,101` assert "you probably do not need to convert or merge anything". Wrong for
  this file: the fused ai-toolkit LoRA must be split to unfused adapters by
  `converter/convert_aitoolkit_yue2_lora.py` (`DECISIONS.md:410-420`), and
  `INFERENCE/run_one.sh:50-53` loads the converted AR/NAR files. Its example also uses
  `yue2-3b-q8_0.gguf`, which `setup.sh --inference` never stages (bf16 only).
- **Fix (S).** Retraction banner citing `DECISIONS.md`; fix the example.
  *(Applied in this commit.)*

### 7. `README.md` `--inference` description is pre-`53b8b2b`
- `README.md:67-70` says `--inference` only clones audio.cpp and pre-warms the model.
  It also stages the prebuilt binary, the converted LoRA, and `prompts/`+`scripts/`
  (`setup.sh:235-261`), and its verify block hard-fails without them.
- **Fix (S).** List the staged artifacts; link `docs/INFERENCE.md`.

### 8. `docs/FINAL_BACKUP.md` calls GCS "append-only" for the final adapter
- `:65-67` (and `:147`) say a superseded checkpoint is safe because GCS is
  append-only. True for step-suffixed checkpoints, **false** for the un-suffixed
  `akbar_arabic_rock_lora.safetensors`, which a same-name resume overwrites
  (`DECISIONS.md:98-109`).
- **Fix (S).** Qualify the wording.

### 14. `docs/GPU_L4_VS_A100.md` headline table says A100 40 GB
- `:37,42,43` use A100-40GB (1,555 GB/s) while `:92-93` and `DECISIONS.md:137` record
  the Colab A100 actually used as **SXM4-80GB** (2,039 GB/s).
- **Fix (S).** Update the column or label it as the pre-run assumption.

### 15. `docs/README.md` index and constants table
- The index omits `text_to_duration_formula.md` (referenced by `INFERENCE.md:74`),
  `LIVE_STATUS.md`, and the two superseded research docs; the constants table covers
  training paths only — no `audiocpp_inference` root/prefix or `agent_notes` note.
- **Fix (S).** Add rows + an inference block to the constants table. *(Partly applied
  in this commit: index now lists this audit and the missing docs.)*

### 19. `DECISIONS.md` numeric/line drift
- `DECISIONS.md:315` says "12 sample events"; `sample_start_step: 0`,
  `sample_every: 250`, `steps: 3000` (`config:65,127,128`) → **13**, matching
  `TRAINING_ANALYSIS/ANALYSIS.md:34`. Several `file:line` citations have drifted
  (`:215`, `:239`, `:249`).
- **Fix (S).** Correct the count; refresh citations (the file already warns they drift).

### 20. `setup.sh --inference` closing banner
- `setup.sh:442-453` still says audio.cpp was "CLONED but NOT built" and tells you to
  run `build_linux.sh` (~21 min), although `job_audiocpp_binary` already staged the
  prebuilt binary at `$AUDIOCPP_BIN_LOCAL`.
- **Fix (S).** Rewrite the banner; keep `build_linux.sh` only for a different GPU arch.

---

## P2 — Workflow efficiency (high impact / low effort)

### 9. Restore `agent_notes/current.md` on a fresh VM
- `AGENTS.md:15` makes it the copy-free handoff surface, `backup_to_gcp.py` pushes it,
  but **nothing pulls it** — `setup.sh` restores only the dataset, and no runbook has
  the command. A fresh agent starts blind to "what happened / exact commands / next".
- **Fix (S, doc or script).** Add to `START.md`/`PAUSE_RESUME.md`/`INFERENCE.md`, or a
  marker-gated `setup.sh` job:
  ```bash
  mkdir -p /content/maqamrock-yue2-lora-finetuning/agent_notes
  gsutil -m rsync -r "$GCP_BACKUP_BASE/<run-name>/agent_notes" \
    /content/maqamrock-yue2-lora-finetuning/agent_notes
  ```

### 10. Give `AGENTS.md` an inference contract
- `AGENTS.md` is training-only: no mention of `audiocpp_inference`, `run_one.sh`,
  `_runs_status.log`, per-track JSON sidecars, or the **manual-execution /
  report-from-files** policy that `DECISIONS.md` records (and `PROGRESS.md` says
  should be written into `AGENTS.md`). The OOM-summary failure mode can recur.
- **Fix (S, doc).** Add an "Inference" section: setup path, observability sources,
  "agent writes commands to `current.md`, does not run GPU work while training may be
  active", and "quote the file line, don't paraphrase".

### 11. One `status` command for the whole job
- "How's it going" currently means assembling many reads (training pid + `monitor_loss`
  + logs + two sidecar pids + GCS freshness +, for inference, `_runs_status.log` and N
  JSONs). Prime source of the "GPU looks idle" misread.
- **Fix (S–M).** `status.py`: training step/rate/liveness, sidecar pids, last backup
  timestamp, local-vs-GCS freshness, disk free, and (if present) batch progress
  `n/16` + failures + any `truncated 1`. Reference it from AGENTS/MONITOR/INFERENCE.

### 12. Commit and document the batch driver
- `/content/audiocpp_inference/scripts/run_batch_random.sh` (random seeds, resumable,
  per-track sidecars) runs the current batch but is **untracked**, undocumented, and
  `PROGRESS.md:575-584` still calls a batch driver a proposal. The benchmark in
  `docs/INFERENCE.md:131` can't be reproduced from the repo.
- **Fix (S, user's call).** Commit it under `INFERENCE/`, document usage + the
  `out/batch_<date>_seeds.tsv` format + the exact background launch line, and reconcile
  `PROGRESS.md`.

### 13. "Bring your own lyrics" has no path in and no docs
- `INFERENCE/run_one.sh:22-23` hardcodes `prompts/<Maqam>_{style,lyrics}.txt`; there
  is no lyrics argument, no documented mapping, and no note that "maqam" selects a
  style/lyric pair on one fixed LoRA.
- **Fix (S doc; M code).** Add a section to `INFERENCE.md` (drop location, mapping,
  seed convention, worked batch command). Optionally add `--lyrics`/`--style` args
  later (proposal only).

### 16. A listening/evaluation runbook
- The actual arbiter of the project is by-ear evaluation; the protocol (word-by-word
  probes, maqam↔suffix mapping, step-0 control, enjambment caveat) lives only in
  PROGRESS prose. Output naming differs between the PyTorch path and audio.cpp.
- **Fix (S–M).** `docs/LISTENING.md`: output locations, filename conventions, protocol
  checklist, and the "quote file lines" rule.

### 17. Sidecar coverage / 18. batch summary
- Only `run_batch_random.sh` writes a JSON sidecar; a manual `run_one.sh` run loses its
  seed/provenance (`DECISIONS.md` policy says every track gets one). And `truncated`
  is only visible by opening logs — no summary.
- **Fix (S–M / M).** Move sidecar writing into `run_one.sh`; add
  `INFERENCE/summarize_batch.py <seeds.tsv>` printing idx/maqam/seed/cap/exit/duration/
  truncated/wav-sha and flagging truncated rows.

### 21. Partition inference outputs by run — one flat `out/` is not okay *(user-requested)*
- **Problem.** Every `run_one.sh`/batch writes into the single directory
  `/content/audiocpp_inference/out/`, with no run scoping. It currently holds **35 WAVs**
  from several unrelated attempts (the 2026-09-22 16-track batch, the seed-1 set, the
  `cap*` experiments), all mixed together. `out/` can only be untangled by cross-
  referencing a TSV by hand, and `backup_to_gcp.py --inference` mirrors that same flat
  prefix to GCS. You cannot look at a file and know which run/batch produced it.
- **Fix (S–M).** Give each run/batch its **own datetime-stamped folder**, e.g.
  `out/<YYYYMMDD-HHMMSS>_<label>/` (`out/20260922-1537_random16/`), containing that
  run's WAVs, JSON sidecars, `*.log`, `*_time.txt`, `*_gpu.csv`, its seeds TSV, and a
  batch summary (`_runs_status.log`). Parameterize the output root in `run_one.sh` +
  `run_batch_random.sh` (env var such as `OUT_DIR`, or a driver arg) so the driver
  creates the folder and points every track at it; keep a tiny `out/latest` pointer
  (symlink or one-line text file) for convenience. `backup_to_gcp.py --inference` then
  mirrors each run folder as a self-contained unit. Filenames can keep the `<Maqam>_<seed>`
  convention inside the folder.
- **One-time cleanup.** The current flat `out/` mixes ~19 older renders that are not
  needed; archive or delete them after the new layout lands (GCS keeps its copies).
- **Pairs with** #11 (a `status` command can then report "current run folder") and #18
  (the summary lives inside the run folder).
- **Impact: Med–High · Effort: S–M.**

---

## Open decisions (user's call — not applied)

- Commit the inference tooling that is currently GCS-only: `run_batch_random.sh`,
  `converter/convert_aitoolkit_yue2_lora.py` (without these, inference isn't
  reproducible from the repo; `duration_cap.py` is now in the repo).
- Whether to re-run the 5 truncated tracks (and tracks 14–16 of the running batch) at
  the corrected cap.
- Whether extending training past step 3000 (see `DECISIONS.md`'s extension entry) —
  unrelated to this audit, still open.
