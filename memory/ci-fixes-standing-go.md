---
name: ci-fixes-standing-go
description: "Standing go (2026-10-21): fix and push CI failures on our own upstream PRs without asking; run lean_check before every TF push"
metadata:
  node_type: memory
  type: feedback
  modified: 2026-10-21T12:42:00.898Z
---

When GitHub CI fails on one of our own PRs because of our change (lint, lean_check, tests), fix it, verify it locally, push a new commit (no rewrite) and report. Don't ask first.

**Why:** the user said "yes, dont ask for it" on 2026-10-21, after #1143/#1147/#1155 failed the TF `zig` job on `lean_check` (multi-line comments, comments over 120 columns, files over 600 lines). The Flash-Next agent never ran `lean_check`, while our PR checklists claimed "comments are one line".

**How to apply:**
- Before pushing any TF branch, run `python3 tools/zig/lean_check.py` against the merge base (CI runs `lean_new.py` base vs head) and require 0 new findings. Agents' briefs must say so.
- Failures that aren't ours, like main's `zig-windows` compile errors or a flaky Electron `pull.test.ts`, are only reported, not fixed.
- Related: [[review-fixes-standing-go]], [[verify-before-push]].
- Before posting an agent's "ready" branch, run the full `zig build test -Dnvcc=/usr/local/cuda/bin/nvcc` myself (zig is at ~/opt/zig-aarch64-linux-0.17.0/zig and is not on the tmux PATH). The half-tiles draft claimed ready and failed to compile its tests.
