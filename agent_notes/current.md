# current

_Copy surface, not authority. Session · 2026-10-01 · **T4 Colab**, branch `music-cover`._

## Rescue batch — RUNNING (started 2026-10-01 ~06:40 UTC)

`qfinal_a0.3` + `cot=full` + fresh seed per take. 24 tracks; log `/content/logs/rescue_winning.log`;
ETA ~2–2.5 h. Stop `pkill -f '[r]escue_abc_batch'; pkill -f '[a]udiocpp_cli --task gen'`; resume = same
command (drawn seeds are reused from `_rescue_index.json`, so it skips succeeded takes).

Prior output (the melody run) archived before launch: GCS
`audiocpp_inference/out_archive/rescue_v2abc_batch12_winning_melody_20261001/` (12 objects, 84.5 MiB);
local `/content/archive/rescue_v2abc_batch12_winning_melody_20261001/`.

### settings + run command

`manifests/rescue_selection.batch_12_rock_v2_winning.json` is now: `lora=qfinal_a0.3`, `cot=full`,
`seed="random"`.

- A **fresh seed is drawn per take**. The ABC + pass-1 WAV stay keyed to the original
  `<name>_<pass1seed>` (recorded as `abc_source_stem`); the output is `<name>_<newseed>`.
- Validated: `--plan` → **24** tracks, `cot=full`, `seed_mode=random`; **stable on re-plan** (drawn
  seeds are persisted in `_rescue_index.json`; delete that file to force a re-draw).
- Driver gained the seed override — see `RECONCILIATION_LOG.md` 2026-10-01 and
  `INFERENCE/rescue_abc_batch.sh --help`.

Run it (detached, GPU):

```bash
cd /content/maqamrock-yue2-lora-finetuning
setsid nohup bash INFERENCE/rescue_abc_batch.sh \
  --songs-json manifests/rescue_selection.batch_12_rock_v2_winning.json \
  > /content/logs/rescue_winning.log 2>&1 & disown
# stop: pkill -f '[r]escue_abc_batch'; pkill -f '[a]udiocpp_cli --task gen'
```

- **No `--force` needed**: fresh seeds ⇒ new output filenames, so the 2 old takes aren't "skipped"
  — they're just left as stale files.
- **Stale files caveat:** `out_dir` (`/content/rescue_v2abc_batch12_winning`) still holds 2 obsolete
  *melody* WAVs (`07-…_{3781160148,1769813156}.wav`) from the aborted run. For a pure set, add a
  clean dir on the CLI (CLI wins), e.g. `--out-dir /content/rescue_v2abc_q03full_reroll`, and add
  that dir to the backup `--extra`.

## LoRA × seed matrix — RESULT

Winner: **`q03_newseed` = `qfinal_a0.3` @ seed `1012482070`**. Recorded in
`manifests/evaluation_lora_seed_matrix/MY_EVALUATION.txt`. (n=1, one listener — signal, not verdict.)

## prepare_ab_eval on the 6-file bundle — layout fix

Needs **variant subfolders**, same stem each (`…/<variant>/track.wav`) — flat → `not in the subpath`:

```powershell
cd C:\Users\DELL\Downloads\lora_seed_matrix_07_alhar_rock
$map = [ordered]@{
  '01_v2_newseed_1012482070.wav'               = 'v2_newseed'
  '02_q03_sameseed_3781160148.wav'             = 'q03_sameseed'
  '03_q03_newseed_1012482070.wav'              = 'q03_newseed'
  '04_q05_sameseed_3781160148.wav'             = 'q05_sameseed'
  '05_q05_newseed_1012482070.wav'              = 'q05_newseed'
  'reference_v2_sameseed_3781160148_pass1.wav' = 'v2_sameseed'
}
foreach ($k in $map.Keys) { New-Item -ItemType Directory -Force -Path $map[$k] | Out-Null; Move-Item -Force $k "$($map[$k])\track.wav" }
```
```powershell
python C:\Users\DELL\Jupyter_Notebooks\maqamrock-yue2-lora-finetuning\INFERENCE\prepare_ab_eval.py `
  --root C:\Users\DELL\Downloads\lora_seed_matrix_07_alhar_rock `
  --output C:\Users\DELL\Downloads\lsm_ab_eval --seed 20261001 --title "LoRA x seed - Al-Har (Ajam)"
```

## State

- **Rescue:** stopped; index rebuilt for the new settings. 2 melody takes still on disk (see caveat).
- **LoRA×seed matrix:** DONE (5/5, 40:24); uploaded; verified on GCS
  (`audiocpp_inference/evals/lora_seed_matrix_07_alhar_rock/lora_seed_matrix_07_alhar_rock.zip`,
  sha256 `33b02724…6bd3`).
- **Backup:** `backup_to_gcp.py --inference` daemon up (pid 22087), current. `vm-continuity` healthy.
- **Repo (uncommitted):** `INFERENCE/rescue_abc_batch.sh` (seed override) + tests; `manifests/` (new
  matrix manifest + moved 5 manifests + selection config); docs (`PRON_LORA_RESCUE.md`,
  `SOURCE_OF_TRUTH.md`, `rescue_selection.example.json`); `RECONCILIATION_LOG.md` entry. Push needs
  your PAT.
