# Small glue kernels and shared kernels (TensorFold)

## Exact arithmetic is a project choice
- TF row kernels keep exactly rounded division/sqrt (`__fdiv_rn`, IEEE 1/sqrt) so bits match across GPU generations.
  Cost: ~0.3–0.5 µs/call vs Triton's approximations (swiglu 1.16 vs 0.86 µs), ~1 % of a long decode.
- Get speed bit-neutrally: launch shapes (take Triton's: ≤16 rows → swiglu 128, gate 64, gdn_prep 64, gated 32
  threads), parallelism, pipelining.

## Shared kernels (user rule 2026-10-25)
- "As simple and optimal as possible without keeping unnecessary restrictions": one canonical reduction order per
  shape class (head dim, dtype); a parameter only if needed for speed or correctness, never to mimic a legacy order.
- A family migrating onto a shared kernel accepts a one-time byte change, gated on its own gates + float64 bounds +
  logit distance no worse than main + chat/needle + speed within noise.
- Never change OTHER families' bytes/SASS in place: add a variant or instance; prove the rest with SASS identity.
- Upstream reviewer (ashhart, #1353/#1354) additionally requires: error no worse per projection class (worst column,
  prompt and decode separately) or keep the old order; and no prefill slowdown. Keep underflow guards (`+1e-20` in
  top-k normalisation: all-underflow → 0/0 = NaN otherwise) and test that case.

## Nemotron glue lessons (#627/#833)
- ncu duration on ~5 µs kernels lies; nsys node trace in the real model.
- The MoE side stream (router → topk → plan → experts) is the critical path; measure main-stream wait per step.
- The glue test was blind to add_moe_norm's sum-of-squares order: verify "same bits" with model digests
  (`tensorfold teacher`), and mutation-test the gate.
- Result: router/topk/add_moe_norm byte-equal, plain decode −1.8…−2.6 %.

## dense_rows (#548 step 4, 2026-10-26)
- Narrow form (2–63 rows: warp does 4 rows of one weight row, 2 warps a block) and tiled form (≥ 64 rows: lane is a
  k-slice with 8×8 partials, block stages 16 rows × 32 weight rows per 256-input step), reached via `rowsFit`;
  `rows()` unchanged so other families' launches stay identical.
- Bit-equal over 25.7e9 outputs (5 data kinds incl. NaN/Inf/denormals/2^±30); but prefill −1.2…−2.3 % and drafted
  decode 2/4 streams −3…−5 % vs step 2. Tiled form 659 µs vs old 562 µs at 8k rows (~29 % of fp32 peak).
  Open levers: reduce-scatter instead of final shuffles; two 256-input steps per barrier; per-row-count boundaries
  measured, keeping the old path where it wins.
