# Graph Report - maqamrock-yue2-lora-finetuning  (2026-09-25)

## Corpus Check
- 114 files · ~181,340 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 1, .ini 1, .log 1)

## Summary
- 764 nodes · 1512 edges · 24 communities (21 shown, 3 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 90 edges (avg confidence: 0.8)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Inference generation pipeline
- Backup script tests
- Inference generate tests
- Pron LoRA merge & sweep
- Offline AR-loss replay
- Repo tooling scripts & CLI
- Dataset prep & conversion
- Pron merge tests
- Chart generation scripts
- suno_to_songs tests
- OpenCode graphify plugin
- Agent contract & governance docs
- Pytest fixtures & scaffold
- Operations runbooks
- Generation/merge knobs investigation
- GitHub auth script
- Pron fine-sweep driver
- Misc utilities
- Training loss & GPU charts
- Inference runbook & backlog
- audiocpp GPU build notes
- akbar training metrics charts
- Training history & decision docs
- Inference skills & dataset notes

## God Nodes (most connected - your core abstractions)
1. `FakeGsutil` - 35 edges
2. `_patch()` - 31 edges
3. `DECISIONS.md — Durable Decisions & Insights` - 29 edges
4. `_invoke()` - 22 edges
5. `YuE2 generation/merge knobs investigation` - 19 edges
6. `AGENTS.md agent operating contract` - 18 edges
7. `main()` - 17 edges
8. `akbar_arabic_rock_lora Training Config` - 17 edges
9. `check()` - 16 edges
10. `resolve_songs()` - 16 edges

## Surprising Connections (you probably didn't know these)
- `loss/ar_kl Unbroken Rise as First Lever for v3` --semantically_similar_to--> `Lower loss/ar_ce Is Mechanism, Not Quality`  [INFERRED] [semantically similar]
  DECISIONS.md → TRAINING_ANALYSIS/ANALYSIS.md
- `Whole-Song L4 vs A100 Measured (~4.3x)` --semantically_similar_to--> `pron Run A100 Data/CPU-Bound`  [INFERRED] [semantically similar]
  DECISIONS.md → TRAINING_ANALYSIS/pron_lora_ar_only_r8/ANALYSIS.md
- `Retraction: LoRA Conversion Required` --semantically_similar_to--> `v1 to v2 Supersession`  [INFERRED] [semantically similar]
  docs/yue2-gguf-lora-findings.md → verification.md
- `INFERENCE/duration_cap.py auto cap` --references--> `Duration Cap Formula`  [INFERRED]
  skills/inference-batch-run/SKILL.md → docs/text_to_duration_formula.md
- `audio.cpp (0xShug0/audio.cpp)` --conceptually_related_to--> `External / runtime tokens (ai-toolkit, audio.cpp, artifacts)`  [AMBIGUOUS]
  docs/investigation_generation_knobs.md → skills/docs-reconciler/references/unverifiable.txt

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **he_loss_metric_panel** — training_analysis_v1_nolyrics_archived_01_loss_curves, concept_loss_loss, concept_loss_ar_ce, concept_loss_ar_kl, concept_additional_model_loss [EXTRACTED 1.00]
- **audiocpp inference pipeline (setup -> run/launch -> cap -> convert)** — docs_inference, inference_run_one, inference_generate, inference_duration_cap, converter_convert_aitoolkit_yue2_lora_py [EXTRACTED 1.00]
- **Docs Reconciliation Workflow** — skills_docs_reconciler_skill, skills_docs_reconciler_scripts_extract_claims, skills_docs_reconciler_scripts_verify_claims, skills_docs_reconciler_skill_human_checkpoint, skills_docs_reconciler_references_example_drift_report [EXTRACTED 1.00]
- **graphify knowledge graph workflow** — docs_graphify_graphify, docs_graphify_graph_report_md, docs_graphify_graph_json, docs_graphify_update_command, docs_graphify_mcp_server [EXTRACTED 1.00]
- **Per-GPU CUDA Build Workflow** — docs_audiocpp_gpu_arch_builds, docs_audiocpp_gpu_arch_builds_cross_compilation, docs_audiocpp_gpu_arch_builds_cuda_arch_flag, docs_audiocpp_gpu_arch_builds_sass_vs_ptx, docs_audiocpp_gpu_arch_builds_per_arch_gcs_staging, docs_audiocpp_gpu_arch_builds_build_verification, docs_audiocpp_gpu_arch_builds_t4_sm75_worked_example [EXTRACTED 1.00]
- **Pronunciation Alpha Sweep Results** — results_pron_sweep_readme, results_pron_fine_sweep_readme, results_pron_sweep_readme_pron_alpha_sweep, results_pron_fine_sweep_readme_fine_alpha_sweep, results_pron_fine_sweep_readme_alpha, results_pron_sweep_readme_short_collapse [EXTRACTED 1.00]
- **pron_lora_ar_only_r8_loss_terms** — concept_loss_loss_metric, concept_loss_ar_ce_metric, concept_loss_ar_kl_metric, concept_additional_model_loss_metric [EXTRACTED 1.00]
- **pron_lora_ar_only_r8_training_run** — concept_pron_lora_ar_only_r8_run, training_analysis_pron_lora_ar_only_r8_01_loss_curves, training_analysis_pron_lora_ar_only_r8_02_loss_main, training_analysis_pron_lora_ar_only_r8_03_learning_rate, training_analysis_pron_lora_ar_only_r8_04_throughput, training_analysis_pron_lora_ar_only_r8_05_gpu_usage [EXTRACTED 1.00]
- **AR-only pronunciation LoRA pipeline (verify -> train -> merge -> sweep)** — docs_pron_lora_verification, docs_pron_lora, docs_pron_lora_merge, docs_pron_lora_sweep [EXTRACTED 1.00]
- **Training observability & backup stack (sidecars, metrics, restore)** — docs_start, docs_monitor, docs_pause_resume, backup_to_gcp, gpu_logger, monitor_loss [EXTRACTED 1.00]
- **Training observability sources** — agents_loss_log_db, monitor_loss, gpu_logger, agents_gpu_usage_csv, agents_train_log [EXTRACTED 1.00]
- **YuE2 AR sampling knobs proposed for probe** — docs_investigation_generation_knobs_guidance_scale, docs_investigation_generation_knobs_semantic_temperature, docs_investigation_generation_knobs_semantic_repetition_penalty, docs_investigation_generation_knobs_semantic_prefix [EXTRACTED 1.00]
- **hyper_training_analysis_akbar_run_observability** — training_analysis_01_loss_curves_chart, training_analysis_02_loss_main_chart, training_analysis_03_learning_rate_chart, training_analysis_04_throughput_chart, training_analysis_05_gpu_usage_chart, training_analysis_02_loss_main_akbar_arabic_rock_lora_run [INFERRED 0.85]
- **he_run_observability** — training_analysis_v1_nolyrics_archived_01_loss_curves, training_analysis_v1_nolyrics_archived_04_throughput, training_analysis_v1_nolyrics_archived_05_gpu_usage, concept_akbar_arabic_rock_lora_run, concept_sample_eval_interval [INFERRED 0.85]
- **Ephemeral Colab to GCS Persistence & Resume Flow** — docs_backup_restore_document, readme_colab_ephemeral, decisions_auto_resume, decisions_cross_vm_resume [INFERRED 0.85]
- **Lyric-Conditioned v2 Dataset & Training Pipeline** — decisions_lyric_caption_format, readme_yue2_dataset, config_akbar_arabic_rock_lora_config, training_analysis_analysis_document, decisions_v2_lyric_fix_result, inference_yue2_eval_heldout_heldout_eval_report_document [INFERRED 0.85]
- **AR-Only Pronunciation LoRA Train-to-Merge-to-Sweep Workflow** — config_pron_lora_ar_only_config, config_pron_lora_ar_only_smoke_config, training_analysis_pron_lora_ar_only_r8_analysis_document, pron_fine_sweep_input_key_alpha_sweep, pron_fine_sweep_input_key_open_after_listening_document, decisions_lora_merge_rank_concat [INFERRED 0.85]

## Communities (24 total, 3 thin omitted)

### Community 1 - "Inference generation pipeline"
Cohesion: 0.08
Nodes (62): PlanError, Result, Song, Track, arabic_letters(), duration_cap(), main(), asset_fingerprint() (+54 more)

### Community 2 - "Backup script tests"
Cohesion: 0.10
Nodes (44): FakeGsutil, _args(), _close_log_handlers(), _dirs(), _invoke(), lg(), _patch(), test_ensure_manifest_adopts_relocated() (+36 more)

### Community 4 - "Inference generate tests"
Cohesion: 0.05
Nodes (24): _Run, _make_run(), _songs_json(), _stub_assets(), test_cap_parity_with_duration_cap_cli(), test_gpu_info(), test_main_full_path_with_out_dir(), test_main_invalid_limit() (+16 more)

### Community 6 - "Pron LoRA merge & sweep"
Cohesion: 0.08
Nodes (47): MergeError, _ab(), build_metadata(), _check_alpha_keys(), main(), merge(), _proj(), _rank_of_a() (+39 more)

### Community 9 - "Offline AR-loss replay"
Cohesion: 0.09
Nodes (38): ItemResult, ReplayError, attach_adapter(), build_arg_parser(), build_model(), _import_ai_toolkit(), list_val_pairs(), load_config_sections() (+30 more)

### Community 0 - "Repo tooling scripts & CLI"
Cohesion: 0.05
Nodes (68): ensure_manifest(), main(), parse_args(), parse_extra_specs(), parse_watch_specs(), read_remote_json(), run_name_from_path(), _settle_ignored() (+60 more)

### Community 11 - "Dataset prep & conversion"
Cohesion: 0.11
Nodes (32): build_parser(), build_report(), build_style(), canonical_tag(), clean_lyrics(), collect_entries(), dedup(), extract_maqam() (+24 more)

### Community 13 - "Pron merge tests"
Cohesion: 0.11
Nodes (13): ar_keys(), build(), nar_keys(), pron(), _sha(), test_alpha_one_rank_concat_and_delta(), test_alpha_zero_is_v2_verbatim(), test_alpha_zero_reproduces_live_converted_v2() (+5 more)

### Community 14 - "Chart generation scripts"
Cohesion: 0.17
Nodes (20): main(), parse_args(), plot_gpu(), plot_loss_curves(), plot_loss_main(), plot_lr(), plot_throughput(), read_gpu() (+12 more)

### Community 18 - "suno_to_songs tests"
Cohesion: 0.21
Nodes (13): _convert(), test_bad_manifests(), test_defaults_and_file_mode(), test_dry_run_writes_nothing_and_determinism(), test_keep_both_and_filters(), test_keep_first(), test_keep_modes(), test_real_manifest_dedup() (+5 more)

### Community 20 - "OpenCode graphify plugin"
Cohesion: 0.40
Nodes (3): IMPORTANT: keep the reminder string free of backticks and $(...) constructs., ref_fs, ref_path

### Community 3 - "Agent contract & governance docs"
Cohesion: 0.07
Nodes (49): connect_readonly(), history(), latest_step(), list_keys(), main(), metrics_at_step(), rate_estimate(), report() (+41 more)

### Community 8 - "Pytest fixtures & scaffold"
Cohesion: 0.07
Nodes (28): bak(), dur(), gen(), _load_module(), lyrics_ar(), manifest_path(), _no_vram_sleep(), real_wait_vram_free() (+20 more)

### Community 10 - "Operations runbooks"
Cohesion: 0.06
Nodes (23): confirm_hf(), setup.sh script, start_job(), usage(), Env vars staged by the launching notebook, GCS not append-only for the un-suffixed final adapter, A100-SXM4-80GB, A100 measured ~4.3x faster than L4 (3.10 s/step) (+15 more)

### Community 15 - "Generation/merge knobs investigation"
Cohesion: 0.15
Nodes (19): pron_alpha_sweep.sh script, run_one.sh script, ar_ce cross-entropy metric, ar_kl AR drift metric, audio.cpp (0xShug0/audio.cpp), Pron checkpoint 1525 (low drift), Pron checkpoint 3050, guidance_scale (+11 more)

### Community 12 - "Training loss & GPU charts"
Cohesion: 0.13
Nodes (27): gpu_logger.py (10s GPU sampling script, data source), Additional Model Loss, additional_model_loss metric, akbar_arabic_rock_lora Training Run (3000 steps), checkpoint save interval every 1525 steps, GPU telemetry (utilization, memory, temperature, power), learning rate schedule (constant 1e-4), Autoregressive Cross-Entropy Loss (loss/ar_ce) (+19 more)

### Community 16 - "Inference runbook & backlog"
Cohesion: 0.15
Nodes (20): One shared GPU (training + inference), No restore path for agent_notes/current.md, Flat inference out/ dir mixes unrelated runs, Staged scripts/ drifted from repo and self-perpetuates, Single status command for the whole job, Bring-your-own-lyrics JSON batch, Converted unfused AR/NAR LoRA adapters, Text-to-duration cap (95th-percentile quantile regression) (+12 more)

### Community 17 - "audiocpp GPU build notes"
Cohesion: 0.19
Nodes (19): scripts/build_linux.sh, Build Verification Procedure, ccache Build Caching, Compute Capabilities for T4 / A100 / L4, --cuda-arch Flag, Per-arch GCS Staging Convention, SASS vs PTX Embedding, T4 sm_75 Worked Example (+11 more)

### Community 19 - "akbar training metrics charts"
Cohesion: 0.17
Nodes (16): additional_model_loss component declining from ~5.8 to ~3.9, loss/ar_ce component (autoregressive cross-entropy) declining from ~5.8 to ~3.6, loss/ar_kl component rising from 0 to ~1.5 (KL divergence term), Per-step training loss metric (raw + 25-step mean), akbar_arabic_rock_lora training run, loss_log.db SQLite metrics store (data source for loss curves), Primary training loss/loss metric (lower is better, sustained downward trend), Learning rate schedule (constant 1e-4, no decay/warmup) (+8 more)

### Community 5 - "Training history & decision docs"
Cohesion: 0.10
Nodes (48): akbar_arabic_rock_lora Training Config, pron_lora_ar_only Config (AR-only, rank 8), pron_lora_ar_only_smoke Config (10-step smoke), ar_kl_weight 0.2, cot: off (Skip SheetSage2), sample.duration: 360 Rationale, Trigger Injection No Double-Prepend, aitk_db.db Is Not a Metrics Source (+40 more)

### Community 7 - "Inference skills & dataset notes"
Cohesion: 0.07
Nodes (44): convert_aitoolkit_yue2_lora.py, INFERENCE/duration_cap.py auto cap, Centre Fit (Not a Cap), Duration Cap Formula, Arabic Letter Counting Rule, Quantile (Pinball-loss) Regression, AR / NAR Stages, audio.cpp Runtime (+36 more)

## Ambiguous Edges - Review These
- `audio.cpp (0xShug0/audio.cpp)` → `External / runtime tokens (ai-toolkit, audio.cpp, artifacts)`  [AMBIGUOUS]
  skills/docs-reconciler/references/unverifiable.txt · relation: conceptually_related_to

## Knowledge Gaps
- **32 isolated node(s):** `pron_alpha_sweep.sh script`, `run_one.sh script`, `github_auth.sh script`, `pron_fine_sweep.sh script`, `gpu_usage.csv hardware log` (+27 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 197 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `audio.cpp (0xShug0/audio.cpp)` and `External / runtime tokens (ai-toolkit, audio.cpp, artifacts)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `inference-batch-run Skill` connect `Inference skills & dataset notes` to `audiocpp GPU build notes`, `Inference generation pipeline`, `Generation/merge knobs investigation`?**
  _High betweenness centrality (0.086) - this node is a cross-community bridge._
- **Why does `AGENTS.md agent operating contract` connect `Agent contract & governance docs` to `Repo tooling scripts & CLI`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._
- **Why does `Inference runbook: audiocpp_cli + YuE2 GGUF + LoRA` connect `Inference runbook & backlog` to `Repo tooling scripts & CLI`, `Inference generation pipeline`, `Pron LoRA merge & sweep`, `Dataset prep & conversion`, `Generation/merge knobs investigation`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **What connects `pron_alpha_sweep.sh script`, `run_one.sh script`, `github_auth.sh script` to the rest of the system?**
  _32 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Inference generation pipeline` be split into smaller, more focused modules?**
  _Cohesion score 0.08482142857142858 - nodes in this community are weakly interconnected._
- **Should `Backup script tests` be split into smaller, more focused modules?**
  _Cohesion score 0.1025974025974026 - nodes in this community are weakly interconnected._