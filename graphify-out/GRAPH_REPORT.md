# Graph Report - maqamrock-yue2-lora-finetuning  (2026-09-28)

## Corpus Check
- 57 files · ~231,345 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 953 nodes · 1867 edges · 71 communities (48 shown, 23 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 70 edges (avg confidence: 0.81)
- Token cost: 94,705 input · 72,340 output

## Community Hubs (Navigation)
- Agent Notes & Session State
- YuE2 Batch Generation CLI
- GCS Backup Tests
- Pron LoRA Merge
- Docs Reconciler
- Offline AR Loss Replay
- Duration Cap Tests
- Blind A/B Eval
- Training Metrics & GPU Telemetry
- generate.py Unit Tests
- GCS Backup Tool
- Training Run Control
- Pron Dataset Prep
- Duration Cap & Quantile
- Suno to Songs Conversion
- Plotting & Numerics Deps
- Pron Dataset Selection Plan
- Blind Eval Tests
- AudioCpp Build Docs
- Loss Monitoring
- Test Fixtures
- Training Loss Analysis
- Pron Sweep Experiments
- Ayah Symbol Appending
- Train Control Tests
- Replay Tests
- Dataset Prep Pipeline
- Pron-Long Reconciliation
- Pron LoRA Runbook
- Maqam Lyric Swap
- Listening Experience Checklist
- Held-Out Eval Set
- Pron Dataset Sampling
- Batch Runner Tests
- L4 vs A100 Economics
- GPU Logger
- Duration Cap CLI
- suno_to_songs CLI Tests
- Graphify Tooling Internals
- Generation Helper Tests
- Pron Training Analysis
- Repo Audit Backlog
- Graphify OpenCode Plugin
- Preflight Tests
- Training Analysis Docs
- Loss Curve Chart Insights
- Pron Knob Probe
- Regenerate Script
- Graphify Runtime Artifacts
- QFinal Suno Sweep
- OpenCode Config
- Duration Cap Parity Tests
- GitHub Auth Script
- Graphify Query Surface
- Pron Alpha Sweep
- Pron Fine Sweep
- Per-Track Runner
- Run-Dir Collision Test
- Per-Song LoRA Test
- Graph Fan-out Notes
- Graphify Explain
- Graph HTML Output
- Graphify Install
- Map vs Territory Note
- Graphify Path Query
- setup.sh Secrets Env
- ai-toolkit Training Engine
- GCS Backup Log
- Exception Node
- Fixture Node
- Training Log

## God Nodes (most connected - your core abstractions)
1. `FakeGsutil` - 35 edges
2. `_patch()` - 31 edges
3. `_invoke()` - 22 edges
4. `check()` - 19 edges
5. `main()` - 18 edges
6. `make()` - 16 edges
7. `resolve_songs()` - 16 edges
8. `Pronunciation LoRA runbook` - 16 edges
9. `run_batch()` - 15 edges
10. `Inference runbook` - 15 edges

## Surprising Connections (you probably didn't know these)
- `v1 to v2 Supersession` --semantically_similar_to--> `Retraction: LoRA Conversion Required`  [INFERRED] [semantically similar]
  verification.md → docs/yue2-gguf-lora-findings.md
- `akbar_arabic_rock_lora training config` --shares_data_with--> `TensorBoard events`  [INFERRED]
  config/akbar_arabic_rock_lora.yml → DECISIONS.md
- `Pronunciation LoRA verification` --references--> `run.py (ai-toolkit)`  [EXTRACTED]
  docs/PRON_LORA_VERIFICATION.md → run.py
- `SKILL.md (command-handover)` --references--> `run.py (ai-toolkit)`  [EXTRACTED]
  skills/command-handover/SKILL.md → run.py
- `SKILL.md (crash-diagnose-and-resume)` --references--> `run.py (ai-toolkit)`  [EXTRACTED]
  skills/crash-diagnose-and-resume/SKILL.md → run.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **he_loss_metric_panel** — training_analysis_v1_nolyrics_archived_01_loss_curves, concept_loss_loss, concept_loss_ar_ce, concept_loss_ar_kl, concept_additional_model_loss [EXTRACTED 1.00]
- **Docs Reconciliation Workflow** — skills_docs_reconciler_skill, skills_docs_reconciler_scripts_extract_claims, skills_docs_reconciler_scripts_verify_claims, skills_docs_reconciler_skill_human_checkpoint, skills_docs_reconciler_references_example_drift_report [EXTRACTED 1.00]
- **Per-GPU CUDA Build Workflow** — docs_audiocpp_gpu_arch_builds, docs_audiocpp_gpu_arch_builds_cross_compilation, docs_audiocpp_gpu_arch_builds_cuda_arch_flag, docs_audiocpp_gpu_arch_builds_sass_vs_ptx, docs_audiocpp_gpu_arch_builds_per_arch_gcs_staging, docs_audiocpp_gpu_arch_builds_build_verification, docs_audiocpp_gpu_arch_builds_t4_sm75_worked_example [EXTRACTED 1.00]
- **Pronunciation Alpha Sweep Results** — results_pron_sweep_readme, results_pron_sweep_readme_pron_alpha_sweep, results_pron_sweep_readme_short_collapse [EXTRACTED 1.00]
- **pron_lora_ar_only_r8_loss_terms** — concept_loss_loss_metric, concept_loss_ar_ce_metric, concept_loss_ar_kl_metric, concept_additional_model_loss_metric [EXTRACTED 1.00]
- **pron_lora_ar_only_r8_training_run** — concept_pron_lora_ar_only_r8_run, training_analysis_pron_lora_ar_only_r8_01_loss_curves, training_analysis_pron_lora_ar_only_r8_02_loss_main, training_analysis_pron_lora_ar_only_r8_03_learning_rate, training_analysis_pron_lora_ar_only_r8_04_throughput, training_analysis_pron_lora_ar_only_r8_05_gpu_usage [EXTRACTED 1.00]
- **hyper_training_analysis_akbar_run_observability** — training_analysis_01_loss_curves_chart, training_analysis_02_loss_main_chart, training_analysis_03_learning_rate_chart, training_analysis_04_throughput_chart, training_analysis_05_gpu_usage_chart, training_analysis_02_loss_main_akbar_arabic_rock_lora_run [INFERRED 0.85]
- **he_run_observability** — training_analysis_v1_nolyrics_archived_01_loss_curves, training_analysis_v1_nolyrics_archived_04_throughput, training_analysis_v1_nolyrics_archived_05_gpu_usage, concept_akbar_arabic_rock_lora_run, concept_sample_eval_interval [INFERRED 0.85]
- **YuE2 LoRA training config family** — config_akbar_arabic_rock_lora, config_pron_lora_ar_only, config_pron_lora_ar_only_smoke, config_quran_long_aya_r8, config_quran_long_aya_r8_s10 [EXTRACTED 0.90]

## Communities (71 total, 23 thin omitted)

### Community 0 - "Agent Notes & Session State"
Cohesion: 0.07
Nodes (81): agent_notes / current, Still pending from last session — qfinal sweep (do not lose), ostris/ai-toolkit (pinned), aitk_db.db, audio.cpp, Learning rate is a flat constant line across all ~8000 steps, no warmup or decay, GPU memory steady near ~8500 MiB, temperature ~75 C plateau, power ~65 W, GPU utilization is bursty, oscillating between near 0 and 100% (+73 more)

### Community 1 - "YuE2 Batch Generation CLI"
Cohesion: 0.09
Nodes (60): Exception, _abs_path(), asset_fingerprint(), build_parser(), build_tracks(), _cap_settings(), check(), draw_seeds() (+52 more)

### Community 2 - "GCS Backup Tests"
Cohesion: 0.10
Nodes (44): _args(), _close_log_handlers(), _dirs(), FakeGsutil, _invoke(), lg(), _patch(), fixture (+36 more)

### Community 3 - "Pron LoRA Merge"
Cohesion: 0.07
Nodes (36): _ab(), build_metadata(), _check_alpha_keys(), main(), merge(), MergeError, _proj(), Exception (+28 more)

### Community 4 - "Docs Reconciler"
Cohesion: 0.08
Nodes (42): collections, fnmatch, re, Example Drift Report, Missing Path Findings, Unverifiable Counts, Source of Truth Template, Authority Table (+34 more)

### Community 5 - "Offline AR Loss Replay"
Cohesion: 0.10
Nodes (33): attach_adapter(), build_arg_parser(), build_model(), _import_ai_toolkit(), ItemResult, list_val_pairs(), load_config_sections(), main() (+25 more)

### Community 6 - "Duration Cap Tests"
Cohesion: 0.10
Nodes (25): pytest, runpy, _invoke_cli(), parametrize, Path, Unit tests for INFERENCE/duration_cap.py (GPU-free). The CLI `main()` is…, test_cli_default_quantile(), test_cli_empty_lyrics_uses_floor() (+17 more)

### Community 7 - "Blind A/B Eval"
Cohesion: 0.12
Nodes (24): Blinded A/B Listening Package, EVAL.txt / KEYS.txt Public-Secret Split, ab-blind-eval Skill, build_parser(), _discover(), _ffmpeg_convert(), _group_pairs(), is_relative_to_dir() (+16 more)

### Community 8 - "Training Metrics & GPU Telemetry"
Cohesion: 0.13
Nodes (27): Additional Model Loss, additional_model_loss metric, akbar_arabic_rock_lora Training Run (3000 steps), checkpoint save interval every 1525 steps, gpu_logger.py (10s GPU sampling script, data source), GPU telemetry (utilization, memory, temperature, power), learning rate schedule (constant 1e-4), Autoregressive Cross-Entropy Loss (loss/ar_ce) (+19 more)

### Community 10 - "GCS Backup Tool"
Cohesion: 0.16
Nodes (24): ensure_manifest(), main(), parse_args(), parse_extra_specs(), parse_watch_specs(), Namespace, Path, Same shape as TRAINING_TARGETS, but for an arbitrary run name. `--run-name`… (+16 more)

### Community 11 - "Training Run Control"
Cohesion: 0.22
Nodes (22): _alive(), build_parser(), cmd_start(), cmd_status(), cmd_stop(), _cmdline(), _cmdline_matches(), main() (+14 more)

### Community 12 - "Pron Dataset Prep"
Cohesion: 0.14
Nodes (22): concurrent_futures, dataclasses, build(), write_one(), choose_splits(), Config, discover_source_audio(), load_tanzil() (+14 more)

### Community 13 - "Duration Cap & Quantile"
Cohesion: 0.16
Nodes (23): Text Length to Audio Duration Cap (yue2_dataset), Asymmetric Loss Favors a High Quantile, Centre Fit (Not a Cap), Duration Cap Formula, Arabic Letter Counting Rule, Quantile (Pinball-loss) Regression, Running a LoRA on the Yue2-3B GGUF Model: Findings, AR / NAR Stages (+15 more)

### Community 14 - "Suno to Songs Conversion"
Cohesion: 0.15
Nodes (22): build_parser(), build_report(), build_style(), canonical_tag(), clean_lyrics(), clean_lyrics_verbatim(), collect_entries(), dedup() (+14 more)

### Community 15 - "Plotting & Numerics Deps"
Cohesion: 0.16
Nodes (21): csv, datetime, matplotlib, matplotlib_pyplot, ndarray, numpy, sqlite3, main() (+13 more)

### Community 16 - "Pron Dataset Selection Plan"
Cohesion: 0.09
Nodes (22): 1. Objective, 2. Locked decisions, 3.1 Selection (from `selection_report.json`), 3.2 Output shape (reference-compatible), 3.3 Scale (as built), 3.4 Build pipeline (DONE; builder reconstructed for reproducibility), 3. Dataset (BUILT, VALIDATED, FINAL), 4.1 Latent cache (kept; banked) (+14 more)

### Community 17 - "Blind Eval Tests"
Cohesion: 0.16
Nodes (18): make(), Path, Unit tests for INFERENCE/prepare_ab_eval.py (GPU-free, ffmpeg-free). The audio…, rec_by_file(), test_bad_variant_name_errors(), test_categories_and_duplicate_stems_get_prefix(), test_category_filter(), test_dry_run_writes_nothing() (+10 more)

### Community 18 - "AudioCpp Build Docs"
Cohesion: 0.19
Nodes (19): Building audiocpp_cli for a Specific GPU from a CPU-only Colab Runtime, scripts/build_linux.sh, Build Verification Procedure, ccache Build Caching, Compute Capabilities for T4 / A100 / L4, nvcc Cross-Compilation on a CPU Host, --cuda-arch Flag, Per-arch GCS Staging Convention (+11 more)

### Community 19 - "Loss Monitoring"
Cohesion: 0.21
Nodes (16): Connection, Check how training is going, gpu_usage.csv hardware log, loss_log.db per-step metrics surface, connect_readonly(), history(), latest_step(), list_keys() (+8 more)

### Community 20 - "Test Fixtures"
Cohesion: 0.23
Nodes (15): bak(), dur(), gen(), _load_module(), lyrics_ar(), manifest_path(), _no_vram_sleep(), fixture (+7 more)

### Community 21 - "Training Loss Analysis"
Cohesion: 0.17
Nodes (16): additional_model_loss component declining from ~5.8 to ~3.9, loss/ar_ce component (autoregressive cross-entropy) declining from ~5.8 to ~3.6, loss/ar_kl component rising from 0 to ~1.5 (KL divergence term), Per-step loss curves 2x2 panel (loss/loss, loss/ar_ce, loss/ar_kl, additional_model_loss vs step), Per-step training loss metric (raw + 25-step mean), akbar_arabic_rock_lora training run, Primary loss/loss curve vs step with 50-step mean and trend line (-2.14e-04/step), loss_log.db SQLite metrics store (data source for loss curves) (+8 more)

### Community 22 - "Pron Sweep Experiments"
Cohesion: 0.17
Nodes (14): Cross-Maqam Lyric Swap, Pron Checkpoint Sweep, Fine Alpha Sweep at Checkpoint 3050, Request-Option Knob Probe, GPU/Architecture Dependence of Seed Reproducibility, Production Merge Candidates, safetensors Metadata Nondeterministic File sha256, A/B blind evaluation packaging (+6 more)

### Community 23 - "Ayah Symbol Appending"
Cohesion: 0.18
Nodes (12): main(), process(), Path, Append ' \u06dd' (space + ARABIC END OF AYAH) to the aya/lyrics line of each…, main(), Path, Pron checkpoint sweep: v2 + pron ckpt {1525, 4575} at alpha 0.5, Hijaz + Kurd.…, wav_frames() (+4 more)

### Community 24 - "Train Control Tests"
Cohesion: 0.23
Nodes (11): fixture, signal, _cli(), fake_env(), _load(), GPU-free tests for `train_ctl.py` (detached launch / clean SIGINT stop). No ai-…, tctl(), test_dry_run_launches_nothing() (+3 more)

### Community 26 - "Dataset Prep Pipeline"
Cohesion: 0.26
Nodes (12): build_caption(), find_audio_files(), main(), normalize(), parse_fields(), process_workspace(), Path, normalized filename -> Path, for every audio file physically present in this… (+4 more)

### Community 27 - "Pron-Long Reconciliation"
Cohesion: 0.17
Nodes (12): Corrections the rewrite MUST make (found 2026-09-27 via local `gsutil`), Ground truth (verified 2026-09-27, git + local gsutil), Locked decisions (this session), Merge-to-main plan (BETA) — decisions locked, Phase 1.5 — the supersede rename, repo + GCS in lockstep — **DONE**, Phase 1 — doc rewrite ON `pron-lora-long` — **DONE (uncommitted)**, Phase 2 — skipped (knobs stays on its branch), Phase 3 — the merge (fast-forward) + tag (+4 more)

### Community 28 - "Pron LoRA Runbook"
Cohesion: 0.18
Nodes (11): Checkpoint-eval on a second (T4) VM — while training runs, Commands that matter, Docs, First GPU session only (kickstart; obsolete once a checkpoint exists), Long-aya Quran pronunciation LoRA — runbook (canonical), Progress log (append one row per session), Prompts to paste, Resume after a pause (+3 more)

### Community 29 - "Maqam Lyric Swap"
Cohesion: 0.28
Nodes (8): argparse, main(), plan(), Path, Cross-maqam lyric swap: one maqam's caption+tag with the other's held-out…, Resolve each track's inputs + auto cap without touching the GPU., wav_frames(), os

### Community 30 - "Listening Experience Checklist"
Cohesion: 0.25
Nodes (7): 1. The gut read, 2. Score the experience (1 = bad, 5 = great), 3. Pitfalls I hit (tick what's true), 4. Moments, 5. The one thing, 6. Hand this to the agent (copy + fill), Working with the agent — experience checklist

### Community 31 - "Held-Out Eval Set"
Cohesion: 0.25
Nodes (8): Byte-Identity Proof (267/267), Step 5 Held-Out Checks, Held-Out Maqam Evaluation Set, Four Per-Maqam Picks, prepare_yue2_dataset_v2.py Build Functions, Run YAML Is Canonical Lyrics, Held-Out Samples YAML Block, Four Held-Out Lyric Prompts

### Community 32 - "Pron Dataset Sampling"
Cohesion: 0.46
Nodes (7): random, combos(), copy_file(), copy_split(), main(), Path, sample_pron_dataset.py ---------------------- Build a frozen random subsample…

### Community 33 - "Batch Runner Tests"
Cohesion: 0.25
Nodes (5): _make_run(), test_main_keyboard_interrupt(), test_materialize_writes_prompts_manifest_input(), test_run_batch_ok_then_skip_then_force_fail(), boom()

### Community 34 - "L4 vs A100 Economics"
Cohesion: 0.38
Nodes (7): L4 vs A100 decision note, A100-SXM4-80GB, A100 measured ~4.3x faster than L4 (3.10 s/step), A100 vs L4 break-even compute-unit economics, NVIDIA L4 (24 GB, 121 TFLOPS bf16), Live status snapshot (A100 post-resume), A100 resume from step-250 checkpoint

### Community 35 - "GPU Logger"
Cohesion: 0.33
Nodes (6): main(), poll(), gpu_logger.py -------------- AI Toolkit logs no GPU…, shutil, subprocess, time

### Community 36 - "Duration Cap CLI"
Cohesion: 0.38
Nodes (6): arabic_letters(), duration_cap(), main(), Dynamic YuE2 `semantic_max_tokens` cap derived from a lyrics file. Canonical…, Return (duration_s, duration_rounded_10s, token_cap, quantile)., unicodedata

### Community 37 - "suno_to_songs CLI Tests"
Cohesion: 0.29
Nodes (4): _songs_json(), test_main_full_path_with_out_dir(), test_main_invalid_limit(), test_main_lora_overrides_plumbed()

### Community 38 - "Graphify Tooling Internals"
Cohesion: 0.33
Nodes (6): graphify-out/cache/ per-file extraction cache, Extraction cache keyed by version and prompt, graphify-out/manifest.json, Doc/paper semantic extraction assistant skill, Dated snapshot graphify-out/<YYYY-MM-DD>/, graphify update .

### Community 39 - "Generation Helper Tests"
Cohesion: 0.33
Nodes (5): Minimal stand-in for subprocess.CompletedProcess., _Run, test_gpu_info(), test_wait_vram_free_paths(), test_wav_duration()

### Community 40 - "Pron Training Analysis"
Cohesion: 0.33
Nodes (6): Caveats, Loss trend (per 810-step decile), Next steps, Observations / flags, Run at a glance, Training analysis — `quran_long_aya_r8_s10` (long-aya Quran pronunciation LoRA, 10% subsample)

### Community 41 - "Repo Audit Backlog"
Cohesion: 0.50
Nodes (5): Repo audit: stale docs, drift & workflow backlog, No restore path for agent_notes/current.md, Flat inference out/ dir mixes unrelated runs, Staged scripts/ drifted from repo and self-perpetuates, Single status command for the whole job

### Community 42 - "Graphify OpenCode Plugin"
Cohesion: 0.40
Nodes (3): IMPORTANT: keep the reminder string free of backticks and $(...) constructs., ref_fs, ref_path

### Community 43 - "Preflight Tests"
Cohesion: 0.40
Nodes (5): _stub_assets(), test_preflight_checks_every_registered_pair(), test_preflight_not_executable_binary(), test_preflight_refuses_active_training_and_gpu_check(), test_preflight_success()

### Community 44 - "Training Analysis Docs"
Cohesion: 0.40
Nodes (5): v2 Training Analysis — akbar_arabic_rock_lora, Lower loss/ar_ce Is Mechanism, Not Quality, pron Run A100 Data/CPU-Bound, pron_lora_ar_only_r8 Training Analysis, v1 No-Lyrics Training Analysis (Archived)

### Community 45 - "Loss Curve Chart Insights"
Cohesion: 0.50
Nodes (4): loss/ar_kl rises from 0 to ~1.35 while ar_ce falls, Grey vertical markers indicate a checkpoint save every 1500 steps, Per-step loss dashboard: four loss components over ~8000 steps with 25-step mean overlay, Per-step loss curves (4 panels)

### Community 46 - "Pron Knob Probe"
Cohesion: 0.83
Nodes (3): emit_sidecar(), opts_for(), pron_knob_probe.sh script

### Community 47 - "Regenerate Script"
Cohesion: 1.00
Nodes (3): fetch(), regenerate.sh script, sha256_of()

### Community 48 - "Graphify Runtime Artifacts"
Cohesion: 0.67
Nodes (3): graphify-out/graph.json, graphify-out/.graphify_python VM-specific interpreter, graphify.serve MCP server

### Community 51 - "Duration Cap Parity Tests"
Cohesion: 0.67
Nodes (3): parametrize, test_cap_parity_with_duration_cap_cli(), test_validation_errors()

## Knowledge Gaps
- **122 isolated node(s):** `Command`, `Input contract`, `Output contract`, `Repo conventions (follow these)`, `Verify` (+117 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 329 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **23 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Check how training is going` connect `Loss Monitoring` to `Agent Notes & Session State`, `GPU Logger`?**
  _High betweenness centrality (0.230) - this node is a cross-community bridge._
- **Why does `Live vs Frozen Doc Scope` connect `Docs Reconciler` to `AudioCpp Build Docs`, `Duration Cap & Quantile`?**
  _High betweenness centrality (0.073) - this node is a cross-community bridge._
- **What connects `Command`, `Input contract`, `Output contract` to the rest of the system?**
  _122 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Agent Notes & Session State` be split into smaller, more focused modules?**
  _Cohesion score 0.06615240766713418 - nodes in this community are weakly interconnected._
- **Should `YuE2 Batch Generation CLI` be split into smaller, more focused modules?**
  _Cohesion score 0.09453551912568306 - nodes in this community are weakly interconnected._
- **Should `GCS Backup Tests` be split into smaller, more focused modules?**
  _Cohesion score 0.1025974025974026 - nodes in this community are weakly interconnected._
- **Should `Pron LoRA Merge` be split into smaller, more focused modules?**
  _Cohesion score 0.06826241134751773 - nodes in this community are weakly interconnected._