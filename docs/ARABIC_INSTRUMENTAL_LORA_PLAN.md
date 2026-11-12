# Plan — `arabic_instrumental_lora` (style LoRA on the 482-track Arabic instrumental set)

_Status: **DRAFT 2026-11-12.** Nothing has been launched, and no training config exists yet:
this document is the proposal. Decisions D1–D10 are mine as defaults — reply "go with
defaults", or override any row, and the config + commands get written to match._

Goal: train a **fresh** YuE2 style LoRA from the base checkpoint on
`gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/arabic_instrumental_dataset.zip`
(482 tracks, 36.60 h), with the same recipe that produced v3, so that the only
difference between this run and v3 is the dataset.

**What this run is not:** not an extension of `v3_arabmaqamrock_lora` (§2), not a merge with
the pron donor, not a rebuild or filter of the dataset.

Authorities: dataset = `docs/ARABIC_INSTRUMENTAL_DATASET.md`; hyperparameters =
`config/v3_arabmaqamrock_lora.yml` · `_l4.yml`; training procedure = `docs/START.md`,
`docs/MONITOR.md`, `docs/PAUSE_RESUME.md`; GPU choice = `docs/GPU_L4_VS_A100.md`.

---

## 0. Verified findings (evidence first)

| # | Finding | How checked |
|---|---|---|
| F1 | The four GCS objects exist at the recorded sizes: `arabic_instrumental_dataset.zip` **3,162,874,610 B** (2026-11-12T10:49:46Z), plus `.zip.sha256` (98 B), `_manifest.json` (349,574 B), `_report.md` (2,966 B). | `gsutil ls -l .../arabic_instrumental_dataset*` |
| F2 | Manifest: **482 tracks**, **36.60 h**, audio 3,162,110,202 B; 460 `yt500` + 22 `fadhl_shaker_shortlist`; prompt prefix `Middle Eastern fusion, instrumental. `; `[Lyrics]` block = section tags only. | manifest read (`/tmp/ai_manifest.json`) |
| F3 | Duration distribution (from `audio_duration_s`): **min 143.1 s · p50 271.7 s · p90 335.3 s · max 478.3 s**. **0 tracks > 600 s**, 0 > 983 s. So `train_window_frames: 0` (whole song) is still inside the AR context ceiling (~983 s), as in v3. | same read |
| F4 | Caption status: **439 `ok`, 35 `fallback`, 6 `failed`, 2 `single_chunk`**; **283/482** carry a vocal term (`caption_vocal_terms` non-empty), **199** are clean. | same read |
| F5 | `bootstrap/setup.sh` already consumes a zip (`job_dataset_zip`, unzip **flat** into `/content/yue2_dataset`), so the config's `folder_path` does not change. | `sed -n 265,282p bootstrap/setup.sh` |
| F6 | **Blocker found: the bootstrap verify hard-codes 438 tracks** and fails the whole setup when a zip is used and the count differs (`setup.sh:552-556`). Pointing `GCP_DATASET_ZIP` at the 482-track zip fails bootstrap as written. | `sed -n 550,562p bootstrap/setup.sh` |
| F7 | **`trigger_word` is not inert on this dataset.** Toolkit injection prepends `trigger + " "` when the trigger appears **zero** times in the caption (`toolkit/prompt_utils.py:715-748`, recorded in `DECISIONS.md` line 26). `arabmaqamrock` appears in **none** of these captions, so reusing the v3 config verbatim would silently train on `arabmaqamrock Middle Eastern fusion, instrumental. …` — a prompt shape no inference script will ever produce. | `DECISIONS.md` line 26 + dataset prompt template |
| F8 | `train_ctl.py` starts `config/v3_arabmaqamrock_lora.yml` unless `--config` is passed, and names the run from the config stem unless `--run-name` is passed. | `train_ctl.py:40,260,268` |
| F9 | This VM is a **Tesla T4, 15,360 MiB, 0 % util, no processes**. The v3 whole-song run peaked at ~15.8 GB on an L4 (24 GB) and ~15–16 GB on an A100, so a T4 cannot train this recipe (and is Turing — no bf16 tensor cores). | `nvidia-smi`, `docs/GPU_L4_VS_A100.md` |
| F10 | The built, unzipped dataset still exists locally at `/content/arabic_instrumental_build/arabic_instrumental_dataset` (964 files); disk free **113.0 GB**. Useful for holdout/eval work without re-downloading; not used as the training path (provenance stays the GCS zip). | `ls`, `du`, `status.py` |

