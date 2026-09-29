# current

_Updated 2026-09-29 (localhost). Step 1 of the style-ablation plan is DONE; the
render below is the next action and is **Colab/GPU only** — this box has no `/content`._

## 0. Resume THIS conversation on the VM (session-restore trick)
This session (`ses_f1557587dffeXPFxvuqBOVpqil`) was exported locally and uploaded:
```
gs://akbar-december-2024-backup/opencode_sessions/by_id/ses_f1557587dffeXPFxvuqBOVpqil.json
```
653,059 B; md5 hex `4b225f41bb55cdbc9ccb162bc34b702a` (remote md5 b64 `SyJfQbtVzbycyxYrw0twKg==`), uploaded 2026-09-29.

Restore on the VM (terminal: foreground, quick) — import target is cwd, there is no `--directory` flag:
```bash
gsutil cp gs://akbar-december-2024-backup/opencode_sessions/by_id/ses_f1557587dffeXPFxvuqBOVpqil.json /content/
cd /content/maqamrock-yue2-lora-finetuning
opencode import /content/ses_f1557587dffeXPFxvuqBOVpqil.json
opencode -s ses_f1557587dffeXPFxvuqBOVpqil          # or pick it in the session list
```
Carries the **conversation** (turns + tool calls), not the environment; history paths are
this local box's (`/home/akbar/…`). Note: the transcript contains a **leaked `GH_TOKEN`** —
rotate that PAT and it's moot. Tool-native alternative (if wanted): from this box
`vm-continuity capture opencode && vm-continuity ship`, then on the VM
`vm-continuity pull`, `vm-continuity restore opencode -- --mode export|db`.

## Done this session — style-ablation manifest built

- New tool `INFERENCE/build_style_ablation.py` (self-validates via
  `generate.resolve_songs`); ruff clean; `generate.py --dry-run` passes.
- Artifact `manifests/style_ablation_ajam.json`: 5 levels L0–L4, lyrics **verbatim
  and byte-identical across levels** (sha256 == source), one fixed seed
  `298970020`, cap `7500` (q0.95, 605 ar letters), lora alias `qfinal_a0.3`.
- Ladder report (full strings): `manifests/style_ablation_ajam.report.json`.
- Source: `manifests/batch_36_songs.json` → `07-الحر-الشديد-وقطع-القفر-والوعول`,
  Maqam Ajam. Lyrics identical to the source entry.

Ladder (style is the only variable):
| | style | isolates |
|---|---|---|
| l0_raw | raw Suno block, verbatim | control (what we send today) |
| l1_full | trained flat shape, every clause | format |
| l2_target_off | L1 − vocals/instrumentation | redundancy rule |
| l3_anti_off | L1 − genre/production | truth rule |
| l4_min | `arabmaqamrock Maqam Ajam. Mood: Epic, Enduring, Triumphant.` | minimal |

Reproduce/rebuild: `python INFERENCE/build_style_ablation.py`
(`--dry-run` to print only).

### Full style strings (the only thing that varies; lyrics identical)

**l0_raw** — control, what we send today (verbatim Suno block incl. header + meta tags):
```
[Is_MAX_MODE: MAX](MAX) [QUALITY: MAX](MAX) [REALISM: MAX](MAX)
[START_ON: TRUE]
[START_ON: "وَيَوْمٍ مِنَ الشِّعْرَى"]

genre: "arabmaqamrock Symphonic cinematic orchestral ballad, hymn-like grand concert hall acoustics, heavy rock instrumentation, stately groove, 110 BPM."
vocals: "deep male vocals, mixed-voice chest-head resonance blend on sustained notes, breath-supported melismatic runs, controlled vibrato, full-voiced commanding presence, precise Arabic diction, melismatic phrasing in Maqam Ajam with unhurried phrase-ending sustains."
production: "Audiophile recording, punchy centered mix, forward vocals pulling instrumentation down on sustained phrases then band re-enters between lines, bright presence, clean transients, large dynamic range, natural breath room between phrases."
instrumentation: "Distorted electric guitars, orchestral strings, weighted acoustic rock drums, tight rhythm section."
mood: "Epic, Enduring, Triumphant"
```

