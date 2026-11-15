---
name: tf-kernel-contract-na-lines
description: Since main ~df7ba29a1 (11-04), v.sh's ci log shows "failed command" for test-kernel-contract with 7 HIP "N/A … not served there" lines, yet RC=0 — pre-existing on main, not a branch regression
metadata:
  type: project
---
Seen 2026-11-04 in the verifies of #2113, #2127, U2 and #1870, all based on main df7ba29a1 or b331731e6. It's absent on #2115, whose base de6c3bdae is older. The test process prints `N/A dense gemm dense_wmma12_gemm<…> on gfx1030/1100/1151: not served there` (new HIP contract rows after #2046), and the Zig build runner then prints `failed command: …/test`, but `ci RC=0`.
**How to apply:** don't treat that line alone as a branch failure. Diff against main's own verify, and look for `error:` lines or a non-zero RC. If GitHub CI ever goes red on it, raise it with ashhart as a main issue.
