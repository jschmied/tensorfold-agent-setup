#!/usr/bin/env python3
"""Claude Code hooks for the Spark board: start | stop | post. Never fails the tool call (always exit 0)."""
import json, re, subprocess, sys, time
from pathlib import Path

D = Path.home() / "notes/dash"
AGENTS, LOG = D / "agents.json", D / "agent-events.jsonl"
KEY = re.compile(r"\[([a-z0-9][a-z0-9-]{1,30})\]")


def strings(x):
    if isinstance(x, str):
        yield x
    elif isinstance(x, dict):
        for v in x.values():
            yield from strings(v)
    elif isinstance(x, list):
        for v in x:
            yield from strings(v)


def findings():
    r = subprocess.run([sys.executable, str(D / "check.py")], capture_output=True, text=True, timeout=25)
    return [ln for ln in r.stdout.splitlines() if ln and not ln.startswith("board ok") and "finding(s)" not in ln]


def load():
    try:
        return json.loads(AGENTS.read_text())
    except (OSError, ValueError):
        return {}


def roster(ev):
    """Running subagents by card key, from the event's background_tasks (None when the event has no list)."""
    tasks = ev.get("background_tasks")
    if not isinstance(tasks, list):
        return None
    out = {}
    for t in tasks:
        m = KEY.search(t.get("description") or "") if t.get("type") == "subagent" else None
        if m and t.get("status") == "running":
            out[m.group(1)] = t.get("id")
    return out


def sync(st, live, now):
    """Mark roster agents running and tracked running agents missing from it stopped."""
    for k, aid in live.items():
        if st.get(k, {}).get("state") != "running" or st[k].get("agent_id") != aid:
            st[k] = {"state": "running", "at": now, "agent_id": aid, "key": k}
    for k, v in st.items():
        if v.get("state") == "running" and k not in live:
            st[k] = {**v, "state": "stopped", "at": now}


def pending_jobs(key):
    """Queued or running dispatcher jobs of a card (its owners/prefixes), so a stopping agent can be held."""
    try:
        T = json.loads((D / "tasks.json").read_text())
    except (OSError, ValueError):
        return []
    t = next((c for c in T.get("tasks", []) if c.get("key") == key), None)
    if not t:
        return []
    out = []
    for d in ("q", "run"):
        for f in (Path.home() / "notes/jobs" / d).glob("*.json"):
            try:
                j = json.loads(f.read_text())
            except (OSError, ValueError):
                continue
            if j.get("owner") in t.get("owners", []) + [key] or any(j.get("id", "").startswith(x) for x in t.get("prefixes", [])):
                out.append(j.get("id"))
    return out


def agent_event(mode, ev):
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    with LOG.open("a") as f:  # raw input kept: the field names are learned from it
        f.write(json.dumps({"mode": mode, "at": now, "ev": ev}) + "\n")
    st = load()
    aid = ev.get("agent_id")
    if mode == "stop" and aid:  # only a tracked agent's own stop counts; helper agents stop all the time
        for k, v in st.items():
            if v.get("agent_id") == aid and v.get("state") == "running":
                st[k] = {**v, "state": "stopped", "at": now}
    live = roster(ev)
    if live is not None:
        live = {k: a for k, a in live.items() if a != aid or mode != "stop"}
        sync(st, live, now)
    if mode == "stop" and aid:
        key = next((k for k, v in st.items() if v.get("agent_id") == aid), None)
        jobs = pending_jobs(key) if key else []
        if jobs and not ev.get("stop_hook_active"):  # held once: an agent must not leave its queued jobs unwatched
            st[key] = {**st[key], "state": "running", "at": now}
            AGENTS.write_text(json.dumps(st, indent=1))
            print(json.dumps({"decision": "block", "reason": f"Your dispatcher jobs are still queued or running: "
                              f"{', '.join(jobs)}. Before ending your turn, start a background wait (run_in_background) "
                              "with a deadline that ends when each of them is DONE or FAIL in ~/notes/jobs/events.log, "
                              "so you are woken to finish the work. Then you may stop."}))
            return
        if jobs:
            st[key] = {**st[key], "state": "parked", "at": now, "jobs": jobs}
    AGENTS.write_text(json.dumps(st, indent=1))
    if mode == "stop":
        out = findings()
        if out:
            print(json.dumps({"systemMessage": "board: " + "; ".join(out)[:600]}))


def agent_launch(ev):
    """PostToolUse on Agent: the description carries the [key], the response the agent id."""
    d = (ev.get("tool_input") or {}).get("description") or ""
    m = KEY.search(d)
    r = ev.get("tool_response")
    rs = json.dumps(r) if not isinstance(r, str) else r
    a = re.search(r"agentId:?\W*([0-9a-f]{12,})", rs)
    if m:
        st = load()
        st[m.group(1)] = {"state": "running", "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                          "agent_id": a.group(1) if a else None, "key": m.group(1)}
        AGENTS.write_text(json.dumps(st, indent=1))


def post(ev):
    if ev.get("tool_name") == "Agent":
        agent_launch(ev)
        return
    if "tasks.json" not in json.dumps(ev.get("tool_input", {})):
        return
    out = findings()
    if out:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse",
                                                  "additionalContext": "spark-board check: " + "; ".join(out)}}))


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "post"
    try:
        ev = json.load(sys.stdin)
    except ValueError:
        ev = {}
    try:
        agent_event(mode, ev) if mode in ("start", "stop") else post(ev)
    except Exception as e:  # a hook must never break the session
        print(json.dumps({"systemMessage": f"board hook error: {e}"}))


if __name__ == "__main__":
    main()
