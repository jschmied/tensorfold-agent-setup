---
name: generated-scripts-sed-trap
description: Deriving a new runner script from an old one with sed replaced only the first match per line — the install applied the OLD diff while the dry-run checked the new one; write runner scripts by hand and assert on content
metadata:
  type: feedback
---

2026-09-27 01:16: night7.sh was made from night6.sh with `sed -e 's|compilation.diff|compilation2.diff|'` (no `g`). The line
`patch --dry-run < compilation.diff && patch < compilation.diff` became dry-run NEW / apply OLD, and the job logged
"installed". Caught only because I grepped the venv file for the new fix's marker afterwards.

2026-10-08: backupclean2.sh was made from backupclean.sh by replacing the `DROP="..."` line with sed; the old value
spanned three lines, so two continuation lines stayed behind outside the quotes. `bash -n` caught it before launch.

**Why:** a one-line substitution looks complete and the log line was unconditional.
**How to apply:** write each runner script by hand (they are short); after installing a change, assert on a string
only the NEW version contains (`grep -q <marker> || exit 1`) before starting a server. Run `bash -n` on every generated script before launching it. Related:
[[verify-guards-on-empty-output]], [[never-edit-a-running-job-file]].
