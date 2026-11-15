---
name: tf-atc-exchange
description: TensorFold uses ATC's PR review exchange (tensorfold.dev): connect our PRs, upload A/B evidence, file benchmark requests tied to exact heads
metadata:
  type: reference
---
TensorFold opted in to ATC's **PR review exchange** (`.github/atc-exchange.json`, origin `https://tensorfold.dev`, retention 168 h). The user said on 2026-10-30 that ashhart's agents use it: review/test/benchmark requests, shared logs, the commit each check covered, and much less duplicated work.

- **Client:** `node $(ls -d ~/.claude/plugins/cache/atc-github/atc/*/ | tail -1)src/exchange/main.js` with `connect|inbox|request|respond|resolve|upload|download|export|id`, plus `--repo ashhart/TensorFold --origin https://tensorfold.dev`.
- **connect** posts ONE `/atc exchange <proof>` comment per PR. Sessions last 24 h and the proof renews them.
- **Install gotcha:** plugin 0.7.0 kept its version string when the exchange landed, so `claude plugin update` said "latest" while the cache had no `src/exchange`. Fix: `claude plugin uninstall atc@atc-github && claude plugin install atc@atc-github`.
- **Connected 2026-10-30:** #1619, #1620, #1653. The hourly watch checks their inboxes.
- **Evidence:** untrusted, max 1 MiB, shared with PR participants, so check it for private paths and secrets. A request or response names the exact 40-hex head. "Accepted" is not a GitHub approval.

Related: [[tf-atc-standing-go]].
