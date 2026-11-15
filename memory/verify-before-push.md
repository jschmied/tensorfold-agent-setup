---
name: verify-before-push
description: The standing push-after-every-change go does NOT license pushing code that has not been run; syntax-checking and testing a helper in isolation are not verification
metadata:
  type: feedback
---

2026-09-14, user: **"dont push code until verified."** Said after I pushed an instrumentation
commit having exercised only its *reporting* block on synthetic data — the instrumented path itself
had never executed.

**What does not count as verified:**
- `ast.parse` / a syntax check. I shipped a `NameError` the same day that parsed clean (`os` unused
  in `scale_survey.py`), reported it green, and had to correct it.
- Testing a helper function in isolation when the call site is what changed. The per-layer
  `DSV41_REF_CB` parser passed standalone; only running it through the real `ExpertLoader` proved
  the *unset* case still leaves the FP4 path untouched.
- "It is behind an env gate and off by default." True and irrelevant — the rule is about the branch
  not carrying code nobody has run, not about blast radius.

**What counts:** the changed path executes, on the engine if it is engine code, and the result is
read. If the box is busy, hold the commit locally (`git format-patch` it) rather than pushing.

**Why:** [[push-own-repos-standing-go]] says push after every commit so work is not invisible. It
does not relax [[commit-after-tests-green]]. The two compose as: verify, then commit, then push —
not commit, push, verify later.

**How to apply:** before pushing engine code, name the run that exercised it. If there isn't one,
say so and keep the patch out of the branch. I reverted `3d0fd0d` on this basis rather than arguing
the gate made it safe.
