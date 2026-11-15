# Metal / Apple silicon (TensorFold qwen27 on Macs)

Measured by mac-agent; GB10 rules (CUDA, nsys, SASS) do not carry over. Receipts: Mac
`~/notes/ledger/q27-wide-prompt/BOUND-1110.md`, `~/notes/ledger/dspine-metal/`.

## Hardware classes
- M1-M4 have no matrix ("tensor") units; M5 does. A cell measured on an M3 Pro says nothing about an M5 Ultra's
  compute-side cost: ask ashhart's Ultras for those cells (#2634: 2-stream DSpine passes cost ~2x one stream on
  the M3 Pro, so drafting both streams lost 4-9 % at c=2; the Ultras decide the default).
- 36 GB Macs: Metal lets the GPU wire ~28 GiB (`iogpu.wired_limit_mb`). TF keeps a stock 8 GiB margin and refuses
  by name rather than adding a setting (ashhart, #2634).

## Prompt GEMM vs MLX (M3 Pro, M=128, MLX 0.32.3, #2089 BOUND-1110)
- TF `tf_sq_mmh_8_4_2` (16x32) 3.38-3.62 TFLOPS, MLX 4-bit flat 3.95-3.97: TF/MLX 1.09-1.11 on 8 of 11 shapes,
  gate_up 1.13 and down 1.12 (largest N, longest K: ~3 % tiling on top).
- Not occupancy: 8x32 (`8_4_1`) is 6.5-12.5 % slower than 16x32 on every shape.
- Not cache: 4 weight copies vs 1 = 0.997-1.001x; the kernels are compute-bound at M=128.
- Not split-K: MLX's smallest lead is at N=1024/2048, where MLX itself drops to 3.75.
- So the ~10 % is per-tile work around the MMAs (dequant + staging). mmh = mma within 1 % at 16x32.
  Next lever: the per-tile dequant/staging path, not tile shape. All four kernels bit-equal at every shape.

## Measuring on a Mac
- GPU timing needs a quiet Mac: a kernel-contract run sharing it flattened 2-3 stream cells to ~8 tok/s on both
  arms (#2464 r4). Token hashes stay valid; tok/s from such a run is not a speed receipt.
- Stale Metal toolchain cache can fail ~56 build steps: `xcrun --kill-cache`, rerun (#2215).
- Metal kernel contract: `zig build kernel-contract -Dcpu=apple_m1`; post its SUMMARY line in the PR.
