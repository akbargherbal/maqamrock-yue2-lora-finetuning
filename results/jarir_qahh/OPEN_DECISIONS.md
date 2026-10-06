# jarir_qahh — open decisions & reminders (durable)

Purpose: the running list of decisions we deferred, so a later session (or the agent) knows
what to change and why. Complements `agent_notes/current.md` (live, overwritten) — this file
is the durable one. Update it as things get decided.

## Locked in

- **Goal:** keep the maqamrock (Suno v2) singing style **and** clear letter articulation —
  ب heard as ب, ر clearly — **without** tajweed prosody bleeding into the singing
  (madd/waqf cadence, idghām, iqlāb — e.g. ب surfacing as م). "Not mere correct
  pronunciation — Tajweed principles followed by vocals."
- **α = 0.1**, quran_ahh_r8 (AR+NAR rank-32) merged into v2 via `merge_quran_lora.py`.

## Running / queued (2026-10-06)

1. **Prompt variants** (canonical / yours / mine) × 2 takes, α0.1, cap 8000 —
   `out/jarir_prompt_probe/`. Listening verdict **pending**.
2. **AR-vs-NAR scale split** (queued right after #1, no GPU overlap) —
   `out/jarir_arnar_probe/`, canonical prompt, seed 20261010:
   `ar100_nar100` (control) · `ar050_nar100` (cut cadence, keep articulation) ·
   `ar100_nar050` (attribution) · `ar050_nar050`.
   Driver: `/content/arnar_probe.sh`; log `/content/logs/jarir_arnar_probe.log`.
   **Stop:** `pkill -f jarir_arnar_probe`.

## Open — decide later

- **[DEFERRED by user] Merge-level change.** Options: (a) **NAR-only** quran merge — keep
  articulation, drop the AR recitation prosody entirely; (b) lower **α (0.05)**.
  User: *"I really don't know .. we'll think about that later."*
- **Winning prompt** → if it is not `canonical`, re-run the AR/NAR split on the winner.
- **Lyric tags.** `jarir_songs.json` lyrics are verbatim Suno (`[Intro | single clean guitar |
  …]`, inline `[guitars surge]`); training lyrics were canonicalized to `[Intro]` / `[Verse 1]`
  (`suno_to_songs.clean_lyrics`). Candidate variant.
- **mood** on / off / normalized.
- **Sampler extras** not yet tried: `guidance_scale` up (caption vs adapter),
  `semantic_temperature` down, `semantic_repetition_penalty` up (attack madd).
- **Persist.** Repo is **uncommitted** (`merge_quran_lora.py`, `results/jarir_qahh/`,
  `/content/jarir_prompt_probe.json`, the `cp -r` nesting gotcha). Needs a git push —
  user runs `bash bootstrap/github_auth.sh` first.

## Why (evidence)

- `config/quran_ahh_r8.yml:5-9` — *"the prior AR-only, rank-8 run could only move
  recitation prosody (madd/waqf): in YuE2 the **AR** picks the discrete semantic codes, but
  the **NAR** flow + VAE render the actual articulation"* ⇒ **AR = prosody, NAR = makhraj**.
- `docs/QURAN_FORMAT_PROBE.md` — quran_only (AR-only) carried recitation *prosody*, not
  phonemic accuracy. (NB: iqlāb/idghām attribution to AR vs NAR is **not** yet proven —
  the scale split is the test.)
