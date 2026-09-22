# Building `audiocpp_cli` for a specific GPU from a CPU-only Colab runtime

How to build `audio.cpp`'s CUDA `audiocpp_cli` for a chosen target GPU on a
CPU/High-RAM Colab runtime (no GPU attached), persist it per-architecture, and
verify it. For *why* the prebuilt-binary path exists at all, see `../DECISIONS.md`
(the `audiocpp_gguf_test/ renamed to audiocpp_inference/` entry); this doc is the
repeatable procedure.

## Why a CPU runtime can build a CUDA binary

`nvcc` cross-compiles device code for a named compute capability without a GPU
present. Compiling needs only the toolkit (`nvcc`, headers, `cudart`) — it is
*running* the result that needs a real CUDA device. So a CPU/High-RAM VM is a
valid build host; it is not a valid run host.

Consequences:

- Pass an explicit `--cuda-arch <CC>`. Do **not** use `--cuda-arch native` on a
  CPU VM — `native` resolves the arch from the local GPU
  (`CMakeLists.txt`, `CMAKE_CUDA_ARCHITECTURES_NATIVE`), and there is none.
- The CUDA path of `scripts/build_linux.sh` probes nothing GPU-specific when the
  arch is explicit; it just sets `-DCMAKE_CUDA_ARCHITECTURES=<CC>`.

## Prerequisites

- `nvidia-cuda-toolkit` installed (`nvcc`, release 12.0 here) — see the
  `DECISIONS.md` note that Colab's default image ships no CUDA toolkit.
- `ccache` installed. `scripts/build_linux.sh --ccache` hard-fails if the binary
  is missing (`build_linux.sh`: prints `--ccache was passed but ccache is not
  installed` and exits 1). `bootstrap/setup.sh --inference` installs it.
- `audio.cpp` cloned (bootstrap does the clone; it never builds).

## Build command template

Run from the `audio.cpp` checkout:

```bash
scripts/build_linux.sh --backend cuda --cuda-arch <CC> --ccache \
  --model-set custom --models yue2 \
  --target audiocpp_cli
```

