---
name: bandwidth-bound-ask-discrete-gpu
description: A GB10 null on a compute-side change is not a verdict when the GB10 is bandwidth-bound; ask a discrete-GPU tester
metadata:
  node_type: memory
  type: feedback
  modified: 2026-11-09T15:34:22.017Z
---

When a change saves compute (instructions, decode, launches) and the GB10 shows no gain because decode is
memory-bandwidth-bound (273 GB/s unified), don't drop it: request a run from someone with a discrete GPU card.
User, 2026-11-09, on the FP4 pair-decode row: "we should request a run from somebody with a GPU Card (every time we
see limited bandwidth)".

**Why:** discrete cards have far more bandwidth per FLOP, so the same kernel can be compute-bound there; a GB10 null
says nothing about them.

**How to apply:** if exactness gates pass and the GB10 is level, still push and write the PR body with the GB10
numbers marked "bandwidth-bound here". Ask a tester with a card in the PR: Maxrio9 (sm_120, ran DSpine frames on
#2592), clee (sm_80, ran #2115 cells). Name the exact cells to run (decode c=1/c=4, prefill 8k, A-B-B-A, md5).
Related: [[only-shippable-work]], [[gb10-job-dispatcher]].
