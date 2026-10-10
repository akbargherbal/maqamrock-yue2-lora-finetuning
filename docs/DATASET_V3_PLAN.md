# Plan — new maqam-rock dataset (438 tracks, verbatim lyrics) + next A100 run

_Status: **EXECUTED (2026-10-10).** The dataset was built, the GCS rename + upload done, and
the configs/docs/code updated. Kept as the record of the decisions. Originally written for the
request: "prepare the new dataset for `config/A100_akbar_arabic_rock_lora.yml`" (now
`config/v3_arabmaqamrock_lora.yml`) from `NEW_min_4stars_ai_music.zip`, verbatim lyrics, more
steps, better naming._

Authority note: this is a plan, not a runbook. Where it cites a fact it cites the
artifact you can re-check. *Provisional* name: "v3" (the naming section explains why
"v3" may change).

---

## 0. Verified findings (evidence first, so nothing below is a guess)

| # | Finding | How it was checked |
|---|---|---|
| F1 | The new zip is a **strict superset**: **438 = 267 existing + 171 added, 0 dropped**. 137 workspaces (was 115; +22). | matched every manifest `assigned_filename` against the zip's `unzip -Z1` audio list; set-compared old vs new on `(maqam, ws, filename, clip_id)` |
| F2 | Per-maqam track counts: **ajam 118, hijaz 107, kurd 101, nahawand 112** (v2: 72/60/62/73). | same matching |
| F3 | Audio is unchanged in kind: **mp3, 48000 Hz, stereo**; **max clip 370 s** (identical to v2; 0 clips > 983 s). So `train_window_frames: 0` (whole-song) stays inside the AR context ceiling (~983 s). | `ffprobe` over all 438 extracted files |
| F4 | The new zip contains **438 mp3 + 137 `workspace_manifest.json`**, root folder `min_4stars_ai_music/`; 0 audio files are unmatched to a manifest; 0 empty `lyrics`; 0 folder↔`vocals` maqam mismatches. | manifest ∩ zip-audio |
| F5 | **Verbatim vs v2 normalization** (what actually changes): v2 `clean_lyrics()` would **drop 117 non-section bracketed tags** (`[orchestral strings swell]`, `[Instrumental Break \| … ]`, …; 41 distinct) and **collapse 1708 section tags** carrying `\| asides` (`[Verse 1 \| powerful resonant vocals \| …]` → `[Verse 1]`). Verbatim keeps all of it. | ran the v2 cleaner over the 438 |
| F6 | Distinct lyric texts: **222 verbatim vs 204 v2-cleaned** (v2 dataset of 267 had 157). 2851 distinct normalized lyric lines. | set compare |
| F7 | All 438 lyrics carry a leading marker line — 415 `///***///`, 23 the escaped variant `///\*\*\*///` — which v2's `MARKER_RE = ^[/*\\]+$` already matches. | scan |
| F8 | **EVAL-VALIDITY (not a training blocker): 3 of the 4 held-out sample prompts are now contaminated.** Against the 438, Hijaz **18/18**, Kurd **20/20**, Nahawand **18/18** of their normalized lyric lines are in training; only **Ajam is still clean (0)**. See §4 for why this does **not** block launching training. | documented held-out normalization over `INFERENCE/yue2_eval_heldout/heldout_eval_prompts.json` |
| F9 | Clean replacement poems exist: **11–13 per maqam** (0 selected takes, e.g. 28-line Lamiyat_Alshanfara, 26-line alharith_bin_heliza). | poem-set analysis vs the 438 |
| F10 | GCS today: the dataset is the generic prefix **`…/dataset/` = 535 objects** (v2, 267 pairs). The current run lives at `…/akbar_arabic_rock_lora/`. **No `A100_*` / `L4_*` prefix exists yet.** | `gcloud storage ls` |
| F11 | A superset-equivalent naming already **decided but not executed**: `docs/GCP_ORGANIZATION_PLAN.md` (branch `music-cover`, *not* on `main`) proposes `datasets/v2_style_267/` + `runs/style_v2/`. Only `audiocpp_inference/` was actually re-sectioned. | read on `music-cover` + bucket `LAYOUT.json`/`README.txt` |
| F12 | Build script for v2 is **not in the repo** (`prepare_yue2_dataset_v2.py` lives in the parent `ostris_prepare_dataset/`), and local `gcloud` is authenticated → build offline here is the established path. | `ls`, `gcloud config get-value account` |

