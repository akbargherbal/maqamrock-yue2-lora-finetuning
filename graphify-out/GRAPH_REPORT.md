# Graph Report - maqamrock-yue2-lora-finetuning  (2026-09-27)

## Corpus Check
- 141 files · ~231,100 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 4 file(s) not represented in the graph (top: (none) 1, .ipynb 1, .ini 1)

## Summary
- 1006 nodes · 1797 edges · 72 communities (47 shown, 25 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 68 edges (avg confidence: 0.8)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `39d1bbde`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- generate.py
- GCS Backup Tests
- conftest.py
- pathlib
- test_generate.py
- unverifiable.txt token allowlist
- sys
- Offline AR-Loss Replay
- suno_to_songs.py
- GCS Backup Engine
- prepare_ab_eval.py
- A/B blind evaluation packaging
- Training Loss Curves
- test_merge_pron_lora.py
- YuE2 Findings & Docs
- test_prepare_ab_eval.py
- ext_root_secrets_env
- audiocpp Build Docs
- opencode.json
- Project Overview
- test_suno_to_songs.py
- Held-Out Eval & Dataset v2
- Training loss/loss Metric
- Agent Operating Contract
- Generated Listening Packages Live in GCS
- Operations Docs Runbook Index
- Pron LoRA Training Run
- train_ctl.py
- Observability Sources
- Training Configs
- v1 Run Lessons
- Inference Assets & LoRA Merge
- L4 vs A100 Decision
- Crash-Diagnose & Resume Skills
- prepare_pron_dataset.py
- monitor_loss.py
- Merge-to-main plan (BETA) — decisions locked
- test_duration_cap.py
- Repo Audit Backlog
- Inference End-to-End Runbook
- Arabic Pron LoRA Research Notes
- pron_knob_probe Script
- Merge Regenerate Script
- Rank / EMA / COT Rationale
- TensorBoard log_dir
- GitHub Auth Script
- Trigger Word
- pron_alpha_sweep Script
- pron_fine_sweep Script
- Latent Cache Config
- Dataset Folder Path
- Batch Verdict Criteria
- Dataset Naming
- Diffusion Trainer Type
- Whole-Song L4 vs A100
- Run Name Reuse
- Token-Count Check
- Torch Stack Pin
- graphify.js
- Working with the agent — experience checklist
- PRON LoRA LONG — build & multi-day training plan (`quran_long_aya_r8`)
- Training analysis — `quran_long_aya_r8_s10` (long-aya Quran pronunciation LoRA, 10% subsample)
- graphify.serve MCP server
- qfinal_suno_sweep.sh
- graphify-out/GRAPH_REPORT.md
- Graph is branch-specific; dangling-endpoint edges gap
- graphify explain
- graphify-out/graph.html
- graphify install --platform
- Map, not the territory
- graphify path
- Bootstrap Split --training / --inference

## God Nodes (most connected - your core abstractions)
1. `FakeGsutil` - 35 edges
2. `_patch()` - 31 edges
3. `_invoke()` - 22 edges
4. `Operations Docs Runbook Index` - 18 edges
5. `main()` - 17 edges
6. `check()` - 16 edges
7. `resolve_songs()` - 16 edges
8. `make()` - 16 edges
9. `run_batch()` - 15 edges
10. `setup_ab_evaluation()` - 13 edges

## Surprising Connections (you probably didn't know these)
- `A/B blind evaluation packaging` --semantically_similar_to--> `Blinded Listening Review`  [INFERRED] [semantically similar]
  skills/ab-blind-eval/SKILL.md → docs/PRON_LORA_SWEEP.md
- `Doc/paper semantic extraction assistant skill` --semantically_similar_to--> `docs-reconciler skill`  [INFERRED] [semantically similar]
  docs/GRAPHIFY.md → RECONCILIATION_LOG.md
- `v1 to v2 Supersession` --semantically_similar_to--> `Retraction: LoRA Conversion Required`  [INFERRED] [semantically similar]
  verification.md → docs/yue2-gguf-lora-findings.md
- `Inference Batch Run (YuE2 GGUF + LoRA)` --conceptually_related_to--> `Operations Docs Runbook Index`  [INFERRED]
  skills/inference-batch-run/SKILL.md → docs/README.md
- `README Observability Section` --semantically_similar_to--> `Training Observability Sources`  [INFERRED] [semantically similar]
  README.md → AGENTS.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Command Handover Discipline** — agents_command_handover_skill, docs_command_handover_gotchas_gotchas, decisions_command_handover, docs_command_handover_gotchas_detached_semantics [EXTRACTED 0.85]
- **audio.cpp Inference Pipeline** — docs_inference_runbook, inference_run_one, docs_inference_generate, inference_duration_cap, inference_suno_to_songs [EXTRACTED 0.85]
- **Training Observability Stack** — agents_observability_sources, decisions_loss_log_db_metrics, decisions_no_gpu_logging, readme_observability [EXTRACTED 0.85]
- **he_loss_metric_panel** — training_analysis_v1_nolyrics_archived_01_loss_curves, concept_loss_loss, concept_loss_ar_ce, concept_loss_ar_kl, concept_additional_model_loss [EXTRACTED 1.00]
- **Docs Reconciliation Workflow** — skills_docs_reconciler_skill, skills_docs_reconciler_scripts_extract_claims, skills_docs_reconciler_scripts_verify_claims, skills_docs_reconciler_skill_human_checkpoint, skills_docs_reconciler_references_example_drift_report [EXTRACTED 1.00]
- **Per-GPU CUDA Build Workflow** — docs_audiocpp_gpu_arch_builds, docs_audiocpp_gpu_arch_builds_cross_compilation, docs_audiocpp_gpu_arch_builds_cuda_arch_flag, docs_audiocpp_gpu_arch_builds_sass_vs_ptx, docs_audiocpp_gpu_arch_builds_per_arch_gcs_staging, docs_audiocpp_gpu_arch_builds_build_verification, docs_audiocpp_gpu_arch_builds_t4_sm75_worked_example [EXTRACTED 1.00]
- **Pronunciation Alpha Sweep Results** — results_pron_sweep_readme, results_pron_sweep_readme_pron_alpha_sweep, results_pron_sweep_readme_short_collapse [EXTRACTED 1.00]
- **pron_lora_ar_only_r8_loss_terms** — concept_loss_loss_metric, concept_loss_ar_ce_metric, concept_loss_ar_kl_metric, concept_additional_model_loss_metric [EXTRACTED 1.00]
- **pron_lora_ar_only_r8_training_run** — concept_pron_lora_ar_only_r8_run, training_analysis_pron_lora_ar_only_r8_01_loss_curves, training_analysis_pron_lora_ar_only_r8_02_loss_main, training_analysis_pron_lora_ar_only_r8_03_learning_rate, training_analysis_pron_lora_ar_only_r8_04_throughput, training_analysis_pron_lora_ar_only_r8_05_gpu_usage [EXTRACTED 1.00]
- **Training observability & backup stack (sidecars, metrics, restore)** — docs_start, docs_monitor, docs_pause_resume, backup_to_gcp, gpu_logger, monitor_loss [EXTRACTED 1.00]
- **External token families in unverifiable allowlist** — skills_docs_reconciler_references_unverifiable_ai_toolkit_clone, skills_docs_reconciler_references_unverifiable_audiocpp_clone, skills_docs_reconciler_references_unverifiable_runtime_artifacts, skills_docs_reconciler_references_unverifiable_external_cli_flags [EXTRACTED 1.00]
- **hyper_training_analysis_akbar_run_observability** — training_analysis_01_loss_curves_chart, training_analysis_02_loss_main_chart, training_analysis_03_learning_rate_chart, training_analysis_04_throughput_chart, training_analysis_05_gpu_usage_chart, training_analysis_02_loss_main_akbar_arabic_rock_lora_run [INFERRED 0.85]
- **he_run_observability** — training_analysis_v1_nolyrics_archived_01_loss_curves, training_analysis_v1_nolyrics_archived_04_throughput, training_analysis_v1_nolyrics_archived_05_gpu_usage, concept_akbar_arabic_rock_lora_run, concept_sample_eval_interval [INFERRED 0.85]
- **Blinded Listening Evaluation Rounds** — docs_pron_lora_sweep_alpha_sweep, results_pron_fine_sweep_readme_fine_sweep, results_pron_ckpt_sweep_readme_ckpt_sweep, results_maqam_lyric_swap_readme_lyric_swap, results_pron_knob_probe_readme_knob_probe, skills_ab_blind_eval_skill_a_b_blind_evaluation_packaging [INFERRED 0.85]
- **Docs reconciliation workflow** — reconciliation_log_docs_reconciler, reconciliation_log_drift_reconciliation, reconciliation_log_unverifiable_allowlist_curation, reconciliation_log_source_of_truth [INFERRED 0.85]
- **v2 + pron LoRA Merge Pipeline** — docs_pron_lora_merge_offline_merge, docs_pron_lora_merge_scaling_convention, docs_pron_lora_merge_rank_concatenation, results_pron_production_merge_readme_production_merge, docs_lora_inventory_lora_library [INFERRED 0.85]

## Communities (72 total, 25 thin omitted)

### Community 0 - "generate.py"
Cohesion: 0.10
Nodes (56): asset_fingerprint(), build_parser(), build_tracks(), _cap_settings(), check(), draw_seeds(), fail(), fmt_hms() (+48 more)

### Community 1 - "GCS Backup Tests"
Cohesion: 0.10
Nodes (44): _args(), _close_log_handlers(), _dirs(), FakeGsutil, _invoke(), lg(), _patch(), fixture (+36 more)

### Community 2 - "conftest.py"
Cohesion: 0.23
Nodes (15): bak(), dur(), gen(), _load_module(), lyrics_ar(), manifest_path(), _no_vram_sleep(), fixture (+7 more)

### Community 3 - "pathlib"
Cohesion: 0.08
Nodes (44): collections, datetime, fnmatch, pathlib, re, Example Drift Report, Missing Path Findings, Unverifiable Counts (+36 more)

### Community 4 - "test_generate.py"
Cohesion: 0.05
Nodes (23): _make_run(), parametrize, Unit tests for INFERENCE/generate.py (GPU-free)., Minimal stand-in for subprocess.CompletedProcess., _Run, _songs_json(), _stub_assets(), test_cap_parity_with_duration_cap_cli() (+15 more)

### Community 5 - "unverifiable.txt token allowlist"
Cohesion: 0.09
Nodes (27): graphify-out/cache/ per-file extraction cache, Extraction cache keyed by version and prompt, graphify-out/manifest.json, Doc/paper semantic extraction assistant skill, Dated snapshot graphify-out/<YYYY-MM-DD>/, graphify update ., Admission Test (keep only what a fresh session would re-litigate), DECISIONS/PROGRESS Consolidation (2026-09-23) (+19 more)

### Community 6 - "sys"
Cohesion: 0.07
Nodes (43): main(), process(), Path, Append ' \u06dd' (space + ARABIC END OF AYAH) to the aya/lyrics line of each…, argparse, csv, main(), poll() (+35 more)

### Community 7 - "Offline AR-Loss Replay"
Cohesion: 0.10
Nodes (34): dataclasses, attach_adapter(), build_arg_parser(), build_model(), _import_ai_toolkit(), ItemResult, list_val_pairs(), load_config_sections() (+26 more)

### Community 8 - "suno_to_songs.py"
Cohesion: 0.10
Nodes (34): build_parser(), build_report(), build_style(), canonical_tag(), clean_lyrics(), clean_lyrics_verbatim(), collect_entries(), dedup() (+26 more)

### Community 9 - "GCS Backup Engine"
Cohesion: 0.11
Nodes (32): ensure_manifest(), main(), parse_args(), parse_extra_specs(), parse_watch_specs(), Namespace, Path, Same shape as TRAINING_TARGETS, but for an arbitrary run name. `--run-name`… (+24 more)

### Community 10 - "prepare_ab_eval.py"
Cohesion: 0.11
Nodes (27): No Adapter Is Best Before the Blind Listen; alpha <= 0.5, Blinded A/B Listening Package, EVAL.txt / KEYS.txt Public-Secret Split, ab-blind-eval Skill, build_parser(), _discover(), _ffmpeg_convert(), _group_pairs() (+19 more)

### Community 11 - "A/B blind evaluation packaging"
Cohesion: 0.13
Nodes (22): Alpha Capped at 0.5, LoRA Library, Converted AR/NAR sha256 as Stable Identity, Offline v2 + pron LoRA Merge, Rank Concatenation Merge Method, ai-toolkit Scaling Convention (alpha/rank)*(B@A), Pronunciation LoRA Alpha Sweep, Blinded Listening Review (+14 more)

### Community 12 - "Training Loss Curves"
Cohesion: 0.13
Nodes (27): Additional Model Loss, additional_model_loss metric, akbar_arabic_rock_lora Training Run (3000 steps), checkpoint save interval every 1525 steps, gpu_logger.py (10s GPU sampling script, data source), GPU telemetry (utilization, memory, temperature, power), learning rate schedule (constant 1e-4), Autoregressive Cross-Entropy Loss (loss/ar_ce) (+19 more)

### Community 13 - "test_merge_pron_lora.py"
Cohesion: 0.07
Nodes (37): hashlib, _ab(), build_metadata(), _check_alpha_keys(), main(), merge(), MergeError, _proj() (+29 more)

### Community 14 - "YuE2 Findings & Docs"
Cohesion: 0.16
Nodes (23): Text Length to Audio Duration Cap (yue2_dataset), Asymmetric Loss Favors a High Quantile, Centre Fit (Not a Cap), Duration Cap Formula, Arabic Letter Counting Rule, Quantile (Pinball-loss) Regression, Running a LoRA on the Yue2-3B GGUF Model: Findings, AR / NAR Stages (+15 more)

### Community 15 - "test_prepare_ab_eval.py"
Cohesion: 0.06
Nodes (33): importlib_util, os, pytest, signal, Unit tests for offline_ar_loss_replay.py (CPU-only, no model load). The replay…, make(), Path, Unit tests for INFERENCE/prepare_ab_eval.py (GPU-free, ffmpeg-free). The audio… (+25 more)

### Community 17 - "audiocpp Build Docs"
Cohesion: 0.19
Nodes (19): Building audiocpp_cli for a Specific GPU from a CPU-only Colab Runtime, scripts/build_linux.sh, Build Verification Procedure, ccache Build Caching, Compute Capabilities for T4 / A100 / L4, nvcc Cross-Compilation on a CPU Host, --cuda-arch Flag, Per-arch GCS Staging Convention (+11 more)

### Community 19 - "Project Overview"
Cohesion: 0.40
Nodes (5): Env Vars Staged by Launching Notebook, README Docs Index, Project Overview, Repo Layout, Running on Colab Section

### Community 20 - "test_suno_to_songs.py"
Cohesion: 0.09
Nodes (28): main(), plan(), Path, Cross-maqam lyric swap: one maqam's caption+tag with the other's held-out…, Resolve each track's inputs + auto cap without touching the GPU., wav_frames(), main(), Path (+20 more)

### Community 21 - "Held-Out Eval & Dataset v2"
Cohesion: 0.13
Nodes (16): sample.samples Held-Out Prompts, duration 360, v2 Caption Lyric Format (binding), Dataset Verification: 267 Pairs, Held-Out Eval Set Contamination, sample.duration 360 Rationale and Cost, v2 Finished: Lyric Fix Worked; ar_kl Drift, Byte-Identity Proof (267/267), Step 5 Held-Out Checks (+8 more)

### Community 22 - "Training loss/loss Metric"
Cohesion: 0.17
Nodes (16): additional_model_loss component declining from ~5.8 to ~3.9, loss/ar_ce component (autoregressive cross-entropy) declining from ~5.8 to ~3.6, loss/ar_kl component rising from 0 to ~1.5 (KL divergence term), Per-step loss curves 2x2 panel (loss/loss, loss/ar_ce, loss/ar_kl, additional_model_loss vs step), Per-step training loss metric (raw + 25-step mean), akbar_arabic_rock_lora training run, Primary loss/loss curve vs step with 50-step mean and trend line (-2.14e-04/step), loss_log.db SQLite metrics store (data source for loss curves) (+8 more)

### Community 23 - "Agent Operating Contract"
Cohesion: 0.16
Nodes (15): Agent Operating Contract, Auto-Resume Exception Policy, Backup Responsibility, Colab Is Ephemeral, command-handover Skill, agent_notes/current.md Handoff Surface, Graphify Knowledge Graph Usage, Agent Training-Control Policy (+7 more)

### Community 25 - "Operations Docs Runbook Index"
Cohesion: 0.21
Nodes (12): Final backup & push checklist, GCS not append-only for the un-suffixed final adapter, Check how training is going, gpu_usage.csv hardware log, loss_log.db per-step metrics surface, Pause for the night, resume next session, ai-toolkit auto-resume from newest checkpoint, ai-toolkit Auto-Resume Rule (+4 more)

### Community 26 - "Pron LoRA Training Run"
Cohesion: 0.33
Nodes (11): L4 handoff after Task 14c, pron-lora-ar-only branch, No _000006100 checkpoint; post-loop save is step 6100, AR-only pronunciation LoRA runbook, pron_lora_ar_only_r8 training run, network_kwargs.ignore_if_contains AR/NAR scoping, Blank trigger_word no-op, AR-only pronunciation LoRA source verification (+3 more)

### Community 27 - "train_ctl.py"
Cohesion: 0.22
Nodes (22): _alive(), build_parser(), cmd_start(), cmd_status(), cmd_stop(), _cmdline(), _cmdline_matches(), main() (+14 more)

### Community 28 - "Observability Sources"
Cohesion: 0.32
Nodes (8): Training Observability Sources, CLI Over Web UI On Purpose, loss_log.db Is the Metrics Source, No GPU Logging in AI Toolkit, README Observability Section, One Authority Per Topic Table, Inference Procedure Authority, Run Config/Hyperparameters Authority

### Community 29 - "Training Configs"
Cohesion: 0.36
Nodes (8): akbar_arabic_rock_lora Training Config, pron_lora_ar_only Config (AR-only, rank 8), pron_lora_ar_only_smoke Config (10-step smoke), v2 Training Analysis — akbar_arabic_rock_lora, Lower loss/ar_ce Is Mechanism, Not Quality, pron Run A100 Data/CPU-Bound, pron_lora_ar_only_r8 Training Analysis, v1 No-Lyrics Training Analysis (Archived)

### Community 30 - "v1 Run Lessons"
Cohesion: 0.25
Nodes (8): train_window_frames: 0 (whole song), Extending a Run Overwrites Final Adapter, Goal Correction: train_window_frames Was the Gap, Lesson: Goal Change Invalidates Old Decisions, Same Run Name Auto-Resumes, Archive Old Output to Start Fresh, v1 Run (style-only captions, 3000/3000), Training Config Section

### Community 31 - "Inference Assets & LoRA Merge"
Cohesion: 0.25
Nodes (8): Assets Resolve via HF Hub Cache, Canonical LoRA Library <base>/loras/, Merging Two YuE2 LoRAs: Rank-Concat, YuE2 LoRA Loading Native in audio.cpp, Inference Asset Provenance Table, 720-Pass AR-Loss Replay, LoRA Inventory Consolidation, Pronunciation LoRA Tasks 14-20

### Community 32 - "L4 vs A100 Decision"
Cohesion: 0.38
Nodes (7): L4 vs A100 decision note, A100-SXM4-80GB, A100 measured ~4.3x faster than L4 (3.10 s/step), A100 vs L4 break-even compute-unit economics, NVIDIA L4 (24 GB, 121 TFLOPS bf16), Live status snapshot (A100 post-resume), A100 resume from step-250 checkpoint

### Community 33 - "Crash-Diagnose & Resume Skills"
Cohesion: 0.33
Nodes (7): command-handover Skill, Detached Hygiene Checklist, Foreground vs Detached Decision, crash-diagnose-and-resume Skill, Auto-Resume Policy, Fresh VM Restore Procedure, Stop Classification Table

### Community 34 - "prepare_pron_dataset.py"
Cohesion: 0.15
Nodes (21): concurrent_futures, build(), write_one(), choose_splits(), Config, discover_source_audio(), load_tanzil(), main() (+13 more)

### Community 35 - "monitor_loss.py"
Cohesion: 0.26
Nodes (14): Connection, connect_readonly(), history(), latest_step(), list_keys(), main(), metrics_at_step(), Namespace (+6 more)

### Community 36 - "Merge-to-main plan (BETA) — decisions locked"
Cohesion: 0.13
Nodes (14): agent_notes / current, Corrections the rewrite MUST make (found 2026-09-27 via local `gsutil`), Ground truth (verified 2026-09-27, git + local gsutil), Locked decisions (this session), Merge-to-main plan (BETA) — decisions locked, Phase 1.5 — the supersede rename, repo + GCS in lockstep — **DONE**, Phase 1 — doc rewrite ON `pron-lora-long` — **DONE (uncommitted)**, Phase 2 — skipped (knobs stays on its branch) (+6 more)

### Community 37 - "test_duration_cap.py"
Cohesion: 0.21
Nodes (9): runpy, _invoke_cli(), parametrize, Path, Unit tests for INFERENCE/duration_cap.py (GPU-free). The CLI `main()` is…, test_cli_default_quantile(), test_cli_empty_lyrics_uses_floor(), test_cli_explicit_quantile() (+1 more)

### Community 38 - "Repo Audit Backlog"
Cohesion: 0.50
Nodes (5): Repo audit: stale docs, drift & workflow backlog, No restore path for agent_notes/current.md, Flat inference out/ dir mixes unrelated runs, Staged scripts/ drifted from repo and self-perpetuates, Single status command for the whole job

### Community 40 - "Inference End-to-End Runbook"
Cohesion: 0.13
Nodes (16): audio.cpp Seeds and Sidecar Policy, audio.cpp Build: --model-set full Was the Cost, audiocpp_inference Staging Rule, Inference Backup Is a Race Against VM Death, T4 VRAM Governed by Attention Kernel, audio.cpp docs/models/yue2.md Is CLI Flag Source of Truth, One Shared Rented GPU, Prebuilt vs Source-Built audiocpp_cli (+8 more)

### Community 41 - "Arabic Pron LoRA Research Notes"
Cohesion: 0.83
Nodes (4): Future idea: Arabic pronunciation LoRA, Disjoint AR/NAR expert scoping, AR-only pronunciation adapter, MERT semantic-token representational ceiling

### Community 42 - "pron_knob_probe Script"
Cohesion: 0.83
Nodes (3): emit_sidecar(), opts_for(), pron_knob_probe.sh script

### Community 43 - "Merge Regenerate Script"
Cohesion: 1.00
Nodes (3): fetch(), regenerate.sh script, sha256_of()

### Community 44 - "Rank / EMA / COT Rationale"
Cohesion: 0.67
Nodes (3): model_kwargs.cot: off, Rank 32 LoRA + EMA 0.999, Rank, EMA, and cot Quality Rationale

### Community 45 - "TensorBoard log_dir"
Cohesion: 0.67
Nodes (3): log_config Dead Key, log_dir TensorBoard Path, TensorBoard log_dir Writes to Subfolder

### Community 59 - "graphify.js"
Cohesion: 0.40
Nodes (3): IMPORTANT: keep the reminder string free of backticks and $(...) constructs., ref_fs, ref_path

### Community 61 - "Working with the agent — experience checklist"
Cohesion: 0.25
Nodes (7): 1. The gut read, 2. Score the experience (1 = bad, 5 = great), 3. Pitfalls I hit (tick what's true), 4. Moments, 5. The one thing, 6. Hand this to the agent (copy + fill), Working with the agent — experience checklist

### Community 62 - "PRON LoRA LONG — build & multi-day training plan (`quran_long_aya_r8`)"
Cohesion: 0.06
Nodes (33): Checkpoint-eval on a second (T4) VM — while training runs, Commands that matter, Docs, First GPU session only (kickstart; obsolete once a checkpoint exists), Long-aya Quran pronunciation LoRA — runbook (canonical), 1. Objective, 2. Locked decisions, 3.1 Selection (from `selection_report.json`) (+25 more)

### Community 63 - "Training analysis — `quran_long_aya_r8_s10` (long-aya Quran pronunciation LoRA, 10% subsample)"
Cohesion: 0.29
Nodes (6): Caveats, Loss trend (per 810-step decile), Next steps, Observations / flags, Run at a glance, Training analysis — `quran_long_aya_r8_s10` (long-aya Quran pronunciation LoRA, 10% subsample)

### Community 71 - "graphify.serve MCP server"
Cohesion: 0.67
Nodes (3): graphify-out/graph.json, graphify-out/.graphify_python VM-specific interpreter, graphify.serve MCP server

## Knowledge Gaps
- **132 isolated node(s):** `$schema`, `plugin`, `pron_alpha_sweep.sh script`, `pron_fine_sweep.sh script`, `run_one.sh script` (+127 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 351 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **25 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Operations Docs Runbook Index` connect `Operations Docs Runbook Index` to `L4 vs A100 Decision`, `Repo Audit Backlog`, `Arabic Pron LoRA Research Notes`, `A/B blind evaluation packaging`, `YuE2 Findings & Docs`, `audiocpp Build Docs`, `Pron LoRA Training Run`, `Working with the agent — experience checklist`?**
  _High betweenness centrality (0.116) - this node is a cross-community bridge._
- **Why does `AR-only pronunciation LoRA runbook` connect `Pron LoRA Training Run` to `GCS Backup Engine`, `Operations Docs Runbook Index`?**
  _High betweenness centrality (0.054) - this node is a cross-community bridge._
- **Why does `Inference End-to-End Runbook` connect `Inference End-to-End Runbook` to `GCS Backup Engine`, `Project Overview`, `Observability Sources`, `Inference Assets & LoRA Merge`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **What connects `$schema`, `plugin`, `pron_alpha_sweep.sh script` to the rest of the system?**
  _132 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `generate.py` be split into smaller, more focused modules?**
  _Cohesion score 0.10025062656641603 - nodes in this community are weakly interconnected._
- **Should `GCS Backup Tests` be split into smaller, more focused modules?**
  _Cohesion score 0.1025974025974026 - nodes in this community are weakly interconnected._
- **Should `pathlib` be split into smaller, more focused modules?**
  _Cohesion score 0.07653061224489796 - nodes in this community are weakly interconnected._