---
name: spark-board
description: Keep the Spark dashboard board (~/notes/dash/tasks.json, http://<spark-host>:8090, Plan + Dependencies views) current — card schema, when to update, the check script, unlocking planned steps. Use whenever an agent starts/finishes, a PR opens/merges, a step is planned or waits on someone, and at every 2 h watch.
---

# Spark board

The board is `~/notes/dash/tasks.json`, served by `spark-dash.service` (`~/notes/dash/server.py`, LAN only, no auth:
**never put secrets in it**). The main session owns it; agents only write the dash block in their ledger
(`<!-- dash now:/next:/eta:/note: -->` in `~/notes/ledger/<ledger>/STATUS.md`), which the server overlays on the card
with a matching `ledger`. The block wins unless the card's `now_at` (ISO time) is newer than the STATUS.md mtime:
**whenever you edit a card's now/next, set `now_at` to the current time**, or a finished agent's stale block keeps
showing (11-09: F2 card still said "STOPPED" hours after the questions were posted). Nothing refreshes a finished
agent's block on its own.

## Card schema (anything else is a bug: two cards with `id`/`state` went invisible on 11-09)

```json
{"group": "agents|mac|wsl|go|waiting|review|planned", "key": "short-id", "title": "...",
 "owners": ["agent name"], "prefixes": ["job-id prefix-"], "ledger": "dir under ~/notes/ledger",
 "branch": "...", "prs": [2633], "issues": [2592], "goal": "accept|core|radix|layer",
 "after": ["other-key", "#2528"], "waits_on": "person/thing outside the board", "now": "...", "next": ["..."],
 "note": "...", "eta": "..."}
```

- `after`: task keys or `"#PR"`; drawn in the Dependencies view. Keep keys stable; when a card is removed, rewrite
  every `after` that named it to the PR number (`"sampler"` -> `"#2606"`).
- `waits_on`: a block that is not a task or PR (a reviewer's answer, weights, a user go). Keeps the check from
  calling the card unlocked.
- `prefixes` must match the dispatcher job ids exactly (`"dsp-"` does not match `dspine-lk-*`).

## Automation (hooks in ~/.claude/settings.json -> ~/notes/dash/hook.py)

- **Agent start/stop:** `~/notes/dash/agents.json` is kept by `hook.py`. **Start every agent's `description` with
  `[card-key]`** (e.g. `[f2] KV P3 F2 ...`). Sources: the Agent tool's PostToolUse (description + agentId -> running),
  and the `background_tasks` roster that Subagent events carry (running subagents with their descriptions; a tracked
  key missing from it -> stopped). SubagentStart has no description, and helper agents (agent_type "") stop all the
  time, so a stop only counts for a tracked agent_id (11-09: a helper's stop marked the running #2115 agent stopped).
  Once stopped, the server drops the card's eta and prefixes `now` with "NOT RUNNING" until you edit the card
  (`now_at`). On stop the check runs and its findings show as a message.
- **"Agents running" is derived** (server.py `tasks()`): a card in group `agents` stays there only while its agent is
  running in `agents.json` or a job matching its owners/prefixes is in `run/` or `q/`. Otherwise the server shows it
  under `review` (it has PRs) or `waiting`, without eta (`idle_from: agents`). mac-agent/wsl-agent work belongs in
  group `mac`/`wsl`, never `agents` (11-09: 3 finished cards sat under "running").
- **No orphaned jobs:** when a tracked agent stops while jobs of its card (owners/prefixes) sit in `q/` or `run/`,
  `hook.py` blocks the stop once ("start a background wait ... then you may stop"). If it stops again, the agent is
  `parked` (board: "PARKED ... main resumes it when <jobs> end") and the MAIN SESSION must arm a wait on those jobs and
  resume the agent with SendMessage. Card prefixes must match the real job ids (11-09: `cm12-` vs `cm-c1` hid them).
- **Board edits:** any Bash/Write/Edit whose input mentions `tasks.json` runs the check; findings come back as
  context ("spark-board check: ..."). Fix them in the same turn.
- Raw hook inputs are logged in `~/notes/dash/agent-events.jsonl`.

## When to update (same turn as the event)

| event | board change |
|---|---|
| agent started | card in `agents` with owners, prefixes, ledger, branch |
| agent waits on jobs / a reply | `now` says what; `waits_on` if outside the board |
| agent finished / stopped | drop `eta`, empty `owners`/`prefixes`, `now` starts "NOT RUNNING:" or "done:", set `now_at` (a leftover eta + next list reads as "running", 11-09 F2) |
| PR opened | add to `prs`, group `review` once the agent is done |
| PR merged/closed | drop it from cards; append to the `rev-merged` note; rewrite `after` links naming it |
| a step is planned | `planned` card with `after` (and `waits_on`) |
| a go is needed | group `go`, `now` = the question |

## The check (run after every edit and at each 2 h watch)

```bash
python3 ~/notes/dash/check.py     # exit 0 = "board ok"
```

Findings: `SCHEMA` (unknown field/group, no title), `DANGLING` (after -> missing key), `CLOSED-PR` (merged PR still
on a non-review card, or every PR on a card closed), `UNLOCKED` (planned/waiting card whose deps are all done and no
`waits_on`). **UNLOCKED = start it** under the standing go (memory `start-unlocked-steps-standing-go`): agent or job
below DSpine priority, sharing check first, card to `agents`, one line to the user. New ideas, posts outside existing
gos, downloads and model swaps still need the user.

Backups before bulk edits: `cp tasks.json tasks.json.bak-<date>`.
- tf-pr: PR agents use the tf-pr skill (finish = POSTED/READY/BLOCKED); a card's agent that says 'waiting' with gates done is a stall.