---

## 1. Build location & tooling

- Build **offline on this local box** (as v2 was), then upload to GCS. No GPU involved.
- Input: `ostris_prepare_dataset/NEW_min_4stars_ai_music.zip` (2.5 GB, root `min_4stars_ai_music/`).
- Base script: `ostris_prepare_dataset/prepare_yue2_dataset_v2.py`.
- Tolerance check: the local `min_4stars_ai_music/` (v2 input) is the **subset** — confirmed by F1.

## 2. The dataset build (one behavioural change)

Create `prepare_yue2_dataset_v3.py` = v2 with **exactly one** change:

- Replace `clean_lyrics()` with a **verbatim** function that:
  1. strips only the **leading marker line** (`MARKER_RE`, covers both `///***///` forms — F7);
  2. keeps every remaining line byte-for-byte, **including** `[Section \| asides]` and non-section tags;
  3. (optional) collapses 3+ blank lines to one blank line — decide; v2 did this.
- **Keep `build_style_caption()` unchanged** — trigger + genre + `Maqam X.` + vocals +
  production + instrumentation + mood. This is the exact format the inference prompts and
  held-out set use; changing it is a separate experiment (see Decision **D2**).
- Keep output filenames `<maqam>_<ws>_<idx>_<clip8>.{mp3,txt}` (stable; matches v2, so any
  re-used tooling still resolves).
- Emit a verification report (counts, distinct texts, `empty_lyrics`, dropped-tag log ≈ 0,
  and a before/after caption example).
