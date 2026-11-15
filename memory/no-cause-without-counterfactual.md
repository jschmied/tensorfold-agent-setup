---
name: no-cause-without-counterfactual
description: "State no cause until the alternative is measured — this single habit produced 10 of 13 errors in one day, and each counterfactual cost minutes"
metadata: 
  node_type: memory
  type: feedback
  modified: 2026-09-12T10:40:02.596Z
---

**Never state why something happened until the alternative has been measured.** Not "read the code
and it looks like X" — measured, with the other condition run.

**Why:** on 2026-09-12 the user asked whether our error rate came from an over-long, topic-mixed
chat. Classifying that day's ~13 mistakes: 3 were attention slips, **10 were this one habit**, and
every one of the ten would have happened in a fresh context. They are not a context problem, they are
a discipline problem, and the counterfactual was cheap in every single case:

| claim asserted | what one measurement showed | cost |
|---|---|---|
| "0.6.18 drops the sm121 cubins, do not upgrade" — published for 11 days | opened both wheels: **neither** ships an sm121 artifact, `*_sm120` identical | 4 min |
| "the 13-minute start was the version-scoped autotune cache" | timed the other version: 11:20 / 12:01 vs 11:54 — it is just what loading 123 GB costs | 1 grep |
| "no PTX for sm_121, so it is an arch gap" | errno is `cudaErrorNotSupported` (801); a missing cubin is **209** | 1 lookup |
| "make the clamp unconditional" | traced it: `smem_size` **is** `chunk_size` in bytes; clamping under-allocates and runs out of bounds | 4 greps |
| "fnmain3 is a prod regression vs fnmain2" | the differing cell also held our tile-union kernel *and* torch.compile on/off | 2 runs |
| "duplicated combining marks" | read an output: it is a **substitution**, and another arm was a fluent translation | 1 print |

**How to apply:**
- Before writing a cause into a finding, a commit message, or anything public, ask: *what did I run
  that would have come out differently if this were false?* No answer ⇒ it is a hypothesis, label it.
- **Read an output, not a counter.** A metric that aggregates cannot distinguish the failure modes it
  aggregates; three separate defects hid behind one "corrupt" count for a whole morning.
- **Check the errno / the artifact / the log, not the dispatch code.** Reading selection logic
  produced three wrong claims in one morning ([[kernel-roster-from-logs]]).
- When a differing cell is claimed, verify it is the *only* thing that moved — `method.md` says the
  knob must reach the cell, which is weaker and let a contaminated A/B run for five rungs.
- The corollary that makes this cheap: the counterfactual is nearly always already available — an
  older log, the other venv, a second wheel, one `sed -n`.

Mechanical companion rule: **commit messages go in a file, never a heredoc containing backticks.**
Command substitution ate a clause three times in one day and once created a stray file in the repo.


**A completion sentinel cannot catch a command that succeeds at the wrong thing.** `qnext` marks a
job `done` on its `== ALL DONE ==`; an `aria2c` given six URLs fetched one file, exited 0, and the
sentinel fired correctly. The guard covers *failure*, not *wrong intent* — so a job definition still
needs its own success criterion (here: count the files you asked for). Recorded 2026-09-12.

Related: [[diff-against-known-good-artifact]] (the artifact beats its description),
[[acceptance-is-not-quality]], [[check-field-before-expensive-steps]].
