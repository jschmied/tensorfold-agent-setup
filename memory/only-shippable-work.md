---
name: only-shippable-work
description: Only start work we can verify end to end (Spark, mac-agent, wsl-agent) or that a named tester agreed to run first; no scaffolding for families we can't run
metadata:
  type: feedback
---
2026-11-08, user after the DS4.1 drafter adapter (no checkpoint here, needs CUDA TP=2 + Metal, nothing served through it):
"why do we work on families we cant ship? either we ship this draft with an asking or we dont do such work in future".
**Why:** unverifiable work can't land; it burns agent time and reviewer attention.
**How to apply:** before briefing an agent, check: checkpoint on this box or PBS-restorable within the disk floor, the
backend runs on Spark/Mac (mac-agent)/Iris Xe (wsl-agent), no TP>1 unless a named tester agreed up front (e.g.
ThinkOffApp for two GB10s on #2005). Otherwise don't start it, or get the tester's yes first. No adapters/scaffolding
that no served path uses. Dropped on this rule: GLM DFlash move. DS4.1 core drafter: user chose to ask a tester instead (#2460 comment 6722343897: ashhart depth-hook question, jayleaton CUDA, gilby/EugeneClaw Metal); build the served part only after a yes, and only AFTER the smaller families are on shared code (user 11-08: "prolong this until smaller families are on shared code").
