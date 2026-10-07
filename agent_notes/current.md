# current.md — handoff surface (overwritten each turn; not a source of truth)

## NOW → the D-test: rating questions are written; GPU render is the next step
_Written 2026-10-07. Branch `pron-lora-long-aya` (uncommitted rename+retire work in tree)._

### What we did this turn
- Cleanup is DONE and verified: `quran_ahh_r8`→`quran_ahh_r32` renamed in GCS (93 objs) + repo
  (22 files); legacy 9-reciter donor (`quran_long_aya_r8_s10` + `qfinal_*`) retired to
  `<base>/archive/quran_long_aya_legacy/` (63 objs) and de-referenced from all live docs.
- **Wrote the D-test scorecard** for the NEW app (github.com/akbargherbal/ai_music_rating_app):
  `INFERENCE/scorecards/dtest_diction.json` — validates against the app's rules (12 criteria,
  `summary_metric=diction`).

### The question the D-test must answer
Does the Quran donor (`qahh_a0p1` = `quran_ahh_r32` α0.1 merge into v2) improve Arabic **diction**
vs v2-only — and is the **AR** branch bleeding recitation (tajweed) prosody while **NAR** adds
articulation? (The 17-track probe could not answer it: mood-dominated rubric, n=1.)

### How to run the rating app (Windows, new app repo = the source of truth for scorecards)
```
# once
py -m pip install -r requirements.txt
# drop the scorecard into the app
copy  INFERENCE\scorecards\dtest_diction.json   <app>\scorecards\dtest_diction.json
# run (blind + this scorecard; audio folder's subfolders = arms)
py app.py --audio "C:\path\to\jarir_dtest" --config configs/blind_eval.json --scorecard dtest_diction
```
- `--scorecard dtest_diction` resolves `scorecards/dtest_diction.json` (filename stem = id).
- `--blind` shuffles with a seed stored in `runs/<id>/run.json`; report reveals arms.
- Precedence: CLI `--scorecard` overrides the `scorecard` key in the config file.

### Audio-folder convention (for the GPU render step)
Sub-folder name = arm (report groups by parent folder). Suggested arms:
`v2`, `qahh` (a0p1 both-full), `qahh_ar_off`, `qahh_ar_half`, `qahh_nar_half`. One `_meta.json`
per arm folder with `{"arm": "...", "seed": ...}` for report columns.

### Scorecard → verdict mapping
- `diction` (summary), `intelligibility`, `errors_count`, `bad_sounds` → does the donor help diction?
- `tajweed_bleed` (+`tajweed_types`), `cadence` → AR-branch overcorrection.
- `articulation` → NAR-branch contribution.
- `mood`, `artifacts`, `keep` → controls (must NOT drive the call).
- Keep donor iff errors/take and tajweed-bleed ≤ v2 and diction ≥ v2 (mood not worse).

### NEXT (GPU, later — user says)
1. Render the D-test: v2 + qahh arms (AR/NAR scales), phoneme-dense stimuli, ≥3–4 seeds × 2 songs.
   - `INFERENCE/quran_arnar_scale_probe.sh` already does the 4 AR/NAR arms on `qahh_a0p1`.
   - Run `nvidia-smi` first; do not overlap an active run.
2. rsync the out dir to GCS, download locally, point the app at it.
3. Export `/report.md` + `/report.csv` and bring them back for analysis.

### Facts
- `$GCP_BACKUP_BASE` = `gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning`
- Donor adapters: `<base>/quran_ahh_r32/maqamrock_merge/convert/qahh_a0p1/{ar,nar}.safetensors`
- Existing (unused for this) split audio: `audiocpp_inference/out/jarir_lever_probe/{v2_1.0_1.0,qa_*}/`
- `jarir_arnar_probe` on GCS is INCOMPLETE (1/4 arms).
