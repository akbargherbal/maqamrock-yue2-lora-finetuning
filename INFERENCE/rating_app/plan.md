# Plan: making `rating_app` adaptable for future evaluation tests

> **SUPERSEDED (2026-10-07).** This plan was realized in the **external** app
> `https://github.com/akbargherbal/ai_music_rating_app.git` (package layout, scorecard
> library, run folders, blind mode). Kept for history — see
> [`docs/LISTENING_EVAL.md`](../../docs/LISTENING_EVAL.md).

## 1. What's in the way today

| Area | Current behaviour | Why it limits you |
|---|---|---|
| Questions | `DEFAULT_CRITERIA` is hardcoded and Arabic/maqam-flavoured. JSON overrides exist but are only reached via `--fields`, `<out>/criteria.json` or `<audio>/_criteria.json`. | Only one criteria file is live at a time. Switching test types means overwriting a file. |
| Precedence | The web editor writes `<out>/criteria.json`, which silently shadows `<audio>/_criteria.json`. | A new scorecard dropped next to the audio can be ignored, with no indication why. |
| Global state | `load_criteria()` mutates the module-level `SUMMARY_METRIC` as a side effect and is re-run on every request. | Hidden coupling, hard to test, and it breaks if you ever run two sessions. |
| Settings | `cfg` is just the argparse namespace. `session.json` stores only `audio` and `label`. Extensions, sidecar filenames, grouping rules and report layout are constants in code. | Every behaviour change means editing `app.py`. |
| Results | A single `evaluations.json` per `--out`, keyed by track name, with no record of which questions were asked. | If you edit the scorecard mid-run, old and new answers mix. Two runs sharing an `--out` collide. |
| Track metadata | Only `_knob.json`/`_meta.json` per folder, reduced to a one-line label. | For prompt/settings comparisons you want the full prompt and parameters visible while listening and in the report. |
| UI/report | HTML is inline strings stitched with `.replace()`. The report only ranks by one metric. | Adding a question type or report section means touching several places. |

## 2. Core idea: separate three things

1. **Scorecard** is the questions. It's reusable across runs and lives in its own JSON file.
2. **Settings/config** is how the app and a run behave: discovery rules, blinding, report options, port and so on.
3. **Run** is one evaluation. It binds an audio folder, a scorecard and settings to a results file.

Every loading mechanism you asked for (browse, paste, scan a directory) then just becomes a different way of picking a scorecard or a config.

## 3. Target layout

```
rating_app/
├── app.py                 # thin entry point: parse CLI → create_app()
├── rating_app/
│   ├── cli.py             # argparse only
│   ├── settings.py        # layered settings loader (see §5)
│   ├── scorecard.py       # load / validate / normalize questions
│   ├── discovery.py       # find tracks, read sidecar metadata
│   ├── store.py           # results persistence, atomic writes, migrations
│   ├── report.py          # Markdown / CSV / JSON export
│   ├── paths.py           # safe server-side path browsing
│   └── web/               # routes + templates/ + static/
├── scorecards/            # your library: default.json, prompt_ab.json, ...
├── configs/               # named settings presets
├── runs/<run_id>/         # run.json, results.json, scorecard.snapshot.json
└── tests/
```

`app.py` stays the command you run (`py app.py`), so your Windows workflow doesn't change. Each module is small, and the pure-logic ones (`scorecard`, `settings`, `discovery`, `report`) are testable without Flask.

## 4. The scorecard file

**Format.** Keep JSON, since it matches what you have and what the web editor already handles. Add a few top-level fields:

- `schema_version`
- `name` / `description`
- `summary_metric` (moves out of the global)
- `sections` (optional grouping of questions on the page)
- `criteria` (the list)

A tiny example of the shape:

```json
{
  "schema_version": 1,
  "name": "Prompt A/B — vocals",
  "summary_metric": "overall",
  "criteria": [
    {"key": "overall", "type": "rating", "max": 5, "label": "Overall"},
    {"key": "artifacts", "type": "choice", "options": ["none", "minor", "major"]},
    {"key": "why", "type": "notes", "show_if": {"key": "overall", "lte": 2}}
  ]
}
```

