---
name: ask-before-download
description: "User preference: ASK before starting any large model download; don't auto-start. Use aria2 with a 6 MB/s cap."
metadata: 
  node_type: memory
  type: feedback
---

**Always ask for explicit go-ahead before starting a large (multi-GB) model download.** Do NOT auto-start
one just because it seems like the obvious next step — even when the box is free and the direction is clear.

**Why:** the user manages their own bandwidth/disk and wants the decision. On 2026-07-15 I kicked off a 63 GB
AWQ pull without asking; they corrected me ("ask before download").

**How to apply:** propose the download (repo, size, ETA), wait for confirmation, THEN start it — **aria2c,
~6 MB/s cap**, detached ([[hf-download-aria2c]], [[long-jobs-need-detach]]). Verifying a repo's config/size via
the HF API first (read-only) is fine and encouraged; pulling the weights is what needs consent.
