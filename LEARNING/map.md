# The map (living — update as we learn)

`[ ]` untouched · `[~]` seen it · `[x]` I can explain it.
An empty box you understand beats a filled one you don't.

## Mental model — the photo-lab analogy

The picture that made the encoder click.

| Photo-lab thing | In YuE2 |
|---|---|
| the photo lab (the model) | YuE2-3B |
| the lab's private, unreadable image format | the tokens / latents (its alien code) |
| **printer** — code in → photo out | decoder: AR + NAR + VAE (**generation**) |
| **scanner** — photo in → code out | the **encoder / tokenizer head** (Mothersuperior's gift) |
| the note taped to each photo | the caption ("Maqam Hijaz, cinematic rock...") |
| studying the scanned photos | LoRA fine-tuning |
| ink / colour calibration | the NAR LoRA (prints look like real photos) |

The story in five steps:

1. YuE2 is a photo lab with a **printer** but **no scanner**. Hand it a note and it
   prints a photo — it always could.
2. You bring 267 photos + notes to teach it your look; the lab **can't read them**
   (they aren't in its private format).
3. Mothersuperior delivers the **scanner**: your photos become readable files in the
   lab's own code.
4. The lab **studies** those files (the LoRA) and learns your look.
5. Now hand it a fresh note and it prints a **new photo in your look**.

Where it leaks: the scanner is **lossy** (vibe in, fine grain out — the v6–v9 fight);
"studying" is blind maths, not thought; each lab invents a **different** private
format.

## Inference — how a song gets made (our current batch)

    manifest JSON  (manifests/batch_36_songs.json)
      -> generate.py          parse songs, pick cap from the lyrics, seeds, LoRA
      -> run_one.sh -> audiocpp_cli
           prompt + lyrics -> [ ] tokens (tokenizer)
           [ ] AR stage   (autoregressive, + AR LoRA)      <- one token at a time?
           [ ] NAR stage  (non-autoregressive, + NAR LoRA) <- many at once / refine?
           [ ] VAE        (yue2-vae-f16.gguf)  latent <-> audio
           -> 48 kHz stereo .wav  + sidecars (.log, _time.txt, _gpu.csv, .json)

## Training — how the LoRA was made

    dataset (/content/yue2_dataset: captions + audio)
      -> ai-toolkit
      -> [ ] forward pass + loss     (loss_log.db tracks it)
      -> [ ] gradients / backprop
      -> [ ] optimizer step, checkpoints
      -> [ ] LoRA adapter (.safetensors, fused)
      -> convert_aitoolkit_yue2_lora.py -> unfused {ar,nar}.safetensors
      -> loaded at inference (above)

## Outside terms — where do they fit?

  [ ] transformer / attention
  [ ] token / tokenizer / embedding
  [ ] weights / parameters  ("3B")
  [ ] autoregressive (AR) vs non-autoregressive (NAR)
  [ ] latent
  [ ] VAE
  [ ] diffusion  (does it even apply here? YuE2 looks LM-based, not diffusion)
  [ ] LoRA
  [ ] quantization / GGUF
  [ ] guidance_scale / temperature / repetition penalty

## You are here
Session 2 — the photo-lab analogy landed (encoder = the scanner YuE2 didn't
ship). Pipeline boxes below still unmarked on purpose.
