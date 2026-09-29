# current

_Updated 2026-09-29 (~09:15 UTC, Colab session 2). Purpose: the two paste-ready
prompts, the repeat cause, the dataset findings, and the test-batch artifacts — now with the
assets staged, the semantic screen **COMPLETE (16/16)**, the 5-track listening render **IN
FLIGHT**, backup running against the **new sectioned GCS layout**, and a plain-English primer
on the screen/ABC (below).
Durable record: `docs/music-cover-feasibility.md` §9. GCS layout: `docs/GCP_ORGANIZATION_PLAN.md`._

## In plain terms — what "the semantic screen" is, and why "ABC" keeps confusing us

**The question we're testing.** Our fine-tuned model learned from songs whose lyric sheets
deliberately repeat themselves: an intro line comes back, and the last verse is sung again in
the outro. Now we want to know — given a lyric sheet, does the model sing **exactly that
sheet**, or does it add repeats of its own? An unasked-for repeat is a defect in the
deliverable, so we need to know which it is.

**"ABC" is two different things sharing one name.**

- **Writing down a tune.** Take a recording and write its melody out as text — like
  transcribing a song into sheet music. That's what SheetSage2 does; the file is called
  `score.abc`. We did this **yesterday** for 12 songs (it's on GCS in `abc_v2/`).
  **Today we are not making any ABCs.**
- **Handing a tune to the model.** Three of our test runs give the model a `score.abc` and
  say, in effect, "sing these words to this tune". This is the *input* use. It steers the
  **melody only — never the words**.

(A third wrinkle, which is where the confusion comes from: when the model is asked to plan its
own tune first, it writes sheet music of its own. That's the "ABC planner". Two of our 16 runs
do that as a by-product, not on purpose.)

**The screen itself has nothing to do with sheet music.** The model builds a song in two big
stages:

1. **Plan** — it decides the music as a long list of numbers (think piano-roll, not sound).
2. **Perform** — it turns those numbers into actual audio. This is the expensive stage.

The screen runs **only stage 1**, and saves those numbers to a file (`semantic.json`).
Analogy: we get the songwriter's blueprint — the shape and the length — without ever hiring
the band.

**Why that's worth doing.** Repeats make the blueprint *longer*. We know how long this song is
meant to be: **7743 frames ≈ 309.7 seconds**, with a hard ceiling of **7750**. So a run that
plans noticeably longer — or that slams into the ceiling — is a run that probably added
something. It's a smoke detector: cheap, and it tells us where to look closely.

**What it can't do.** The numbers describe *sound*, not words. Nothing in `semantic.json` says
which line was sung. So the screen narrows the field but cannot settle the question: to learn
whether the outro is really sung twice, we still have to render the audio and listen.

**Why we bother at all.** It filters the 16 variations at ~4–5 min each instead of ~7+ min
each with audio, so only the interesting ones earn a full render.

_The terse version of the same three-way distinction is in §1 below._

## 0. VM state (checked, not assumed)

- Branch **`music-cover`** @ `bcaf1a6`, clean tree, pushed (`origin/music-cover` == HEAD).
  This session's commits: `d46c8c6` (section the GCS inference layout), `b462d5b` (trigger
  gotcha + the 1-seed manifest), `c2ccd7d` (reconciliation pass + verified GCS inventory),
  `bcaf1a6` (**correction** — the trigger claim committed in `b462d5b` was wrong; see §6).
- `/content` present, T4 **idle** (0 MiB / 0%). No training run active.
- `bash bootstrap/setup.sh --inference` **done**: all 8 jobs `ok`, total 35 s
  (`/content/logs/timing.txt`). Staged: main GGUF 7.26 GB, VAE, sidecars, both v2
  adapters in `/content/converter/out/`, binary in `/content/audiocpp_inference/bin/`.
