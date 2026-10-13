# Next-session prompt — publish the LoRAs on HF + build the lean generation repo

_Created 2026-10-13. Paste the block below into the session. Copy surface, not authority —
**authority is `docs/PUBLISH_PLAN.md`** (the full plan). Training is frozen; this session ships
what exists. (The prior revision of this file was the completed Probe Q prompt — recoverable at
`git show <sha>:agent_notes/next_session_prompt.md`.)_

```text
Session goal: freeze training and ship. Two deliverables:
  A. Publish the final ArabMaqamRock LoRA + the Quran (quran_ahh_r32) LoRA on Hugging Face.
  B. Create a NEW lean, end-user repo: generation + production only, referencing
     akbargherbal/maqamrock-yue2-lora-finetuning as the parent for provenance.

READ FIRST, in order:
  1. docs/PUBLISH_PLAN.md                 — the plan: decisions, phases, done-criteria, order.
  2. docs/LORA_INVENTORY.md               — which adapters exist + their hashes (stable identity).
  3. docs/INFERENCE.md                    — the generation path the lean repo will carry.
  4. docs/QURAN_AHH_RUN.md                — the Quran LoRA (note: branch pron-lora-long-aya).
  5. docs/yue2-gguf-lora-findings.md      — the licensing fact that gates everything.

BLOCKING — ask me these BEFORE any publish step (do not guess):
  - License: YuE2 is CC-BY-NC-4.0, so our LoRAs are non-commercial derivatives. Confirm I accept
    that, and pick a code license for the new repo. There is NO LICENSE file in the parent repo.
  - HF namespace + token (the `hf` CLI is installed; no token is cached).
  - Which weights ship: v3 final (latest) and/or v2 (the promoted production style); Quran = final.
  - New repo owner + name + visibility.
  - Binary: build audio.cpp from source for the user's arch, or also ship a prebuilt release asset.
  - Dataset: do NOT publish (Suno-rendered) unless I say otherwise.

HARD CONSTRAINTS:
  - One shared GPU; do not start GPU work without nvidia-smi confirming it is free.
  - Publishing is CPU/network only — no GPU needed for Phase A. The acceptance test (a fresh-VM
    generate) is the only GPU step.
  - Never write a token into the repo or into chat. Let me run `hf auth login` myself if needed.
  - Nothing in the parent repo may break: reference the new artifacts, don't move them out.

Order: answer the blocking list -> Phase A (auth, create repos, model cards, upload, verify
hashes via `hf download` round-trip) -> Phase B (scaffold the lean repo: export the 4 style
prompts, rewrite run_one.sh/generate.py off GCS, README + LICENSE + install.sh) -> fresh-VM
generate test -> wire the parent repo (SOURCE_OF_TRUTH.md + docs/README.md) and log the pass.

Report plainly what you verified vs assumed; quote artifact lines, not memories.
```
