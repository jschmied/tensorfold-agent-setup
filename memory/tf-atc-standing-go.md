---
name: tf-atc-standing-go
description: Standing go (2026-10-29) to use TensorFold's ATC board for every task — check/claim/start before work, overlap before PRs
metadata:
  type: feedback
---
User 2026-10-29: "standing go: use tensorfold ATC for any task". ATC defaults to the cwd's repo (dgx-spark-setup-guide = empty board) — always run from a TF worktree or pass `--repo ashhart/TensorFold`. CLI: `node ~/.claude/plugins/cache/atc-github/atc/0.7.0/src/cli/main.js` (or mcp atc_* tools).

**Why:** the user looked at the ATC board and saw nothing of our work — we had never checked in.
**How to apply:** before starting TF work: `atc check <issue>` then `atc claim`/`atc start`; pulse while working; `atc overlap` before opening/pushing a PR; `atc land`/`release` when done. Claims are public but covered by this go; other posts still need the user's go.
