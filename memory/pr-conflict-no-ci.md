---
name: pr-conflict-no-ci
description: A TF PR whose branch conflicts with main (even CHANGELOG only) gets NO GitHub CI; open new PRs on current main
metadata:
  type: feedback
---
2026-11-08: #2604 and #2606 were opened conflicting with main in CHANGELOG.md only (release 1.2.5 cut Unreleased);
GitHub ran no checks at all ("no checks reported", mergeable_state dirty). Replaying the commits on current main with
the CHANGELOG line moved under the new `## Unreleased` (code diff verified identical) started CI within a minute.
**Why:** pull_request workflows need a mergeable merge commit.
**How to apply:** open every new PR on current origin/main; before opening, `git merge-tree --write-tree origin/main HEAD`
must be clean. Already-reviewed PRs: still rebase only on ashhart's ask ([[tf-rebase-only-on-request]]).
