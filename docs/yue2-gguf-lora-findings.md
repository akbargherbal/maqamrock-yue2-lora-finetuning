# Running a LoRA on the Yue2-3B GGUF model: findings

*Research date: 21 September 2026. This is a fast-moving project (releases are days apart), so details may change.*

## The short version

- **Yes, it looks like you can use your LoRA with `audio-cpp/Yue2-3B-GGUF` for inference.** The runtime that uses these files (audio.cpp) has built-in LoRA support, added in mid-September 2026.
- **You probably do not need to convert or merge anything.** The LoRA is loaded alongside the model at run time.
- **A few details are not confirmed yet** (exact file format, exact command). They are listed in [Section 4](#4-still-needs-checking).

---

## 1. Plain-language glossary

| Term | What it means here |
|---|---|
| **Model** | A large file of numbers ("weights") that a program uses to generate something, here music. |
| **YuE2-3B** | An open music-generation model (`m-a-p/YuE2-3B`). It turns lyrics and a style description into a song. The "3B" means about 3 billion numbers. |
| **Inference** | *Using* a finished model to produce output. The opposite of training or fine-tuning. |
| **GGUF** | A file format that packs a model into a single file so it can run on ordinary computers with lightweight software, instead of a full research setup. |
| **Quantization** | Storing the model's numbers with less precision (e.g. 8-bit or 4-bit) so the file is smaller and uses less memory. Quality drops a little. |
| **LoRA** | A small add-on file that adjusts a big model's behavior (a style, a voice, a genre) without changing the big file. Think of it as a "filter" placed over the model. |
| **Runtime** | The program that actually loads the model and runs it. GGUF files only work with runtimes that understand them. |
| **VAE** | A separate component that turns the model's internal output into actual audio. Here it is a separate file from the main model. |
| **AR / NAR** | Two stages inside YuE2 that can each have their own LoRA. See the note in [Section 4](#4-still-needs-checking). |

---

## 2. Verified findings

"Verified" means I read it directly on the project's own pages (Hugging Face model card, GitHub release notes, GitHub pull requests).

### 2.1 What the repository contains

- The repository is a **repackaged copy of `m-a-p/YuE2-3B`** in GGUF format, made for a program called **audio.cpp**.
- It comes in three sizes of the main model:

  | File | Precision | Size |
  |---|---|---|
  | `yue2-3b-bf16.gguf` | Full quality | 7.26 GB |
  | `yue2-3b-q8_0.gguf` | 8-bit (compressed) | 4.26 GB |
  | `yue2-3b-q4_0.gguf` | 4-bit (more compressed) | 2.67 GB |

- It also has the **audio-producing component** as separate files (`yue2-vae-f32.gguf`, 531 MB, and `yue2-vae-f16.gguf`, 265 MB), plus small settings files and a tokenizer in a `sidecars/` folder. You need the main model **and** a VAE file.
- The license is **CC-BY-NC-4.0** (non-commercial), inherited from the original model.

### 2.2 It is not a general-purpose GGUF

- The file declares its architecture as `audiocpp`, meaning it is built for the **audio.cpp** runtime.
- Another third-party GGUF card for the same model says the popular llama.cpp tools cannot load this architecture. So tools that work for text-model GGUFs will not work here.
- The command-line program is `audiocpp_cli`, and the model card gives worked examples.

### 2.3 LoRA support exists

- The model card says: "LoRA support added in release 0.8.1."
- The audio.cpp release notes (v0.8.1, dated 2026-09-15) say YuE2 now supports **independent AR and NAR LoRA adapters** through the command line and the server. The web interface only has a control for the AR adapter.
- A merged code change (pull request #586, 17 September 2026) defines the settings:
  - `yue2.ar_lora` and `yue2.ar_lora_scale`
  - `yue2.nar_lora` and `yue2.nar_lora_scale`
- The older names (`yue2.lora`, `yue2.lora_scale`) were **renamed**, so older examples will not work as written.
- The scale setting controls how strongly the adapter is applied. Zero switches the adapter off completely.

### 2.4 What the developer tested

From the description of pull request #586:

- The results were compared against a separate Python calculation of the same math. Four tensors matched exactly. The remaining ones differed by tiny rounding amounts.
- Tests covered AR-only, NAR-only, both together, disabled, and no adapter. Repeated runs with the same settings gave identical audio, and returning to "no adapter" reproduced the original output.
- A run with the **8-bit (Q8) model plus both adapters** produced valid audio.
- The developer explicitly said the checks were short (about 3.8 seconds of audio) and **do not prove long songs match the Python original**.

### 2.5 Speed and memory (measured by the repository owner)

Test machine: NVIDIA RTX 5090, a 225-second song.

| Version | Time to generate | Peak GPU memory |
|---|---|---|
| Full quality (BF16) | about 60 s | about 12.5 GB |
| 8-bit (Q8_0) | about 39 s | about 8.9 GB |
| 4-bit (Q4_0) | about 44 s | about 7.8 GB |

These are the owner's numbers on a very high-end graphics card. Your speeds will differ.

### 2.6 Reported in a draft pull request (moderate confidence)

A community contributor's draft pull request (#614) describes existing behavior:

- LoRA files are placed in a `loras/` folder inside the model directory and referenced like `loras/<file>`.
- LoRA files are recognized by reading the header of a `.safetensors` file, not by the file name.

Because this is a draft written by someone other than the main developer, treat it as "probably right, confirm before relying on it."

---

## 3. Corrections to my earlier answers

I answered before checking the repository. These parts were wrong or misleading:

| What I said earlier | What is actually true |
|---|---|
| Merge your LoRA, then convert with llama.cpp scripts (`convert_hf_to_gguf.py`, `llama-quantize`). | Those tools do not apply. This is a different runtime with its own format. No merge should be needed. |
| Load the LoRA with llama.cpp's `--lora` flag after converting it to GGUF. | audio.cpp uses its own settings (`yue2.ar_lora` etc.) and appears to load the adapter as-is. |
| Suggested `Q4_K_M` and similar quantization levels. | The repository only offers BF16, Q8_0 and Q4_0. |
| "Might not support LoRA; check the README." | It does support LoRA (since v0.8.1). |
| The GGUF probably holds only part of the pipeline, with audio handled separately. | Roughly right: the audio-producing VAE is a separate file. |

The general explanation of what GGUF is and why quantization helps still holds.

---

## 4. Still needs checking

I could not confirm these. Please treat them as open questions.

### 4.1 Adapter file format (highest priority)

- **What exact format must the LoRA be in?** The examples I saw were adapters from other people's repositories (published as `.safetensors`). I do not know if a standard export from the common Python LoRA library (PEFT) loads directly, or needs renaming or conversion.
- **How to check:** Read the audio.cpp docs for YuE2 or the changes in pull request #586, and look at the layer names inside your LoRA file.

### 4.2 The exact command

- My example command is **inferred** from the option names and the model card's demo. It has not been run or confirmed.
- Unclear: whether the setting takes a **file path or a folder**, and whether a path outside the model folder works.
- **How to check:** Run `audiocpp_cli --help`, read the YuE2 documentation in the audio.cpp repository, or ask on the project's GitHub issues.

Inferred example, **unverified**:

```bash
audiocpp_cli --task gen --family yue2 --model <YUE2_GGUF> --backend cuda \
  --text $'[Verse]\n...' \
  --request-option 'style=English, ...' \
  --session-option yue2.model_gguf=yue2-3b-q8_0.gguf \
  --session-option yue2.vae_gguf=yue2-vae-f16.gguf \
  --session-option yue2.ar_lora=loras/my_lora.safetensors \
  --session-option yue2.ar_lora_scale=1.0
```

### 4.3 Which stage does your LoRA target?

- YuE2 has two LoRA slots (AR and NAR). I did **not** find a definition in the sources I read. My understanding is that AR is the main song-generating stage and NAR is a second refinement stage, but this is an **interpretation, not a confirmed fact**.
- **How to check:** Find out which part of the model you trained your LoRA on, and check the audio.cpp YuE2 docs for what AR and NAR mean.

### 4.4 Version and date mismatch

- The release notes list v0.8.1 as dated **15 September**, but the pull request that introduced the `ar_lora` / `nar_lora` names was merged **17 September**. It is unclear which release first contains those exact names.
- **How to check:** Build the latest `main` branch or the newest release, and confirm the options exist with `--help`.

### 4.4b Which version of the program to use

- Earlier notes on the model card said YuE2 support was only in a "dev branch." The current card says it is merged into main. Confirm you are building or downloading a version recent enough to include both YuE2 and LoRA.

### 4.5 Quality with the smaller (Q4_0) model

- Only the **Q8** model was reported tested with adapters. Q4_0 with a LoRA is untested in the sources I found. Start with Q8 or BF16 and compare.

### 4.6 Long songs

- The developer's LoRA checks were short clips. Whether your LoRA gives the same result on full-length songs, compared with the original Python version, is **not established**.
- **How to check:** Generate the same song with the original Python setup and with audio.cpp, using the same seed, and compare by ear.

### 4.7 Your own hardware

- All speed and memory numbers come from one high-end graphics card. Actual requirements on your machine are unknown. The model card mentions CUDA (NVIDIA); other backends are said to exist for related projects but I did not confirm them for this repository.

### 4.8 Licensing of your LoRA

- The base model is non-commercial. If your LoRA was trained on other people's music or voices, it may carry its own restrictions. This is not something I researched.

### 4.9 Other runtimes I did not evaluate

Search results showed other community projects that run YuE2 GGUFs:

- `yue2.cpp` (Serveurperso) and `yuey.cpp` (thepatch). The latter mentions "optional adapters" and says it converts adapters into GGUF form.
- I did not check whether these would suit a custom LoRA better. They are separate from audio.cpp and probably use different file layouts, so files are likely **not interchangeable** between them.

---

## 5. Suggested next steps

1. Get the latest audio.cpp (release v0.8.1 or newer) and run `audiocpp_cli --help` to confirm the LoRA options.
2. Read the YuE2 section of the audio.cpp docs and pull request #586 to find the required adapter format.
3. Inspect your LoRA file (layer names, which model parts it changes) to see whether it targets the AR or NAR stage.
4. Try it with the **Q8** model first, at scale `1.0`, then compare against scale `0` (adapter off) to confirm it has an effect.
5. If it fails to load, open a question on the audio.cpp GitHub issues with your LoRA's layer names.

---

## 6. Sources

- Model card: <https://huggingface.co/audio-cpp/Yue2-3B-GGUF>
- Runtime repository: <https://github.com/0xShug0/audio.cpp>
- Release v0.8.1: <https://github.com/0xShug0/audio.cpp/releases/tag/v0.8.1>
- LoRA pull request #586 (merged): <https://github.com/0xShug0/audio.cpp/pull/586>
- Web interface LoRA pull request #614 (draft): <https://github.com/0xShug0/audio.cpp/pull/614>
- Original model: <https://huggingface.co/m-a-p/YuE2-3B>
- Related community GGUF cards: `Serveurperso/YuE2-GGUF`, `thepatch/YuE2-3B-GGUF`, `ngquocvinh/YuE2-3B-GGUF` on Hugging Face
