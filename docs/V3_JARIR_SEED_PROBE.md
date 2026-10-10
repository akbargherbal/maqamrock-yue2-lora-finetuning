# T4 probe — 5 random seeds × v3 final adapter × one Jarir poem

_Drafted + finalised 2026-10-10. Status: **executing (agent-run, background)**. Decisions in §7._

## 1. Goal

Listen to **5 takes of one song** produced by the **v3 final adapter**
(`v3_arabmaqamrock_lora.safetensors`, step 5000) with **5 fresh random seeds** and everything
else fixed — an adapter **seed-variance / reproduction** probe, ~1 h on a Colab **T4**.
Output: 5 WAVs + per-track sidecars, to be listened to (optionally blind).

## 2. ⚠️ Contamination — this poem is IN the training set

The Jarir poem used here (`سُمُّ الشُّعَرَاءِ وَكِيرُ القُيُونِ`, opening line
`أَعْدَدْتُ لِلشُّعَرَاءِ سُمًّا نَاقِعًا`) is a **v3 training track**: it appears as
`kurd_jarir_24072026_006_d0fd493c` and `…_007_7abae477` (both Maqam Kurd). The inference
lyric body is **byte-identical** to the training caption's (verified 2026-10-10).

So this is **not** a held-out generalisation test — it measures how the adapter **re-renders a
piece it trained on**, and how much it **varies across seeds**. That is a valid question; it just
isn't a quality-vs-held-out signal. (A genuinely held-out probe needs a fresh poem — the
held-out set is stale vs the 438; regenerate first.)

## 3. What is fixed vs varied

| | value |
|---|---|
| adapter | v3 final, converted AR+NAR pair (rank 32, scale 1.0/1.0) |
| song | the Jarir poem, **exact v3 training caption** (style + verbatim lyric tags) |
| cap | **auto q0.95 → 6500** `semantic_max_tokens` (the training-corpus quantile) |
| takes | **5**, fresh random seeds (`repeat: 5`; seeds drawn `< 2^32`, recorded in `batch_manifest.json`) |
| sampler | audio.cpp anchor defaults (`cot=off`, guidance 1.01, temp 1.0, rep-pen 1.2) |
| GPU | one T4; the 5 run **sequentially** (two concurrent runs can OOM the NAR graph) |

Prompt is byte-identical to a training caption, so **seed is the only variable**. Cap is the
corpus auto cap at **q0.95**: 484 Arabic letters → **6500** `semantic_max_tokens`. One prior Jarir
take truncated at 6500; if one does here it's flagged `truncated` in that track's sidecar
(re-render just that seed at 8000 and note it — don't change the other four).

## 4. Prep — CPU, off the GPU (**DONE** 2026-10-10)

The v3 adapter is converted (the converter is **torch-free** — raw `mmap`/`struct`) and banked:

| artifact (under `<base>/v3_arabmaqamrock_lora/convert/`) | bytes | sha256 |
|---|---|---|
| `v3_arabmaqamrock_lora_ar.safetensors` | 69,771,144 | `3531bb9106d2292eefe58eabe11ec08bb7dddc69554f2b016dc9f13f711fab18` |
| `v3_arabmaqamrock_lora_nar.safetensors` | 69,772,712 | `a7eabcadb22146048bcb5e65d04828ee9454559523ca161bd38c06060deb0cae` |

Source `…/output/v3_arabmaqamrock_lora.safetensors` (sha256 `37dba84a7fff301b159a30322bd6d631d34c6a85f1ef8667df969d6c7d39a37b`),
rank 32, α=rank, byte-level verified by the converter; provenance in `…/convert/MANIFEST.json`.
Reproduce: `python convert_aitoolkit_yue2_lora.py <final>.safetensors --out-dir convert`.
`docs/LORA_INVENTORY.md` updated (v3 style row; `loras/` promotion still optional).

## 5. T4 session (turnkey)

Prereq: `bash bootstrap/setup.sh --inference` finished clean (the notebook's "Inference setup"
block). Then one detached command does the rest — staging, dry-run, the 5 takes, and banking:

```bash
cd /content/maqamrock-yue2-lora-finetuning
setsid nohup bash INFERENCE/run_v3_jarir_seed_probe.sh \
  > /content/logs/v3_jarir_probe.log 2>&1 < /dev/null & disown
tail -f /content/logs/v3_jarir_probe.log
```

`INFERENCE/run_v3_jarir_seed_probe.sh` (idempotent; re-run resumes): refuses if the GPU is busy
(one-GPU rule), rsyncs `…/v3_arabmaqamrock_lora/convert/` → `/content/converter/out/v3`, runs
`generate.py --dry-run`, generates the 5 takes, then banks the run folder to
`…/v3_arabmaqamrock_lora/listening/<run>/`.

Manual equivalent (if you'd rather drive it by hand):

```bash
B="gs://akbar-december-2024-backup/OSTRIS_Arabic_Suno_Finetuning"
gcloud storage rsync -r "$B/v3_arabmaqamrock_lora/convert" /content/converter/out/v3
python INFERENCE/generate.py INFERENCE/songs.v3_jarir_seed.json --dry-run
python INFERENCE/generate.py INFERENCE/songs.v3_jarir_seed.json --label v3_jarir_seeds
```

Input JSON committed at `INFERENCE/songs.v3_jarir_seed.json` (1 song · `repeat: 5` · `cap: 8000`,
`lora: v3` → `/content/converter/out/v3/v3_arabmaqamrock_lora_{ar,nar}.safetensors`). Dry-run
off-VM: `plan: 1 song(s), 5 track(s); projected ~32 min on a T4 (~390 s/track)` — the measured
Jarir rounds (8:47–11:51/track on a free T4) suggest ~45–60 min in practice.

## 6. Outputs

`out/<YYYYMMDD-HHMMSS>_v3_jarir_seeds/`: `v3_jarir_<seed>.{wav,log,_time.txt,_gpu.csv,json}` ×5,
`batch_manifest.json` (the 5 seeds), `batch_summary.txt`, `prompts/`, `input.json`.

Optional: blind-package the 5 takes (`skills/ab-blind-eval` → `INFERENCE/prepare_ab_eval.py`) so
they're judged by ear without knowing the seed. Seeds are neutral, so blinding is mostly about
removing order bias.

## 7. Decisions (resolved by the user, 2026-10-10)

1. **Contamination (§2):** **accepted** — the poem appears 2× in the 438; that is not enough
   exposure to memorise. Proceed on the trained Jarir poem.
2. **Cap:** **q0.95 (auto → 6500)**.
3. **Conversion:** **now, CPU** (off the GPU).
4. **Blind package:** **no** — plain generation only.

The user granted reign to execute this plan autonomously, in the background, without blocking
the chat.

## 8. References

`docs/INFERENCE.md` (runner + JSON schema) · `docs/LORA_INVENTORY.md` (adapter library) ·
`results/jarir_qahh/README.md` (prior Jarir rounds + T4 timings) · `docs/text_to_duration_formula.md` (cap).
