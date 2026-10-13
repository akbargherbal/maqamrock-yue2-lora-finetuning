# ArabMaqamRock — Colab-centric hardening plan

_Task: make the lean repo [`akbargherbal/arabmaqamrock`](https://github.com/akbargherbal/arabmaqamrock)
work on **ephemeral Colab**: a dedicated GCS prefix, arch-selected prebuilt binaries, and the GCP
backup scripts folded in._

Status: **IMPLEMENTED 2026-10-13.** Decisions in §3, result + verification in §7.

## 1. Why

The lean repo was extracted from this parent as "generation + production, no GCS"
(`docs/PUBLISH_PLAN.md` §4). In practice the workflow is **Colab-centric and ephemeral**:
`/content` is wiped on VM loss, so every fresh VM re-fetches the binary, model and LoRA, and
re-establishes auth. Two of those (the ~334 MiB CUDA binary and the ~7.5 GB GGUF) are pure
re-download cost, and the binary is the piece most likely to **break on drift** (§2).

This **reverses the earlier "no GCS references anywhere in the tree" rule** (`docs/PUBLISH_PLAN.md`
§6). That rule still holds for the *generation* path (running a track needs no credentials); GCS
becomes an explicit *plumbing/durability* layer — see the §7 corrections.

## 2. Grounding facts (verified)

| Fact | Where |
|---|---|
| Build procedure exists and is repeatable | `docs/audiocpp_gpu_arch_builds.md` |
| **Building needs no GPU** (`nvcc` cross-compiles for a named CC; only *running* needs a device) | same, §"Why a CPU runtime can build a CUDA binary" |
| Must pass explicit `--cuda-arch <CC>`; `native` needs a GPU | same, lines 18–22 |
| Build prereqs: `nvidia-cuda-toolkit` (nvcc) + `ccache`; T4 cold build `real 21m20.226s` | same, lines 24–31, 170 |
| CC table: T4 `75`→`sm75-t4`, A100 `80`→`sm80-a100`, L4 `89`→`sm89-l4` | same, lines 60–66 |
| Prebuilt is tied to an **audio.cpp commit**; audio.cpp is cloned **unpinned** (tracking main) | `bootstrap/setup.sh:621`, `bootstrap/setup.sh:386-398` |
| "Prebuilt fails *hard* (stale); ccache fails *soft* (rebuild)" | `docs/investigation.md` §2 |
| CUDA-13 image breaks the CUDA-12-linked binary (`exit=127`) | `docs/COMMAND_HANDOVER_GOTCHAS.md:117` |
| Existing binaries: sm_75 flat `audiocpp_inference/build/audiocpp_cli` (350,161,824 B); `build/sm89-l4/audiocpp_cli` (352,411,648 B). No `.sha256`; **no sm_80 build** | GCS listing 2026-10-13 |
| Backup machinery to port: append-only `gsutil rsync` + `run_manifest.json` + 5-min sidecar | `backup_to_gcp.py`, `docs/BACKUP_RESTORE.md` |

Config-free base: `GCP_BACKUP_BASE = gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning`
(runtime-supplied, never hardcoded — `backup_to_gcp.py:92`).

## 3. Decisions (settled 2026-10-13)

1. **GCS prefix** — a new dedicated `gs://akbar-december-2024-backup/arabmaqamrock/` **at the
   bucket root** (not nested under the project prefix `OSTRIS_Arabic_Suno_Finetuning/`), organised
   cleanly from scratch. Its bucket root is held in `GCP_ROOT`, separate from the parent's
   `GCP_BACKUP_BASE` (a project prefix), so exporting one never relocates the other.
2. **Folder name** — `plumbing/`.
3. **Binary source** — **GCS-first** (the author is the primary user; fastest path), with a
   build-from-source fallback so outsiders need no credentials. `install.sh` and `setup_colab.sh`
   both delegate to `plumbing/fetch_binary.sh`.
4. **Pin audio.cpp** — pin the commit per binary and record it in the manifest. No ccache build cache
   for now.
5. **GitHub release asset** — dropped; GCS holds the arch-selected binaries.
6. **Plan location** — this doc, in the parent `docs/`.

## 4. Design (as built)

### 4.1 GCS prefix layout

At the bucket root — `gs://akbar-december-2024-backup/arabmaqamrock/` (`$GCP_ROOT/arabmaqamrock`):

```
gs://akbar-december-2024-backup/arabmaqamrock/
  README.md                                what this prefix is + the layout
  binaries/<arch-tag>/audiocpp_cli         prebuilt CUDA CLI, arch-selected at fetch time
  binaries/<arch-tag>/audiocpp_cli.sha256  sha256 of the binary
  binaries/<arch-tag>/manifest.json        build provenance (audio.cpp commit, CUDA, flags)
  runs/<timestamp>_<label>/                mirrored from the repo's out/   (append-only)
  logs/                                    mirrored from the repo's logs/
  run_manifest.json                        written by plumbing/backup_to_gcp.py
```

`<arch-tag>` = `sm<CC>-<gpu>`. **Not backed up** (regenerable): the GGUF model and the LoRAs — both
come from Hugging Face.

### 4.2 Binary staging + arch auto-select

Closes the parent's open item ("auto-selecting the per-arch GCS subdir … is not designed yet",
`docs/INFERENCE.md:357`). `plumbing/fetch_binary.sh`:
1. `compute_cap` via `nvidia-smi` (or an explicit `--cuda-arch`) → arch tag;
2. `gcs_cp <prefix>/binaries/<tag>/audiocpp_cli` → `bin/audiocpp_cli`, **sha256-verified** against the
   published `.sha256`; the tag is recorded in `bin/.arch`;
