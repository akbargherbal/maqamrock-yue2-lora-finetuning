# Plan — publish the LoRAs on Hugging Face + a lean end-user generation repo

_Status: **PLAN — not started.** Written 2026-10-13; **§1 decisions recorded 2026-10-13**
(publish under CC-BY-NC-4.0; ship v3 final + `quran_ahh_r32`). Training is frozen; this plan
ships what already exists. Nothing here is executed until the user types each command (§8)._

Two deliverables:

- **A. HF models** — the final **ArabMaqamRock** LoRA and the **Quran pronunciation** LoRA,
  each as a Hugging Face *model* repo (weights + model card).
- **B. Lean repo** — a new, small, end-user-oriented GitHub repo: *"this is what we have,
  and this is how to use it."* Generation + production only. References this repo as the
  parent for provenance.

Authority for what exists: `docs/LORA_INVENTORY.md` (adapters + hashes), `docs/INFERENCE.md`
(the generation path), `docs/QURAN_AHH_RUN.md` (the Quran LoRA), `docs/yue2-gguf-lora-findings.md`
(licensing).

---

## 1. Decisions

**Decided (2026-10-13, user):**

1. **License — publish under CC-BY-NC-4.0.** YuE2 is CC-BY-NC-4.0
   (`docs/yue2-gguf-lora-findings.md:54`), so the LoRAs are non-commercial derivatives.
   **Accepted:** publish publicly, with `license: cc-by-nc-4.0` in the model card and a
   prominent non-commercial notice. (The *new repo's* code license is still open — see #4.)
2. **Weights — ArabMaqamRock v3 final only** (step 5000); **Quran = `quran_ahh_r32` final**
   (AR+NAR, rank 32/32, 3 epochs). The **v2 style adapter is not published**.

**Open (ask when we reach them — none block a start):**

3. **HF namespace** — which account/org owns the model repos (needed for `hf repos create`).
   The token is the user's: `hf auth login`, never pasted into chat.
4. **New repo** — owner, name (proposals: `arabmaqamrock`, `maqamrock-yue2-generate`,
   `arabmaqamrock-studio`), visibility, and its code license.
5. **The runtime binary.** `audiocpp_cli` is staged from a **private GCS** build (sm_75/T4,
   CUDA 12); a public repo cannot use that. Options: (a) require a **source build**
   (`docs/audiocpp_gpu_arch_builds.md`, ~21 min CPU), (b) ship a **GitHub/HF release asset** per
   arch, (c) both (build script + optional prebuilt).
6. **Dataset** — default **do not publish** (Suno-rendered audio → Suno ToS + poem copyright).
   Confirm only if that changes.

---

## 2. Inventory to publish (verified)

| Artifact | Where (GCS `<base>` = the private backup bucket) | Identity |
|---|---|---|
| **ArabMaqamRock v3 final** — publish | `<base>/v3_arabmaqamrock_lora/convert/` → `v3_arabmaqamrock_lora_{ar,nar}.safetensors` | converted AR sha256 `3531bb91…` (`LORA_INVENTORY.md:60`) |
| **Quran `quran_ahh_r32`** — publish | `<base>/quran_ahh_r32/convert/` → `quran_ahh_r32_{ar,nar}.safetensors` | rank 32/32 AR+NAR |

Not published: the v2 style adapter (`<base>/loras/audio_cpp/style/`, `747d5cfe…`) — the
promoted production style, but not the "final" (§1.2); the `qahh_a0*` merges (v2 × quran,
unlistened, donor **shelved**); the archived donors; and the pre-rename v1 (no surviving copy).

---

## 3. Phase A — Hugging Face publication

**A1. Auth (user).**
```bash
hf auth login          # paste a token from huggingface.co/settings/tokens (write scope)
hf auth whoami
```

**A2. Create the model repos** (one per LoRA; adjust namespace):
```bash
hf repos create <user>/arabmaqamrock-yue2-lora --type model --public
hf repos create <user>/quran-pronunciation-yue2-lora --type model --public
```

**A3. Assemble the payload** in a scratch dir (`/tmp/opencode/hf-publish/<name>/`):
- the **converted AR/NAR pair**, renamed readably (`arabmaqamrock-v3-ar.safetensors`, …);
- optional `source/` with the fused ai-toolkit final (the merge source — `LORA_INVENTORY.md:128`);
- **`README.md`** = the model card (below).

**A4. Model card skeleton** (HF YAML front-matter + prose):
```yaml
---
base_model: m-a-p/YuE2-3B
library_name: audiocpp          # consumed by audio.cpp, not transformers
license: cc-by-nc-4.0           # decided 2026-10-13 (§1.1)
tags: [audio, music-generation, yue2, lora, arabic, maqam]
---
```
Prose must state: what it does; the **trigger word `arabmaqamrock`**; how to load it
(`yue2.ar_lora` / `yue2.nar_lora`, scale 1.0, `cot=off`); the **converted-AR sha256**; training
provenance (dataset size, steps, rank, EMA); the NC limitation; and a pointer to the lean repo
for a runnable path. Mirror the honesty of the README's "~4/5, not the incumbent" scoreboard.

**A5. Upload + verify:**
```bash
hf upload <user>/arabmaqamrock-yue2-lora /tmp/opencode/hf-publish/arabmaqamrock --type model
hf download <user>/arabmaqamrock-yue2-lora --local-dir /tmp/opencode/hf-verify   # round-trip
sha256sum /tmp/opencode/hf-verify/*.safetensors      # must equal the card's hashes
```
Optional: an HF **collection** grouping the two models.

---

## 4. Phase B — the lean repo

**B1. Principle:** carry only the **inference path**. No GCS, no Colab/GCP, no training,
no monitoring, no backups. A user clones, installs, downloads two HF repos, generates.

**B2. Layout (new repo):**
```
README.md                 # what it is + 5-minute quickstart (the whole point)
LICENSE                   # code license (§1.4); NOT the weights' license
install.sh                # build audio.cpp (audiocpp_cli) for the local arch; ccache+time
generate.py               # from INFERENCE/generate.py (strip GCS/lora-alias bits)
run_one.sh                # from INFERENCE/run_one.sh
duration_cap.py           # canonical text->duration cap
cuda_loader_path.sh       # CUDA-12 loader shim (only if a prebuilt binary is shipped)
songs.example.json        # user-supplied-lyrics batch input
prompts/{Ajam,Hijaz,Kurd,Nahawand}_style.txt   # the 4 style templates (export from GCS)
prompts/example_lyrics.txt
MODEL_CARD.md             # what the LoRA is, trigger word, license, hashes
```
**Must not be carried over:** `bootstrap/setup.sh` (GCS), `train_ctl.py`, `monitor_loss.py`,
`backup_to_gcp.py`, `merge_*`, `config/`, `results/`, `TRAINING_ANALYSIS/`, `agent_notes/`.

**B3. Work items:**
- Export the 4 `*_style.txt` from `<base>/audiocpp_inference/prompts/` once (they are **not in
  this repo**); commit them. Ship one example lyrics file for the smoke test.
- Rewrite `run_one.sh`'s staging to read the model from a **local** path (HF `hf download`)
  instead of GCS; keep the fixed session options (`family yue2`, `cot=off`, `flash`).
- `generate.py`: drop the `loras`/GCS-alias machinery (or re-point aliases at HF); keep the
  schema, dry-run, resume, and seed cap (`< 2^32`).
- `install.sh`: clone `0xShug0/audio.cpp`, `scripts/build_linux.sh --backend cuda
  --cuda-arch <local> --ccache --model-set custom --models yue2 --target audiocpp_cli`
  (per `docs/audiocpp_gpu_arch_builds.md`), then `hf download audio-cpp/Yue2-3B-GGUF`.
- README quickstart: install → download base + LoRA → `python generate.py songs.example.json`
  → a WAV in `out/`. State the **GPU requirement** and the **NC** notice up front.
- Port the small relevant tests; drop the rest.

**B4. README skeleton:** *What this is* (one maqam-rock LoRA + a generation pipeline you own)
→ *Requirements* (CUDA GPU; ~10 GB disk) → *Quickstart* → *Bring your own lyrics* →
*License (NC)* → *Provenance* (parent repo + HF + the base model).

---

## 5. Wiring the two repos

- This repo (parent) gets a short **"Artifacts & downstream"** section: the HF model IDs and
  the lean repo URL; `SOURCE_OF_TRUTH.md` gains rows for the HF model authorities and the
  release repo.
- The lean repo's README points back at the parent for **provenance and the research trail**,
  and at HF for the weights.
- Keep the two in sync on one fact only: the **adapter hashes** (the stable identity).

---

## 6. Definition of done

- `hf download` of both models round-trips and the sha256s match the model cards.
- On a **fresh GPU VM**, from the lean repo alone, `generate.py songs.example.json`
  produces a WAV — with **no GCS references** anywhere in the tree.
- Both repos carry a `LICENSE`; the NC derivation is stated in the model card and the README.
- The parent repo references the HF models + the lean repo; nothing in the parent is broken
  by the extraction.

---

## 7. Risks / open questions

- **NC vs. audience.** If any audience use is commercial, publishing NC weights (or using the
  base at all) is out of scope — surface this before Phase A.
- **Suno provenance.** The training audio is Suno-rendered; a model card should note the
  training data is generated audio, without publishing it (§1.6).
- **Quran artifacts live partly on the `pron-lora-long-aya` branch** (`QURAN_AHH_RUN.md:9`:
  *do NOT merge to main*). The **weights are in GCS** so publishing needs no merge, but the
  model card's provenance should cite `config/quran_ahh_r32.yml` + `docs/QURAN_AHH_RUN.md`
  (both on `main`). Confirm nothing else is needed from that branch.
- **Binary distribution** is the biggest end-user friction (§1.5); a build step is honest but
  a prebuilt release asset is friendlier — decide per arch (sm_75 / sm_80 / sm_89).
- **Scope creep:** the lean repo is *not* a rewrite; it is a curated copy. Resist porting
  training.

---

## 8. Next-session execution order

1. Answer §1 (license, namespace/token, which weights, repo name, binary, dataset).
2. Phase A: auth → create repos → assemble + model cards → upload → verify hashes.
3. Phase B: scaffold the lean repo, export prompts, rewrite the two scripts, README, LICENSE.
4. Fresh-VM round-trip test (§6) — the real acceptance gate.
5. Wire §5 back into this repo; update `SOURCE_OF_TRUTH.md` + `docs/README.md`; log the pass.
