# PRON LoRA LONG — build & multi-day training plan (`quran_long_aya_r8`)

Branch: **`pron-lora-long`** (created off `pron-lora-ar-only`). Status as of
2026-09-27: **dataset built + validated and in GCS; config written; decisions
locked; no GPU work yet.** Canonical entry point: `docs/PRON_LORA_LONG.md` (run
hub, which includes the kickstart/resume/status prompts).

> **Provenance note.** The original plan/config/builder were lost with a VM on
> 2026-09-26 and never pushed. This revision folds in the surviving facts: the
> `selection_report.json` / `excluded_ayat.jsonl` in GCS, the separately-verified
> ` ۝` caption edit, and the locked decisions recovered from the original
> GPU-phase opening prompt.
> `docs/PRON_LORA_LONG_PLAN.md` (this file) is the single source of truth.

## 1. Objective

Train a new YuE2 pronunciation LoRA on the **quality-filtered** Quran collection,
with **longer ayat and far more data** than the reference, and run it **across
multiple days** (e.g. 5 h today, 8 h tomorrow). Continuity is the primary design
constraint: because one ~1-epoch run spans many Colab sessions, *any* interruption
must cost at most one checkpoint interval.

## 2. Locked decisions

- **Filtering (final):** `min_words = 6`, `max_words = 60`, `max_repeat = 2` on
  exact duplicate texts. Word count is taken *after* dropping the end-of-ayah sign
  U+06DD. (An earlier revision used `min_words = 5` with no cap; that was
  superseded during the build — see §3.)
- **Captions:** both `_simple` and `_uthmani` variants. Layout (exact):
  `<prompt>\n[Lyrics]\n[Verse]\n<ayah text> ۝\n`, prompt =
  `/content/quran_training_data_specs/PROMPT.txt`:
  `Solo male voice, unaccompanied. Quran recitation. Clear precise classical Arabic diction. Spoken Words.`
- **Source audio:** `gs://sheikh-fitzgerald-backup/ARABIC_DATA/Quran_Filtered_Audio_Data/accepted`
  (54,626 mp3, 9 reciters; `review`/`reject` excluded).
- **Splits:** train = the rest; val = 20 unique ayat × all 9 reciters; smoke =
  4 ayat × 2 reciters (smoke also stays in train, as in the reference).
- **Run identity:** run name **`quran_long_aya_r8`**, config
  `config/quran_long_aya_r8.yml`, output prefix
  `<base>/quran_long_aya_r8/output/`, log `<base>/... run>`. Never overwrite the
  existing `pron_dataset`.
- **Pair count: A** — keep both text variants (81,006 train pairs).
- **Caching:** `cache_text_embeddings: false`; `cache_latents_to_disk: true`; the
  latent cache **is banked** to GCS (§4.3).
- **Checkpoint cadence:** `save_every: 1500`, `max_step_saves_to_keep: 24`;
  5-min GCS mirror.
- **Branch:** `pron-lora-long` off `pron-lora-ar-only`.

## 3. Dataset (BUILT, VALIDATED, FINAL)

### 3.1 Selection (from `selection_report.json`)
- **6,236 ayat in → 4,670 selected / 1,566 excluded**, all 114 surahs covered:
  - `below_min_words` 1,524 (word counts 1–5),
  - `above_max_words` 28 (word counts 62–145),
  - `exact_duplicate_exceeds_threshold` 14.
- **Dedup rule (verified against `excluded_ayat.jsonl`):** group surviving ayat by
  exact text; for any group with frequency `f > max_repeat (2)`, keep the first two
  (lowest `SSSAAA`) and exclude the rest. `4+3+2+1+4 = 14`, matching the report.
- Bismillah prefix stripped from the first aya of **112** surahs (all but 1 and 9).
- Reference set for comparison: 350 ayat, 4–13 words, ~4–11 s.

### 3.2 Output shape (reference-compatible)
```
<dataset>/train/<reciter>_<SSSAAA>_<simple|uthmani>.mp3 + .txt
<dataset>/val/...   <dataset>/smoke/...
```
`_simple.mp3` and `_uthmani.mp3` are **byte-identical audio** (verified on the
reference) — the variant only changes the caption. AI-Toolkit pairs
`<stem>.mp3` with `<stem>.txt`, so two scripts ⇒ two files.

### 3.3 Scale (as built)
| split | combos | pairs (×2) | objects |
|---|---|---|---|
| train | 40,503 | **81,006** | 162,012 |
| val | 176 | 352 | 704 |
| smoke | 7 | 14 | 28 |

