# Mix plan — `v3_arabmaqamrock_lora` × `arabic_instrumental_lora` (style × style)

_Status: **artifacts built and verified 2026-11-13** (α = **0.1 / 0.2** only — a0.3 and a0.5
were built, then deleted the same day when the user rejected high α; see §2), converted,
uploaded to `<base>/arabic_instrumental_lora/mix_v3/` with `MANIFEST.json`). Nothing has been
**rendered or listened to yet.** This doc is the repeatable procedure for the three stages and
the decision rule — not a claim that any α wins._

Question it answers: **does adding the instrumental style adapter improve how v3's takes are
performed** (real instruments, ornamentation, human timing, section dynamics) — and at what α
does that gain start costing the thing v3 exists for (sung Arabic lyrics, maqam-rock character)?

Authorities: merge math + scaling convention = `docs/PRON_LORA_MERGE.md`; the tool =
`merge_quran_lora.py --help`; render = `docs/INFERENCE.md`; rating = `docs/LISTENING_EVAL.md`.

---

## 0. Is a CPU VM enough? Yes — for stage A

Measured on a local CPU box (2026-11-13), per merge: **0.47 s**; per conversion: **0.27 s**;
download of the two source adapters (224 MiB): **20 s**; upload of four converted arms
(1.06 GiB): **~1 min**. No GPU is touched at any point in stage A. Peak disk ≈ 1.6 GB
(4 fused + 4 converted pairs), RAM < 2 GB.

**You do not have to repeat stage A at all** — those outputs already exist and are verified.
Run it only to (a) rebuild with a different α list, or (b) independently reproduce the
artifacts. If neither is needed, go straight to stage B.

---

## 1. The three stages

| stage | where | what | GPU? |
|---|---|---|---|
| **A — build** | any CPU VM | stage sources → merge α grid → verify → convert → upload | no |
| **B — render** | GPU VM (sm80/sm75 binary) | pull arms → dry-run → batch render → mirror to GCS | yes |
| **C — listen** | your machine | blind package → rate → apply the decision rule | no |

Arm names are fixed: `v3` (control), `a0.1`, `a0.2`. **`a0.3` / `a0.5` were rejected and
removed 2026-11-13** — do not rebuild them unless that decision is revisited.

---

## 2. Stage A — build the grid (CPU only)

```bash
B=gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning
git clone https://github.com/akbargherbal/maqamrock-yue2-lora-finetuning.git
cd maqamrock-yue2-lora-finetuning
mkdir -p /tmp/mix/src /tmp/mix/grid /tmp/mix/conv /tmp/mix/tools

# sources + the converter (the converter lives in GCS, not in this repo)
gsutil cp "$B/v3_arabmaqamrock_lora/output/v3_arabmaqamrock_lora.safetensors" \
          "$B/arabic_instrumental_lora/output/arabic_instrumental_lora.safetensors" /tmp/mix/src/
gsutil cp "$B/audiocpp_inference/converter/convert_aitoolkit_yue2_lora.py" /tmp/mix/tools/
```

**Gate 1 — the sources are the published ones.** Expected `sha256sum`:

```
37dba84a7fff301b159a30322bd6d631d34c6a85f1ef8667df969d6c7d39a37b  v3_arabmaqamrock_lora.safetensors
cf6d44bbf4c03b28b2511e03c985e1d49894f6d4b2508a23a8f2bda3182e3584  arabic_instrumental_lora.safetensors
```

The first must equal `source_sha256` in `<base>/v3_arabmaqamrock_lora/convert/MANIFEST.json`;
converting it must reproduce the HF pair (`ar 3531bb91…fab18`, `nar a7eabcad…0cae`). If either
check fails, stop — everything downstream would be built on the wrong file.

```bash
# merge: v3 = carrier (--v2), instrumental = donor (--quran); α dials the instrumental side
for A in 0.1 0.2; do
  python3 merge_quran_lora.py --alpha "$A" \
    --v2   /tmp/mix/src/v3_arabmaqamrock_lora.safetensors \
    --quran /tmp/mix/src/arabic_instrumental_lora.safetensors \
    --out  "/tmp/mix/grid/v3instr_a${A}.safetensors"
done
```

**Gate 2 — the merge is arithmetic, not vibes.** Two checks (both were run when this doc was
written):

- `--alpha 0` must be **tensor-identical** to v3 (`torch.equal` over all 448 tensors). This is
  what makes the control arm free.
- for each α, the dense delta must satisfy `B_mix @ A_mix == B_v3 @ A_v3 + α · (B_instr @ A_instr)`
  on **all 224 projections**. At α=0.5 (a power-of-two scale, so the folded block is exact in
  bf16) the measured max abs error was 3.0e-8; at the shipped α=0.2 it is 3.5e-5 (rel 4.6e-4),
  which is bf16 rounding of the α-scaled donor block — not an arithmetic error.

```bash
for A in 0.1 0.2; do
  python /tmp/mix/tools/convert_aitoolkit_yue2_lora.py \
    "/tmp/mix/grid/v3instr_a${A}.safetensors" \
    --out-dir "/tmp/mix/conv/a${A}" --stem "v3instr_a${A}"
done
sha256sum /tmp/mix/conv/a*/*.safetensors | tee /tmp/mix/converted_sha256.txt
```

Expected: `rank 64` on both branches, and the converter's own line
`byte-level verification against the source: OK` for each file.

```bash
# upload (an existing prefix — re-running overwrites the same four arms)
gsutil -m cp /tmp/mix/conv/a0.1/*.safetensors "$B/arabic_instrumental_lora/mix_v3/a0.1/"
# … a0.2 likewise, then the manifest (it lists only the arms that exist)
gsutil cp /tmp/mix/MANIFEST.json "$B/arabic_instrumental_lora/mix_v3/"
```

