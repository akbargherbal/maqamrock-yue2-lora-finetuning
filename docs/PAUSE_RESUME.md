# Pause for the night, resume next session

Colab is ephemeral: stopping the runtime (or it being reclaimed) wipes
`/content`. So a "pause" is really *stop cleanly + make sure GCS has the latest
checkpoint*. Resume tomorrow = fresh VM + restore the run folder + relaunch; it
continues from the last checkpoint.

## Why this works

`ai-toolkit` auto-resumes from the newest checkpoint in the run's output folder:
it reads `training_info.step` from the `.safetensors` metadata and loads
`optimizer.pt`, then loops from that step. Same run name + same config = it
continues toward `steps: 3000`. (Verified in
`jobs/process/BaseSDTrainProcess.py`; see `../DECISIONS.md`.)

## Pause (at night)

1. Stop training cleanly:
   ```bash
   cd /content/maqamrock-yue2-lora-finetuning
   python train_ctl.py stop      # SIGINT; waits for "Job stopped"
   ```
2. Force one backup pass and confirm the latest checkpoint is in GCS:
   ```bash
   cd /content/maqamrock-yue2-lora-finetuning
   python backup_to_gcp.py --run-name akbar_arabic_rock_lora --once
   gsutil ls -l gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/akbar_arabic_rock_lora/output/ | tail
   ```
   You want to see the newest `akbar_arabic_rock_lora_0000NNNNNN.safetensors`
   **and** `optimizer.pt`, with sizes matching local.
3. You can now let the VM go. You do not need to keep the tab open.

Loss on pause: checkpoints save every 250 steps, so you lose at most the partial
interval since the last save (≤ 249 steps). To lose nothing, pause right after a
step that is a multiple of 250.

## Resume (next morning, fresh VM)

1. Follow [START.md](START.md) steps 1–3 (clone, bootstrap, then this restore).
2. Restore the run folder from GCS **into the exact training folder path**. The
   parent directory must exist first — `gsutil rsync` aborts with *"does not
   name a directory"* otherwise:
   ```bash
   mkdir -p /content/ai-toolkit/output/akbar_arabic_rock_lora
   gsutil -m rsync -r \
     gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/akbar_arabic_rock_lora/output \
     /content/ai-toolkit/output/akbar_arabic_rock_lora
   ```
3. Start the sidecars (START.md step 4).
4. Launch, with the **identical** config and run name: `python train_ctl.py start`
   (START.md step 5). You type it — this is a planned resume, not the agent's
   auto-resume exception. Watch the log; it should print a "Found step N ...
   starting from there" line, not start at 0.

## Notes

- The latent cache is **not** in GCS; a fresh VM rebuilds it (~12 min) during
  startup. That is expected.
- Use the **same run name and config**. A changed config/hyperparameter is not a
  resume — archive the old run and start fresh instead
  ([BACKUP_RESTORE.md](BACKUP_RESTORE.md)).
- Disconnect safety: if the VM dies mid-run without a clean pause, the last
  backed-up checkpoint (≤ 5 min old) is still resumable. An unplanned
  interruption of an already-approved, unchanged run may be auto-resumed by the
  agent (`../AGENTS.md`); a planned pause is always you typing the command.