**28.04 GiB**, ~162.7k objects — ≈13× the reference (6,100 pairs). Combos are
emitted only where an accepted source file exists (val/smoke lose a few combos:
176/180 and 7/8). Captions end with ` ۝` (U+06DD).

### 3.4 Build pipeline (DONE; builder reconstructed for reproducibility)
1. Download `accepted/` once (15.77 GiB) to `/content/quran_accepted`.
2. `prepare_pron_dataset.py` → dataset root + `selection_report.json` +
   `excluded_ayat.jsonl`. *(The original was lost with the VM; the committed
   version is a faithful reconstruction of the rules above — reference, not
   byte-verified provenance.)*
3. Validation gates (all passed before upload):
   - object counts match the report exactly; every `.mp3` has a same-stem `.txt`;
   - captions byte-equal a fresh re-derivation from the JSON texts;
   - every selected combo maps to an accepted source file; gaps listed;
   - decode a random sample (≥50) with `ffprobe` (mp3, 48 kHz-capable, duration > 0);
   - no filename >255 bytes; ASCII-safe reciter names.
4. Upload to GCS (new prefix, never `pron_dataset`):
   `gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/quran_long_aya_dataset/`.

## 4. Caches and their cost

AI-Toolkit writes caches under the dataset folder. Neither is mirrored
automatically, so a fresh VM rebuilds them before the first training step.

### 4.1 Latent cache (kept; banked)
`cache_latents_to_disk` is mandatory for YuE2. VAE latents (64 ch × 25 fps × bf16
= 3.2 KB/s of audio) + codec tokens (int32) ≈ **~5.2 GiB** for the train split.
**One-time build ≈ 5–9 h** on the first launch, **before step 1**. That build is
the dominant cost of the first GPU session, not the steps.

### 4.2 Text-embedding cache (disabled)
`cache_text_embeddings: true` would write AR-prefix embeddings (`[L, 2048]` bf16,
~0.33–0.61 MB/file ≈ **28–53 GiB**), 9× redundant because the caption is identical
across the 9 reciters and the cache path includes the file stem. `YuE2TextEncoder`
is just `ar.embed(ids)` — an embedding-table lookup — so recomputing per step is
~free. **Decision: `cache_text_embeddings: false`.**

### 4.3 Banking the latent cache (decision: YES)
`backup_to_gcp.py` does not mirror `_latent_cache`, so bank it by hand the moment
it is complete (one-time expensive artifact):
```bash
tar -C /content/quran_long_aya_dataset/train -cf - _latent_cache \
  | gcloud storage cp - gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/quran_long_aya_dataset/_latent_cache.tar
```
Later VMs untar it into `/content/quran_long_aya_dataset/train/` instead of
rebuilding.

## 5. Multi-day continuity design

### 5.1 Run identity
- One run name, one config, one GCS prefix for the whole effort: `quran_long_aya_r8`.
- `ai-toolkit` auto-resumes: `get_latest_save_path()` picks the newest
  `<name>*.safetensors`, loads its `training_info.step` and `optimizer.pt`, and
  continues. Same name + same config = resume; anything changed = a new run.
- **Invariant:** never run the same run name on two VMs at once.

### 5.2 Checkpoint cadence
- `save.save_every: 1500` (steps) and `save.max_step_saves_to_keep: 24` — fixed,
  not smoke-derived. 24 retained checkpoints is the buffer for the 5-min GCS
  mirror across the multi-day run. Checkpoints are EMA weights; each save also
  writes `optimizer.pt`.

### 5.3 Backup cadence
`backup_to_gcp.py --run-name quran_long_aya_r8` runs detached every 5 min (it
skips `loss_log.db*` and TensorBoard event files when deciding a folder has
settled). Worst-case loss on VM death = one checkpoint interval. Before each
pause, force `--once` and confirm the newest checkpoint + optimizer are in GCS.

### 5.4 Session lifecycle
- **Start:** `train_ctl.py start --config <cfg> --run-name <run> --log-name <log>`
  (detached; `start` is Ctrl+C-proof).
- **Pause:** `train_ctl.py stop --log-name <log>` (checkpoint-safe SIGINT) →
  `backup_to_gcp.py --run-name <run> --once` → verify GCS has the newest ckpt.
- **Resume (fresh VM):** clone → `bootstrap/setup.sh --training` (it may also
  pull the old v2 dataset — ignore that) → restore the dataset by hand:
  `gcloud storage rsync -r gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/quran_long_aya_dataset /content/quran_long_aya_dataset`
  → untar the banked latent cache → restore the run output prefix into
  `output/quran_long_aya_r8/` → start sidecars → relaunch the **identical**
  command (user-typed). Log must show "Found step N", not step 0.

