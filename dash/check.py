#!/usr/bin/env python3
"""Board check: schema, dangling deps, merged PRs still on cards, planned cards whose deps all closed."""
import json, subprocess, sys
from pathlib import Path

T = Path.home() / "notes/dash/tasks.json"
ALLOWED = {"group", "key", "title", "owners", "prefixes", "note", "issues", "next", "goal", "eta", "ledger", "branch",
           "prs", "after", "now", "waits_on", "now_at"}
GROUPS = {"agents", "mac", "wsl", "go", "waiting", "review", "planned"}


def _refs():
    try:  # the dashboard already holds every PR state (refreshed every 15 min): one local call, no gh per PR
        import urllib.request
        return json.load(urllib.request.urlopen("http://127.0.0.1:8090/api/state", timeout=5)).get("refs", {})
    except Exception:
        return {}


REFS = _refs()


def pr_state(n, cache={}):
    r = REFS.get(str(n))
    if r and n not in cache:
        cache[n] = {"merged": "MERGED", "closed": "CLOSED"}.get(r.get("kind"), "OPEN")
    if n not in cache:
        r = subprocess.run(["gh", "pr", "view", str(n), "-R", "ashhart/TensorFold", "--json", "state", "-q", ".state"],
                           capture_output=True, text=True)
        cache[n] = r.stdout.strip() or "?"
    return cache[n]


def main():
    t = json.loads(T.read_text())
    tasks = t["tasks"]
    keys = {x.get("key") for x in tasks if x.get("key")}
    bad = 0
    for i, x in enumerate(tasks):
        name = x.get("key") or x.get("title", f"#{i}")[:50]
        extra = set(x) - ALLOWED
        if extra:
            print(f"SCHEMA {name}: unknown fields {sorted(extra)}"); bad += 1
        if x.get("group") not in GROUPS:
            print(f"SCHEMA {name}: group {x.get('group')!r}"); bad += 1
        if not x.get("title"):
            print(f"SCHEMA {name}: no title"); bad += 1
        for a in x.get("after") or []:
            if not a.startswith("#") and a not in keys:
                print(f"DANGLING {name} -> {a}"); bad += 1
        prs = x.get("prs") or []
        merged = [p for p in prs if pr_state(p) in ("MERGED", "CLOSED")]
        if merged and x.get("group") != "review" or (merged and len(merged) == len(prs)):
            print(f"CLOSED-PR {name}: {merged} (drop the card or the PRs)"); bad += 1
        if x.get("group") in ("planned", "waiting"):
            open_deps = [a for a in x.get("after") or []
                         if (a.startswith("#") and pr_state(a[1:]) not in ("MERGED", "CLOSED"))
                         or (not a.startswith("#") and a in keys)]
            if x.get("after") and not open_deps and not x.get("waits_on"):
                print(f"UNLOCKED {name}: all of {x['after']} done -> start it (standing go)"); bad += 1
    print("board ok" if not bad else f"{bad} finding(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
