# Current — 2026-11-12 (preflight pass)

**`arabic_instrumental_lora` passed local preflight with three plan fixes. Nothing is
training. Next action: commit + push this branch, then open the A100 Colab session and paste
`agent_notes/vm_start_prompt.md`.**

Plan + rationale: `docs/ARABIC_INSTRUMENTAL_LORA_PLAN.md` (D1–D10, accepted as defaults).
Dataset runbook: `docs/ARABIC_INSTRUMENTAL_DATASET.md`.
VM session prompt: `agent_notes/vm_start_prompt.md` (paste as-is).

## State (verified this turn, 2026-11-12)

```
git              main @ 106aa15 · pushed to origin · tree clean before edits
gpu              local box: no /content, no CUDA checks applicable
training         not running · no output/arabic_instrumental_lora/
GCS dataset      arabic_instrumental_dataset.zip 3,162,874,610 B @ 2026-11-12T10:49:46Z
                 sha256 cea34fa2e584472d0b134f51dc0ae83b66d999ee1dffbc40dad4dcd783e39954
GCS sidecars     _manifest.json 349,574 B · _report.md 2,966 B · .zip.sha256 98 B — all present
manifest         482 tracks · 36.60 h · 283 vocal-flagged / 199 clean
configs          parse; A100 vs L4 differ only in name/log_dir/gradient_checkpointing
```

## Preflight findings (three gaps, all fresh-VM specific)

| # | Gap | Fix now in the plan |
|---|---|---|
| P1 | The launch notebook's secrets cell pins `GCP_DATASET_ZIP=…/v3_arabmaqamrock_dataset.zip` and sets no `GCP_DATASET_COUNT` → a stock launch pulls **438** tracks and the verify passes | §4.3 env guard: assert/append both vars after the secrets cell, before bootstrap |
| P2 | `stop`/`status` also default to the v3 config and reject the live process; the output run name comes from the config's `name:`, not `--run-name` | §5.2/§5.3 + F8: all verbs carry `--config` |
| P3 | §4.4 read the manifest from the build workspace (absent on a fresh VM) and never persisted the 8-track eval set | §4.4: fetch manifest from GCS; upload `/content/eval_holdout` |

Also appended: two entries in `docs/COMMAND_HANDOVER_GOTCHAS.md` (v3-zip default; stop/status
config matching).

## Holdout — pinned (D7, seed 42, rehearsed against the GCS manifest)

```
yt500   vocal  yt500-0153-HU_nX3kcvBk        yt500   clean  yt500-0211-yAl48Tk0Sno
yt500   vocal  yt500-0032-a8TZVDBsxTo        yt500   clean  yt500-0188-3bKyiwq30Fc
yt500   vocal  yt500-0327-TZVrsUGhKTw        yt500   clean  yt500-0108-CPLgqU65Dss
fs18    vocal  fs18-waynak_habib_2204908989  yt500   clean  yt500-0083-gU2rAJVlw1A
```

The VM run must pick exactly these; a different list = wrong manifest.

## To do before the VM

```bash
cd /content/maqamrock-yue2-lora-finetuning   # or this worktree
git add -A && git commit -m "preflight: arabic_instrumental_lora fresh-VM guards (env, holdout, stop)"
git push origin main
```

Auth comes from your terminal (`bash bootstrap/github_auth.sh` if needed) — not from the agent.
The VM prompt is self-contained, so it still works if the push is skipped; the repo plan would
just be the older revision.

## Launch (A100; the command is yours to type)

terminal: detached — log `/content/logs/setup.log`; stop: `pkill -f bootstrap/setup.sh`;
resume: re-run the same line (already-present files are skipped).

```bash
mkdir -p /content/logs
cd /content/maqamrock-yue2-lora-finetuning
setsid nohup bash bootstrap/setup.sh --training > /content/logs/setup.log 2>&1 & disown
```

Gate: `[ok] dataset: 482 tracks` + `sha256sum /content/yue2_dataset.zip` = `cea34fa2…39954`
→ holdout (474 mp3) → sidecars → dry run → then:

```bash
python train_ctl.py start --config config/arabic_instrumental_lora.yml --run-name arabic_instrumental_lora
python train_ctl.py stop  --config config/arabic_instrumental_lora.yml   # checkpoint-safe
```

## Unchanged / still open

- **Composability:** one file per expert → "mixed" = offline merge. This adapter + pron donor =
  `merge_pron_lora.py`; this adapter + v3 style = no tool yet (plan §1.1).
- Cosmetic drift: fixed this turn — the `config/arabic_instrumental_lora*.yml` comments now say
  482 tracks and max **478.3 s** (were 438 / 370 s). No value changed.
- Sidecars are down because there is no run to mirror — start both at launch (plan §5.1).
