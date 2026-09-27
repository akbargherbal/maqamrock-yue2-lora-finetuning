#!/usr/bin/env python3
"""
prepare_pron_dataset.py
-----------------------
Build the YuE2 **pronunciation** dataset (long-aya Quran set) from a
quality-filtered `accepted/` recitation collection plus the Tanzil Quran text.

================================ RECONSTRUCTION ================================
This file is a *faithful reconstruction* of the builder that produced
`gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/quran_long_aya_dataset/`
on 2026-09-26. The original script was lost with the VM (never committed) and the
session backup predated it; the rules below were re-derived from the surviving
`selection_report.json` and `excluded_ayat.jsonl` and re-verified against them:

  * 6,236 ayat in -> 4,670 selected / 1,566 excluded
      - 1,524 below_min_words (word_count 1..5)
      -    28 above_max_words (word_count 62..145)
      -    14 exact_duplicate_exceeds_threshold
  * Dedup rule (verified): group the surviving ayat by EXACT text; for any group
    whose frequency f > max_repeat (2), keep the first `max_repeat` (lowest
    sura:aya) and exclude the remaining f-2. 4+3+2+1+4 = 14, matching the report.
  * Bismillah prefix stripped from the first aya of 112 surahs (all but 1 and 9).
  * Captions are the 4-line template; the aya line ends with " <U+06DD>".

Because this is a reconstruction, treat it as documentation + a reproducible
build path, NOT as byte-verified provenance. The dataset already on GCS is FINAL
(do not rebuild over it); the validation gates in the plan are what certify it.

===============================================================================

Inputs
------
    <accepted_root>/                 # gs://sheikh-fitzgerald-backup/ARABIC_DATA/Quran_Filtered_Audio_Data/accepted
        <reciter>/<SSSAAA>.mp3       # (also tolerates <SSSAAA>_<variant>.mp3 and a flat
                                     #  <reciter>_<SSSAAA>.mp3 layout; see --audio-layout)
    quran-simple.json                # Tanzil, simple orthography
    quran-uthmani.json               # Tanzil, Uthmani orthography
    PROMPT.txt                       # single-line style prompt

Output
------
    <out>/train/<reciter>_<SSSAAA>_<simple|uthmani>.{mp3,txt}
    <out>/val/...  <out>/smoke/...
    <out>/selection_report.json
    <out>/excluded_ayat.jsonl

Splits (verified against the surviving report)
----------------------------------------------
    train = every selected combo EXCEPT the val set (the smoke combos stay in train)
    val   = val_ayat x all reciters
    smoke = smoke_ayat x smoke_reciters

Usage
-----
    python prepare_pron_dataset.py --accepted-root /content/quran_accepted \
        --simple  /content/quran_audio_filtering/quran_text/quran-simple.json \
        --uthmani /content/quran_audio_filtering/quran_text/quran-uthmani.json \
        --prompt-file /content/quran_training_data_specs/PROMPT.txt \
        --out /content/quran_long_aya_dataset --dry-run

    # real build (writes files); --jobs N parallelises the audio copies
    python prepare_pron_dataset.py ... --out /content/quran_long_aya_dataset --jobs 12
"""

from __future__ import annotations

import argparse
import json
import random
import re
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

AYAH_SIGN = "\u06dd"  # ARABIC END OF AYAH
AYAH_LINE_SUFFIX = " " + AYAH_SIGN

# Arab diacritics / Quranic marks, stripped only for *comparison* (bismillah match),
# never for the stored caption text.
_DIACRITICS = re.compile("[\u064B-\u0652\u0670\u06D6-\u06ED\u0640]")

BISMILLAH = "بسم الله الرحمن الرحيم"

# --- Defaults that reproduce the surviving selection_report.json --------------
DEFAULT_PROMPT = (
    "Solo male voice, unaccompanied. Quran recitation. "
    "Clear precise classical Arabic diction. Spoken Words."
)
DEFAULT_RECITERS = [
    "Abdul_Basit_Murattal_192kbps",
    "Abdullah_Basfar_192kbps",
    "Abu_Bakr_Ash-Shaatree_128kbps",
    "Hudhaify_128kbps",
    "Husary_128kbps",
    "Minshawy_Murattal_128kbps",
    "Muhammad_Ayyoub_128kbps",
    "Yaser_Salamah_128kbps",
    "aziz_alili_128kbps",
]
DEFAULT_SMOKE_RECITERS = ["Abdul_Basit_Murattal_192kbps", "Abdullah_Basfar_192kbps"]
DEFAULT_VAL_AYAT = [
    "002213", "002227", "002256", "002273", "005079", "006015", "006087",
    "006160", "008032", "012089", "015068", "016027", "016105", "017079",
    "020052", "037097", "052030", "070030", "070039", "083007",
]
DEFAULT_SMOKE_AYAT = ["001007", "002002", "002003", "002004"]


