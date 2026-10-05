#!/usr/bin/env python3
"""pron_eval_app - a small Flask app to score the held-out 2:255 pron probe and export a
shareable Markdown report.

Self-contained: the held-out text + hard-letter anchors are embedded verbatim from
`INFERENCE/yue2_eval_heldout/quran_heldout.json`, so this file needs nothing from the repo.

    pip install flask
    python app.py --audio ~/Downloads/quran_pt_probe --out ./eval_out
    # open http://127.0.0.1:5000

Score one track at a time: tap each word you heard wrong on the grid (counts are computed
for you), answer the plain-language questions, save. `GET /report.md` returns the Markdown
to hand back to the agent.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
from pathlib import Path

from flask import (Flask, Response, abort, redirect, render_template_string, request,
                   send_from_directory, url_for)

# --------------------------------------------------------------------------- instrument
AYA = {  # verbatim from INFERENCE/yue2_eval_heldout/quran_heldout.json
    "key": "002255",
    "words": 58,
    "hard_letters": ["ح", "خ", "ض", "ط", "ظ", "ع", "ق"],
    "uthmani": "ٱللَّهُ لَآ إِلَـٰهَ إِلَّا هُوَ ٱلْحَىُّ ٱلْقَيُّومُ ۚ لَا تَأْخُذُهُۥ سِنَةٌۭ وَلَا نَوْمٌۭ ۚ لَّهُۥ مَا فِى ٱلسَّمَـٰوَٰتِ وَمَا فِى ٱلْأَرْضِ ۗ مَن ذَا ٱلَّذِى يَشْفَعُ عِندَهُۥٓ إِلَّا بِإِذْنِهِۦ ۚ يَعْلَمُ مَا بَيْنَ أَيْدِيهِمْ وَمَا خَلْفَهُمْ ۖ وَلَا يُحِيطُونَ بِشَىْءٍۢ مِّنْ عِلْمِهِۦٓ إِلَّا بِمَا شَآءَ ۚ وَسِعَ كُرْسِيُّهُ ٱلسَّمَـٰوَٰتِ وَٱلْأَرْضَ ۖ وَلَا يَـُٔودُهُۥ حِفْظُهُمَا ۚ وَهُوَ ٱلْعَلِىُّ ٱلْعَظِيمُ",  # noqa: E501
    "simple": "اللَّهُ لَا إِلَـٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ ۚ لَا تَأْخُذُهُ سِنَةٌ وَلَا نَوْمٌ ۚ لَّهُ مَا فِي السَّمَاوَاتِ وَمَا فِي الْأَرْضِ ۗ مَن ذَا الَّذِي يَشْفَعُ عِندَهُ إِلَّا بِإِذْنِهِ ۚ يَعْلَمُ مَا بَيْنَ أَيْدِيهِمْ وَمَا خَلْفَهُمْ ۖ وَلَا يُحِيطُونَ بِشَيْءٍ مِّنْ عِلْمِهِ إِلَّا بِمَا شَاءَ ۚ وَسِعَ كُرْسِيُّهُ السَّمَاوَاتِ وَالْأَرْضَ ۖ وَلَا يَئُودُهُ حِفْظُهُمَا ۚ وَهُوَ الْعَلِيُّ الْعَظِيمُ",  # noqa: E501
}
SCRIPTS = ("uthmani", "simple")
HARD = set(AYA["hard_letters"])
HARD_COUNT = 18  # total hard-letter occurrences in the aya
MARKS = set("ۖۗۘۙۚۛۜ۝")

ARM_LABELS = {
    "base": "Base model — the ceiling reference",
    "quran_only": "quran_only (no AHH)",
    "final": "Final checkpoint",
}


def arm_label(arm: str) -> str:
    if arm in ARM_LABELS:
        return ARM_LABELS[arm]
    if re.fullmatch(r"c\d+", arm):
        return f"Checkpoint @ {int(arm[1:]):,} steps"
    return arm


# --- run / knob grouping -----------------------------------------------------
# A batch can nest each config under its own folder (e.g. the Phase 2 knob probe:
# quran_knob_<cfg>/<arm>_<script>_<seed>.wav). The folder is the knob; tracks with
# the same arm+script in different knobs must not collide, so the folder is part
# of a track's key. A flat folder (the Phase 1 probe) has group == "".
KNOB_RANK = {"g1.0": 0, "g1.5": 1, "t0.8": 2, "rp1.4": 3, "pw100": 4}


def group_name(group: str) -> str:
    return Path(group).name if group else ""


def group_rank(group: str) -> tuple:
    if not group:
        return (-1, 0, "")
    name = group_name(group)
    knob = name[len("quran_knob_"):] if name.startswith("quran_knob_") else name
    return (0, KNOB_RANK.get(knob, 99), knob)


def group_label(group: str, audio_dir: Path) -> str:
    """Prefer the knob folder's `_knob.json` (`<cfg>: <opts>`); else the folder name."""
    if not group:
        return ""
    knob_json = Path(audio_dir) / group / "_knob.json"
    if knob_json.is_file():
        try:
            meta = json.loads(knob_json.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            meta = {}
        cfg = str(meta.get("config", "")).strip()
        opts = str(meta.get("extra_request_opts", "")).strip()
        if opts:
            return f"{cfg}: {opts}" if cfg else opts
        if cfg:
            return cfg
    return group_name(group)


# hard-letter anchors: (1-based word #, word, letters, target)
ANCHORS = [
    (5, "ٱلْحَىُّ", "ح", "voiceless pharyngeal — breathy, deep in the throat (not «h» or a glottal stop)"),
    (6, "ٱلْقَيُّومُ", "ق", "voiceless uvular stop — a deep «q», not ك / غ / hamza"),
    (9, "تَأْخُذُهُ", "خ", "voiceless uvular fricative — raspy «kh», not ك / غ"),
    (19, "ٱلْأَرْضِ", "ض", "emphatic «d» — heavy/backed, not د / ظ"),
    (23, "يَشْفَعُ", "ع", "voiced pharyngeal — a squeeze in the throat, not ʾ / a plain vowel"),
    (24, "عِندَهُ", "ع", "voiced pharyngeal"),
    (27, "يَعْلَمُ", "ع", "voiced pharyngeal"),
    (32, "خَلْفَهُمْ", "خ", "voiceless uvular fricative"),
    (34, "يُحِيطُونَ", "ح+ط", "ح pharyngeal; ط emphatic «t» (heavy, backed)"),
    (37, "عِلْمِهِ", "ع", "voiced pharyngeal"),
    (41, "وَسِعَ", "ع", "voiced pharyngeal"),
    (44, "وَٱلْأَرْضَ", "ض", "emphatic «d»"),
    (47, "حِفْظُهُمَا", "ح+ظ", "ح pharyngeal; ظ emphatic «th» (heavy, voiced)"),
    (49, "ٱلْعَلِىُّ", "ع", "voiced pharyngeal"),
    (50, "ٱلْعَظِيمُ", "ع+ظ", "ع pharyngeal; ظ emphatic interdental"),
]
HARD_BY_WORD = {n: l for n, _, l, _ in ANCHORS}

# scorecard - plain-language questions (values are what get stored/exported)
FIELDS = [
    {"key": "completion", "label": "1. Did it recite the whole ayah?", "type": "radio",
     "help": "Just listen once first — before counting anything.",
     "options": [{"v": "C", "t": "Yes — all the words, in order"},
                 {"v": "T", "t": "No — it cut off early"},
                 {"v": "L", "t": "It looped / repeated itself"},
                 {"v": "X", "t": "Garbled or something else"}]},
    {"key": "word_err", "label": "2. Words it got wrong", "type": "number", "min": 0, "max": 50,
     "help": "Computed from the word grid below — you can override it."},
    {"key": "hard_err", "label": "3. Hard-letter errors", "type": "number", "min": 0, "max": HARD_COUNT,
     "help": "Computed too: wrong words that contain ح خ ع ق ط ض ظ (out of 18)."},
    {"key": "waqf", "label": "4. Pausing / phrasing", "type": "radio",
     "options": [{"v": 2, "t": "Natural"}, {"v": 1, "t": "A few pauses off"},
                 {"v": 0, "t": "Rushed or random"}]},
    {"key": "madd", "label": "5. Elongation (the long vowels)", "type": "radio",
     "options": [{"v": 2, "t": "Natural"}, {"v": 1, "t": "A bit off"},
                 {"v": 0, "t": "Distorted the words"}]},
    {"key": "bleed", "label": "6. Do the mistakes sit inside the stretched vowels?", "type": "radio",
     "options": [{"v": "Y", "t": "Yes, mostly"}, {"v": "N", "t": "No, separate"}]},
    {"key": "intelligible", "label": "7. Could someone understand it from the audio alone?", "type": "radio",
     "options": [{"v": 2, "t": "Yes, clearly"}, {"v": 1, "t": "Partly"}, {"v": 0, "t": "No"}]},
]
FIELD_KEYS = [f["key"] for f in FIELDS]
ERROR_TYPES = [("S", "wrong letter"), ("D", "dropped sound"), ("A", "extra sound"),
               ("V", "wrong vowel"), ("O", "wrong order"), ("N", "non-word / noise")]

# suggested (not binding) ceiling thresholds - the user sets the real ones (AGENTS.md §8)
BASE_HARD_MAX = 1
BASE_WORD_MAX = 2

# --------------------------------------------------------------------------- helpers
def tokenize(text: str):
    """[(1-based word no, token, is_pause_mark)]."""
    out, n = [], 0
    for tok in text.split():
        if tok and all(c in MARKS for c in tok):
            out.append((n, tok, True))
        else:
            n += 1
            out.append((n, tok, False))
    return out


def hard_in(token: str) -> int:
    return sum(1 for c in token if c in HARD)


def parse_track(name: str):
    parts = name.rsplit("_", 2)
    if len(parts) != 3:
        return None
    arm, script, seed = parts
    if script not in SCRIPTS or not seed.isdigit():
        return None
    return arm, script, seed


def arm_rank(arm: str) -> tuple:
    if arm == "base":
        return (0, 0)
    if arm == "quran_only":
        return (1, 0)
    if re.fullmatch(r"c\d+", arm):
        return (2, int(arm[1:]))
    if arm == "final":
        return (3, 0)
    return (4, 0)


def discover(audio_dir: Path) -> list[dict]:
    """Find renders under audio_dir, recursing into per-run/per-knob subfolders.

    A file is a track when its stem parses as ``<arm>_<script>_<seed>``. A track
    living in a subfolder is keyed and labelled by that folder (the knob/run), so
    identically named renders across knobs never collide. A flat folder (group
    ``""``) behaves exactly as before.
    """
    tracks = []
    for wav in sorted(audio_dir.rglob("*.wav")):
        parsed = parse_track(wav.stem)
        if not parsed:
            continue
        arm, script, seed = parsed
        rel = wav.relative_to(audio_dir)
        group = "" if rel.parent == Path(".") else rel.parent.as_posix()
        tracks.append({"name": rel.with_suffix("").as_posix(), "arm": arm, "script": script,
                       "seed": seed, "file": rel.as_posix(), "group": group,
                       "group_label": group_label(group, audio_dir), "label": arm_label(arm)})
    tracks.sort(key=lambda t: (SCRIPTS.index(t["script"]), group_rank(t["group"]),
                               arm_rank(t["arm"]), t["seed"]))
    return tracks


def sections_of(tracks: list[dict]) -> list[tuple]:
    """[(script, [(group_label, [tracks...]), ...]), ...] for the index page."""
    out = []
    for script in SCRIPTS:
        sel = [t for t in tracks if t["script"] == script]
        if not sel:
            continue
        groups: list = []
        index: dict = {}
        for t in sel:
            g = t["group"]
            if g not in index:
                index[g] = len(groups)
                groups.append((t["group_label"] if g else "", []))
            groups[index[g]][1].append(t)
        out.append((script, groups))
    return out


def load_state(path: Path) -> dict:
    if path.is_file():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pass
    return {"meta": {}, "tracks": {}}


def save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def is_done(rec: dict) -> bool:
    return bool(rec) and str(rec.get("completion", "")).strip() != "" \
        and str(rec.get("word_err", "")).strip() != "" and str(rec.get("hard_err", "")).strip() != ""


def _int(v, default=None):
    try:
        return int(str(v).strip())
    except (TypeError, ValueError):
        return default


def _knob_verdict(tracks: list[dict], recs: dict) -> list[str]:
    """Non-binding read-out for a grouped (knob/run) batch that has no `base` arm."""
    lines: list[str] = []
    labels = {t["group"]: t["group_label"] for t in tracks if t["group"]}
    for script in SCRIPTS:
        sel = [t for t in tracks if t["script"] == script and t["group"]]
        if not sel:
            continue
        lines.append(f"**{script}** — by knob (non-binding):")
        for g in sorted({t["group"] for t in sel}, key=group_rank):
            rows = []
            for t in (x for x in sel if x["group"] == g):
                r = recs.get(t["name"], {})
                if not is_done(r):
                    continue
                rows.append(f"{t['arm']}: finished {r.get('completion', '?')}, "
                            f"{r.get('hard_err', '?')}/18 hard, {r.get('word_err', '?')}/50 words")
            if rows:
                lines.append(f"- {labels.get(g, g)} — " + "; ".join(rows))
        loops = [(labels.get(t["group"], t["group"]), t["arm"]) for t in sel
                 if str(recs.get(t["name"], {}).get("completion", "")).strip().upper() == "L"]
        if loops:
            lines.append("- still looping / restarting: "
                         + ", ".join(f"{g}·{a}" for g, a in loops))
        bleed = [(labels.get(t["group"], t["group"]), t["arm"]) for t in sel
                 if recs.get(t["name"], {}).get("bleed") == "Y"]
        if bleed:
            lines.append("- mistakes in the stretched vowels (reverb-ish) on: "
                         + ", ".join(f"{g}·{a}" for g, a in bleed))
    if not lines:
        lines.append("_(no rows scored yet)_")
    lines += ["", "> No `base` arm in this batch, so the ceiling check can't run here. Compare "
              "each knob against the default-knob anchor separately (Phase 2, "
              "QURAN_PRON_REVIEW.md §2.5)."]
    return lines


def suggested_verdict(tracks: list[dict], state: dict) -> list[str]:
    recs = state["tracks"]
    if any(t["group"] for t in tracks) or not any(t["arm"] == "base" for t in tracks):
        return _knob_verdict(tracks, recs)
    lines = []
    by = {(t["arm"], t["script"]): recs.get(t["name"], {}) for t in tracks}
    for script in SCRIPTS:
        base = by.get(("base", script), {})
        if not is_done(base):
            lines.append(f"**{script}** — base not scored yet.")
            continue
        h, w = _int(base.get("hard_err"), 99), _int(base.get("word_err"), 99)
        clean = base.get("completion") == "C" and h <= BASE_HARD_MAX and w <= BASE_WORD_MAX
        if clean:
            lines.append(f"**{script}** — base looks clean (finished, {h}/18 hard, {w}/50 words) "
                         f"⇒ the model *can* pronounce these; the differences below are the adapter's doing.")
        else:
            lines.append(f"**{script}** — the base itself got hard letters wrong ({h}/18 hard, "
                         f"{w}/50 words) ⇒ **representational ceiling suspected** "
                         f"(QURAN_PRON_REVIEW.md §5) — a stopping signal for the LoRA line.")
        arms = [t for t in tracks if t["script"] == script and t["arm"] != "base"]
        scored = [(t, by[(t["arm"], script)]) for t in arms if is_done(by.get((t["arm"], script), {}))]
        if scored:
            best = min(scored, key=lambda tr: (_int(tr[1].get("hard_err"), 99),
                                               _int(tr[1].get("word_err"), 99)))
            worse = [t["arm"] for t, r in scored
                     if _int(r.get("hard_err"), 99) > h or _int(r.get("word_err"), 99) > w]
            lines.append(f"- best so far: **{best[0]['arm']}** "
                         f"({best[1].get('hard_err')}/18 hard, {best[1].get('word_err')}/50 words).")
            if worse:
                lines.append(f"- more errors than base: {', '.join(worse)} (degradation / forgetting).")
        bleed = [t["arm"] for t in arms if by.get((t["arm"], script), {}).get("bleed") == "Y"]
        if bleed:
            lines.append(f"- mistakes sit in stretched vowels on: {', '.join(bleed)} — "
                         f"that's a generation/knob issue, not the weights (feeds Phase 2).")
    return lines


# --------------------------------------------------------------------------- markdown
def render_markdown(tracks: list[dict], state: dict, audio_dir: Path) -> str:
    recs = state["tracks"]
    meta = state.get("meta", {})
    now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    seeds = sorted({t["seed"] for t in tracks})
    grouped = any(t["group"] for t in tracks)
    groups = sorted({t["group"] for t in tracks if t["group"]}, key=group_rank)
    scope = f"{len(groups)} knobs/runs × " if grouped else ""
    L = ["# Pron-eval report — held-out 2:255 (Āyat al-Kursī)", "",
         f"_Exported {now} by `pron_eval_app`._", "", "## Setup", "",
         f"- audio dir: `{audio_dir}`",
         f"- run: `{meta.get('label', 'quran_pt_probe')}` · seed {', '.join(seeds) or '?'} · cap 7500",
         f"- tracks: {len(tracks)} ({scope}{len({t['arm'] for t in tracks})} arms × "
         f"{len({t['script'] for t in tracks})} scripts)",
         "- instrument: 50 lexical words + 8 waqf marks (= the manifest's 58 tokens); "
         "7 hard letters over 15 anchor words (18 occurrences).",
         "- scale: words wrong /50 · hard-letter errors /18 · pausing /2 · elongation /2 · "
         "intelligibility /2", "", "## Score table", ""]
    if grouped:
        L += ["| knob/run | arm | script | done | finished | words wrong /50 | hard-letter errors /18 | "
              "pausing /2 | elongation /2 | stretch-vowel bleed | intelligible /2 |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
        for t in tracks:
            r = recs.get(t["name"], {})
            L.append("| {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} |".format(
                t["group_label"] or t["group"], t["arm"], t["script"], "Y" if is_done(r) else "—",
                r.get("completion", ""), r.get("word_err", ""), r.get("hard_err", ""),
                r.get("waqf", ""), r.get("madd", ""), r.get("bleed", ""), r.get("intelligible", "")))
    else:
        L += ["| arm | script | done | finished | words wrong /50 | hard-letter errors /18 | "
              "pausing /2 | elongation /2 | stretch-vowel bleed | intelligible /2 |",
              "|---|---|---|---|---|---|---|---|---|---|"]
        for t in tracks:
            r = recs.get(t["name"], {})
            L.append("| {} | {} | {} | {} | {} | {} | {} | {} | {} | {} |".format(
                t["arm"], t["script"], "Y" if is_done(r) else "—",
                r.get("completion", ""), r.get("word_err", ""), r.get("hard_err", ""),
                r.get("waqf", ""), r.get("madd", ""), r.get("bleed", ""), r.get("intelligible", "")))
    L += ["", "## Suggested verdict (auto — confirm before acting)", ""]
    L += suggested_verdict(tracks, state) or ["_(no rows scored yet)_"]
    L += ["", "> Base is treated as clean if it finished and had ≤ "
          f"{BASE_HARD_MAX}/18 hard-letter errors and ≤ {BASE_WORD_MAX}/50 wrong words. "
          "Proposed, not binding.", "", "## Per-track notes", ""]
    any_notes = False
    for t in tracks:
        r = recs.get(t["name"], {})
        if not r or not any(str(r.get(k, "")).strip() for k in FIELD_KEYS + ["notes", "word_flags"]):
            continue
        any_notes = True
        L.append(f"### `{t['name']}`")
        L.append(f"- finished: `{r.get('completion', '')}` · words wrong {r.get('word_err', '')}/50 · "
                 f"hard-letter errors {r.get('hard_err', '')}/18 · pausing {r.get('waqf', '')}/2 · "
                 f"elongation {r.get('madd', '')}/2 · stretch-vowel bleed {r.get('bleed', '')} · "
                 f"intelligible {r.get('intelligible', '')}/2")
        if r.get("word_flags"):
            flags = sorted(int(x) for x in r["word_flags"])
            L.append(f"- words marked wrong: {', '.join('w'+str(x) for x in flags)}")
        if r.get("notes"):
            L.append(f"- notes: {r['notes']}")
        L.append("")
    if not any_notes:
        L += ["_(none yet)_", ""]
    L += ["## Reference — 2:255", ""]
    for script in SCRIPTS:
        L += [f"**{script}**", "", AYA[script], ""]
    L += ["## Hard-letter anchors", "", "| # | word | letter(s) | what it should be |",
          "|---|---|---|---|"]
    for n, word, letters, target in ANCHORS:
        L.append(f"| {n} | {word} | {letters} | {target} |")
    L += ["", "## Raw evaluation data (`evaluations.json`)", "", "```json",
          json.dumps({"meta": meta, "tracks": recs}, ensure_ascii=False, indent=2), "```", ""]
    return "\n".join(L)


# --------------------------------------------------------------------------- html
PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ title }}</title>
<style>
 :root{--bg:#0f1218;--fg:#e9ebef;--mut:#98a0ad;--card:#171b24;--line:#28303d;--acc:#6ea8fe;
   --ok:#5ad19a;--warn:#e6b450;--bad:#f07070}
 *{box-sizing:border-box}
 body{margin:0;font:15px/1.55 system-ui,Segoe UI,Roboto,sans-serif;background:var(--bg);color:var(--fg)}
 a{color:var(--acc)} h1{font-size:22px;margin:.2em 0} h2{font-size:18px;margin:1.2em 0 .4em}
 header{position:sticky;top:0;z-index:5;background:#0b0e13;border-bottom:1px solid var(--line);
   padding:10px 16px;display:flex;gap:12px;align-items:center;flex-wrap:wrap}
 header .brand{font-weight:700} header .sp{flex:1}
 .wrap{max-width:1000px;margin:0 auto;padding:18px}
 .card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px;margin:14px 0}
 .muted{color:var(--mut)} .small{font-size:13px} .help{color:var(--mut);font-size:13px;margin-top:4px}
 .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px}
 a.track{display:block;background:var(--card);border:1px solid var(--line);border-radius:12px;
   padding:14px;text-decoration:none;color:var(--fg);transition:border-color .1s}
 a.track:hover{border-color:var(--acc)}
 a.track .arm{font-weight:650} a.track .sub{color:var(--mut);font-size:13px;margin-top:2px}
 .chip{display:inline-block;font-size:12px;padding:2px 9px;border-radius:20px;margin-left:6px;vertical-align:middle}
 .chip.ok{background:#14351f;color:var(--ok)} .chip.no{background:#241f16;color:var(--warn)}
 .bar{height:9px;border-radius:6px;background:#232a36;overflow:hidden;margin:6px 0 2px}
 .bar>i{display:block;height:100%;background:linear-gradient(90deg,#4d8bf0,#6ea8fe);width:{{ pct }}%}
 .btn{background:var(--acc);color:#07101f;border:0;border-radius:9px;padding:10px 16px;font-weight:650;
   cursor:pointer;text-decoration:none;display:inline-block;font-size:14px}
 .btn.ghost{background:transparent;color:var(--acc);border:1px solid #3b6dbd}
 .btn.big{padding:12px 20px;font-size:15px}
 audio{width:100%;margin:10px 0}
 .steps{counter-reset:s;list-style:none;padding-left:0;margin:8px 0 0}
 .steps li{position:relative;padding-left:34px;margin:8px 0}
 .steps li:before{counter-increment:s;content:counter(s);position:absolute;left:0;top:0;width:23px;height:23px;
   border-radius:50%;background:#233047;color:#cfe0ff;text-align:center;line-height:23px;font-size:13px;font-weight:700}
 .ref{direction:rtl;text-align:right;font-family:"Amiri","Scheherazade New","Traditional Arabic",serif;
   line-height:2.9;font-size:27px}
 .word{border:1px solid transparent;background:#1d222c;border-radius:9px;padding:6px 10px;margin:3px 2px;
   color:var(--fg);font:inherit;font-size:26px;cursor:pointer;direction:rtl}
 .word:hover{border-color:#3b465a}
 .word .wn{font-size:11px;color:var(--mut);font-family:system-ui;vertical-align:super;margin-inline-start:3px}
 .word .hl{color:#ffd479}
 .word.wrong{background:#3a1f22;border-color:#8a3b3b}
 .word.wrong .hl,.word.wrong .wn{color:#ff9a9a}
 .pause{color:var(--acc);font-size:17px;margin:0 3px}
 .counts{display:flex;gap:18px;flex-wrap:wrap;align-items:center;margin-top:10px}
 .badge{background:#1d222c;border:1px solid var(--line);border-radius:9px;padding:6px 12px;font-size:14px}
 .badge b{font-size:17px}
 .q{margin:18px 0 4px;font-weight:650}
 .seg{display:flex;gap:8px;flex-wrap:wrap;margin-top:6px}
 .seg label{border:1px solid var(--line);border-radius:10px;padding:9px 13px;cursor:pointer;font-size:14px;
   display:inline-flex;align-items:center;gap:7px}
 .seg label:hover{border-color:#3b465a}
 .seg input{position:absolute;opacity:0;pointer-events:none}
 .seg input:checked~span{font-weight:650}
 .seg label:has(input:checked){background:#182a45;border-color:var(--acc)}
 .seg label:has(input:checked.neg){background:#3a1f22;border-color:#8a3b3b}
 .seg label:has(input:checked.mid){background:#332b16;border-color:#a9852f}
 input[type=number]{width:130px;padding:9px;background:#0d1117;color:var(--fg);
   border:1px solid var(--line);border-radius:9px;font-size:15px}
 textarea{width:100%;min-height:80px;background:#0d1117;color:var(--fg);border:1px solid var(--line);
   border-radius:10px;padding:10px;font:inherit}
 pre{background:#0b0e13;border:1px solid var(--line);border-radius:10px;padding:14px;overflow:auto;
   white-space:pre-wrap;word-break:break-word}
 table{width:100%;border-collapse:collapse;font-size:14px}
 th,td{border:1px solid var(--line);padding:7px 9px;text-align:left} th{background:#141922}
 details summary{cursor:pointer;color:var(--mut);margin:6px 0}
 .row{display:flex;gap:12px;align-items:center;flex-wrap:wrap}
</style></head><body>
<header>
  <span class="brand">Quran pronunciation eval</span>
  <span class="muted small">2:255 · {{ done }}/{{ total }} scored</span>
  <span class="sp"></span>
  <a class="btn ghost" href="{{ url_for('index') }}">tracks</a>
  <a class="btn ghost" href="{{ url_for('report') }}">preview report</a>
  <a class="btn" href="{{ url_for('report_md') }}">export .md</a>
</header>
<div class="wrap">
{% block body %}{% endblock %}
</div></body></html>"""

INDEX = PAGE.replace("{% block body %}{% endblock %}", """
{% if saved %}<div class="card" style="border-color:var(--ok)">Saved.</div>{% endif %}
<div class="card">
  <h1>Score the recitations</h1>
  <p class="muted">Each track is a different model or checkpoint reciting the same ayah.
  You listen, tap the words that sound wrong, answer a few questions, save — and the app
  writes the report for you.</p>
  <div class="bar"><i></i></div>
  <div class="small muted">{{ done }} of {{ total }} tracks scored</div>
  <ol class="steps">
    <li>Pick a track below. Do all the <b>{{ scripts[0] }}</b> ones first, then <b>{{ scripts[1] }}</b>.</li>
    <li>Listen once, then tap any word you heard wrong.</li>
    <li>Answer the numbered questions and hit <b>Save &amp; next</b>.</li>
    <li>When you're done, <b>export .md</b> and hand the file back.</li>
  </ol>
  <p class="help">Headphones, one fixed volume, listen at most twice per track.</p>
</div>
{% for script, groups in sections %}
  <h2>{{ script }}</h2>
  {% for glabel, gts in groups %}
  {% if glabel %}<h3 class="muted small" style="margin:14px 0 4px">{{ glabel }}</h3>{% endif %}
  <div class="grid">
  {% for t in gts %}
    <a class="track" href="{{ url_for('track', name=t.name) }}">
      <div class="arm">{{ t.label }}{% if t.name in done_names %}<span class="chip ok">scored</span>
        {% else %}<span class="chip no">to do</span>{% endif %}</div>
      <div class="sub">{{ t.script }} · {{ t.arm }}</div>
    </a>
  {% endfor %}
  </div>
  {% endfor %}
{% endfor %}
""")

TRACK = PAGE.replace("{% block body %}{% endblock %}", """
<div class="card">
  <div class="row">
    <div>
      <h1>{{ t.label }}</h1>
      <div class="muted">{{ t.script }} script · track {{ pos }}/{{ total }} · <code>{{ t.name }}</code></div>
    </div>
    <span class="sp" style="flex:1"></span>
    {% if prev_name %}<a class="btn ghost" href="{{ url_for('track', name=prev_name) }}">← previous</a>{% endif %}
    {% if next_name %}<a class="btn ghost" href="{{ url_for('track', name=next_name) }}">next →</a>{% endif %}
  </div>
  <audio controls preload="metadata" src="{{ url_for('audio', name=t.file) }}"></audio>
  <div class="help">Tap any word you heard wrong (the counts below update themselves).
    Hard letters are highlighted; the blue marks are pause points. <span class="muted">You can undo a tap by tapping again.</span></div>
  <div class="ref" id="wordgrid">{{ grid|safe }}</div>
  <div class="counts">
    <span class="badge">Words wrong: <b id="wc">0</b></span>
    <span class="badge">Hard-letter errors: <b id="hc">0</b> / {{ hard_total }}</span>
    <button type="button" class="btn ghost" id="cleargrid">reset grid</button>
    <span class="help">e.g. tap <b>يُحِيطُونَ</b> if the ط or ح is off.</span>
  </div>
</div>

<form method="post" class="card">
  <input type="hidden" name="next" value="{{ next_name or '' }}">
  <input type="hidden" name="word_flags" id="wordflags" value="{{ flags_json }}">
  {% for f in fields %}
    <div class="q">{{ f.label }}</div>
    {% if f.get('help') %}<div class="help">{{ f.help }}</div>{% endif %}
    {% if f.type == 'radio' %}
      <div class="seg">
      {% for o in f.options %}
        {% set checked = (rec.get(f.key)|string) == (o.v|string) %}
        <label>
          <input type="radio" name="{{ f.key }}" value="{{ o.v }}"
                 class="{% if f.key == 'completion' and o.v != 'C' %}{{ 'mid' if o.v == 'T' else 'neg' }}{% elif f.key in ['waqf','madd','intelligible'] and o.v|string == '0' %}neg{% elif f.key in ['waqf','madd','intelligible'] and o.v|string == '1' %}mid{% endif %}"
                 {% if checked %}checked{% endif %}>
          <span>{{ o.t }}</span>
        </label>
      {% endfor %}
      </div>
    {% else %}
      <input type="number" name="{{ f.key }}" min="{{ f.min }}" max="{{ f.max }}"
             value="{{ rec.get(f.key, '') }}">
    {% endif %}
  {% endfor %}
  <div class="q">Notes (optional)</div>
  <div class="help">Anything worth remembering — e.g. <code>w23 wrong letters</code>,
    <code>w34 dropped</code>, <code>loops at w40</code>. Types: {{ error_legend }}.</div>
  <textarea name="notes">{{ rec.get('notes','') }}</textarea>
  <div class="row" style="margin-top:14px">
    <button type="submit" class="btn big">Save</button>
    {% if next_name %}<button type="submit" class="btn big" name="advance" value="1">Save &amp; next →</button>{% endif %}
  </div>
</form>

<details class="card"><summary>Hard-letter cheat-sheet (the 7 letters that matter here)</summary>
  <table><tr><th>#</th><th>word</th><th>letter(s)</th><th>what it should be</th></tr>
  {% for n,w,l,tg in anchors %}<tr><td>w{{ n }}</td>
    <td style="font-size:23px" dir="rtl">{{ w }}</td><td>{{ l }}</td><td class="help">{{ tg }}</td></tr>{% endfor %}
  </table>
</details>

<script>
(function(){
  const grid=document.getElementById('wordgrid');
  const hidden=document.getElementById('wordflags');
  const wc=document.getElementById('wc'), hc=document.getElementById('hc');
  const words=[...grid.querySelectorAll('.word')];
  let flags=new Set();
  try{ flags=new Set((JSON.parse(hidden.value||'[]')).map(String)); }catch(e){}
  function render(){
    let h=0;
    words.forEach(b=>{ const on=flags.has(b.dataset.n);
      b.classList.toggle('wrong',on); if(on) h+=parseInt(b.dataset.hard||'0',10); });
    wc.textContent=flags.size; hc.textContent=h;
    hidden.value=JSON.stringify([...flags].map(Number).sort((a,b)=>a-b));
    const wf=document.querySelector('input[name=word_err]'), hf=document.querySelector('input[name=hard_err]');
    if(wf) wf.value=flags.size; if(hf) hf.value=h;
  }
  words.forEach(b=>b.addEventListener('click',()=>{
    const n=b.dataset.n; flags.has(n)?flags.delete(n):flags.add(n); render();
  }));
  document.getElementById('cleargrid').addEventListener('click',()=>{ flags.clear(); render(); });
  if(flags.size) render();
})();
</script>
""")

REPORT = PAGE.replace("{% block body %}{% endblock %}", """
<div class="card">
  <div class="row"><h1 style="margin:0">Report preview</h1><span class="sp" style="flex:1"></span>
    <button class="btn" onclick="navigator.clipboard.writeText(document.getElementById('md').innerText).then(()=>this.textContent='copied')">copy markdown</button>
    <a class="btn ghost" href="{{ url_for('report_md') }}">download .md</a></div>
  <pre id="md">{{ md }}</pre>
</div>
""")


# --------------------------------------------------------------------------- app
def create_app(config: dict) -> Flask:
    app = Flask(__name__)
    audio_dir = Path(config["audio"]).expanduser().resolve()
    out_dir = Path(config["out"]).expanduser().resolve()
    state_path = out_dir / "evaluations.json"
    label = config.get("label", "quran_pt_probe")

    def state():
        st = load_state(state_path)
        st.setdefault("meta", {})
        st["meta"].update({"label": label, "audio": str(audio_dir), "out": str(out_dir)})
        st.setdefault("tracks", {})
        return st

    def grid_html(script: str) -> str:
        parts = []
        for n, tok, is_mark in tokenize(AYA[script]):
            if is_mark:
                parts.append(f'<span class="pause">{tok}</span>')
                continue
            body = "".join(f'<span class="hl">{c}</span>' if c in HARD else c for c in tok)
            parts.append(f'<button type="button" class="word" data-n="{n}" '
                         f'data-hard="{hard_in(tok)}" title="word {n}">{body}'
                         f'<span class="wn">{n}</span></button>')
        return " ".join(parts)

    def ctx(**kw):
        st = state()
        ts = discover(audio_dir)
        dn = {t["name"] for t in ts if is_done(st["tracks"].get(t["name"], {}))}
        total = len(ts) or 1
        return dict(audio=str(audio_dir), out=str(out_dir), tracks=ts, scripts=SCRIPTS,
                    sections=sections_of(ts),
                    done=len(dn), total=len(ts), done_names=dn, pct=int(100 * len(dn) / total), **kw)

    @app.get("/")
    def index():
        return render_template_string(INDEX, title="pron-eval · tracks",
                                      saved=request.args.get("saved") == "1", **ctx())

    @app.get("/track/<path:name>")
    def track(name):
        ts = discover(audio_dir)
        match = next((t for t in ts if t["name"] == name), None)
        if not match:
            abort(404)
        i = ts.index(match)
        st = state()
        rec = st["tracks"].get(name, {})
        return render_template_string(
            TRACK, title=f"{match['arm']} · {match['script']}",
            t=match, rec=rec, grid=grid_html(match["script"]), anchors=ANCHORS, fields=FIELDS,
            pos=i + 1, hard_total=HARD_COUNT,
            prev_name=ts[i - 1]["name"] if i > 0 else None,
            next_name=ts[i + 1]["name"] if i + 1 < len(ts) else None,
            flags_json=json.dumps(rec.get("word_flags", [])),
            error_legend=" · ".join(f"{k} = {v}" for k, v in ERROR_TYPES),
            saved=request.args.get("saved") == "1", **ctx())

    @app.post("/track/<path:name>")
    def save(name):
        if not any(t["name"] == name for t in discover(audio_dir)):
            abort(404)
        st = state()
        rec = st["tracks"].get(name, {})
        for f in FIELDS:
            if f["type"] == "radio":
                v = request.form.get(f["key"], "")
                if v == "":
                    rec.pop(f["key"], None)
                else:
                    rec[f["key"]] = _int(v, v) if v.isdigit() else v
            else:
                v = request.form.get(f["key"], "").strip()
                if v == "":
                    rec.pop(f["key"], None)
                else:
                    rec[f["key"]] = _int(v, v)
        raw = request.form.get("word_flags", "").strip()
        if raw:
            try:
                rec["word_flags"] = sorted({int(x) for x in json.loads(raw)})
            except (ValueError, TypeError):
                pass
        else:
            rec.pop("word_flags", None)
        rec["notes"] = request.form.get("notes", "").strip()
        rec["updated"] = _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")
        st["tracks"][name] = rec
        save_state(state_path, st)
        target = request.form.get("next") if request.form.get("advance") == "1" else None
        if target:
            return redirect(url_for("track", name=target))
        return redirect(url_for("track", name=name, saved=1))

    @app.get("/audio/<path:name>")
    def audio(name):
        p = Path(name)
        if p.suffix.lower() != ".wav" or p.is_absolute() or ".." in p.parts:
            abort(404)
        return send_from_directory(audio_dir, name)

    @app.get("/report")
    def report():
        md = render_markdown(discover(audio_dir), state(), audio_dir)
        return render_template_string(REPORT, title="pron-eval · report", md=md, **ctx())

    @app.get("/report.md")
    def report_md():
        md = render_markdown(discover(audio_dir), state(), audio_dir)
        stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M")
        return Response(md, mimetype="text/markdown", headers={
            "Content-Disposition": f"attachment; filename=pron_eval_{stamp}.md"})

    return app


def main() -> int:
    ap = argparse.ArgumentParser(description="score the 2:255 pron probe + export Markdown")
    ap.add_argument("--audio", default="./quran_pt_probe",
                    help="dir with <arm>_<script>_<seed>.wav renders; run/knob subfolders "
                         "are discovered automatically")
    ap.add_argument("--out", default="./eval_out", help="dir for evaluations.json + reports")
    ap.add_argument("--label", default="quran_pt_probe")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=5000)
    ap.add_argument("--debug", action="store_true")
    args = ap.parse_args()
    audio = Path(args.audio).expanduser()
    if not audio.is_dir():
        ap.error(f"--audio dir not found: {audio}")
    app = create_app({"audio": str(audio), "out": args.out, "label": args.label})
    found = len(discover(audio))
    print(f"pron_eval_app: {found} track(s) in {audio}")
    if found == 0:
        print("  (no *_<script>_<seed>.wav files found — check --audio)")
    print(f"  open http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=args.debug)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
