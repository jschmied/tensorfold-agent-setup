---
name: agent-brief-verify-paths
description: "Give subagents the exact verify script path and the new-family checklist; an agent missed v.sh and the contract_limits list"
metadata:
  type: feedback
---
On 2026-10-27 the LFM2 port agent reported `<scratchpad>/verify/v.sh` as missing, but it existed; it skipped the standard lean + full test. The full test then caught a `kernel_symbols` failure. A second gap (`contract_limits.zig` lacking `lfm2_moe`) was found only by the next agent.

**Why:** an agent only knows what the brief says, and these gates are TF-specific.

**How to apply:**
- In every TF code brief, give the commands verbatim: `WS=<worktree> bash <scratchpad>/verify/v.sh <scratchpad>/verify`, or `tools/zig/lean_check.py` + `lean_new.py` and `zig build test -Dnvcc`.
- For new images and families, point to the checklist in gpu-kernel-optimization topic 07: `kernel_symbols`, `contract_limits`, records.
- Rerun v.sh myself before any push when an agent says it couldn't.
