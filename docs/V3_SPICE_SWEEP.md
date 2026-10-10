# v3 "spice" sweep — lift the Jarir probe from 4/5 to 5/5

_Plan written 2026-10-10 (CPU-only session; **not started**). Implement on a Colab runtime (§7).
Authority for settings: this doc + `config/v3_arabmaqamrock_lora.yml`. Output is listening-judged
by the user — the agent cannot hear audio._

Companions: [`V3_JARIR_SEED_PROBE.md`](V3_JARIR_SEED_PROBE.md) (the probe that produced the 4/5),
[`INFERENCE.md`](INFERENCE.md) (runner + input-JSON schema), [`LORA_INVENTORY.md`](LORA_INVENTORY.md).

## 1. What we're reacting to

The seed probe `audiocpp_inference/out/20261010-142358_v3_jarir_seeds` — 5 takes, all **exit 0,
none truncated**, adapter = v3 **final/5000** (`3531bb91…` / `a7eabcad…`), scale 1.0/1.0, `cot=off`,
sampler defaults (guidance 1.01, temp 1.0, rep-pen 1.2), cap 6500 (q0.95):

| take | seed | wall | WAV dur |
|---:|---:|---:|---:|
| 0 | 2640605763 | 9:57 | 232.7 s |
| 1 | 4128132630 | 9:38 | 233.6 s |
| 2 | 2604703505 | 9:09 | 212.8 s |
| 3 | 1135089524 | 9:30 | 222.8 s |
| 4 | 2246126983 | 8:59 | 219.0 s |

**User verdict: 4/5 good; the takes feel "flat / generic — like arabmaqamrock but not impressive".**
None is a cut-off, so this is a *settings* question, and it's testable.

## 2. Why "generic" — and what a checkpoint can't do