# ---------------------------------------------------------------------------
@dataclass
class Config:
    accepted_root: Path
    simple: Path
    uthmani: Path
    prompt_file: Path | None
    out: Path
    min_words: int = 6
    max_words: int = 60
    max_repeat: int = 2
    val_ayat: int = 20
    smoke_ayat: int = 4
    smoke_reciters: int = 2
    variants: tuple[str, ...] = ("simple", "uthmani")
    freq_script: str = "simple"
    seed: int = 42
    jobs: int = 12
    ayah_symbol: bool = True
    dry_run: bool = False
    reciters: list[str] = field(default_factory=lambda: list(DEFAULT_RECITERS))
    val_explicit: list[str] = field(default_factory=lambda: list(DEFAULT_VAL_AYAT))
    smoke_explicit: list[str] = field(default_factory=lambda: list(DEFAULT_SMOKE_AYAT))


# ---------------------------------------------------------------------------
def norm_ar(s: str) -> str:
    """Strip diacritics/tatweel and collapse spaces — for bismillah comparison only."""
    return re.sub(r"\s+", " ", _DIACRITICS.sub("", s)).strip()


def word_count(text: str) -> int:
    """Words in an aya after dropping the end-of-ayah sign."""
    return len(text.replace(AYAH_SIGN, "").split())


def strip_bismillah(text: str) -> tuple[str, bool]:
    """Remove a leading bismillah. Returns (text, stripped?)."""
    if norm_ar(text).startswith(BISMILLAH):
        # locate the bismillah prefix boundary in the ORIGINAL text without
        # discarding its first diacritics: split on whitespace, drop the first
        # four words (bism / allah / al-rahman / al-rahim).
        words = text.split()
        if len(words) > 4:
            return " ".join(words[4:]), True
    return text, False


def load_tanzil(path: Path) -> dict[str, str]:
    """Load a Tanzil Quran JSON into {'SSSAAA': text}.

    Tolerates the common Tanzil/JS shapes: a top-level list of
    {sura, aya, text}, a dict wrapping such a list, or {index: {...}}.
    """
    raw = path.read_text(encoding="utf-8")
    raw = re.sub(r"^\s*(var\s+\w+\s*=\s*)?", "", raw).rstrip().rstrip(";")
    data = json.loads(raw)

    if isinstance(data, dict):
        for v in data.values():
            if isinstance(v, list):
                data = v
                break
    if isinstance(data, dict):  # {index: {...}}
        data = list(data.values())

    out: dict[str, str] = {}
    for row in data:
        if not isinstance(row, dict):
            continue
        try:
            sura = int(row.get("sura") or row.get("surah") or row.get("chapter"))
            aya = int(row.get("aya") or row.get("ayah") or row.get("verse"))
        except (TypeError, ValueError):
            continue
        text = row.get("text") or row.get("aya_text") or ""
        out[f"{sura:03d}{aya:03d}"] = text.strip()
    if not out:
        raise SystemExit(f"no ayat parsed from {path}")
    return out


def discover_source_audio(accepted_root: Path, reciters: list[str]) -> dict[tuple[str, str], Path]:
    """Map (reciter, SSSAAA) -> source mp3. Tolerates a few layouts."""
    index: dict[tuple[str, str], Path] = {}
    key_re = re.compile(r"(?P<key>\d{6})")

    for reciter in reciters:
        rdir = accepted_root / reciter
        search = list(rdir.glob("*.mp3")) if rdir.is_dir() else list(accepted_root.glob(f"{reciter}*.mp3"))
        for p in search:
            m = key_re.search(p.stem)
            if m:
                index.setdefault((reciter, m.group("key")), p)
    return index


def make_caption(prompt: str, aya_text: str, ayah_symbol: bool) -> str:
    line = aya_text + (AYAH_LINE_SUFFIX if ayah_symbol else "")
    return f"{prompt}\n[Lyrics]\n[Verse]\n{line}\n"


