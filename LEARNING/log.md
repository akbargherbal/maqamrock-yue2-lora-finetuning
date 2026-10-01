# Session log (newest last) + parking lot

## Session 0 — 2026-09-28
- Created branch `user-learning` + this workspace; agreed the method
  (see `README.md`).
- Entry point: **TBD**.
- Next: **TBD**.

## Session 1 (side-quest) — 2026-09-28
- Installed **DeepSeek Harness** (`dsh` 0.1.7-rc.2) to try as the browser-based
  reading companion. Needs **Node >= 22.19** (repo `engines`); this VM's Node 20
  *silently no-ops* (`--help` prints nothing, exit 0). Fix: Node **v22.23.3** at
  `/opt/node22`, `dsh` installed globally into it. (Same root cause as the old
  WSL pnpm failure.)
- Running headless: `dsh web --no-open --host 127.0.0.1 --port 3080`; log
  `/content/logs/dsh_web.log`; it prints a `?token=...` URL for browser trust.
- Learned: `/api` sits behind a **browser-trust fence** — a forwarded public host
  gets **403** unless passed via `--trusted-host <host>`.
- Experiment: shared file channel `scratch/between-harnesses.md` so dsh (browser)
  and opencode (terminal) can leave each other messages in the workspace.

## Session 2 — 2026-10-01
- **Decision: scrap DeepSeek Harness (`dsh`) for this branch.** Too early/buggy to
  build on: difficult to install, slow to compile, breaks often.
- **Standing interface for this branch from now on: OpenCode Web** (this was the
  first Web session). TUI/CLI not used for `user-learning` going forward.
- Cleanup: removed `scratch/between-harnesses.md` (dsh-only experiment); updated
  the `current.md` note in `AGENTS.md` to point at OpenCode Web instead of `dsh web`.
- Next: resume a parking-lot thread (e.g. encoder vs decoder, or what a latent is).

## Session 2 (cont.) — 2026-10-01
- Landed the **photo-lab analogy** (after trying book / singer / alphabet):
  encoder = the **scanner** YuE2 didn't ship. Saved in `map.md` ("Mental model")
  + a reference table in `glossary.md`.
- Core finding: **Mothersuperior provided the missing encoder** — without it your
  own audio can't be read into YuE2's token/latent code, so there are no training
  targets. It shipped alongside a NAR "ink calibration" LoRA (the decoder fix).
- Correction on dataset origin: the 267 training tracks are **Suno generations**
  (the prompt script is a Suno builder; `prepare_yue2_dataset.py` consumes the Suno
  pipeline). So the LoRA distilled Suno's *rendering* of the maqam-rock spec, keyed
  to trigger `arabmaqamrock` — it learns from the audio, not the description.

---

## Parking lot (questions to come back to — not a commitment)
- What is an encoder vs a decoder? Do they exist in this project? *(started — see map.md "photo-lab analogy": encoder = the scanner)*
- What *is* a "latent", concretely, and what does it look like here?
- Where does the VAE sit, and why is it a separate file?
- Why AR *and* NAR stages? What does each actually do?
- Is any of this "diffusion"? If not, how does it differ?
- What are the 3 billion numbers, and what do they mean?
