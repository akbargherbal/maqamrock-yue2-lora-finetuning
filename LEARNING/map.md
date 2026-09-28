# The map (living — update as we learn)

`[ ]` untouched · `[~]` seen it · `[x]` I can explain it.
An empty box you understand beats a filled one you don't.

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
Session 0 — picking an entry point. Nothing marked yet.