**Assumed, not verified** (named so they aren't mistaken for facts):
A1 step-time scaling with song length (§6, ±10 %); A2 latent-cache time (~22 min, scaled from
v3's ~20 min for 438); A3 that a 8-track holdout (§2 D7) changes training quality negligibly.

---

## 1. What gets trained, and where it goes

| | |
|---|---|
| Run name | `arabic_instrumental_lora` (A100 config) · `arabic_instrumental_lora_l4` (L4 config) |
| Config | `config/arabic_instrumental_lora.yml` + `…_l4.yml` (copies of the v3 pair, §3) |
| Dataset | `/content/yue2_dataset` ← `GCP_DATASET_ZIP` = the 482-track zip |
| Output | `/content/ai-toolkit/output/arabic_instrumental_lora/` |
| Metrics | `…/arabic_instrumental_lora/loss_log.db` → `monitor_loss.py` |
| GCS mirror | `<base>/arabic_instrumental_lora/` (sidecar `backup_to_gcp.py --run-name`) |
| Artifact | A/NAR-converted adapter pair + sha256, evaluated by ear (§7) |

### 1.1 Composability — the point of a separate LoRA (your requirement, 2026-11-12)

You want this usable **on its own** and later **mixed** with the existing LoRAs. That constraint
shapes three things, and the plan already satisfies the first:

1. **Train from the base model, with no donor and no v3 init** (D1). A delta trained on top of
   another adapter is not a clean second term; the mix would be uninterpretable.
2. **Ship the converted pair, not just the ai-toolkit checkpoint.** The deliverable is the
   AR + NAR `.safetensors` pair produced by `converter/convert_aitoolkit_yue2_lora.py`, with its
   sha256 recorded — the same shape as everything in `<base>/loras/`. Raw ai-toolkit output is
   not loadable by audio.cpp.
3. **Mixing is an offline file merge, never a runtime flag.** `yue2.ar_lora` / `yue2.nar_lora`
   each accept exactly **one** file and one scale (`docs/PRON_LORA_MERGE.md` §Why a file merge).
   So "independently or mixed" means: render with this adapter at α=1 (standalone), and render
   from a fused file (mixed).

What is already supported, and what is not:

| Mix | Tool | Status |
|---|---|---|
| this style adapter + `quran_ahh_r32` pron donor | `merge_pron_lora.py --alpha` (rank-concat on the **AR** branch, NAR copied from style) | **Supported** — this LoRA slots in as the style input; α grid 0.2/0.5/1.0 as in `docs/PRON_LORA_SWEEP.md` |
| this adapter alone (α=1) | none needed | Supported — it is just a converted pair |
| this adapter + **v3 style** (style×style) | — | **Not supported today.** Every existing merge is style+pron; two full style adapters overlap on **both** AR and NAR, and no script merges two style deltas. If you want that, it is a new small tool (both branches, same rank-concat math) and a separate run decision. |

Two consequences for the config, both already in place: keep `linear/linear_alpha 32/32` and
`conv 16/16` (D3) so the file is rank-compatible with the library, and never overwrite v3's
`loras/audio_cpp/style/` — this becomes a **new** row there (`docs/LORA_INVENTORY.md`).

---

## 2. Decisions

| | Decision | Recommendation | Why |
|---|---|---|---|
| **D1** | Train a fresh LoRA from the **base** YuE2 (`Comfy-Org/YuE2/checkpoints/yue2_3b_int8_convrot.safetensors`), not from the v3 adapter | **Fresh from base** | Extending a finished run rewrites `<name>.safetensors` (`DECISIONS.md` §Run-lifecycle); `network.pretrained_lora_path` is weights-only and untested. Different caption distribution (prose vs structured tags) makes v3 a poor init anyway. |
| **D2** | New run name `arabic_instrumental_lora` (not `v3_…`) | **Yes** | Same-name launch auto-resumes `output/` checkpoints; a new name is the only clean start (`DECISIONS.md` line 47). |
| **D3** | Keep the v3 network/optimiser recipe unchanged (rank 32/32, conv 16/16, lr 1e-4, adamw8bit, EMA 0.999, bf16, whole-song window, `ar_kl_weight: 0`, `cot: off`) | **Unchanged** | One variable at a time: the dataset is the experiment. Any LoRA-size/LR change is a second variable and not measurable at n=1. |
| **D4** | `train.steps` = **5500** | **5500** | Reproduces v3's per-track exposure: 5000/438 = 11.42 epochs → 11.42 × 482 = **5504**. 5500 lands on the 250-step save cadence (§6). |
| **D5** | Train on **all 482** tracks as delivered (including the 41 `fallback`/`failed` captions and the 283 vocal-flagged ones) | **All 482** | The delivered artifact is the authority; filtering is a second dataset decision. The vocal flags are a captioner artifact inherited from the sources, and cutting 283 tracks would cut 59 % of the data. Revisit only if the first run's audio shows it mattered. |
| **D6** | `trigger_word` | **`Middle Eastern fusion`** | Present in every caption, so injection is a no-op (F7). Any trigger absent from the captions gets injected and mismatches inference. |
| **D7** | Hold out **8 tracks** (7 `yt500` + 1 `fs18`, 4 vocal-flagged + 4 clean, seed 42) from training and use them as the eval set | **Yes, 8** | v3's eval was contaminated because the train set contained every prompt (F8 in `docs/DATASET_V3_PLAN.md`). A real holdout costs 1.7 % of data and makes the listening test mean something. |
| **D8** | Train on L4, A100, or both | **A100 if turnaround matters; L4 is cost-equivalent** | Measured 4.3× (A100 3.10 s/step vs L4 13.4 s/step) against a 4.35× cost ratio: the A100 buys ~5 h instead of ~22 h for about the same money (§6). |
| **D9** | Do not touch `sample.samples` (three stale v3 prompts, inert because `disable_sampling: true`) | **Replace with 2 prose instrumental prompts** | They are inert during training but would be the template anyone copy-pastes for offline sampling — and the v3 format is the wrong prompt shape for this LoRA. |
| **D10** | Post-run deliverable = converted **AR + NAR pair** with sha256, registered as a new row in `<base>/loras/` | **Yes** | Makes it independently loadable and mixable (§1.1); the ai-toolkit checkpoint alone is not loadable by audio.cpp. |

---

## 3. The config — exact diff from v3

`config/arabic_instrumental_lora.yml` = `config/v3_arabmaqamrock_lora.yml` with **five** edits
(the `_l4` file = the `_l4` original with the same edits):

| key | v3 | proposed |
|---|---|---|
| `name` | `v3_arabmaqamrock_lora` | `arabic_instrumental_lora` |
| `log_dir` | `output/v3_arabmaqamrock_lora/tensorboard` | `output/arabic_instrumental_lora/tensorboard` |
| `trigger_word` | `arabmaqamrock` | `Middle Eastern fusion` (D6) |
| `train.steps` | `5000` | `5500` (D4) |
| `sample.samples` | 3 stale v3 maqam-rock poems | 2 instrumental prose prompts (D9, inert) |

Everything else stays byte-identical, including the parts that look odd but are deliberate:
`ar_kl_weight: 0.0`, `cot: "off"`, `train_window_frames: 0`, `gradient_checkpointing: false`
(A100) / `true` (L4), `disable_sampling: true`, `save_every: 250`,
`max_step_saves_to_keep: 12`, `cache_latents_to_disk: true`,
`cache_text_embeddings: true`, `datasets[0].folder_path: /content/yue2_dataset`,
`caption_ext: "txt"`, `caption_dropout_rate: 0`.

Two things **not** to copy from the v3 config into any new sampling prompt: the
`arabmaqamrock …` prefix and the `[Verse 1 | … ]` tag style. This dataset's prompts are prose
+ plain section tags, and training must match inference (`docs/ARABIC_INSTRUMENTAL_DATASET.md`
caveat 1).

---

## 4. Pre-flight (one code change, then GPU checks)

### 4.1 The bootstrap count check (F6)

`bootstrap/setup.sh` must stop assuming 438. Minimal change — an env var with the old value
as default, so nothing else moves:

```bash
# setup.sh, in the training verify block
-DATASET_EXPECTED=438
+DATASET_EXPECTED="${GCP_DATASET_COUNT:-438}"
 if [ -n "$DATASET_ZIP_URL" ] && [ "$track_count" -ne "$DATASET_EXPECTED" ]; then
-  echo "[FAIL] dataset: $track_count tracks in $DATASET_LOCAL (expected 438 for the v3 zip) — ..."
+  echo "[FAIL] dataset: $track_count tracks in $DATASET_LOCAL (expected $DATASET_EXPECTED) — ..."
```

Then the launching notebook stages, next to `HF_TOKEN` / `GCP_BACKUP_BASE`:

```bash
export GCP_DATASET_ZIP=gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/arabic_instrumental_dataset.zip
export GCP_DATASET_COUNT=482
```

This is a code change, not a hyperparameter change: it needs your approval, and it gets the
`docs-reconciler` pass + a `RECONCILIATION_LOG.md` entry in the same commit.

### 4.2 GPU rule

terminal: foreground — read-only, instant.

```bash
nvidia-smi
pgrep -af 'run.py|train_ctl|generate.py'
```

Expect a **24 GB L4 or an A100**, 0 % util, no `run.py`. If anything is running, stop here —
no overlap, ever. Today's VM is a T4 (F9): it cannot run this and must be switched first.

### 4.3 Bootstrap (fresh VM)

terminal: detached — log `/content/logs/setup.log`; stop: `pkill -f bootstrap/setup.sh`;
resume: re-run the same command (it skips what is already there).

```bash
mkdir -p /content/logs
cd /content/maqamrock-yue2-lora-finetuning
setsid nohup bash bootstrap/setup.sh --training > /content/logs/setup.log 2>&1 & disown
```

Watch for the verify block to end all-`[ok]` **and** to report `[ok] dataset: 482 tracks`.
Anything else (438, or `[FAIL] dataset:`) means the env var did not reach the shell — the
marker `/content/yue2_dataset/.bootstrap_complete` also means a re-run will skip the pull, so
delete `/content/yue2_dataset` (and the zip) before retrying.

### 4.4 Hold out the 8 eval tracks (D7)

Must run **after** the dataset verify and **before** `train_ctl.py start`, so the latent cache
never encodes them.

terminal: foreground — instant, but it moves files.

```bash
cd /content/maqamrock-yue2-lora-finetuning
python3 - <<'PY'
import json, random, pathlib, shutil
man = json.load(open('/content/arabic_instrumental_build/arabic_instrumental_dataset_manifest.json'))
recs = man['tracks']
rng = random.Random(42)
pick = []
for src, n_vocal, n_clean in (('yt500', 3, 4), ('fadhl_shaker_shortlist', 1, 0)):
    vocal = sorted((r for r in recs if r['source_dataset'] == src and r.get('caption_vocal_terms')),
                   key=lambda r: r['out_name'])
    clean = sorted((r for r in recs if r['source_dataset'] == src and not r.get('caption_vocal_terms')),
                   key=lambda r: r['out_name'])
    pick += rng.sample(vocal, n_vocal) + rng.sample(clean, n_clean)
out = pathlib.Path('/content/eval_holdout/arabic_instrumental'); out.mkdir(parents=True, exist_ok=True)
src = pathlib.Path('/content/yue2_dataset')
for r in pick:
    for ext in ('.mp3', '.txt'):
        shutil.move(str(src / (r['out_name'] + ext)), str(out / (r['out_name'] + ext)))
json.dump(pick, open(out / 'HOLDOUT.json', 'w'), indent=2)
print('held out', len(pick), 'tracks ->', out)
PY
find /content/yue2_dataset -maxdepth 1 -name '*.mp3' | wc -l   # expect 474
```

(3 + 4 from `yt500`, 1 from `fs18`; 4 vocal-flagged + 4 clean — the split `D7` promises. If the
build workspace is gone, read the manifest from GCS instead: `gsutil cp …/arabic_instrumental_dataset_manifest.json /tmp/`.)

The chosen names are then fixed by `HOLDOUT.json` — record them in `current.md` and do not
change them between runs, or the A/B loses its baseline.

---

## 5. Launch, monitor, stop, resume

### 5.1 Sidecars (before training)

terminal: detached — logs `/content/logs/gcp_backup_stdout.log`,
`/content/logs/gpu_logger_stdout.log`; stop: `pkill -f backup_to_gcp.py` /
`pkill -f gpu_logger.py`; resume: re-run the same two lines.

```bash
cd /content/maqamrock-yue2-lora-finetuning
setsid nohup python backup_to_gcp.py --run-name arabic_instrumental_lora \
  > /content/logs/gcp_backup_stdout.log 2>&1 & disown
setsid nohup python gpu_logger.py --out /content/logs/gpu_usage.csv \
  > /content/logs/gpu_logger_stdout.log 2>&1 & disown
pgrep -af 'backup_to_gcp.py|gpu_logger.py'
```

`GCP_BACKUP_BASE` must be exported by the notebook, or the daemon cannot mirror anything.

### 5.2 Start (you type this)

terminal: detached — log `/content/logs/train.log`; stop: `python train_ctl.py stop`;
resume: re-run the identical `start` command (same name auto-resumes the newest checkpoint).

```bash
cd /content/maqamrock-yue2-lora-finetuning
python train_ctl.py start --config config/arabic_instrumental_lora.yml \
  --run-name arabic_instrumental_lora --dry-run    # print the launch, no GPU
python train_ctl.py start --config config/arabic_instrumental_lora.yml \
  --run-name arabic_instrumental_lora              # the real launch
```

`--config` and `--run-name` are mandatory here (F8) — the defaults still point at v3, and a
"default" launch would train the v3 config against the instrumental dataset under the v3 name,
which is the exact same-name-resume hazard `DECISIONS.md` warns about.

The first ~22 min is latent caching (A2), then step 0. `loss_log.db` stays at 0 steps during
caching — normal.

### 5.3 Monitor

terminal: foreground — read-only.

```bash
python monitor_loss.py /content/ai-toolkit/output/arabic_instrumental_lora/loss_log.db \
  --watch 30 --total-steps 5500
python status.py
```

Read `loss/loss` as a smoothed trend (batch 1 is noisy). Reference shape from v3: still
descending at the end, `ar_kl` irrelevant at weight 0. Loss is **not** the verdict — audio is.

---

## 6. Effort, wall clock, cost

Steps: **11.42 epochs** at 5500/482 = 11.41 (5500/474 = 11.60 with the holdout).

| GPU | measured step | 5500 steps | + cache (A2) | notes |
|---|---:|---:|---:|---|
| A100 (40/80 GB) | 3.10 s | **4.7 h** | ~5.0 h | +~10 % if songs run longer than v3's (A1) |
| L4 (24 GB) | 13.4 s | **20.5 h** | ~21 h | `gradient_checkpointing: true`; peak ~15.8 GB |

Cost at the recorded rates (`6.7` / `1.54` per hour): **≈ $33 (A100 5 h) vs ≈ $32 (L4 21 h)** —
because measured speedup 4.3× sits on the 4.35× break-even. A100 buys the turnaround for free.

Reality check vs v3: v3 5000 steps completed in ~4.5–4.8 h on A100. This run is 10 % more
steps on songs that are somewhat longer, so **plan for ~5–6 h on A100 or ~22–24 h on L4**.

---

## 7. Evaluation (before anyone calls it good)

1. **Checkpoint ladder.** 5500/250 = 22 checkpoints; back up (5-min daemon) covers them.
   Offline-sample steps **3000 / 4000 / 5000 / 5500** — v3's lesson was that "done" ≠ "right".
2. **Held-out renders (D7).** Prompt each of the 8 held-out tracks with its own `.txt`
   verbatim; compare LoRA-on vs base-model (same seed, duration, sampler). This is the only
   contamination-free test set.
3. **Instruction-following probes.** 2–3 new prose prompts that mix elements not in any single
   training caption (e.g. an instrument/section combination), to check the LoRA follows prose
   rather than replaying prompts.
4. **Blind A/B.** Package variants with `INFERENCE/prepare_ab_eval.py` (skill `ab-blind-eval`)
   and rate with `docs/LISTENING_EVAL.md` — a 1–5 ear score, not loss.
5. **Only then**: pick the checkpoint, convert (AR/NAR), record the converted sha256, register a
   new `<base>/loras/` row (D10). Then the mix test: this adapter at α=1 (standalone) vs
   `merge_pron_lora.py --alpha {0.2, 0.5, 1.0}` with `quran_ahh_r32` (§1.1), same prompts and
   seeds, blind A/B. Publishing to HF stays a separate decision.

---

## 8. Risks

| Risk | Effect | Mitigation |
|---|---|---|
| Prose captions vs v3 structured tags | Prompting this LoRA with `arabmaqamrock …` text yields mush | D9 + §7.3; keep the two zips in separate runs (dataset caveat 1) |
| 283/482 captions name vocals while the prefix says "instrumental" | Mild train-time contradiction on 59 % of tracks | D5 (accept); the manifest flag allows a 199-track clean run later without a rebuild |
| 41/482 captions are `fallback`/`failed` rewrites | Prompt–audio mismatch on 8.5 % of tracks | Recorded in the manifest; filterable later; not worth a rebuild now |
| Effective variety < 482 (460 yt500 takes over 142 section plans) | 11.4 epochs may memorise rather than generalise | Checkpoint sweep + holdout (§7) — judge at 3000/4000/5000, not only the last |
| Same-name relaunch auto-resumes | A "fresh" run silently continues an old one | New run name (D2); check `output/` empty before launch |
| `trigger_word` injection (F7) | Every caption silently gets a foreign prefix | D6 + verify one cached caption in `train.log`/dataset path |
| Bootstrap count hard-coded 438 (F6) | `[FAIL] dataset:` and no training | §4.1 |
| T4 runtime | bf16 whole-song training impossible | §4.2 — switch GPU first |
| Dataset is synthetic (Suno/ACE takes) | The LoRA imitates generated takes, with their artifacts | Stated up front; this is a style adapter, not a quality gate |

---

## 9. Out of scope

- No training launch, no GPU work, no config written until you approve D1–D10.
- No dataset rebuild, filter, or edit — the zip stays the authority.
- No merge with `quran_ahh_r32` / v3, no HF publish, no `loras/` promotion.
- No change to `/content/yue2_dataset` contents beyond the D7 holdout move.

---

## 10. Execution checklist (in order)

- [ ] You approve D1–D10 (or override rows).
- [ ] Commit `config/arabic_instrumental_lora.yml` + `_l4.yml`, the `setup.sh` count change,
      this plan; run `docs-reconciler`; note it in `RECONCILIATION_LOG.md`; add a `docs/README.md`
      index row and a `SOURCE_OF_TRUTH.md` row (config + this plan).
- [ ] Update `docs/README.md` constants for the new run name once launched.
- [ ] Fresh L4/A100 VM; `GCP_DATASET_ZIP` + `GCP_DATASET_COUNT=482` staged.
- [ ] `nvidia-smi` clean → bootstrap detached → verify `[ok] dataset: 482 tracks`.
- [ ] Holdout move → 474 mp3.
- [ ] Sidecars up (`pgrep -af` shows both).
- [ ] `train_ctl.py start --config … --run-name …` (typed by you).
- [ ] First checkpoint at 250 reaches GCS before trusting the run.
- [ ] Eval at 3000/4000/5000/5500; record the verdict.
- [ ] Convert (AR/NAR), sha256, new `loras/` row; standalone vs α-mixed listening (§1.1, D10).
