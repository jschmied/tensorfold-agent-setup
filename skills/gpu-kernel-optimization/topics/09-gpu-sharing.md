# Sharing one GB10 GPU between agents

Protocol file: `/tmp/claude-1000/gpu-rules.md` (recreate it from here if /tmp was wiped).

- **Timing** (any number that is a result): register `/tmp/claude-1000/gpu.xwant.d/$$`, then
  `flock -x /tmp/claude-1000/gpu.lock <cmd>`, remove the marker. One arm per acquire.
- **Any run that loads model weights takes the exclusive lock too**, even correctness runs. Two shared-lock loads
  raced past the non-atomic free-memory check and global-OOMed the box twice on 2026-10-26 (killing the Claude
  session and every agent, plus cloudflared/dashboards/rasdaemon). Inside the acquire still check
  `free -g` available ≥ model + 20 GB.
- **Shared** (`flock -s`) only for checkpoint-free runs (contract, synthetic sweeps, sanitizer on synthetic data):
  wait while gpu.xwant.d is non-empty; each acquire ≤ 15 min.
- CPU-only work (float64 references, case generation) runs outside the lock. Never hold `tfbuild.lock` and
  `gpu.lock` together (deadlocks, starved builds). Never delete other agents' xwant markers.
- No ncu replay on a loaded model; pinned-memory sweeps one arena per process with an aborting pre-check;
  source builds capped (`MAX_JOBS`, BUILD_JOBS) — heavy compiles hung the box.
- Waits: on a PID, a lock or a file, always with a deadline. Never `pkill -f`/`pgrep -f` (matches its own shell).
  Kill by PID. Long jobs detached (tmux); they still die if the Claude service cgroup is OOM-killed.
- Budget: speed A/Bs only on final branches, 2+2 alternating (3+3 only within noise), only touched families;
  exactness gates stay complete. At most 4 agents at once; reviewer-requested fixes first.
