#!/usr/bin/env python3
"""rating_app — a general listening rating app (single-file Flask).

Point it at ANY folder of rendered audio variants, rate each track on a
configurable scorecard, and export a Markdown report. Nothing about a specific
run is hardcoded: the tracks are whatever audio files sit under the folder, the
sub-folders are the "arms"/variants, and the criteria are yours to change in a
JSON file (no code edits).

    pip install -r requirements.txt
    python app.py                       # then paste the folder when asked
    python app.py --audio ~/Downloads/jarir_lever_probe --label jarir_lever_probe
    # open http://127.0.0.1:5000

Design notes
------------
* No audio is bundled or assumed. If --audio is omitted the app asks for the
  track directory on the terminal, and there is a web /setup page to change it
  (and a /criteria page to change the scorecard) at any time.
* Discovery is generic: every ``*.wav/.mp3/.flac/.m4a/.ogg`` under the folder is
  a track; its relative parent folder is its group/arm. Flat folders work too.
* The scorecard is configurable, in precedence order:
      --fields <json>   >   <out>/criteria.json   >   <audio>/_criteria.json
      >   built-in DEFAULT_CRITERIA
  so you can tune the questions once and reuse them for every future run.
* Optional per-folder label: a ``_knob.json`` (or ``_meta.json``) in a folder
  with keys like ``label`` / ``config`` / ``arm`` / ``extra_request_opts``.
  Optional per-file labels: ``labels.json`` at the root, mapping relative path
  (or filename) -> label.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from pathlib import Path

from flask import (Flask, Response, abort, redirect, render_template_string,
                   request, send_from_directory, url_for)

AUDIO_EXTS = (".wav", ".mp3", ".flac", ".m4a", ".ogg", ".opus")

# --------------------------------------------------------------------------- criteria
# The default, run-agnostic scorecard. Override with a criteria.json (see module
# docstring) — you should not need to touch this file again.
DEFAULT_CRITERIA = [
    {"key": "overall", "label": "Overall quality", "type": "rating", "max": 5,
     "help": "Your gut call on the whole take."},
    {"key": "diction", "label": "Vocal diction / clarity", "type": "rating", "max": 5,
     "help": "Are the words clear and correctly pronounced?"},
    {"key": "melody", "label": "Melody / maqam fit", "type": "rating", "max": 5,
     "help": "Does the melodic line sit in the intended maqam / mood?"},
    {"key": "prosody", "label": "Prosody / rhythm / timing", "type": "rating", "max": 5,
     "help": "Phrasing, groove, breath, and timing."},
    {"key": "mix", "label": "Mix / audio quality", "type": "rating", "max": 5,
     "help": "Balance, clarity, artifacts of the mix itself."},
    {"key": "artifacts", "label": "Artifacts", "type": "choice",
     "options": [{"v": "none", "t": "None"}, {"v": "minor", "t": "Minor"},
                 {"v": "major", "t": "Major"}, {"v": "broken", "t": "Broken / unusable"}]},
    {"key": "keep", "label": "Would you keep this take?", "type": "choice",
     "options": [{"v": "yes", "t": "Yes"}, {"v": "maybe", "t": "Maybe"},
                 {"v": "no", "t": "No"}]},
    {"key": "notes", "label": "Notes", "type": "notes", "required": False,
     "help": "Anything worth remembering (e.g. loops at 0:40, wrong word, takes off)."},
]
SUMMARY_METRIC = "overall"   # which rating to rank by (override in criteria.json)


def _norm_options(opts):
    out = []
    for o in opts or []:
        if isinstance(o, dict):
            out.append({"v": o.get("v", o.get("value", "")), "t": o.get("t", o.get("label", str(o.get("v", ""))))})
        else:  # bare value
            out.append({"v": o, "t": str(o)})
    return out


def normalize_criteria(crit: list) -> list:
    out = []
    for c in crit:
        c = dict(c)
        c.setdefault("type", "rating")
        c.setdefault("label", c.get("key", "?"))
        c.setdefault("required", c["type"] != "notes")
        if c["type"] == "rating":
            c.setdefault("max", 5)
        if c["type"] in ("choice", "radio"):
            c["type"] = "choice"
            c["options"] = _norm_options(c.get("options"))
        out.append(c)
    return out


def load_criteria(audio_dir: Path | None, out_dir: Path, fields_path: str | None) -> list:
    """Precedence: --fields > <out>/criteria.json > <audio>/_criteria.json > default."""
    candidates = []
    if fields_path:
        candidates.append(Path(fields_path).expanduser())
    candidates.append(out_dir / "criteria.json")
    if audio_dir:
        candidates.append(audio_dir / "_criteria.json")
    for p in candidates:
        if p and p.is_file():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            crit = data.get("criteria", data) if isinstance(data, dict) else data
            if isinstance(crit, list) and crit:
                global SUMMARY_METRIC
                if isinstance(data, dict) and data.get("summary_metric"):
                    SUMMARY_METRIC = str(data["summary_metric"])
                return normalize_criteria(crit)
    return normalize_criteria(DEFAULT_CRITERIA)


# --------------------------------------------------------------------------- discovery
def meta_label(folder: Path) -> str:
    """Optional human label for a group folder, read from _knob.json/_meta.json."""
    for fn in ("_knob.json", "_meta.json"):
        p = folder / fn
        if not p.is_file():
            continue
        try:
            m = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(m, dict):
            continue
        for k in ("label", "name", "variant", "arm"):
            if str(m.get(k, "")).strip():
                return str(m[k]).strip()
        cfg = str(m.get("config", "")).strip()
        opts = str(m.get("extra_request_opts", m.get("opts", ""))).strip()
        if opts:
            return f"{cfg}: {opts}" if cfg else opts
        if cfg:
            return cfg
    return ""


def load_file_labels(audio_dir: Path) -> dict:
    p = audio_dir / "labels.json"
    if not p.is_file():
        return {}
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def discover(audio_dir: Path) -> list[dict]:
    """Every audio file under audio_dir is a track; its parent folder is its group."""
    flabels = load_file_labels(audio_dir)
    tracks = []
    for f in sorted(audio_dir.rglob("*")):
        if not f.is_file() or f.suffix.lower() not in AUDIO_EXTS:
            continue
        rel = f.relative_to(audio_dir)
        group = "" if rel.parent == Path(".") else rel.parent.as_posix()
        glabel = meta_label(audio_dir / group) if group else ""
        name = rel.as_posix()
        label = str(flabels.get(name) or flabels.get(f.name) or f.stem)
        tracks.append({"name": name, "file": rel.as_posix(), "stem": f.stem,
                       "group": group, "group_label": glabel, "label": label})
    tracks.sort(key=lambda t: (t["group"], t["stem"]))
    return tracks


def sections_of(tracks: list[dict]) -> list[tuple]:
    out, index = [], {}
    for t in tracks:
        g = t["group"]
        if g not in index:
            index[g] = len(out)
            out.append((t["group_label"] if g else "", []))
        out[index[g]][1].append(t)
    return out


# --------------------------------------------------------------------------- state
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


def is_done(rec: dict, criteria: list) -> bool:
    if not rec:
        return False
    for c in criteria:
        if c.get("required", True) and str(rec.get(c["key"], "")).strip() == "":
            return False
    return True


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


# --------------------------------------------------------------------------- markdown
def render_markdown(tracks: list[dict], state: dict, criteria: list, audio_dir: Path, label: str) -> str:
    recs = state["tracks"]
    now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    groups = sorted({t["group"] for t in tracks if t["group"]})
    gl = {t["group"]: t["group_label"] for t in tracks}
    rating_keys = [c for c in criteria if c["type"] == "rating"]
    metric = SUMMARY_METRIC if any(c["key"] == SUMMARY_METRIC and c["type"] == "rating" for c in criteria) \
        else (rating_keys[0]["key"] if rating_keys else None)
    L = [f"# Listening rating report — {label}", "",
         f"_Exported {now} by `rating_app`._", "", "## Setup", "",
         f"- audio dir: `{audio_dir}`",
         f"- tracks: {len(tracks)}" + (f" in {len(groups)} folders/arms" if groups else ""),
         f"- criteria: " + ", ".join(c["label"] for c in criteria), "",
         "## Score table", ""]
    head = ["folder/arm", "track", "done"] + [c["label"] for c in criteria]
    L.append("| " + " | ".join(head) + " |")
    L.append("|" + "---|" * len(head))
    for t in tracks:
        r = recs.get(t["name"], {})
        row = [t["group_label"] or t["group"] or "—", t["label"],
               "Y" if is_done(r, criteria) else "—"]
        row += [str(r.get(c["key"], "")) for c in criteria]
        L.append("| " + " | ".join(row) + " |")
    L += ["", "## Summary by folder/arm", ""]
    if not metric:
        L.append("_(no rating criteria defined)_")
    else:
        mlabel = next(c["label"] for c in criteria if c["key"] == metric)
        stat = {}
        for t in tracks:
            r = recs.get(t["name"], {})
            v = _num(r.get(metric))
            if v is None:
                continue
            s = stat.setdefault(t["group"], {"n": 0, "sum": 0.0})
            s["n"] += 1
            s["sum"] += v
        if stat:
            L += [f"Mean **{mlabel}** per folder (n scored):", "",
                  "| folder/arm | mean | n |", "|---|---|---|"]
            for g, s in sorted(stat.items(), key=lambda kv: -kv[1]["sum"] / kv[1]["n"]):
                L.append(f"| {gl.get(g) or g or '—'} | {s['sum'] / s['n']:.2f} | {s['n']} |")
        else:
            L.append(f"_(no **{mlabel}** ratings yet)_")
    L += ["", "## Per-track notes", ""]
    anyn = False
    for t in tracks:
        r = recs.get(t["name"], {})
        if not r:
            continue
        if not any(str(r.get(c["key"], "")).strip() for c in criteria):
            continue
        anyn = True
        L.append(f"### `{t['name']}`")
        L.append("- " + " · ".join(f"{c['label']}: {r.get(c['key'], '')}"
                                   for c in criteria if str(r.get(c["key"], "")).strip() != ""))
        L.append("")
    if not anyn:
        L += ["_(none yet)_", ""]
    L += ["## Raw evaluation data", "", "```json",
          json.dumps({"meta": state.get("meta", {}), "tracks": recs}, ensure_ascii=False, indent=2),
          "```", ""]
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
 .wrap{max-width:1050px;margin:0 auto;padding:18px}
 .card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px;margin:14px 0}
 .muted{color:var(--mut)} .small{font-size:13px} .help{color:var(--mut);font-size:13px;margin-top:4px}
 .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px}
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
 .q{margin:18px 0 4px;font-weight:650}
 .seg{display:flex;gap:8px;flex-wrap:wrap;margin-top:6px}
 .seg label{border:1px solid var(--line);border-radius:10px;padding:9px 14px;cursor:pointer;font-size:14px;
   display:inline-flex;align-items:center;gap:7px}
 .seg label:hover{border-color:#3b465a}
 .seg input{position:absolute;opacity:0;pointer-events:none}
 .seg label:has(input:checked){background:#182a45;border-color:var(--acc)}
 input[type=number],input[type=text]{padding:9px;background:#0d1117;color:var(--fg);
   border:1px solid var(--line);border-radius:9px;font-size:15px}
 input.wide{width:100%}
 textarea{width:100%;min-height:80px;background:#0d1117;color:var(--fg);border:1px solid var(--line);
   border-radius:10px;padding:10px;font:inherit}
 pre{background:#0b0e13;border:1px solid var(--line);border-radius:10px;padding:14px;overflow:auto;
   white-space:pre-wrap;word-break:break-word}
 table{width:100%;border-collapse:collapse;font-size:14px}
 th,td{border:1px solid var(--line);padding:7px 9px;text-align:left} th{background:#141922}
 .row{display:flex;gap:12px;align-items:center;flex-wrap:wrap}
</style></head><body>
<header>
  <span class="brand">Listening rating</span>
  <span class="muted small">{{ label }} · {{ done }}/{{ total }} rated</span>
  <span class="sp"></span>
  <a class="btn ghost" href="{{ url_for('index') }}">tracks</a>
  <a class="btn ghost" href="{{ url_for('report') }}">report</a>
  <a class="btn ghost" href="{{ url_for('criteria_page') }}">criteria</a>
  <a class="btn ghost" href="{{ url_for('setup') }}">folder</a>
  <a class="btn" href="{{ url_for('report_md') }}">export .md</a>
</header>
<div class="wrap">{% block body %}{% endblock %}</div>
</body></html>"""

