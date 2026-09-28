# agent_notes / current

**Date:** 2026-09-28 · **State:** no run active. Local machine (DELL), not Colab.
**Changed:** critique of `AGENTS.md` — what is actually wrong with the agent's operating
contract, written here for reading/TTS (not a command handoff). Replaces the mixed-LoRA
inference handoff (recoverable from git; the feature itself is in `INFERENCE/generate.py`
+ `docs/INFERENCE.md`).

---

# What's wrong with AGENTS.md

Ranked by cost to agent quality (not style). Line refs are to the file as read.

### 1. It forbids guessing, then makes ground truth expensive
Lines 8 and 26 say never answer from an earlier turn — but the Observability section
(58-68) hands me **seven** sources and no single command. "How's it going" = pid +
`monitor_loss` + two logs + CSV + sidecar pids + GCS freshness. The contract names the
exact failure mode and then does nothing to prevent it. Cheap ground truth *is* honest
ground truth; this is the highest-leverage gap, and it is upstream of every other finding.

### 2. It claims inference scope but has no inference contract
Line 13 lists inference/merge/pron as first-class modes and line 8 references inference
artifacts — yet there is no section on `audiocpp_inference`, `run_one.sh`, `_runs_status.log`,
per-track JSON sidecars, or the **manual-execution / report-from-files** policy that
`DECISIONS.md` records (and `IMPROVEMENTS.md` #10 flagged). A fresh agent honours the
declared scope and still gets inference wrong. Declared scope > delivered scope.

### 3. Internal contradictions
- Line 11: "**Nothing else.** Not a monitor… not a companion" — directly contradicted by
  the standing backup/continuity/listening duties (96-104), which are recurring companion
  work. Taken literally, I'd skip the session-end backup check.
- Line 56 permits running tests/smoke checks (only "check `nvidia-smi` first"); line 76
  says "**Never** run GPU-heavy work while a run *might* be active." "Might be active" is
  unbounded, so it forbids all my GPU work — the permission and the prohibition don't
  reconcile.

### 4. Duplication → drift, in the file a fresh agent trusts most
- The canonical-docs list appears twice (22 and 112), plus a third "consult the index"
  (26). Redundant when correct, silently conflicting when one is edited.
- Lines 83-92 restate `docs/START.md`; 96-104 restate `docs/BACKUP_RESTORE.md`. Copies
  of live docs go stale the moment the doc changes.
- `_Last revised: 2026-09-26_` (line 3) already predates `DECISIONS.md`'s 2026-09-27
  condensation — evidence the file is not reconciled, while being the most-trusted file.

### 5. Hardcoded facts that silently don't generalize
Line 60 asserts everything lives under `output/akbar_arabic_rock_lora/` — true only for
the main run. The pron run and `quran_long_aya_r8_s10` have different names/paths
(`docs/README.md` says so explicitly). And the whole file assumes Colab `/content` +
GCS + `nvidia-smi`, while current state is a local DELL box. Mode-dependence is declared
for *tasks* (line 13) but not for *environment*, so outside the main run the contract
quietly lies.

### 6. Unanchored thresholds → non-reproducible behaviour
"long-running" (49), "cheaply" (100, 104), "~5 lines" / "a few lines" (30), "might be
active" (76) have no anchors. I will interpret each differently per session; the same
situation yields different behaviour. That's the opposite of a contract.

### 7. No positive norm — what a good turn produces
The file is all "never" and where-to-look; it never says a claim must be falsifiable, that
I must state what I **verified vs assumed**, or what "done" means for a problem-solver.
Except for the narrow current.md rule, agents can fully comply while overclaiming — the
"Trust"/"Honesty" axes of `EXPERIENCE_CHECKLIST.md` are left unhooked by the contract.

### 8. No self-maintenance hook
No reconciliation step, no owner, no cadence. The most load-bearing doc is the only one
with no process for staying true — which is exactly why the experience lesson (checklist →
lowest scores → durable edit) dies each session. Lesson persistence has no mechanism here.

### Meta (self-implicating)
The current.md rules (28-33) say "copy/paste surface, not documentation… no narrative,"
and then the same file is git-tracked, GCS-mirrored, and the fresh-VM handoff target
(26). It's scoped as ephemeral, backed up as durable. This critique is itself the proof:
you asked for narrative analysis, and the only sanctioned place to put it is a file that
forbids narrative.
