# GB10 facts that change kernel decisions

| Fact | Consequence |
|---|---|
| sm_121 (consumer Blackwell family), 48 SMs | a wave = 48 CTAs (×resident CTAs per SM). Every 27B prompt shape ends its last wave on 32 of 48 SMs → tail effect at small M |
| 24 MiB L2 | a weight > 24 MiB is re-streamed per tile row unless the scheduler swizzles (CUTLASS `max_swizzle_size=8`); microbenches that reuse one matrix read from L2 — use distinct-matrix pools |
| ~273 GB/s unified LPDDR5X | decode floors: bytes/token ÷ 273 GB/s. TF dense decode reaches 80–89 % of it; EXL3 experts 192–214 GB/s; Flash Next experts M=1 190 GB/s. **Practical copy ceiling 231–241 GB/s** (bwbench, 8 GiB, any CTA count or run length); a figure above 273 is L2 reuse (hostmem_bw's rand() ids gave 281) |
| CPU and GPU share one 128 GB pool | GPU allocations are invisible to cgroups; two model loads at once global-OOM the box and kill every session (2026-10-26, twice) |
| ncu `dram__throughput %` | measured against the wrong peak on GB10 and no `dram__bytes` counters — compute bytes ÷ time yourself |
| sm_120 cubins run on sm_121 | Triton 3.7.1 only emits native NVFP4/MXFP4 block-scale MMA when compiled for sm_120 (`TRITON_OVERRIDE_ARCH=sm120`, scoped per kernel) |
| Shared memory budget | keep the pipeline ≤ ~99 KiB per CTA for 2 CTAs/SM designs (TileLang config filter used this) |
| Register limits | lean records per arch (sm_120/121: prompt16 252/250 after the tail recut); the limits contract part checks them |

Driver/CUDA: driver 615.71 (2026-10-23), CUDA 13.0 at /usr/local/cuda (13.2.2 beside it). A driver bump invalidates
JIT caches (FlashInfer) — first start rebuilds with unbounded ninja fan-out → cap MAX_JOBS.

**Native FP4/FP8 → bf16 decode (2026-10-26).**
- PTX ISA 9.2 (nvcc **13.2**) adds `cvt.rn.bf16x2.e2m1x2` and `cvt.rn.bf16x2.e4m3x2` (SASS `F2FP.BF16.E2M1.UNPACK_B`). They exist only for arch- or family-specific targets (`sm_120a`/`sm_121a`); 13.0 rejects them.
- Exactness on the GB10:
  - e2m1: equal to `fp4pair` for all 256 bytes, −0 kept.
  - e4m3: equal to `fp8pair` for every finite pair. NaN bytes give NaN in hardware and ±480 in software.
- Proposed for TF in RFC #1448; notes in `~/notes/hmloop/RESULT.md`.
