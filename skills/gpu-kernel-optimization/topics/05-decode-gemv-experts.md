# Decode (M = 1..16): GEMV, experts, small-M GEMM

## Where decode time goes
- Dense decode is memory-bound: floor = weight bytes per token ÷ 273 GB/s. TF dense reaches 80–89 %; Humming is
  1–14 % ahead only via Stream-K (TF is 0–28 % faster in batch-invariant mode). No kernel lever > ~5 % at the floor;
  remaining levers are bytes (formats — not ours to change) and forwards (acceptance, concurrency).
  Correction (cudafast 2026-10-31): bytes CAN move without changing the format. A lossless load-time re-encoding of the per-group scales and biases (dictionary-coded, ~11 % of affine-4 g64 bytes) gave +2.4 %, and folding a redundant 151 MB state read gave +2.1 %. Count metadata and state bytes before calling a kernel floor-bound (see 10).
- Flash-Next vLLM c=1 (2026-08-27): 69 % of the step was BF16 GEMV on dense weights the checkpoint left
  unquantized (9.7 GB/token → 35.5 ms floor). The checkpoint, not the kernel, set the limit.
- Flash-Next MTP-3 decode budget: blockwise-FP8 dense GEMM 32 % at ~2.5× its byte floor at M=4 (largest
  kernel-level waste), MoE 32 % at floor, BF16 GEMMs 16.5 %.
- Mid-size weight reads (3–16 MB) cost ~+10 µs each in the live decode sequence regardless of kernel (Triton =
  cuBLAS in-model); explain in-model overhead before writing more mid-size GEMM kernels.

## NVFP4 expert decode dispatch (TF #1351)
- Three kernels: classic, waves (equal waves of units), half (two warps a unit for one row).
- Measured M=1..16, spread/mixed/hot routing, cold L2: **half wins whenever 2 × active units ≤ resident warps**
  (M=1 −7 %), +19 % one point past it — the rule is exact. **Waves pays only when the plan spills past one wave**
  (M=4 spread −9 %, M=8/16 mixed −5…−7 %); on a one-wave plan it is the same work and costs +2 % (hot case).
- `pick()` returns classic while items × blocks fit one wave and no half fit applies.
- Warps per CTA 1 vs 4 (`TF_NVFP4_DECODE_WARPS`): within ±1 %.
- Contract must force ≥ 2 waves (the 4-expert fixture never ran a second wave) and register the 1-warp instances.

## FP4 × FP4 experts (TF #211, historical — lossy activations are now banned in TF)
- Warp per (plan item, 32 columns), pack4 words re-laid lane-major, 4 K steps in flight: experts −26 %.
- Traps: one reply's decode "−16 %" was drafter acceptance; layer 0 had two gate/up input scales (take the max).

## Small-M FP8 / DeepGEMM
- DeepGEMM for small-M blockwise FP8: CLOSED — CUTLASS is 8.3 % faster on GB10 and DeepGEMM's E8M0 requant moves
  weights 2.6 % (rel. Frobenius). The 32 % waste is real but needs a kernel tuned for M=4, not a backend switch.

## Graphs and host time
- cudagraph mode at c=1 (Flash-Next): null twice; `FULL_DECODE_ONLY` runs as `FULL`, eager breaks do not fire on
  decode. Closed.
- TF concurrent-round graphs: one replay saves ~4 ms/forward = 7.8 % of a round at c=2, 5.6–6.2 % at c=4.
- PLE offload gather fully hidden (gap 0) — do not spend on PLE prefetch.

## Ideas from a 3090 MoE playbook (added 2026-11-22)
- **NVFP4 code → exact FP16 by byte permutes** (`prmt`): packed nibbles become the FP16 high bytes of the exact
  E2M1 values, FMA order unchanged. Their decode 112.6 → 116.5 tok/s, all 200,058 logits equal at 795 positions
  (playbook 09 "codebook lookup", ledger QP-14). Candidate for core `cuda/experts` NVFP4 decode (Inkling, Flash Next).
- **Launch count with graphs:** 1,404 → 781 launches per token, each fusion bit-exact, router picks resolved on the
  device and the whole token in one graph: 57 → 112 tok/s (PL-15/16). Only pays while launches are not hidden.
- **Sampling on the device:** a 1,024-bin histogram finds the top-1,000 logits instead of copying 200,058 to the host:
  100 → 110 tok/s, same tokens per seed (13, HD-04). Sampled decode only.
Source: alesha-pro/inference-optimization-playbook (MIT, read 2026-11-22; RTX 3090 sm_86, many single runs; their exactness = token match or logit tolerance, not ours). Priors, not GB10 facts.