SETUP = PAGE.replace("{% block body %}{% endblock %}", """
<div class="card">
  <h1>Track directory</h1>
  <p class="muted">Paste the folder that holds your rendered tracks (it is read in place — nothing is copied).
  Sub-folders become the arms/variants. Example Windows path:
  <code>C:\\Users\\DELL\\Downloads\\jarir_lever_probe</code></p>
  <form method="post">
    <div class="q">Folder</div>
    <input class="wide" type="text" name="audio" value="{{ audio }}" placeholder="C:\\Users\\you\\Downloads\\my_run">
    <div class="q">Run label</div>
    <input class="wide" type="text" name="label" value="{{ label }}" placeholder="my_run">
    <div class="row" style="margin-top:14px">
      <button class="btn big" type="submit">Save</button>
      <span class="help">Saved to <code>{{ session }}</code> and remembered next time.</span>
    </div>
  </form>
</div>
""")

CRITERIA = PAGE.replace("{% block body %}{% endblock %}", """
<div class="card">
  <h1>Scorecard (criteria)</h1>
  <p class="muted">Edit the JSON below to change the questions. It is saved to
  <code>{{ path }}</code> and used from then on. Types:
  <code>rating</code> (1..max), <code>choice</code> (options), <code>number</code>, <code>notes</code>.
  Top-level <code>summary_metric</code> picks the rating to rank folders by.</p>
  <form method="post">
    <textarea name="criteria_json" style="min-height:340px;font-family:ui-monospace,monospace">{{ json }}</textarea>
    <div class="row" style="margin-top:14px">
      <button class="btn big" type="submit">Save criteria</button>
      <a class="btn ghost" href="{{ url_for('criteria_page') }}">reset view</a>
    </div>
  </form>
  {% if err %}<div class="card" style="border-color:var(--bad)">Could not save: {{ err }}</div>{% endif %}
</div>
""")

