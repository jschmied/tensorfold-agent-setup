# Method: what to optimize and when to believe a result

## Bound the core before polishing overheads
- Count the kernel's own redundant work against the minimum (e.g. weight-tile decodes per expert vs one per tile)
  and put a time on it before choosing a lever.
- EXL3 prompts, 2026-10-01/02: five bit-exact overhead PRs (empty programs, grouping, copies, window) gave −25 %;
  grearjake's #212 took −54 % by decoding each trellis tile ONCE per 64 pairs in shared memory (cp.async + ldmatrix).
  ncu had said tensor ops were 2–3 % of instructions — the decode WAS the kernel. All five of ours closed as superseded.
- Three mistakes to avoid:
  1. Testing only the extremes (materialise in global memory vs per-16-row in registers) and missing the middle
     (on-chip shared-memory reuse).
  2. Closing an idea because its smallest implementation was slower. A failed variant closes that design point,
     not the idea; write down which point failed and test the intermediate one.
  3. Ranking levers by cost of the change instead of size of the prize.
- A floor is only useful once its binding term is tested: "experts are weight-traffic-bound" was refuted by one knob
  (prefill rows 2048→8192 gave −1 %/+5 %).

## Rank against the best external implementation
- Measure a tuned external kernel as the ceiling before writing one (FlashInfer CUTLASS MoE, Humming, CUTLASS).
- The vendor bf16 GEMM was WORSE than our FP4 path (bandwidth-bound on bf16 weights), so the real target was a
  tensor-core FP4 grouped GEMM.

- Split a gap against the reference into flat vs shape-dependent before choosing a lever (TF #2089, Metal, 11-10):
  1. occupancy: run the half-tile variant (8x32 vs 16x32); slower everywhere = occupancy is not the limit;
  2. cache traffic: N distinct weight copies (`SQ_COPIES=4` vs 1); unchanged time = compute-bound at that M;
  3. per-shape ratio ours/reference over every served (N, K): flat (1.09-1.11 on 8 of 11) = per-tile work around
     the MMAs (dequant, staging); a gap that grows only on small N or long K = tiling/split-K. Three one-knob runs,
     no kernel edit, and the lever is named before anyone writes one.

## Hypothesis and range before every experiment
- Write the expected direction and range first. An outcome outside it means debug the measurement before
  interpreting. (Example that worked: tail-wave recut predicted served TTFT within noise; it was.)

## No cause without the counterfactual
- State a cause only after flipping just that input and seeing the effect appear and disappear. In one day 10 of 13
  errors came from skipping this.

## When is a gain real
- Sign must hold in every round AND ranges must not overlap; arms drift within an arm, sometimes oppositely.
- Kernel microbench gains often do not reach the server: FLA fused kkt+solve −7…−12 % per GDN forward → −1.1…−1.4 %
  cold TTFT, null on warm agent turns. prompt16 tail recut −10 % kernel at M=512 → served null.
- Agentic speed is TTFT-bound: rank by time to first token on warm agent turns, not decode tok/s.
- Spec-decode acceptance moves ±10 pp from a 1-ulp change: tok/s differences between non-bit-identical builds are
  usually acceptance, not kernel speed (see 03).

## Engine, not weights
- Speed levers are engine-side. Never propose requantizing or changing stored weights to make a kernel faster.
- Exception that is still engine-side: when the ENGINE quantizes at load (cudafast's bf16 drafter → affine-4), the fit quality at the same width is a free acceptance lever (refit +1.2 % official). See 10.

## The benchmark's public sample is not its scored workload
- A +6.8 % local gain on the public seed scored +0.25 % on the private prompts (cudafast edge_weight). Rank workload-dependent knobs on a generic prompt set; trust only prompt-independent gains to transfer. See 10.
