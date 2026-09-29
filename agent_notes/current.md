# current

_Updated 2026-09-29. **Next session = Colab.** We finished on the local machine: the
guide-conditioned batch is written, `bash -n` + `--dry-run` checked, and the bucket
inventory is verified read-only. Read this first on the Colab VM, then run §3. Durable
analysis is `docs/music-cover-feasibility.md` **§11** (inventory, guide options, risks) and
**§10** (last round's verdict). Branch `music-cover`._

## 0. TL;DR

- **Goal:** test whether v2's plan (exported as `score.abc`) can steer **`qfinal_a0.3`**
  into v2's maqamrock arrangement **without losing** qfinal's pronunciation.
- **Driver:** `INFERENCE/v2_abc_to_qfinal.sh` — 4 arms, one track/seed. Verified: `bash -n`
  clean, `--dry-run` plan correct, `--stage` pulls `qfinal_a0.3`.
- **Everything needed is in GCS** (verified 2026-09-29) **except** v2's own `cot=full`
  `score.abc` — phase 1 of the driver generates it. (The pre-existing SheetSage2 ABC can be
  used instead; see §3 note.)
- **Not run yet** — needs a Colab GPU. This box is localhost: no `nvidia-smi`, no `/content`.

## 1. Where we are (what changed just before this)

- The **verbatim / lyric-adherence blind round is scored and recorded** —
  `docs/music-cover-feasibility.md` §10. Result: **no repeats in any arm**; quality
  **B ≥ A > C > D > E** (B = baseline+`110 BPM`; D = the "winning" prompt, 4th; E bare tags,
  last). Commit `e284052`.
- Deleted the stale `manifests/evaluation_verbatim_hijaz/KEY.json`; normalized the manifest
  text files CRLF→LF.
- Wrote `INFERENCE/v2_abc_to_qfinal.sh` and verified the bucket (see §2).

## 2. Verified assets (`gsutil ls`, bucket read-only, 2026-09-29)

Base = `gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning`

| asset | path (under base) | note |
|---|---|---|
| candidate adapter | `loras/audio_cpp/pron/qfinal_a0.3/akbar_arabic_rock_lora_{ar,nar}.safetensors` | AR rank 40; AR sha256 `0169e5a0…` |
| v2 style pair | `loras/audio_cpp/style/…` | staged by bootstrap |
| guide ABC (B2) | `audiocpp_inference/workspace/out/abc_v2/01-نسيب…_4148240095/score.abc` | + `chords.mid`, `melody_vocal.mid`, `tokens.json` |
| 11 more v2 ABCs | `…/workspace/out/abc_v2/` | 12 dirs total |
| guide WAV | `…/workspace/out/batch_36_songs/01-نسيب…_4148240095.wav` | B2 source / reference |
| today's 5 arms | `…/workspace/out/verbatim_hijaz_seed4148240095/*.wav` | re-listenable |
| pinned tooling | `audiocpp_inference/tools/{build,converter,prompts,scripts}` | |
| **not stored** | v2's own `cot=full` `score.abc` | phase 1 generates it |

Prompt/lyrics are in-repo: `manifests/test_verbatim_hijaz/styles/hijaz_winning.txt` (or
`hijaz_sunoblk.txt`) and `lyrics/01_nesib_as-is.txt`.

## 3. Commands (Colab GPU VM)

```bash
# 0) fresh VM: stage pinned tooling (model, binary, v2 style, prompts). Skip if done.
cd /content/maqamrock-yue2-lora-finetuning
git pull --ff-only                     # pick up this file + the driver (branch music-cover)
bash bootstrap/setup.sh --inference

# 1) GPU rule — confirm the card is free before any render (AGENTS.md §8)
nvidia-smi

# 2) stage the candidate adapter (bootstrap stages ONLY the style pair)
bash INFERENCE/v2_abc_to_qfinal.sh --stage

# 3) dry run — prints the plan, runs nothing
bash INFERENCE/v2_abc_to_qfinal.sh --dry-run

# 4) real run — DETACHED (survives Ctrl+C / closing the tab)
mkdir -p /content/logs
setsid nohup bash INFERENCE/v2_abc_to_qfinal.sh > /content/logs/v2abc.log 2>&1 & disown
#   watch:  tail -f /content/logs/v2abc.log
#   stop:   pkill -f 'v2_abc_to_qfinal.sh'     (re-runnable; overwrites its arms)
#   resume: re-run the same line

# 5) mirror the run
python3 backup_to_gcp.py --inference --once
```

**Use the existing SheetSage2 ABC (B2) instead of phase 1** — pull the guide dir and point
`ABC_SCORE=` at it (skips the v2 `cot=full` render):

```bash
gsutil -m cp -r "$BASE/audiocpp_inference/workspace/out/abc_v2/01-نسيب…_4148240095" \
  /content/audiocpp_inference/out/abc_v2/
ABC_SCORE=/content/audiocpp_inference/out/abc_v2/01-نسيب…_4148240095/score.abc \
  bash INFERENCE/v2_abc_to_qfinal.sh
```

## 4. The arms — and how to read them

One track (Hijaz, seed `4148240095`), style `hijaz_winning`, lyrics `01_nesib_as-is`.

| arm | adapter | cot / abc | question it answers |
|---|---|---|---|
| `a0_cotoff` | qfinal_a0.3 | `cot=off` | control (current qfinal) |
| `a1_cotfull_noabc` | qfinal_a0.3 | `cot=full` | how much is just the `cot` change |
| `a2_cotfull_abc` | qfinal_a0.3 | `cot=full` + `abc_file` | **the idea** |
| `ref_v2_cotoff` | v2 | `cot=off` | arrangement/pron reference |

Outputs under `/content/audiocpp_inference/out/v2_abc_to_qfinal_seed4148240095/`.

**Verdict:** `a0` vs `a2` — does `a2` keep v2's arrangement **without** losing
pronunciation? If `a2` pronounces like `ref_v2`, the AR-override conflict is real (§3/§11.3)
and only the blocked `semantic_prefix` route can thread it. If `a2 ≈ a0`, the guide did
nothing. Blind with `INFERENCE/prepare_ab_eval.py` (next unused blinding seed) for a fair
call; there is **no objective arrangement metric**.

## 5. Open questions / risks

1. **AR conflict** — the pron fix lives in the AR stream; any guide overrides it.
2. **Off-distribution** — adapters trained `cot=off`; `abc_file` forces `cot=melody|full`
   (hence `a1`).
3. **Melody ≠ arrangement** — stored ABCs are melody-only; only B1 (`score.abc`) or
   `semantic_prefix` carry chords/plan.
4. `semantic_prefix` — the more promising partial-prefix route — is **blocked**: our staged
   binary is < v0.8.2 (0 `semantic_prefix` hits). Needs a newer build.
5. Maqam match: guide ABC + prompt must both be Hijaz (don't pair with the Ajam winning
   prompt).

## 6. Pointers

- Feasibility: `docs/music-cover-feasibility.md` §11 (this batch) · §3 (α tradeoff) · §5
  (B1/B2) · §10 (last round).
- Adapters/identity: `docs/LORA_INVENTORY.md` (`qfinal_a0.3` row), `docs/PRON_LORA_MERGE.md`.
- Blind packaging: skill `ab-blind-eval`, `INFERENCE/prepare_ab_eval.py`.
- This file is a handoff surface, not authority — re-derive state from the artifacts/logs.
