# Exactness: proving a faster kernel changes nothing it should not

## TensorFold gates (what "exact" means)
- drafted == plain, concurrent == solo, chunked == whole, resumed == fresh, paged == contiguous; within a model the
  compared paths agree; error inside the float64 bound. Byte-equal-to-main is a cheap no-bug proof, not a
  correctness requirement (unless a reviewer asks).
- No lossy activation formats, not even opt-in (ashhart #1145).

## Bit-equality sweep (kernel level)
- Compare the new kernel against the reference kernel over every row count in range plus odd shapes (K not a
  multiple of the block, strided inputs) and five data kinds: normal, overflow to NaN/Inf, denormals, sprinkled
  NaN/±Inf/signalling NaN, magnitudes 2^±30. Report the count compared and the count differing.
- Include sweeps around grid multiples when the change depends on the wave count (grids 20/47/48/132).
- Check fp32 and bf16 outputs separately.

## SASS identity (for everything you did not mean to touch)
- `cuobjdump -sass` every touched fatbin from main and from the branch, per arch (sm_80/86/89/120/121), and diff per
  function: all pre-existing functions byte-identical, list the added ones. This replaces a model-level token check
  for families whose checkpoint is not on the box (Ling port: 225 of 225 GLM functions identical).

## Kernel contract (TF)
- Gates 1–5 per registered kernel; new launches need contract records; a planted control (e.g. reversed shuffle tree,
  pieces shifted 64 columns, row tables not shifted) must go red, or the gate proves nothing.
- Register a replacement form as a replacement of the reference so gate 3 demands bit-equality.
- The full contract is mostly CPU (float64 references), 40–60 min: split into parts of ≤ 15 min
  (local, uncommitted `TF_CONTRACT_PART` filter) or run once at the end. A part can hang CPU-bound (lane_gemv,
  qwen_learning) — kill by PID, note it.

## Float64 receipts
- rel-L2 vs a float64 forward on the same routing, argmax misses over a fixed passage set (960 rows), per projection
  class worst column, prompt and decode separately. Report the difference with its uncertainty
  (e.g. −0.00098 ± 0.00100, p = 0.76) — not a win unless it clears the spread.
- A lower NLL can be softening; acceptance is not quality.

## Nondeterminism
- Flash-Next on vLLM: the NVFP4 MoE expert kernels were the only nondeterministic part (emulation backend is
  bit-deterministic); atomics in fused-finalize epilogues shift checksums. Find it with per-submodule hashes over
  identical requests, first differing module wins.
- TF keeps one reduction order per shape so batching and paging cannot change bits.

## Refactors: prove "SASS unchanged" per function (2026-10-26, TF #1440)
- **Tool:** `<scratchpad>/prims/sassid.py`. It builds base vs head for every image that includes a touched file, for sm_80/86/89/120/121, and diffs `cuobjdump -sass` function by function. Prove it can see a change with planted controls: an altered `fp4pair` constant changed 52 functions, and a reordered `warp_sum` changed 25/35/10.
- **Moving a helper into a shared header can still change SASS.** `h3_norm` compiled differently through the shared serial `block_sum`, so h3 kept its own copy. Check every function; don't reason about it.
- **Some generators parse kernel source text:** `qwen4_ple_cuda_host.zig` (embeds `glue_math.cuh`), `hybrid_ple_source.zig`, `qwen4_cuda_attention_host.zig` (parses `flashnext_attn.cu`), `gdn_control_source.zig`. Moving or renaming text there breaks the build, not the kernels.
- **Shared device headers live in `zig/kernels/cuda/common/`** (namespace `tf_common`; `qmm_frag` keeps its name), mirroring `hip/common/`.
- **Reviewers want the SASS comparison as evidence they can rerun** (ashhart on #1440, 2026-10-27). Counts in a comment aren't enough. Commit the tool under `tools/` (Python, no .sh) or a digest receipt, and rerun it on a merge with current main, not an 80-commit-old base.
- **Text fixtures pin header paths:** `zig/tests/fixtures/gradient-serving.tsv` names `.cuh` files, so a move breaks `zig build test-gradient-serving`. Grep the whole tree for the old path, fixtures included.

## New CUDA kernel image or family: checklist (learned on #1492/LFM3, 2026-10-27)
- **`kernel_symbols` test:** every kernel name looked up from Zig (`.function("...")`) must appear as a whole word somewhere in CUDA source. Names built by macro token-pasting (`paged##_64`) fail it. Name them literally in a source comment, or define them literally.
- **`zig/tests/cuda/contract_limits.zig`:** the limits check reads only the images in its hard-coded name list. A new fatbin (`lfm2_moe`, `lfm3`) must be added there, or the full contract fails, even though the per-kernel gates pass.
- Records for nvcc 13.0 and 13.2 (13.2 overrides where registers differ). A later 13.3 record on main for a kernel you delete or rename breaks `registry_sets_test` (`UnregisteredOverride`).
- **A contract kind must make the property observable.** One bf16 slot at weight 1 makes a combine equal to its input, so the slot order and rounding are invisible. Use the family's real slot count and dtypes (Nemotron: 8 slots, fp32 and bf16), and plant a control that breaks exactly that property (ashhart on #1353).
- **Kernels shared across families go in a neutral header named for the shared idea**, with neutral exported names (`liquid_conv.cuh`, `tf_liquid_conv_3`; `paged_attn_segs.cuh`, `tf_paged_attn_*_64`), templated on what differs (taps, head dim). They move to `common/` once that exists on the base.

## Two-turn equality (added 2026-11-22)
A drafter change matched every token on turn 1 and diverged on turn 2: the accepted-token boundary moved by one
position (playbook 13 HD-02, 15). Served equality for drafting changes compares at least two turns, resumed.
Source: alesha-pro/inference-optimization-playbook (MIT, read 2026-11-22; RTX 3090 sm_86, many single runs; their exactness = token match or logit tolerance, not ours). Priors, not GB10 facts.
