# Prefill / prompt GEMMs

## prompt16 (TF #1350): NVFP4 weights × BF16 activations, f32 accumulate
Design, in the order the gains came from:
1. **Persistent CTAs** with an **mbarrier ring** and a **decoupled copy** (producer fills stages with cp.async,
   consumers run the mma chain). `prompt_lean<FP4,128,256,1,8,3>`: 128×256 tile, 3 stages.
2. **FP4 decode in registers straight into the MMA B fragment** (`e2m1_pairs`): |e2m1| via bf16 byte tables held in
   two 32-bit words, 3 `prmt` per 4 values, sign OR-ed in (−0 kept).
3. **Weights repacked at load into mma-fragment order**: one 64/128-bit load per thread is exactly its operand.
4. **Scales** broadcast with `prmt` into bf16 pairs, multiplied in bf16x2 (exact, since e2m1×e4m3 is exact in bf16).
5. A via `ldmatrix` from a swizzled shared tile (`swz<CHUNKS>`); `mma` m16n8k16 bf16, f32 accumulators.
- Fixed K order, no split-K → bit-equal to the classic kernel (the old one is the byte reference).
- vs Humming 0.1.18 (128×256×64, 3-stage TMA, warp-specialised): before the rewrite TF was 21–46 % slower
  (qkv M=8192 82 vs 106 TFLOP/s). After the rewrite (2026-10-26): 11–26 % behind Humming's default (Stream-K) and
  7–15 % behind its batch-invariant mode, which uses the SAME 128×256 tile with cp.async (block K 32, 3 stages, no TMA,
  no warp spec). The remaining gap is therefore in the mainloop (decode, scales, K step), not TMA or warp specialization.

## Tail wave (48 SMs)
- Every 27B shape's last wave holds 32 of 48 blocks; at M=512 o/down ran 80 tiles at 83 % efficiency.
- Half-width tiles cannot fix it (still ends on 32/48). A classic launch for the remainder was slower (225 vs 190 µs).
- Recut inside the kernel (trailing 3×256 columns into four 192-wide pieces, only when the slowest block finishes
  sooner, fixed-width code paths — a runtime width cost full tiles 3–5 %): kernel −10 % (o, M=512), −1…−3 % at 2k,
  0 at 8k; **served TTFT null** (1.000 at 2k, 0.994 at 8k). Parked.

## L2 at large M (CUTLASS)
- Weight > 24 MiB re-streamed per tile row: blockwise-FP8 GEMM dropped 165 → 52 TFLOPS from M=4k to 16k.
  `scheduler.max_swizzle_size = 8` restores 150–168 TF, bit-identical (raster order is noise). Gate it on
  `weight_bytes > L2 && M > 4096` (−5…−9 % when the weight fits L2). Server: −12 % TTFT at 30k.
- Test swizzle before chunking M for any CUTLASS launch on this part.

## MoE grouped GEMM
- FlashInfer SM120 grouped GEMM1 is at the DRAM floor (0.84 GB weights + 0.10 act + 0.19 out per layer at
  M=7503 → 4.13 ms floor vs 4.19 measured). Nothing to schedule.
- Strided tile order is good (adjacent CTAs share an expert's B tiles in L2); contiguous runs per CTA are −26…−29 %.
- Remaining lever: fuse SwiGLU (+ the next layer's input handling) into GEMM1's epilogue (~1.1 of 13.5 ms/layer).
- Fused-finalize GEMM2 (scatter epilogue, atomics) is −4.3 % but nondeterministic (output checksum −0.58 %).

## EXL3 / trellis weights
- Decode each tile once into shared memory (cp.async + ldmatrix) and reuse it across rows: −54 % (#212). The decode
  is the kernel; tensor ops were 2–3 % of instructions.
- Window 2048 prompt pieces: −3.7 % 8k / −6.0 % 32k.

## Prefill scheduling (server level)
- Chunk size is workload-dependent (vLLM: 16384 wins at 32k, loses at ~4k agent load). TF lane host: chunks
  interleave with decode rounds; aging (`preference_rounds = 8`) makes equal long prompts round-robin.

## MoE prompt experts: keep each 32 B sector's halves adjacent in shared memory (2026-10-27)
- **The bug in `fp8_expert_prompt_kernel`:** its cp.async wrote 16 B chunks into a permuted fragment layout (`sw[c][m][h][l]`). The two halves of each 32 B L2 sector landed in non-adjacent slots, so every sector was fetched twice.
- **The fix:** copy contiguously and index the fragment on the read side (optionally XOR-swizzled against bank conflicts). Bit-equal, −19…−28 % at T ≤ 2048. Native e4m3 decode then adds −15 % on gate at T = 8192.
- **NVFP4 experts (`prompt_tiles`)** already copy contiguously; they run at the stream ceiling up to T = 2048.
- **`tf_nvfp4_fact_swiglu` quad-load (tried 2026-10-27, local `fact-quad` `ea5686db6` in `~/git/tf-factq`, not posted):** at T = 8192 it took 9.86 ms against 7.67 for `prompt_swiglu`, at 255 registers.
  - The fix loads the A-fragment quad as one 16 B shared load with rows r and r+8 interleaved, copied through registers a k-step ahead (a 4 B cp.async ate about 1 ms of the win). It applies to full 64-row items only.
  - Instructions per HMMA 17.9 → 13.8, MOVs 644 → 119, bit-equal.
  - Only T = 8192 gains (−8.3 %). Served Flash-Next prompts run in 1536-row chunks, where the kernel is bound by weight bandwidth (a zero-copy diagnostic equals base there), so served TTFT is neutral.
  - It is worth posting only if the prompt chunk grows to 8k.
- **Native FP4 decode in prompt16 (needs nvcc 13.2, sm_121a):** regroup each 32-bit word into 4 bytes (3 ops) and `cvt` them. That gives −4…−5.4 % per kernel, bit-equal.
  - Elsewhere (`nvfp4_experts`, qmmf) a same-signature swap saves 0–4 % of instructions, because the nibble regroup costs as much as `fp4pair`.
  - A real gain there needs a load-time repack that puts each value pair in one byte.
