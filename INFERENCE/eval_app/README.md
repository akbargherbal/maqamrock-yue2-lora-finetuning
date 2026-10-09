# pron_eval_app

A tiny single-file Flask app for scoring the held-out **2:255** renders and exporting a
**Markdown report** you can hand back to the agent.

Self-contained: the held-out text and the hard-letter anchors are embedded verbatim from
`INFERENCE/yue2_eval_heldout/quran_heldout.json` — the app needs nothing else from the repo.
Scoring fields match `agent_notes/T4_listening_checklist.md`.

## Run

```bash
pip install -r requirements.txt          # or: pip install flask

# bring a run down from GCS (keeps its folder structure):
mkdir -p ./quran_knob_probe
gsutil -m rsync -r "$GCP_BACKUP_BASE/quran_knob_probe" ./quran_knob_probe

python app.py --audio ./quran_knob_probe --out ./eval_out
# open http://127.0.0.1:5000
```

- `--audio` — folder with the downloaded `*_<script>_<seed>.wav` renders. It **recurses**, so a
  run that nests one folder per config (the Phase 2 knob probe:
  `quran_knob_<cfg>/<arm>_<script>_<seed>.wav`) is picked up directly. The folder (the knob) is
  part of each track's identity, so the same `c4500_simple` render under different knobs never
  collides. A **flat** folder (the Phase 1 probe, e.g. `base_uthmani_20261004.wav`) still works
  unchanged. Default `./quran_pt_probe`.
- `--out` — where `evaluations.json` and the report live. Default `./eval_out`.
- `--label` — run label shown in the report. Default `quran_pt_probe`.
- Whatever arms/knobs are present are discovered automatically.

## Workflow

1. **tracks** → pick one. Score one **script at a time** (uthmani, then simple).
2. On the track page, tap each word you heard **wrong** on the grid — the
   "words wrong" and "hard-letter errors" counts update automatically (hard letters
   ح خ ع ق ط ض ظ are highlighted). Override the numbers by hand only if you need to.
3. Answer the numbered questions (finish/pausing/elongation/…). Hit **Save & next →**
   to walk the tracks in order. Everything persists to `evaluations.json` after each save,
   so you can close the tab and resume.
4. **export .md** downloads `pron_eval_<stamp>.md`: setup, the score table, an
   *auto-suggested* verdict (clearly marked non-binding), per-track notes (including the
   words you flagged), the reference text, the anchor table, and the **raw
   `evaluations.json` in a fenced block** so the agent can read exact numbers.

For a **knob/run** batch the score table gains a `knob/run` column (labelled from each
folder's `_knob.json`, e.g. `g1.5: guidance_scale=1.5`) and the verdict is knob-oriented;
it notes that there is no `base` arm in that batch to check the ceiling against.

## Notes

- Thresholds in the suggested verdict (base clean ⇔ completion `C`, `hard_err ≤ 1/18`,
  `word_err ≤ 2/50`) are proposals — set your own; criteria are yours (AGENTS.md §8).
- No blinding here: files are already arm-named. For a label-blind listen use
  `INFERENCE/prepare_ab_eval.py` first, then score the shuffled labels.
- Bind to `--host 0.0.0.0` only if you need to reach it from another device on the LAN.
