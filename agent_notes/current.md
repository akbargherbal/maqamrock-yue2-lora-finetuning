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

## 1. Listen blind — the two prefixes are different

| what | GCS prefix | contents |
|---|---|---|
| **blinded package** (what you want) | `listening/V2_ABC_TO_QFINAL_INPUT/` | `EVAL.txt`, `KEY_open_after_listening.txt`, `nesib_4148240095_{A,B,C,D}.mp3` |
| raw render (not needed to listen) | `audiocpp_inference/workspace/out/v2_abc_to_qfinal_seed4148240095/` | 4 WAVs + logs + `score.abc` |

Repo text (committed, no audio): `manifests/evaluation_v2_abc_to_qfinal/` — `EVAL.txt`,
`KEYS.txt` (secret decoder), `MY_EVALUATION.txt` (the sheet to fill).

**Seed `20260931`.** Do **not** open the key until every section is scored. (The `20260930`
shuffle was discarded after its mapping got printed — lesson now in
`skills/ab-blind-eval/SKILL.md`.)

### Pull the blind package (Powershell)

```powershell
cd $HOME\Downloads
gsutil -m rsync -r 'gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/listening/V2_ABC_TO_QFINAL_INPUT' .\v2abc_blind
dir .\v2abc_blind
```

### Get the score sheet into your local clone (Powershell)

```powershell
cd C:\Users\DELL\Jupyter_Notebooks\maqamrock-yue2-lora-finetuning
git pull origin music-cover
```

Sheet to fill: `manifests\evaluation_v2_abc_to_qfinal\MY_EVALUATION.txt`.

### Regenerate it locally (optional — only if you want your own shuffle)

`prepare_ab_eval.py` needs `<root>/<variant>/<track>.<ext>`, so stage the four raw WAVs into
variant folders and pass a **fresh** seed (the committed `KEYS.txt` already owns
`20260931`). Powershell:

```powershell
$repo = "C:\Users\DELL\Jupyter_Notebooks\maqamrock-yue2-lora-finetuning"
$src  = "$HOME\Downloads\v2abc_tracks"
$root = "$HOME\Downloads\v2abc_root"
"a0_cotoff","a1_cotfull_noabc","a2_cotfull_abc","ref_v2_cotoff" | % { New-Item -ItemType Directory -Force -Path "$root\$_" | Out-Null }
Copy-Item "$src\a0_cotoff_hijaz_win_4148240095.wav"        "$root\a0_cotoff\nesib_4148240095.wav"
Copy-Item "$src\a1_cotfull_noabc_hijaz_win_4148240095.wav" "$root\a1_cotfull_noabc\nesib_4148240095.wav"
Copy-Item "$src\a2_cotfull_abc_hijaz_win_4148240095.wav"   "$root\a2_cotfull_abc\nesib_4148240095.wav"
Copy-Item "$src\ref_v2_cotoff_hijaz_win_4148240095.wav"    "$root\ref_v2_cotoff\nesib_4148240095.wav"
python "$repo\INFERENCE\prepare_ab_eval.py" --root "$root" --output "$HOME\Downloads\v2abc_blind" `
  --variants a0_cotoff a1_cotfull_noabc a2_cotfull_abc ref_v2_cotoff `
  --seed 20260932 --audio-format copy   # `--audio-format mp3 --bitrate 192k` needs ffmpeg
```

The tool prints the label→variant map on stdout — that **is** the decoder; don't read it
before scoring (redirect to a file to stay blind). `--audio-format copy` avoids needing
ffmpeg.

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
- **Graph:** `graphify update .` rebuilt the graph; it now reads a few commits behind again
  (the 4 commits after the build are docs/notes/eval text only, no code). Semantic
  `/graphify --update` not run (no skill on this VM).
- **Backup daemon** running (`backup_to_gcp.py --inference`, 5-min passes; 5/5 folders);
  arms already on GCS under `audiocpp_inference/workspace/out/v2_abc_to_qfinal_seed4148240095/`.

## 4. Pointers

- Feasibility: `docs/music-cover-feasibility.md` §11 (this batch, §11.3 risks, §11.5
  verdict) · §10 (verbatim round) · §3 (α tradeoff) · §5 (B1/B2).
- Blind packaging: `skills/ab-blind-eval/SKILL.md`, `INFERENCE/prepare_ab_eval.py`.
- Adapters/identity: `docs/LORA_INVENTORY.md`, `docs/PRON_LORA_MERGE.md`; runbook
  `docs/INFERENCE.md`.
- This file is a handoff surface, not authority — re-derive state from the artifacts/logs.