INDEX = PAGE.replace("{% block body %}{% endblock %}", """
{% if saved %}<div class="card" style="border-color:var(--ok)">Saved.</div>{% endif %}
{% if not total %}
<div class="card"><h1>No tracks found</h1>
  <p class="muted">No audio files under <code>{{ audio }}</code>. Set the folder on the
  <a href="{{ url_for('setup') }}">folder</a> page.</p></div>
{% else %}
<div class="card">
  <h1>Rate the tracks</h1>
  <div class="bar"><i></i></div>
  <div class="small muted">{{ done }} of {{ total }} tracks rated</div>
  <p class="help">Pick a track, listen, answer the criteria, save. Everything persists to
  <code>evaluations.json</code>; export the Markdown when done.</p>
</div>
{% for glabel, gts in sections %}
  {% if glabel %}<h2>{{ glabel }}</h2>{% else %}<h2>tracks</h2>{% endif %}
  <div class="grid">
  {% for t in gts %}
    <a class="track" href="{{ url_for('track', name=t.name) }}">
      <div class="arm">{{ t.label }}{% if t.name in done_names %}<span class="chip ok">rated</span>
        {% else %}<span class="chip no">to do</span>{% endif %}</div>
      <div class="sub">{{ t.group or "root" }}</div>
    </a>
  {% endfor %}
  </div>
{% endfor %}
{% endif %}
""")

