# current.md — next session: publish + lean repo (plan written) — 2026-10-13

Copy/read surface only, **not authority**. Authority is **`docs/PUBLISH_PLAN.md`**. Training is
frozen; the next session ships what already exists.

## The two deliverables
- **A.** Final **ArabMaqamRock** LoRA + **Quran** (`quran_ahh_r32`) LoRA → Hugging Face model repos.
- **B.** A new **lean end-user repo** (generation + production), referencing this repo as parent.

## Decisions (recorded 2026-10-13)
- **License: publish under CC-BY-NC-4.0** (inherited from YuE2; plan §1.1). Model card carries
  the NC notice.
- **Weights: ArabMaqamRock v3 final** (step 5000) + **Quran `quran_ahh_r32` final**.
  The v2 style adapter is **not** published.
- **Open (ask at execution):** HF namespace; new repo name/visibility + code license; binary
  distribution; dataset (default: don't publish). Full detail: `docs/PUBLISH_PLAN.md` §1.

## Fast facts gathered this session (verified)
- Parent repo `akbargherbal/maqamrock-yue2-lora-finetuning` is **public**, **no license file**.
- v3 converted adapter sha256 `3531bb91…` (`docs/LORA_INVENTORY.md:60`); v2 style in `loras/`;
  Quran converted pair `quran_ahh_r32_{ar,nar}.safetensors` under `<base>/quran_ahh_r32/convert/`.
- Base model for the runtime comes from HF `audio-cpp/Yue2-3B-GGUF`; the **binary** comes from a
  **private GCS** build (sm_75/T4) — that path is not reusable publicly (plan §1.5).
- The 4 style prompts are **not in this repo** (GCS `audiocpp_inference/prompts/`) — the lean repo
  must export them.
