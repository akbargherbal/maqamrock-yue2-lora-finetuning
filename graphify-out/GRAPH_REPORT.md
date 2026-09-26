# Graph Report - maqamrock-yue2-lora-finetuning  (2026-09-26)

## Corpus Check
- 143 files · ~193,019 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 923 nodes · 1633 edges · 62 communities (46 shown, 16 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 60 edges (avg confidence: 0.79)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Inference CLI (generate.py)
- GCS Backup Tests
- Merge & Replay Tests
- Docs Reconciler Scripts
- Inference CLI Tests
- Graphify & Docs Reconciliation
- GPU Logger & Runtime Imports
- Offline AR-Loss Replay
- Dataset Build & Suno Conversion
- GCS Backup Engine
- AB Evaluation Packaging
- A/B Blind Evaluation Design
- Training Loss Curves
- LoRA Merge Pipeline
- YuE2 Findings & Docs
- AB Evaluation Tests
- Colab Bootstrap (setup.sh)
- audiocpp Build Docs
- Training Charts
- Inference Runbook (audio.cpp)
- Suno Conversion Tests
- Held-Out Eval & Dataset v2
- Training loss/loss Metric
- Agent Contract & Command Handover
- Loss Monitor
- Operations Docs & Runbooks
- Pron LoRA Training Run
- LoRA Inventory
- Observability Sources
- Training Configs
- v1 Run Lessons
- Inference Assets & LoRA Merge
- L4 vs A100 Decision
- Crash-Diagnose & Resume Skills
- maqam_lyric_swap Results
- pron_knob_probe Results
- Merge Candidates Results
- Project Overview & Docs
- Repo Audit Backlog
- pron_ckpt_sweep Results
- T4 Re-Render
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
- ref_fs Helper
- ref_path Helper
- pathlib Path

## God Nodes (most connected - your core abstractions)
1. `FakeGsutil` - 35 edges
2. `_patch()` - 31 edges
3. `_invoke()` - 22 edges
4. `Repo knowledge graph (graphify)` - 21 edges
5. `Operations Docs Runbook Index` - 19 edges
6. `main()` - 17 edges
7. `check()` - 16 edges
8. `resolve_songs()` - 16 edges
9. `make()` - 16 edges
10. `run_batch()` - 15 edges

## Surprising Connections (you probably didn't know these)
- `A/B blind evaluation packaging` --semantically_similar_to--> `Blinded Listening Review`  [INFERRED] [semantically similar]
  skills/ab-blind-eval/SKILL.md → docs/PRON_LORA_SWEEP.md
- `Doc/paper semantic extraction assistant skill` --semantically_similar_to--> `docs-reconciler skill`  [INFERRED] [semantically similar]
  docs/GRAPHIFY.md → RECONCILIATION_LOG.md
- `v1 to v2 Supersession` --semantically_similar_to--> `Retraction: LoRA Conversion Required`  [INFERRED] [semantically similar]
  verification.md → docs/yue2-gguf-lora-findings.md
- `README Observability Section` --semantically_similar_to--> `Training Observability Sources`  [INFERRED] [semantically similar]
  README.md → AGENTS.md
- `graphify update .` --semantically_similar_to--> `Drift Reconciliation Pass (live docs)`  [INFERRED] [semantically similar]
  docs/GRAPHIFY.md → RECONCILIATION_LOG.md

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
- **hyper_training_analysis_akbar_run_observability** — training_analysis_01_loss_curves_chart, training_analysis_02_loss_main_chart, training_analysis_03_learning_rate_chart, training_analysis_04_throughput_chart, training_analysis_05_gpu_usage_chart, training_analysis_02_loss_main_akbar_arabic_rock_lora_run [INFERRED 0.85]
- **he_run_observability** — training_analysis_v1_nolyrics_archived_01_loss_curves, training_analysis_v1_nolyrics_archived_04_throughput, training_analysis_v1_nolyrics_archived_05_gpu_usage, concept_akbar_arabic_rock_lora_run, concept_sample_eval_interval [INFERRED 0.85]
- **Blinded Listening Evaluation Rounds** — docs_pron_lora_sweep_alpha_sweep, results_pron_fine_sweep_readme_fine_sweep, results_pron_ckpt_sweep_readme_ckpt_sweep, results_maqam_lyric_swap_readme_lyric_swap, results_pron_knob_probe_readme_knob_probe, skills_ab_blind_eval_skill_a_b_blind_evaluation_packaging [INFERRED 0.85]
- **v2 + pron LoRA Merge Pipeline** — docs_pron_lora_merge_offline_merge, docs_pron_lora_merge_scaling_convention, docs_pron_lora_merge_rank_concatenation, results_pron_production_merge_readme_production_merge, docs_lora_inventory_lora_library [INFERRED 0.85]
- **graphify output artifact set** — docs_graphify_repo_knowledge_graph_graphify, docs_graphify_graph_report, docs_graphify_graph_json, docs_graphify_graph_html, docs_graphify_manifest_json, docs_graphify_cache [EXTRACTED 1.00]
- **Docs reconciliation workflow** — reconciliation_log_docs_reconciler, reconciliation_log_drift_reconciliation, reconciliation_log_unverifiable_allowlist_curation, reconciliation_log_source_of_truth [INFERRED 0.85]
- **External token families in unverifiable allowlist** — skills_docs_reconciler_references_unverifiable_ai_toolkit_clone, skills_docs_reconciler_references_unverifiable_audiocpp_clone, skills_docs_reconciler_references_unverifiable_runtime_artifacts, skills_docs_reconciler_references_unverifiable_external_cli_flags [EXTRACTED 1.00]

## Communities (62 total, 16 thin omitted)

### Community 0 - "Inference CLI (generate.py)"
Cohesion: 0.08
Nodes (63): argparse, arabic_letters(), duration_cap(), main(), Dynamic YuE2 `semantic_max_tokens` cap derived from a lyrics file. Canonical…, Return (duration_s, duration_rounded_10s, token_cap, quantile)., asset_fingerprint(), build_parser() (+55 more)

### Community 1 - "GCS Backup Tests"
Cohesion: 0.10
Nodes (44): _args(), _close_log_handlers(), _dirs(), FakeGsutil, _invoke(), lg(), _patch(), fixture (+36 more)

### Community 2 - "Merge & Replay Tests"
Cohesion: 0.06
Nodes (29): importlib_util, pytest, bak(), dur(), gen(), _load_module(), lyrics_ar(), manifest_path() (+21 more)

### Community 3 - "Docs Reconciler Scripts"
Cohesion: 0.08
Nodes (42): collections, datetime, fnmatch, Path, re, Example Drift Report, Missing Path Findings, Unverifiable Counts (+34 more)

### Community 4 - "Inference CLI Tests"
Cohesion: 0.05
Nodes (22): _make_run(), parametrize, Unit tests for INFERENCE/generate.py (GPU-free)., Minimal stand-in for subprocess.CompletedProcess., _Run, _songs_json(), _stub_assets(), test_cap_parity_with_duration_cap_cli() (+14 more)

### Community 5 - "Graphify & Docs Reconciliation"
Cohesion: 0.05
Nodes (44): Graph is branch-specific; dangling-endpoint edges gap, graphify-out/cache/ per-file extraction cache, Caveats, Enable it in another agent / environment, graphify explain, Extraction cache keyed by version and prompt, graphify-out/graph.html, graphify-out/graph.json (+36 more)

### Community 6 - "GPU Logger & Runtime Imports"
Cohesion: 0.08
Nodes (31): csv, main(), poll(), gpu_logger.py -------------- AI Toolkit logs no GPU…, main(), plan(), Path, Cross-maqam lyric swap: one maqam's caption+tag with the other's held-out… (+23 more)

### Community 7 - "Offline AR-Loss Replay"
Cohesion: 0.10
Nodes (34): dataclasses, attach_adapter(), build_arg_parser(), build_model(), _import_ai_toolkit(), ItemResult, list_val_pairs(), load_config_sections() (+26 more)

### Community 8 - "Dataset Build & Suno Conversion"
Cohesion: 0.11
Nodes (32): build_parser(), build_report(), build_style(), canonical_tag(), clean_lyrics(), collect_entries(), dedup(), extract_maqam() (+24 more)

### Community 9 - "GCS Backup Engine"
Cohesion: 0.11
Nodes (32): ensure_manifest(), main(), parse_args(), parse_extra_specs(), parse_watch_specs(), Namespace, Path, Same shape as TRAINING_TARGETS, but for an arbitrary run name. `--run-name`… (+24 more)

### Community 10 - "AB Evaluation Packaging"
Cohesion: 0.10
Nodes (28): No Adapter Is Best Before the Blind Listen; alpha <= 0.5, Blinded A/B Listening Package, EVAL.txt / KEYS.txt Public-Secret Split, ab-blind-eval Skill, build_parser(), _discover(), _ffmpeg_convert(), _group_pairs() (+20 more)

### Community 11 - "A/B Blind Evaluation Design"
Cohesion: 0.09
Nodes (27): Generated Listening Packages Live in GCS, Blinded A/B audio evaluation packaging, Conventions, Input layout, Usage, What it produces, Alpha Capped at 0.5, LoRA Library (+19 more)

### Community 12 - "Training Loss Curves"
Cohesion: 0.13
Nodes (27): Additional Model Loss, additional_model_loss metric, akbar_arabic_rock_lora Training Run (3000 steps), checkpoint save interval every 1525 steps, gpu_logger.py (10s GPU sampling script, data source), GPU telemetry (utilization, memory, temperature, power), learning rate schedule (constant 1e-4), Autoregressive Cross-Entropy Loss (loss/ar_ce) (+19 more)

### Community 13 - "LoRA Merge Pipeline"
Cohesion: 0.13
Nodes (26): hashlib, _ab(), build_metadata(), _check_alpha_keys(), main(), merge(), MergeError, _proj() (+18 more)

### Community 14 - "YuE2 Findings & Docs"
Cohesion: 0.16
Nodes (23): Text Length to Audio Duration Cap (yue2_dataset), Asymmetric Loss Favors a High Quantile, Centre Fit (Not a Cap), Duration Cap Formula, Arabic Letter Counting Rule, Quantile (Pinball-loss) Regression, Running a LoRA on the Yue2-3B GGUF Model: Findings, AR / NAR Stages (+15 more)

### Community 15 - "AB Evaluation Tests"
Cohesion: 0.16
Nodes (18): make(), Path, Unit tests for INFERENCE/prepare_ab_eval.py (GPU-free, ffmpeg-free). The audio…, rec_by_file(), test_bad_variant_name_errors(), test_categories_and_duplicate_stems_get_prefix(), test_category_filter(), test_dry_run_writes_nothing() (+10 more)

### Community 16 - "Colab Bootstrap (setup.sh)"
Cohesion: 0.12
Nodes (6): confirm_hf(), setup.sh script, start_job(), usage(), ext_root_secrets_env, Bootstrap Split --training / --inference

### Community 17 - "audiocpp Build Docs"
Cohesion: 0.19
Nodes (19): Building audiocpp_cli for a Specific GPU from a CPU-only Colab Runtime, scripts/build_linux.sh, Build Verification Procedure, ccache Build Caching, Compute Capabilities for T4 / A100 / L4, nvcc Cross-Compilation on a CPU Host, --cuda-arch Flag, Per-arch GCS Staging Convention (+11 more)

### Community 18 - "Training Charts"
Cohesion: 0.20
Nodes (18): matplotlib, matplotlib_pyplot, ndarray, numpy, main(), parse_args(), plot_gpu(), plot_loss_curves() (+10 more)

### Community 19 - "Inference Runbook (audio.cpp)"
Cohesion: 0.13
Nodes (16): audio.cpp Seeds and Sidecar Policy, audio.cpp Build: --model-set full Was the Cost, audiocpp_inference Staging Rule, Inference Backup Is a Race Against VM Death, T4 VRAM Governed by Attention Kernel, audio.cpp docs/models/yue2.md Is CLI Flag Source of Truth, One Shared Rented GPU, Prebuilt vs Source-Built audiocpp_cli (+8 more)

### Community 20 - "Suno Conversion Tests"
Cohesion: 0.21
Nodes (13): _convert(), parametrize, Unit tests for INFERENCE/suno_to_songs.py (GPU-free)., test_bad_manifests(), test_defaults_and_file_mode(), test_dry_run_writes_nothing_and_determinism(), test_keep_both_and_filters(), test_keep_first() (+5 more)

### Community 21 - "Held-Out Eval & Dataset v2"
Cohesion: 0.13
Nodes (16): sample.samples Held-Out Prompts, duration 360, v2 Caption Lyric Format (binding), Dataset Verification: 267 Pairs, Held-Out Eval Set Contamination, sample.duration 360 Rationale and Cost, v2 Finished: Lyric Fix Worked; ar_kl Drift, Byte-Identity Proof (267/267), Step 5 Held-Out Checks (+8 more)

### Community 22 - "Training loss/loss Metric"
Cohesion: 0.17
Nodes (16): additional_model_loss component declining from ~5.8 to ~3.9, loss/ar_ce component (autoregressive cross-entropy) declining from ~5.8 to ~3.6, loss/ar_kl component rising from 0 to ~1.5 (KL divergence term), Per-step loss curves 2x2 panel (loss/loss, loss/ar_ce, loss/ar_kl, additional_model_loss vs step), Per-step training loss metric (raw + 25-step mean), akbar_arabic_rock_lora training run, Primary loss/loss curve vs step with 50-step mean and trend line (-2.14e-04/step), loss_log.db SQLite metrics store (data source for loss curves) (+8 more)

### Community 23 - "Agent Contract & Command Handover"
Cohesion: 0.16
Nodes (15): Agent Operating Contract, Auto-Resume Exception Policy, Backup Responsibility, Colab Is Ephemeral, command-handover Skill, agent_notes/current.md Handoff Surface, Graphify Knowledge Graph Usage, Agent Training-Control Policy (+7 more)

### Community 24 - "Loss Monitor"
Cohesion: 0.26
Nodes (14): Connection, connect_readonly(), history(), latest_step(), list_keys(), main(), metrics_at_step(), Namespace (+6 more)

### Community 25 - "Operations Docs & Runbooks"
Cohesion: 0.17
Nodes (13): Final backup & push checklist, GCS not append-only for the un-suffixed final adapter, Check how training is going, gpu_usage.csv hardware log, loss_log.db per-step metrics surface, Pause for the night, resume next session, ai-toolkit auto-resume from newest checkpoint, ai-toolkit Auto-Resume Rule (+5 more)

### Community 26 - "Pron LoRA Training Run"
Cohesion: 0.33
Nodes (11): L4 handoff after Task 14c, pron-lora-ar-only branch, No _000006100 checkpoint; post-loop save is step 6100, AR-only pronunciation LoRA runbook, pron_lora_ar_only_r8 training run, network_kwargs.ignore_if_contains AR/NAR scoping, Blank trigger_word no-op, AR-only pronunciation LoRA source verification (+3 more)

### Community 27 - "LoRA Inventory"
Cohesion: 0.22
Nodes (9): Archived — α>0.5 (out of scope), Caveats, Counts, Experimental adapters (in scope, α≤0.5 — NOT the library), Fused source adapters (`loras/source/`), How to stage an adapter, Library adapters (`loras/`, audio.cpp-loadable), Library location (+1 more)

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

### Community 34 - "maqam_lyric_swap Results"
Cohesion: 0.33
Nodes (5): Blinded review, Configs, Groups, maqam_lyric_swap — cross-maqam lyric swap (Hijaz + Kurd), Tracks

### Community 35 - "pron_knob_probe Results"
Cohesion: 0.33
Nodes (5): Blinded review, Configs (one knob vs the anchor defaults), pron_knob_probe — request-option knob probe at ckpt 3050, alpha 0.5, Resources per generation, Tracks

### Community 36 - "Merge Candidates Results"
Cohesion: 0.33
Nodes (5): Large binaries are not committed, Non-obvious: file-level sha256 is not reproducible (tensor digest is), pron_production_merge — v2 + pron merge candidates (checkpoint 3050), Sidecars, Verification performed (2026-09-25, CPU)

### Community 37 - "Project Overview & Docs"
Cohesion: 0.40
Nodes (5): Env Vars Staged by Launching Notebook, README Docs Index, Project Overview, Repo Layout, Running on Colab Section

### Community 38 - "Repo Audit Backlog"
Cohesion: 0.50
Nodes (5): Repo audit: stale docs, drift & workflow backlog, No restore path for agent_notes/current.md, Flat inference out/ dir mixes unrelated runs, Staged scripts/ drifted from repo and self-perpetuates, Single status command for the whole job

### Community 39 - "pron_ckpt_sweep Results"
Cohesion: 0.40
Nodes (4): Blinded review, Configs, pron_ckpt_sweep — pron checkpoints 1525 vs 4575 at alpha 0.5 (Hijaz + Kurd), Tracks

### Community 40 - "T4 Re-Render"
Cohesion: 0.40
Nodes (4): Caveats, Result — the outputs differ, T4 re-render of the two lost Kurd WAVs (2026-09-25), Where

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

## Knowledge Gaps
- **107 isolated node(s):** `run_one.sh script`, `Input layout`, `Usage`, `What it produces`, `Archived — α>0.5 (out of scope)` (+102 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 319 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **16 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Operations Docs Runbook Index` connect `Operations Docs & Runbooks` to `L4 vs A100 Decision`, `Repo Audit Backlog`, `Arabic Pron LoRA Research Notes`, `A/B Blind Evaluation Design`, `YuE2 Findings & Docs`, `audiocpp Build Docs`, `Pron LoRA Training Run`?**
  _High betweenness centrality (0.172) - this node is a cross-community bridge._
- **Why does `Repo knowledge graph (graphify)` connect `Graphify & Docs Reconciliation` to `Operations Docs & Runbooks`, `Observability Sources`, `Agent Contract & Command Handover`?**
  _High betweenness centrality (0.082) - this node is a cross-community bridge._
- **Why does `Inference End-to-End Runbook` connect `Inference Runbook (audio.cpp)` to `GCS Backup Engine`, `Observability Sources`, `Project Overview & Docs`, `Inference Assets & LoRA Merge`?**
  _High betweenness centrality (0.062) - this node is a cross-community bridge._
- **What connects `run_one.sh script`, `Input layout`, `Usage` to the rest of the system?**
  _107 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Inference CLI (generate.py)` be split into smaller, more focused modules?**
  _Cohesion score 0.08317307692307692 - nodes in this community are weakly interconnected._
- **Should `GCS Backup Tests` be split into smaller, more focused modules?**
  _Cohesion score 0.1025974025974026 - nodes in this community are weakly interconnected._
- **Should `Merge & Replay Tests` be split into smaller, more focused modules?**
  _Cohesion score 0.05580693815987934 - nodes in this community are weakly interconnected._