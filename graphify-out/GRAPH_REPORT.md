# Graph Report - maqamrock-yue2-lora-finetuning  (2026-09-29)

## Corpus Check
- 159 files · ~271,060 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 5 file(s) not represented in the graph (top: (none) 1, .example 1, .ipynb 1)

## Summary
- 1125 nodes · 2207 edges · 73 communities (52 shown, 21 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 74 edges (avg confidence: 0.82)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `5ca4c710`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- DECISIONS.md
- generate.py
- test_backup_to_gcp.py
- test_merge_pron_lora.py
- pathlib
- offline_ar_loss_replay.py
- test_suno_to_songs.py
- prepare_ab_eval.py
- per-step loss curves (loss/loss, loss/ar_ce, loss/ar_kl, additional_model_loss)
- test_generate.py
- backup_to_gcp.py
- train_ctl.py
- prepare_pron_dataset.py
- Running a LoRA on the Yue2-3B GGUF Model: Findings
- suno_to_songs.py
- generate_plots.py
- PRON LoRA LONG — build & multi-day training plan (`quran_long_aya_r8`)
- test_prepare_ab_eval.py
- Building audiocpp_cli for a Specific GPU from a CPU-only Colab Runtime
- Music cover / guide-conditioned generation — feasibility
- test_train_ctl.py
- Per-step loss curves 2x2 panel (loss/loss, loss/ar_ce, loss/ar_kl, additional_model_loss vs step)
- A/B blind evaluation packaging
- sys
- GCS organization plan — OSTRIS project (non-breaking)
- abc_transcribe.py
- test_status.py
- status.py
- Long-aya Quran pronunciation LoRA — runbook (canonical)
- time
- Working with the agent — experience checklist
- Held-Out Maqam Evaluation Set
- sample_pron_dataset.py
- test_run_batch_ok_then_skip_then_force_fail
- screen_summary.py
- subprocess
- User cheatsheet
- _songs_json
- graphify update .
- _Run
- Training analysis — `quran_long_aya_r8_s10` (long-aya Quran pronunciation LoRA, 10% subsample)
- test_duration_cap.py
- ref_fs
- _stub_assets
- v2 Training Analysis — akbar_arabic_rock_lora
- json
- pron_knob_probe.sh
- regenerate.sh
- graphify.serve MCP server
- qfinal_suno_sweep.sh
- test_batch.sh
- parametrize
- github_auth.sh
- graphify-out/GRAPH_REPORT.md
- pron_alpha_sweep.sh
- pron_fine_sweep.sh
- run_one.sh
- test_pick_run_dir_collision
- test_run_batch_uses_per_song_lora
- Graph is branch-specific; dangling-endpoint edges gap
- graphify explain
- graphify-out/graph.html
- graphify install --platform
- Map, not the territory
- graphify path
- setup.sh
- run.py (ai-toolkit training engine)
- gcp_backup.log
- v2_abc_to_qfinal.sh
- screen_arms.sh
- train.log
- ref_path
- SKILL.md (command-handover)

## God Nodes (most connected - your core abstractions)
1. `FakeGsutil` - 35 edges
2. `_patch()` - 31 edges
3. `docs/README.md index` - 26 edges
4. `check()` - 22 edges
5. `_invoke()` - 22 edges
6. `resolve_songs()` - 18 edges
7. `main()` - 18 edges
8. `Inference runbook` - 18 edges
9. `make()` - 16 edges
10. `Pronunciation LoRA runbook` - 16 edges

## Surprising Connections (you probably didn't know these)
- `4. Measure A — the style-text (prompt) lever — cheapest, in-distribution` --references--> `build_caption()`  [INFERRED]
  docs/music-cover-feasibility.md → prepare_yue2_dataset.py
- `11. Implementation log — 2026-09-29` --references--> `test_inference_targets_are_sectioned()`  [INFERRED]
  docs/GCP_ORGANIZATION_PLAN.md → tests/test_backup_to_gcp.py
- `9.6 Open questions for the next session` --references--> `v2()`  [INFERRED]
  docs/music-cover-feasibility.md → tests/test_merge_pron_lora.py
- `0. Verified state this session` --references--> `status()`  [INFERRED]
  agent_notes/current.md → tests/test_status.py
- `v1 to v2 Supersession` --semantically_similar_to--> `Retraction: LoRA Conversion Required`  [INFERRED] [semantically similar]
  verification.md → docs/yue2-gguf-lora-findings.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **YuE2 LoRA training config family** — config_akbar_arabic_rock_lora, config_pron_lora_ar_only, config_pron_lora_ar_only_smoke, config_quran_long_aya_r8, config_quran_long_aya_r8_s10 [EXTRACTED 0.90]
- **he_loss_metric_panel** — training_analysis_v1_nolyrics_archived_01_loss_curves, concept_loss_loss, concept_loss_ar_ce, concept_loss_ar_kl, concept_additional_model_loss [EXTRACTED 1.00]
- **Docs Reconciliation Workflow** — skills_docs_reconciler_skill, skills_docs_reconciler_scripts_extract_claims, skills_docs_reconciler_scripts_verify_claims, skills_docs_reconciler_skill_human_checkpoint, skills_docs_reconciler_references_example_drift_report [EXTRACTED 1.00]
- **Per-GPU CUDA Build Workflow** — docs_audiocpp_gpu_arch_builds, docs_audiocpp_gpu_arch_builds_cross_compilation, docs_audiocpp_gpu_arch_builds_cuda_arch_flag, docs_audiocpp_gpu_arch_builds_sass_vs_ptx, docs_audiocpp_gpu_arch_builds_per_arch_gcs_staging, docs_audiocpp_gpu_arch_builds_build_verification, docs_audiocpp_gpu_arch_builds_t4_sm75_worked_example [EXTRACTED 1.00]
- **Pronunciation Alpha Sweep Results** — results_pron_sweep_readme, results_pron_sweep_readme_pron_alpha_sweep, results_pron_sweep_readme_short_collapse [EXTRACTED 1.00]
- **pron_lora_ar_only_r8_loss_terms** — concept_loss_loss_metric, concept_loss_ar_ce_metric, concept_loss_ar_kl_metric, concept_additional_model_loss_metric [EXTRACTED 1.00]
- **pron_lora_ar_only_r8_training_run** — concept_pron_lora_ar_only_r8_run, training_analysis_pron_lora_ar_only_r8_01_loss_curves, training_analysis_pron_lora_ar_only_r8_02_loss_main, training_analysis_pron_lora_ar_only_r8_03_learning_rate, training_analysis_pron_lora_ar_only_r8_04_throughput, training_analysis_pron_lora_ar_only_r8_05_gpu_usage [EXTRACTED 1.00]
- **hyper_training_analysis_akbar_run_observability** — training_analysis_01_loss_curves_chart, training_analysis_02_loss_main_chart, training_analysis_03_learning_rate_chart, training_analysis_04_throughput_chart, training_analysis_05_gpu_usage_chart, training_analysis_02_loss_main_akbar_arabic_rock_lora_run [INFERRED 0.85]
- **he_run_observability** — training_analysis_v1_nolyrics_archived_01_loss_curves, training_analysis_v1_nolyrics_archived_04_throughput, training_analysis_v1_nolyrics_archived_05_gpu_usage, concept_akbar_arabic_rock_lora_run, concept_sample_eval_interval [INFERRED 0.85]

## Communities (73 total, 21 thin omitted)

### Community 0 - "DECISIONS.md"
Cohesion: 0.05
Nodes (95): ostris/ai-toolkit (pinned), aitk_db.db, audio.cpp, loss/ar_kl rises from 0 to ~1.35 while ar_ce falls, Grey vertical markers indicate a checkpoint save every 1500 steps, Learning rate is a flat constant line across all ~8000 steps, no warmup or decay, GPU memory steady near ~8500 MiB, temperature ~75 C plateau, power ~65 W, GPU utilization is bursty, oscillating between near 0 and 100% (+87 more)

### Community 1 - "generate.py"
Cohesion: 0.08
Nodes (70): build_levels(), main(), Path, select_track(), arabic_letters(), duration_cap(), main(), Dynamic YuE2 `semantic_max_tokens` cap derived from a lyrics file. Canonical… (+62 more)

### Community 2 - "test_backup_to_gcp.py"
Cohesion: 0.10
Nodes (44): _args(), _close_log_handlers(), _dirs(), FakeGsutil, _invoke(), lg(), _patch(), fixture (+36 more)

### Community 3 - "test_merge_pron_lora.py"
Cohesion: 0.07
Nodes (37): 9.6 Open questions for the next session, _ab(), build_metadata(), _check_alpha_keys(), main(), merge(), MergeError, _proj() (+29 more)

### Community 4 - "pathlib"
Cohesion: 0.11
Nodes (32): fnmatch, pathlib, re, is_excluded(), iter_code(), iter_markdown(), Path, Shared scope rules for the docs-reconciler claim extractor/verifier. (+24 more)

### Community 5 - "offline_ar_loss_replay.py"
Cohesion: 0.10
Nodes (34): dataclasses, attach_adapter(), build_arg_parser(), build_model(), _import_ai_toolkit(), ItemResult, list_val_pairs(), load_config_sections() (+26 more)

### Community 6 - "test_suno_to_songs.py"
Cohesion: 0.19
Nodes (15): _convert(), parametrize, Unit tests for INFERENCE/suno_to_songs.py (GPU-free)., test_bad_manifests(), test_defaults_and_file_mode(), test_dry_run_writes_nothing_and_determinism(), test_keep_both_and_filters(), test_keep_first() (+7 more)

### Community 7 - "prepare_ab_eval.py"
Cohesion: 0.11
Nodes (25): collections, Blinded A/B Listening Package, EVAL.txt / KEYS.txt Public-Secret Split, ab-blind-eval Skill, build_parser(), _discover(), _ffmpeg_convert(), _group_pairs() (+17 more)

### Community 8 - "per-step loss curves (loss/loss, loss/ar_ce, loss/ar_kl, additional_model_loss)"
Cohesion: 0.13
Nodes (27): Additional Model Loss, additional_model_loss metric, akbar_arabic_rock_lora Training Run (3000 steps), checkpoint save interval every 1525 steps, gpu_logger.py (10s GPU sampling script, data source), GPU telemetry (utilization, memory, temperature, power), learning rate schedule (constant 1e-4), Autoregressive Cross-Entropy Loss (loss/ar_ce) (+19 more)

### Community 10 - "backup_to_gcp.py"
Cohesion: 0.16
Nodes (24): ensure_manifest(), main(), parse_args(), parse_extra_specs(), parse_watch_specs(), Namespace, Path, Same shape as TRAINING_TARGETS, but for an arbitrary run name. `--run-name`… (+16 more)

### Community 11 - "train_ctl.py"
Cohesion: 0.22
Nodes (22): _alive(), build_parser(), cmd_start(), cmd_status(), cmd_stop(), _cmdline(), _cmdline_matches(), main() (+14 more)

### Community 12 - "prepare_pron_dataset.py"
Cohesion: 0.15
Nodes (21): concurrent_futures, build(), write_one(), choose_splits(), Config, discover_source_audio(), load_tanzil(), main() (+13 more)

### Community 13 - "Running a LoRA on the Yue2-3B GGUF Model: Findings"
Cohesion: 0.10
Nodes (33): Text Length to Audio Duration Cap (yue2_dataset), Asymmetric Loss Favors a High Quantile, Centre Fit (Not a Cap), Duration Cap Formula, Arabic Letter Counting Rule, Quantile (Pinball-loss) Regression, Running a LoRA on the Yue2-3B GGUF Model: Findings, AR / NAR Stages (+25 more)

### Community 14 - "suno_to_songs.py"
Cohesion: 0.10
Nodes (34): build_parser(), build_report(), build_style(), canonical_tag(), clean_lyrics(), clean_lyrics_verbatim(), collect_entries(), dedup() (+26 more)

### Community 15 - "generate_plots.py"
Cohesion: 0.11
Nodes (32): Connection, matplotlib, matplotlib_pyplot, connect_readonly(), history(), latest_step(), list_keys(), main() (+24 more)

### Community 16 - "PRON LoRA LONG — build & multi-day training plan (`quran_long_aya_r8`)"
Cohesion: 0.09
Nodes (22): 1. Objective, 2. Locked decisions, 3.1 Selection (from `selection_report.json`), 3.2 Output shape (reference-compatible), 3.3 Scale (as built), 3.4 Build pipeline (DONE; builder reconstructed for reproducibility), 3. Dataset (BUILT, VALIDATED, FINAL), 4.1 Latent cache (kept; banked) (+14 more)

### Community 17 - "test_prepare_ab_eval.py"
Cohesion: 0.16
Nodes (18): make(), Path, Unit tests for INFERENCE/prepare_ab_eval.py (GPU-free, ffmpeg-free). The audio…, rec_by_file(), test_bad_variant_name_errors(), test_categories_and_duplicate_stems_get_prefix(), test_category_filter(), test_dry_run_writes_nothing() (+10 more)

### Community 18 - "Building audiocpp_cli for a Specific GPU from a CPU-only Colab Runtime"
Cohesion: 0.19
Nodes (19): Building audiocpp_cli for a Specific GPU from a CPU-only Colab Runtime, scripts/build_linux.sh, Build Verification Procedure, ccache Build Caching, Compute Capabilities for T4 / A100 / L4, nvcc Cross-Compilation on a CPU Host, --cuda-arch Flag, Per-arch GCS Staging Convention (+11 more)

### Community 19 - "Music cover / guide-conditioned generation — feasibility"
Cohesion: 0.07
Nodes (28): 10.1 Design, 10.2 Result, 10.3 Caveats, 10.4 Provenance, 10. Addendum — 2026-09-29: the verbatim / lyric-adherence blind round (scored), 11.1 Verified inventory (bucket read-only, `gsutil ls`, 2026-09-29), 11.2 Guide options, 11.3 The three risks (unchanged from §3) (+20 more)

### Community 20 - "test_train_ctl.py"
Cohesion: 0.07
Nodes (29): importlib_util, pytest, signal, bak(), dur(), gen(), _load_module(), lyrics_ar() (+21 more)

### Community 21 - "Per-step loss curves 2x2 panel (loss/loss, loss/ar_ce, loss/ar_kl, additional_model_loss vs step)"
Cohesion: 0.17
Nodes (16): additional_model_loss component declining from ~5.8 to ~3.9, loss/ar_ce component (autoregressive cross-entropy) declining from ~5.8 to ~3.6, loss/ar_kl component rising from 0 to ~1.5 (KL divergence term), Per-step loss curves 2x2 panel (loss/loss, loss/ar_ce, loss/ar_kl, additional_model_loss vs step), Per-step training loss metric (raw + 25-step mean), akbar_arabic_rock_lora training run, Primary loss/loss curve vs step with 50-step mean and trend line (-2.14e-04/step), loss_log.db SQLite metrics store (data source for loss curves) (+8 more)

### Community 22 - "A/B blind evaluation packaging"
Cohesion: 0.17
Nodes (14): Cross-Maqam Lyric Swap, Pron Checkpoint Sweep, Fine Alpha Sweep at Checkpoint 3050, Request-Option Knob Probe, GPU/Architecture Dependence of Seed Reproducibility, Production Merge Candidates, safetensors Metadata Nondeterministic File sha256, A/B blind evaluation packaging (+6 more)

### Community 23 - "sys"
Cohesion: 0.20
Nodes (10): main(), process(), Path, Append ' \u06dd' (space + ARABIC END OF AYAH) to the aya/lyrics line of each…, argparse, hashlib, build_parser(), ArgumentParser (+2 more)

### Community 24 - "GCS organization plan — OSTRIS project (non-breaking)"
Cohesion: 0.09
Nodes (23): 10. Recommended immediate step (safe, today, additive only), 11. Implementation log — 2026-09-29, 1. Why this document exists, 2.1 Everything is a sibling of everything, 2.2 Our prefix root — 22 entries, no taxonomy, 2.3 `audiocpp_inference/` — a workspace acting as a run dir, 2.4 Sizes and object counts — the migration currency, 2. What is actually there (evidence) (+15 more)

### Community 25 - "abc_transcribe.py"
Cohesion: 0.25
Nodes (18): build_tracks(), collect_inputs(), command(), Config, find_abc(), log_tail(), main(), now() (+10 more)

### Community 26 - "test_status.py"
Cohesion: 0.12
Nodes (10): 0. Verified state this session, 1. The render — how it was launched (already running), 2. On my local machine — pull the run output (after it finishes), 3. Then — the verdict, 4. Pointers, current, _load(), fixture (+2 more)

### Community 27 - "status.py"
Cohesion: 0.28
Nodes (16): datetime, _age(), main(), _parse_ts(), _pgrep(), _pid_alive(), Path, status.py -- one deterministic read of this project's run state. The AGENTS.md… (+8 more)

### Community 28 - "Long-aya Quran pronunciation LoRA — runbook (canonical)"
Cohesion: 0.18
Nodes (11): Checkpoint-eval on a second (T4) VM — while training runs, Commands that matter, Docs, First GPU session only (kickstart; obsolete once a checkpoint exists), Long-aya Quran pronunciation LoRA — runbook (canonical), Progress log (append one row per session), Prompts to paste, Resume after a pause (+3 more)

### Community 29 - "time"
Cohesion: 0.18
Nodes (13): main(), plan(), Path, Cross-maqam lyric swap: one maqam's caption+tag with the other's held-out…, Resolve each track's inputs + auto cap without touching the GPU., wav_frames(), main(), Path (+5 more)

### Community 30 - "Working with the agent — experience checklist"
Cohesion: 0.25
Nodes (7): 1. The gut read, 2. Score the experience (1 = bad, 5 = great), 3. Pitfalls I hit (tick what's true), 4. Moments, 5. The one thing, 6. Hand this to the agent (copy + fill), Working with the agent — experience checklist

### Community 31 - "Held-Out Maqam Evaluation Set"
Cohesion: 0.25
Nodes (8): Byte-Identity Proof (267/267), Step 5 Held-Out Checks, Held-Out Maqam Evaluation Set, Four Per-Maqam Picks, prepare_yue2_dataset_v2.py Build Functions, Run YAML Is Canonical Lyrics, Held-Out Samples YAML Block, Four Held-Out Lyric Prompts

### Community 32 - "sample_pron_dataset.py"
Cohesion: 0.46
Nodes (7): random, combos(), copy_file(), copy_split(), main(), Path, sample_pron_dataset.py ---------------------- Build a frozen random subsample…

### Community 33 - "test_run_batch_ok_then_skip_then_force_fail"
Cohesion: 0.25
Nodes (5): _make_run(), test_main_keyboard_interrupt(), test_materialize_writes_prompts_manifest_input(), test_run_batch_ok_then_skip_then_force_fail(), boom()

### Community 34 - "screen_summary.py"
Cohesion: 0.26
Nodes (14): ar_seconds(), expect_seconds(), frames_of(), log_field(), main(), Path, Duration of a PCM WAV via the stdlib (no deps)., Summarise a screen_arms.sh run: planned length per arm, no audio needed. Reads… (+6 more)

### Community 35 - "subprocess"
Cohesion: 0.40
Nodes (5): main(), poll(), gpu_logger.py -------------- AI Toolkit logs no GPU…, shutil, subprocess

### Community 36 - "User cheatsheet"
Cohesion: 0.15
Nodes (12): 0. Ground truth — always start here, 1. Sidecars (run these before a long job), 2. Fresh VM: repo + setup + auth, 3. Training: start / status / stop, 4. Monitor training, 5. Inference: stage LoRAs, then generate, 6. Backup now / verify / restore, 7. Pause for the night / resume next session (+4 more)

### Community 37 - "_songs_json"
Cohesion: 0.29
Nodes (4): _songs_json(), test_main_full_path_with_out_dir(), test_main_invalid_limit(), test_main_lora_overrides_plumbed()

### Community 38 - "graphify update ."
Cohesion: 0.33
Nodes (6): graphify-out/cache/ per-file extraction cache, Extraction cache keyed by version and prompt, graphify-out/manifest.json, Doc/paper semantic extraction assistant skill, Dated snapshot graphify-out/<YYYY-MM-DD>/, graphify update .

### Community 39 - "_Run"
Cohesion: 0.33
Nodes (5): Minimal stand-in for subprocess.CompletedProcess., _Run, test_gpu_info(), test_wait_vram_free_paths(), test_wav_duration()

### Community 40 - "Training analysis — `quran_long_aya_r8_s10` (long-aya Quran pronunciation LoRA, 10% subsample)"
Cohesion: 0.33
Nodes (6): Caveats, Loss trend (per 810-step decile), Next steps, Observations / flags, Run at a glance, Training analysis — `quran_long_aya_r8_s10` (long-aya Quran pronunciation LoRA, 10% subsample)

### Community 41 - "test_duration_cap.py"
Cohesion: 0.21
Nodes (9): runpy, _invoke_cli(), parametrize, Path, Unit tests for INFERENCE/duration_cap.py (GPU-free). The CLI `main()` is…, test_cli_default_quantile(), test_cli_empty_lyrics_uses_floor(), test_cli_explicit_quantile() (+1 more)

### Community 43 - "_stub_assets"
Cohesion: 0.40
Nodes (5): _stub_assets(), test_preflight_checks_every_registered_pair(), test_preflight_not_executable_binary(), test_preflight_refuses_active_training_and_gpu_check(), test_preflight_success()

### Community 44 - "v2 Training Analysis — akbar_arabic_rock_lora"
Cohesion: 0.40
Nodes (5): v2 Training Analysis — akbar_arabic_rock_lora, Lower loss/ar_ce Is Mechanism, Not Quality, pron Run A100 Data/CPU-Bound, pron_lora_ar_only_r8 Training Analysis, v1 No-Lyrics Training Analysis (Archived)

### Community 45 - "json"
Cohesion: 0.24
Nodes (8): csv, collect(), main(), now(), Path, Batch audio -> melody ABC with the official Python SheetSage2 (cover front…, json, Pattern

### Community 46 - "pron_knob_probe.sh"
Cohesion: 0.83
Nodes (3): emit_sidecar(), opts_for(), pron_knob_probe.sh script

### Community 47 - "regenerate.sh"
Cohesion: 1.00
Nodes (3): fetch(), regenerate.sh script, sha256_of()

### Community 48 - "graphify.serve MCP server"
Cohesion: 0.67
Nodes (3): graphify-out/graph.json, graphify-out/.graphify_python VM-specific interpreter, graphify.serve MCP server

### Community 50 - "test_batch.sh"
Cohesion: 0.44
Nodes (8): abc(), _abc_one(), cap_for(), _knob_one(), knobs(), preflight(), run(), test_batch.sh script

### Community 51 - "parametrize"
Cohesion: 0.67
Nodes (3): parametrize, test_cap_parity_with_duration_cap_cli(), test_validation_errors()

### Community 65 - "setup.sh"
Cohesion: 0.11
Nodes (7): confirm_hf(), job_vm_continuity(), setup.sh script, start_continuity_loop(), start_job(), usage(), ext_root_secrets_env

### Community 68 - "v2_abc_to_qfinal.sh"
Cohesion: 0.46
Nodes (6): _gen(), one(), phase1_export_v2_score(), preflight(), v2_abc_to_qfinal.sh script, stage()

### Community 69 - "screen_arms.sh"
Cohesion: 0.57
Nodes (6): abc(), cap_for(), core(), preflight(), _screen_one(), screen_arms.sh script

## Knowledge Gaps
- **162 isolated node(s):** `pron_alpha_sweep.sh script`, `pron_fine_sweep.sh script`, `run_one.sh script`, `github_auth.sh script`, `Run at a glance` (+157 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 408 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **21 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Check how training is going` connect `DECISIONS.md` to `subprocess`, `generate_plots.py`?**
  _High betweenness centrality (0.207) - this node is a cross-community bridge._
- **Why does `docs/README.md index` connect `DECISIONS.md` to `User cheatsheet`, `Running a LoRA on the Yue2-3B GGUF Model: Findings`, `Building audiocpp_cli for a Specific GPU from a CPU-only Colab Runtime`, `Music cover / guide-conditioned generation — feasibility`, `Working with the agent — experience checklist`?**
  _High betweenness centrality (0.117) - this node is a cross-community bridge._
- **What connects `pron_alpha_sweep.sh script`, `pron_fine_sweep.sh script`, `run_one.sh script` to the rest of the system?**
  _162 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `DECISIONS.md` be split into smaller, more focused modules?**
  _Cohesion score 0.054840416152354084 - nodes in this community are weakly interconnected._
- **Should `generate.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07629107981220658 - nodes in this community are weakly interconnected._
- **Should `test_backup_to_gcp.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1025974025974026 - nodes in this community are weakly interconnected._
- **Should `test_merge_pron_lora.py` be split into smaller, more focused modules?**
  _Cohesion score 0.0663265306122449 - nodes in this community are weakly interconnected._