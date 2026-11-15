---
name: worktree-name-drafter-trap
description: A TF worktree path containing "drafter" fails server/benchmark_run_test.zig:196 (bare-word check on output with temp paths)
metadata:
  type: reference
---
2026-11-08: `benchmark_run_test.zig:196` asserts `!r.has("drafter")` over all stdout/stderr, which include temp paths under
the cwd. Worktree `tf-ds41-drafter` -> fails every run; same binary from another path passes (1178/0). Not a main bug.
Name worktrees without "drafter" (e.g. tf-ds41-dr). Details ~/notes/ledger/benchmark-run-test.md.