Flag rationale (all first-party; see `../DECISIONS.md`'s `--model-set full` entry):

| Flag | Why |
|---|---|
| `--backend cuda` | CUDA target. Mutually exclusive with Vulkan/HIP in this script. |
| `--cuda-arch <CC>` | Compile for one compute capability (SASS + PTX, see below) instead of the portable multi-arch default. |
| `--ccache` | Routes C/C++/CUDA compilation through `ccache`. A cold build is about as slow; rebuilds are far faster. |
| `--model-set custom --models yue2` | Compiles only the `yue2` family. The default (`full`) builds all 80+ families and was the real ~30-minute cost, not something to cache around. |
| `--target audiocpp_cli` | Builds only the CLI, not every tool/server target. |

Build dir is `build/linux-<backend>-<buildtype>` (RelWithDebInfo maps to
`release`), so the output is:

```
build/linux-cuda-release/bin/audiocpp_cli
```

## Compute capabilities for the GPUs this project uses

| GPU | Compute capability | `--cuda-arch` | Suggested arch-tag |
|---|---|---|---|
| Tesla T4 | 7.5 | `75` | `sm75-t4` |
| A100 | 8.0 | `80` | `sm80-a100` |
| L4 | 8.9 | `89` | `sm89-l4` |

These CCs all appear in `CMakeLists.txt`'s default architecture list
(`CMakeLists.txt`, the `# Define default CUDA architectures` block, ~lines
220–261), which is the authoritative source for values, not this table: with
CUDA 12.0 the portable default is

```
50-virtual 61-virtual 70-virtual 75-real 80-virtual 86-real 89-real 90-virtual
```

(the `50/61/70` entries are dropped on CUDA ≥ 13; `120a`/`121a` are added on
CUDA ≥ 12.8/12.9). In that list `-real` = SASS (runs natively only on that CC)
and `-virtual` = PTX (JIT, forward-compatible).

## SASS vs PTX: what `--cuda-arch <N>` actually embeds (verified, not assumed)

`build_linux.sh` sets `-DCMAKE_CUDA_ARCHITECTURES=<N>` for a plain `--cuda-arch N`.
CMake treats an **unadorned integer as both real and virtual**, so the generated
`nvcc` flag is:

```
--generate-code=arch=compute_75,code=[compute_75,sm_75]
```

Verified directly from the arch-75 build (`build/linux-cuda-release/CMakeFiles`
`flags.make`), and confirmed in the linked binary with `cuobjdump`:

```
$ cuobjdump -lelf bin/audiocpp_cli | head    # SASS (native cubins)
ELF file 1: ..._0.sm_75.cubin
...
$ cuobjdump -lptx bin/audiocpp_cli | head     # PTX (JIT source)
PTX file 1: ..._1.sm_75.ptx
...
```

So a bare `--cuda-arch N` is **not** SASS-only: it embeds SASS for compute
capability N *and* PTX for compute capability N.

**What that means in practice — do not rely on cross-CC compatibility:**

- The **SASS** cubins are tied to exactly CC N. A `--cuda-arch 75` binary's SASS
  runs natively only on sm_75, not on sm_80 or sm_89.
- The embedded **PTX** is `compute_75`, which a newer driver *may* JIT to a
  different CC at load time (PTX is forward-compatible). That is a possible
  fallback, not a guarantee: it is untested here, adds first-load JIT cost, and
  cannot be assumed. **Treat each target GPU as needing its own build.** The T4
  binary is not "the L4 binary with a fallback"; build `--cuda-arch 89` for L4.

The alternative to a per-GPU arch is to drop `--cuda-arch` entirely and take
CMake's portable multi-arch default above: one binary covering several CCs, at
the cost of compiling every `.cu` file once per architecture (materially slower
cold builds). This project uses per-GPU, single-arch builds instead — smaller,
faster, and explicit about which GPU it targets.

## GCS staging convention (per-arch)

```
$GCP_BACKUP_BASE/audiocpp_inference/build/<arch-tag>/audiocpp_cli
```

with `<arch-tag>` = `sm<CC>-<gpu>`, e.g. `sm75-t4`, `sm80-a100`, `sm89-l4`:

```bash
gsutil cp /content/audio.cpp/build/linux-cuda-release/bin/audiocpp_cli \
  "$GCP_BACKUP_BASE/audiocpp_inference/build/sm89-l4/audiocpp_cli"
```

Note: the existing T4 binary lives at the *flat* path
`.../audiocpp_inference/build/audiocpp_cli` (predates this convention), and
`bootstrap/setup.sh`'s `job_audiocpp_binary` currently pulls only that flat path.
Auto-selecting the arch subdir for whatever GPU a live VM has is **not designed
yet** — that is a separate task. Until then, stage per-arch copies and fetch the
right one by hand.

## Verifying a build

1. **Exit code 0** from the build script.
2. **Binary exists, plausible size:**
   `ls -la build/linux-cuda-release/bin/audiocpp_cli` (~334 MiB / 350,161,824 B
   for the T4 build — it carries debug info and is not stripped).
3. **Expected CUDA libs** are linked: `ldd` should show `libcublas.so.12`,
   `libcuda.so.1`, `libcudart.so.12`, `libcublasLt.so.12` (plus `libgomp`,
   `libstdc++`, `libm`, `libgcc_s`, `libc`, `librt`, `libpthread`, `libdl`).
   `libnvrtc` is *not* in `ldd` (loaded dynamically at runtime).
4. **The right arch is inside:** `cuobjdump -lelf` should list `.sm_<CC>.cubin`
   and `cuobjdump -lptx` should list `.sm_<CC>.ptx`.

**Steps 1–4 only prove it *compiled* for that arch — not that it *runs*.** Running
needs the actual target GPU and is a separate check: a smoke run of
`audiocpp_cli --version` (or a real generation via `INFERENCE/run_one.sh`) on the
target hardware. Compiling and running are independently verified; do not let one
stand in for the other.

## Worked example (T4, sm_75)

The T4 path is the worked example for this whole procedure.

- **Build** (CPU/High-RAM runtime, 8 cores, CUDA 12.0, `nvidia-cuda-toolkit`):
  ```
  scripts/build_linux.sh --backend cuda --cuda-arch 75 --ccache \
    --model-set custom --models yue2 --target audiocpp_cli
  ```
  exit 0; `real 21m20.226s` (user 128m37s, sys 5m34s). Full log:
  `/content/logs/audiocpp_build.log`.
- **Artifact:** `build/linux-cuda-release/bin/audiocpp_cli`, ELF 64-bit, not
  stripped, **350,161,824 bytes**; `ldd` shows the CUDA libs listed above.
- **Persisted:** `$GCP_BACKUP_BASE/audiocpp_inference/build/audiocpp_cli`
  (the flat path; `job_audiocpp_binary` pulls it on `--inference`).
- **Run proof (live T4):** the persisted CPU-runtime-built sm75 binary is
  proven end-to-end on a live T4. On 2026-09-22 `bootstrap/setup.sh --inference`
  staged exactly this binary (`job_audiocpp_binary` pulls the flat GCS path) and
  `INFERENCE/run_one.sh` generated **all four held-out maqams, seed 1, exit 0**
  (real 48 kHz stereo WAVs, 216–240 s each) — `../PROGRESS.md`, "First T4
  inference run". Earlier T4 runs (2026-09-21, `audio.cpp` @ `e3de8e3`) proved
  the LoRA/attention path; the 2026-09-22 run proves the CPU-built persisted
  binary itself runs. See also `../DECISIONS.md`'s *"T4 VRAM is governed by the
  attention kernel..."* and *"T4 `auto` picking eager attention..."* entries.
  - Still worth a one-line `audiocpp_cli --version` smoke check per *new* build
    (e.g. each new arch), since only the sm75 artifact has been run so far.

## Known dead ends / open items

- `bypassing build_linux.sh` (plain cmake) has been *suggested* but not tested;
  the scoped `build_linux.sh` invocation above is the verified path.
- `--cuda-arch native` requires a GPU; not usable on the CPU build host.
- Auto-selecting the per-arch GCS subdir from the live GPU's compute capability
  is not implemented (see the staging section).
