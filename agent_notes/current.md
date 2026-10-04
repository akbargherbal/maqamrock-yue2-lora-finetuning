# current

## Restore THIS session in another Colab notebook

Session id **`ses_ef89e8480ffejOR0B5sv6kKkO2`** ("Continuing session prep for next
GPU session"). Backed up by vm-continuity to
`gs://akbar-december-2024-backup/opencode_sessions/by_host/b847ef236a79/`
(DB snapshot 15,089,664 B, sha256 `8e6aaec2…`). Run on the **target** notebook:

terminal: mixed — `clone`/`pull` are long (network); `restore` is state-changing.

```bash
# 1. install vm-continuity (once per fresh VM)
git clone https://github.com/akbargherbal/vm-continuity.git /content/vm-continuity
bash /content/vm-continuity/install.sh

# 2. GCS auth (Colab)
python -c "from google.colab import auth; auth.authenticate_user()"

# 3. confirm our namespace, then pull it
vm-continuity hosts                          # expect by_host/b847ef236a79/
vm-continuity pull --host b847ef236a79

# 4. restore the DB — REPLACES the target's opencode DB (it is backed up to
#    opencode.db.bak-<ts> first, and the opencode service is stopped/restarted)
vm-continuity restore opencode -- --mode db

# 5. resume the conversation
opencode -s ses_ef89e8480ffejOR0B5sv6kKkO2
```

- Use **`--mode db` only.** `--mode export` is broken on this image: opencode
  1.18.34's `session` command has no `export`, so the per-session JSON is 0 bytes.
- `pull`/`restore` are per-tool; starting the backup loop on the target first is
  safe — each VM ships to its own `by_host/<host>/` namespace.
- After restore, re-run `opencode` from the repo dir (`cd /content/maqamrock-yue2-lora-finetuning`).

## State @ 2026-10-04 (CPU prep VM): Quran format/caption probe manifest READY

Branch `experimental-quran-pron`. This session was CPU-only discussion + prep.
Manifest: **`INFERENCE/songs.quran_format_probe.json`** (6 arms, dry-run clean).
Authority for the earlier finding: `docs/QURAN_ONLY_EXPERIMENT.md`.

### Confirmed cause of last session's early stop (from artifacts)

Training clips are a hardcoded 4-line template (`prepare_pron_dataset.py:210`,
`docs/PRON_LORA_LONG_PLAN.md:41`):
`<caption>\n[Lyrics]\n[Verse]\n<one aya> ۝`. Every file uses a **bare `[Verse]`**
and exactly **one aya** (e.g. `quran_long_aya_dataset/train/Abdul_Basit_*_002004_uthmani.txt`).
Inference builds `[Tags]\n<style>\n[Lyrics]\n<lyrics>` (`audio.cpp pipeline.cpp:22-30`),
so our last run fed `[Intro]`/`[Verse 1]`/`[Chorus]`/`[Outro]` — all never seen.
Result: it recited ~one verse then natural EOS (`truncated 0`). Not a cap issue.

### The 6-arm probe (why, not just numbers)

Question: **is the Quran-adapter's Arabic pronunciation high-fidelity, and can the
caption / the `۝` end-marker move it?** `۝` is treated as the *true-end* marker
(used once, at the very end). All arms: adapter `quran_only`, seed `20261004`,
cap `7500` (uniform, so EOS is the only intended stop), `--no-trigger`.

| # | lyrics | caption | tests |
|---|---|---|---|
| T1 | poem, single ` ۝` on last line | QURAN | does the true-end mark make it finish? |
| T2 | poem, no `۝` | QURAN | (vs T1) `۝` effect; (vs last session) tag fix |
| T3 | poem, single `۝` | NASHEED | caption → articulation |
| T4 | poem, single `۝` | KHALIJI TARAB | caption → articulation |
| T5 | poem, single `۝` | QASIDA | caption → articulation |
| T6 | Āyat al-Kursī (2:255, 58 w) + `۝` | QURAN | in-domain fidelity yardstick (open-source text) |

Poem = the song's 8 couplets (deduped, `...` stripped), single `[Verse]` header.
Captions are deliberately distinct, not one-word swaps. T6 aya sourced from the
open Quran API (`api.alquran.cloud/v1/ayah/2:255/quran-uthmani`), all hard letters
ح خ ع ق ط ض ظ present.

### Next-session prerequisites (GPU)

1. Stage the `quran_only` adapter (not GCS-mirrored; rebuild from the pron source —
   steps in `docs/QURAN_ONLY_EXPERIMENT.md`):
   `${GCP_BACKUP_BASE}/quran_long_aya_r8_s10/output/quran_long_aya_r8_s10.safetensors`
   → `build_pron_only_fused.py` → converter → `/content/converter/out/quran_only/`.
2. Export the CUDA-12 loader path (else the sm_75 CLI dies `exit=127`):
   ```bash
   export LD_LIBRARY_PATH="$(find /usr/local/lib/python3.13/dist-packages/nvidia \
     -maxdepth 2 -type d \( -name lib -o -name lib64 \) | tr '\n' ':')/usr/lib64-nvidia"
   ldd /content/audiocpp_inference/bin/audiocpp_cli | grep 'not found' || echo OK
   ```
3. Confirm GPU idle: `nvidia-smi`. Prereqs for backup sidecars per `AGENTS.md` §10.

### Run command — detached

terminal: detached — survives Ctrl+C / closing the tab.
log: `/content/logs/quran_format_probe.log`; stop: `pkill -f quran_format_probe`;
resume: re-run the same command (seeds/caps are fixed, so it reproduces; a partial
run just leaves a new timestamped `out/` dir — check `out/latest`).

```bash
cd /content/maqamrock-yue2-lora-finetuning
setsid nohup python INFERENCE/generate.py \
  INFERENCE/songs.quran_format_probe.json --no-trigger \
  --label quran_format_probe > /content/logs/quran_format_probe.log 2>&1 & disown
```

Progress: `tail -f /content/logs/quran_format_probe.log`; driver status in
`out/<ts>_quran_format_probe/_runs_status.log`. Projected worst case ~39 min on a
T4; short EOS stops will make it faster.

### After the runs

Package a blind A/B with the `ab-blind-eval` skill /
`INFERENCE/prepare_ab_eval.py` (new blinding seed). Judge the hard letters
(ح خ ع ق ط ض ظ) with the tashkeel text visible; `🔊` the prior control wav for a
floor. Reference: the 2026-10-04 run (`out/quran_only_sample/`, seed `20261004`).

### Durability caveat

`INFERENCE/songs.quran_format_probe.json` is **uncommitted** — a fresh GPU VM
(clone) will not have it. Commit+push, or `gsutil cp` it to
`${GCP_BACKUP_BASE}/audiocpp_inference/` before the VM resets.
