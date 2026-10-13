# current.md — publish DONE (Phase A verified; Phase B scaffolded) — 2026-10-13

Copy/read surface only, **not authority**. Authority: `docs/PUBLISH_PLAN.md` (§9 = the
execution record) and `SOURCE_OF_TRUTH.md`.

## Done this session
- **Phase A (HF) — complete + verified.** Public model repos created and the weights
  round-trip-checked (`hf download` → sha256 equals the model card):
  - `akbargherbal/arabmaqamrock-yue2-lora` (v3 final) — AR `3531bb91…`, NAR `a7eabcad…`
  - `akbargherbal/quran-pronunciation-yue2-lora` (`quran_ahh_r32` final) — AR `c9305c35…`, NAR `2097fd6e…`
- **Phase B (lean repo) — scaffolded + committed locally** at `/tmp/opencode/lean-repo`
  (15 files; **MIT** code, CC-BY-NC-4.0 weights; zero GCS/`/content`/training references).
  Dry-run passes: `python3 generate.py songs.example.json --dry-run`.
- Parent repo wired (this commit): `README.md` "Published artifacts & downstream",
  `SOURCE_OF_TRUTH.md` rows, `docs/README.md`, `docs/PUBLISH_PLAN.md` §9, `RECONCILIATION_LOG.md`.

## Outstanding — you run these
1. **Create the new GitHub repo** (public, empty — no README/license) `akbargherbal/arabmaqamrock`,
   then push the local scaffold:
   ```bash
   cd /tmp/opencode/lean-repo
   git remote add origin https://github.com/akbargherbal/arabmaqamrock.git
   git push -u origin main
   ```
2. **Prebuilt T4 binary (optional release asset).** Build script is the default in `install.sh`;
   the verified **sm_75/T4** `audiocpp_cli` is in GCS
   `gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/audiocpp_inference/build/audiocpp_cli`
   (350,161,824 B) — attach it to the repo's first release as `audiocpp_cli.sm75-t4`.
3. **Fresh-VM generate acceptance test (the §6 gate, needs a GPU).** On a fresh GPU VM:
   ```bash
   git clone https://github.com/akbargherbal/arabmaqamrock.git && cd arabmaqamrock
   ./install.sh                                       # or ./install.sh --cuda-arch <CC>
   python3 generate.py songs.example.json --dry-run   # validate the plan, no GPU
   python3 generate.py songs.example.json             # real run → out/<ts>_songs-example/*.wav
   ```

## Security
- The HF token was accidentally printed into the chat by a broken masking regex earlier this
  session. **Revoke it** at https://huggingface.co/settings/tokens and store the replacement via
  `hf auth login` (→ `~/.cache/huggingface/token`), not in `~/.bashrc`.

## Environment (verified)
- localhost (no `/content`, no GPU). `hf` 2.2.0; `gcloud` works; `gh` absent (create the repo via web or install `gh`).
- Stored git credentials exist; `git push` to origin works.