3. on miss/mismatch, or with `--build`: build from source (`--cuda-arch <CC>`); `--publish` uploads the
   result + a fresh `.sha256` + `manifest.json`.

### 4.3 Backup

`plumbing/backup_to_gcp.py` — the parent's daemon, narrowed: `--run-name arabmaqamrock`, targets
repo-relative `out/`→`runs/` and `logs/`→`logs/` (no `/content`, no settle/sqlite handling). Same
append-only `gsutil rsync`, `run_manifest.json`, and CLI (`--once/--dry-run/--interval-minutes/
--watch/--extra/--base/--exclude`); sidecar via `setsid nohup … & disown`.

### 4.4 `plumbing/` contents

`README.md`, `env.sh` (base + `gcs_*` wrappers), `arch.sh`, `fetch_binary.sh`, `backup_to_gcp.py`,
`audio_cpp.pin`. (The planned `gcs.py` was dropped: the helpers are small enough for bash, and one
implementation is better than two.)

### 4.5 Colab entrypoint

`setup_colab.sh` — tooling checks, `fetch_binary.sh`, HF model + LoRA, start the backup sidecar. The
repo stays repo-root-relative (Colab clones it to `/content/arabmaqamrock`).

## 5. Work breakdown (all done)

1. ✅ Decisions settled (§3).
2. ✅ `<base>/arabmaqamrock/` created; sm_75 + sm_89 staged with `.sha256` + `manifest.json`.
3. ✅ `plumbing/` written.
4. ✅ `setup_colab.sh` added; `install.sh` rewired to `fetch_binary.sh`.
5. ✅ CPU-only smoke tests (below).
6. ✅ Parent docs reconciled (§7).
7. ✅ Lean repo committed + pushed.
8. ⏳ GPU acceptance on a fresh Colab VM — user-run.

## 6. Non-goals

- Rebuilding the GGUF or re-training anything.
- Making outside users depend on GCS; the public path stays HF + source build.
- Touching the parent's training pipeline.

## 7. Result — 2026-10-13

**GCS prefix created** at the bucket root — `gs://akbar-december-2024-backup/arabmaqamrock/`
(relocated from a first cut under the project prefix; old copy deleted, sizes matched) — binary
staged from the existing objects (server-side copy + re-hash):

| arch tag | sha256 | bytes |
|---|---|---|
| `sm75-t4` | `7ad69d1ccfe432b8c5e100009188b56013e48dc117ae391958b1000439caa93c` | 350,161,824 |
| `sm89-l4` | `97028a71fd4d86378161162364dc6cdc85a569461d3afb6bf78f83ea572ad3d4` | 352,411,648 |

Both manifests record `ggml_commit: eb8e21b`, `cuda_toolkit: 12.0.140`, and
`audio_cpp_commit: unknown` (the 2026-09-22 builds predate any pin — recorded honestly; future
`--publish` builds record it).

**Lean repo** `github.com/akbargherbal/arabmaqamrock` @ `6411d43`: `plumbing/` (6 files),
`setup_colab.sh`, `install.sh` rewired, README Colab section, `.gitignore` `logs/`.

**Verified, CPU-only (no GPU on this box):**
- `bash -n` on all shell scripts; `py_compile` on `backup_to_gcp.py` + `generate.py`.
- `fetch_binary.sh --cuda-arch 75` → real fetch from the prefix → **sha256 matched**
  (`7ad69d1c…`) → staged; a second run correctly skipped (idempotent).
- `backup_to_gcp.py --dry-run --once` → correct targets (`out/`→`runs/`, `logs/`→`logs/`), dry-run
  only.
- `generate.py songs.example.json --dry-run` → unchanged (regression pass).

**Not yet verified (needs a GPU / fresh VM):** `setup_colab.sh` end-to-end, a real generation, and a
backup pass landing in `runs/`.

**Corrections to earlier statements:**
- `docs/PUBLISH_PLAN.md` §4/§6 "no GCS references" is superseded: the generation path is still
  credential-free, but the repo now carries an explicit GCS plumbing layer.
- `SOURCE_OF_TRUTH.md`'s lean-repo row changed from "no training/GCS" to record the prefix + plumbing.