**Question types to support** (existing ones kept as-is):

- `rating`, `choice`, `number`, `notes`, all unchanged
- `multi_choice` (e.g. tick every artifact heard)
- `boolean`
- `scale_labels` on ratings (e.g. 1 = "unusable", 5 = "release-ready")
- Optional per-question fields: `required`, `default`, `help`, `show_if`
- Later: pairwise A/B preference, which is a different data shape (see §9)

**Validation.** One `validate_scorecard()` returns a list of human-readable errors with the offending key. These are surfaced on the `/criteria` page before saving: duplicate keys, a `summary_metric` that doesn't exist, a choice with no options. The app should never silently fall back to the default when a file is broken, because today bad JSON is just `continue`d past.

**Built-in default.** Move `DEFAULT_CRITERIA` into `scorecards/default.json` and make it genre-neutral. The maqam/diction questions become `scorecards/arabic_vocal.json`. The code keeps only a minimal last-resort fallback.

## 5. Settings and config

**What moves out of code into settings:**

- Server: `host`, `port`, `strict_port`
- Paths: `out`, `runs_dir`, `scorecard_dirs` (where to scan), `config_dirs`
- Discovery: `audio_exts`, `group_by` (parent folder, filename pattern, or none), sidecar filenames, ignore globs
- Behaviour: `blind` (hide folder/arm labels and shuffle order with a stored seed), `autosave`, `save_and_advance` default
- Report: which sections to include, grouping, extra metrics

**Precedence**, as one documented rule used everywhere (CLI flag > environment variable > explicit config file > `<audio>/_rating.json` > user-level config > built-in defaults):

`settings.py` builds the merged settings object once. The UI shows the effective value and where it came from (e.g. `scorecard: prompt_ab.json ← --scorecard`). That removes the "why is my file being ignored" problem.

**Config format.** Use JSON for consistency. TOML is a reasonable alternative since `tomllib` is in the stdlib on Python 3.11+, but supporting two formats adds surface area, so I'd start with JSON only.

**Typed settings.** A `@dataclass` (or `TypedDict`) with defaults, plus a single `from_layers()` merge function. I'd avoid pydantic and keep the dependency list at Flask only. `jsonschema` can be an optional extra for strict validation.

## 6. Loading scorecards and configs: the four ways

All four resolve to a validated path or payload, then go through the same loader:

1. **CLI flags**: `--scorecard PATH` and `--config PATH`. `--fields` stays as a deprecated alias.
2. **Paste a path** in the web UI: a text box on `/criteria` and `/setup`, with a "Validate" button that previews the questions without activating them.
3. **Browse**: a browser file input can't expose the real filesystem path, only the content. So "browse" has to be one of two things:
   - a **server-side file picker**: a small `/browse` endpoint that lists directories and `.json` files and lets you click through. This is the right choice for a local app.
   - **upload / paste content**: the file is copied into `scorecards/` and then used. This is a good fallback.
4. **Scan a directory**: list every valid scorecard in `scorecard_dirs`, shown as a dropdown with name and description. This is the day-to-day workflow: pick "Prompt A/B" from a list.

**Safety.** The folder browser should only run when bound to loopback, or be restricted to configured roots if `--host 0.0.0.0` is used. It also needs the same traversal protection the `/audio` route already has.

**Fixing the shadowing bug.** The active scorecard becomes an explicit run setting, not "whichever file is found first". The web editor saves to a named file in `scorecards/` (Save / Save as) instead of overwriting `<out>/criteria.json`.

## 7. Runs and data integrity

- **Run folder** (`runs/<run_id>/`) holds `run.json` (audio path, label, settings used), `results.json` and a **frozen copy of the scorecard** as it was when the run started. Two experiments can no longer collide.
- **Scorecard drift.** Edit a scorecard mid-run and the app compares keys against the snapshot. Results for removed questions are kept (shown as "orphaned") rather than lost, and new questions show as unanswered.
- **Schema versioning.** `schema_version` in every file, with a small migration function so your existing `evaluations.json` imports cleanly.
- **Atomic writes** (write to a temp file, then `os.replace`) so a crash can't corrupt results.
- **Caching.** Discover tracks and load the scorecard once per run, with a "rescan" button, rather than on every request as `ctx()` does now.

