---
name: git-stash-shared-across-worktrees
description: git stash (refs/stash) is shared by all worktrees of a repo; parallel scripts that stash/pop in different worktrees swap each other's changes. Use a separate base worktree or patch files instead
metadata:
  type: feedback
---

`git stash` lives in `refs/stash`, and every worktree of a repo shares it. On 2026-10-26 two background scripts each ran `git stash` and `git stash pop` in different TF worktrees (`tf-wrfix` and `tf-spillwarn`). Each popped the other's change, so one test run and two builds measured the wrong code.

**Why:** a "with fix / without fix" A/B that toggles the fix through stash silently tests the wrong tree when anything else stashes at the same time.

**How to apply:** for an A/B without the fix, build from a separate detached worktree at the base commit, or save `git diff` to a patch file and `git apply -R` / `git apply` it. Never use stash in scripts while other agents or worktrees may be active. See also [[verify-before-push]].
