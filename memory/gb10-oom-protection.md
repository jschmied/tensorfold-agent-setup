---
name: gb10-oom-protection
description: "GB10: cgroup memory limits CANNOT cap vLLM (GPU allocs are invisible to cgroups). SSH survives OOM via MemoryMin on ssh.service AND user.slice; swappiness 10."
metadata: 
  node_type: memory
  type: project
  modified: 2026-08-15T16:19:52.871Z
---

Set up 2026-08-15 after a vLLM config change froze the box and forced a hard powercycle
(see [[qwen38-27b-nvfp4-prod]]).

## ⚠️ Cgroup memory limits DO NOT work for vLLM on GB10 — measured

At steady state, one vLLM process:

| source | value |
|---|---|
| cgroup `memory.current` | **13.96 GiB** (anon 5.73 + file 8.07) |
| sum of process `VmRSS` | ~7.2 GiB |
| `nvidia-smi` used_gpu_memory | **59,251 MiB = 57.9 GiB** ← the real consumer |

GB10 is unified memory, so "GPU" memory IS system RAM — but it is allocated through the
NVIDIA driver and charged to **neither** process RSS **nor** the cgroup. Consequences:

- **`MemoryMax=` / `MemoryHigh=` on the vLLM unit is decorative.** It would bind on the ~14 GiB
  of host-side memory while the ~58 GiB that actually fills the box sails past unaccounted.
- **`systemd-oomd` cannot rescue you from vLLM either** — it acts on cgroup pressure, and
  vLLM's cgroup looks small and calm. (Installed + configured anyway; it still catches
  host-side runaway.)
- **The ONLY effective limits are vLLM's own** `--gpu-memory-utilization` and
  `--kv-cache-memory`. Treat those as the safety system. At util 0.5 we already sit at
  57.9 GiB of 121 GiB — which is why util 0.9 + a 75 GiB KV pin killed the machine.

## What DOES work: protect the login path from reclaim

When the driver eats RAM invisibly, the kernel reclaims from cgroups that *do* have accounted
memory — i.e. sshd and your shell. `memory.min` is hard protection in cgroup v2 and stops
exactly that eviction.

| cgroup | file | setting |
|---|---|---|
| `ssh.service` | `/etc/systemd/system/ssh.service.d/oom-protect.conf` | `MemoryMin=192M`, `MemoryLow=256M`, `OOMScoreAdjust=-900` |
| `user.slice` | `/etc/systemd/system/user.slice.d/oom-protect.conf` | `MemoryMin=4G`, `MemoryLow=6G` |
| `user-.slice` (template, per UID) | `/etc/systemd/system/user-.slice.d/oom-protect.conf` | `MemoryMin=2G`, `MemoryLow=3G` |

**Protecting `ssh.service` alone is a TRAP.** An SSH login is moved by logind into
`user.slice/user-<uid>.slice/session-N.scope` — a different cgroup entirely. Protect only sshd
and you connect fine, then watch the shell hang. **`user.slice` is the one that matters.**
Also size the guarantee ABOVE observed usage: user.slice idles ~1.5 GiB, so the original 1 GiB
min left the difference reclaimable and was useless.

## Fail fast instead of freezing

`vm.swappiness` 60 → **10** (`/etc/sysctl.d/99-llm-oom.conf`). With 121 GiB RAM and a 16 GiB
swapfile, the default made the kernel swap anonymous memory under pressure — turning an
over-allocation into a multi-minute freeze (no kernel `oom-kill` line ever appeared) instead of
a clean, survivable process kill.

## systemd-oomd

Installed 2026-08-15 (`apt install systemd-oomd`), active+enabled. Ubuntu ships NO `ManagedOOM*`
directives by default, so it is inert until told otherwise. Configured:
`ssh.service` + `user.slice` → `ManagedOOMPreference=avoid`;
`vllm-qwen38.service` → `ManagedOOMMemoryPressure=kill`, limit 60%, `MemoryAccounting=yes`.
PSI is available (`/proc/pressure/memory`). Caveat above: it can't see vLLM's real footprint.

## Rule

Change ONE memory-affecting variable at a time (util / kv-cache-memory / max-num-seqs /
cudagraph capture sizes) and verify the box between each. All four at once is what killed it.

**Sequencing two large models is the real OOM trigger (2026-08-18).** `systemctl stop`
returns long before vLLM has released its memory. A readiness check that only waits for
**port 8080 to close** therefore starts the next server while the previous one still holds
55 GB — two BF16 models at once took the box to 121/121 GB, load 128, `NVRM: Out of memory`
in the kernel log, and `systemctl` itself stopped answering.

Gate the next start on **memory, not on the port**:

```bash
alive=$(pgrep -cf "bin/vll[m]" || true)
avail=$(awk '/MemAvailable/{print int($2/1048576)}' /proc/meminfo)
[ "$alive" = 0 ] && [ "$avail" -ge 90 ] || wait
```

**Recovering from it:** kill the ORCHESTRATOR first, then the servers — otherwise the
script keeps spawning replacements and memory never comes back (the PIDs kept changing
between my kill attempts). `sudo` is unusable at that load (PAM times out); processes
started via `systemd-run --uid=1000` are yours, so plain `kill -9` works. Use bracketed
patterns (`bin/vll[m]`) so `pgrep`/`pkill` cannot match their own command line — that
self-match cost three separate incidents in one session.

**Two more ways this bit back (2026-08-18, second OOM the same day):**

**A memory gate before the start does not cover the load itself.** My gate checks that ≥90 GB
is free before launching — it was. The OOM came from `--gpu-memory-utilization 0.50` for the
55.6 GB BF16 checkpoint: a 60.5 GB budget leaves vLLM no room for load-time buffers. Earlier
BF16 runs at **util 0.62** loaded fine. Lower util is not "safer"; for a model that nearly
fills its budget it is the opposite. Size the budget to weights + headroom, not downward out
of caution.

**The inner vLLM units run as ROOT.** The orchestrator is `systemd-run --uid=1000`, but the
`systemd-run --unit=<name>` it issues for vLLM has no `--uid`, so plain `kill -9` as your own
user silently does nothing — three attempts in a row looked like the process was stuck in
D-state when it was simply not mine to kill. `systemctl stop <unit>` freed 118 GB instantly.
Check the owner before concluding a process is unkillable.
