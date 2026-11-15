---
name: tf-exact-arithmetic-choice
description: TF CUDA row kernels keep exactly rounded division/sqrt (same bits on every GPU) over Triton's div.full/ex2.approx speed; user decision 2026-10-13
metadata:
  type: feedback
---

2026-10-13 user: "do 1 and document the choice/gap" (option 1 = keep exact arithmetic). The 27B's small row
kernels are ~0.3-0.5 us/call slower than Triton's at the same launch shape because the sigmoid uses __fdiv_rn
(swiglu microbench 1.16 vs 0.86 us with __fdividef/__expf; __frcp_rn = same bits but 1.21 us). Launch shapes were
taken from Triton (launch.rowThreads, <= 16 rows: swiglu 128, gate 64, gdn_prep 64, gated 32) - only 3-9 %.

**Why:** bits identical across GPU generations (div.full/ex2.approx/rsqrtf are hardware approximations), matching the
IEEE 1/sqrt move in norms (#796) and qk_rows/gdn_prep (#797). Cost ~1 % of a long decode on an RTX 5090.
**How to apply:** don't swap exact ops for approximate ones to chase Triton per-call speed; tune launch shapes,
parallelism and pipelining instead (bit-neutral). Documented in #797/#796 descriptions and a one-line comment at
the sigmoid. Related: [[quality-rule-noticeable]].

**2026-10-24 project rule (ashhart on #1145):** "TensorFold is exact serial decode made faster, so we're not taking lossy activation formats, even as an opt-in." #1145 lands loading/packing for ModelOpt + compressed-tensors NVFP4/FP8/bf16 and `--precision full` (bf16 rows); NOT `--precision checkpoint` (e4m3/NVFP4 activation quant) or its kernels (ck_dense4, tf_ck_quant4, ck_lane8t, K-whole FP8 prompt). ashhart splits it; offered to take our split instead. Apply to all future TF work: no activation quantization.
