---
name: verify-guards-on-empty-output
description: a readability/liveness check that passes on EMPTY output is no check; prove the guard sees data, not that a command exits 0
metadata:
  type: feedback
---

`dmesg -T | tail -1 >/dev/null && echo readable` exits 0 when dmesg prints **nothing**, so it
reported "readable" for a stream restricted to root. The Xid arm of a watchdog I had just told the
user was watching for GPU faults was dead for its whole 30-minute run, comparing 0 to 0.

**Why:** silence and success are indistinguishable to an exit-code test. The Monitor guidance says it
outright — if the thing being watched failed right now, would the filter emit anything?

**How to apply:** verify a guard by asserting on **content**, not exit status — `[ "$(cmd | wc -l)"
-gt 0 ]`, or check the counter it will use is non-zero at arm time. Prove the watcher can see the
thing before claiming it is watching. Same family as [[no-cause-without-counterfactual]]: run the
case that should trip it. Nothing was missed that time only because the failure was a Python
exception, not an Xid.

- 2026-10-02: a benchmark checksum that XORs a periodic sequence (8 tiles x 512 repeats) is always 0; rotate-by-5 also cycles back to 0 after 64 steps. Use a multiply-add hash and assert the check is nonzero and equal across variants.
