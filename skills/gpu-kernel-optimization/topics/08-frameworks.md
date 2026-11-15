# External frameworks and libraries on GB10

## TileLang (evaluated 2026-10-26, ~/tilelang-trial, TODO in memory `tf-todo-tilelang-mojo-eval`)
- Runs on sm_121a (aarch64 wheel), exports standalone .cubin, autotunes 84 configs/shape in 1–2 min, 1,008
  variants compile with 0 failures. Bit-identical to prompt16 with the same math.
- Naive port is 1.34–1.61× slower than prompt16 (o/qkv, M 512–8k) and 1.17–1.40× slower than the classic kernel.
  Best configs: 256×128×64 or 128×256×64, 2 stages, 256 threads, warp-specialised (WS: 2.79 → 2.04 ms, o 2k).
- Gap analysis (prompt16 has, port lacks): register FP4 decode into the mma fragment (port goes through a bf16
  shared tile), `prmt` byte-table decode (no prmt primitive — needs `T.call_extern`), fragment-order prepacked
  weights, bf16x2 scales, persistent CTAs. Only the last two-ish are true TileLang gaps.
- Fair variant, step 1 (2026-10-26): `gemm_sr` with B decoded straight into registers (per-byte shared loads,
  arithmetic decode) is bit-identical but 5–12 % SLOWER than the shared-tile variant. Without prmt decode and
  prepacked vector loads (= re-implementing prompt16) register decode does not pay. Closed for prompt16.

- gate: 1.66× (512), 1.33× (2k), 1.35× (8k); down not run. Its built-in NVFP4 path quantizes activations (banned in
  TF), so the trial used a hand-written ~90-line NVFP4 × BF16 kernel. Emits one standalone .cu that nvcc compiles;
  using it in TF would need its header templates, TMA descriptors set up from Zig, one kernel per shape/config.
- Verdict: good shape/format explorer (exact in 90 lines, real autotuner), not a kernel source for prompt16.

## Mojo / MAX (Modular) 1.2.0 / 26.7
- Runs on GB10 ("DGX Spark" is a named target; compiles without a GPU). Emits PTX → ptxas → cubin that loads with no
  Mojo runtime.
- No kernel for exact NVFP4 × BF16: MAX's NVFP4/MXFP4 paths quantize activations; its W4A16 is int4 with BF16 scales,
  groups ≥ 32. Would mean forking a ~1,500-line kernel or porting prompt16 by hand.
- Variants are compile-time parameters swept by a benchmark script (grid search, one build per point), not an
  autotuner. One config exceeded sm_121's shared memory.
- Smoke test (noisy): MAX's plain BF16 GEMM 948–1167 µs on o at M=512 vs 395 µs for prompt16. Not worth more effort.

## Triton
- 3.7.1 on sm_121: `tl.dot_scaled` falls back (MXFP4 → bf16 upcast) or crashes (NVFP4). Compile for sm_120 via
  `triton.knobs.runtime.override_arch = "sm120"` scoped around your own launches (the cache key omits arch; a global
  env var recompiles every Triton kernel in the server). Fixed upstream in 3.8.0 (#10010).
- Triton's row kernels use approximate div/exp; TF does not copy that (06).

## CUTLASS / FlashInfer
- `max_swizzle_size=8` for weights > L2 (04).
- FlashInfer tactics: only inside `autotune(True)` via `MoERunner.get_valid_tactics`; `profile_ids` dead (03).
- FlashInfer JIT after a driver bump: cap MAX_JOBS or the build OOMs the box.
- b12x on vLLM: the −1 "not routed" sentinel must be masked before indexing experts (vllm#50189).

## DeepGEMM — closed (05)

## FLA (GDN chunk kernels)
- fla-core's fused kkt+solve: keeps the gate cumsum in log2 (exp2) — the vendored pipeline uses natural log; tf32
  hard-wired in fla-core's solve vs `FLA_TRIL_PRECISION` (ieee) in the vendored one. In tests q shares the KEY heads.
- −7…−12 % per GDN forward, −1.1…−1.4 % cold TTFT, null warm. Within 1 bf16 ulp but not bit-identical →
  acceptance swings that look like decode speed.

## Humming
- Reference for TF NVFP4/W4A16 GEMMs: 128×256×64, 3-stage TMA, warp-specialised; Stream-K in decode.
