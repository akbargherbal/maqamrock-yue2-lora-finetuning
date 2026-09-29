# current

_Updated 2026-09-29 (Colab VM). The guide-conditioned batch is **mid-run**: bootstrap done,
adapter staged + sha256-verified, **phase 1 done (`score.abc=yes`)**, `a0_cotoff` rendering.
Durable analysis: `docs/music-cover-feasibility.md` **§11**. Branch `music-cover` @ `5ca4c71`._

## 0. Verified state this session

- **Env:** Colab. GPU **Tesla T4**, in use by the render. Disk 188 GB free at bootstrap.
- **Bootstrap** `bash bootstrap/setup.sh --inference`: **8/8 jobs `[ok]`, total 40 s**, no
  `[FAIL]`. Staged `bin/audiocpp_cli` (350 MB sm_75/T4), `models/Yue2-3B-GGUF/` (7.26 GB
  bf16 + VAE + sidecars), v2 LoRA pair, `prompts/`(8) + `scripts/`(6), GNU `time`.
- **Candidate adapter** `--stage`: `/content/converter/out/qfinal_a0.3/` — AR sha256
  **`0169e5a0ef7d4734…`** (matches the notes' `0169e5a0…`).
- **Guide route = B1** (v2's own `score.abc`; phase 1 exported it).
- **Render** (started 13:48 UTC), driver detached, log `/content/logs/v2abc.log`:
  - phase 1 `v2_plan_…` → `score.abc=yes` (done ~5 min);
  - `a0_cotoff` **END exit=0** (13:53:37 → 14:02:26); `a1_cotfull_noabc` running; then
    `a2_cotfull_abc`, `ref_v2_cotoff`. ~6.5–9 min/arm on a T4.
- **Backup daemon** `python3 backup_to_gcp.py --inference` running (mirrors every **5 min**,
  `--interval-minutes` default `5.0`).
- **`gpu_logger.py`** = n/a (training-only; correlates with `loss_log.db`).
  **`vm-continuity`** loop running, `status` OK. Git `music-cover` == `origin`.

## 1. The render — how it was launched (already running)

`terminal: detached` — survives Ctrl+C / closing the tab.

```bash
cd /content/maqamrock-yue2-lora-finetuning
setsid nohup python3 backup_to_gcp.py --inference > /content/logs/backup_inference.log 2>&1 & disown
setsid nohup bash INFERENCE/v2_abc_to_qfinal.sh > /content/logs/v2abc.log 2>&1 & disown
#   watch:  tail -f /content/logs/v2abc.log
#   stop:   pkill -f 'v2_abc_to_qfinal.sh'      (re-runnable; overwrites its own arms)
#   resume: re-run the same line
```

Outputs (VM): `/content/audiocpp_inference/out/v2_abc_to_qfinal_seed4148240095/`.

## 2. On my local machine — pull the run output (after it finishes)

`backup_to_gcp.py --inference` maps **`/content/audiocpp_inference/out` →
`audiocpp_inference/workspace/out`** (sectioned layout). So the new arms land at:

```bash
gsutil -m rsync -r 'gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/audiocpp_inference/workspace/out/v2_abc_to_qfinal_seed4148240095' ./v2abc_tracks
```

Check it's actually there first (each arm appears within ~5 min of its WAV settling):

```bash
gsutil ls 'gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/audiocpp_inference/workspace/out/v2_abc_to_qfinal_seed4148240095/'
```

Add `-d` (`gsutil -m rsync -r -d …`) for a true local mirror; omit it to be safe.

**Previous round's blinded package** (the A–E mp3s already scored) lives under `listening/`,
**not** `workspace/out/`:

```bash
gsutil -m rsync -r 'gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/listening/VERBATIM_HIJAZ_LYRIC_ADHERENCE_INPUT' ./verbatim_blind
#   do not open KEY_open_after_listening.txt until after scoring
```

**Previous round's raw tracks** (what the earlier command pulled):

```bash
gsutil -m rsync -r 'gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/audiocpp_inference/workspace/out/verbatim_hijaz_seed4148240095' ./verbatim_tracks
```

A **new blinded package for these four arms does not exist yet** — build it after the render
(`INFERENCE/prepare_ab_eval.py`, skill `ab-blind-eval`; next unused blinding seed, e.g.
`20260930` — `20260928`/`20260929` are used), then it goes to `listening/<NAME>/` on GCS.

## 3. Then — the verdict

Listen `a0` vs `a2`: does `a2` keep v2's arrangement **without** losing pronunciation? If
`a2` pronounces like `ref_v2`, the AR-override conflict is real (§11.3) and only the blocked
`semantic_prefix` route can thread it; if `a2 ≈ a0`, the guide did nothing. Blind the four
arms for a fair call — there is **no objective arrangement metric**. Cross-check: rendered
durations/frame counts (an injected repeat lengthens the plan).

## 4. Session side-work on the VM (non-GPU, done 2026-09-29)

- **Docs reconcile** (`docs-reconciler`): first pass flagged 11 (0.9 %), all `missing_path`.
  Root cause: `manifests/workspace_manifest.json` was **deleted in `528f573`** while
  `tests/test_suno_to_songs.py` (10 tests) and 3 live docs still referenced it — the tests
  were **failing**. **Restored** the fixture from `528f573^` (70 KB, 16 tracks): all 17
  tests pass; the 6 doc claims resolve with **no prose edits**. `SOURCE_OF_TRUTH.md:33`
  path qualified; 3 doc-scoped entries added to
  `skills/docs-reconciler/references/unverifiable.txt`. Re-verify: **11 → 1 flagged**
  (residual `docs/music-cover-feasibility.md:313` `KEYS.txt`, declined).
  Logged in `RECONCILIATION_LOG.md`.
- **Graph:** `uv tool install graphifyy` (+ `graphify-out/.graphify_python`); `graphify
  update .` → 1125 nodes / 2207 edges at HEAD `5ca4c71`; `status.py` says
  **`graph: fresh at HEAD 5ca4c71`**. Semantic `/graphify --update` not run (no skill here).
- **Uncommitted:** `manifests/workspace_manifest.json` (restored, untracked),
  `RECONCILIATION_LOG.md`, `SOURCE_OF_TRUTH.md`, `unverifiable.txt`, this file, plus the
  graph rebuild (`graphify-out/*`, and the 0.9.70→0.9.71 cache churn). Commit when ready.

## 5. Pointers

- Feasibility: `docs/music-cover-feasibility.md` §11 (this batch) · §3 (α tradeoff) · §5
  (B1/B2) · §10 (last round) · §11.3 (the three risks).
- Adapters/identity: `docs/LORA_INVENTORY.md`, `docs/PRON_LORA_MERGE.md`.
- Runbook: `docs/INFERENCE.md`; blind packaging: skill `ab-blind-eval`.
- GCS layout: `backup_to_gcp.py` `INFERENCE_TARGETS`; `docs/GCP_ORGANIZATION_PLAN.md`.
- This file is a handoff surface, not authority — re-derive state from §0's artifacts/logs.