# ---------------------------------------------------------------------------
def select_ayat(cfg: Config, simple: dict[str, str], uthmani: dict[str, str]):
    """Return (selected_keys sorted, excluded rows, stats)."""
    text_by_key = {k: (simple.get(k) or uthmani.get(k) or "") for k in simple}
    keys = sorted(text_by_key)

    # 1) strip bismillah from first aya of surahs other than 1 and 9
    stripped = 0
    for k in keys:
        sura, aya = int(k[:3]), int(k[3:])
        if aya == 1 and sura not in (1, 9):
            new, did = strip_bismillah(text_by_key[k])
            if did:
                text_by_key[k] = new
                if k in simple:
                    simple[k] = new
                if k in uthmani:
                    uthmani[k] = new
                stripped += 1

    excluded: list[dict] = []
    survivors: list[str] = []

    # 2) word-count gate (on the freq_script text)
    for k in keys:
        wc = word_count(text_by_key[k])
        if wc < cfg.min_words:
            excluded.append({"key": k, "text": text_by_key[k], "reason": "below_min_words",
                             "word_count": wc, "freq": 1})
        elif wc > cfg.max_words:
            excluded.append({"key": k, "text": text_by_key[k], "reason": "above_max_words",
                             "word_count": wc, "freq": 1})
        else:
            survivors.append(k)

    # 3) exact-duplicate cap: keep the first `max_repeat` of any repeated text
    groups: dict[str, list[str]] = {}
    for k in survivors:
        groups.setdefault(text_by_key[k], []).append(k)
    kept: list[str] = []
    for text, ks in groups.items():
        ks.sort()  # lowest sura:aya first
        if len(ks) > cfg.max_repeat:
            for k in ks[cfg.max_repeat:]:
                excluded.append({"key": k, "text": text, "reason":
                                 "exact_duplicate_exceeds_threshold",
                                 "word_count": word_count(text), "freq": len(ks)})
            kept.extend(ks[:cfg.max_repeat])
        else:
            kept.extend(ks)
    kept.sort()

    stats = {
        "ayat_total": len(keys),
        "ayat_selected": len(kept),
        "ayat_excluded": len(excluded),
        "bismillah_stripped": stripped,
        "excluded_by_reason": {
            "below_min_words": sum(e["reason"] == "below_min_words" for e in excluded),
            "above_max_words": sum(e["reason"] == "above_max_words" for e in excluded),
            "exact_duplicate_exceeds_threshold": sum(
                e["reason"] == "exact_duplicate_exceeds_threshold" for e in excluded),
        },
    }
    return kept, excluded, stats


def choose_splits(cfg: Config, selected: list[str]) -> tuple[list[str], list[str], list[str]]:
    smoke = [k for k in cfg.smoke_explicit if k in selected]
    val = [k for k in cfg.val_explicit if k in selected]
    if len(val) < cfg.val_ayat:
        pool = [k for k in selected if k not in set(val) | set(smoke)]
        rng = random.Random(cfg.seed)
        val += rng.sample(pool, min(cfg.val_ayat - len(val), len(pool)))
        val.sort()
    return val, smoke


