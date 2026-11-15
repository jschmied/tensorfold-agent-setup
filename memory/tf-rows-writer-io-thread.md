---
name: tf-rows-writer-io-thread
description: "TF main (2026-10-27): kept-state disk writes run on an I/O thread; tests must drain the worker, not step the queue"
metadata:
  type: project
---
Main changed on 2026-10-27 in afa4fa38f, cbd530521, d22d70496 and 10aac5e55.

**How it works now:**
- Spill writes are staged on the engine thread and written by one I/O worker (`rows_write.queued` hands off to `rows_write_sync.queued`).
- RAM states are saved at a stop.
- Queued requests' disk states are read ahead on an I/O thread.
- A 1 GiB staging limit applies; a state past it isn't saved.

**For tests:** `while (rows.write.step(r)) {}` no longer publishes states. Use `_ = rows.write.drain(r, rows.write.nowNs() + 3 * std.time.ns_per_s);`, as main's `5897e0bca` does. This broke our #1358 `cuda_disk_test` (expected 2, found 0) until fixed.

**Why it matters:** every disk/spill PR of ours (#1358, #1359, #1413) has to describe this behaviour and rebase onto it.
