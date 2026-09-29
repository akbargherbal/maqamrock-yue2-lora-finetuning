# current

_Updated 2026-09-29 (Colab session 2, ~07:20–07:45 UTC). Purpose: the two paste-ready
prompts, the repeat cause, the dataset findings, and the test-batch artifacts — now with the
assets staged, the semantic-screen driver built and running, backup restored, and a
plain-English primer on the screen/ABC (below).
Durable record: `docs/music-cover-feasibility.md` §9._

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

- Branch **`music-cover`** @ `fb071aa`, clean tree apart from this session's two new
  files (uncommitted, see §3).
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
R=$(readlink -f /content/audiocpp_inference/out/latest)
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

Add the upload step to §6's packaging block once the mp3s exist:

```bash
gsutil -m cp /content/ab_verbatim_out/*.mp3 \
  /content/ab_verbatim_out/EVAL.txt \
  /content/ab_verbatim_out/KEYS.txt \
  gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/listening/VERBATIM_HIJAZ_LYRIC_ADHERENCE_INPUT/
```

Two gaps found while checking this (2026-09-29): **today's round has no GCS path yet** because no
audio has been rendered, and **yesterday's ajam blind mp3 package is not on GCS either** — only the
raw WAVs under `audiocpp_inference/out/style_ablation_ajam/` are (`l0_raw_298970020.wav` …
`l4_min_298970020.wav`, ~224 MiB). Its label map survives in git
(`manifests/evaluation_style_ablation_ajam/KEYS.txt`), but the `ajam_A.mp3` … files themselves do
not exist anywhere — they were built under `/content/` outside the mirror set. Re-packaging from the
WAVs is possible but would need the same blinding seed (20260928) *and* variant order to reproduce
yesterday's A–E labels, otherwise a re-run's labels won't match the scores already recorded.



