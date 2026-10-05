# pron_eval_app

A tiny single-file Flask app for scoring the held-out **2:255** pron probe
(base / `quran_only` / each `quran_ahh_r8` checkpoint, both scripts) and exporting a
**Markdown report** you can hand back to the agent.

Self-contained: the held-out text and the hard-letter anchors are embedded verbatim from
`INFERENCE/yue2_eval_heldout/quran_heldout.json` — the app needs nothing else from the repo.
Scoring fields match `agent_notes/T4_listening_checklist.md`.

## Run

```bash
pip install -r requirements.txt          # or: pip install flask
python app.py --audio ~/Downloads/quran_pt_probe --out ./eval_out
# open http://127.0.0.1:5000
```

- `--audio` — folder with the downloaded `*_<script>_<seed>.wav` renders
  (`base_uthmani_20261004.wav`, …). Default `./quran_pt_probe`.
- `--out` — where `evaluations.json` and the report live. Default `./eval_out`.
- It discovers whatever arms are present, so `c9000`/`final` appear automatically once rendered.

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

## Notes

- Thresholds in the suggested verdict (base clean ⇔ completion `C`, `hard_err ≤ 1/18`,
  `word_err ≤ 2/50`) are proposals — set your own; criteria are yours (AGENTS.md §8).
- No blinding here: files are already arm-named. For a label-blind listen use
  `INFERENCE/prepare_ab_eval.py` first, then score the shuffled labels.
- Bind to `--host 0.0.0.0` only if you need to reach it from another device on the LAN.
