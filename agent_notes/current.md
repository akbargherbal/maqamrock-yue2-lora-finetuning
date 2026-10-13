# current.md — Colab hardening shipped — 2026-10-13

Copy/read surface only, **not authority**. Authority: `docs/COLAB_PLAN.md` (§7 = result),
`docs/PUBLISH_PLAN.md` (§9), `SOURCE_OF_TRUTH.md`.

## Done this session
- **Published (HF):** `akbargherbal/arabmaqamrock-yue2-lora` (v3 final) + `…/quran-pronunciation-yue2-lora`;
  `hf download` round-trip sha256 matches each model card.
- **Lean repo live:** `github.com/akbargherbal/arabmaqamrock` @ `6411d43` (public, MIT code, NC weights).
- **Colab hardening (new):** GCS prefix `…/OSTRIS_Arabic_Suno_Finetuning/arabmaqamrock/` with
  `binaries/{sm75-t4,sm89-l4}/` (binary + `.sha256` + `manifest.json`). The repo gains `plumbing/`
  (`fetch_binary.sh`, `backup_to_gcp.py`, `env.sh`, `arch.sh`, `audio_cpp.pin`, `README.md`) and
  `setup_colab.sh`; `install.sh` rewired to the shared fetch. `binaries/sm75-t4` sha256 =
  `7ad69d1c…`, `sm89-l4` = `97028a71…`.
- **Verified CPU-only:** fetch → sha256 round-trip; backup dry-run targets; generate dry-run. Details
  in `docs/COLAB_PLAN.md` §7.

## Outstanding
1. **Fresh-VM acceptance test (GPU).** On a Colab T4:
   ```bash
   git clone https://github.com/akbargherbal/arabmaqamrock.git /content/arabmaqamrock
   cd /content/arabmaqamrock
   gcloud auth login            # to read the prebuilt binary + write backups
   export HF_TOKEN=...          # (or: hf auth login)
   ./setup_colab.sh
   python3 generate.py songs.example.json --dry-run
   python3 generate.py songs.example.json
   ```
   Confirm a WAV under `out/…` and that `…/arabmaqamrock/runs/` gets the mirrored run.
2. **Pin audio.cpp** the next time a build is verified: put the commit in `plumbing/audio_cpp.pin`
   (the 2026-09-22 prebuilts record `audio_cpp_commit: unknown`).

## Notes
- A build needs **no GPU** (`nvcc` cross-compiles for `--cuda-arch <CC>`); ~21 min cold; needs the
  CUDA toolkit + cmake + ccache. See `docs/audiocpp_gpu_arch_builds.md` (parent).
