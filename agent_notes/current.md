# current

> **Session plan:** [`docs/QURAN_AHH_RESUME_PLAN.md`](../docs/QURAN_AHH_RESUME_PLAN.md) Phase 3b —
> T4 epoch test on Ayat al-Kursi (2:255) → blind A/B.
> **This file is a handoff copy surface, not a source of truth** — re-derive from live artifacts.

## State @ 2026-10-06 05:35 UTC — T4, **render running** (3/6); CUDA-12 loader fix committed

Fresh Colab **T4** (`COLAB_GPU=1`). Repo `pron-lora-long-aya`, HEAD **`72297f0`** (fix, below;
1 commit ahead of origin — **needs push**). `setup.sh --inference` done; probe arms staged
(`c4500 c7500 c9000 c10500 c16500 c19500 final`); `vm-continuity` loop `state=OK`.

### Done this session (CPU-only)
Converted **c9000 / c19500 / final** from the banked ai-toolkit checkpoints with the canonical
`convert_aitoolkit_yue2_lora.py` (`--stem quran_ahh_r8`; byte-level verified, rank 32) and banked
them to `…/quran_ahh_r8_rank32/convert/`. `adapter_manifest.json` updated additively
(old copy: `/tmp/opencode/adapter_manifest.backup.json`).

### Root-cause fix — CUDA-12 loader (`exit=127`), now encoded (commit `72297f0`)
Run #1 died instantly: all 6 tracks `exit=127`, 0:00, `libcublas.so.12: cannot open shared object
file`. Cause: the prebuilt sm_75 binary links **CUDA 12**; the image is **CUDA 13**; nothing set
the loader path. Fixed **in code**, not by hand:
- `INFERENCE/cuda_loader_path.sh` — self-healing, idempotent resolver for the pip `nvidia/*/lib` dirs.
- `INFERENCE/run_one.sh` sources it before `$BIN` (choke point for every `generate.py` / `*_sweep.sh` / `maqam_lyric_swap.py` run).
- `bootstrap/setup.sh --inference` resolves it, `pip install`s the `-cu12` wheels if absent, **fails the verify** if `ldd` still shows `not found`, and persists it in `~/.bashrc`.
- Docs marked "Encoded"; `RECONCILIATION_LOG.md` entry added.
- Verified: bare shell (`env -u LD_LIBRARY_PATH`) resolves; `--check` exit 0; idempotent; interactive shell resolves via `~/.bashrc`; `tests/test_generate.py test_duration_cap.py` = 69 passed.

### Render (live) — run dir `out/20261006-052626_quran_pt_probe/`
`setsid … quran_pt_probe.py --prefix quran_ahh_r8_rank32/convert --arms c9000,c19500,final`
→ 6 tracks `{c9000,c19500,final} × {uthmani,simple}`, seed 20261004, cap 7500.
log `/content/logs/quran_pt_probe_r32_epochs.log`; stop `pkill -f 'quran_pt_probe.py --prefix quran_ahh_r8_rank32'`.
(`out/20261006-051955_quran_pt_probe/` is the failed run #1 — empty, harmless.)

## After the render
Blind A/B (`ab-blind-eval`) over the 6 tracks → play → record the verdict in
`TRAINING_ANALYSIS/quran_ahh_r8_rank32/ANALYSIS.md`.

## Still open
- **Push `72297f0`** (VM is ephemeral; run `bash bootstrap/github_auth.sh`, then `git push`).
- Phase 3b listener verdict (above).
- Phase 5: rename `quran_ahh_r8` → `quran_ahh_r32`; docs-reconciler; blind gate before any merge.
- Two more *documented-but-not-encoded* durable fixes (same class, training-side — not done):
  restore helper that fixes ckpt ctime; backup daemon that `wal_checkpoint(TRUNCATE)`s `loss_log.db`.

## Gotchas
- **CUDA-12 loader path is now automatic** via `run_one.sh` + `setup.sh` (commit `72297f0`); the
  manual `export LD_LIBRARY_PATH=…` is only for ad-hoc `ldd`/direct-CLI use. `--dry-run` still
  does not exercise the loader, so use `INFERENCE/cuda_loader_path.sh --check <bin>` to preflight.
- `run.py -l <log>` **appends** — verify resume with `grep 'Found step' <log> | tail -1`.
- GCS restore randomizes ckpt ctime → auto-resume picks the wrong step; `chmod` (not `touch`) fixes it.
- The probe re-rsyncs the whole convert prefix (~980 MB) each run and exposes no `--out-dir`, so a
  failed render restarts in a fresh folder rather than resuming.