### 5.5 Hazards (from `DECISIONS.md`, verified against ai-toolkit)
- EMA restarts a fresh average on resume (continues from EMA'd weights). Known,
  accepted for the reference run; flag if we rely on EMA.
- The un-suffixed final adapter (`<run>.safetensors`) is a same-name overwrite;
  safe here because the run name is new, but never re-point an old config at it.
- `train.start_step` only overrides the counter, never which checkpoint loads.
- Dataset folder must be immutable once training starts (changes desync cache).

## 6. Phased execution

**Phases 0–3 — done:**
0. Plan + branch — this doc; branch `pron-lora-long`.
1. Build dataset (download → build → validate). *[gates passed]*
2. Upload dataset to GCS + document restore. *[81,006 / 352 / 14 verified]*
3. Write the run config — `config/quran_long_aya_r8.yml`. *[decisions locked]*

**GPU phase — the exact sequence (kickstart prompt in `docs/PRON_LORA_LONG.md`):**

1. **Preflight.** Confirm the branch is `pron-lora-long` and the config parses;
   report `nvidia-smi` (GPU/VRAM), disk, and `vm-continuity` health.
2. **Bootstrap + restore.** `bootstrap/setup.sh --training` (it may also pull the
   old v2 dataset — ignore that), then restore ours:
   ```bash
   gcloud storage rsync -r gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/quran_long_aya_dataset \
     /content/quran_long_aya_dataset
   ```
   Verify 81,006 train `.mp3` + 81,006 `.txt`, 352/352 val, 14/14 smoke.
3. **Sidecars.** `backup_to_gcp.py --run-name quran_long_aya_r8` and `gpu_logger.py`.
4. **Launch** (user-typed, detached). The first launch builds the latent cache
   (~5–9 h) **before step 1**:
   ```bash
   python train_ctl.py start --config config/quran_long_aya_r8.yml \
     --run-name quran_long_aya_r8 --log-name train_quran_long
   ```
5. **Bank the cache** the moment it completes — watch
   `/content/quran_long_aya_dataset/train/_latent_cache/*.safetensors` in
   `/content/logs/train_quran_long.log` until ~81,006, then:
   ```bash
   tar -C /content/quran_long_aya_dataset/train -cf - _latent_cache \
     | gcloud storage cp - gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/quran_long_aya_dataset/_latent_cache.tar
   ```
6. **Measure** s/step, VRAM peak, and wall clock per 1500-step save over ~50 steps
   (`monitor_loss.py` + `/content/logs/gpu_usage.csv`). **Do not edit the config.**
7. **Train across sessions** per §5. Pause only with
   `python train_ctl.py stop --log-name train_quran_long`; **no auto-resume**.
   Later fresh VM = restore dataset, untar the banked cache, restore the run
   output prefix, relaunch the identical command.
8. **Merge / inference** later via the existing pron merge tooling.

## 7. Cost & scope

Full 1 epoch = **81,006 steps**. At the reference's short-clip ~0.9 s/step that is
~20 h, but our clips are ~2× longer, so expect materially more; the exact rate is
measured in Phase 5. Scope decision: **A (as-is, both variants)**. The cost levers
(B uthmani-only; C cap ayah length; D fixed step budget) remain available but are
not chosen. "Train as much as possible" + multi-day = A/D.

## 8. Risks

- **First-launch latent-cache build (~5–9 h)** is the main time cost; bank it (§4.3).
- Per-VM cache rebuild on later sessions — mitigated by the banked tar.
- Colab 12 h session limits / reclaims — mitigated by detached run + 1500-step
  saves + 24 retained checkpoints.
- Disk is **not** binding: ~28 GB audio + ~5.2 GiB latent cache + model caches fit
  the ~220 GB target VM. *Time* is the constraint, not space.

## 9. Decisions (resolved — formerly "open")

1. **Pair count:** **A** — both variants, 81,006 pairs.
2. **Persist the latent cache:** **yes** — bank as `_latent_cache.tar` (§4.3).
3. **Run name + prefixes:** `quran_long_aya_r8`; local dataset
   `/content/quran_long_aya_dataset`; dataset prefix `.../quran_long_aya_dataset/`;
   run output prefix `.../quran_long_aya_r8/output/`.
4. **Commit on `pron-lora-long`:** yes.
