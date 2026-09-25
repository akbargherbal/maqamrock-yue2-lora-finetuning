# Graph Report - maqamrock-yue2-lora-finetuning  (2026-09-25)

## Corpus Check
- 112 files · ~176,146 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 1, .ini 1, .log 1)

## Summary
- 720 nodes · 1461 edges · 23 communities (21 shown, 2 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 73 edges (avg confidence: 0.79)
- Token cost: 26,000 input · 9,000 output

## Community Hubs (Navigation)
- Operations Runbooks & Handover
- Inference CLI (generate.py)
- Project Docs & Decisions
- Backup Tests
- Merge & Replay Tests
- Dataset & Tooling Scripts
- Inference CLI Tests
- Offline AR-Loss Replay & Sweeps
- LoRA Merge Pipeline
- Inference & Skills Docs
- Docs Reconciler Scripts
- GPU Build & Reconciler Docs
- Training Telemetry Charts
- GCS Backup Engine
- Validation Tests
- Colab Bootstrap Setup
- Plot Generation
- Suno Conversion Tests
- Loss Monitor
- v2 Training Charts
- Graphify OpenCode Plugin
- GitHub Auth Script
- Pron Fine Sweep Script

## God Nodes (most connected - your core abstractions)
1. `FakeGsutil` - 35 edges
2. `DECISIONS.md — Durable Decisions & Insights` - 32 edges
3. `_patch()` - 31 edges
4. `_invoke()` - 22 edges
5. `PROGRESS.md — Milestone Trail` - 18 edges
6. `akbar_arabic_rock_lora Training Config` - 18 edges
7. `main()` - 17 edges
8. `check()` - 16 edges
9. `resolve_songs()` - 16 edges
10. `Inference runbook: audiocpp_cli + YuE2 GGUF + LoRA` - 16 edges

## Surprising Connections (you probably didn't know these)
- `Lower loss/ar_ce Is Mechanism, Not Quality` --semantically_similar_to--> `loss/ar_kl Unbroken Rise as First Lever for v3`  [INFERRED] [semantically similar]
  TRAINING_ANALYSIS/ANALYSIS.md → DECISIONS.md
- `pron Run A100 Data/CPU-Bound` --semantically_similar_to--> `Whole-Song L4 vs A100 Measured (~4.3x)`  [INFERRED] [semantically similar]
  TRAINING_ANALYSIS/pron_lora_ar_only_r8/ANALYSIS.md → DECISIONS.md
- `v1 to v2 Supersession` --semantically_similar_to--> `Retraction: LoRA Conversion Required`  [INFERRED] [semantically similar]
  verification.md → docs/yue2-gguf-lora-findings.md
- `Backup Responsibility (GCS mirroring)` --conceptually_related_to--> `Backup to GCS, Verify, and Restore Runbook`  [INFERRED]
  AGENTS.md → docs/BACKUP_RESTORE.md
- `INFERENCE/duration_cap.py auto cap` --references--> `Duration Cap Formula`  [INFERRED]
  skills/inference-batch-run/SKILL.md → docs/text_to_duration_formula.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Lyric-Conditioned v2 Dataset & Training Pipeline** — decisions_lyric_caption_format, readme_yue2_dataset, config_akbar_arabic_rock_lora_config, training_analysis_analysis_document, decisions_v2_lyric_fix_result, inference_yue2_eval_heldout_heldout_eval_report_document [INFERRED 0.85]
- **AR-Only Pronunciation LoRA Train-to-Merge-to-Sweep Workflow** — config_pron_lora_ar_only_config, config_pron_lora_ar_only_smoke_config, training_analysis_pron_lora_ar_only_r8_analysis_document, pron_fine_sweep_input_key_alpha_sweep, pron_fine_sweep_input_key_open_after_listening_document, decisions_lora_merge_rank_concat [INFERRED 0.85]
- **Ephemeral Colab to GCS Persistence & Resume Flow** — docs_backup_restore_document, readme_colab_ephemeral, agents_backup_responsibility, decisions_auto_resume, decisions_cross_vm_resume [INFERRED 0.85]
- **AR-only pronunciation LoRA pipeline (verify -> train -> merge -> sweep)** — docs_pron_lora_verification, docs_pron_lora, docs_pron_lora_merge, docs_pron_lora_sweep [EXTRACTED 1.00]
- **audiocpp inference pipeline (setup -> run/launch -> cap -> convert)** — docs_inference, inference_run_one, inference_generate, inference_duration_cap, converter_convert_aitoolkit_yue2_lora_py [EXTRACTED 1.00]
- **Training observability & backup stack (sidecars, metrics, restore)** — docs_start, docs_monitor, docs_pause_resume, backup_to_gcp, gpu_logger, monitor_loss [EXTRACTED 1.00]
- **Per-GPU CUDA Build Workflow** — docs_audiocpp_gpu_arch_builds, docs_audiocpp_gpu_arch_builds_cross_compilation, docs_audiocpp_gpu_arch_builds_cuda_arch_flag, docs_audiocpp_gpu_arch_builds_sass_vs_ptx, docs_audiocpp_gpu_arch_builds_per_arch_gcs_staging, docs_audiocpp_gpu_arch_builds_build_verification, docs_audiocpp_gpu_arch_builds_t4_sm75_worked_example [EXTRACTED 1.00]
- **Pronunciation Alpha Sweep Results** — results_pron_sweep_readme, results_pron_fine_sweep_readme, results_pron_sweep_readme_pron_alpha_sweep, results_pron_fine_sweep_readme_fine_alpha_sweep, results_pron_fine_sweep_readme_alpha, results_pron_sweep_readme_short_collapse [EXTRACTED 1.00]
- **Docs Reconciliation Workflow** — skills_docs_reconciler_skill, skills_docs_reconciler_scripts_extract_claims, skills_docs_reconciler_scripts_verify_claims, skills_docs_reconciler_skill_human_checkpoint, skills_docs_reconciler_references_example_drift_report, skills_docs_reconciler_references_unverifiable_token_list [EXTRACTED 1.00]
- **hyper_training_analysis_akbar_run_observability** — training_analysis_01_loss_curves_chart, training_analysis_02_loss_main_chart, training_analysis_03_learning_rate_chart, training_analysis_04_throughput_chart, training_analysis_05_gpu_usage_chart, training_analysis_02_loss_main_akbar_arabic_rock_lora_run [INFERRED 0.85]
- **pron_lora_ar_only_r8_training_run** — concept_pron_lora_ar_only_r8_run, training_analysis_pron_lora_ar_only_r8_01_loss_curves, training_analysis_pron_lora_ar_only_r8_02_loss_main, training_analysis_pron_lora_ar_only_r8_03_learning_rate, training_analysis_pron_lora_ar_only_r8_04_throughput, training_analysis_pron_lora_ar_only_r8_05_gpu_usage [EXTRACTED 1.00]
- **pron_lora_ar_only_r8_loss_terms** — concept_loss_loss_metric, concept_loss_ar_ce_metric, concept_loss_ar_kl_metric, concept_additional_model_loss_metric [EXTRACTED 1.00]
- **he_loss_metric_panel** — training_analysis_v1_nolyrics_archived_01_loss_curves, concept_loss_loss, concept_loss_ar_ce, concept_loss_ar_kl, concept_additional_model_loss [EXTRACTED 1.00]
- **he_run_observability** — training_analysis_v1_nolyrics_archived_01_loss_curves, training_analysis_v1_nolyrics_archived_04_throughput, training_analysis_v1_nolyrics_archived_05_gpu_usage, concept_akbar_arabic_rock_lora_run, concept_sample_eval_interval [INFERRED 0.85]

## Communities (23 total, 2 thin omitted)

### Community 0 - "Operations Runbooks & Handover"
Cohesion: 0.06
Nodes (56): Human-terminal handover gotchas, Detached launch pattern (setsid nohup ... & disown), Training runs foreground on purpose so Ctrl+C works, Every detached command ships with stop + resume, Env vars staged by the launching notebook, One shared GPU (training + inference), Detached jobs inherit SIGINT ignored, vscode.dev clipboard is glitchy -> current.md handoff (+48 more)

### Community 1 - "Inference CLI (generate.py)"
Cohesion: 0.10
Nodes (56): asset_fingerprint(), build_parser(), build_tracks(), _cap_settings(), check(), draw_seeds(), fail(), fmt_hms() (+48 more)

### Community 2 - "Project Docs & Decisions"
Cohesion: 0.09
Nodes (56): AGENTS.md — Agent Operating Contract, Backup Responsibility (GCS mirroring), Command Handover Policy, Training Observability Surfaces, akbar_arabic_rock_lora Training Config, ar_kl_weight 0.2, cot: off (Skip SheetSage2), sample.duration: 360 Rationale (+48 more)

### Community 3 - "Backup Tests"
Cohesion: 0.10
Nodes (44): _args(), _close_log_handlers(), _dirs(), FakeGsutil, _invoke(), lg(), _patch(), fixture (+36 more)

### Community 4 - "Merge & Replay Tests"
Cohesion: 0.05
Nodes (31): importlib_util, pytest, safetensors_torch, bak(), dur(), gen(), _load_module(), lyrics_ar() (+23 more)

### Community 5 - "Dataset & Tooling Scripts"
Cohesion: 0.07
Nodes (46): argparse, csv, main(), poll(), gpu_logger.py -------------- AI Toolkit logs no GPU…, arabic_letters(), duration_cap(), main() (+38 more)

### Community 6 - "Inference CLI Tests"
Cohesion: 0.05
Nodes (24): hashlib, _make_run(), parametrize, Unit tests for INFERENCE/generate.py (GPU-free)., Minimal stand-in for subprocess.CompletedProcess., _Run, _songs_json(), _stub_assets() (+16 more)

### Community 7 - "Offline AR-Loss Replay & Sweeps"
Cohesion: 0.09
Nodes (38): dataclasses, attach_adapter(), build_arg_parser(), build_model(), _import_ai_toolkit(), ItemResult, list_val_pairs(), load_config_sections() (+30 more)

### Community 8 - "LoRA Merge Pipeline"
Cohesion: 0.11
Nodes (33): converter/convert_aitoolkit_yue2_lora.py, Future idea: Arabic pronunciation LoRA, Disjoint AR/NAR expert scoping, AR-only pronunciation adapter, MERT semantic-token representational ceiling, Offline merge: v2 style + pron AR-only LoRA, alpha=0 merge reproduces v2 byte-identically, LoRA additivity: (alpha/rank)*(B@A) scaling (+25 more)

### Community 9 - "Inference & Skills Docs"
Cohesion: 0.10
Nodes (34): Text Length to Audio Duration Cap (yue2_dataset), Asymmetric Loss Favors a High Quantile, Centre Fit (Not a Cap), Duration Cap Formula, Arabic Letter Counting Rule, Quantile (Pinball-loss) Regression, Running a LoRA on the Yue2-3B GGUF Model: Findings, AR / NAR Stages (+26 more)

### Community 10 - "Docs Reconciler Scripts"
Cohesion: 0.13
Nodes (28): collections, datetime, fnmatch, json, os, re, is_excluded(), iter_code() (+20 more)

### Community 11 - "GPU Build & Reconciler Docs"
Cohesion: 0.11
Nodes (31): Building audiocpp_cli for a Specific GPU from a CPU-only Colab Runtime, scripts/build_linux.sh, Build Verification Procedure, ccache Build Caching, Compute Capabilities for T4 / A100 / L4, nvcc Cross-Compilation on a CPU Host, --cuda-arch Flag, Per-arch GCS Staging Convention (+23 more)

### Community 12 - "Training Telemetry Charts"
Cohesion: 0.13
Nodes (27): Additional Model Loss, additional_model_loss metric, akbar_arabic_rock_lora Training Run (3000 steps), checkpoint save interval every 1525 steps, gpu_logger.py (10s GPU sampling script, data source), GPU telemetry (utilization, memory, temperature, power), learning rate schedule (constant 1e-4), Autoregressive Cross-Entropy Loss (loss/ar_ce) (+19 more)

### Community 13 - "GCS Backup Engine"
Cohesion: 0.16
Nodes (24): ensure_manifest(), main(), parse_args(), parse_extra_specs(), parse_watch_specs(), Namespace, Path, Same shape as TRAINING_TARGETS, but for an arbitrary run name. `--run-name`… (+16 more)

### Community 14 - "Validation Tests"
Cohesion: 0.13
Nodes (17): runpy, sys, Path, _repo(), test_extract_scope_and_kinds(), test_ignore_file_suppresses_missing(), test_include_all_scans_frozen(), test_report_render() (+9 more)

### Community 15 - "Colab Bootstrap Setup"
Cohesion: 0.12
Nodes (5): confirm_hf(), setup.sh script, start_job(), usage(), ext_root_secrets_env

### Community 16 - "Plot Generation"
Cohesion: 0.20
Nodes (18): matplotlib, matplotlib_pyplot, ndarray, numpy, main(), parse_args(), plot_gpu(), plot_loss_curves() (+10 more)

### Community 17 - "Suno Conversion Tests"
Cohesion: 0.21
Nodes (13): _convert(), parametrize, Unit tests for INFERENCE/suno_to_songs.py (GPU-free)., test_bad_manifests(), test_defaults_and_file_mode(), test_dry_run_writes_nothing_and_determinism(), test_keep_both_and_filters(), test_keep_first() (+5 more)

### Community 18 - "Loss Monitor"
Cohesion: 0.23
Nodes (15): Connection, connect_readonly(), history(), latest_step(), list_keys(), main(), metrics_at_step(), Namespace (+7 more)

### Community 19 - "v2 Training Charts"
Cohesion: 0.17
Nodes (16): additional_model_loss component declining from ~5.8 to ~3.9, loss/ar_ce component (autoregressive cross-entropy) declining from ~5.8 to ~3.6, loss/ar_kl component rising from 0 to ~1.5 (KL divergence term), Per-step loss curves 2x2 panel (loss/loss, loss/ar_ce, loss/ar_kl, additional_model_loss vs step), Per-step training loss metric (raw + 25-step mean), akbar_arabic_rock_lora training run, Primary loss/loss curve vs step with 50-step mean and trend line (-2.14e-04/step), loss_log.db SQLite metrics store (data source for loss curves) (+8 more)

### Community 20 - "Graphify OpenCode Plugin"
Cohesion: 0.40
Nodes (3): IMPORTANT: keep the reminder string free of backticks and $(...) constructs., ref_fs, ref_path

## Knowledge Gaps
- **25 isolated node(s):** `pron_alpha_sweep.sh script`, `pron_fine_sweep.sh script`, `run_one.sh script`, `github_auth.sh script`, `pron_lora_ar_only_smoke Config (10-step smoke)` (+20 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 184 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `inference-batch-run Skill` connect `Inference & Skills Docs` to `Operations Runbooks & Handover`, `Inference CLI (generate.py)`, `GPU Build & Reconciler Docs`?**
  _High betweenness centrality (0.088) - this node is a cross-community bridge._
- **Why does `Operations docs index` connect `Operations Runbooks & Handover` to `LoRA Merge Pipeline`?**
  _High betweenness centrality (0.049) - this node is a cross-community bridge._
- **Why does `Inference runbook: audiocpp_cli + YuE2 GGUF + LoRA` connect `Operations Runbooks & Handover` to `LoRA Merge Pipeline`, `Inference CLI (generate.py)`, `Dataset & Tooling Scripts`, `GCS Backup Engine`?**
  _High betweenness centrality (0.048) - this node is a cross-community bridge._
- **What connects `pron_alpha_sweep.sh script`, `pron_fine_sweep.sh script`, `run_one.sh script` to the rest of the system?**
  _25 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Operations Runbooks & Handover` be split into smaller, more focused modules?**
  _Cohesion score 0.05747126436781609 - nodes in this community are weakly interconnected._
- **Should `Inference CLI (generate.py)` be split into smaller, more focused modules?**
  _Cohesion score 0.09899749373433583 - nodes in this community are weakly interconnected._
- **Should `Project Docs & Decisions` be split into smaller, more focused modules?**
  _Cohesion score 0.08896103896103896 - nodes in this community are weakly interconnected._