---
name: cuda-launch-blocking-finds-async-faults
description: reach for CUDA_LAUNCH_BLOCKING=1 FIRST when a CUDA fault names a kernel that makes no sense
metadata:
  type: feedback
---

When an illegal-memory-access traceback names a kernel that has no business faulting, the named
kernel is the next `load_binary`/launch after an earlier async fault — not the culprit. Set
`CUDA_LAUNCH_BLOCKING=1` and re-run; the faulting launch then reports itself.

**Why:** on 2026-09-21 the b12x fault blamed `_hc_combine_kernel` (layer 0 attention, before any
MoE ran). I spent five source-level theories and ~6 engine loads chasing it — workspace undersizing,
missed gated fallback, scratch shortfall, seq-count dependence, `reorder_w1w3_to_w3w1` — all dead.
One blocking run named the real site immediately. Our 2026-08-30 comment on vllm#50189 had already
drawn the wrong conclusion from that same misleading frame.

**How to apply:** misleading-kernel signature → blocking run BEFORE reading dispatch code. Reading
dispatch code to guess a cause is the failure mode [[kernel-roster-from-logs]] already records.
Then prove it with the counterfactual ([[no-cause-without-counterfactual]]): flip only the suspect
input and show the fault appears and disappears.