**l1_full** — trained flat shape, every clause (build_caption):
```
arabmaqamrock Symphonic cinematic orchestral ballad, hymn-like grand concert hall acoustics, heavy rock instrumentation, stately groove, 110 BPM. Maqam Ajam. deep male vocals, mixed-voice chest-head resonance blend on sustained notes, breath-supported melismatic runs, controlled vibrato, full-voiced commanding presence, precise Arabic diction, melismatic phrasing in Maqam Ajam with unhurried phrase-ending sustains. Audiophile recording, punchy centered mix, forward vocals pulling instrumentation down on sustained phrases then band re-enters between lines, bright presence, clean transients, large dynamic range, natural breath room between phrases. Distorted electric guitars, orchestral strings, weighted acoustic rock drums, tight rhythm section. Mood: Epic, Enduring, Triumphant.
```

**l2_target_off** — L1 − vocals/instrumentation (redundancy rule):
```
arabmaqamrock Symphonic cinematic orchestral ballad, hymn-like grand concert hall acoustics, heavy rock instrumentation, stately groove, 110 BPM. Maqam Ajam. Audiophile recording, punchy centered mix, forward vocals pulling instrumentation down on sustained phrases then band re-enters between lines, bright presence, clean transients, large dynamic range, natural breath room between phrases. Mood: Epic, Enduring, Triumphant.
```

**l3_anti_off** — L1 − genre/production (truth rule):
```
arabmaqamrock Maqam Ajam. deep male vocals, mixed-voice chest-head resonance blend on sustained notes, breath-supported melismatic runs, controlled vibrato, full-voiced commanding presence, precise Arabic diction, melismatic phrasing in Maqam Ajam with unhurried phrase-ending sustains. Distorted electric guitars, orchestral strings, weighted acoustic rock drums, tight rhythm section. Mood: Epic, Enduring, Triumphant.
```

**l4_min** — minimal:
```
arabmaqamrock Maqam Ajam. Mood: Epic, Enduring, Triumphant.
```

## Next action — render on Colab (GPU, ~32 min on T4)

**0. Check state first (no GPU overlap):** `python status.py`
**1. Stage the α0.3 adapter** (verify the path exists before relying on it):

```
gsutil ls "$GCP_BACKUP_BASE/loras/audio_cpp/pron/qfinal_a0.3/"
gsutil -m cp -r "$GCP_BACKUP_BASE/loras/audio_cpp/pron/qfinal_a0.3" /content/converter/out/
```

**2. Render L0–L4** — terminal: detached; log: `/content/logs/style_ablation_ajam.log`;
stop: `pkill -f 'generate.py manifests/style_ablation_ajam.json'`;
resume: re-run the same command (fixed `--out-dir` resumes; succeeded tracks are skipped).

```
cd /content/maqamrock-yue2-lora-finetuning
mkdir -p /content/logs
setsid nohup python INFERENCE/generate.py manifests/style_ablation_ajam.json \
  --out-dir /content/audiocpp_inference/out/style_ablation_ajam \
  > /content/logs/style_ablation_ajam.log 2>&1 & disown
```

Progress: `tail -f /content/logs/style_ablation_ajam.log` (or `cat /content/audiocpp_inference/out/latest`).
`generate.py` refuses to start if training is detected unless `--allow-concurrent` —
do not pass it.

**3. Blind A/B** the 5 renders with `INFERENCE/prepare_ab_eval.py` (see
`docs/AB_BLIND_EVAL.md`); KEYS records L0–L4 → labels.

**4. The one question it answers:** does the trigger alone hold the MUST features?
If the arrangement stays sparse at L3/L4, full-band lives in the adapter → Branch B
(ABC), not more words.

## Still open (not done, flagged)

- Doc index/reconciliation for the new `INFERENCE/build_style_ablation.py` is
  **pending** (`docs/README.md` + `RECONCILIATION_LOG.md`) — not touched this session.
- Branch B (only if a MUST feature proves adapter-weak): Python SheetSage2 front end
  DONE; 1-track cover render via existing `bin/audiocpp_cli`, `cot=melody` + `abc_file`,
  seed of the v2 track; call the binary directly (`run_one.sh:79` hardcodes `cot=off`).
  Do NOT rebuild audio.cpp.