v3 trained with `cot: "off"` (config §model_kwargs; comment: *"your captions carry no melodic/ABC
info"*). So the LoRA learned **style + timbre**, not melody. Plain terms:

- a **composer** (the AR stage) invents the melody + arrangement;
- a **performer** (the NAR stage) renders it to audio.

The LoRA taught the *performer* a sound. **A different checkpoint re-tints the performer; it does not
make the composer more inventive.** "Needs improvisation / spice" is a *composer* problem → the
sampler + prompt + selection. "Samey sound" is a *performer* problem → adapter scale + checkpoint.

## 3. Levers and hypotheses

| lever | how | hypothesis |
|---|---|---|
| `guidance_scale` (default **1.01**) | `EXTRA_REQUEST_OPTS` | 1.01 ≈ near-unconditional → the model falls back on its prior. Raising it obeys the (very detailed) style text → more character. |
| `semantic_temperature` (default **1.0**) | `EXTRA_REQUEST_OPTS` | ↑ = more adventurous phrasing; too high breaks lyrics/pronunciation. |
| `semantic_repetition_penalty` (default **1.2**) | `EXTRA_REQUEST_OPTS` | ↑ = fewer loops/repeats. |
| AR adapter scale (**1.0**) | `LORA_AR_SCALE` | < 1 narrows the corpus less → more base-model inventiveness. |
| checkpoint (final 5000) | convert + swap pair | earlier = less-trained *sound* (this is the user's original question). |
| style-prompt wording | new style text | add improvisation cues (off the training distribution). |
| `cot` (**off**) | request option (needs verification) | with CoT the base model plans melody first — potential structural richness; **risky**, §9. |

## 4. Pass 1 — paired single-knob screen (what the Colab session implements)

One song, one **pinned seed** (`2640605763`, = probe take 0 so the `ref` arm is a determinism check),
cap 6500, `cot=off`, sequential. Each arm differs by exactly one knob.

| arm | adapter | AR/NAR scale | extra request opts |
|---|---|---|---|
| `ref` | final | 1.0/1.0 | — (must reproduce probe take 0) |
| `g1.5` | final | 1.0/1.0 | `guidance_scale=1.5` |
| `g2.5` | final | 1.0/1.0 | `guidance_scale=2.5` |
| `t1.2` | final | 1.0/1.0 | `semantic_temperature=1.2` |
| `t1.4` | final | 1.0/1.0 | `semantic_temperature=1.4` |
| `rp1.4` | final | 1.0/1.0 | `semantic_repetition_penalty=1.4` |
| `ar0.7` | final | **0.7**/1.0 | — |
| `ck4500` | ck 4500 | 1.0/1.0 | — |
| `ck3500` | ck 3500 | 1.0/1.0 | — |
| `ck2500` | ck 2500 | 1.0/1.0 | — |

**Budget: 10 arms × ~9.5 min ≈ 95 min** on a T4 (sequential; two NAR runs concurrently can OOM).

Then the user listens and ranks; we keep the best 1–2 configs.

## 5. Pass 2 — winner × seeds (the actual keepers)

Take the winning config and run **8 fresh random seeds** (cap 6500) → target ≥ 5/6 good. This is the
cheap, reliable half of "5/5": quality has variance, so we screen configs at n=1 and then sample the
winner.

## 6. Pass 1b — prompt variant (optional, keep separate so it doesn't confound Pass 1)

Same song, `ref` settings, but a **style variant** appending improvisation cues, e.g. after the
existing caption: *"Instrumental break with an improvised electric-guitar taqsim in Maqam Kurd;
vocal mawwal improvisation; call-and-response between voice and lead guitar; sudden dynamic swells."*
2 arms: `style_ref` vs `style_improv`, optionally × `t1.2`. Off-distribution — treat as a probe.

## 7. Implementation on Colab

### Stage A — CPU runtime (no GPU): convert the checkpoints, stage, validate

```bash
cd /content/maqamrock-yue2-lora-finetuning          # or: git clone the repo (main)
B="$(grep -h GCP_BACKUP_BASE /root/.secrets.env | cut -d= -f2-)"   # or the literal gs:// path
mkdir -p /content/v3_conv && cd /content/v3_conv
gcloud storage cp "$B/audiocpp_inference/converter/convert_aitoolkit_yue2_lora.py" .
for N in 000002500 000003500 000004500; do
  gcloud storage cp "$B/v3_arabmaqamrock_lora/output/v3_arabmaqamrock_lora_$N.safetensors" .
  python3 convert_aitoolkit_yue2_lora.py "v3_arabmaqamrock_lora_$N.safetensors" --out-dir "ck$N"
done
# outputs: ck<N>/v3_arabmaqamrock_lora_<N>_{ar,nar}.safetensors  (the converter echoes them)
for N in 000002500 000003500 000004500; do
  gcloud storage cp "ck$N/v3_arabmaqamrock_lora_${N}_ar.safetensors" \
                    "ck$N/v3_arabmaqamrock_lora_${N}_nar.safetensors" \
                    "$B/v3_arabmaqamrock_lora/convert/ck$N/"
done
```

Then create the two files below + dry-run (**no GPU**): `DRY=1 bash INFERENCE/v3_spice_probe.sh`.

**Input JSON** `INFERENCE/songs.v3_spice.json` — copy `INFERENCE/songs.v3_jarir_seed.json`,
replace `songs[0]` with a single pinned take (style + lyrics **verbatim**, unchanged), and drop the
`loras`/`repeat` keys:

```json
{
  "defaults": { "repeat": 1 },
  "songs": [
    { "name": "v3_spice", "style": "<…verbatim from songs.v3_jarir_seed.json…>",
      "lyrics": "<…verbatim…>", "seed": 2640605763, "cap": 6500 }
  ]
}
```

**Driver** `INFERENCE/v3_spice_probe.sh` (model on `INFERENCE/jarir_lever_probe.sh`; the per-arm
adapter + scale + `EXTRA_REQUEST_OPTS` go in via env, exactly as that script does):

```bash
#!/usr/bin/env bash
# Pass 1 of docs/V3_SPICE_SWEEP.md -- paired single-knob screen. Run DETACHED on the GPU VM.
set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; REPO="$(cd "$SCRIPT_DIR/.." && pwd)"
CONV=/content/converter/out
JSON="$SCRIPT_DIR/songs.v3_spice.json"
OUTROOT="${OUTROOT:-/content/audiocpp_inference/out/v3_spice_probe}"
: "${GCP_BACKUP_BASE:?source /root/.secrets.env}"
ARMS="${ARMS:-ref g1.5 g2.5 t1.2 t1.4 rp1.4 ar0.7 ck4500 ck3500 ck2500}"
DRY="${DRY:-}"
command -v nvidia-smi >/dev/null || { echo "no GPU"; exit 1; }
nvidia-smi --query-compute-apps=pid --format=csv,noheader | grep -q '[0-9]' \
  && { echo "GPU busy - refusing"; exit 1; }
cd "$REPO" || exit 1
arm_spec(){ case "$1" in
  ref)    echo "FINAL||1.0|1.0|" ;;
  g1.5)   echo "FINAL||1.0|1.0|guidance_scale=1.5" ;;
  g2.5)   echo "FINAL||1.0|1.0|guidance_scale=2.5" ;;
  t1.2)   echo "FINAL||1.0|1.0|semantic_temperature=1.2" ;;
  t1.4)   echo "FINAL||1.0|1.0|semantic_temperature=1.4" ;;
  rp1.4)  echo "FINAL||1.0|1.0|semantic_repetition_penalty=1.4" ;;
  ar0.7)  echo "FINAL||0.7|1.0|" ;;
  ck4500) echo "CK|000004500|1.0|1.0|" ;;
  ck3500) echo "CK|000003500|1.0|1.0|" ;;
  ck2500) echo "CK|000002500|1.0|1.0|" ;;
  *) return 1;; esac; }
mkdir -p "$OUTROOT"
for arm in $ARMS; do
  spec="$(arm_spec "$arm")" || { echo "unknown arm $arm" >&2; exit 2; }
  IFS='|' read -r kind n ascale nscale extra <<<"$spec"   # kind FINAL|CK ; n = ck step
  if [ "$kind" = "CK" ]; then
    ar="$CONV/ck$n/v3_arabmaqamrock_lora_${n}_ar.safetensors"
    nar="$CONV/ck$n/v3_arabmaqamrock_lora_${n}_nar.safetensors"
  else
    ar="$CONV/v3_arabmaqamrock_lora_ar.safetensors"
    nar="$CONV/v3_arabmaqamrock_lora_nar.safetensors"
  fi
  if [ ! -f "$ar" ] || [ ! -f "$nar" ]; then
    echo "[FAIL] arm=$arm missing adapter ($ar)" >&2; continue
  fi
  gargs=(); [ -n "$DRY" ] && gargs+=(--dry-run)
  echo "=== [arm $arm] ar=$ascale nar=$nscale extra='$extra' $(date -u +%FT%TZ) ==="
  LORA_AR_SCALE="$ascale" LORA_NAR_SCALE="$nscale" EXTRA_REQUEST_OPTS="$extra" \
    python INFERENCE/generate.py "$JSON" --lora-ar "$ar" --lora-nar "$nar" \
      --out-dir "$OUTROOT/$arm" --label "v3_spice_$arm" "${gargs[@]}"
done
gcloud storage rsync -r "$OUTROOT" "$GCP_BACKUP_BASE/v3_arabmaqamrock_lora/spice_probe" \
  && echo "banked -> $GCP_BACKUP_BASE/v3_arabmaqamrock_lora/spice_probe"
```

### Stage B — GPU (T4) runtime: run it

```bash
cd /content/maqamrock-yue2-lora-finetuning
bash bootstrap/setup.sh --inference > /content/logs/setup.log 2>&1   # wait; require no [FAIL]
B="$GCP_BACKUP_BASE"
gcloud storage rsync -r "$B/v3_arabmaqamrock_lora/convert" /content/converter/out   # final + ck*/ pairs
setsid nohup bash INFERENCE/v3_spice_probe.sh \
  > /content/logs/v3_spice_probe.log 2>&1 < /dev/null & disown
tail -f /content/logs/v3_spice_probe.log
```

Output: `/content/audiocpp_inference/out/v3_spice_probe/<arm>/` → one `v3_spice_<seed>.{wav,log,json,…}`
per arm, banked to `<base>/v3_arabmaqamrock_lora/spice_probe/`.

## 8. Provenance bug found (fix separately)

`batch_manifest.json`'s top-level `assets.lora_ar_sha256` = `747d5cfe…` = the **v2** adapter, and
`assets.checkpoint_step` = **3000** — because `fp` is built from the CLI-default pair
(`INFERENCE/generate.py:552`), not the per-song `lora` alias. The **per-track sidecars are correct**
(v3 `3531bb91…`). Fix: derive `assets` from the aliases actually used, or drop the field. Small,
non-blocking.

## 9. Risks / constraints

- **One shared GPU.** `nvidia-smi` first; never overlap; two concurrent NAR graphs can OOM.
- `guidance_scale` too high → artifacts; `semantic_temperature` too high → broken words/pronunciation.
- Checkpoint/scale changes move off the trained distribution — listen for loss of the maqam-rock voice.
- `cot` option is **unverified**: `run_one.sh` hardcodes `--request-option cot=off` *before* the extras;
  whether a later `cot=on` wins depends on the CLI (last-wins?). Verify on the VM before trusting it.
- Don't edit the adapter/JSON/config to "make it pass" — measure and report.

## 10. Success criteria

Pass 1 identifies ≥ 1 config that (a) the user rates clearly better than `ref` and (b) is *stable*
enough that Pass 2 gives ≥ 5/6 good takes. If no knob beats `ref`, the honest conclusion is "run more
seeds and select" — and we say so rather than tune noise.
