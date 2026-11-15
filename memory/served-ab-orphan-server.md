---
name: served-ab-orphan-server
description: Served A/B arms can silently hit a leftover server; check port free + own "serving" line + md5 per arm (cost #2238 a posted correction)
metadata:
  type: feedback
---
On 2026-11-05, #2238's served 27B table was posted with rounds 3 and 4 contaminated. A round-2 crash skipped the
server stop, so that server kept answering on the port. Rounds 3 and 4 never started their own servers, and both
arms measured the same software-decode binary. The table claimed −5.6 % at 2k; the clean reruns gave −1.7 % at
every length. It needed a public correction.
**Why:** a TTFT client can't tell which server answered. "Both arms slower, no gap" in two rounds was the
signal, and it was written off as noise.
**How to apply:** in every served A/B arm:
1. refuse to start while the port is busy;
2. require the arm's own server log to show its "serving" line;
3. md5 the served binary;
4. confirm the server is gone before the next arm.
Treat rounds where both arms shift together with no gap as suspect until checked.
See [[gb10-job-dispatcher]].