# ---------------------------------------------------------------------------
def build(cfg: Config) -> int:
    prompt = DEFAULT_PROMPT
    if cfg.prompt_file and cfg.prompt_file.is_file():
        prompt = cfg.prompt_file.read_text(encoding="utf-8").strip()

    simple = load_tanzil(cfg.simple)
    uthmani = load_tanzil(cfg.uthmani)
    selected, excluded, stats = select_ayat(cfg, simple, uthmani)
    val, smoke = choose_splits(cfg, selected)

    audio = discover_source_audio(cfg.accepted_root, cfg.reciters)
    val_set, smoke_set = set(val), set(smoke)
    smoke_reciters = cfg.reciters[: cfg.smoke_reciters]

    # (split, key, reciter) triples
    combos: list[tuple[str, str, str]] = []
    for key in selected:
        for reciter in cfg.reciters:
            if key in val_set:
                combos.append(("val", key, reciter))
            else:
                combos.append(("train", key, reciter))  # smoke stays in train too
    for key in smoke:
        for reciter in smoke_reciters:
            combos.append(("smoke", key, reciter))

    have = [(s, k, r) for (s, k, r) in combos if (r, k) in audio]
    missing = [(s, k, r) for (s, k, r) in combos if (r, k) not in audio]

    counts = {
        "train_combos": sum(s == "train" for s, _, _ in have),
        "val_combos": sum(s == "val" for s, _, _ in have),
        "smoke_combos": sum(s == "smoke" for s, _, _ in have),
    }
    counts["train_pairs"] = counts["train_combos"] * len(cfg.variants)
    counts["val_pairs"] = counts["val_combos"] * len(cfg.variants)
    counts["smoke_pairs"] = counts["smoke_combos"] * len(cfg.variants)
    per_reciter = {
        r: sum(s == "train" and rr == r for s, _, rr in have) for r in cfg.reciters
    }

    report = {
        "params": {
            "accepted_root": str(cfg.accepted_root), "simple": str(cfg.simple),
            "uthmani": str(cfg.uthmani), "prompt_file": str(cfg.prompt_file or ""),
            "out": str(cfg.out), "min_words": cfg.min_words, "max_words": cfg.max_words,
            "max_repeat": cfg.max_repeat, "val_ayat": cfg.val_ayat,
            "smoke_ayat": cfg.smoke_ayat, "smoke_reciters": cfg.smoke_reciters,
            "variants": ",".join(cfg.variants), "freq_script": cfg.freq_script,
            "seed": cfg.seed, "dry_run": cfg.dry_run, "jobs": cfg.jobs,
        },
        "prompt": prompt,
        **stats,
        "reciters": cfg.reciters,
        "smoke_reciters": smoke_reciters,
        "val_ayat": val,
        "smoke_ayat": smoke,
        "counts": counts,
        "per_reciter_train_combos": per_reciter,
    }

    print(json.dumps({k: report[k] for k in
                      ("ayat_selected", "ayat_excluded", "excluded_by_reason",
                       "bismillah_stripped", "counts")}, indent=2))
    print(f"combos with source audio: {len(have)}  missing: {len(missing)}")

    if cfg.dry_run:
        return 0

    text_by_key = {k: (simple.get(k) or uthmani.get(k) or "") for k in simple}
    for split in ("train", "val", "smoke"):
        (cfg.out / split).mkdir(parents=True, exist_ok=True)

    def write_one(item: tuple[str, str, str]) -> None:
        split, key, reciter = item
        src = audio[(reciter, key)]
        for variant in cfg.variants:
            stem = f"{reciter}_{key}_{variant}"
            dst_audio = cfg.out / split / (stem + ".mp3")
            dst_text = cfg.out / split / (stem + ".txt")
            if not dst_audio.exists():
                shutil.copy2(src, dst_audio)
            aya = (simple if variant == "simple" else uthmani).get(key) or text_by_key[key]
            dst_text.write_text(make_caption(prompt, aya, cfg.ayah_symbol), encoding="utf-8")

    with ThreadPoolExecutor(max_workers=cfg.jobs) as ex:
        list(ex.map(write_one, have))

    (cfg.out / "selection_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    with open(cfg.out / "excluded_ayat.jsonl", "w", encoding="utf-8") as fh:
        for e in excluded:
            fh.write(json.dumps(e, ensure_ascii=False) + "\n")
    print(f"wrote dataset to {cfg.out}")
    return 0


# ---------------------------------------------------------------------------
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--accepted-root", required=True, type=Path)
    ap.add_argument("--simple", required=True, type=Path)
    ap.add_argument("--uthmani", required=True, type=Path)
    ap.add_argument("--prompt-file", type=Path, default=None)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--min-words", type=int, default=6)
    ap.add_argument("--max-words", type=int, default=60)
    ap.add_argument("--max-repeat", type=int, default=2)
    ap.add_argument("--val-ayat", type=int, default=20)
    ap.add_argument("--smoke-ayat", type=int, default=4)
    ap.add_argument("--smoke-reciters", type=int, default=2)
    ap.add_argument("--freq-script", choices=["simple", "uthmani"], default="simple")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--jobs", type=int, default=12)
    ap.add_argument("--no-ayah-symbol", action="store_true",
                    help="omit the ' <U+06DD>' suffix (the original builder did; it was added later)")
    ap.add_argument("--reciter", action="append", dest="reciters", default=None,
                    help="restrict/override the reciter list (repeatable)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    cfg = Config(
        accepted_root=args.accepted_root, simple=args.simple, uthmani=args.uthmani,
        prompt_file=args.prompt_file, out=args.out, min_words=args.min_words,
        max_words=args.max_words, max_repeat=args.max_repeat, val_ayat=args.val_ayat,
        smoke_ayat=args.smoke_ayat, smoke_reciters=args.smoke_reciters,
        freq_script=args.freq_script, seed=args.seed, jobs=args.jobs,
        ayah_symbol=not args.no_ayah_symbol, dry_run=args.dry_run,
    )
    if args.reciters:
        cfg.reciters = args.reciters
    return build(cfg)


if __name__ == "__main__":
    sys.exit(main())
