# current

## State @ 2026-10-04 (CPU VM) — Phase 0 started; run design locked

Branch `experimental-quran-pron`, HEAD `e157d50`. No training, no GPU work, no
config edited. Review: **`docs/QURAN_PRON_REVIEW.md`**. This file = the decision
log for the next run.

### NEXT SESSION (planned)
**Finalize the training dataset** end-to-end: adapt `prepare_pron_dataset.py`
(AHH filtered source, 50/50 simple/uthmani **stratified per reciter**, hold out
**2:255 → val**), validate counts + write the manifest, and freeze the train
split (+ the matching YAML) **before any GPU run**. No GPU work until then.

### Decisions locked (user, 2026-10-04)

1. **Data:** rebuild from the **AHH filtered** set (9,492 clips, 3 reciters,
   61.09 h). **Single caption per clip, 50/50 simple/uthmani**, assignment
   **stratified per reciter** (so script never correlates with voice).
2. **Objective:** correct recitation (tajwīd/ḥarakāt/makhārij/waqf), free-run,
   error-free at α=1. "Hear ح/ع" ceiling is retired.
3. **Training:** start **1 epoch**; keep **all** checkpoints (no early deletion);
   extend to epoch 2/3 by bumping `steps` (absolute target) if the eval earns it.
4. **Rank:** **keep 8/8**; 16/32 deferred (only if the ceiling probe says capacity
   is the limiter). Do NOT also move `ar_kl`/`lr`.
5. **Eval:** **free-run per checkpoint** on a **held-out** aya. Chosen:
   **2:255 (Āyat al-Kursī)** — 58 words, covers all 7 hard letters (ح خ ع ق ط ض ظ)
   in both scripts, rich in madd/waqf. Rubric: error count/word, error type,
   waqf, madd, completed-vs-looped.
6. **Caption:** keep the 4-line template `style \n [Lyrics] \n [Verse] \n {aya} ۝`.

### Phase 0 progress

- **Text source — RESOLVED (user, 2026-10-04):** official **Tanzil XML**
  (`/content/quran-uthmani.xml`, `/content/quran-simple.xml`) → JSON
  `/content/quran_text/quran-{uthmani,simple}.json` as `[{sura,aya,text}]`,
  `text = NFC(raw)`, **no embedded `۝`**. **Verified byte-identical to the s10
  training captions** (1:7 + 2:255, both scripts). The alquran.cloud JSONs were the
  *wrong* rendering (no tatweel: `إِلَٰهَ` vs Tanzil `إِلَـٰهَ`); backed up to
  `quran_text/_alquran_cloud_backup/`. **Committed to the repo** at `quran_text/`
  (durable across VMs; the raw XML stays only on this VM).
- **Held-out eval manifest written:**
  `INFERENCE/yue2_eval_heldout/quran_heldout.json` (2:255 both scripts + rubric +
  fixed gen params). MUST stay out of every train split.
- **`۝` handling:** the builder appends ` ۝` (`AYAH_LINE_SUFFIX` → `make_caption`),
  exactly as s10 captions end (`… ٱلْعَظِيمُ ۝`). So `۝` stays OUT of the JSON.
  Held-out manifest `quran_heldout.json` regenerated from Tanzil (2:255 both scripts).

### Next (Phase 0 → needs go-ahead)

1. ~~Ingest the Tanzil XML~~ **DONE** — XML→JSON (NFC) verified vs s10; heldout updated.
2. **Adapt the builder** `prepare_pron_dataset.py`: AHH source, single-script
   50/50 (stratified), hold out 2:255 to val, new val/smoke aya list.
3. **YAML:** new name/paths + `steps` (= train clip count) + keep rank/lr/ar_kl.
   (Eval remains an **offline checkpoint sweep**, not in-training sampling.)
4. **Sweep script** (adapt `INFERENCE/pron_ckpt_sweep.py`) for per-checkpoint
   generation of 2:255.

### Open / not done

- YAML not edited (configs are the user's).
- `docs-reconciler` pass still outstanding.
- Checkpoint sweeps vs style: evaluate **pron-only at α=1** (as the probe did).
