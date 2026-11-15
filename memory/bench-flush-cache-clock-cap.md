---
name: bench-flush-cache-clock-cap
description: Every benchmark flushes the page cache before each server start; the GB10 GPU clock is capped at 2300 MHz from boot (gpu-clock-cap.service)
metadata:
  node_type: memory
  type: feedback
  modified: 2026-11-04T07:24:25.469Z
---

- **Page cache:** every benchmark runs `sync; echo 3 > /proc/sys/vm/drop_caches` (via `SUDO_ASKPASS=~/.sudo-askpass sudo -A`) before each server start. `~/notes/qpages/tools/srv.py` `drop_caches()` does it in `start()`.
- **Clock cap:** `/etc/systemd/system/gpu-clock-cap.service` (enabled 2026-11-04) runs `nvidia-smi -lgc 0,2300` at boot; its stop runs `-rgc`. Under load the clock reads about 2281 MHz.
- **Comparing numbers:** prompt timings at the cap are about 5 % slower than at stock. Never compare a capped number with an uncapped one. Check the clock with `nvidia-smi --query-gpu=clocks.gr`.

**Why:** the user asked on 2026-11-04 ("use 1 for any benchmark, make 2 with 2300 MHz at boot"), after reading https://al-engr.com/dgx-spark-how-we-run-them.html.
- Leftover file cache changes free memory and so the size of the KV pool.
- At stock clocks the GPU clock falls about 2 % as it heats from 55 to 80 °C. The 32k time to first token tracked temperature at r = +0.85 and made A/A runs noisy ([[gb10-ab]] style runs).

**How to apply:** use it in any new harness (gb10-ab, cudafast, TF speed runs) and in every server A/B. This box is an ASUS Ascent GX10 (BIOS GX10DGX.0105.2026.0505). The al-engr display-memory EFI tweak (`NvidiaDispFrmStatus`) is for NVIDIA's own firmware and doesn't exist here.
