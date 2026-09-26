# Graph Report - maqamrock-yue2-lora-finetuning  (2026-09-26)

## Corpus Check
- 123 files · ~192,542 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 1, .ini 1, .log 1)

## Summary
- 841 nodes · 1658 edges · 34 communities (30 shown, 4 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 72 edges (avg confidence: 0.79)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d78a3790`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Inference runbook: audiocpp_cli + YuE2 GGUF + LoRA
- generate.py
- DECISIONS.md — Durable Decisions & Insights
- test_backup_to_gcp.py
- test_merge_pron_lora.py
- suno_to_songs.py
- test_generate.py
- offline_ar_loss_replay.py
- merge_pron_lora.py
- Running a LoRA on the Yue2-3B GGUF Model: Findings
- backup_to_gcp.py
- Building audiocpp_cli for a Specific GPU from a CPU-only Colab Runtime
- per-step loss curves (loss/loss, loss/ar_ce, loss/ar_kl, additional_model_loss)
- prepare_ab_eval.py
- test_prepare_ab_eval.py
- setup.sh
- generate_plots.py
- test_suno_to_songs.py
- sys
- Per-step loss curves 2x2 panel (loss/loss, loss/ar_ce, loss/ar_kl, additional_model_loss vs step)
- ref_fs
- github_auth.sh
- pron_fine_sweep.sh
- conftest.py
- A/B blind evaluation packaging
- LoRA inventory
- Repo knowledge graph (graphify)
- maqam_lyric_swap — cross-maqam lyric swap (Hijaz + Kurd)
- pron_knob_probe — request-option knob probe at ckpt 3050, alpha 0.5
- pron_ckpt_sweep — pron checkpoints 1525 vs 4575 at alpha 0.5 (Hijaz + Kurd)
- T4 re-render of the two lost Kurd WAVs (2026-09-25)
- pron_knob_probe.sh
- regenerate.sh
- ref_path

## God Nodes (most connected - your core abstractions)
1. `FakeGsutil` - 35 edges
2. `DECISIONS.md — Durable Decisions & Insights` - 33 edges
3. `_patch()` - 31 edges
4. `_invoke()` - 22 edges
5. `README.md — Project Overview & Status` - 22 edges
6. `Operations docs index` - 21 edges
7. `Inference runbook: audiocpp_cli + YuE2 GGUF + LoRA` - 20 edges
8. `PROGRESS.md — Milestone Trail` - 18 edges
9. `main()` - 17 edges
10. `akbar_arabic_rock_lora Training Config` - 17 edges

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
- **he_loss_metric_panel** — training_analysis_v1_nolyrics_archived_01_loss_curves, concept_loss_loss, concept_loss_ar_ce, concept_loss_ar_kl, concept_additional_model_loss [EXTRACTED 1.00]
- **audiocpp inference pipeline (setup -> run/launch -> cap -> convert)** — docs_inference, inference_run_one, inference_generate, inference_duration_cap, converter_convert_aitoolkit_yue2_lora_py [EXTRACTED 1.00]
- **Docs Reconciliation Workflow** — skills_docs_reconciler_skill, skills_docs_reconciler_scripts_extract_claims, skills_docs_reconciler_scripts_verify_claims, skills_docs_reconciler_skill_human_checkpoint, skills_docs_reconciler_references_example_drift_report, skills_docs_reconciler_references_unverifiable_token_list [EXTRACTED 1.00]
- **Per-GPU CUDA Build Workflow** — docs_audiocpp_gpu_arch_builds, docs_audiocpp_gpu_arch_builds_cross_compilation, docs_audiocpp_gpu_arch_builds_cuda_arch_flag, docs_audiocpp_gpu_arch_builds_sass_vs_ptx, docs_audiocpp_gpu_arch_builds_per_arch_gcs_staging, docs_audiocpp_gpu_arch_builds_build_verification, docs_audiocpp_gpu_arch_builds_t4_sm75_worked_example [EXTRACTED 1.00]
- **Pronunciation Alpha Sweep Results** — results_pron_sweep_readme, results_pron_fine_sweep_readme, results_pron_sweep_readme_pron_alpha_sweep, results_pron_fine_sweep_readme_fine_alpha_sweep, results_pron_fine_sweep_readme_alpha, results_pron_sweep_readme_short_collapse [EXTRACTED 1.00]
- **pron_lora_ar_only_r8_loss_terms** — concept_loss_loss_metric, concept_loss_ar_ce_metric, concept_loss_ar_kl_metric, concept_additional_model_loss_metric [EXTRACTED 1.00]
- **pron_lora_ar_only_r8_training_run** — concept_pron_lora_ar_only_r8_run, training_analysis_pron_lora_ar_only_r8_01_loss_curves, training_analysis_pron_lora_ar_only_r8_02_loss_main, training_analysis_pron_lora_ar_only_r8_03_learning_rate, training_analysis_pron_lora_ar_only_r8_04_throughput, training_analysis_pron_lora_ar_only_r8_05_gpu_usage [EXTRACTED 1.00]
- **AR-only pronunciation LoRA pipeline (verify -> train -> merge -> sweep)** — docs_pron_lora_verification, docs_pron_lora, docs_pron_lora_merge, docs_pron_lora_sweep [EXTRACTED 1.00]
- **Training observability & backup stack (sidecars, metrics, restore)** — docs_start, docs_monitor, docs_pause_resume, backup_to_gcp, gpu_logger, monitor_loss [EXTRACTED 1.00]
- **hyper_training_analysis_akbar_run_observability** — training_analysis_01_loss_curves_chart, training_analysis_02_loss_main_chart, training_analysis_03_learning_rate_chart, training_analysis_04_throughput_chart, training_analysis_05_gpu_usage_chart, training_analysis_02_loss_main_akbar_arabic_rock_lora_run [INFERRED 0.85]
- **he_run_observability** — training_analysis_v1_nolyrics_archived_01_loss_curves, training_analysis_v1_nolyrics_archived_04_throughput, training_analysis_v1_nolyrics_archived_05_gpu_usage, concept_akbar_arabic_rock_lora_run, concept_sample_eval_interval [INFERRED 0.85]
- **Ephemeral Colab to GCS Persistence & Resume Flow** — docs_backup_restore_document, readme_colab_ephemeral, agents_backup_responsibility, decisions_auto_resume, decisions_cross_vm_resume [INFERRED 0.85]
- **Lyric-Conditioned v2 Dataset & Training Pipeline** — decisions_lyric_caption_format, readme_yue2_dataset, config_akbar_arabic_rock_lora_config, training_analysis_analysis_document, decisions_v2_lyric_fix_result, inference_yue2_eval_heldout_heldout_eval_report_document [INFERRED 0.85]

## Communities (34 total, 4 thin omitted)

### Community 0 - "Inference runbook: audiocpp_cli + YuE2 GGUF + LoRA"
Cohesion: 0.10
Nodes (30): Human-terminal handover gotchas, Detached launch pattern (setsid nohup ... & disown), Training runs foreground on purpose so Ctrl+C works, Every detached command ships with stop + resume, Env vars staged by the launching notebook, One shared GPU (training + inference), Detached jobs inherit SIGINT ignored, vscode.dev clipboard is glitchy -> current.md handoff (+22 more)

### Community 1 - "generate.py"
Cohesion: 0.08
Nodes (62): arabic_letters(), duration_cap(), main(), Dynamic YuE2 `semantic_max_tokens` cap derived from a lyrics file. Canonical…, Return (duration_s, duration_rounded_10s, token_cap, quantile)., asset_fingerprint(), build_parser(), build_tracks() (+54 more)

### Community 2 - "DECISIONS.md — Durable Decisions & Insights"
Cohesion: 0.07
Nodes (72): AGENTS.md — Agent Operating Contract, Backup Responsibility (GCS mirroring), Command Handover Policy, Training Observability Surfaces, akbar_arabic_rock_lora Training Config, ar_kl_weight 0.2, cot: off (Skip SheetSage2), sample.duration: 360 Rationale (+64 more)

### Community 3 - "test_backup_to_gcp.py"
Cohesion: 0.10
Nodes (44): _args(), _close_log_handlers(), _dirs(), FakeGsutil, _invoke(), lg(), _patch(), fixture (+36 more)

### Community 4 - "test_merge_pron_lora.py"
Cohesion: 0.07
Nodes (15): importlib_util, safetensors_torch, ar_keys(), build(), nar_keys(), pron(), fixture, Unit tests for merge_pron_lora.py (CPU-only, synthetic bf16 tensors). The… (+7 more)

### Community 5 - "suno_to_songs.py"
Cohesion: 0.11
Nodes (32): build_parser(), build_report(), build_style(), canonical_tag(), clean_lyrics(), collect_entries(), dedup(), extract_maqam() (+24 more)

### Community 6 - "test_generate.py"
Cohesion: 0.05
Nodes (23): hashlib, _make_run(), parametrize, Unit tests for INFERENCE/generate.py (GPU-free)., Minimal stand-in for subprocess.CompletedProcess., _Run, _songs_json(), _stub_assets() (+15 more)

### Community 7 - "offline_ar_loss_replay.py"
Cohesion: 0.11
Nodes (30): dataclasses, attach_adapter(), build_arg_parser(), build_model(), _import_ai_toolkit(), ItemResult, list_val_pairs(), load_config_sections() (+22 more)

### Community 8 - "merge_pron_lora.py"
Cohesion: 0.06
Nodes (54): converter/convert_aitoolkit_yue2_lora.py, Future idea: Arabic pronunciation LoRA, Disjoint AR/NAR expert scoping, AR-only pronunciation adapter, MERT semantic-token representational ceiling, L4 handoff after Task 14c, pron-lora-ar-only branch, No _000006100 checkpoint; post-loop save is step 6100 (+46 more)

### Community 9 - "Running a LoRA on the Yue2-3B GGUF Model: Findings"
Cohesion: 0.07
Nodes (46): Text Length to Audio Duration Cap (yue2_dataset), Asymmetric Loss Favors a High Quantile, Centre Fit (Not a Cap), Duration Cap Formula, Arabic Letter Counting Rule, Quantile (Pinball-loss) Regression, Running a LoRA on the Yue2-3B GGUF Model: Findings, AR / NAR Stages (+38 more)

### Community 10 - "backup_to_gcp.py"
Cohesion: 0.06
Nodes (60): argparse, ensure_manifest(), main(), parse_args(), parse_extra_specs(), parse_watch_specs(), Namespace, Path (+52 more)

### Community 11 - "Building audiocpp_cli for a Specific GPU from a CPU-only Colab Runtime"
Cohesion: 0.19
Nodes (19): Building audiocpp_cli for a Specific GPU from a CPU-only Colab Runtime, scripts/build_linux.sh, Build Verification Procedure, ccache Build Caching, Compute Capabilities for T4 / A100 / L4, nvcc Cross-Compilation on a CPU Host, --cuda-arch Flag, Per-arch GCS Staging Convention (+11 more)

### Community 12 - "per-step loss curves (loss/loss, loss/ar_ce, loss/ar_kl, additional_model_loss)"
Cohesion: 0.13
Nodes (27): Additional Model Loss, additional_model_loss metric, akbar_arabic_rock_lora Training Run (3000 steps), checkpoint save interval every 1525 steps, gpu_logger.py (10s GPU sampling script, data source), GPU telemetry (utilization, memory, temperature, power), learning rate schedule (constant 1e-4), Autoregressive Cross-Entropy Loss (loss/ar_ce) (+19 more)

### Community 13 - "prepare_ab_eval.py"
Cohesion: 0.09
Nodes (29): collections, csv, main(), poll(), gpu_logger.py -------------- AI Toolkit logs no GPU…, build_parser(), _discover(), _ffmpeg_convert() (+21 more)

### Community 14 - "test_prepare_ab_eval.py"
Cohesion: 0.16
Nodes (18): make(), Path, Unit tests for INFERENCE/prepare_ab_eval.py (GPU-free, ffmpeg-free). The audio…, rec_by_file(), test_bad_variant_name_errors(), test_categories_and_duplicate_stems_get_prefix(), test_category_filter(), test_dry_run_writes_nothing() (+10 more)

### Community 15 - "setup.sh"
Cohesion: 0.12
Nodes (5): confirm_hf(), setup.sh script, start_job(), usage(), ext_root_secrets_env

### Community 16 - "generate_plots.py"
Cohesion: 0.20
Nodes (18): matplotlib, matplotlib_pyplot, ndarray, numpy, main(), parse_args(), plot_gpu(), plot_loss_curves() (+10 more)

### Community 17 - "test_suno_to_songs.py"
Cohesion: 0.10
Nodes (23): pytest, runpy, _invoke_cli(), parametrize, Path, Unit tests for INFERENCE/duration_cap.py (GPU-free). The CLI `main()` is…, test_cli_default_quantile(), test_cli_empty_lyrics_uses_floor() (+15 more)

### Community 18 - "sys"
Cohesion: 0.11
Nodes (27): Connection, main(), plan(), Path, Cross-maqam lyric swap: one maqam's caption+tag with the other's held-out…, Resolve each track's inputs + auto cap without touching the GPU., wav_frames(), main() (+19 more)

### Community 19 - "Per-step loss curves 2x2 panel (loss/loss, loss/ar_ce, loss/ar_kl, additional_model_loss vs step)"
Cohesion: 0.17
Nodes (16): additional_model_loss component declining from ~5.8 to ~3.9, loss/ar_ce component (autoregressive cross-entropy) declining from ~5.8 to ~3.6, loss/ar_kl component rising from 0 to ~1.5 (KL divergence term), Per-step loss curves 2x2 panel (loss/loss, loss/ar_ce, loss/ar_kl, additional_model_loss vs step), Per-step training loss metric (raw + 25-step mean), akbar_arabic_rock_lora training run, Primary loss/loss curve vs step with 50-step mean and trend line (-2.14e-04/step), loss_log.db SQLite metrics store (data source for loss curves) (+8 more)

### Community 23 - "conftest.py"
Cohesion: 0.23
Nodes (15): bak(), dur(), gen(), _load_module(), lyrics_ar(), manifest_path(), _no_vram_sleep(), fixture (+7 more)

### Community 24 - "A/B blind evaluation packaging"
Cohesion: 0.15
Nodes (11): Blinded A/B audio evaluation packaging, Conventions, Input layout, Usage, What it produces, A/B blind evaluation packaging, Command, Input contract (+3 more)

### Community 25 - "LoRA inventory"
Cohesion: 0.20
Nodes (9): Archived — α>0.5 (out of scope), Caveats, Counts, Experimental adapters (in scope, α≤0.5 — NOT the library), Fused source adapters (`loras/source/`), How to stage an adapter, Library adapters (`loras/`, audio.cpp-loadable), Library location (+1 more)

### Community 26 - "Repo knowledge graph (graphify)"
Cohesion: 0.29
Nodes (6): Caveats, Enable it in another agent / environment, Refresh it, Repo knowledge graph (graphify), Use it, Where it lives

### Community 27 - "maqam_lyric_swap — cross-maqam lyric swap (Hijaz + Kurd)"
Cohesion: 0.33
Nodes (5): Blinded review, Configs, Groups, maqam_lyric_swap — cross-maqam lyric swap (Hijaz + Kurd), Tracks

### Community 28 - "pron_knob_probe — request-option knob probe at ckpt 3050, alpha 0.5"
Cohesion: 0.33
Nodes (5): Blinded review, Configs (one knob vs the anchor defaults), pron_knob_probe — request-option knob probe at ckpt 3050, alpha 0.5, Resources per generation, Tracks

### Community 29 - "pron_ckpt_sweep — pron checkpoints 1525 vs 4575 at alpha 0.5 (Hijaz + Kurd)"
Cohesion: 0.40
Nodes (4): Blinded review, Configs, pron_ckpt_sweep — pron checkpoints 1525 vs 4575 at alpha 0.5 (Hijaz + Kurd), Tracks

### Community 30 - "T4 re-render of the two lost Kurd WAVs (2026-09-25)"
Cohesion: 0.40
Nodes (4): Caveats, Result — the outputs differ, T4 re-render of the two lost Kurd WAVs (2026-09-25), Where

### Community 31 - "pron_knob_probe.sh"
Cohesion: 0.83
Nodes (3): emit_sidecar(), opts_for(), pron_knob_probe.sh script

### Community 32 - "regenerate.sh"
Cohesion: 1.00
Nodes (3): fetch(), regenerate.sh script, sha256_of()

## Knowledge Gaps
- **64 isolated node(s):** `pron_alpha_sweep.sh script`, `pron_fine_sweep.sh script`, `run_one.sh script`, `github_auth.sh script`, `What it produces` (+59 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 244 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Inference runbook: audiocpp_cli + YuE2 GGUF + LoRA` connect `Inference runbook: audiocpp_cli + YuE2 GGUF + LoRA` to `generate.py`, `DECISIONS.md — Durable Decisions & Insights`, `suno_to_songs.py`, `merge_pron_lora.py`, `Running a LoRA on the Yue2-3B GGUF Model: Findings`, `backup_to_gcp.py`, `Building audiocpp_cli for a Specific GPU from a CPU-only Colab Runtime`?**
  _High betweenness centrality (0.134) - this node is a cross-community bridge._
- **Why does `Operations docs index` connect `DECISIONS.md — Durable Decisions & Insights` to `Inference runbook: audiocpp_cli + YuE2 GGUF + LoRA`, `merge_pron_lora.py`, `Running a LoRA on the Yue2-3B GGUF Model: Findings`, `Building audiocpp_cli for a Specific GPU from a CPU-only Colab Runtime`, `A/B blind evaluation packaging`, `LoRA inventory`, `Repo knowledge graph (graphify)`?**
  _High betweenness centrality (0.120) - this node is a cross-community bridge._
- **Why does `README.md — Project Overview & Status` connect `DECISIONS.md — Durable Decisions & Insights` to `merge_pron_lora.py`, `Inference runbook: audiocpp_cli + YuE2 GGUF + LoRA`?**
  _High betweenness centrality (0.084) - this node is a cross-community bridge._
- **What connects `pron_alpha_sweep.sh script`, `pron_fine_sweep.sh script`, `run_one.sh script` to the rest of the system?**
  _64 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Inference runbook: audiocpp_cli + YuE2 GGUF + LoRA` be split into smaller, more focused modules?**
  _Cohesion score 0.09655172413793103 - nodes in this community are weakly interconnected._
- **Should `generate.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08482142857142858 - nodes in this community are weakly interconnected._
- **Should `DECISIONS.md — Durable Decisions & Insights` be split into smaller, more focused modules?**
  _Cohesion score 0.06572769953051644 - nodes in this community are weakly interconnected._