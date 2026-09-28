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

---

## Parking lot (questions to come back to — not a commitment)
- What is an encoder vs a decoder? Do they exist in this project?
- What *is* a "latent", concretely, and what does it look like here?
- Where does the VAE sit, and why is it a separate file?
- Why AR *and* NAR stages? What does each actually do?
- Is any of this "diffusion"? If not, how does it differ?
- What are the 3 billion numbers, and what do they mean?
