# Twenty Tracks a Month

### How a one-email setback became a model I own end to end

*A lessons-learned chronicle.*

---

## The day the exit closed

On 11 August 2026, an email arrived that changed the terms of a practice I had
spent months building.

My entire AI-music workflow ran on one platform. I had a pinned style template,
a set of scripts, a vocabulary of prompts hammered out over two and a half months
of trial and error. What I did *not* have was a way to get my own work out of the
building if the building decided to hold the door.

The email changed the export rule: downloads capped at twenty tracks a month.

For most users that is an inconvenience. For me it removed the floor. I don't
mean the output was precious — I mean the *access to my own output* was the
product. This is the same move you see everywhere now: let people work inside
your walls, then make leaving expensive. You can view your codebase only in the
editor. You can export your images only as a subscription. The work is yours; the
exit isn't.

The clean way to say it: **an output you can't export isn't an asset. It's a
lease.**

That distinction is what the next eight weeks were about.

---

## Stage one: inventory by controllability

The first move wasn't panic. It was triage — and the sorting key mattered more
than the effort.

Most people, hit like this, inventory what they *lost*: the songs, the credits,
the convenience. That's the wrong list, because it's the list you can't act on.
The useful list is sorted by **control**:

- **Gone.** The ability to generate at will on someone else's platform.
- **Portable.** The style template, the workflow scripts, the taste encoded
  inside them. These were the real intellectual property — not the songs.
- **Newly urgent.** Raw material I could still produce while the subscription
  was alive.

That template was worth more than any single track. Two and a half months of
trial and error had compressed into one file where *only the maqam name changes*
— every other field deliberately fixed, because early attempts to "improve" them
with an LLM introduced drift. A platform can revoke its songs. It cannot revoke a
file on my disk, and it cannot revoke the judgment that produced it.

So I spent down the credits, ended the subscription, and generated as much as I
could before the door shut. Not because I had a model to feed yet — I didn't —
but because **the raw material was the one asset nobody could take back.**

---

## Stage two: don't marry the first candidate

The first replacement I reached for did not work.

To be fair about it: an early open model produced Arabic that scored maybe 3.5
out of 10. Not "needs polish." *Wrong* — the pronunciation fell apart in ways
that no amount of prompting fixed. It would have been easy to rationalize:
*just needs fine-tuning.* That sentence has eaten more months than any other in
applied ML.

I killed it early, and the discipline paid later.

Meanwhile, the work that mattered was unglamorous: curating. Of roughly 2,281
candidate tracks, **438** survived selection. The filter — quality ratings,
consistent vocal character, clean lyric alignment — *is* the product. Anyone can
generate. Almost no one curates. **Curation is where quality is manufactured.**

---

## Stage three: prepare during the wait

I had a conviction that felt reckless at the time and looks obvious in hindsight:
a capable open-weights music model was *coming*. Not maybe. Coming.

If that's true, the rational thing to do while you wait is not to wait. It's to
build the thing the future model will need. So I worked on the dataset — the one
component that travels intact from one tool to the next, the one nobody can
discontinue.

**Bet on the inevitable. Prepare for it before it arrives.** The wait is
inventory time, not idle time.

---

## The unlock nobody announced

On 10 September, a new open model dropped. I heard about it the next day. Out of
the box it scored about 6.5 out of 10 on Arabic — genuinely promising, the first
candidate that didn't fall over.

It was also **not trainable.**

The model could *generate*; it couldn't be *improved*, because the piece that
converts audio into tokens was withheld. Capability had shipped; **access** had
not. The difference between the two is the whole game, and it's the kind of gap
that press announcements quietly skip.

Then, on 16 September, a stranger on the internet released the missing piece — a
real-audio tokenizer, built from scratch, given away. I watched that thread like
a hawk.

That was the actual turning point. Not the headline model — a component nobody
would write a blog post about. **The bottleneck is rarely the thing everyone is
excited about.** Find the dependency that's missing and watch *it*.

---

## Choosing tools as if your collaborator can't see

With a trainable model and a curated dataset, the last question was *how*.

I tried the GUI-first ecosystems. They were walls of unreadable state — nodes,
wires, parameters living in a canvas rather than a file. Even where they had an
API, the thing I needed to reason about was visual, and my collaborator — an AI
coding agent working alongside me — reasons in text. We were both blind to the
same object.

Then I found a trainer that was just YAML and a command line. Every knob in a
file. Every run tail-able. Every checkpoint a path. Everything *legible.*

That is no longer a matter of taste. **Choose tools whose entire state is text.**
In an agent-assisted workflow, legibility to a text-based collaborator is a
hard requirement, not a convenience — and it's why the last three weeks produced
259 commits while the canvas-based attempts produced frustration.

---

## What exists now

Three weeks after the repo's first commit:

- A curated dataset — 438 audio/caption pairs across four maqams, with a
  trigger token and classical Arabic poetic lyrics.
- A completed training run — 5,000 of 5,000 steps, final adapter converted and
  banked.
- A pipeline where **every layer is mine**: the data, the tokenizer, the
  trainer, the checkpoints, the adapter.

And the honest scoreboard: the output is at about **4 out of 5**, not yet the
5.5-grade experience I was used to on the platform that locked me out. I'm
tuning samplers and checkpoint selection to close that gap.

So this is not a story about beating the incumbent. It's a story about no longer
*needing* the incumbent's permission — which is a different and more durable
kind of winning.

---

## The lessons

1. **Ask what you control, not what you lost.** The loss list is inert. The
   control list is a plan.
2. **Codify your taste into portable artifacts.** A template file outlives a
   subscription. Judgment that stays in your head can be stranded; judgment
   written down cannot.
3. **Bank the raw material early.** During the grace window, make the thing that
   survives every future tool change.
4. **Prepare during the wait.** If a capability is inevitable, build what it
   will need before it arrives.
5. **Kill weak candidates fast.** "It just needs fine-tuning" is usually a
   rationalization for a dead end.
6. **Separate capability from access.** The headline release and the thing that
   actually unblocks you are rarely the same object.
7. **Choose tools by legibility.** Whole state in text, or your collaborator
   can't help you.
8. **Let the ear judge.** Don't let an undefined standard (is this *really*
   maqam Hijaz?) veto a result that clearly works. Perfection against an
   unfalsifiable benchmark is procrastination wearing a lab coat.
9. **Constrain on purpose.** Four maqams instead of forty, one variable instead
   of many — constraints made the problem solvable and the model learnable.
10. **Curation is the moat.** Generation is commodity; selection is craft.
11. **Persist what is expensive to regenerate.** Compute is rental. Keep the
    artifacts somewhere durable.

---

## The close

The email felt like a wall. It was a lock — and locks are engineering problems.

Two months on, I don't have the thing I lost back. I have something better: a
system where the exit can never be closed again, because I *am* the exit. The
music is mine all the way down, from a dataset I curated to an adapter I trained.

Grief on a deadline is just a project plan. The useful question was never
"how do I get my music back?" It was: **"what can I build that no one can take
away?"** Answer that, and the setback turns into the reason you ended up owning
the thing you used to rent.
