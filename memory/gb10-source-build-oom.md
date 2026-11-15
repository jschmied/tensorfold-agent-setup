---
name: gb10-source-build-oom
description: Building CUDA/vLLM from source on GB10 hung the box via global OOM; must stop the fleet + cap BUILD_JOBS
metadata: 
  node_type: memory
  type: project
---

**2026-07-04: from-source vLLM build for DeepSeek-V4 ([[deepseek-v4-flash-180b-baremetal]]) hung the whole box.** Build froze 11:01:20 at the qutlass CUDA-kernel compile; kernel `Call trace` + sustained `global_oom` (constraint=CONSTRAINT_NONE) from 11:01–11:40 OOM-killed journald/pipewire and even made dockerd invoke the oom-killer; box wedged, unreachable ~2.5h, needed a manual power cycle (came back 14:16).

**Cause:** GB10 shares ONE 128 GB pool across CPU **and** GPU. Three things collided: (1) `vllm.service` NVFP4 35B resident (~30 GB, `MemoryCurrent`≈32.7 GB — it's the enabled boot default), (2) the build's default `BUILD_JOBS=16` CUDA compile (nvcc/cicc is multi-GB *per job*), (3) no cgroup cap on the build → global OOM.

**Rule for any heavy source build / compile on this box:**
1. `llm-switch stop` FIRST — frees the fleet (took available RAM 43 GiB → 116 GiB). Verify `free -h` shows ~110 GiB before starting.
2. Cap parallelism — `export BUILD_JOBS=4` (baked into `baremetal/config.env`). Never the default 16.

Same unified-memory-contention family as [[gb10-quant-speed-q8-vs-q5]] (isolate benchmarks) — CPU and GPU are not separate memory budgets here. Also note [[long-jobs-need-detach]]: tmux does NOT survive a reboot, so a multi-hour build interrupted by a hang/reboot must be relaunched (BuildKit cache resumes it, ~13 GB cached).
