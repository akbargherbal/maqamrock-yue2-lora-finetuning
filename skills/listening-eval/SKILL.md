---
name: listening-eval
description: Score rendered audio variants with the external listening/rating app -- one command with the scorecard, audio folder and run label; blind mode; report export. Use when asked to listen to, rate, score, or evaluate generated tracks, run the rating app, wire up a scorecard, or export a listening report. Trigger words - listening eval, listening evaluation, rating app, rate tracks, score tracks, scorecard, blind listening, listening report, ai_music_rating_app.
---

# Listening evaluation (rating app)

Score rendered variants. Authority: [`docs/LISTENING_EVAL.md`](../../docs/LISTENING_EVAL.md).
The tool is **not in this repo** — it is the external
`https://github.com/akbargherbal/ai_music_rating_app.git`; it **supersedes** the earlier
in-repo single-file listening app (retired).

## The one command

```powershell
python app.py --audio "<audio folder>" --label <run_id> --scorecard "<card.json | name>" [--blind]
```

- Run from the app folder (`scorecards/`, `configs/`, `runs/` live next to `app.py`).
- No `/setup` step: the scorecard + run are resolved at launch. Confirm via the printed
  `rating_app: ready for '<run_id>' [scorecard: …]`.
- `--blind` hides arm names and shuffles order (seeded in `run.json`); use it for the final
  unbiased pass.

## Where the scorecard comes from

Only two places: an explicit `--scorecard <path>`, or `<name>.json` in the app's own
`scorecards/`. It never scans the audio folder or this repo. Our cards live in
`INFERENCE/scorecards/` — copy one into `scorecards/` or pass its path.

## Steps

1. Render (this repo) → mirrored to GCS by `backup_to_gcp.py --inference`.
2. Pull audio: `gsutil -m rsync -r <GCS base>/audiocpp_inference/out/<run> .\<run>\`
3. Launch with the one command; `--label <run>` and the scorecard.
4. Rate; **↻ Rescan** when new takes land.
5. Export `/report.md` / `.csv` / `.json`.

Stopping the server loses nothing: each save writes `runs/<run_id>/results.json` atomically.
Relaunch the **same** command (`--label` + `--audio` unchanged) to resume the same run.

## Traps

- **The run's scorecard is frozen** at `runs/<run_id>/scorecard.snapshot.json`. To change
  cards, use a **new `--label`** — reusing a run will not pick up the new card (drift).
- **Same label + different audio = a new run**; same label + same audio = resume.
- **Rescan** re-reads the folder; the blind order is a seeded permutation in `run.json`, so
  it's stable until files are added/removed. Ratings are keyed to the file path.
- A bare `[scorecard: default]` at startup means the card was **not** picked up (path/name
  wrong, or the file isn't in `scorecards/`).
- Precedence: CLI > `RATING_*` env > `--config` > `<audio>/_rating.json` >
  `~/.config/rating_app/config.json` > defaults.

## Not this skill

Handing a blinded package to a **different** person is `ab-blind-eval` /
`prepare_ab_eval.py` — different job, keep using it.
