---
name: tf-python-retired
description: TensorFold is retiring its Python engine (2026-10-10): no tooling that imports it lands; tests need float64 references; captured Triton sets are a stopgap
metadata:
  type: project
---
ashhart, 2026-10-10 (#605/#629 merge notes): "we are retiring the Python engine, so tooling that imports it doesn't
land in the tree". He removed our oracle/*.py fixture generators; tests read recorded fixtures until they get a float64
reference of their own (as `train` has). Our #633 adds `tf-cuda-test quant-ref` (f64 refs + row-count bit checks).

**Why:** upstream direction; Nemotron already moved from a captured Triton set to native kernels (8fc1e872).
**How to apply:** new TF PRs ship native CUDA kernels with f64/host references, never Python oracles. The Kolibri
Zig port's captured Triton set ([[kolibri-zig-port]]) is our bit-exact oracle only; before upstreaming, its glue
kernels (norms, qkv/RoPE, sliding + tree attention, router, top-k, combine) need native versions.
