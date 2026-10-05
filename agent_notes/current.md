# current

## State @ 2026-10-05 10:59Z — Phase 2 knob probe **COMPLETE (20/20, 0 failures)**

> **Session paused.** The user is disconnecting this VM and will return **after scoring the 20
> tracks with `pron_eval_app`** (Windows/PowerShell block below). This handoff is pushed to
> `pron-lora-long-aya` so it survives the disconnect; GCS already holds the audio + the app.

Branch `pron-lora-long-aya` @ `f3762fa` (+ local-only `agent_notes/current.md`). T4 (sm_75,
native binary). Fresh `/content` → `setup.sh --inference` all `[ok]` (35s).

### Result

`INFERENCE/quran_knob_probe.sh` — **20/20 tracks, all `exit=0`, 0 failures, no truncations.**
- 2 arms (`c4500`,`c9000`) × 2 scripts (`uthmani`,`simple`) × 5 knobs
  (`g1.0 g1.5 t0.8 rp1.4 pw100`), held-out **2:255**, seed `20261004`, cap 7500.
- Wall: **first track 10:16:27Z → done 10:59:28Z = ~43 min** (per-knob 6:57 / 8:08 / 9:13 /
  8:56 / 8:23). Audio durations 40–87 s each.
- Local: `/content/quran_knob_probe/quran_knob_<cfg>/` (4 tracks each). Run log:
  `/content/logs/quran_knob_probe.log`.
- **GCS (authoritative): `$GCP_BACKUP_BASE/quran_knob_probe/`** — 20/20 WAVs + all sidecars +
  `quran_knob_probe.log` (218.66 MiB). Sample sha256 verified vs local (`90983228…`).
- Anchor (default knobs) is NOT here: `/content/audiocpp_inference/out/20261005-072738_quran_pt_probe/`.

### ⚠ Launch gotcha (fixed) — export `LD_LIBRARY_PATH`

First launch (10:14:57Z) failed **every** track instantly `exit=127`:
`libcublas.so.12: cannot open shared object file` (CUDA-12 binary on a CUDA-13 image;
`docs/COMMAND_HANDOVER_GOTCHAS.md` 2026-10-04). The handover line omitted the export.
**Corrected launch / resume** (re-running the raw line re-fails):
```bash
cd /content/maqamrock-yue2-lora-finetuning
export LD_LIBRARY_PATH="$(find /usr/local/lib/python3.13/dist-packages/nvidia \
  -maxdepth 2 -type d \( -name lib -o -name lib64 \) | tr '\n' ':')/usr/lib64-nvidia"
setsid nohup bash INFERENCE/quran_knob_probe.sh > /content/logs/quran_knob_probe.log 2>&1 & disown
```
`_failed.log`'s `g1.0 exit=1` line is that **pre-fix** attempt — ignore.

### Eval app now handles the nested knob layout — `INFERENCE/eval_app/` (`f3762fa`)

Old app globbed `*.wav` flat and keyed by `<arm>_<script>_<seed>` only → 0 tracks here, and
colliding arm names across knobs. Now `discover()` recurses; each track's key/identity
includes its run/knob folder (label read from that dir's `_knob.json`, e.g.
`g1.5: guidance_scale=1.5`); index sections by script→knob; report gains a `knob/run` column
and a non-binding knob verdict. Flat Phase-1 layout unchanged. Verified locally (all routes
200, POST→report, save&next, dotted name, traversal 404).
Staged: `$GCP_BACKUP_BASE/tools/pron_eval_app/`.

**Score on a CPU VM:**
```bash
mkdir -p pron_eval_app && gsutil -m rsync -r "$GCP_BACKUP_BASE/tools/pron_eval_app" ./pron_eval_app
cd pron_eval_app && pip install -r requirements.txt
mkdir -p ../quran_knob_probe && gsutil -m rsync -r "$GCP_BACKUP_BASE/quran_knob_probe" ../quran_knob_probe
python app.py --audio ../quran_knob_probe --out ../eval_out --label quran_knob_probe
```

**Windows / PowerShell (local machine):**
```powershell
# Needs Google Cloud SDK (gcloud/gsutil) + Python 3 on PATH.
#   - no `py`?          use:  python        (in all three places below)
#   - first time here:  gcloud auth login   (bucket is your own project)
#   - gsutil rsync REQUIRES the local destination dir to exist first -- mkdir, then rsync.
$Bucket = "gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning"
$Work   = "$HOME\quran_knob_eval"
New-Item -ItemType Directory -Force -Path "$Work\pron_eval_app"    | Out-Null
New-Item -ItemType Directory -Force -Path "$Work\quran_knob_probe" | Out-Null
Set-Location $Work

gsutil -m rsync -r "$Bucket/tools/pron_eval_app" "$Work/pron_eval_app"      # the app
gsutil -m rsync -r "$Bucket/quran_knob_probe"    "$Work/quran_knob_probe"   # the 20 renders
(Get-ChildItem -Recurse ".\quran_knob_probe" -Filter *.wav).Count            # expect 20

py -m pip install -r ".\pron_eval_app\requirements.txt"
py ".\pron_eval_app\app.py" --audio ".\quran_knob_probe" --out ".\eval_out" --label quran_knob_probe
# open http://127.0.0.1:5000  (Ctrl+C stops it)
```
- The app writes only under `--out` (`.\eval_out\evaluations.json`, resume-safe); **export .md**
  downloads `pron_eval_<stamp>.md` to your Downloads folder — hand that back for the verdict.
- Optional — score the default-knob anchor alongside: `gsutil -m rsync -r
  "$Bucket/audiocpp_inference/out/20261005-072738_quran_pt_probe" ".\anchor"` then a second run
  with `--audio ".\anchor" --out ".\eval_out_anchor"`.
- Index is grouped script → knob (`g1.0: guidance_scale=1.0`, …); tap wrong words, answer the
  questions, **Save & next**. Audio lives in `.\quran_knob_probe\quran_knob_<cfg>\*.wav`.

### Backup / continuity

- GCS is **current** (20/20 + log; sample sha verified). The 5-min safety-net loop was stopped
  once the authoritative upload landed. `vm-continuity` healthy (pid 7261).
- `backup_to_gcp.py` / `gpu_logger.py` daemons were not started (not needed for this run).
- **GitHub:** `f3762fa` is **1 ahead of origin, not pushed** (needs your PAT via
  `bootstrap/github_auth.sh`). `agent_notes/current.md` stays local-only.

### Next (open)

1. Score the 20 tracks with `pron_eval_app` (CPU VM) → export `.md`.
2. Blind package vs the anchor (`ab-blind-eval`); no merge before the listen.
3. Outstanding: `docs-reconciler` pass; 3 docs still say `experimental-quran-pron`.
