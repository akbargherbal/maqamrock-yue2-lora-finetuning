# current

_Updated 2026-09-29 (local). **Guide-conditioned round scored + decoded — the idea works:
`a2` (`qfinal_a0.3` `cot=full` + v2's `score.abc`) wins arrangement AND pronunciation, and
beats the `cot=full`-no-plan arm (`a1`) decisively.** Recorded in
`docs/music-cover-feasibility.md` **§7**; authority
`manifests/evaluation_v2_abc_to_qfinal/MY_EVALUATION.txt` (+ `KEYS.txt`). Next: replicate on
the other two seeds. Branch `music-cover`._

## 0. Verdict (decoded vs `KEYS.txt`, blinding seed `20260932`)

| | A `ref_v2_cotoff` | B `a0_cotoff` | C `a1_cotfull_noabc` | D `a2_cotfull_abc` |
|---|---:|---:|---:|---:|
| arrangement fidelity | 4.5 | 3.5 | 3 | **5** |
| overall pronunciation | 4 | 4.5 | 5\* | 4.5 |
| pace | 4.5 | 4 | 2 | **5** |
| overall vocal | 4 | 4 | 3.5 | **4.5** |
| duration (log) | 271.9 s | 256.8 s | 310.0 s (cap) | 282.2 s |

- **Same clip wins both axes: D (`a2_cotfull_abc`).** Arrangement 5 ≥ v2's 4.5; pronunciation
  4.5 > v2's 4.0 — §7's hypothesis is supported.
- **D vs C is the controlled proof:** both qfinal `cot=full`, only D got v2's ABC. Adding the
  guide: arrangement `3 → 5`, pace `2 → 5`, and it *finishes* — C's 310.0 s is the
  `7750`-token auto cap (the "didn't finish" the listener heard).
- \*C's pronunciation 5 = reciter/Quranic cadence (the exact leak); D is the best *sung*
  pronunciation. C (bare `cot=full`) = nasheed/recitation, reject.
- Caveats: n=1 track/seed/listener; D still "not wow" (wants crisper pronunciation); D's
  intro is 3 s (shortest of the four). No objective arrangement metric — listening call.

## 1. Next — replicate on the other two seeds (same 4 arms)

The sheet asks for it; each run re-does phase 1 + the 4 arms (~35 min each). **One GPU,
sequential — never two at once.** Fresh VM first: `bash bootstrap/setup.sh --inference` then
`bash INFERENCE/v2_abc_to_qfinal.sh --stage`.

Foreground (watch it), replaces the seed and keeps the same tag:

```bash
cd /content/maqamrock-yue2-lora-finetuning
SEED=1029169725 bash INFERENCE/v2_abc_to_qfinal.sh
SEED=1938238049 bash INFERENCE/v2_abc_to_qfinal.sh
```

Detached (both seeds back-to-back, one log) — stop with `pkill -f v2_abc_to_qfinal.sh`;
resume by re-running (each arm overwrites its own output):

```bash
setsid nohup bash -c 'SEED=1029169725 bash INFERENCE/v2_abc_to_qfinal.sh; \
  SEED=1938238049 bash INFERENCE/v2_abc_to_qfinal.sh' \
  > /content/logs/v2abc_seeds.log 2>&1 & disown
# watch: tail -f /content/logs/v2abc_seeds.log
```

Outputs land in `/content/audiocpp_inference/out/v2_abc_to_qfinal_seed<SEED>/`; blind them
per seed with `INFERENCE/prepare_ab_eval.py` (fresh blinding seed — `20260931` and `20260932`
are both taken) and mirror with `python3 backup_to_gcp.py --inference --once`.

## 2. Already on record (this round)

- **Which package was scored — read this.** Two shuffles exist. The one the scores match is
  the working-tree build **seed `20260932`** (`manifests/evaluation_v2_abc_to_qfinal/KEYS.txt`:
  `A=ref_v2, B=a0, C=a1, D=a2`). The GCS package `listening/V2_ABC_TO_QFINAL_INPUT/`
  (`nesib_4148240095_{A..D}.mp3`) is a *different*, unused build — seed `20260931`
  (`KEY_open_after_listening.txt`: `A=a2, B=ref_v2, C=a0, D=a1`); the committed
  `KEYS.txt` at `HEAD` is its copy. The listener's "C is the longest and didn't finish"
  rules the `20260931` mapping out (there `C=a0` = 256.8 s, the shortest). **Refresh or
  delete the GCS package; commit the `20260932` build as the record** (both need your say-so).
  Confirmed against the listener's own copy (`…\Downloads\v2abc_blind\`, `.wav`): byte sizes
  match the render logs arm-for-arm (A `ref` 52,208,428; B `a0` 49,313,068; C `a1` 59,519,788;
  D `a2` 54,182,188) — the decode is mechanical, not inferred.
- Raw render `/content/audiocpp_inference/out/v2_abc_to_qfinal_seed4148240095/` (4 WAVs + logs
  + phase-1 `score.abc`, sha256 `b08427f1…`), all `truncated 0`, 48 kHz stereo; the same 4
  renders underlie either shuffle — only the label map differs.
- Repo text: `manifests/evaluation_v2_abc_to_qfinal/{EVAL,KEYS,MY_EVALUATION}.txt` (the
  working-tree pair is the evaluated `20260932` build; `HEAD` holds the `20260931` one).
- Driver `INFERENCE/v2_abc_to_qfinal.sh`; the `a2` arm used v2's B1 `score.abc` (the question
  answered in the Colab dialog was **B1**, option 1).

## 3. Pointers

- Feasibility: `docs/music-cover-feasibility.md` §7 (this round) · §3 (α tradeoff / AR
  conflict) · §4.2 (B1/B2) · §5 (v2 training-set facts) · §6 (verbatim round) · §8 (open
  questions).
- Adapters/identity: `docs/LORA_INVENTORY.md`, `docs/PRON_LORA_MERGE.md`; runbook
  `docs/INFERENCE.md`. Blind packaging: `skills/ab-blind-eval/SKILL.md`.
- This file is a handoff surface, not authority — re-derive state from the artifacts/logs.
