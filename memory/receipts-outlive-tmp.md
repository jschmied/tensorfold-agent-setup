---
name: receipts-outlive-tmp
description: Raw run files behind any posted number go to ~/notes/<topic>/, never /tmp — #1553 lost its receipt
metadata:
  type: feedback
---
Every number that goes into a PR, doc or comment must have its raw runs (requests, per-run values, hashes, server logs) under ~/notes/<topic>/ before posting.

**Why:** on 2026-10-29, ashhart asked for #1553's receipt (the chunk-size table, the nsys numbers, the token hashes). The runs had lived in /tmp/claude-1000/chunk/ and were gone, so the user chose to cut the numbers from the docs. Same failure as [[runners-live-in-opt]].

**How to apply:** when a measurement finishes, copy its run dir to ~/notes before writing the post. The post's receipt section names that path.
