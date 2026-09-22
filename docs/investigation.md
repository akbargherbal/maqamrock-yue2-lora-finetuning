# Getting `setup.sh --inference` to "ready to run" in ≤10 min, every session

> **SUPERSEDED (2026-09-22).** The recommendation below — persist `ccache`, "prefer
> ccache over a prebuilt binary" — was **not** adopted. The shipped path is a
> prebuilt `audiocpp_cli` staged by `bootstrap/setup.sh`'s `job_audiocpp_binary`
> (see `docs/INFERENCE.md` and `docs/audiocpp_gpu_arch_builds.md`). The `run_one.sh`
> path/model bugs it lists were fixed in the same commit that added this file, and
> its `/content/audiocpp_test` paths are pre-rename. Kept for the investigation
> record only — do not follow it. See `docs/IMPROVEMENTS.md` item 5.

Investigation only — no execution beyond read-only checks; no scripts changed,
nothing built or pushed. This document is the recommendation for review.

**Question:** what would it take to get `bootstrap/setup.sh --inference` from a
completely fresh Colab VM to "ready to run `audiocpp_cli` inference with the
converted LoRA" in 10 minutes or less, *every* session? Tooling/caching
question only — GPU choice and inference speed are out of scope.

---

## Recommendation (TL;DR)

**Persist the `ccache` directory to GCS (the approach already proposed in
`DECISIONS.md`), not a prebuilt binary.** ccache is small, matches the
project's existing persist-to-GCS pattern, and fails *soft* (a cache miss
costs a rebuild). A prebuilt `audiocpp_cli` has no upstream release to
consume, hard-codes an absolute CUDA-toolkit path, and fails *hard* across a
Colab image rollover.

Estimated critical path: **~4–7 minutes**, clearing 10 with margin — provided
the cache is populated with the *exact* flags it is later rebuilt with.

---

## 1. Does the arithmetic clear 10 minutes? Yes.

Measured on this VM (a fresh T4, driver 580.82.07, CUDA 12.8.93, 8 cores):

| Item | Measured / derived | Notes |
|---|---|---|
| ccache dir once populated | **159 MB on disk** (205 MiB ccache-counted), 406 entries, 812 files | `ccache -s` + `du`; cache dir `/root/.cache/ccache` |
| GCS pull of ccache | **~3–6 s** at measured ~50 MB/s, plus per-file overhead for 812 small files → realistically **≤40 s** | measured: 133 MiB of converter assets via `gsutil -m cp` in 2.7 s |
| Warm rebuild | cold 25–30 min (given); upstream's own script claims **~14×** (`scripts/build_linux.sh:406-408`) → ~1.8–2.1 min compile, + ~20 s configure, + ~30–60 s link of the 212 MB binary → **~2.5–4 min** | 406 objects / 0.60 GiB of `.o` rewritten at 1.2 GB/s here |
| GGUF download | bf16 7.26 GB + VAE 0.27 GB landed **6–23 s** after setup start → ~315 MB/s | runs **in parallel** with the build, so off the critical path |
| audio.cpp clone | 113 MB `.git` → ~15–45 s | parallel |

Critical path ≈ `ccache pull (≤40 s) + warm build (2.5–4 min)` ≈ **3–5 min**,
plus setup overhead. Even a pessimistic 6-min build clears.

**Caveat:** if the cache misses (Colab compiler/toolkit change), you are back
to a 19–30 min cold build. The build must therefore be a hard, verified step —
a silent miss blows the target.

---

## 2. Prebuilt binary: riskier, and there is no upstream CLI to use

- **Upstream only ships the server, not the CLI.** Downloaded and inspected
  `audio-v0.8.1-bin-ubuntu-x64-cuda12.8-colab.tar.gz` (63.9 MB): it contains
  `audiocpp_server` (109 MB) at the root and `tools/audiocpp_cli/` *scripts* —
  no `audiocpp_cli` binary. Upstream's own Colab notebook
  (`Notebooks/colab_audio_cpp.ipynb:71,199`) fetches that artifact and runs
  `audiocpp_server`. So `DECISIONS.md`'s "no Ubuntu+CUDA prebuilt" is now
  half-stale — a Colab artifact exists, but it cannot satisfy "ready to run
  `audiocpp_cli`".
- **Upstream treats it as experimental:** `release.yml:245-312`
  (`linux-cuda-colab`) builds **server only**, sets `continue-on-error: true`,
  and is **omitted from the release job's success gate**
  (`release.yml:596-612`); the README prebuilt table (`README.md:200-213`)
  lists only Windows CUDA + Ubuntu CPU/Vulkan + macOS.
- **ABI/toolkit risk is real.** The built binary's RUNPATH is the absolute
  `/usr/local/cuda-12.8/targets/x86_64-linux/lib`, and it needs
  `libcudart.so.12`, `libcublas.so.12`, `libcublasLt.so.12`, `libnccl.so.2`.
  The *driver* is fine — this VM is 580.82.07, well above the CUDA-12.x
  minor-version-compatibility floor (~525). But Colab's FAQ explicitly says
  GPU/resource types are not guaranteed and vary over time, and publishes no
  driver/toolkit pin. A Colab image bump to 12.9/13.x removes that path and
  the binary fails **hard**, with no fallback.
