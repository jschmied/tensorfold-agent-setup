---
name: spark-dash
description: Live queue dashboard http://<spark-host>:8090/ (spark-dash.service, ~/notes/dash); keep ~/notes/dash/pending.md current
metadata:
  type: project
---
2026-11-08, user asked for a spark endpoint with live queue + ETA + pending tasks (+ finished last 24 h).
- `~/notes/dash/server.py` (stdlib), transient unit `spark-dash.service` (systemd-run as uid 1000, Restart=always;
  NOT reboot-persistent: after a reboot restart it with the same systemd-run line, see AFTER-REBOOT).
- `/` html (auto-refresh 20 s), `/json`. ETA = median of the job's/name-stem's last DONE durations, else lane default;
  timing+correct one serial lane, build two slots, `ready` DONE-deps honoured. Rough.
- v3 (same day): overview dashboard as main page (KPI tiles, queue Gantt, work cards, needs-attention, PR tabs, recent finished) + right sidebar for every drill-down (hash routes #job/<id>, #task/<i>, #ref/<n>, #list/<x>); TensorFold logo (logo-128.png from tensorfold.dev) and brand. Server = JSON API (/api/state, /log/<id>) + static index.html; GitHub PRs/issues refreshed hourly in a thread.
- **`~/notes/dash/tasks.json` is mine to keep current** (groups agents/mac/wsl/go/waiting/review/planned; task: title, key, after = [task keys or "#PR"], owners, prefixes = job-id prefixes, branch, prs, issues, note). "Dependencies" view (#deps) draws after-links with mermaid 10.9.1; keep after-links current when plans change.: update it whenever an agent starts/finishes, a go is needed,
  or something waits on others. LAN only (ufw rule 8090/tcp from <lan-subnet>, added 2026-11-08), no auth: never put secrets in it.