- **Portability:** v2 was never committed. Recommend committing the v3 script to the repo
  (e.g. `prepare_yue2_dataset_v3.py`) so the dataset is reproducible from the repo — a
  standing complaint in `DECISIONS.md` ("survived because it lived in a build script's
  docstring"). (Decision **D5**.)

Deliverables: `v3_arabmaqamrock_dataset/` (438 mp3 + 438 txt ≈ 2.4 GB) + a build report.

### D2 detail — what "the `styles` Suno header" is

Each manifest track has a `styles` field that is **two different things glued together**:

```
[Is_MAX_MODE: MAX](MAX) [QUALITY: MAX](MAX) [REALISM: MAX](MAX)   ← Suno render presets (metadata)
[START_ON: TRUE]                                                  ← Suno "start singing" flag
[START_ON: "هَلْ غَادَرَ الشُّعَرَاءُ"]                             ← first lyric line hint

genre: "Symphonic cinematic orchestral ballad, … 110 BPM."        ← reusable sound description
vocals: "…"  production: "…"  instrumentation: "…"  mood: "…"
```

v2 `build_style_caption()` **drops** the three header lines and keeps only the five
`key: "value"` fields, rebuilt as one line:
`arabmaqamrock <genre>. Maqam X. <vocals>. <production>. <instrumentation>. Mood: <mood>.`

D2 = do we also put the header back verbatim?
- **A (recommended): keep v2's rebuild — don't.** Grounded reasons (this is where I
  over-claimed earlier — see note):
  1. **Project artifacts document them as Suno-side controls, and strip them.**
     `prepare_yue2_dataset.py:34,57-59` describes the header as *"control tags + the literal
     lyric start … the Suno-only header + lyric hint"*, and `verification.md:39` asserts the
     built captions contain no `[Is_MAX_MODE/[QUALITY/[REALISM/[START_ON`. So excluding them is
     the existing, verified convention — not a new claim.
  2. `[START_ON: "…"]` **duplicates the first `[Lyrics]` line** verbatim.
  3. **Format consistency (the only load-bearing reason):** the inference prompts are built by
     the same `build_caption()` (`INFERENCE/suno_to_songs.py` reuses it *"byte-identically to
     the training captions"*). Adding the header to training only would make training diverge
     from generation.
- **B: keep the three header lines too.** Literal reading of "leave Suno tags alone"; cost is
  the mismatch above, and redundancy.
- **C (most literal): keep the entire `styles` field raw**, `genre:`/`vocals:` labels and all.
  Same inference-mismatch cost, plus the labels are never present at generation time.

> **Correction / honesty note.** I earlier wrote that `[Is_MAX_MODE…]` "means nothing to
> YuE2." That is an **inference, not a verified fact** — I have no source proving YuE2 ignores
> those tokens, and in fact YuE2 has no prompt *schema*: it would tokenize and encode them like
> any other text, so they are extra (likely out-of-distribution) tokens, not literally nothing.
> The honest case for A rests on (1) the project's documented convention and (3) the
> train/inference consistency requirement — **not** on a claim about YuE2 semantics. If you
> want to *know* rather than assume, it is empirically testable (a small A/B training run with
> and without the header, judged by ear), but that is its own experiment.

Whichever is chosen, the **inference prompts must be regenerated in the same format** (see D3).
Recommended: **A** (lyrics-only verbatim); the user's "Suno tags are better at instruction
following" observation is about the **lyric** `[Section | asides]` tags, which A already keeps.

Do **not** re-use v2's output dir; write fresh.

## 3. Naming — DECIDED (D1)

**Decision (user, 2026-10-10):**
- v2 dataset → **`v2_arabmaqamrock_dataset`**
- v3 dataset → **`v3_arabmaqamrock_dataset`**
- Reflected in the codebase.
- Local dir: **keep `/content/yue2_dataset`** (D4) — so the configs' `folder_path` and
  `setup.sh` `DATASET_LOCAL` are **unchanged**.
- This supersedes the `datasets/` section proposed in `docs/GCP_ORGANIZATION_PLAN.md` (that
  plan stays unexecuted for datasets; the flat, descriptive names win). Per that plan's own
  rule — *nothing is deleted in the same step that creates its replacement* — the old prefix
  is **copied + verified, and only then retired** (see §7).

Three names, and they are separate:

| Thing | Today | After |
|---|---|---|
| GCS v2 dataset | `…/dataset/` (535 obj) | **`…/v2_arabmaqamrock_dataset/`** |
| GCS v3 dataset | — | **`…/v3_arabmaqamrock_dataset/`** (876 obj) |
| Local dataset dir | `/content/yue2_dataset` | **unchanged** (`GCP_DATASET_PATH` decides content) |
| Run prefix | `…/akbar_arabic_rock_lora/` | a fresh name (unchanged plan — §6) |

**Codebase references the rename must touch** (live files; history stays history):

| File | Change |
|---|---|
| `notebooks/L4_QPRON_ArabicSuno_vscode_anywhere.ipynb` | `GCP_DATASET_PATH` → `…/v3_arabmaqamrock_dataset` |
| `agent_notes/CPU_benchmark.ipynb` | same value (it also stages the env) |
| `README.md` (L23, L103) | GCS name; also 267→438 |
| `docs/README.md` (constants, L51) | dataset row |
| `DECISIONS.md` §Dataset-Naming | replace "live keeps its plain name" with the new scheme |
| `SOURCE_OF_TRUTH.md` | dataset authority row if it names the prefix |
| `docs/PRON_LORA.md`, `docs/PRON_LORA_VERIFICATION.md`, `docs/L4_HANDOFF_TASK14C.md` | `…/dataset` → `…/v2_arabmaqamrock_dataset` (these describe the v2 path) |
| `bootstrap/setup.sh` | comments ("267 tracks", "v2's /content/yue2_dataset"); count check → 438 |
| `backup_to_gcp.py` docstring | "`dataset/` already lives under the root and is reserved" |
| bucket `README.txt` / `LAYOUT.json` | record old→new dataset names |
| `docs/text_to_duration_formula.md`, `verification.md` banners | 267 → 438 note (formula is fitted on v2; see §Verification) |

History files (`PROGRESS.md`, `RECONCILIATION_LOG.md`) keep the old name as the record of
what happened; add a dated "renamed to v2_arabmaqamrock_dataset" line where it matters.

> The local path is *not* the confusing one — the confusion is at the GCS layer, which
> `GCP_DATASET_PATH` already mediates. Keeping the local dir means **no config/bootstrap
> churn** and the pipeline is otherwise unaffected.

## 4. Held-out eval set — an evaluation-validity prerequisite, NOT a training blocker

First, what the prompts are actually for (so we don't fix the wrong thing):

- **The A100/L4 config uses none of them during training.** `disable_sampling: true` means no
  in-training samples at all (confirmed: the last three runs' analyses all read "Samples: none").
  Launching training does **not** require fixing the prompts. (Decision **D7** below.)
- They exist for **offline evaluation**: after training we render checkpoints (T4 + audio.cpp)
  and *listen*. `INFERENCE/run_one.sh` / `generate.py` condition generation on
  `prompts/<Maqam>_{style,lyrics}.txt`, not on the config block.
- They are **held out** for one reason: the run's stated goal is "*sing the provided lyrics*".
  If the eval prompt's lyrics are *in* training, the render can't distinguish "learned to sing
  a new lyric and apply the style" from "reproduced a memorized training song". For pure
  style/timbre judgment that distinction doesn't matter; for the pronunciation / lyric-following
  goal it is the whole point.

So F8 does not stop the run. It means: **if we keep an honest held-out eval, the prompts must be
rebuilt; if we don't care about the lyric-generalization claim, we can evaluate on training
lyrics and skip the rebuild.** That is a real choice, not a formality (Decision **D7**).

There is also a **drift problem** to fix regardless: the "held-out" text currently lives in
**three** places that must agree — the config `sample.samples`, `INFERENCE/yue2_eval_heldout/*`,
and the staged `audiocpp_inference/prompts/*_lyrics.txt`. This exact divergence is why the
contamination went unnoticed. Recommend collapsing to one canonical copy (the `INFERENCE/`
set) and deriving the rest, or dropping the inert config block.

Tasks:
1. Pick, per maqam, one clean poem (**0 shared normalized lines** vs all 438) from the F9
   candidate pool; prefer distinct poems per maqam, 24–28 lines.
2. Rebuild with the same caption-assembly logic as the (new) build script, so the prompts are
   byte-identical to a potential training caption of the same poem (v2's report Step 3 did
   this proof — repeat it).
3. Update: `INFERENCE/yue2_eval_heldout/heldout_eval_prompts.json`,
   `heldout_eval_report.md`, `heldout_samples_block.yml`, the config's `sample.samples`
   (A100 + L4), and any staged `audiocpp_inference/prompts/*_lyrics.txt`.
4. Re-verify 0 shared lines vs the 438 with the documented normalization; record it.
5. Also re-check `INFERENCE/evaluation_alharith.json` (already partly non-clean; Ajam was the
   clean one) and label or retire it.

**Prompt-format decision (D3) — what it means.** The eval/sample prompt's `[Lyrics]` block can
carry either tag style:

- **Plain (today):** `[Verse 1]`, `[Chorus]`, `[Intro]`, `[Outro]` — this is what the config's
  four prompts use and what v2 training taught.
- **Verbatim (v3 training):** `[Verse 1 | deep baritone vocals | clean electric guitar]` — the
  asides the new build keeps.

Because v3 training now teaches the **rich** tags, generation should match training, or the
model sees a tag distribution at generation it never trained on (a train/inference mismatch).
Recommendation: **use whatever training uses** (i.e. verbatim if D2 = lyrics-only-verbatim),
since the whole premise is that the rich tags improve instruction-following. Cheap extra: render
**both** plain and verbatim variants at eval and compare — but pick one as canonical.

D2 and D3 are **coupled**: the style block (`build_style_caption`) and the `[Lyrics]` tags form
one prompt format, and training + inference + held-out must all agree on it.

## 5. Step count

The question was whether 4500 is "proportional". With `batch_size: 1`, epochs = steps / dataset:

| run | steps | tracks | epochs |
|---|---:|---:|---:|
| v2 | 3000 | 267 | **11.24** |
| "proportional" (same epochs) | **4921** | 438 | 11.24 |
| proposal | **4500** | 438 | 10.27 |
| round-to-cadence | **5000** | 438 | 11.42 |

- **4500 is ~91 % of proportional** (it trains ~8.6 % less exposure per track than v2), not
  exactly proportional. If "same exposure" is the intent, **~4900–5000** is the number;
  **5000** lands on the 250-step save/sample cadence.
- Wall-clock (rough): v2 measured **3.42 s/step** whole-song on A100. With `disable_sampling:
  true` there is no sample tax; `ar_kl_weight: 0` removes a no-grad base forward (slightly
  faster), while longer verbatim captions add a little AR length. Estimate **≈4.5–4.8 h for
  4500–5000 steps** (vs v2's 4.73 h *including* 13 sample events).
- v2's loss was still descending at 3000 (`loss/loss` 2901–3000 = 4.845) and `ar_kl` was rising
  — "3000 was enough" was an audio verdict, not a loss plateau. So there is no hard reason to
  under-shoot; choosing 4500 vs 5000 is a time/exposure preference (Decision **D6**).

**Reason for one vs the other (D6):**
- **5000** is the *principled* choice: it reproduces v2's per-track exposure (11.42 epochs vs
  11.24) on the larger data, so any v2→v3 difference isn't confounded by "saw each track ~9 %
  less". It also lands on the 250-step checkpoint cadence.
- **4500** has **no methodological** justification — it is simply ~9 % less exposure and
  ~28 min less GPU time (≈4.28 h vs ≈4.75 h at 3.42 s/step). Pick it only to cap wall-clock.
- Recommendation: **5000**. **DECIDED (D6): 5000.**

## 5b. Verification items (not yet done)

- Caption token budget: verbatim adds asides; re-check max prompt tokens vs AR context
  (`CONTEXT 24576`) if a tokenizer is available. Expected fine (v2 captions 780–1631 tokens).
- Report whether the duration formula in `docs/text_to_duration_formula.md` (fit on the 267)
  still holds for the 438, or just note it's a v2 fit.

## 6. Config changes for the next run

Changed by the user (agent proposes, user types the launch):
- `train.steps`: `3000` → **5000** (D6, §5).
- `sample.samples`: replace the 4 contaminated prompts (§4).
- `datasets[0].folder_path`: unchanged if local path is kept (§3).
- `name:` / run prefix: a fresh name (§3) — **do not extend v2**; extending rewrites the final
  adapter (`DECISIONS.md` §Run-lifecycle).
- Already set in the A100 config and unrelated to the dataset: `ar_kl_weight: 0.0`,
  `disable_sampling: true`, `gradient_checkpointing: false`.

Latent/text-embedding cache: the caption `.txt` changes for all 438, so cached text
embeddings must be rebuilt; a fresh `/content` gives that automatically. Cache time scales
with track count (~12 min for 267 → ~20 min for 438).

**Stale-cache footgun (only on a re-used VM):** `job_dataset()` is marker-guarded
(`/content/yue2_dataset/.bootstrap_complete`) and uses `gsutil rsync` **without `-d`**. On a
same-VM re-run, delete `/content/yue2_dataset` (incl. the marker) before bootstrap, or use a
new local path (D4). On a fresh Colab VM this is a non-issue.

**Run-name coordination:** today `train_ctl.py DEFAULT_CONFIG` points at
`config/LEGACY_akbar_arabic_rock_lora.yml`, docs constants say run name
`akbar_arabic_rock_lora`, and the A100 config declares `A100_akbar_arabic_rock_lora`.
Whichever name is chosen must be identical in: the config `name:`, `log_dir`,
`train_ctl.py --config/--run-name`, `backup_to_gcp.py --run-name`, and docs/START.

## 7. Upload & rollout (after build + eval fixes)

Naming is decided (D1): GCS `v2_arabmaqamrock_dataset` / `v3_arabmaqamrock_dataset`.

1. **Rename v2 first — copy, verify, retire separately** (never delete in the same step):
   `gcloud storage cp -r …/dataset/* …/v2_arabmaqamrock_dataset/` (or `rsync -r`),
   then verify **535 objects**, total bytes, and a CRC32C spot-check. Keep `dataset/` until a
   session has actually used the new path, then remove it (gated).
2. Build v3 locally → `v3_arabmaqamrock_dataset/` (438 mp3 + 438 txt).
3. Upload:
   `gcloud storage rsync -r v3_arabmaqamrock_dataset …/v3_arabmaqamrock_dataset/`.
   Verify **876 objects** + spot CRC32C + a 5-file byte compare.
4. Apply the codebase edits from the §3 table (notebook `GCP_DATASET_PATH` → v3; docs;
   `DECISIONS.md` naming scheme; bucket `README.txt`/`LAYOUT.json`).
5. Fresh VM → `bash bootstrap/setup.sh --training`; confirm the verify block reports
   **438 tracks** (bump `setup.sh`'s count check from `>0` to `== 438`).
6. Sidecars + `train_ctl.py start` per `docs/START.md` (you type the launch).
7. Post-run: `docs-reconciler` + `RECONCILIATION_LOG.md`; update `README.md` (267 → 438),
   `docs/README.md` constants, `DECISIONS.md` (naming + verbatim), `PROGRESS.md` milestone.

## 8. Decision status

| | Decision | Status |
|---|---|---|
| D1 | GCS names `v2_arabmaqamrock_dataset` / `v3_arabmaqamrock_dataset`, reflected in codebase | **DECIDED** (§3) |
| D2 | **Strip** the Suno header; keep the rebuilt style caption (lyrics-only verbatim) | **DECIDED — Option A** (§2) |
| D3 | Held-out/generation tag style: verbatim (match training) | **DECIDED — verbatim** (§4) |
| D4 | Local dir: keep `/content/yue2_dataset` | **DECIDED** |
| D5 | Commit the build script to the repo | **DECIDED — yes** |
| D6 | Steps: 5000 (≈v2 exposure) | **DECIDED — 5000** (§5) |
| D7 | Held-out eval | **DEFERRED** — testing happens at inference time on the cheap GPU, not during training; user decides then (see note) |
| D8 | Run name | **DECIDED — `v3_arabmaqamrock_lora`** (A100); L4 → `v3_arabmaqamrock_lora_l4` |
| D9 | L4 config gets the same dataset + 5000 steps | **DECIDED — yes** |

**D7 note.** Because `disable_sampling: true`, the training run never touches the prompts, so
nothing needs doing now. The config's four `sample.samples` prompts stay as-is and are **stale**
(3 of 4 contaminated vs the 438) — whoever runs the offline/inference eval must pick fresh
held-out lyrics first. Recorded so it isn't forgotten.

**D8 notes.** Run name: **`v3_arabmaqamrock_lora`** (A100) and **`v3_arabmaqamrock_lora_l4`** (L4) —
the earlier `arabmaqrock` spelling was a typo, corrected by the user. The two names must differ
because two runs can't share one GCS prefix.

### Defaults I will take unless you object (no decision needed)

- **Blank lines:** collapse 3+ consecutive blank lines to one blank line (v2 behaviour, cosmetic;
  keeps captions tidy without touching any non-blank line). The lyrics are otherwise byte-exact.
- **`dataset/` retirement:** do **not** delete the old prefix yet — copy to
  `v2_arabmaqamrock_dataset/`, verify, and retire only after a session has used v3 (the project's
  own rule). One command when you want it.
- **Latent cache:** not banked to GCS (v2 didn't either); rebuild per fresh VM (~20 min).
- **Repo artifacts:** commit the build script **and** a small `manifest`/checksum of the 438
  (train-script provenance, no audio).
- **Held-out picks (if D7 = rebuild):** I choose the poems (0 shared lines each, 24–28 lines),
  show them to you, and you approve before anything is written.

## 9. What is *not* being decided here

- No change to rank/EMA/LR/optimizer/`content_or_style`/`cot`/`train_window_frames`.
- No GPU work in this plan (build + upload are CPU/network only). The training launch is yours
  to type.
- No deletion of any existing GCS object.
