---
name: commit-after-tests-green
description: "Commit only after tests/verification pass green — don't commit on unverified changes"
metadata: 
  node_type: memory
  type: feedback
---

Commit changes (docs included) **only after the relevant tests/verification pass green**, not before.

**Why:** user gates commits on a green verification, even for docs that describe a deployment — the deployment must be proven working first.

**How to apply:** when work is staged but a verification step is pending, hold the commit until that step passes, then commit. Worked example: the vLLM NVFP4 switch docs were held until the CUDA sanity check + `llm-switch vllm` smoke test passed green, then committed (ff84d79). See [[nvfp4-vllm-version-reference]].
