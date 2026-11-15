---
name: tf-rebase-only-on-request
description: TensorFold PRs are rebased only when ashhart asks for it (user: likely a project rule); CONFLICTING alone is no reason
metadata:
  type: feedback
---
Don't rebase our open TensorFold PRs just because GitHub shows them CONFLICTING. Rebase only when ashhart (the maintainer) asks for it in the thread, or when the user explicitly says to.

**Why:** the user said on 2026-10-29 "rebase only if ashhart requests it (think that's project rule)". A rebase force-pushes and resets review state, and the maintainer merges or rebases on his own schedule.

**How to apply:** in watch reports, list conflicting PRs as information only. A rebase request from ashhart counts as a reviewer ask under the standing go: fix, verify, push, reply. Related: [[tf-atc-standing-go]].

**Refinement (2026-11-11):** the rule still stands; `docs/recipes/SKILL.md:37` on main still says "Maintainers rebase at landing, so don't force-push a branch under review just to follow main". But don't wait idle for the ask. When `pr-ready.py` shows a conflict in code, not one only in CHANGELOG.md (ashhart resolves those at landing, e.g. #2392), rebase into a local branch and rerun the evidence on it without pushing. When ashhart asks, push within minutes. A main change that alters semantics (like #2699 under #1503) shows up in that local rerun, before the ask.
