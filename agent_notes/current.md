# current

## EXPERIMENT: Quran pron LoRA alone (α=1) on the base model — branch `experimental-quran-pron` (2026-10-04)

**The ask.** Test the Quran pronunciation LoRA **by itself** — no v2 style LoRA —
at full strength (α=1) on the base YuE2 model, and judge it on **pronunciation**.

**Why this is untested.** Every current candidate is a merge: `qfinal_a0.3` /
`qfinal_a0.5` = v2 style (AR+NAR, rank 32) **+** `quran_long_aya_r8_s10` final
(AR-only, rank 8), rank-concatenated to AR rank 40, with v2's NAR copied through
(`docs/LORA_INVENTORY.md:53-64`). So the Quran adapter has **always** been heard
under v2's style. Its isolated effect on articulation is unknown.

**Key mechanical facts (checked against the repo, not memory).**
- The Quran adapter is **AR-only, rank 8** — config
  `config/quran_long_aya_r8_s10.yml:33-41` (`linear: 8`, `linear_alpha: 8`,
  `network_kwargs.ignore_if_contains: ["transformer.nar"]`). Pronunciation lives in
  the **AR** expert; NAR is timbre/rendering (`docs/FUTURE_PRONUNCIATION_LORA.md:43-66`).
- It was trained `alpha == rank` (8/8), so its saved delta is `B @ A` at **full
  strength** — i.e. the raw file *is* the α=1 arm. Nothing to merge or scale.
- ai-toolkit saves a **fused** file; audio.cpp needs **unfused** per-projection
  names, so the converter is required (`docs/yue2-gguf-lora-findings.md` banner).