The manifest records: α, both source shas, the merged-fused sha, both converted shas, the tool
strings, and the δ-norm ratios. Ship it with the arms or the α values stop being checkable.

### α grid, and why these four

‖dW_instr‖ / ‖dW_v3‖ = **0.985** (AR) / **0.878** (NAR) — the donor is the same size as the
carrier, so α is not a small knob:

| α | share of the AR style delta | reading |
|---:|---:|---|
| 0.1 | 8.9 % | may be below the audibility threshold |
| 0.2 | 16.5 % | first likely audible step |
| 0.3 | 22.8 % | built, **rejected 2026-11-13** (high α does not work) |
| 0.5 | 33.0 % | built, **rejected 2026-11-13** |

Low ceiling on purpose: the donor's captions are `Middle Eastern fusion, instrumental.` +
**tags only, no words**, so its AR (conditioning) delta pulls toward "instrumental, no vocal".
That is the thing v3 does not have and the thing this mix can most easily damage.

---

## 3. Stage B — render the grid (GPU VM)

GPU rule first: `nvidia-smi` must be clean and no `run.py` running — no overlap, ever.

```bash
B=gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning
gsutil -m rsync -r "$B/arabic_instrumental_lora/mix_v3" /content/mix
mkdir -p /content/mix/v3
gsutil -m cp "$B/v3_arabmaqamrock_lora/convert/v3_arabmaqamrock_lora_"*.safetensors /content/mix/v3/
```

The spec is committed: `INFERENCE/input_mix_v3instr.json` — 5 arms, **Hijaz** prompt from the
staged `prompts/Hijaz_{style,lyrics}.txt`, seed 101, `quantile 0.95` → cap **7250** for every arm
(same lyrics ⇒ same cap), one `lora` alias per song.

```bash
python INFERENCE/generate.py INFERENCE/input_mix_v3instr.json --dry-run   # existence + time
setsid nohup python INFERENCE/generate.py INFERENCE/input_mix_v3instr.json \
  --label mix_v3instr > /content/logs/mix_v3instr.log 2>&1 & disown
```

**Do not add `--no-trigger` here.** The stage style file already begins with `arabmaqamrock`,
and the mix's conditioning branch is v3 — v3's prompt shape is the one to keep. (`--no-trigger`
is a rule for the *instrumental-only* adapter, which was trained on a different prefix.)

Budget: **~32 min on a T4** (dry-run projection, 5 tracks), **~10–12 min on an A100**.

---

## 4. Stage C — listen and decide

1. Pull the batch (`…/audiocpp_inference/out/<run>/`) and, for a blind pass, build a package
   with `INFERENCE/prepare_ab_eval.py` (one folder per arm, matching stems) — or stage
   `v3/a0.1/a0.2` as three folders and use the rating app with `--blind`.
2. Scorecard: `INFERENCE/scorecards/arabic_instrumental_quick.json` if you want speed;
   the 1–5 breakdown in `…_style.json` if you want to separate performance from production.
3. **Pre-written decision rule** (so the result cannot be rationalised afterwards):
   - pick the **smallest** α whose `overall` beats the `v3` control **and** whose vocals do not
     degrade (no lost words, no dropped vocal sections);
   - if no α beats v3 on `overall`, the answer is **α=0** — do not ship a mix to justify the merge;
   - artifacts worse than v3 = that α is out regardless of style gain;
   - if 0.1 ≈ v3 exactly, say so: the donor is inaudible on this prompt and the grid ends there.
4. Record the verdict next to the α it belongs to, plus the converted sha256 of the winning arm.

---

## 5. Failure modes

| risk | effect | guard |
|---|---|---|
| merging the wrong v3 file | everything downstream is off-spec | Gate 1 (source sha vs convert `MANIFEST.json`) |
| α entered as a percentage (e.g. `--alpha 30`) | 30× the donor, garbage audio | α ∈ [0, 1]; the printout says `alpha: 30.0` |
| forgetting the converter | audio.cpp cannot load a fused file | stage A ends with `rank 64` pairs |
| expecting rank 32 | file size looks "wrong" | rank 64 is the point: 32 + 32 |
| `--no-trigger` copied from the instrumental round | v3's prompt shape breaks | not passed in stage B |
| `cap` allowed to vary per arm | durations differ ⇒ unfair A/B | one q/cap for all arms (7250) |
| trusting the merged-fused sha256 | safetensors metadata order is nondeterministic | verify the converted pair instead |
| declaring a winner on 1 prompt | over-reading | 1 prompt ranks α; confirm the winner needs 2–3 prompts |
| high α "sounds more Arabic" | it is mostly the donor's instrumental bias | vocal/lyric check is part of the rule |

---

## 6. Checklist

- [ ] Stage A (only if rebuilding): Gate 1 shas ok · merge loop done · α=0 identity check · delta-sum check
- [ ] converted pairs exist at rank 64 with `byte-level verification: OK`
- [ ] `MANIFEST.json` uploaded next to the arms
- [ ] `nvidia-smi` clean before stage B
- [ ] arms pulled to `/content/mix/{v3,a0.1,a0.2}`
- [ ] `--dry-run` shows 5 songs, cap 7250, seed 101, five distinct loras
- [ ] batch rendered detached, log `/content/logs/mix_v3instr.log`
- [ ] batch mirrored to GCS (`backup_to_gcp.py --inference`)
- [ ] blind package built, `KEYS.txt` opened only after scoring
- [ ] decision rule applied as written; winning α + its sha recorded