TRACK = PAGE.replace("{% block body %}{% endblock %}", """
<div class="card">
  <div class="row">
    <div>
      <h1>{{ t.label }}</h1>
      <div class="muted">{{ t.group or "root" }} · track {{ pos }}/{{ total }} · <code>{{ t.name }}</code></div>
    </div>
    <span class="sp" style="flex:1"></span>
    {% if prev_name %}<a class="btn ghost" href="{{ url_for('track', name=prev_name) }}">← previous</a>{% endif %}
    {% if next_name %}<a class="btn ghost" href="{{ url_for('track', name=next_name) }}">next →</a>{% endif %}
  </div>
  <audio controls preload="metadata" src="{{ url_for('audio', name=t.file) }}"></audio>
</div>
<form method="post" class="card">
  <input type="hidden" name="next" value="{{ next_name or '' }}">
  {% for c in criteria %}
    <div class="q">{{ c.label }}</div>
    {% if c.get('help') %}<div class="help">{{ c.help }}</div>{% endif %}
    {% if c.type == 'rating' %}
      <div class="seg">
      {% for i in range(1, c.max + 1) %}
        <label><input type="radio" name="{{ c.key }}" value="{{ i }}"
          {% if rec.get(c.key)|string == i|string %}checked{% endif %}><span>{{ i }}</span></label>
      {% endfor %}
      </div>
    {% elif c.type == 'choice' %}
      <div class="seg">
      {% for o in c.options %}
        <label><input type="radio" name="{{ c.key }}" value="{{ o.v }}"
          {% if rec.get(c.key)|string == o.v|string %}checked{% endif %}><span>{{ o.t }}</span></label>
      {% endfor %}
      </div>
    {% elif c.type == 'number' %}
      <input type="number" name="{{ c.key }}" value="{{ rec.get(c.key, '') }}">
    {% else %}
      <textarea name="{{ c.key }}">{{ rec.get(c.key, '') }}</textarea>
    {% endif %}
  {% endfor %}
  <div class="row" style="margin-top:16px">
    <button type="submit" class="btn big">Save</button>
    {% if next_name %}<button type="submit" class="btn big" name="advance" value="1">Save &amp; next →</button>{% endif %}
  </div>
</form>
""")