- audio.cpp's `yue2.{ar,nar}_lora_scale` is a per-expert strength dial; **scale 0 =
  adapter off / base weights** (verified in `docs/yue2-gguf-lora-findings.md:2.3`,
  PR #586). `INFERENCE/run_one.sh` now exposes `LORA_AR_SCALE` / `LORA_NAR_SCALE`
  (default 1.0) so an expert can be switched off.

### Arm matrix (same lyrics + same seed across arms)
| Arm | AR | NAR | What it answers |
|---|---|---|---|
| **A. base** | off (scale 0) | off (scale 0) | the model's own articulation ceiling |
| **B. quran-alone-on-base** ← the ask | Quran AR-only, 1.0 | off (scale 0) | the Quran adapter's isolated effect, base timbre |
| **C. quran-AR + v2-NAR** (optional, cheap) | Quran AR-only, 1.0 | v2 NAR, 1.0 | isolates *AR* (v2's AR replaced by Quran's) while keeping arabmaqamrock timbre |
| **D. current shipping control** | qfinal_a0.5 AR, 1.0 | qfinal_a0.5 NAR, 1.0 | what we ship today (v2 + Quran α0.5) |

B is the literal request. **C is the more decision-relevant arm**: pron is AR-only,
so with NAR held at v2 you hear only the AR swap. Watch for recitation-prosody bleed
(stretched vowels / tajweed cadence) and the **ceiling risk** — if MERT semantic
tokens don't separate ح/خ and ع/أ, no AR adapter can fix it
(`docs/FUTURE_PRONUNCIATION_LORA.md:120-151`).

### Inputs / provenance
- **Quran pron source** (not pinned in `loras/source/`; lives in the run prefix):
  `gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning/quran_long_aya_r8_s10/output/quran_long_aya_r8_s10.safetensors`
  sha256 `f8c842e48b93d142bc3cfee6e98f54809020813ae272485a4afb849320b1e2e8`
  (`docs/LORA_INVENTORY.md:59-62`).
- **Converter** (staged by `setup.sh --inference`):
  `/content/converter/out/convert_aitoolkit_yue2_lora.py`.
- **Built target**: `/content/converter/out/quran_only/quran_long_aya_r8_s10_ar.safetensors`
  (AR-only, rank 8; the `_nar` output, if any, is irrelevant — NAR runs off/base).
- **Controls** in GCS `loras/audio_cpp/`: `style/` (v2 pair) and
  `pron/qfinal_a0.5/` (arm D), staged per `docs/LORA_INVENTORY.md:149-158`.
- **Eval lyrics**: the held-out set `INFERENCE/yue2_eval_heldout/heldout_eval_prompts.json`
  (0 shared lines with training; the Ajam entry is the ح/ع probe).

---

## GPU session — start here (run on `experimental-quran-pron`)

### 0. Preflight — no GPU work until this reads clean
```bash
nvidia-smi; free -h; df -h /content
pgrep -af 'run\.py|generate\.py|audiocpp_cli' || echo "nothing running"
python status.py
```
**GPU rule:** one shared GPU. If a run is active (or you can't confirm none is), do
**not** start GPU work — no overlap. Non-GPU steps below (1–4) are fine either way.

### 1. Bootstrap inference assets
terminal: foreground — you watch it; Ctrl+C stops it (re-run resumes; jobs are
marker-guarded). It runs ~7 jobs in parallel; watch `/content/logs/setup.log`.
```bash
cd /content/maqamrock-yue2-lora-finetuning
bash bootstrap/setup.sh --inference > /content/logs/setup.log 2>&1
grep -n "\[FAIL\]" /content/logs/setup.log || echo "no failures"
cat /content/logs/timing.txt
```

### 2. Stage the Quran pron checkpoint and verify its hash
terminal: foreground — small (~117 MB), quick.
```bash
export GCP_BACKUP_BASE=gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning
mkdir -p /content/pron_src
gsutil cp "$GCP_BACKUP_BASE/quran_long_aya_r8_s10/output/quran_long_aya_r8_s10.safetensors" /content/pron_src/
sha256sum /content/pron_src/quran_long_aya_r8_s10.safetensors
# expect: f8c842e48b93d142bc3cfee6e98f54809020813ae272485a4afb849320b1e2e8
```

### 3. Convert the AR-only adapter (the one place to verify, not assume)
terminal: foreground — CPU-only, seconds. **First read the tool's own contract:**
```bash
python /content/converter/out/convert_aitoolkit_yue2_lora.py --help
```
Then convert the pron file **directly** (no merge — that would re-add v2):
```bash
python /content/converter/out/convert_aitoolkit_yue2_lora.py \
  /content/pron_src/quran_long_aya_r8_s10.safetensors \
  --out-dir /content/converter/out/quran_only --stem quran_long_aya_r8_s10
```
Expect `/content/converter/out/quran_only/quran_long_aya_r8_s10_ar.safetensors`.
Verify it is AR-only, rank 8 (~112 A + 112 B = 224 tensors, all `text_encoders.*`):
```bash
python - <<'PY'
from safetensors import safe_open
p = "/content/converter/out/quran_only/quran_long_aya_r8_s10_ar.safetensors"
with safe_open(p, framework="pt") as f:
    ks = list(f.keys())
    print("tensors:", len(ks))
    print("non-text_encoders keys:", [k for k in ks if not k.startswith(("text_encoders", "transformer.ar"))][:5])
    a = next(k for k in ks if k.endswith("lora_A.weight"))
    print("rank(A):", f.get_slice(a).get_shape()[0])
PY
```
**If the converter refuses an AR-only input** (it has only ever been fed AR+NAR
fused files — see `tests/test_merge_pron_lora.py:207-233`), fall back to:
stage the *fused* v2 (`loras/source/akbar_arabic_rock_lora.safetensors`), build a
fused file whose AR = pron and whose NAR = **zero** tensors at rank 8 (shapes read
from v2's NAR), convert that, and run with `LORA_NAR_SCALE=0`. Record whichever
path worked in this file.

### 4. Generate the arms (choose ONE seed < 2^32; B/C use the same seed as A/D)
Use the held-out Ajam prompt first (the ح/ع probe). Arms A and B are the priority;
C and D are cheap add-ons.

terminal: **detached** — survives Ctrl+C / closing the tab.
log: `/content/logs/quran_only.log`; stop: `pkill -f 'INFERENCE/run_one.sh'`;
resume: re-run the same block (each track is independent).
Progress: `tail -f /content/logs/quran_only.log`.
```bash
cd /content/maqamrock-yue2-lora-finetuning
SEED=20261004
QAR=/content/converter/out/quran_only/quran_long_aya_r8_s10_ar.safetensors
V2AR=/content/converter/out/akbar_arabic_rock_lora_ar.safetensors
V2NAR=/content/converter/out/akbar_arabic_rock_lora_nar.safetensors
QF_AR=/content/converter/out/qfinal_a0.5/akbar_arabic_rock_lora_ar.safetensors
QF_NAR=/content/converter/out/qfinal_a0.5/akbar_arabic_rock_lora_nar.safetensors
mkdir -p /content/exp/quran_only/{base,quran_only,quran_ar_v2nar,current}
setsid nohup bash -c "
  OUT_DIR=/content/exp/quran_only/base        LORA_AR=$V2AR LORA_NAR=$V2NAR LORA_AR_SCALE=0.0 LORA_NAR_SCALE=0.0 INFERENCE/run_one.sh Ajam $SEED
  OUT_DIR=/content/exp/quran_only/quran_only  LORA_AR=$QAR  LORA_NAR=$V2NAR LORA_AR_SCALE=1.0 LORA_NAR_SCALE=0.0 INFERENCE/run_one.sh Ajam $SEED
  OUT_DIR=/content/exp/quran_only/quran_ar_v2nar LORA_AR=$QAR LORA_NAR=$V2NAR LORA_AR_SCALE=1.0 LORA_NAR_SCALE=1.0 INFERENCE/run_one.sh Ajam $SEED
  OUT_DIR=/content/exp/quran_only/current     LORA_AR=$QF_AR LORA_NAR=$QF_NAR INFERENCE/run_one.sh Ajam $SEED
" > /content/logs/quran_only.log 2>&1 & disown
```
(≈6.5 min/track on a T4, ~3 min on an L4 → 4 tracks is ~25 min on a T4.)

### 5. Judge by ear, blinded
Load the `ab-blind-eval` skill; build a blinded package from
`/content/exp/quran_only/{base,quran_only,quran_ar_v2nar,current}/*.wav`. Score
articulation of the hard letters (ح, خ, ع, أ, ق, ط) and note any recitation bleed.
No α / checkpoint is "the winner" — that follows the listening
(`docs/LORA_INVENTORY.md:7-10`).

### 6. Back up + continuity (session end)
- `python backup_to_gcp.py --inference --once` (mirrors `out/`, `agent_notes/`, logs).
- `vm-continuity status` must read OK before disconnecting; stamp it in the reply.

---

## Open decisions to confirm before step 4
1. **Arm B's NAR** — the literal ask is *base model* ⇒ NAR off (arm B). The
   practical candidate is v2 NAR on (arm C). Both are in the matrix; listen to both.
2. **Pron checkpoint** — use the run's **final** (step 8100). Intermediate
   checkpoints also exist (1500–7500) if the final sounds over-cooked; the donor
   sweep for a non-final ckpt would need `merge_pron_lora.py --pron <ckpt>` first
   (it merges v2 back in, so only use it for the AR+NAR controls, not arm B).
3. **Which maqam(s)/seed** — default Ajam + one seed; expand only if the probe is
   inconclusive.

## Ref
`docs/INFERENCE.md` (runner, prompts, output layout) · `docs/LORA_INVENTORY.md`
(what exists, hashes) · `docs/PRON_LORA_MERGE.md` (merge/scaling — history) ·
`docs/FUTURE_PRONUNCIATION_LORA.md` §4–5 (the ح/ع ceiling risk + cheaper levers).

## Session continuity (2026-10-04, CPU runtime)
- `vm-continuity` installed + watch loop running (`/content/logs/vm_continuity.log`);
  this session shipped to
  `gs://akbar-december-2024-backup/opencode_sessions/by_host/365ac80abf49/`.
- Restore this session on the fresh GPU VM:
  `vm-continuity hosts` → `vm-continuity pull --host 365ac80abf49` →
  `vm-continuity restore opencode -- --mode db` → reopen the session.
  Cold start (no restore) always works from this file + the repo.

