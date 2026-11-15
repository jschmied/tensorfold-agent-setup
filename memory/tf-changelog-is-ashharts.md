---
name: tf-changelog-is-ashharts
description: "TF (11-09): ashhart places CHANGELOG lines at landing; don't add CHANGELOG commits to PRs unless he asks"
metadata:
  node_type: memory
  type: feedback
  modified: 2026-11-09T03:03:05.688Z
---

ashhart 2026-11-09 on #2528 and #2606: "the CHANGELOG line is ours to place at landing" (folded our CHANGELOG commits out
of #2528). On #2580 he explicitly asked for one line, so: add a CHANGELOG line only when he asks on that PR.

**Why:** a CHANGELOG hunk is the usual cause of a PR going CONFLICTING/DIRTY, and a conflicting PR gets no GitHub CI
([[pr-conflict-no-ci]]); every main landing re-breaks it, forcing replays.

**How to apply:** new TF PRs: no CHANGELOG commit; put the proposed line in the PR body ("CHANGELOG (Unreleased): ...").
pr_check's "no Unreleased bullet" warning is advisory. Tell agents in briefs. Existing PRs: leave as they are unless they
conflict; then drop the CHANGELOG commit instead of replaying it.
