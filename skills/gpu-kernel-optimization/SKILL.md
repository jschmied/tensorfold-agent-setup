---
name: gpu-kernel-optimization
description: What we learned optimizing CUDA kernels on the GB10 (sm_121, 48 SMs, 24 MiB L2, 273 GB/s unified memory) for TensorFold and vLLM — bounding a kernel before tuning it, measuring without fooling yourself, prefill GEMM / decode GEMV / MoE expert / small glue kernel design, exactness proofs (bit-equality, SASS identity, kernel contract), external frameworks (TileLang, Triton, CUTLASS, FlashInfer, DeepGEMM), and the GPU-sharing safety rules. Use before starting, reviewing or measuring any kernel speed work, and to look up why a design point was already closed.
---

# GPU kernel optimization (GB10)

Read this page, then open only the topic you need. Each topic is self-contained, with the evidence and the trap
that taught it.

## The loop (every kernel task)

1. **Bound first.** Write the floor (bytes ÷ 273 GB/s, or FLOPs ÷ peak; drafted decode: the union formula in 01) next to the measured time, and name the
   binding term only after a one-knob test. Rank levers by the size of the prize, not the cost of the change. → `topics/01-method.md`
2. **Check the field.** The best external implementation (Humming, CUTLASS, FlashInfer, a competitor PR) is the
   reference, not our last commit. Also check our own closed findings (the index below). → `topics/08-frameworks.md`
3. **Hypothesis + expected range** before running. Out of range = debug the measurement first. → `topics/01-method.md`
4. **Measure honestly:** cold L2 with distinct matrices, in-model with nsys for small kernels, kernel choice from
   logs, alternating A/B arms, acceptance kept out of speed claims. → `topics/03-measurement.md`
5. **Prove exactness** (TensorFold): bit-equality sweep, SASS identity for every kernel you did not mean to change,
   contract records with a red planted control, served gates. → `topics/07-exactness.md`
6. **Share the GPU safely:** lock rules, no ncu replay on a loaded model, budgets. → `topics/09-gpu-sharing.md`

## Topics

| File | Read it when |
|---|---|
| `topics/01-method.md` | choosing what to optimize; a variant failed; deciding whether a gain is real |
| `topics/02-gb10-hardware.md` | any number on this box: SM count, L2, bandwidth, unified memory, sm_121 vs sm_120 |
| `topics/03-measurement.md` | timing a kernel or a server, profiling, reading kernel selection, debugging a fault |
| `topics/04-prefill-gemm.md` | prompt/prefill GEMMs: prompt16's design, tiles, waves, L2 swizzle, MoE grouped GEMM |
| `topics/05-decode-gemv-experts.md` | decode (M = 1..16): GEMV, NVFP4 experts, wave/half-unit dispatch, small-M FP8 |
| `topics/06-small-glue-kernels.md` | norms, routers, act/rows kernels, dense_rows, shared kernels across families |
| `topics/07-exactness.md` | TensorFold gates, kernel contract, SASS identity, float64 receipts, nondeterminism |
| `topics/08-frameworks.md` | TileLang, Triton, CUTLASS, FlashInfer, DeepGEMM, FLA, Mojo: what works here, what is closed |
| `topics/09-gpu-sharing.md` | before running anything on the GPU while agents share it |
| `topics/10-spec-decode-engine.md` | speculative-decode engines (DFlash tree + drafter): verify attention kernel, draft length by context, round budget, offline acceptance sim, which levers carry to private prompts, cudafast closed items |
| `topics/11-metal-apple.md` | Metal/Mac work: M3 vs M5 (no tensor units below M5), MLX GEMM gap and how it was split, 36 GB wiring limit, quiet-Mac timing |

## Closed — do not re-run without new evidence

- cudagraph mode at c=1 on Flash-Next (null twice; mechanism known) → 03/05
- DeepGEMM for small-M blockwise FP8 (8 % slower, lossy E8M0 requant) → 08
- Approximate math (`__fdividef`, `ex2.approx`) for speed in TF row kernels → 06
- Lossy activation formats in TF (project rule, ashhart #1145) → 07
- TileLang for prompt16 (1.33–1.66× slower; fair variant optional) and Mojo/MAX (no exact NVFP4 × BF16 kernel,
  BF16 GEMM > 2× slower) → 08
- prompt16 tail-wave recut: kernel −2…−10 % at M=512, served TTFT null → 04
- PLE prefetch under speculation (gap already 0) → 05
- cudafast 27B: tree knobs (edge weight, scale, shortlist, cap, 23/31 nodes), host/graph idle, prefill gaps, dequant-once, lm_head pruning, GDN wide, bw patterns → 10

## Rule: exclude thermal throttling in every timing A/B (user, 2026-10-28)
#1525's GB10 A/B mixed a ~1.3 % SM-clock gap with the kernel effect. For every A/B:
- pause between arms and rounds until temperature and clock are back at baseline;
- log SM clock, temperature and throttle reasons at 1 Hz;
- drop any round with active thermal or power throttling, or with an SM-clock gap >1 % between arms;
- report the clock and throttle counts per arm.
