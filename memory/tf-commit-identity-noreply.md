---
name: tf-commit-identity-noreply
description: "TensorFold commits use the GitHub noreply address 600316+jschmied@users.noreply.github.com, never the personal email"
metadata:
  node_type: memory
  type: feedback
  modified: 2026-10-04T11:34:43.834Z
---

TensorFold commits are authored as `Jürgen Schmied <600316+jschmied@users.noreply.github.com>`, not the personal
gmail address. Still no AI attribution line and no tool trailers in TensorFold commits or PR bodies.

**Why:** TensorFold's CONTRIBUTING asks for noreply addresses; jayleaton (#300) offered to re-author our commits and
the user said "ok, noreply address" (2026-10-04). Our earlier TF commits (#211, #303, #304, #318, #327, #328,
#300's taken commits) carry the personal address; the maintainers re-author at landing.

**How to apply:** the TF worktrees (`~/git/tf-kolibri`, `~/git/tf-pr300`, `~/git/tf-fp4x`) have the noreply
`user.email` in their repo config; for any new TF worktree pass `-c user.email=600316+jschmied@users.noreply.github.com`.
vLLM commits keep their own convention (Signed-off-by etc., see [[pr-ai-note-one-line]]).
