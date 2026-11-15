---
name: minimal-builds-verify
description: User 2026-11-08 — run only the necessary minimum of builds/verifies; full CI set once on the final head before push
metadata:
  type: feedback
---
User 2026-11-08: "we should only run the necessary minimum of builds/verify" and "do only full ci if necessary".
Iterate with the touched families' tests only; the full CI set once on the final head before the push a PR/reply
needs; rerun only a failed step; no native/served build unless compiled CUDA code changes; reuse main binaries per
commit (~/notes/bins/<sha>/).

**Why:** verify jobs ran ~1,500 min over 96 runs (ds5 was on verify5); they held build slots and drained behind timing.

**How to apply:** put this in every agent brief that builds; rule text lives in ~/notes/jobs/README.md.
Related: [[gb10-job-dispatcher]], [[verify-before-push]].
