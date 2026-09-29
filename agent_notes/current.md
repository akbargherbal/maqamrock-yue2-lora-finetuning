# current

_Updated 2026-09-29 (Colab VM). **Guide-conditioned batch rendered — 4/4 arms `exit=0`, no
truncation. Blind package built (blinding seed `20260931`) and mirrored; the evaluation
sheet is ready.** Next: listen blind, fill the sheet, then decode. Durable analysis:
`docs/music-cover-feasibility.md` **§11**. Branch `music-cover`._

## 0. Result (read from artifacts, not memory)

Render dir `/content/audiocpp_inference/out/v2_abc_to_qfinal_seed4148240095/` (all 48 kHz
stereo; `truncated 0` in every log):

| arm | cot / guide | adapter | dur | wall | wav bytes |
|---|---|---|---:|---:|---:|
| `a0_cotoff` | `cot=off` | qfinal_a0.3 | 256.8 s | 8:49 | 49 313 068 |
| `a1_cotfull_noabc` | `cot=full` | qfinal_a0.3 | 310.0 s | 10:31 | 59 519 788 |
| `a2_cotfull_abc` | `cot=full` + `abc_file` | qfinal_a0.3 | 282.2 s | 7:53 | 54 182 188 |
| `ref_v2_cotoff` | `cot=off` | v2 | 271.9 s | 8:59 | 52 208 428 |

- Phase 1 exported v2's `score.abc` (3275 B, sha256 `b08427f1…`); the a2 arm used it.
- `a1`'s 310.0 s coincides exactly with the auto cap (7750 tokens = 310 s) but the log
  reports `truncated 0` — flag it if it sounds cut off.
- Binary sha256 `7ad69d1c…` (sm_75 / T4).

## 1. Listen blind

- **Audio (GCS):** `listening/V2_ABC_TO_QFINAL_INPUT/` — `EVAL.txt`,
  `KEY_open_after_listening.txt`, `nesib_4148240095_{A,B,C,D}.mp3`.
- **Repo (text only):** `manifests/evaluation_v2_abc_to_qfinal/` — `EVAL.txt`, `KEYS.txt`
  (secret), `MY_EVALUATION.txt` (the sheet to fill).
- **Seed `20260931`.** Do **not** open the key until every section is scored. (The
  `20260930` shuffle was discarded after its mapping got printed — the lesson is now in
  `skills/ab-blind-eval/SKILL.md`.)

Pull the package to the local machine:

```bash
gsutil -m rsync -r 'gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/listening/V2_ABC_TO_QFINAL_INPUT' ./v2abc_blind
```

## 2. Then — the verdict

The crux is `a0` vs `a2`: does the guided arm keep v2's **arrangement** without losing
qfinal's **pronunciation**? If `a2` pronounces like `ref_v2`, the AR-override conflict is
real (§11.3) and only the blocked `semantic_prefix` route can thread it; if `a2 ≈ a0`, the
guide did nothing. `a1` isolates the bare `cot` effect. There is **no objective
arrangement metric** — this is a listening call (durations are the only mechanical
cross-check: the guided arm is *not* obviously longer/shorter).

## 3. Session side-work on the VM (non-GPU, done)

- **Docs reconcile** (`docs-reconciler`): restored the fixture deleted in `528f573`
  (`manifests/workspace_manifest.json`) — 10 tests were failing; now 17/17 pass. Also
  qualified `SOURCE_OF_TRUTH.md`'s `KEYS.txt` path and added 3 doc-scoped
  `unverifiable.txt` entries. Re-verify **11 → 1 flagged**. See `RECONCILIATION_LOG.md`.
- **Graph:** `graphify update .` → `status.py` reports **`graph: fresh at HEAD`**; semantic
  `/graphify --update` not run (no skill on this VM).
- **Backup daemon** running (`backup_to_gcp.py --inference`, 5-min passes); arms already on
  GCS under `audiocpp_inference/workspace/out/v2_abc_to_qfinal_seed4148240095/`.

## 4. Pointers

- Feasibility: `docs/music-cover-feasibility.md` §11 (this batch, §11.3 risks, §11.5
  verdict) · §10 (verbatim round) · §3 (α tradeoff) · §5 (B1/B2).
- Blind packaging: `skills/ab-blind-eval/SKILL.md`, `INFERENCE/prepare_ab_eval.py`.
- Adapters/identity: `docs/LORA_INVENTORY.md`, `docs/PRON_LORA_MERGE.md`; runbook
  `docs/INFERENCE.md`.
- This file is a handoff surface, not authority — re-derive state from the artifacts/logs.
