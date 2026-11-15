---
name: hourly-watch-since-trap
description: running ~/notes/watch/hourly.py by hand advances its since-marker and hides the next cron window
metadata:
  type: feedback
---
`~/notes/watch/hourly.py` reads and rewrites `~/notes/watch/last.txt`. A manual test run (2026-10-27, testing the usage line) moved the marker, so the following cron run only covered 2 minutes.

**Why:** a missed hour of TF comments looks like "nothing new".

**How to apply:** when testing, back up `last.txt` and restore it afterwards. If a run's `since` is minutes old, reset it to the previous cron time and rerun.
