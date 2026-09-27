# PRON LoRA LONG — build & multi-day training plan

Branch: **`pron-lora-long`** (created 2026-09-26 off `pron-lora-ar-only`; nothing
pushed). Status: **PLANNING ONLY** — no dataset built, no run started, no config
edited. Companion runbook will be `docs/PRON_LORA_LONG.md` once the run exists.

## 1. Objective

Train a new YuE2 pronunciation LoRA on the **quality-filtered** Quran collection,
this time with **longer ayat and far more data**, and run it **across multiple
days** (e.g. 5 h today, 8 h tomorrow). Continuity is the primary design
constraint: because one ~1-epoch run will span many Colab sessions, the plan must
make *any* interruption cost at most one checkpoint interval.

## 2. Locked decisions (from this session)

- Filtering: `quran_ayah_filtering_specs.md` as-is — `min_words = 5` (after
  dropping the end-of-ayah sign U+06DD), `max_repeat = 2` on literal duplicates.
- Captions: both `_simple` and `_uthmani` variants, matching the reference set.
- Caption layout (exact): `<prompt>\n[Lyrics]\n[Verse]\n<ayah text>\n`, prompt =
  `/content/quran_training_data_specs/PROMPT.txt`.
- Source audio: `gs://sheikh-fitzgerald-backup/ARABIC_DATA/Quran_Filtered_Audio_Data/accepted`
  (54,626 mp3, 9 reciters; `review`/`reject` excluded).
- Splits: train = the rest; val = 20 unique ayat × all 9 reciters; smoke = 4 ayat
  × 2 reciters (smoke also stays in train, as in the reference).
- Train as much as possible; storage is cheaper than compute; checkpoint ~every
  30 min and mirror to GCS; never overwrite the existing `pron_dataset`.

## 3. Dataset design

### 3.1 Selection (verified by dry-run; no audio touched)
- **5,160 ayat kept** — 1,048 dropped for <5 words, 28 for over-repetition; all
  114 surahs covered.
- Word counts: min 5, **median 13, mean 15.3, max 145** → genuinely long clips.
- Reference set for comparison: 350 ayat, 4–13 words, ~4–11 s.

### 3.2 Output shape (reference-compatible)
```
<dataset>/train/<reciter>_<SSSAAA>_<simple|uthmani>.mp3 + .txt
<dataset>/val/...
<dataset>/smoke/...
```
Note: `_simple.mp3` and `_uthmani.mp3` are **byte-identical audio** (verified on
the reference) — the variant only changes the caption. That is intrinsic to how
AI-Toolkit pairs `<stem>.mp3` with `<stem>.txt`: two scripts ⇒ two files.

### 3.3 Scale
| split | combos | pairs (×2) | objects |
|---|---|---|---|
| train | 46,260 | **92,520** | 185,040 |
| val | 180 | 360 | 720 |
| smoke | 8 | 16 | 32 |

≈28 GB audio, ~185k objects. This is **~15×** the reference (6,100 pairs).

### 3.4 Build pipeline
1. Download `accepted/` once (15.77 GiB) to `/content/quran_accepted`.
2. `prepare_pron_dataset.py` (written, untracked, **not run**) → dataset root +
   `selection_report.json` + `excluded_ayat.jsonl`.
3. Validation gates (must all pass before upload):
   - object counts match the report exactly; every `.mp3` has a same-stem `.txt`;
   - captions byte-equal a fresh re-derivation from the JSON texts;
   - every selected combo maps to an accepted source file; list any gaps;
   - decode a random sample (≥50) with `ffprobe` (mp3, 48 kHz-capable, duration > 0);
   - no filename >255 bytes; ASCII-safe reciter names.
4. Upload to GCS (new prefix, never `pron_dataset`).

## 4. Hidden costs: the per-VM caches (sized from source, 2026-09-26)

AI-Toolkit writes two caches per run under the dataset folder, **neither mirrored
to GCS**, so a fresh VM rebuilds them before the first training step:
`_latent_cache` (`cache_latents_to_disk` is mandatory for YuE2) and, with
`cache_text_embeddings: true`, `_t_e_cache`. Sized from the actual dataset and the
YuE2 source (`vae.py`, `model.py`, `tokenizer.py`, `yue2_model.py`):

Measured inputs: 46,440 train combos; ×2 text variants = **92,520 train files**;
total audio **513 h** (256.5 h ×2); clip durations median 16 s, mean 19.9 s,
max 260 s.

