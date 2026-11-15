---
name: finish-before-posting
description: "Never post a half-finished run. If part of what was offered did not get measured, finish it first — do not publish the partial result with a caveat, and never narrate my own harness bugs upstream"
metadata:
  type: feedback
---

**2026-09-22, user deleted a post of mine on vllm#54076** with: *"deleted post, dont post after a
half fail"*.

The post carried a real result (the geometry divergence persists on stock main `1ea7c63f4`) but also
said generation was never exercised, because my runner breaks on "server UP", greps, and its cleanup
trap tore the server down before my follow-up completion could land. So it published an unfinished
run **and** explained my own harness race to upstream.

**Why:** a caveat does not make a partial result complete. To the reader it converts a clean finding
into a qualified one and puts my tooling problems in their thread, where they are noise. The offer
had been "run it on main"; delivering "ran it, but the half you flagged as untested is still
untested" is less than was offered, and it spends credibility.

**How to apply:**
- **Finish, then post.** If a run misses part of what was offered, re-run it complete. Do not post
  the partial with an apology attached.
- **Never narrate my own harness failures upstream** — races with cleanup traps, wrong greps, void
  checks that misfired. Those belong in our findings, not in someone else's PR.
- Design the runner so the whole measurement happens **inside** it: put the completion request in
  the runner, not in a follow-up shell racing the trap.
- Applies to a re-post too: after finishing, ask for a **fresh go**; the original go was for the
  original post. Related: [[upstream-post]], [[posting-check-thread-state-first]],
  [[verify-before-push]].
