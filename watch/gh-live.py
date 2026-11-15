#!/usr/bin/env python3
"""Live GitHub feed: polls /notifications (conditional, every 5 min) and prints one line per new non-self comment."""
import json, os, subprocess, sys, time, urllib.request, urllib.error

REPOS = {"ashhart/TensorFold"}
ME = "jschmied"
STATE = os.path.expanduser("~/.config/gh-live/seen.json")
TOKEN = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True).stdout.strip()


def get(url, since=None):
    h = {"Authorization": "Bearer " + TOKEN, "Accept": "application/vnd.github+json"}
    if since:
        h["If-Modified-Since"] = since
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=30)
        return r.status, r.headers, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, e.headers, None


def load():
    try:
        return json.load(open(STATE))
    except Exception:
        return {"seen": [], "start": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}


def save(s):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    s["seen"] = s["seen"][-2000:]
    json.dump(s, open(STATE + ".tmp", "w"))
    os.replace(STATE + ".tmp", STATE)


def thread_comments(subject_url, since):
    """Every comment on the thread since `since`: issue comments, PR review comments and review bodies."""
    out = []
    base = subject_url.replace("/pulls/", "/issues/")
    c, _, items = get(base + "/comments?per_page=100&since=" + since)
    out += items or []
    if "/pulls/" in subject_url:
        c, _, items = get(subject_url + "/comments?per_page=100&since=" + since)
        out += items or []
        c, _, items = get(subject_url + "/reviews?per_page=100")
        for r in items or []:
            if (r.get("submitted_at") or "") >= since and (r.get("body") or "").strip():
                out.append({**r, "updated_at": r["submitted_at"]})
    return sorted(out, key=lambda x: x.get("updated_at") or "")


def main():
    once = "--once" in sys.argv  # exit after the first line; later events stay unseen for the next run
    s = load()
    seen = set(s["seen"])
    lastmod = None
    while True:
        since = s.get("polled") or s["start"]
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - 120))
        code, hdr, items = get("https://api.github.com/notifications?all=true&since=" + s["start"], lastmod)
        wait = int((hdr or {}).get("X-Poll-Interval", 60) or 60)
        if code == 200 and items is not None:
            lastmod = hdr.get("Last-Modified")
            for n in items:
                if n["repository"]["full_name"] not in REPOS or (n.get("updated_at") or "") < since:
                    continue
                url = n["subject"].get("url")
                if not url:
                    continue
                num = url.rsplit("/", 1)[-1]
                for c in thread_comments(url, since):
                    key = str(c.get("id")) + ":" + str(c.get("updated_at") or "")
                    who = (c.get("user") or {}).get("login", "?")
                    if key in seen:
                        continue
                    seen.add(key)
                    s["seen"].append(key)
                    if who == ME:
                        continue
                    body = " ".join((c.get("body") or "").split())
                    tag = "TAGGED " if "@" + ME in (c.get("body") or "") else ""
                    save(s)  # before the print: a reader that exits on the first line must not see it again
                    print(f"{tag}#{num} [{n['reason']}] {who}: {body[:300]} {c.get('html_url','')}", flush=True)
                    if once:
                        return
            s["polled"] = now
            save(s)
        elif code not in (304,):
            print(f"gh-live: HTTP {code}", file=sys.stderr, flush=True)
        time.sleep(max(wait, 300))


if __name__ == "__main__":
    main()
