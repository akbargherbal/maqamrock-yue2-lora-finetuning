# Graph Report - maqamrock-yue2-lora-finetuning  (2026-09-26)

## Corpus Check
- 143 files · ~192,629 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 894 nodes · 1586 edges · 63 communities (46 shown, 17 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 58 edges (avg confidence: 0.79)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Inference CLI (generate.py)
- GCS Backup Tests
- Eval & Sweep Tests
- Inference CLI Tests
- Docs Reconciler Scripts
- Offline AR-Loss Replay
- Colab Bootstrap & Run Handoff
- Dataset Build & Suno Conversion
- AB Evaluation Packaging
- AB Blind Evaluation Design
- YuE2 Findings & Docs Index
- GCS Backup Engine
- Training Loss Curves
- LoRA Merge Pipeline
- Training Charts
- Merge Tests
- audiocpp_build Build Docs
- GPU Logging & Training Launch
- Inference Runbook (audio.cpp)
- Inference Sweep Entrypoints
- Suno Conversion Tests
- Pytest Conftest & Fixtures
- Training loss/loss Metric
- Agent Operating Contract
- Loss Monitor
- Observability Sources
- Held-Out Eval & Dataset v2
- v2 Run Lessons
- Graphify Knowledge Graph
- LoRA Inventory
- Training Configs
- Project Overview & Docs
- L4 vs A100 Decision
- Graphify Usage Docs
- Crash-Diagnose & Handover Skills
- Backup Mirror Targets
- maqam_lyric_swap Results
- pron_knob_probe Results
- Merge Candidates Results
- Repo Audit Backlog
- pron_ckpt_sweep Results
- T4 Re-Render
- pron_knob_probe Script
- Merge Regenerate Script
- Rank / EMA / COT Rationale
- TensorBoard log_dir
- GitHub Auth Script
- Trigger Word
- pron_alpha_sweep Script
- pron_fine_sweep Script
- CLI Namespace
- Latent Cache Config
- Dataset Folder Path
- Batch Verdict Criteria
- Dataset Naming
- Diffusion Trainer Type
- Whole-Song L4 vs A100
- Run Name Reuse
- Token-Count Check
- Torch Stack Pin
- ArgumentParser
- ref_fs Helper
- ref_path Helper

## God Nodes (most connected - your core abstractions)
1. `FakeGsutil` - 35 edges
2. `_patch()` - 31 edges
3. `_invoke()` - 22 edges
4. `main()` - 17 edges
5. `check()` - 16 edges
6. `resolve_songs()` - 16 edges
7. `make()` - 16 edges
8. `run_batch()` - 15 edges
9. `setup_ab_evaluation()` - 13 edges
10. `Inference End-to-End Runbook` - 13 edges

## Surprising Connections (you probably didn't know these)
- `A/B blind evaluation packaging` --semantically_similar_to--> `Blinded Listening Review`  [INFERRED] [semantically similar]
  skills/ab-blind-eval/SKILL.md → docs/PRON_LORA_SWEEP.md
- `docs-reconciler Skill` --semantically_similar_to--> `graphify Repo Knowledge Graph`  [INFERRED] [semantically similar]
  RECONCILIATION_LOG.md → docs/GRAPHIFY.md
- `v1 to v2 Supersession` --semantically_similar_to--> `Retraction: LoRA Conversion Required`  [INFERRED] [semantically similar]
  verification.md → docs/yue2-gguf-lora-findings.md
- `README Observability Section` --semantically_similar_to--> `Training Observability Sources`  [INFERRED] [semantically similar]
  README.md → AGENTS.md
- `Run YAML Is Canonical Lyrics` --references--> `akbar_arabic_rock_lora Training Config`  [EXTRACTED]
  INFERENCE/yue2_eval_heldout/heldout_eval_report.md → config/akbar_arabic_rock_lora.yml

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **he_loss_metric_panel** — training_analysis_v1_nolyrics_archived_01_loss_curves, concept_loss_loss, concept_loss_ar_ce, concept_loss_ar_kl, concept_additional_model_loss [EXTRACTED 1.00]
- **Docs Reconciliation Workflow** — skills_docs_reconciler_skill, skills_docs_reconciler_scripts_extract_claims, skills_docs_reconciler_scripts_verify_claims, skills_docs_reconciler_skill_human_checkpoint, skills_docs_reconciler_references_example_drift_report [EXTRACTED 1.00]
- **Per-GPU CUDA Build Workflow** — docs_audiocpp_gpu_arch_builds, docs_audiocpp_gpu_arch_builds_cross_compilation, docs_audiocpp_gpu_arch_builds_cuda_arch_flag, docs_audiocpp_gpu_arch_builds_sass_vs_ptx, docs_audiocpp_gpu_arch_builds_per_arch_gcs_staging, docs_audiocpp_gpu_arch_builds_build_verification, docs_audiocpp_gpu_arch_builds_t4_sm75_worked_example [EXTRACTED 1.00]
- **Pronunciation Alpha Sweep Results** — results_pron_sweep_readme, results_pron_sweep_readme_pron_alpha_sweep, results_pron_sweep_readme_short_collapse [EXTRACTED 1.00]
- **pron_lora_ar_only_r8_loss_terms** — concept_loss_loss_metric, concept_loss_ar_ce_metric, concept_loss_ar_kl_metric, concept_additional_model_loss_metric [EXTRACTED 1.00]
- **pron_lora_ar_only_r8_training_run** — concept_pron_lora_ar_only_r8_run, training_analysis_pron_lora_ar_only_r8_01_loss_curves, training_analysis_pron_lora_ar_only_r8_02_loss_main, training_analysis_pron_lora_ar_only_r8_03_learning_rate, training_analysis_pron_lora_ar_only_r8_04_throughput, training_analysis_pron_lora_ar_only_r8_05_gpu_usage [EXTRACTED 1.00]
- **Training observability & backup stack (sidecars, metrics, restore)** — docs_start, docs_monitor, docs_pause_resume, backup_to_gcp, gpu_logger, monitor_loss [EXTRACTED 1.00]
- **hyper_training_analysis_akbar_run_observability** — training_analysis_01_loss_curves_chart, training_analysis_02_loss_main_chart, training_analysis_03_learning_rate_chart, training_analysis_04_throughput_chart, training_analysis_05_gpu_usage_chart, training_analysis_02_loss_main_akbar_arabic_rock_lora_run [INFERRED 0.85]
- **he_run_observability** — training_analysis_v1_nolyrics_archived_01_loss_curves, training_analysis_v1_nolyrics_archived_04_throughput, training_analysis_v1_nolyrics_archived_05_gpu_usage, concept_akbar_arabic_rock_lora_run, concept_sample_eval_interval [INFERRED 0.85]
- **Training Observability Stack** — agents_observability_sources, decisions_loss_log_db_metrics, decisions_no_gpu_logging, readme_observability [EXTRACTED 0.85]
- **Command Handover Discipline** — agents_command_handover_skill, docs_command_handover_gotchas_gotchas, decisions_command_handover, docs_command_handover_gotchas_detached_semantics [EXTRACTED 0.85]
- **audio.cpp Inference Pipeline** — docs_inference_runbook, inference_run_one, docs_inference_generate, inference_duration_cap, inference_suno_to_songs [EXTRACTED 0.85]
- **Blinded Listening Evaluation Rounds** — docs_pron_lora_sweep_alpha_sweep, results_pron_fine_sweep_readme_fine_sweep, results_pron_ckpt_sweep_readme_ckpt_sweep, results_maqam_lyric_swap_readme_lyric_swap, results_pron_knob_probe_readme_knob_probe, skills_ab_blind_eval_skill_a_b_blind_evaluation_packaging [INFERRED 0.85]
- **v2 + pron LoRA Merge Pipeline** — docs_pron_lora_merge_offline_merge, docs_pron_lora_merge_scaling_convention, docs_pron_lora_merge_rank_concatenation, results_pron_production_merge_readme_production_merge, docs_lora_inventory_lora_library [INFERRED 0.85]

## Communities (63 total, 17 thin omitted)

### Community 0 - "Inference CLI (generate.py)"
Cohesion: 0.09
Nodes (61): arabic_letters(), duration_cap(), main(), Dynamic YuE2 `semantic_max_tokens` cap derived from a lyrics file. Canonical…, Return (duration_s, duration_rounded_10s, token_cap, quantile)., asset_fingerprint(), build_parser(), build_tracks() (+53 more)

### Community 1 - "GCS Backup Tests"
Cohesion: 0.10
Nodes (44): _args(), _close_log_handlers(), _dirs(), FakeGsutil, _invoke(), lg(), _patch(), fixture (+36 more)

### Community 2 - "Eval & Sweep Tests"
Cohesion: 0.06
Nodes (30): importlib_util, pytest, runpy, _invoke_cli(), parametrize, Path, Unit tests for INFERENCE/duration_cap.py (GPU-free). The CLI `main()` is…, test_cli_default_quantile() (+22 more)

### Community 3 - "Inference CLI Tests"
Cohesion: 0.05
Nodes (22): _make_run(), parametrize, Unit tests for INFERENCE/generate.py (GPU-free)., Minimal stand-in for subprocess.CompletedProcess., _Run, _songs_json(), _stub_assets(), test_cap_parity_with_duration_cap_cli() (+14 more)

### Community 4 - "Docs Reconciler Scripts"
Cohesion: 0.11
Nodes (31): fnmatch, json, re, is_excluded(), iter_code(), iter_markdown(), Path, Shared scope rules for the docs-reconciler claim extractor/verifier. (+23 more)

### Community 5 - "Offline AR-Loss Replay"
Cohesion: 0.10
Nodes (34): dataclasses, attach_adapter(), build_arg_parser(), build_model(), _import_ai_toolkit(), ItemResult, list_val_pairs(), load_config_sections() (+26 more)

### Community 6 - "Colab Bootstrap & Run Handoff"
Cohesion: 0.08
Nodes (21): confirm_hf(), setup.sh script, start_job(), usage(), Future idea: Arabic pronunciation LoRA, Disjoint AR/NAR expert scoping, AR-only pronunciation adapter, MERT semantic-token representational ceiling (+13 more)

### Community 7 - "Dataset Build & Suno Conversion"
Cohesion: 0.10
Nodes (33): build_parser(), build_report(), build_style(), canonical_tag(), clean_lyrics(), collect_entries(), dedup(), extract_maqam() (+25 more)

### Community 8 - "AB Evaluation Packaging"
Cohesion: 0.10
Nodes (29): ArgumentParser, collections, No Adapter Is Best Before the Blind Listen; alpha <= 0.5, Blinded A/B Listening Package, EVAL.txt / KEYS.txt Public-Secret Split, ab-blind-eval Skill, build_parser(), _discover() (+21 more)

### Community 9 - "AB Blind Evaluation Design"
Cohesion: 0.09
Nodes (31): Generated Listening Packages Live in GCS, Blinded A/B audio evaluation packaging, Conventions, Input layout, Usage, What it produces, Alpha Capped at 0.5, LoRA Library (+23 more)

### Community 10 - "YuE2 Findings & Docs Index"
Cohesion: 0.10
Nodes (33): Text Length to Audio Duration Cap (yue2_dataset), Asymmetric Loss Favors a High Quantile, Centre Fit (Not a Cap), Duration Cap Formula, Arabic Letter Counting Rule, Quantile (Pinball-loss) Regression, Running a LoRA on the Yue2-3B GGUF Model: Findings, AR / NAR Stages (+25 more)

### Community 11 - "GCS Backup Engine"
Cohesion: 0.15
Nodes (26): ensure_manifest(), main(), parse_args(), parse_extra_specs(), parse_watch_specs(), Path, Same shape as TRAINING_TARGETS, but for an arbitrary run name. `--run-name`…, `LOCAL` or `LOCAL:SUB` -> (expanded local path, remote subfolder). SUB defaults… (+18 more)

### Community 12 - "Training Loss Curves"
Cohesion: 0.13
Nodes (27): Additional Model Loss, additional_model_loss metric, akbar_arabic_rock_lora Training Run (3000 steps), checkpoint save interval every 1525 steps, gpu_logger.py (10s GPU sampling script, data source), GPU telemetry (utilization, memory, temperature, power), learning rate schedule (constant 1e-4), Autoregressive Cross-Entropy Loss (loss/ar_ce) (+19 more)

### Community 13 - "LoRA Merge Pipeline"
Cohesion: 0.13
Nodes (26): hashlib, _ab(), build_metadata(), _check_alpha_keys(), main(), merge(), MergeError, _proj() (+18 more)

### Community 14 - "Training Charts"
Cohesion: 0.16
Nodes (21): csv, datetime, matplotlib, matplotlib_pyplot, ndarray, numpy, sqlite3, main() (+13 more)

### Community 15 - "Merge Tests"
Cohesion: 0.13
Nodes (11): ar_keys(), build(), nar_keys(), pron(), fixture, Unit tests for merge_pron_lora.py (CPU-only, synthetic bf16 tensors). The…, _sha(), test_alpha_one_rank_concat_and_delta() (+3 more)

### Community 16 - "audiocpp_build Build Docs"
Cohesion: 0.19
Nodes (19): Building audiocpp_cli for a Specific GPU from a CPU-only Colab Runtime, scripts/build_linux.sh, Build Verification Procedure, ccache Build Caching, Compute Capabilities for T4 / A100 / L4, nvcc Cross-Compilation on a CPU Host, --cuda-arch Flag, Per-arch GCS Staging Convention (+11 more)

### Community 17 - "GPU Logging & Training Launch"
Cohesion: 0.15
Nodes (16): argparse, Final backup & push checklist, GCS not append-only for the un-suffixed final adapter, Check how training is going, gpu_usage.csv hardware log, loss_log.db per-step metrics surface, Pause for the night, resume next session, ai-toolkit auto-resume from newest checkpoint (+8 more)

### Community 18 - "Inference Runbook (audio.cpp)"
Cohesion: 0.13
Nodes (16): audio.cpp Seeds and Sidecar Policy, audio.cpp Build: --model-set full Was the Cost, audiocpp_inference Staging Rule, Inference Backup Is a Race Against VM Death, T4 VRAM Governed by Attention Kernel, audio.cpp docs/models/yue2.md Is CLI Flag Source of Truth, One Shared Rented GPU, Prebuilt vs Source-Built audiocpp_cli (+8 more)

### Community 19 - "Inference Sweep Entrypoints"
Cohesion: 0.17
Nodes (15): main(), plan(), Path, Cross-maqam lyric swap: one maqam's caption+tag with the other's held-out…, Resolve each track's inputs + auto cap without touching the GPU., wav_frames(), main(), Path (+7 more)

### Community 20 - "Suno Conversion Tests"
Cohesion: 0.21
Nodes (13): _convert(), parametrize, Unit tests for INFERENCE/suno_to_songs.py (GPU-free)., test_bad_manifests(), test_defaults_and_file_mode(), test_dry_run_writes_nothing_and_determinism(), test_keep_both_and_filters(), test_keep_first() (+5 more)

### Community 21 - "Pytest Conftest & Fixtures"
Cohesion: 0.23
Nodes (15): bak(), dur(), gen(), _load_module(), lyrics_ar(), manifest_path(), _no_vram_sleep(), fixture (+7 more)

### Community 22 - "Training loss/loss Metric"
Cohesion: 0.17
Nodes (16): additional_model_loss component declining from ~5.8 to ~3.9, loss/ar_ce component (autoregressive cross-entropy) declining from ~5.8 to ~3.6, loss/ar_kl component rising from 0 to ~1.5 (KL divergence term), Per-step loss curves 2x2 panel (loss/loss, loss/ar_ce, loss/ar_kl, additional_model_loss vs step), Per-step training loss metric (raw + 25-step mean), akbar_arabic_rock_lora training run, Primary loss/loss curve vs step with 50-step mean and trend line (-2.14e-04/step), loss_log.db SQLite metrics store (data source for loss curves) (+8 more)

### Community 23 - "Agent Operating Contract"
Cohesion: 0.18
Nodes (14): Agent Operating Contract, Auto-Resume Exception Policy, Backup Responsibility, Colab Is Ephemeral, command-handover Skill, agent_notes/current.md Handoff Surface, Agent Training-Control Policy, Handing Over a Command States Terminal Semantics (+6 more)

### Community 24 - "Loss Monitor"
Cohesion: 0.29
Nodes (13): Connection, connect_readonly(), history(), latest_step(), list_keys(), main(), metrics_at_step(), Namespace (+5 more)

### Community 25 - "Observability Sources"
Cohesion: 0.18
Nodes (13): Training Observability Sources, CLI Over Web UI On Purpose, Assets Resolve via HF Hub Cache, Canonical LoRA Library <base>/loras/, loss_log.db Is the Metrics Source, Merging Two YuE2 LoRAs: Rank-Concat, No GPU Logging in AI Toolkit, YuE2 LoRA Loading Native in audio.cpp (+5 more)

### Community 26 - "Held-Out Eval & Dataset v2"
Cohesion: 0.18
Nodes (11): sample.samples Held-Out Prompts, duration 360, Held-Out Eval Set Contamination, sample.duration 360 Rationale and Cost, Byte-Identity Proof (267/267), Step 5 Held-Out Checks, Held-Out Maqam Evaluation Set, Four Per-Maqam Picks, prepare_yue2_dataset_v2.py Build Functions (+3 more)

### Community 27 - "v2 Run Lessons"
Cohesion: 0.20
Nodes (11): train_window_frames: 0 (whole song), Extending a Run Overwrites Final Adapter, Goal Correction: train_window_frames Was the Gap, Lesson: Goal Change Invalidates Old Decisions, Same Run Name Auto-Resumes, v2 Finished: Lyric Fix Worked; ar_kl Drift, Archive Old Output to Start Fresh, v1 Run (style-only captions, 3000/3000) (+3 more)

### Community 28 - "Graphify Knowledge Graph"
Cohesion: 0.27
Nodes (10): Graphify Knowledge Graph Usage, graphify install / MCP Server, graphify Repo Knowledge Graph, graphify-out Artifacts, graphify update, docs-reconciler Skill, Live-Doc Drift Reconciliation Runs, One Authority Per Topic Table (+2 more)

### Community 29 - "LoRA Inventory"
Cohesion: 0.20
Nodes (9): Archived — α>0.5 (out of scope), Caveats, Counts, Experimental adapters (in scope, α≤0.5 — NOT the library), Fused source adapters (`loras/source/`), How to stage an adapter, Library adapters (`loras/`, audio.cpp-loadable), Library location (+1 more)

### Community 30 - "Training Configs"
Cohesion: 0.36
Nodes (8): akbar_arabic_rock_lora Training Config, pron_lora_ar_only Config (AR-only, rank 8), pron_lora_ar_only_smoke Config (10-step smoke), v2 Training Analysis — akbar_arabic_rock_lora, Lower loss/ar_ce Is Mechanism, Not Quality, pron Run A100 Data/CPU-Bound, pron_lora_ar_only_r8 Training Analysis, v1 No-Lyrics Training Analysis (Archived)

### Community 31 - "Project Overview & Docs"
Cohesion: 0.25
Nodes (8): v2 Caption Lyric Format (binding), Dataset Verification: 267 Pairs, Env Vars Staged by Launching Notebook, Dataset Section, README Docs Index, Project Overview, Repo Layout, Running on Colab Section

### Community 32 - "L4 vs A100 Decision"
Cohesion: 0.38
Nodes (7): L4 vs A100 decision note, A100-SXM4-80GB, A100 measured ~4.3x faster than L4 (3.10 s/step), A100 vs L4 break-even compute-unit economics, NVIDIA L4 (24 GB, 121 TFLOPS bf16), Live status snapshot (A100 post-resume), A100 resume from step-250 checkpoint

### Community 33 - "Graphify Usage Docs"
Cohesion: 0.29
Nodes (6): Caveats, Enable it in another agent / environment, Refresh it, Repo knowledge graph (graphify), Use it, Where it lives

### Community 34 - "Crash-Diagnose & Handover Skills"
Cohesion: 0.33
Nodes (7): command-handover Skill, Detached Hygiene Checklist, Foreground vs Detached Decision, crash-diagnose-and-resume Skill, Auto-Resume Policy, Fresh VM Restore Procedure, Stop Classification Table

### Community 35 - "Backup Mirror Targets"
Cohesion: 0.20
Nodes (6): Backup Settle Must Ignore loss_log.db, Cross-VM / Cross-GPU Resume, Backup Mirror Targets by Mode, Restore from GCS, Settle Wait on output/, --watch Replaces vs --extra Adds

### Community 36 - "maqam_lyric_swap Results"
Cohesion: 0.33
Nodes (5): Blinded review, Configs, Groups, maqam_lyric_swap — cross-maqam lyric swap (Hijaz + Kurd), Tracks

### Community 37 - "pron_knob_probe Results"
Cohesion: 0.33
Nodes (5): Blinded review, Configs (one knob vs the anchor defaults), pron_knob_probe — request-option knob probe at ckpt 3050, alpha 0.5, Resources per generation, Tracks

### Community 38 - "Merge Candidates Results"
Cohesion: 0.33
Nodes (5): Large binaries are not committed, Non-obvious: file-level sha256 is not reproducible (tensor digest is), pron_production_merge — v2 + pron merge candidates (checkpoint 3050), Sidecars, Verification performed (2026-09-25, CPU)

### Community 39 - "Repo Audit Backlog"
Cohesion: 0.50
Nodes (5): Repo audit: stale docs, drift & workflow backlog, No restore path for agent_notes/current.md, Flat inference out/ dir mixes unrelated runs, Staged scripts/ drifted from repo and self-perpetuates, Single status command for the whole job

### Community 40 - "pron_ckpt_sweep Results"
Cohesion: 0.40
Nodes (4): Blinded review, Configs, pron_ckpt_sweep — pron checkpoints 1525 vs 4575 at alpha 0.5 (Hijaz + Kurd), Tracks

### Community 41 - "T4 Re-Render"
Cohesion: 0.40
Nodes (4): Caveats, Result — the outputs differ, T4 re-render of the two lost Kurd WAVs (2026-09-25), Where

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
- **94 isolated node(s):** `github_auth.sh script`, `pron_fine_sweep.sh script`, `Input layout`, `Usage`, `What it produces` (+89 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 305 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **17 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `docs-reconciler Skill` connect `YuE2 Findings & Docs Index` to `Docs Reconciler Scripts`?**
  _High betweenness centrality (0.086) - this node is a cross-community bridge._
- **Why does `Live vs Frozen Doc Scope` connect `YuE2 Findings & Docs Index` to `audiocpp_build Build Docs`?**
  _High betweenness centrality (0.077) - this node is a cross-community bridge._
- **Why does `Inference End-to-End Runbook` connect `Inference Runbook (audio.cpp)` to `Observability Sources`, `GCS Backup Engine`, `Graphify Knowledge Graph`, `Project Overview & Docs`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **What connects `github_auth.sh script`, `pron_fine_sweep.sh script`, `Input layout` to the rest of the system?**
  _94 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Inference CLI (generate.py)` be split into smaller, more focused modules?**
  _Cohesion score 0.08704557091653865 - nodes in this community are weakly interconnected._
- **Should `GCS Backup Tests` be split into smaller, more focused modules?**
  _Cohesion score 0.1025974025974026 - nodes in this community are weakly interconnected._
- **Should `Eval & Sweep Tests` be split into smaller, more focused modules?**
  _Cohesion score 0.05851063829787234 - nodes in this community are weakly interconnected._