- **Latent cache** = VAE latents (64 ch × 25 fps × bf16 = **3.2 KB/s of audio**)
  + codec tokens (int32) ≈ **~5.7 GiB** for the whole train split.
- **Text-embedding cache** = the AR prefix embeddings `[L, 2048]` bf16
  (`yue2_model.py:get_prompt_embeds` → `YuE2TextEncoder`). `L` ≈ 80–150 tokens
  (instruction + tags + `[Lyrics]` + ayah) → ~0.33–0.61 MB per file →
  **~28–53 GiB**. It is **9× redundant**: the caption is identical across the 9
  reciters, but the cache path includes the file stem, so it is stored per file.
- **Total cache ≈ 34–59 GiB**, rebuilt on every fresh VM.

Two findings that shrink this a lot:

1. **`cache_text_embeddings` is nearly pointless here.** `YuE2TextEncoder` is
   just `ar.embed(ids)` — an embedding-table lookup, no transformer. Disabling it
   and recomputing per step costs almost nothing and removes ~28–53 GiB and the
   corresponding rebuild time. *Recommended: set `cache_text_embeddings: false`
   for this run.*
2. **The two text variants duplicate identical audio.** `_simple.mp3` and
   `_uthmani.mp3` are byte-identical, yet each gets its own (expensive) VAE +
   MERT/codec-token cache entry. Emitting only one audio per combo (e.g.
   uthmani-only, §7 B) halves the costly cache build.

Remaining mitigation (decide after a Phase-3 smoke that times a small build):
persist `_latent_cache` to GCS via `backup_to_gcp.py --extra` and restore on boot.
The expensive part is the per-clip VAE + MERT/head pass, so this is worth it if we
keep the cache at all.

## 5. Multi-day continuity design

### 5.1 Run identity
- One run name, one config, one GCS prefix for the whole multi-day effort.
- `ai-toolkit` auto-resumes: `get_latest_save_path()` picks the newest
  `<name>*.safetensors`, loads its `training_info.step` and `optimizer.pt`, and
  continues. Same name + same config = resume; anything changed = a new run.
- **Invariant:** never run the same run name on two VMs at once.

### 5.2 Checkpoint cadence (the core of "save every 30 min")
`save.save_every` is in **steps**, so it is derived after a timing smoke on the
real dataset:
```
save_every = clamp(round(30*60 / s_per_step), 100, 4000)
```
`max_step_saves_to_keep` kept high enough that checkpoints survive until the
5-min GCS mirror lands (e.g. 8–12). Checkpoints are EMA weights; each save also
writes `optimizer.pt`.

### 5.3 Backup cadence
`backup_to_gcp.py --run-name <run>` runs detached every 5 min (already
calibrated; it skips `loss_log.db*` and TensorBoard event files when deciding a
folder has settled). Worst-case loss on VM death = one checkpoint interval.
Before each pause, force `--once` and confirm the newest checkpoint + optimizer
are in GCS.

### 5.4 Session lifecycle
- **Start:** `train_ctl.py start --config <cfg> --run-name <run> --log-name <log>`
  (detached; `start` is Ctrl+C-proof).
- **Pause:** `train_ctl.py stop --log-name <log>` (checkpoint-safe SIGINT) →
  `backup_to_gcp.py --run-name <run> --once` → verify GCS has newest ckpt.
- **Resume (fresh VM):** clone → `bootstrap/setup.sh` → restore dataset →
  restore run output prefix into `output/<run>/` → start sidecars → relaunch the
  **identical** command (user-typed). Log must show "Found step N", not step 0.
- The latent cache rebuilds on every fresh VM (§4) unless we persist it.

