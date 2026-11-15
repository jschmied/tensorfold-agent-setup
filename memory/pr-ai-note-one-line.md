---
name: pr-ai-note-one-line
description: "AI note is for vLLM only (one plain line + Signed-off/Co-authored trailers); TensorFold gets NO AI line and NO tool trailers (its CONTRIBUTING forbids them)"
metadata:
  node_type: memory
  type: feedback
  modified: 2026-09-26T22:09:27.933Z
---

User, 2026-09-27, on the GDN RecoverSSM vLLM PR draft: "keep ai note short, one line, no icons".
Use exactly one plain line such as "Developed with AI assistance (Claude Code); all changes reviewed by the author."
No 🤖 line, no session URL in upstream PR bodies.

**2026-10-03 correction (user: "ai attribution line is for vllm"):** the AI line and the Claude co-author trailers
are vLLM's policy. TensorFold's CONTRIBUTING (0.6.3+) says "No AI tool attribution lines, and no co-author trailers
for tools" — so TF PR bodies, comments and commits carry none of them (no `Co-Authored-By: Claude`, no
`Claude-Session`, no "Written with AI assistance"), and the PR template's last checklist box is ticked.

**Why:** the user wants the disclosure (vLLM policy) but not branding noise in upstream posts.
**How to apply:** vLLM PR/issue bodies and comments ([[upstream-post]] skill); commit trailers
(Signed-off-by + Co-authored-by: Claude) stay as vLLM requires. Fork-internal review PRs may keep the old footer
only if the user hasn't said otherwise — prefer the one-liner there too.
