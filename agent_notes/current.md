# current.md — handoff surface (overwritten each turn; not a source of truth)

## NEXT SESSION → design & run the `jarir_lever_probe` listening evaluation
_Written 2026-10-07 ~06:50Z at session end. **The VM is being disconnected**, so next session
starts on a FRESH VM — re-stage from GitHub + GCS (see "Fresh-VM resume")._

### Where we are
The **scale-tier probe is done** — 17/17 WAVs, all `exit 0`, none truncated, mirrored to GCS.
Nothing is running here (sidecars aside). The open item is the **listening evaluation**: we have
NOT started it; the plan is to design it next session (blind vs labeled, rubric, tooling, who rates).

### What the probe compared
One fixed song `jlv_scale_ref`, seed `20261011`, cap 8000, `cot=off`, attention=flash. Adapter =
`qahh_a0p1` (current α0.1 merge of `quran_ahh_r8` rank32 into v2). 9 scale arms:

| arm | AR scale | NAR scale | extra request opt | isolates |
|---|---|---|---|---|
| v2_1.0_1.0 | 1.0 | 1.0 | — | v2 style only, no Quran donor (reference/ceiling) |
| qa_1.0_1.0 | 1.0 | 1.0 | — | both experts full (current baseline) |
| qa_0.5_1.0 | 0.5 | 1.0 | — | cut merged-AR (prosody), keep NAR (**leading hypothesis**) |
| qa_1.0_0.5 | 1.0 | 0.5 | — | keep AR, cut NAR (attribution) |
| qa_0.0_1.0 | 0.0 | 1.0 | — | AR off, NAR full (base AR + quran NAR) |
| qa_0.5_1.0_rp1.4 | 0.5 | 1.0 | `semantic_repetition_penalty=1.4` | attack madd/loops |
| qa_0.5_1.0_t0.8 | 0.5 | 1.0 | `semantic_temperature=0.8` | less prosodic wander |
| qa_0.5_1.0_g1.0 | 0.5 | 1.0 | `guidance_scale=1.0` | let base voice through |
| qa_0.5_1.0_notrigger | 0.5 | 1.0 | `--no-trigger` | domain switch (drop `arabmaqamrock `) |

Plus the **prompt tier** (8 tracks, Tier 1/3: prompt wording / lyric canonicalization / merge donor)
under `.../jarir_lever_probe/prompt/` — separate axis, evaluate if wanted.

### Evidence (checkable)
- Driver log `done (rc_total=0)` at **06:20:12Z** (`/content/logs/jarir_lever_all.log`, mirrored to GCS `logs/`).
- Per-arm `batch_summary.txt` (exit/wall/dur/trunc), `_knob.json`, and per-track `.json/.log/_time.txt`.
- The 5 arms rendered this session — all **`trunc=no`**:
  `qa_0.0_1.0` 10:49/269.9s · `qa_0.5_1.0_rp1.4` 10:09/197.9s · `qa_0.5_1.0_t0.8` 10:49/209.3s ·
  `qa_0.5_1.0_g1.0` 10:21/266.8s · `qa_0.5_1.0_notrigger` 10:25/196.1s.
- GCS holds **17 WAVs** (`<base>/audiocpp_inference/out/jarir_lever_probe/**`); `_failed.log` empty.

### The evaluation — to DISCUSS next session
Open decisions: **blind vs labeled**; **absolute rating** (`rating_app`) vs **pair-wise A/B**
(`INFERENCE/prepare_ab_eval.py` / the `ab-blind-eval` skill); the **rubric** (diction/pronunciation,
maqam/tune accuracy, prosody & madd, mix, artifacts/loops, keep?); **who** rates; and the decision the
eval must produce (which lever (if any) goes into the production v2+pron merge). n=1 track per arm →
the read is qualitative, not statistical.

### Tooling ready
- **rating_app** (`INFERENCE/rating_app/`, also in GCS `tools/rating_app/`): single-file Flask; asks
  for the track folder; configurable criteria; Markdown export. `--port` is now a **preference**
  (auto-picks the next free port if 5000 is busy; `--strict-port` opts out). Windows: `py -m pip install flask; py app.py`.
- **`INFERENCE/prepare_ab_eval.py`** + `ab-blind-eval` skill for a blinded package (renamed/randomized A/B/C).

### Fresh-VM resume (listening only — no GPU/render needed)
```
set -a; . /root/.secrets.env; set +a
cd /content/maqamrock-yue2-lora-finetuning
git fetch origin pron-lora-long-aya && git checkout pron-lora-long-aya && git pull --ff-only   # HEAD 5315ad4
mkdir -p /content/audiocpp_inference/out/jarir_lever_probe          # dest must exist first (gsutil rsync)
gsutil -m rsync -r "$GCP_BACKUP_BASE/audiocpp_inference/out/jarir_lever_probe" \
                  /content/audiocpp_inference/out/jarir_lever_probe
```
To listen on your own machine, just download that run folder from GCS and point `rating_app` at it.

### Environment gotchas that will recur
- **Do NOT run `bootstrap/setup.sh`** on a VM whose harness is OpenCode **2.0.24**: its `job_opencode`
  runs `curl opencode.ai/install | bash` and downgrades to **1.18.35**, which can't read the V2-schema
  DB → CLI + web show "configure provider" with everything grayed. Recover with
  `cp /proc/<server-pid>/exe /root/.opencode/bin/opencode` (24→2.0.24 verified).
- On 2.0.24 the web UI is `opencode pair` (there is **no** `opencode web`); service listens on `0.0.0.0:49374`.
- `gsutil rsync` aborts unless the **destination directory already exists**.

### Facts
- branch `pron-lora-long-aya` @ **`5315ad4`** (pushed; origin == local). Recent: `415e236` rating_app
  auto-port, `5315ad4` agent_notes.
- `$GCP_BACKUP_BASE` = `gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning`.
- GCS run prefix: `<base>/audiocpp_inference/out/jarir_lever_probe/`.
