---
name: atc-release-stale-claims
description: At every 2-hourly watch, check my ATC claims and release the stale ones (user 2026-11-04)
metadata:
  type: feedback
---
At every 2-hourly watch, run `atc_status` on ashhart/TensorFold and look at my claims (`mine: true`).

Release a claim when any of these holds:
- its PR has merged and nothing of ours is left on the issue;
- someone else took the work;
- I dropped it;
- it shows up in `refreshDue` and I'm not working on it.

Renew the ones I'm actively working on when they show up in `refreshDue`. Report releases in the watch line.

**Why:** the user said "release claims what are stale regularly" (2026-11-04). ATC caps claims at 8, and stale claims kept blocking new ones (claimLimit on #1870 and #2165). See [[tf-atc-standing-go]].

**How to apply:** a release or renew is covered by the ATC standing go, so no extra approval is needed. Never release a claim whose work is still in progress in a local worktree.

**Correction 2026-11-05:** releasing #2005 (an RFC with open stacked PRs and planned next steps) made ashhart ask "is the RFC paused, or handed on?". I re-claimed it. Don't release an RFC or a multi-PR issue while we still plan further steps on it, even when the open PRs only wait on the maintainer.
