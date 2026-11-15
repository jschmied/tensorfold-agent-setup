# Measuring kernels and servers without fooling yourself

## Kernel microbenchmarks
- Cold L2: rotate a pool of distinct matrices (L2 is 24 MiB; a reused matrix reads from L2). Median of ~50 replays,
  3 repeats. State the method in every table.
- Random routing overstates MoE wins (FP4 experts: 0.59× in microbench vs −26 % in model). Use real routing traces
  or in-model timing.
- ncu `Duration` on a ~5 µs kernel is mostly launch overhead + cold caches. For small kernels measure in the real
  model with nsys `--cuda-graph-trace=node`.

## Profiling
- **ncu replay never on a process holding weights** — replay backs up writable device memory into the same unified
  pool and OOMs the box (2026-10-11 reboot). Use synthetic `tf-cuda-test <kernel>` cases.
- nsys node trace of a warm vLLM server: `--profiler-config {"profiler":"cuda"}`, `/start_profile` `/stop_profile`,
  `nsys profile --trace=cuda,nvtx,osrt --cuda-graph-trace=node --capture-range=cudaProfilerApi
  --capture-range-end=stop-shutdown --sample=none --cpuctxsw=none`; export sqlite, analyse with
  `tools/prof/nsysan.py` (Flash-Next repo).
- GPU busy = union of kernel intervals across streams, never the profiler summary table (its parent ranges
  double-count; percentages summed to 158 %).
- The torch profiler inflates host time; idle % from it is an upper bound.

## Which kernel actually ran
- Ask the log, not the dispatch source: `/opt/llm/runners/kernelroster.py <server-log>` (vLLM). Three wrong claims in
  one morning came from reading dispatch code. Paste the roster into every A/B result.
- FlashInfer: `profile_ids` is dead in 0.6.17; outside `autotune()` the runner uses the fallback tactic, so tactic
  sweeps outside autotune all measured the same kernel.
- vLLM traced regions freeze Python shape branches at the profiling shape; put shape decisions inside a
  `torch.library.custom_op` and verify a patch with a runtime marker after a real request.

## Server A/B
- Alternating fresh servers, 2+2 rounds (3+3 only if within noise), fixed prompts (no nonces), token hashes per arm.
- Restart drift: the first few hundred decode tokens of a fresh server run ~11 % slower (cold window).
- Speculative decoding: tok/s tracks acceptance; acceptance is chaotic at the ulp level. Compare speed only between
  bit-identical arms, or report per-round time and acceptance separately. Clip per prompt.
- For TF small decode kernels on Nemotron, the MoE side stream is the critical path: main-stream wait per step is the
  metric.

## Faults
- A fault that names an implausible kernel: rerun with `CUDA_LAUNCH_BLOCKING=1` before reading code — the named
  kernel is just the next launch after an earlier async fault.
- After any rebase where our kernel replaces an upstream one: trace every newly merged parameter into the kernel body
  (upstream fused `output_gate` into an epilogue our kernel bypassed → ungated output, all tests green).

## Is a memory-bound kernel fetching twice? (2026-10-27)
Three numbers per launch:
1. **ncu `lts__t_sectors_srcunit_tex_op_read` vs requested bytes / 32.** A ratio above ~1.05 means sectors are fetched more than once.
2. The kernel's time.
3. A **no-math stream probe**: the same copy loop with the math removed, as the achievable ceiling. Also run a weights-only version.

Example: FP8 experts read 73.6 M sectors for 49.1 M requested (1.5×) and ran at ~165 GB/s, against a 233 GB/s stream ceiling. NVFP4 experts were within 0.3 % and ran at the ceiling, so there was nothing to fix. Template: `~/notes/hmloop/fp8/DIAG.md`; synthetic launches only.

## Instructions per mma in the main loop
`~/notes/hmloop/loops.py` counts SASS instructions per HMMA in the innermost loop of a cubin. It is a quick proxy for decode/address overhead in a tensor-core GEMM. Reference points: prompt16 lean 5.88, prompt16 with native FP4 decode 4.72, Humming batch-invariant 2.1.

## TF's speed bar for exactness refactors (ashhart, #1353/#1354, 2026-10-27)
- **Not even 1 % slower.** A bit-equal refactor that is 0.9–1.3 % slower in plain decode, or about 1 % in prefill, is rejected. "Within noise" doesn't help when the sign holds every round.
- **Before posting:** A/B served cold TTFT and plain decode at 1 and 4 streams, with a fresh server per arm and round, alternating order, and enough rounds that the sign is stable.
- **Compare against the exact kernel you replace, at the family's shape:** e.g. `tf_nemo_topk` at 128 experts, top 6, 6 slices, 1–16 rows. Comparing against a different pair of launches (combine plus top-k) hides the regression.
- A runtime loop over slices that main unrolls with all loads issued first is the usual cause.

## nsys on a binary started with `env -i` (cudafast resident, 2026-10-31)
- nsys traced no kernels: the harness launches the worker with `env -i`, so the injection never reached it. Wrap the worker itself (`nsys profile ... "$REAL" "$@"` inside a wrapper script the harness execs).
- Then CUPTI lost every record until `--cuda-flush-interval=500` was added. Recipe: `~/notes/cudafast/nsys/wrap.sh`.
- **Name a phase by its kernels' shapes before attributing a gap.** I called 63 passes with ~5 ms gaps "prefill" (~7 % idle); they were the serial leg: embed grid 1, 64 ms per step, no drafter. Real prefill passes (embed grid 16–64) had 0.86 ms per 87 ms. Check the token count per pass (embed grid, GEMM M) and the leg timeline first.