- `vm-continuity status` → loop running (pid 9844), **healthy (exit 0)**.
- `backup_to_gcp.py --inference` — **was down** (never started this VM); a `--once`
  catch-up was run 2026-09-29T07:41Z (5/5 folders, drift then zero) and the daemon is now
  running (log `/content/logs/gcp_backup.log`, 5-min interval). Drift before the catch-up:
  `out/` 5.4 h, `logs/` 4.7 h, `agent_notes/` 5 h. `gpu_logger.py` is still down (training
  concern, not this session's).
- **GCS remote layout changed the same day** (2026-09-29): `audiocpp_inference/` is now sectioned
  and the daemon writes the sections (`out -> workspace/out`, `prompts -> tools/prompts`,
  `scripts -> tools/scripts`; `logs/`, `agent_notes/` unchanged). Local paths are UNCHANGED. The
  old flat paths still exist and are still the rollback — see
  `docs/GCP_ORGANIZATION_PLAN.md` §9 and §11.
- **The GPU is NO LONGER idle**: the 5-track verbatim render is running (§6). Track 1 finished
  09:04, track 2 in flight as of ~09:12. Check `nvidia-smi` before starting anything else.

## 1. What changed this session — read before re-planning

**Three things get conflated here; they are not the same** (plain-English version above):

1. **ABC extraction** — audio → `score.abc` via SheetSage2. **Finished 2026-09-28**
   (`abc_v2/` on GCS). We only *download* these; none are produced now.
2. **The semantic screen** — `stop_after=semantic` → **`semantic.json`** (codec indices,
   25/s), **no audio**. This is what `screen_arms.sh` runs. The option is documented as
   "ABC planner + semantic AR", so the `cot=melody` arms *without* `abc_file`
   (`c0_cotonly`, `c0raw_cotonly`) will additionally write a `score.abc` of the model's
   **own** plan — a byproduct, and **not** the same file as an `abc_v2/` transcription.
   `cot=off` arms write `semantic.json` only.
3. **ABC as input** — the C arms feed the `abc_v2` guide `score.abc` through `abc_file`
   to steer **melody** (not words).

### 1.1 The ABC already exists (no transcription needed)

`gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/audiocpp_inference/out/abc_v2/`
— **12** `score.abc` files, written **2026-09-28 18:02–18:12 UTC** (Python SheetSage2,
route B2). Includes the guide track itself:

- GCS: `abc_v2/01-نسيب-وظعن-الحي-ونخيل-يامن-وعرائس-النعمة_4148240095/score.abc`
- Local (pulled this session):
  `/content/audiocpp_inference/out/abc_v2/01-نسيب-وظعن-الحي-ونخيل-يامن-وعرائس-النعمة_4148240095/score.abc`
  — 3701 B, `sha256 14ae1ae0f885c41b5ae312d746864daac247f2399c158e039cdb278b40540d32`,
  `K:D#m`, `Q:1/4=125`.

Do **not** confuse the prefixes: `out/sheetsage2_abc/` is the **failed** audio.cpp-route
smoke (`transcribe_manifest.json`: `n_ok: 0`, one track, `exit 1`, 3 s). `ss2_smoke/` and
`ss2_smoke2/` are earlier one-track smokes. The good output is `abc_v2/`.

**Seed provenance:** `sheetsage2_transcribe.py:105` names each output dir after the source
WAV's stem (`tdir = out_dir / wav.stem`), and the default input is `out/batch_36_songs`
(variants excluded). So the seed in the stem **is the render seed** of the audio the ABC
was transcribed from — `_4148240095` ⇒ the guide WAV at seed 4148240095. `abc_v2/` holds
12 such tracks, **each with its own seed**; the arms only hold the guide's constant
(`SEED=4148240095` in `screen_arms.sh:50`, first entry of `batch.json`'s seeds). Switching
the guide means switching the seed with it.

### 1.2 The screen is possible — but `semantic_prefix` is not

Checked with `strings` against the **staged** binary (not just the docs):

| option | hits | meaning |
|---|---:|---|
| `stop_after` | 12 | `abc\|semantic\|audio`; `semantic` implies `export_semantic` |
| `export_semantic` | 4 | writes `semantic.json` under `--out-dir` |
| `text/vnd.abc`, `application/vnd.yue2.semantic+json` | — | the artifact MIMEs |
| `yue2.semantic.frames` / `.truncated` | — | artifact meta |
| `abc_file`, `cot`, `melody` | 6 / 18 / 6 | cover knobs present |
| `semantic_prefix` | **0** | **absent** — that one needs v0.8.2+ |

`stop_after=semantic` implies `export_semantic=true`, writes `score.abc` + `semantic.json`,
produces **no audio**, and needs `--out-dir` (`--out` writes nothing).

### 1.3 The guide render is NOT truncated — `generate.py` says otherwise

`out/batch_36_songs/01-نسيب…_4148240095` sidecar reports `"truncated": true`, but with
`"truncated_source": "duration_heuristic"`. The run's own log says:

```
[TIMING ts=20260928-112248] yue2.semantic.tokens 7743
[TIMING ts=20260928-112248] yue2.semantic.truncated 0      <- the model's own flag
[TIMING ts=20260928-112248] yue2.semantic_ms 231906.26479
```

WAV = 309.72 s = 7743/25 s; cap = 7750. It **ended on EOS, 7 frames under the cap** —
the sidecar's `true` is the WAV-near-cap heuristic firing, not truncation. Always read
the model flag, not generate.py's sidecar.

Useful consequence: the cap (7750) is only 7 frames above this sheet's natural plan
(7743), so **any injected section repeat overruns the cap and shows
`yue2.semantic.truncated 1`** — a cheap, objective repeat detector.

Cost: AR semantic = 232 s of the 423 s full render (~55%). So the screen costs ~45% of a
render and emits no 57 MB WAV; it is a pre-filter plus a truncation signal, not a
replacement for listening.

### 1.4 The control arm is exact

`styles/hijaz_sunoblk.txt` `sha256 300d1ae0…` == the guide's `style_sha256`;
`lyrics/01_nesib_as-is.txt` `sha256 29f46a89…` == the guide's `lyrics_sha256`. Same
seed 4148240095, same adapter (v2), same `cot=off` ⇒ `ctl_sunoblk_as-is` reproduces the
guide render.

### 1.5 Arm A is now one variable

`styles/hijaz_modified.txt` was a five-variable placeholder (added BPM + `vocals` +
`instrumentation` + `Mood`, and flipped Mood). Rewritten this session as the winning
text **with only `110 BPM` restored** — a clean single variable vs `win_as-is`.

## 2. The screen driver (new, uncommitted)

- `INFERENCE/screen_arms.sh <core|abc|all> [--dry-run]` — the same arm names as
  `batch.json` / `test_batch.sh`, but each run is `stop_after=semantic` + `--out-dir`
  (no `--out`). Refuses if a training run is active or `nvidia-smi` is missing.
  `ABC_FILE` defaults to the pulled guide ABC. Tested: `bash -n` clean, `core` dry-run
  plan correct.
- `INFERENCE/screen_summary.py <screen_dir> [--expect-wav guide.wav | --expect S]` —
  prints `frames / sec / trunc / ar_s` per arm. `trunc` is the **model** flag; `frames`
  falls back to the CLI log when `semantic.json` is absent. Tested against fakes.

**Limit (do not oversell it):** `semantic.json` is acoustic **codec** indices — there is
no lyric↔frame alignment, so it cannot say *which line* was sung. It ranks arms by planned
length + truncation. The verbatim verdict still needs the rendered audio (listening, or
ASR of the output vs the sheet).

### 2.1 Results — complete, 16/16 (seed 4148240095; `ref` = the guide's 309.7 s)

All 16 arms `exit=0` and wrote `semantic.json`. No audio, by design. Log:
`/content/logs/tv_screen.log`; artifacts `out/screen_semantic/<arm>_4148240095/`.

| arm | frames | sec | trunc | vs ref |
|---|---:|---:|---|---:|
| `ctl_sunoblk_as-is` | 7743 | 309.7 | no | +0.0 |
| `c3_abc_raw` | 7750 | 310.0 | **yes** | +0.3 |
| `c2_abc_mod` | 7698 | 307.9 | no | −1.9 |
| `c1_abc_win` | 7557 | 302.3 | no | −7.4 |
| `b1_window` | 7499 | 300.0 | no | −9.8 |
| `c0_cotonly` | 7328 | 293.1 | no | −16.6 |
| `mod_as-is` | 7303 | 292.1 | no | −17.6 |
| `c0raw_cotonly` | 7134 | 285.4 | no | −24.4 |
| `win_as-is` | 6798 | 271.9 | no | −37.8 |
| `b3raw_both` | 6545 | 261.8 | no | −47.9 |
| `b1raw_window` | 6497 | 259.9 | no | −49.8 |
| `b3_both` | 6453 | 258.1 | no | −51.6 |
| `b2_guidance` | 6368 | 254.7 | no | −55.0 |
| `b2raw_guidance` | 6179 | 247.2 | no | −62.6 |
| `win_dedup` | 5701 | 228.0 | no | −81.7 *(own cap 7000)* |
| `win_bare` | 5692 | 227.7 | no | −82.0 |

**Measured (not interpretation):**
- **Exactly one truncation**: `c3_abc_raw` reached 7750 = the cap. Every `cot=off` arm plans
  *shorter* than the guide; the `cot=melody` family is the longest (7750 / 7698 / 7557).
- Same sheet, prompt only: ctl 7743 → mod 7303 → win 6798. Restoring `110 BPM` alone
  **lengthens** the plan by ~20 s.
- Tag format alone (same words, same style): descriptor tags 6798 vs **bare** 5692 — **−44 s**.
- Sheet repeats removed: as-is 6798 vs dedup 5701 — **−44 s**.
- The knob arms' effect on length is **not consistent across styles**: `b1_window` lengthens the
  winning style (6798 → 7499) but shortens the raw style (7743 → 6497). So planned length alone
  cannot identify a "fix".
- `ar_s` is contention-polluted (parallel npm/jsdom work) — do not read it as cost.

**Not established:** whether any arm re-sang a line. Length effects of ~44 s are visible; the
*words* are not. One truncation on one ABC arm says nothing about repeats.

## 3. Next commands (GPU work — check `nvidia-smi` first)

> **Status: the semantic screen is ALREADY RUNNING** (started 2026-09-29T07:27:50Z, detached,
> log `/content/logs/tv_screen.log`). Its arms below are therefore *done or in progress*, not
> "next" — kept here for the resume/stop commands and for the steps after it.

Assets are staged; nothing below needs `setup.sh` again.

```bash
cd /content/maqamrock-yue2-lora-finetuning

# 0) free pre-checks
nvidia-smi                       # confirm no other GPU work
bash INFERENCE/screen_arms.sh core --dry-run          # instant, no GPU

# 1) SEMANTIC SCREEN — the cheap pass (no audio, ~4 min/arm). DETACHED.
setsid nohup bash INFERENCE/screen_arms.sh all \
  > /content/logs/tv_screen.log 2>&1 & disown
#   watch:  tail -f /content/logs/tv_screen.log
#   stop:   pkill -f 'screen_arms.sh'
#   resume: re-run the same command (arms with artifacts are still re-run; it is cheap)
#   then:   python3 INFERENCE/screen_summary.py \
#             /content/audiocpp_inference/out/screen_semantic \
#             --expect-wav /content/audiocpp_inference/out/batch_36_songs/01-نسيب-وظعن-الحي-ونخيل-يامن-وعرائس-النعمة_4148240095.wav

# 2) RENDER the winners to audio (only after reading the screen)
setsid nohup python3 INFERENCE/generate.py manifests/test_verbatim_hijaz/batch.json \
  > /content/logs/tv_batch.log 2>&1 & disown
#   stop: pkill -f 'generate.py manifests/test_verbatim_hijaz'

# 3) B / C arms as full audio (test_batch.sh) — superseded by screen_arms.sh for screening
# ABC_FILE is already staged; test_batch.sh picks its own default, pass it explicitly:
ABC_FILE=/content/audiocpp_inference/out/abc_v2/01-نسيب-وظعن-الحي-ونخيل-يامن-وعرائس-النعمة_4148240095/score.abc \
  setsid nohup bash INFERENCE/test_batch.sh abc > /content/logs/tv_abc.log 2>&1 & disown

# backup after any run that produced audio
python3 backup_to_gcp.py --inference --once
```

## 4. Still open (unchanged from the earlier handoff)

- Which adapter for the batch — `v2` or `qfinal_a0.3`? (`batch.json` pins `v2`.)
- **Maqam clash:** the winning prompt was measured on **Ajam**; this track is **Hijaz**
  (the Hijaz copy is what the arms use).
- No-repeat arm (`win_dedup`) is the injection control; bare-tag arm (`win_bare`) tests
  the descriptor-tag mismatch.
- Two train/inference mismatches remain: the edited prompts dropped `110 BPM` (restored
  in arm A only), and training lyrics use **bare** tags while the as-is sheet carries
  `[Section | descriptors]`.

## 5. This session's diagram — how to view it

`agent_notes/session_2026-09-29_flow.html` — Mermaid diagrams of the session flow and the
16 arms (**validated** with mermaid's own parser: 2/2 blocks). `browser.preview` does
**not** work on this VM (no desktop app attached), so it is served over HTTP instead:

```bash
# terminal: detached — survives Ctrl+C / closing the tab
#   log:    /content/logs/http.log
#   stop:   pkill -f 'http.server 8765'
#   resume: re-run the line below
cd /content/webshare && python3 -m http.server 8765 --bind 0.0.0.0
```

- **View:** <https://amusing-dog-glt654t-8765.asse.devtunnels.ms/>
  (or `.../agent_notes/session_2026-09-29_flow.html`).
- Tunnel name/id/cluster live in `/root/.vscode/cli/code_tunnel.json`; the pattern is
  `https://<tunnel-id>-<port>.<cluster>.devtunnels.ms`.
- `/content/webshare` holds **copies** (`index.html` + `agent_notes/…`) — re-copy after
  editing the source file. It is deliberately not the repo root, so the tunnel does not
  expose the whole checkout.
- First few seconds after a (re)start the URL may 302/404 while the tunnel re-registers
  the port; retry. Restarting the server **breaks an already-open tab**.
- Details + traps: `docs/COMMAND_HANDOVER_GOTCHAS.md` (2026-09-29 entry).

## 6. Blind listening round — sheet written, not yet fillable

**Sheet:** `manifests/evaluation_verbatim_hijaz/MY_EVALUATION.txt` (new). Same shape as
yesterday's style-ablation round (intro/vocal-start, intro-verse quality, Maqam Rock (v2),
overall vocal quality, pronunciation, pace) **plus** the two sections that are today's actual
question: **LYRICS ADHERENCE** and **REPEAT COUNT of the final couplet** (2× = the sheet's own
design — the training songs repeat a couplet once; 3×+ = an added repeat).

**Blinding seed for this round: `20260929`** (next unused; prior rounds were 20260925–28).

`EVAL.txt` / `KEYS.txt` / `KEY.json` are deliberately **not written yet** — the packaging tool
produces them at build time, and hand-writing them now would invent labels that map to no file.

**STATUS 2026-09-29 ~09:13Z — RENDERING: 2/5 DONE, track 3 in flight** (GPU 100%).

| # | arm | wall | audio rendered | screen predicted |
|---|---|---|---|---|
| 1 | `ctl_sunoblk_as-is` | 7:17 | 309.7 s | 7743 f = 309.7 s ✅ |
| 2 | `win_as-is` | 8:23 | 271.9 s | 6798 f = 271.9 s ✅ |
| 3 | `mod_as-is` | in flight (started 09:12:33) | — | 7303 f = 292.1 s |

**The screen's frame counts predict the rendered duration exactly (2/2 so far):**
`7743/25 = 309.72 s` and `6798/25 = 271.92 s`, both matching the WAVs to a tenth of a second.
That validates the screen's length signal against real audio rather than argument — which is
what makes §2.1's `vs ref` column usable as a predictor.

Revised expectation: **≈22.2 min of audio**, not the ~25.3 min derived from the caps — the caps
are ceilings and most arms stop short of theirs (only `c3_abc_raw` ever reached 7750). The
screen's measured frames are the better estimate. Run dir:
`/content/audiocpp_inference/out/verbatim_hijaz_seed4148240095` (explicit `--out-dir`, so it is
resumable and `out/latest` cannot point the copy below at the *wrong* round). Manifest:
`manifests/test_verbatim_hijaz/batch_seed4148240095.json` — a 5-arm × **1-seed** trim of
`batch.json`, because `generate.py` has no `--seed` filter. `--no-trigger` is passed, and
here it is a **no-op**: `generate.py`'s trigger check is a substring search over the whole
style file, and every Hijaz style already contains `arabmaqamrock` (in `hijaz_sunoblk.txt`
it sits in the `genre:` line, not at the start) — so nothing is prepended either way. The
rendered arms therefore match the screened ones. See `docs/COMMAND_HANDOVER_GOTCHAS.md`,
entry 2026-09-29 (which carries a same-day correction).

**The build + upload is AUTOMATED this round** — the packaging block below is what a background
job is already running, so you should not need to paste it by hand. It waits for the render,
verifies 5/5 WAVs, stages flat→per-arm, runs `prepare_ab_eval.py`, copies the sheets into
`manifests/evaluation_verbatim_hijaz/`, and uploads. Log `/content/logs/ab_verbatim_pipeline.log`;
stop `pkill -f 'verbatim_pipeline[.]sh'`. Every step is idempotent, so re-running the block is
safe if it dies.

The 5 arms in the round — one track, seed 4148240095, all from `batch.json`, `lora: v2`:

| arm | what differs |
|---|---|
| `ctl_sunoblk_as-is` | baseline: the guide render's own Suno block |
| `win_as-is` | the winning `l2_target_off` prompt, Hijaz |
| `mod_as-is` | winning + `110 BPM` restored (one variable) |
| `win_dedup` | winning prompt + sheet with the built-in repeats removed (**injection test**) |
| `win_bare` | winning prompt + bare `[Verse 1]` tags (= the trained tag format) |

Build the package once the audio exists (`prepare_ab_eval.py` wants one folder per variant;
`generate.py` writes flat):

```bash
# terminal: state-changing one-shot (writes the mp3 package + key)
#   log:    /content/logs/ab_build.log
#   stop:   pkill -f 'prepare_ab_eval[.]py'   (aborts; re-runnable)
#   resume: re-run the block — the copy loop is idempotent
R=/content/audiocpp_inference/out/verbatim_hijaz_seed4148240095   # explicit: do NOT use out/latest (it may still point at an older round)
mkdir -p /content/ab_verbatim
for a in ctl_sunoblk_as-is win_as-is mod_as-is win_dedup win_bare; do
  mkdir -p "/content/ab_verbatim/$a"
  cp "$R/${a}_4148240095.wav" "/content/ab_verbatim/$a/nesib_4148240095.wav"
done
python3 INFERENCE/prepare_ab_eval.py --root /content/ab_verbatim \
  --output /content/ab_verbatim_out --audio-format mp3 --bitrate 192k \
  --seed 20260929 --json /content/ab_verbatim_out/KEY.json \
  --title "VERBATIM_HIJAZ_LYRIC_ADHERENCE"
cp /content/ab_verbatim_out/{EVAL.txt,KEYS.txt,KEY.json} manifests/evaluation_verbatim_hijaz/
```

Two cautions baked into the sheet as well: `win_dedup` carries a **lower cap** (7000 vs 7750 —
it has fewer letters), so a length difference there is not by itself an added repeat; and if the
other two seeds are rendered too, they are a **separate block** — labels do not carry across tracks.

### 6.1 Where the evaluator downloads it from

Follow the existing `listening/` convention (`MAQAM_LYRIC_SWAP_INPUT/`, `PRON_*_INPUT/`), so the
round is fetchable the same way as every earlier one:

```
gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/listening/VERBATIM_HIJAZ_LYRIC_ADHERENCE_INPUT/
  nesib_4148240095_A.mp3 … _E.mp3     # blind labels; no mapping in the filenames
  EVAL.txt                            # instructions only, no mapping
  KEY_open_after_listening.txt        # SECRET — do not open until every section is scored
```

```bash
# terminal: foreground — one download, watch the progress bar
mkdir -p ~/verbatim_eval && gsutil -m cp -r \
  'gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/listening/VERBATIM_HIJAZ_LYRIC_ADHERENCE_INPUT/*' \
  ~/verbatim_eval/
# then in the same folder: python3 -m http.server 8765   (or just open the files locally)
```

Add the upload step to §6's packaging block once the mp3s exist. **Note the rename**: the
secret decoder goes up as `KEY_open_after_listening.txt`, matching every existing package
(`MAQAM_LYRIC_SWAP_INPUT/` etc. all use that name — checked on the bucket, 2026-09-29):

```bash
gsutil -m cp /content/ab_verbatim_out/*.mp3 \
  /content/ab_verbatim_out/EVAL.txt \
  gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/listening/VERBATIM_HIJAZ_LYRIC_ADHERENCE_INPUT/
# secret decoder — renamed on upload, per the convention above
gsutil cp /content/ab_verbatim_out/KEYS.txt \
  gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/listening/VERBATIM_HIJAZ_LYRIC_ADHERENCE_INPUT/KEY_open_after_listening.txt
```

**Deliberate deviation:** the four existing packages carry audio + the key and **no `EVAL.txt`**
at all — the evaluator is handed audio with no instructions. This round adds `EVAL.txt`.

One gap found while checking this (2026-09-29): **yesterday's ajam blind mp3 package is not on
GCS** — only the raw WAVs under `audiocpp_inference/out/style_ablation_ajam/` are
(`l0_raw_298970020.wav` … `l4_min_298970020.wav`, ~224 MiB). Its label map survives in git
(`manifests/evaluation_style_ablation_ajam/KEYS.txt`), but the `ajam_A.mp3` … files themselves do
not exist anywhere — they were built under `/content/` outside the mirror set. Re-packaging from the
WAVs is possible but would need the same blinding seed (20260928) *and* variant order to reproduce
yesterday's A–E labels, otherwise a re-run's labels won't match the scores already recorded.

*(The other gap is now closed: today's round does have a GCS path. The raw renders are already
under `audiocpp_inference/workspace/out/verbatim_hijaz_seed4148240095/`, and the blind package will
land at `listening/VERBATIM_HIJAZ_LYRIC_ADHERENCE_INPUT/` when the pipeline finishes.)*

### 6.2 Syncing the raw tracks while they render (progress only — NOT for scoring)

```bash
# terminal: FOREGROUND loop — long-running. Ctrl+C stops it; nothing is left running after.
#   log:    n/a (prints to the terminal)
#   resume: re-run — `rsync` is incremental and has no -d, so nothing local is ever deleted
mkdir -p ~/verbatim_tracks
while true; do
  gsutil -m rsync -r \
    'gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/audiocpp_inference/workspace/out/verbatim_hijaz_seed4148240095' \
    ~/verbatim_tracks && date -u +%FT%TZ && ls ~/verbatim_tracks/*.wav 2>/dev/null | wc -l
  sleep 60
done
```

- **One-shot** (no loop): keep only the `gsutil -m rsync -r` line.
- **Audio only**, skipping the `.log`/`.json`/`_gpu.csv`/`_time.txt` sidecars: add
  `-x '\.(log|json|csv|txt)$'`.
- **Timing:** the daemon mirrors `out/` every ~5 min (passes observed 09:00:07 / 09:05:17 /
  09:10:26), so GCS trails local by up to ~5 min. The first WAV was already up when checked.
- **Do NOT use `out/latest` to locate this round.** Local `out/latest` does not exist yet:
  `generate.py:984` writes it only *after* `run_batch` returns, so it appears once the whole batch
  finishes. The `latest` object already on GCS is a **stale** pointer to a previous round
  (`…/out/style_ablation_ajam`), left there by an older session. Use the explicit run dir.

> **Blinding warning.** The raw filenames **are** the arm names
> (`ctl_sunoblk_as-is_4148240095.wav`, `win_dedup_4148240095.wav`). Listening to these tells you
> which arm you are hearing, which destroys the point of the round. Use this sync to watch progress
> only; **score from §6.1's blind package**, whose files are `nesib_4148240095_A.mp3 … _E.mp3`.

### 6.3 `*_gpu.csv` now has a header (fixed 2026-09-29)

`run_one.sh` wrote its 1 Hz `nvidia-smi` CSV with `--format=csv,noheader,nounits`, so the column
meaning was recorded nowhere. Fixed at the writer; this round's files were backfilled
(header-only). Columns, in order:

```
gpu_util_pct,mem_used_mib,power_draw_w,temp_c
```

**Anything parsing it must skip row 1** — `pron_knob_probe.sh`'s `_gpu_stats` now does so
explicitly. If an older headerless file turns up, this helper is idempotent:

```bash
# terminal: foreground, instant; re-runnable (skips files that already have the header)
bash /tmp/opencode/add_gpu_csv_header.sh /content/audiocpp_inference/out
```

`/tmp/opencode/` does **not** survive a VM reset — the content is reproducible from the message
of commit `34d84cc`.

**Gap, not fixed:** `screen_arms.sh` runs the binary directly rather than through `run_one.sh`,
so the 16 screened arms wrote `_time.txt` + `.log` but **no `_gpu.csv`** — the screen has no GPU
telemetry. Wiring in the sampler needs a real GPU run to test, and the GPU is busy with the render.