REPORT = PAGE.replace("{% block body %}{% endblock %}", """
<div class="card">
  <div class="row"><h1 style="margin:0">Report</h1><span class="sp" style="flex:1"></span>
    <button class="btn" onclick="navigator.clipboard.writeText(document.getElementById('md').innerText).then(()=>this.textContent='copied')">copy markdown</button>
    <a class="btn ghost" href="{{ url_for('report_md') }}">download .md</a></div>
  <pre id="md">{{ md }}</pre>
</div>
""")


# --------------------------------------------------------------------------- app
def create_app(cfg: dict) -> Flask:
    app = Flask(__name__)
    out_dir = Path(cfg["out"]).expanduser().resolve()
    session_path = out_dir / "session.json"
    state_path = out_dir / "evaluations.json"

    def persist_session():
        out_dir.mkdir(parents=True, exist_ok=True)
        session_path.write_text(json.dumps({"audio": cfg["audio"], "label": cfg["label"]},
                                           ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if cfg.get("audio"):          # remember the chosen folder for next time
        try:
            persist_session()
        except OSError:
            pass

    def audio_path():
        return Path(cfg["audio"]).expanduser().resolve() if cfg.get("audio") else None

    def criteria():
        return load_criteria(audio_path(), out_dir, cfg.get("fields"))

    def state():
        st = load_state(state_path)
        st.setdefault("meta", {})
        st["meta"].update({"label": cfg["label"], "audio": cfg.get("audio"), "out": str(out_dir)})
        st.setdefault("tracks", {})
        return st

    def ctx(**kw):
        a = audio_path()
        ts = discover(a) if a and Path(a).is_dir() else []
        crit = criteria()
        consumed = {c["key"] for c in crit}
        st = state()
        dn = {t["name"] for t in ts if is_done(st["tracks"].get(t["name"], {}), crit)}
        total = len(ts) or 1
        return dict(audio=cfg.get("audio") or "", label=cfg["label"], criteria=crit,
                    sections=sections_of(ts), tracks=ts, done=len(dn), total=len(ts),
                    done_names=dn, pct=int(100 * len(dn) / total), session=str(session_path),
                    consumed=consumed, **kw)

    @app.get("/setup")
    def setup():
        return render_template_string(SETUP, title="rating · folder", **ctx())

    @app.post("/setup")
    def setup_save():
        cfg["audio"] = request.form.get("audio", "").strip().strip('"').strip("'")
        cfg["label"] = request.form.get("label", "").strip() or cfg["label"]
        persist_session()
        return redirect(url_for("index"))

    @app.get("/criteria")
    def criteria_page():
        p = out_dir / "criteria.json"
        eff = criteria()
        data = {"summary_metric": SUMMARY_METRIC, "criteria": eff}
        return render_template_string(CRITERIA, title="rating · criteria",
                                      json=json.dumps(data, ensure_ascii=False, indent=2),
                                      path=str(p), err=request.args.get("err"), **ctx())

    @app.post("/criteria")
    def criteria_save():
        raw = request.form.get("criteria_json", "")
        try:
            data = json.loads(raw)
            crit = data.get("criteria", data) if isinstance(data, dict) else data
            if not isinstance(crit, list) or not crit:
                raise ValueError("criteria must be a non-empty list")
            normalize_criteria(crit)
        except (ValueError, TypeError) as e:
            return redirect(url_for("criteria_page", err=str(e)))
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "criteria.json").write_text(raw if raw.endswith("\n") else raw + "\n", encoding="utf-8")
        return redirect(url_for("index"))

    @app.get("/")
    def index():
        return render_template_string(INDEX, title="rating · tracks",
                                      saved=request.args.get("saved") == "1", **ctx())

    @app.get("/track/<path:name>")
    def track(name):
        a = audio_path()
        ts = discover(a) if a and Path(a).is_dir() else []
        match = next((t for t in ts if t["name"] == name), None)
        if not match:
            abort(404)
        i = ts.index(match)
        st = state()
        return render_template_string(
            TRACK, title=f"{match['label']} · rating", t=match, rec=st["tracks"].get(name, {}),
            pos=i + 1,
            prev_name=ts[i - 1]["name"] if i > 0 else None,
            next_name=ts[i + 1]["name"] if i + 1 < len(ts) else None, **ctx())

    @app.post("/track/<path:name>")
    def save(name):
        a = audio_path()
        ts = discover(a) if a and Path(a).is_dir() else []
        if not any(t["name"] == name for t in ts):
            abort(404)
        st = state()
        rec = st["tracks"].get(name, {})
        for c in criteria():
            v = request.form.get(c["key"], "").strip()
            if v == "":
                rec.pop(c["key"], None)
            elif c["type"] == "number":
                rec[c["key"]] = _num(v) if _num(v) is not None and "." in v else (int(v) if v.isdigit() else v)
            else:
                rec[c["key"]] = v
        rec["updated"] = _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")
        st["tracks"][name] = rec
        save_state(state_path, st)
        target = request.form.get("next") if request.form.get("advance") == "1" else None
        if target:
            return redirect(url_for("track", name=target))
        return redirect(url_for("track", name=name, saved=1))

    @app.get("/audio/<path:name>")
    def audio(name):
        a = audio_path()
        if not a:
            abort(404)
        p = Path(name)
        if p.suffix.lower() not in AUDIO_EXTS or p.is_absolute() or ".." in p.parts:
            abort(404)
        return send_from_directory(a, name)

    @app.get("/report")
    def report():
        a = audio_path()
        ts = discover(a) if a and Path(a).is_dir() else []
        md = render_markdown(ts, state(), criteria(), a or Path("."), cfg["label"])
        return render_template_string(REPORT, title="rating · report", md=md, **ctx())

    @app.get("/report.md")
    def report_md():
        a = audio_path()
        ts = discover(a) if a and Path(a).is_dir() else []
        md = render_markdown(ts, state(), criteria(), a or Path("."), cfg["label"])
        stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M")
        return Response(md, mimetype="text/markdown", headers={
            "Content-Disposition": f"attachment; filename=rating_{stamp}.md"})

    return app


def _read_session(out_dir: Path) -> dict:
    p = out_dir / "session.json"
    if p.is_file():
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            return d if isinstance(d, dict) else {}
        except (OSError, ValueError):
            pass
    return {}


def main() -> int:
    ap = argparse.ArgumentParser(description="general listening rating app")
    ap.add_argument("--audio", default=None, help="folder of rendered tracks (asked for if omitted)")
    ap.add_argument("--out", default="./rating_out", help="dir for evaluations.json, criteria.json, session.json")
    ap.add_argument("--label", default=None, help="run label (defaults to the folder name)")
    ap.add_argument("--fields", default=None, help="optional criteria JSON path (see README)")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=5000)
    ap.add_argument("--debug", action="store_true")
    args = ap.parse_args()

    out_dir = Path(args.out).expanduser()
    sess = _read_session(out_dir)
    audio = args.audio or sess.get("audio")
    label = args.label or sess.get("label")
    if not audio:
        if sys.stdin and sys.stdin.isatty():
            try:
                audio = input("Track directory (e.g. C:\\Users\\DELL\\Downloads\\jarir_lever_probe): ").strip()
            except EOFError:
                audio = ""
        audio = (audio or "").strip().strip('"').strip("'")
    if not label:
        label = Path(audio).name if audio else "listening"
    if audio and not Path(audio).expanduser().is_dir():
        print(f"rating_app: warning — folder not found yet: {audio} (you can fix it on /setup)")

    cfg = {"audio": audio, "out": str(out_dir), "label": label, "fields": args.fields}
    app = create_app(cfg)
    try:
        found = len(discover(Path(audio).expanduser())) if audio else 0
    except OSError:
        found = 0
    print(f"rating_app: {found} track(s) in {audio or '(unset — open /setup)'}")
    print(f"  open http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=args.debug)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
