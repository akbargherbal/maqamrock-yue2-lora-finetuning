# rating_app

> **SUPERSEDED (2026-10-07).** New listening evaluations use the external app
> `https://github.com/akbargherbal/ai_music_rating_app.git` — see
> [`docs/LISTENING_EVAL.md`](../../docs/LISTENING_EVAL.md). This single-file copy is kept
> for history (it produced the M13 report); do not use it for new evaluations.

A **general** listening rating app (single-file Flask). Point it at any folder of
rendered audio variants — the sub-folders are the arms/variants — rate each track
on a scorecard you can change without touching the code, and export a Markdown
report.

Nothing about a specific run is hardcoded: no bundled audio, no fixed reference
text, no run-specific filenames. Use it for the Jarir lever probe today and the
next run tomorrow.

## What it does

- **Asks for the track directory** — on the terminal if `--audio` is omitted, and
  on the web `/setup` page any time. The folder is read in place; nothing is copied.
- **Discovers generically** — every `*.wav/.mp3/.flac/.m4a/.ogg` under the folder is
  a track; its relative parent folder is its group/arm. A flat folder works too.
- **Configurable scorecard** (`/criteria` page or a JSON file) — default criteria are
  Overall, Diction/clarity, Melody/maqam, Prosody/timing, Mix, Artifacts, Keep?, Notes.
- **Persists** every save to `evaluations.json`; **export .md** gives a table, a
  per-folder mean, per-track notes, and the raw JSON.
- Optional per-folder label: a `_knob.json` / `_meta.json` with `label` / `config` /
  `arm` / `extra_request_opts`; optional per-file labels via a root `labels.json`.

## Run (Windows)

```powershell
# once
py -m pip install -r requirements.txt

# put the app somewhere and run it
cd path\to\rating_app
py app.py
#   => "Track directory (e.g. C:\Users\DELL\Downloads\jarir_lever_probe):"
#      paste the folder that holds your WAVs, e.g.
#      C:\Users\DELL\Downloads\jarir_lever_probe
#   => open http://127.0.0.1:5000
#      (if 5000 is already taken by another app, it auto-uses the next free
#       port — e.g. 5001 — and prints that URL instead)
```

You can also pass it directly (no prompt):

```powershell
py app.py --audio "C:\Users\DELL\Downloads\jarir_lever_probe" --label jarir_lever_probe
```

`--out` (default `.\rating_out`) holds `evaluations.json`, `criteria.json`, and
`session.json` (which remembers your last folder), so re-running with no arguments
resumes exactly where you left off.

**Ports.** `--port` (default `5000`) is just a *preference*: if it is already in
use, the app moves up to the next free port and prints the real URL. So you can
leave several Flask apps running side by side. Use `--strict-port` to bind exactly
`--port` and fail if it is taken, or `--port 0` to let the OS pick any free port.

## Changing the criteria

Open the **criteria** tab, edit the JSON, save — it is written to
`rating_out\criteria.json` and used from then on. Types: `rating` (1..`max`),
`choice` (options), `number`, `notes`. `summary_metric` picks the rating used to
rank folders. Precedence: `--fields` > `<out>/criteria.json` >
`<audio>/_criteria.json` > built-in default.

## Notes from the agent

- Serve audio locally: `--host 127.0.0.1` is default; use `--host 0.0.0.0` only if
  you want to reach it from another device.
- No blinding here — files are shown with their folder/arm labels. For a label-blind
  listen, shuffle/rename the WAVs first (`INFERENCE/prepare_ab_eval.py`).
- The older Quran-specific `INFERENCE/eval_app` (2:255 word-grid) is untouched; this
  is the general-purpose replacement for everything else.
