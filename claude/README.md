# Claude Code configuration

`settings.excerpt.json` is the relevant part of `~/.claude/settings.json` (model, theme and notification settings
dropped; `/home/jschmied` shortened to `~`). There is no `permissions` block: the session runs with
`--dangerously-skip-permissions` (see `docs/SERVICE.md`, security posture), and `skipDangerousModePermissionPrompt`
suppresses the confirmation prompt that would otherwise block an unattended start.

## Hooks

All three call `~/notes/dash/hook.py` (copy in `dash/hook.py`). It never fails the tool call (always exits 0) and
logs every raw hook input to `~/notes/dash/agent-events.jsonl`.

| Hook | Matcher | What `hook.py` does |
|---|---|---|
| `SubagentStart` | all | `start`: records running subagents from the event's `background_tasks` roster into `agents.json`. Agents are tied to board cards by a `[card-key]` at the start of their description. |
| `SubagentStop` | all | `stop`: marks a tracked agent stopped (helpers without a tracked id are ignored), runs `dash/check.py` and returns findings as a message. If the agent's card still has jobs in the dispatcher's `q/` or `run/`, the first stop is **blocked** ("start a background wait, then stop"); a second stop marks the card `parked` so the main session resumes it when the jobs end. |
| `PostToolUse` | `Bash\|Write\|Edit\|Agent` | `post`: for `Agent` calls, records description + agentId as running. For any Bash/Write/Edit whose input mentions `tasks.json`, runs the board check and feeds the findings back as context, so board errors get fixed in the same turn. |

## Status line

`statusline-command.sh` prints model, context %, 5 h / 7 d rate limits and cwd. As a side effect it writes
`~/.claude/usage-now.json` (current rate limits) and appends to `~/.claude/usage-history.jsonl` when a value changes
(at most every 10 min otherwise). `usage-report.py` reads that history and gives burn rates, the projection to the
7-day reset and a state (`ok` / `careful` / `throttle` / `stop`) used by the `usage-self-management` skill.
Needs `jq`.

## Plugin

`atc@atc-github` (Agent Traffic Control, `ashhart/ATC`): claims, overlap checks and the review exchange used by
TensorFold contributors. See `memory/tf-atc-*.md`.