## 8. Richer track metadata (prompt and settings comparisons)

Since you're comparing prompts and generation settings, make that metadata first-class:

- Per-track and per-folder sidecars (`_meta.json`, or `<track>.json`) can carry arbitrary key/values: `prompt`, `seed`, `model`, `cfg_scale`, `duration` and so on.
- The rating page shows them in a collapsible "generation settings" panel next to the player.
- The report can include chosen metadata fields as columns (`report.columns: ["prompt","seed"]`).
- The existing `_knob.json` / `labels.json` keep working. The new sidecar is a superset.

## 9. Blinding and comparison modes

- **Blind mode** (already flagged as a gap in your README): hide the folder/arm and filename, randomise order with a seed stored in `run.json` so it's reproducible, and reveal in the report.
- **Pairwise / A-B** as a later scorecard mode: a question type that shows two tracks and records a preference. It needs its own data shape (`pair_id`, `winner`), so I'd defer it until the basics are done.

## 10. Report and export

- Make the report driven by settings plus the scorecard: for each `rating` criterion, per-group mean, n and standard deviation. For each `choice`, a count distribution. Not just one `summary_metric`.
- Include the scorecard name and a settings summary in the header so a report is self-describing.
- Add **CSV** and **JSON** export beside Markdown, since you'll likely want to analyse results in pandas.
- Keep the Markdown export as the primary format, as it is now.

## 11. UI structure

- Move HTML out of the inline strings into `templates/` with a real `base.html` and Jinja `{% extends %}`. That replaces the `PAGE.replace(...)` trick.
- Render questions via one partial per type, so adding a question type means one new partial plus one entry in the normalizer.
- Add a single **Run settings** page showing the effective settings and their sources, plus the scorecard picker and path picker.

## 12. Phased roadmap

Each phase is shippable on its own and leaves the app working.

| Phase | Work | Done when |
|---|---|---|
| **0. Safety net** | Add tests around `discover`, `normalize_criteria`, `is_done` and `render_markdown`, using a tiny fixture folder. | Current behaviour is pinned by tests. |
| **1. Extract scorecard** | Move defaults to `scorecards/default.json`, add `scorecard.py` with validation, remove the `SUMMARY_METRIC` global, add `--scorecard`. | You can swap scorecards by flag, and errors are readable. |
| **2. Settings layer** | Add `settings.py` with the precedence rule and a `--config` file. Show effective settings in the UI. | No behavioural constants remain in `app.py`. |
| **3. Loaders** | Add the scorecard library dropdown, paste-path with preview, the server-side browser, and Save / Save as. | All four loading methods work, and the shadowing bug is gone. |
| **4. Runs** | Add run folders, scorecard snapshot, drift handling, atomic writes and migration of old `evaluations.json`. | Two runs can't clobber each other, and old data imports. |
| **5. Templates and types** | Split templates, add `multi_choice`, `boolean`, `show_if`, scale labels. | A new question type is a one-partial change. |
| **6. Metadata, blind mode, reports** | Metadata panel, blind mode, per-criterion stats, CSV/JSON export. | Prompt/settings comparisons are readable end to end. |

## 13. Defaults I'd go with unless you object

- JSON everywhere, no TOML or YAML.
- Flask stays the only hard dependency.
- A package layout with a thin `app.py`, since you want questions separated from code.
- Existing `criteria.json`, `_criteria.json`, `_knob.json` and `evaluations.json` keep working, via compatibility shims and a one-time import.
- Pairwise A/B deferred to after Phase 6.

If you'd like this saved as a `PLAN.md` for the repo, I can do that. When you're ready to start, Phase 0 and Phase 1 together are the best first step, since they pin the current behaviour and then pull the questions out of `app.py`.