---
name: tf-precision-checkpoint-rejected
description: "TF upstream rejected --precision checkpoint (activation-quantized mode); never propose activation quantizers as an opt-in"
metadata:
  type: project
---
The user said on 2026-10-27: "--precision checkpoint was rejected".

**Why:** TF upstream (ashhart) didn't take a mode that runs a checkpoint's activation quantizers, such as FP4/FP8 inputs.

**How to apply:**
- NVFP4/FP8 checkpoints on CUDA run weight-only (dequantized weights, bf16 activations).
- Don't propose `--precision checkpoint` or any activation-quantizer mode in plans, PRs or issues.
- This applies to the LFM3 plan ([[tf-todo-lfm3-cuda]]) and to any new NVFP4/FP8 family.
