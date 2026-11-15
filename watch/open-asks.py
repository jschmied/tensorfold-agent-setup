#!/usr/bin/env python3
"""Open threads involving jschmied where someone else spoke after our last comment and nobody marked it handled.

Usage: open-asks.py            list unhandled comments (full bodies with --full)
       open-asks.py done ID... mark comment ids handled (answered, no ask for us, or tracked elsewhere: say where)
State: ~/notes/watch/asks-handled.json  {comment_id: note}
"""
import datetime, json, os, subprocess, sys

ME, REPO = "jschmied", "ashhart/TensorFold"
STATE = os.path.expanduser("~/notes/watch/asks-handled.json")
Q = """query($q:String!){search(query:$q,type:ISSUE,first:100){nodes{
 ... on PullRequest{number title url comments(last:40){nodes{databaseId author{login} createdAt body}}}
 ... on Issue{number title url comments(last:40){nodes{databaseId author{login} createdAt body}}}}}}"""


def load():
    try:
        return json.load(open(STATE))
    except FileNotFoundError:
        return {}


def main():
    handled = load()
    if sys.argv[1:2] == ["done"]:
        note = os.environ.get("NOTE", "handled")
        for i in sys.argv[2:]:
            handled[i] = note
        json.dump(handled, open(STATE, "w"), indent=0)
        print(f"marked {len(sys.argv) - 2}")
        return
    full = "--full" in sys.argv
    out = subprocess.run(["gh", "api", "graphql", "-f", "query=" + Q, "-f", f"q=repo:{REPO} is:open involves:{ME}"],
                         capture_output=True, text=True, check=True).stdout
    n_open, stale = 0, 0
    now = datetime.datetime.now(datetime.timezone.utc)
    for n in json.loads(out)["data"]["search"]["nodes"]:
        if not n:
            continue
        cs = n["comments"]["nodes"]
        mine = max((c["createdAt"] for c in cs if (c["author"] or {}).get("login") == ME), default="")
        for c in cs:
            who = (c["author"] or {}).get("login", "?")
            if who == ME or c["createdAt"] <= mine or str(c["databaseId"]) in handled:
                continue
            if c["body"].lstrip().startswith("/atc"):
                continue
            n_open += 1
            age_h = (now - datetime.datetime.fromisoformat(c["createdAt"].replace("Z", "+00:00"))).total_seconds() / 3600
            stale += age_h > 2
            flag = f" STALE {age_h:.0f}h" if age_h > 2 else ""
            body = c["body"] if full else " ".join(c["body"].split())[:240]
            print(f"#{n['number']} {c['databaseId']} {who} {c['createdAt'][5:16]}{flag}: {body}\n")
    print(f"OPEN-ASKS {n_open} unhandled" + (f", {stale} older than 2 h: finish them (tf-pr skill section 4)" if stale else ""))


if __name__ == "__main__":
    main()
