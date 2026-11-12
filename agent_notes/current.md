# Current — `arabic_instrumental_lora` · 2026-11-12 13:50 UTC (16:50 Bahrain) · TRAINING

## State

```
run        RUNNING · pid 22456 · started 12:22:58 · 4407/5500 steps (80 %)
rate       1.74 s/it recent · 2:53:22 elapsed → ETA ~32 min → finish ≈ 18:57–19:05 Bahrain
gpu        100 % util · 73,846 MiB · 66 C
oom        112 total = 2.54 % of steps — steady, isolated
errors     0 tracebacks/exceptions
```

## Loss (225-step bins, `loss/loss`)

```
 500- 749  4.130      1500-1749  4.024
 750- 999  4.091      1750-1999  4.028
1000-1249  4.061
1250-1499  4.068
first100 4.455 → last100 4.003 (Δ −0.451, −10 %) · slope since 1000: −6.1e-5/step
linear projection @5500 ≈ 3.79 (indicative only — the curve is decelerating, not linear)
ar_ce 3.512 → 3.122
```

Reading: still descending, but the slope since step 1000 is ~6× shallower than the opening
phase. Normal deceleration for a style adapter; loss is not the verdict — audio is.

## Checkpoints

```
local   1000 1250 1500 1750 2000 2250 2500 2750 3000 3250 3500 3750  (12 = the keep cap)
        → rotation began at 3250; 250/500/750 are gone locally, by design
GCS     250 500 750 1000 1250 1500 1750 2000 2250 2500 2750 3000 3250 3500 3750  (15, complete)
backup  last pass 15:04:19 "3/3 folders synced" — current · output prefix 1.5 GB local
disk    205 GB free on /content
```

## Eval plan written (draft)

`docs/ARABIC_INSTRUMENTAL_EVAL_PLAN.md` — checkpoint screen (base/3000/4000/5000/5500) on
5 prompts ≈ 2.7 h T4, then depth on the winner ≈ 3 h. Pending your approval + index row.

## Open items for the post-run docs pass (not touched mid-run)

1. Plan F3/§8 quotes ~15–16 GB whole-song VRAM. `TRAINING_ANALYSIS/ANALYSIS.md:71-79` records
   v3 at peak 81,144 MiB / 776 MiB headroom on the same A100 — the 15–16 GB number is the
   L4/checkpointing-on case. Worth correcting, since it hid the OOM mechanism.
2. Coverage gap: the 13 tracks ≥ ~377 s are dropped every epoch (53 OOMs = 2.65 %, matching
   13/474). Adapter = 461 effective tracks. User decision: accept, do not stop.
3. `status.py:33` hardcodes `RUN_NAME = "v3_arabmaqrock_lora"` → wrong run label/db path/sidecar pid.
4. `pgrep -f 'bash bootstrap/setup.sh'` self-matches the watcher's own command line (a watcher
   spun for the full hour after setup finished). Append to `docs/COMMAND_HANDOVER_GOTCHAS.md`.

## Stop / resume (yours)

```bash
python train_ctl.py stop   --config config/arabic_instrumental_lora.yml
# resume = re-run the identical start command
```
