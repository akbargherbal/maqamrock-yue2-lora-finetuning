# current.md — next session: publish + lean repo (plan written) — 2026-10-13

Copy/read surface only, **not authority**. Authority is **`docs/PUBLISH_PLAN.md`**. Training is
frozen; the next session ships what already exists.

## The two deliverables
- **A.** Final **ArabMaqamRock** LoRA + **Quran** (`quran_ahh_r32`) LoRA → Hugging Face model repos.
- **B.** A new **lean end-user repo** (generation + production), referencing this repo as parent.

## Blocking decisions — answer these first (details in the plan §1)
1. **License.** YuE2 is **CC-BY-NC-4.0** → our LoRAs are NC derivatives. Accept + publish with a
   notice? And a code license for the new repo. (This repo has **no LICENSE**.)
2. HF **namespace + token** (`hf` CLI installed; no token cached).
3. **Which weights**: v3 final (latest) and/or v2 (promoted production style); Quran = final.
4. New **repo owner + name + visibility**.
5. **Binary**: build from source per arch, or also ship a prebuilt release asset.
6. **Dataset**: do not publish (Suno-rendered) unless told otherwise.

## Fast facts gathered this session (verified)
- Parent repo `akbargherbal/maqamrock-yue2-lora-finetuning` is **public**, **no license file**.
- v3 converted adapter sha256 `3531bb91…` (`docs/LORA_INVENTORY.md:60`); v2 style in `loras/`;
  Quran converted pair `quran_ahh_r32_{ar,nar}.safetensors` under `<base>/quran_ahh_r32/convert/`.
- Base model for the runtime comes from HF `audio-cpp/Yue2-3B-GGUF`; the **binary** comes from a
  **private GCS** build (sm_75/T4) — that path is not reusable publicly (plan §1.5).
- The 4 style prompts are **not in this repo** (GCS `audiocpp_inference/prompts/`) — the lean repo
  must export them.
