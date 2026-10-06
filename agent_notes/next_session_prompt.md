# Next-session prompt — paste this to start the T4 session

_Created 2026-10-06 at training completion. Task: Phase 3b, Ayat al-Kursi (2:255) epoch test._
_Copy from here (vscode.dev text selection is glitchy; this file is a copy surface, not authority)._

```text
Continue the quran_ahh_r8 work: Phase 3b — end-of-epoch listening test on Ayat al-Kursi
(Quran 2:255), on a fresh T4 VM. Training is already DONE (quran_ahh_r8 hit 28,467/28,467,
clean stop, fully banked in GCS); the L4 is not needed.

Read first, in order: AGENTS.md -> docs/QURAN_AHH_RESUME_PLAN.md (see Phase 3 / 3b) ->
agent_notes/current.md. Then VERIFY live (git, nvidia-smi, the GCS prefixes) — don't recall.

Goal: render THREE checkpoints on the held-out ayah 2:255 at a fixed seed, then prepare a
blind A/B package (ab-blind-eval):
  - c9000  (~=epoch 1 end)
  - c19500 (~=epoch 2 end)
  - final  (un-suffixed quran_ahh_r8.safetensors, epoch 3, exact)
Exact epoch ends (9489/18978/28467) don't land on saves; c9000/c19500 are the nearest.

Environment: fresh T4 Colab; ONE shared GPU — run nvidia-smi first and never overlap.
Repo akbargherbal/maqamrock-yue2-lora-finetuning, branch pron-lora-long-aya @ 3d492ba.
Setup: bash bootstrap/setup.sh --inference
Run:   python INFERENCE/quran_pt_probe.py --prefix quran_ahh_r8_rank32/convert --arms c9000,c19500,final
(the probe already uses 2:255 via INFERENCE/yue2_eval_heldout/quran_heldout.json; it adds a
'base' all-zero arm automatically and renders uthmani+simple.)

Caveat: c9000, c19500, and the final adapter exist as LoRA .safetensors in GCS but are NOT yet
converted to GGUF-LoRA arms under the probe prefix — convert them first (docs/INFERENCE.md + the
probe's staging), and verify each arm is banked in GCS before running.

All state lives in GCS: $GCP_BACKUP_BASE/quran_ahh_r8/. Report state before acting; hand me any
state-changing command to run; don't edit configs.
```
