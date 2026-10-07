# Listening evaluation — scoring rendered variants

How we **score** generated audio. The render side is [`INFERENCE.md`](INFERENCE.md); the
hand-a-package-to-someone-else side is [`AB_BLIND_EVAL.md`](AB_BLIND_EVAL.md); this doc is
the rating step. The agent-facing procedure is the
[`listening-eval` skill](../skills/listening-eval/SKILL.md).

## The tool

The rating app lives in its **own repo** (not in this one):

```
https://github.com/akbargherbal/ai_music_rating_app.git
```

Flask app, one rater, a package layout. Three concepts:

| Thing | What it is | Where |
|---|---|---|
| **Scorecard** | the questions (reusable JSON) | `scorecards/<name>.json` |
| **Run** | one evaluation: audio folder + frozen scorecard + results | `runs/<run_id>/` |
| Settings | how the app behaves (port, blind, dirs, …) | CLI / env / `--config` |

It **supersedes the in-repo `INFERENCE/rating_app/`** single-file app (kept for history;
that one produced the M13 report). Do not use the in-repo copy for new evaluations.

## The one command

```powershell
python app.py --audio "<audio folder>" --label <run_id> --scorecard "<card.json | name>" [--blind]
```

- Run it **from the app folder** — `scorecards/`, `configs/`, `runs/` always live next to
  `app.py`, so it works from any directory.
- Everything is set **at launch**: there is no `/setup` step. The startup line
  `rating_app: ready for '<run_id>' [scorecard: <…>]` is your confirmation.
- `--blind` hides arm/folder names and shuffles order (seed stored in `run.json`);
  reports reveal everything. Use it for the unbiased final pass.

Concrete (the D-test):

```powershell
python app.py `
  --audio "C:\Users\DELL\Downloads\jarir_dtest" `
  --label dtest_diction `
  --scorecard "C:\Users\DELL\Downloads\dtest_diction.json"
```

## One-time setup (per machine)

```powershell
git clone https://github.com/akbargherbal/ai_music_rating_app.git
cd ai_music_rating_app
py -m pip install -r requirements.txt
```

**Where the app finds the scorecard** — only two places:

1. an explicit `--scorecard <path>` to an existing file, or
2. `<name>.json` in its own `scorecards/` folder.

It never scans the audio folder or this repo. Our cards live in `INFERENCE/scorecards/`
(e.g. `dtest_diction.json`) — copy one into `scorecards/` (then `--scorecard dtest_diction`)
or just pass its path.

## Standard sequence

1. **Render** (this repo) — outputs mirror to GCS automatically
   (`backup_to_gcp.py --inference`).
2. **Pull the audio** to the rating machine:
   ```powershell
   gsutil -m rsync -r gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/audiocpp_inference/out/<run> .\<run>\
   ```
3. **Launch** with the one command above (`--label <run>`, `--scorecard <card>`).
4. **Rate.** Click **↻ Rescan** when new takes land (e.g. a render still finishing).
5. **Export** the report: `/report.md`, `/report.csv`, `/report.json` (also the
   **export .md** link).

## Rules that bite

- **A run's scorecard is frozen.** `runs/<run_id>/scorecard.snapshot.json` is written once
  when the run is created and never rewritten; changing the card later does **not** change
  an existing run (the settings page shows *Drift Detected*). To change cards, start a
  **new run** — a new `--label`.
- **Same label + different audio folder = a new run** (the app suffixes the id), so results
  never mix; same label + same folder = resume the same run.
- **Name vs path.** `--scorecard dtest_diction` needs `scorecards/dtest_diction.json`;
  `--scorecard C:\…\dtest_diction.json` needs nothing copied.
- **Rescan** re-reads the audio folder. With the file set unchanged the blind order is
  identical (a seeded permutation stored once in `run.json`); adding or removing files
  changes it. Ratings are keyed to the **file path**, so nothing is lost either way.
- **Settings precedence** (all optional): CLI flag > `RATING_*` env var > `--config` file >
  `<audio>/_rating.json` > `~/.config/rating_app/config.json` > defaults.
- **Legacy import:** an old `<out>/evaluations.json` is imported once (only if that run's
  `results.json` does not already exist).

## Stopping and resuming

Every rating is written to disk **the moment you save that track**
(`runs/<run_id>/results.json`, atomic write) — nothing lives only in memory. Stop the server
whenever; relaunch the **same command** (`--label` and `--audio` unchanged) and the same run
returns with all ratings intact (and the same blind order). A **different `--label`** — or a
different audio folder — starts a fresh, empty run.

## Blinding: two mechanisms, different jobs

- **App `--blind`** — *you* rate your own renders without seeing the arm names. Single
  rater, in-process, reproducible seed.
- **[`INFERENCE/prepare_ab_eval.py`](../INFERENCE/prepare_ab_eval.py)** +
  [`AB_BLIND_EVAL.md`](AB_BLIND_EVAL.md) — build a self-contained mp3 package +
  `EVAL.txt`/`KEYS.txt` to hand to a **different** person. Keep using it for that.

## Not built yet

There is no headless rate/report CLI: `app.py` always starts the Flask server and the
report is a web route. If we ever need "rate → markdown in one command with no browser", a
small wrapper over `rating_app/report.py` is the next step.