### 5.5 Hazards (from `DECISIONS.md`, verified against ai-toolkit)
- EMA restarts a fresh average on resume (continues from EMA'd weights). Known,
  accepted for the reference run; flag if we rely on EMA.
- The un-suffixed final adapter (`<run>.safetensors`) is a same-name overwrite;
  safe here because the run name is new, but never re-point an old config at it.
- `train.start_step` only overrides the counter, never which checkpoint loads.
- Dataset folder must be immutable once training starts (changes desync cache).

## 6. Phased execution (gates in brackets)

0. **Plan + branch** (this doc). [user review]
1. **Build dataset** (download → build → validate). [validation gates pass]
2. **Upload dataset to GCS + document restore.** [object counts verified]
3. **Timing/cache smoke** on the `smoke` split (GPU): measure s/step, VRAM, cache
   bytes/clip, encode rate → finalize `save_every`, `max_step_saves_to_keep`,
   and decide §4 mitigation. [numbers recorded]
4. **Write the run config** (new name; dataset path; `steps` = chosen target;
   save cadence from Phase 3; everything else copied from `pron_lora_ar_only.yml`
   unless justified). [user approves — config is the user's]
5. **Launch + monitor** across sessions per §5. [user types the launch]
6. **Merge / inference** later via the existing pron merge tooling.

## 7. Cost & scope options (decide after Phase 3 timing)

Full 1 epoch = 92,520 steps. At the reference's short-clip ~0.9 s/step that is
~23 h, but our clips are ~2× longer, so expect materially more. Options if the
budget is too large:
- **A. As-is** — 92,520 pairs (max data).
- **B. Uthmani-only** — 46,260 pairs, halves steps, cache and disk (no
  duplicate identical audio).
- **C. Cap ayah length** (e.g. drop >40 words) — bounds per-step memory/time.
- **D. Fixed step budget** — keep the full dataset but train to a chosen step
  count (e.g. 30k) and use the best checkpoint; we do not have to finish an epoch.

"Train as much as possible" + multi-day = A or D; B/C are the cost levers.

## 8. Risks
- **Per-VM cache rebuild** (§4) is the main time cost; must measure.
- Longest clips (145 words) — memory/time outliers; verify no OOM, consider cap.
- Colab 12 h session limits / reclaims — mitigated by detached run + 30-min saves.
- Disk is **not** a binding constraint: the target VM has ~220 GB, and the whole
  set (28 GB audio + ≤60 GB cache + ~20 GB model caches) fits. Rebuild *time* is
  the constraint, not space.
- Naming: dataset/run/GCS prefixes are provisional until you set them (§9).

## 9. Open decisions
1. **Pair count:** A / B / C / D (§7)?
2. Persist the latent cache to GCS (yes/no)?
3. Exact run name + GCS prefixes (local dataset root, dataset prefix, run prefix)
   — currently provisional (`pron_lora_long_r8`, `quran_pron_long_dataset/`).
4. Commit this plan + `prepare_pron_dataset.py` on `pron-lora-long`? (local only;
   no push without your auth)

---

## 10. As-built addendum (2026-09-27)

Reconstructed after the VM loss. **The plan body above is the pre-build revision;
the dataset on GCS is FINAL and supersedes §3's numbers.**

- Filtering actually applied: `min_words=6`, `max_words=60` (long ayat above 60
  words were discarded), `max_repeat=2`. Plan §3.1/§3.3 said `min_words=5` and no
  cap; that revision was superseded during the build.
- Built dataset (verified): **4,670 ayat selected**, 1,566 excluded
  (1,524 below / 28 above / 14 duplicate). **81,006 train pairs**, val 352,
  smoke 14 → 28.04 GiB.
- Captions end with ` ۝` (U+06DD ARABIC END OF AYAH) — appended in a later,
  separately-verified step.
- Location (final): `gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/quran_long_aya_dataset/`
- Lost with the VM (reconstructed now): `prepare_pron_dataset.py`, the run config,
  and the specs files. Recovered from the surviving report: prompt + all params.

### §9 open decisions — RESOLVED (locked; recovered from `GPU_OPENING_PROMPT.md`)
1. **Pair count: A** — keep both `simple` and `uthmani` (81,006 train pairs).
2. **Persist the latent cache to GCS: YES** — bank it once complete as
   `gs://.../quran_long_aya_dataset/_latent_cache.tar` (one-time, ~5.2 GiB).
3. **Run name / prefixes:** run `quran_long_aya_r8`; local dataset
   `/content/quran_long_aya_dataset`; dataset prefix `.../quran_long_aya_dataset/`;
   run output prefix `.../quran_long_aya_r8/output/`.
4. **Commit on `pron-lora-long`:** yes — branch `pron-lora-long` off
   `pron-lora-ar-only` (not `main`).
- Config: `config/quran_long_aya_r8.yml` — steps 81,006 · `save_every: 1500` ·
  `max_step_saves_to_keep: 24` · `cache_text_embeddings: false` ·
  `cache_latents_to_disk: true`; else identical to `pron_lora_ar_only.yml`.
- First launch pays the one-time latent-cache build (~5–9 h) before step 1; the
  training config must not be edited after launch (see `GPU_OPENING_PROMPT.md`).