- Building and persisting our *own* `audiocpp_cli` would also require
  bundling/versioning the CUDA runtime and maintaining a per-commit binary
  artifact — new infrastructure, and exactly the kind of scheme
  `DECISIONS.md` said to avoid.

**Conclusion:** ccache fails *soft* (rebuild); prebuilt fails *hard*. Prefer
ccache.

---

## 3. GCS conventions to match

- Base is runtime-supplied, never hardcoded:
  `GCP_BACKUP_BASE = gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning`
  (exported by the notebook; `setup.sh:87-93`, `backup_to_gcp.py:51-56`).
- Convention: one prefix per run/purpose + `run_manifest.json`;
  `gsutil -m rsync` append/update-only; `dataset/` is reserved
  (`backup_to_gcp.py:58`). The inference harness already mirrors to
  `audiocpp_gguf_test/{converter,scripts,prompts,out,logs,agent_notes}` via
  `audiocpp_test/scripts/backup_live.py`.
- **Proposed:** a reserved prefix `<base>/build_cache/audio_cpp/` holding the
  ccache tree plus a small `manifest.json` (audio.cpp commit, `--cuda-arch`,
  exact flags, `ccache --version`, CUDA suite). Pull with
  `gsutil -m rsync -r` in `setup.sh` (matches the existing pattern); a
  `ccache.tar.zst` is an option only if 812-small-file overhead proves slow.
  Add `build_cache` to `backup_to_gcp.py`'s `RESERVED_SUBFOLDERS` so no run
  can collide with it.

---

## 4. Other `--inference` friction worth folding in (stayed scoped)

1. **`setup.sh` never builds** — it deliberately stops at clone
   (`setup.sh:185-202,335-348`). To hit the target, `--inference` must pull
   ccache → build → verify.
2. **Sidecars are missing.** yue2 requires `sidecars/yue2-model-config.json`,
   `yue2-generation-config.json`, `yue2-qwen.tiktoken`,
   `yue2-vae-config.json` (`docs/models/yue2.md`). `setup.sh:196-202`
   downloads only the two `.gguf`, so a fresh VM would fail to load.
3. **No model dir layout.** `audiocpp_cli --model <dir>` needs the ggufs +
   `sidecars/` alongside; setup only warms the HF cache. Stage a dir/symlink.
4. **Converted LoRA isn't pulled.** It is 133 MiB at
   `audiocpp_gguf_test/converter/`; "ready to run with the converted LoRA"
   requires pulling it.
5. **`run_one.sh` has a broken path** — it points at
   `/content/audiocpp_test/audio.cpp/build/...` (`run_one.sh:17`) but the
   build lands in `/content/audio.cpp/build/...` (that dir does not exist).
6. **Model mismatch:** `run_one.sh` uses `q8_0` (4.26 GB) while setup
   pre-warms bf16 (7.26 GB); `DECISIONS.md` recommends bf16 for LoRA merges.
   Align.
7. **ccache hardening (important for "every session"):** populate with
   `--native-cpu OFF` (upstream's own Colab build does
   `-DENGINE_ENABLE_NATIVE_CPU=OFF`; with the default, `-march=native` is a
   literal in the cache key, so a cross-VM cache hit could return
   host-specific code) and set `CCACHE_COMPILERCHECK=content` before
   populating (the default `mtime` invalidates entries whenever Colab
   re-materializes the same compiler with new mtimes). Also set `CCACHE_DIR`
   explicitly and raise `CCACHE_MAXSIZE`.

---

## Concrete `setup.sh --inference` shape (design only)

```bash
CCACHE_DIR=/root/.cache/ccache CCACHE_COMPILERCHECK=content CCACHE_MAXSIZE=10G
# parallel: clone audio.cpp, apt-get install ccache, pull GGUF + sidecars,
#           pull ccache tree from <base>/build_cache/audio_cpp/, pull LoRA
# then, sequenced after clone + ccache:
cd /content/audio.cpp
scripts/build_linux.sh --backend cuda --cuda-arch 75 --ccache --native-cpu OFF \
  --model-set custom --models yue2 --target audiocpp_cli
# verify: bin/audiocpp_cli exists; run --version/--list-devices; print ccache -s
```

**One-time population:** run the above on a fresh VM to fill ccache, then
`gsutil -m rsync -r /root/.cache/ccache <base>/build_cache/audio_cpp/ccache`
and write the manifest. Note the existing 159 MB cache was built with
`--native-cpu ON`, so it does **not** match the hardened flags — the hardened
cache needs one cold population first.

---

## Honest tradeoffs

- **ccache:** graceful, commit-agnostic, tiny, on-pattern. But the 10-min
  guarantee holds only for the common case; a Colab image/compiler change
  forces a re-population (one ~20–30 min build) and depends on flags staying
  byte-identical between populate and rebuild.
- **Prebuilt:** fastest pull, but tied to an absolute toolkit path + a
  per-commit artifact, no upstream CLI, and a hard failure mode. Not
  recommended as primary.
- **Hybrid** (ccache primary + cached binary gated by a `ldd`/`--version`
  check) buys speed at the cost of more moving parts; worth revisiting only
  if a measured warm rebuild + pulls exceed 10 min.
