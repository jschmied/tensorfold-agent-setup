---
name: ncu-full-model-oom
description: ncu kernel replay on a full-model process OOM-killed the GB10 (2026-10-11 reboot); profile kernels on synthetic tests only
metadata:
  node_type: memory
  type: feedback
  modified: 2026-10-11T20:34:18.375Z
---

2026-10-11 ~22:09: `ncu --kernel-name tf_add_rms_rows ... tf-cuda-test kolibri-generate <30 GB Kolibri>` drove the
box into NVRM NV_ERR_NO_MEMORY + journald memory pressure; the user had to reboot ("reboot, system oom").

**Why:** ncu's kernel replay saves and restores the device memory a kernel can write; on GB10 that is the same
unified 128 GB pool the model already fills, so the backups exhaust it.

**How to apply:** never run ncu replay against a process holding model weights. Profile single kernels through the
synthetic `tf-cuda-test <kernel>` commands (tiny buffers), or use nsys (no replay) on the full model. Related:
[[gb10-oom-protection]], [[pinned-sweep-crashed-box]].

**2026-11-05 22:31: nsys too can kill the GPU.** l2pf-nsys-g4 (nsys on a Gemma 4 31B server) → Xid 120 "GSP task exception: store access page fault" in the CUPTI worker thread, then NV_ERR_RESET_REQUIRED; every later CUDA start fails CUDA_ERROR_NO_DEVICE, nvidia-smi says "GPU requires reset". Several nsys traces on full models ran fine the same day, so it is intermittent.
