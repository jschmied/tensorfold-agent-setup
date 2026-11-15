---
name: review-fixes-standing-go
description: Reviewer-requested changes AND rebases of our CONFLICTING upstream PRs are pre-approved — fix/rebase, verify, push, reply without asking
metadata:
  type: feedback
---

When a maintainer/reviewer (e.g. ashhart on TensorFold, turboderp on exllamav3) requests changes on one of our PRs, do them right away: fix, test (incl. mutation check), push to the fork, and post the reply — no "should I?" question.

**Why:** 2026-10-15, after I asked before fixing ashhart's #848/#874 points: "yes of course, dont ask for requested changes".

**How to apply:** covers only what the reviewer asked for (plus a short reply naming commit + evidence). New proposals, new PRs, scope changes beyond the request, or posts not answering a review still need the user's go. Still verify before push ([[verify-before-push]]), re-read the thread before posting ([[posting-check-thread-state-first]]), TF identity/no AI trailers. Report what was done afterwards.

**Rebases (2026-10-16, "go for rebase, standing rule"):** when one of our open upstream PRs goes CONFLICTING, rebase it onto upstream main, re-run its verification, force-push to the fork and (if useful) leave a one-line note on the PR — no need to ask. Keep the commit set and messages; keep a local `<branch>-pre-rebase` backup ref. Report afterwards.

**SUPERSEDED for TensorFold (2026-10-17):** ashhart's new docs/recipes/SKILL.md says "Maintainers rebase at landing, so don't force-push a branch under review just to follow main." So on TensorFold: do NOT rebase our PRs just because they show CONFLICTING; rebase only when ashhart/a reviewer asks (then it's a review fix). The 2026-10-16 rebase of 8 PRs predates this rule. Other repos: the standing rebase go still applies.
