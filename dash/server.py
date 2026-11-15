#!/usr/bin/env python3
"""Spark dashboard on :8090 (LAN): job queue with ETA, tasks with PR links, our GitHub PRs (15 min), drill-down logs."""
import glob, html, json, os, re, statistics, subprocess, threading, time, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

J = os.path.expanduser("~/notes/jobs")
D = os.path.expanduser("~/notes/dash")
REPO, ME = "ashhart/TensorFold", "jschmied"
GH = f"https://github.com/{REPO}"
EV = re.compile(r"^(\d\d:\d\d:\d\d) (START|DONE|FAIL|QUIET|TIMEOUT|STALL|BADJOB|ORPHAN) (\S+)(.*)$")
DEP = re.compile(r"\(?(?:DONE\|FAIL|FAIL\|DONE|DONE)\)? ([\w.\-]+) rc")
DEFAULT = {"build": 10, "correct": 12, "timing": 15, "x86": 15}
END = ("DONE", "FAIL", "QUIET", "TIMEOUT", "ORPHAN", "BADJOB")
gh = {"at": None, "prs": [], "refs": {}, "err": ""}
e = lambda s: html.escape(str(s), quote=True)


# ---------- GitHub, refreshed hourly in a thread ----------
def gh_get(url, tok):
    r = urllib.request.Request(url, headers={"Authorization": "Bearer " + tok, "Accept": "application/vnd.github+json"})
    return json.load(urllib.request.urlopen(r, timeout=30))


def gh_refresh():
    tok = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True).stdout.strip()
    prs, page = [], 1
    while page <= 5:
        q = urllib.parse.quote(f"repo:{REPO} author:{ME} type:pr")
        r = gh_get(f"https://api.github.com/search/issues?q={q}&sort=updated&order=desc&per_page=100&page={page}", tok)
        prs += r.get("items", [])
        if len(r.get("items", [])) < 100:
            break
        page += 1
    refs = {p["number"]: p for p in prs}
    want = set()
    for t in tasks().get("tasks", []):
        want |= set(t.get("prs", [])) | set(t.get("issues", []))
        want |= {int(a[1:]) for a in t.get("after") or [] if str(a).startswith("#") and a[1:].isdigit()}
    for n in sorted(want - set(refs)):
        try:
            refs[n] = gh_get(f"https://api.github.com/repos/{REPO}/issues/{n}", tok)
        except Exception:
            pass
    gh.update(at=datetime.now(), prs=prs, refs=refs, err="")


usage = {}


def usage_loop():  # lazy: the usage report every 15 min
    while True:
        try:
            u = json.loads(subprocess.run(["python3", os.path.expanduser("~/.claude/usage-report.py"), "--json"],
                                          capture_output=True, text=True, timeout=120).stdout)
            usage.clear(); usage.update({k: u.get(k) for k in ("state", "d7", "h5", "d7_reset_in", "projected_d7_at_reset",
                                                             "allowed_pct_per_h")}, rate6=(u.get("rate_pct_per_h") or {}).get("6h"), at=time.time())
        except Exception:
            pass
        time.sleep(900)


def gh_loop():
    while True:
        try:
            gh_refresh()
        except Exception as x:
            gh["err"] = str(x)[:200]
        time.sleep(900)


def kind_of(it):
    if "pull_request" in it:
        if it["pull_request"].get("merged_at"):
            return "merged"
        return "draft" if it.get("draft") else it["state"]
    return "issue-" + it["state"]


def ref(n, pr=True):
    it = gh["refs"].get(n)
    k = kind_of(it) if it else ("pr" if pr else "issue")
    tip = e(it["title"]) if it else ""
    return f"<a class='ref {k}' href='{GH}/{'pull' if pr else 'issues'}/{n}' title='{tip}' target=_blank>#{n}</a>"


def link_refs(text):
    return re.sub(r"#(\d{3,5})", lambda m: f"<a class=ref href='{GH}/issues/{m.group(1)}' target=_blank>#{m.group(1)}</a>", e(text))


# ---------- jobs ----------
def stem(i):
    return re.sub(r"(-?\d+)$", "", i)


def events():
    try:
        lines = open(os.path.join(J, "events.log"), errors="replace").read().splitlines()
    except OSError:
        return []
    return [m.groups() for m in map(EV.match, lines[-4000:]) if m]


L = os.path.expanduser("~/notes/ledger")
DASH = re.compile(r"<!-- dash\n(.*?)-->", re.S)


def live_status(t):
    """An agent's own now/next/eta from the `<!-- dash ... -->` block in its ledger STATUS.md (overrides tasks.json)."""
    p = os.path.join(L, t["ledger"], "STATUS.md")
    try:
        m = DASH.search(open(p, errors="replace").read())
        at = datetime.fromtimestamp(os.path.getmtime(p))
    except OSError:
        return
    if not m:
        return
    if t.get("now_at") and at.isoformat() < t["now_at"]:  # main session edited the card after the agent's block
        return
    kv = dict(ln.split(":", 1) for ln in m.group(1).splitlines() if ":" in ln)
    kv = {k.strip(): v.strip() for k, v in kv.items() if v.strip()}
    if "now" in kv:
        t["now"] = kv["now"]
    if "next" in kv:
        t["next"] = [x.strip() for x in kv["next"].split(";") if x.strip()]
    if "eta" in kv:
        t["eta"] = kv["eta"]
    if "note" in kv:
        t["note"] = kv["note"]
    t["live_at"] = at.isoformat()


def tasks():
    try:
        T = json.load(open(os.path.join(D, "tasks.json")))
    except Exception:
        return {"groups": [], "tasks": []}
    try:  # written by the SubagentStart/SubagentStop hooks (hook.py); agents name their card as "[key]" in the description
        A = json.load(open(os.path.join(D, "agents.json")))
    except Exception:
        A = {}
    for t in T.get("tasks", []):
        if t.get("ledger"):
            live_status(t)
        a = A.get(t.get("key") or "")
        if not a:
            continue
        t["agent_state"], t["agent_at"] = a["state"], a["at"]
        if a["state"] == "parked" and a["at"] >= (t.get("now_at") or ""):
            t["now"] = f"PARKED {a['at'][11:16]} (agent stopped, main resumes it when {', '.join(a.get('jobs', []))} end): " + str(t.get("now", ""))
        if a["state"] == "stopped" and a["at"] >= (t.get("now_at") or ""):
            t.pop("eta", None)  # a stopped agent has no finish time; the card says so until the main session edits it
            if not str(t.get("now", "")).startswith(("NOT RUNNING", "done")):
                t["now"] = f"NOT RUNNING (agent stopped {a['at'][11:16]}): " + str(t.get("now", ""))
    jobs = load("run") + load("q")
    for t in T.get("tasks", []):  # "running" is derived: a live agent or a running/queued job, else the card is idle
        if t.get("group") != "agents" or t.get("agent_state") == "running":
            continue
        if any(task_of(j, [t]) for j in jobs):
            continue
        t["group"] = "review" if t.get("prs") else "waiting"
        t["idle_from"] = "agents"
        t.pop("eta", None)
    return T


def load(d):
    out = []
    for p in glob.glob(os.path.join(J, d, "*.json")):
        try:
            j = json.load(open(p)); j["_mtime"] = os.path.getmtime(p); out.append(j)
        except Exception:
            pass
    return out


def to_dt(hms, now):
    t = datetime.combine(now.date(), datetime.strptime(hms, "%H:%M:%S").time())
    return t - timedelta(days=1) if t > now + timedelta(minutes=1) else t


def simulate(running, queued, evs, now, busy_builds=0):
    """Rough schedule with the dispatcher's rules: timing runs alone (no build, no other GPU job); correct jobs share
    the GPU with each other and run beside builds; builds have two slots. Hand-started builds hold slots ~10 min."""
    by_id, by_stem, st = {}, {}, {}
    for t, kind, jid, rest in evs:
        m = re.search(r" (\d+) min", rest)
        if kind in ("DONE", "FAIL") and m:
            by_id.setdefault(jid, []).append(int(m.group(1))); by_stem.setdefault(stem(jid), []).append(int(m.group(1)))
        if kind == "START":
            st[jid] = t

    def est(j):
        for src, k in ((by_id, j["id"]), (by_stem, stem(j["id"]))):
            if src.get(k):
                return max(1, statistics.median(src[k][-5:])), True
        d = DEFAULT.get(j.get("lane"), 12)
        return min(d, j.get("deadline_min", d)), False

    iv = []  # (start, end, lane) of placed work

    def clash(s, e, lane):
        for a, b, l in iv:
            if a < e and s < b:
                if (lane == "x86") != (l == "x86"):  # the x86 box: its own lane, one job at a time
                    continue
                if lane == "x86":
                    return b
                if lane == "timing" or l == "timing":
                    return b
                if lane == "build" and l == "build" and sum(1 for a2, b2, l2 in iv if l2 == "build" and a2 < e and s < b2) >= 2:
                    return min(b2 for a2, b2, l2 in iv if l2 == "build" and a2 < e and s < b2)
                if lane == "correct" and l == "correct":
                    continue
        return None

    def place(s, m, lane):
        for _ in range(500):
            e = s + timedelta(minutes=m)
            c = clash(s, e, lane)
            if c is None:
                iv.append((s, e, lane)); return s, e
            s = c
        iv.append((s, s + timedelta(minutes=m), lane)); return s, s + timedelta(minutes=m)

    for _ in range(busy_builds):
        iv.append((now, now + timedelta(minutes=10), "build"))
    done_at, rows = {}, []
    for j in running:
        m, h = est(j)
        t0 = to_dt(st[j["id"]], now) if j["id"] in st else now
        end = max(now + timedelta(minutes=1), t0 + timedelta(minutes=m)); done_at[j["id"]] = end
        iv.append((now, end, j.get("lane", "build")))
        rows.append(dict(j, _state="running", _start=t0, _end=end, _est=m, _hist=h, _deps=[]))
    pend = sorted(queued, key=lambda j: (-j.get("prio", 0), j["_mtime"]))
    while pend:
        left = []
        for j in pend:
            deps = DEP.findall(j.get("ready", "") or "")
            if any(d not in done_at and any(q["id"] == d for q in pend) for d in deps):
                left.append(j); continue
            m, h = est(j)
            after = max([done_at.get(d, now) for d in deps] + [now])
            s, e2 = place(after, m, j.get("lane", "build"))
            done_at[j["id"]] = e2
            rows.append(dict(j, _state="queued", _start=s, _end=e2, _est=m, _hist=h, _deps=deps))
        if len(left) == len(pend):
            rows += [dict(j, _state="blocked", _start=None, _end=None, _est=0, _hist=False, _deps=DEP.findall(j.get("ready", "") or "")) for j in left]
            break
        pend = left
    return rows, max(done_at.values(), default=now)


def finished(evs):
    last = {}
    for t, kind, jid, rest in evs:
        if kind in END:
            last[jid] = (kind, rest.strip())
    out, cut = [], time.time() - 86400
    for p in glob.glob(os.path.join(J, "done", "*.json")):
        m = os.path.getmtime(p)
        if m < cut:
            continue
        try:
            j = json.load(open(p))
        except Exception:
            continue
        kind, rest = last.get(j.get("id"), ("?", ""))
        mins = re.search(r"(\d+) min", rest)
        why = rest.split(":", 1)[1].strip()[:300] if kind != "DONE" and ":" in rest else ""
        out.append(dict(j, _state=kind, _ended=datetime.fromtimestamp(m), _took=int(mins.group(1)) if mins else None, _why=why))
    return sorted(out, key=lambda r: r["_ended"], reverse=True)


def task_of(j, ts):
    for t in ts:
        if j.get("owner") in t.get("owners", []) or any(j["id"].startswith(p) for p in t.get("prefixes", [])):
            return t
    return None


def outside():
    """Builds holding a tfb slot that the dispatcher did not start (agents running tfb by hand)."""
    mine = {j["id"] for j in load("run")}
    out = []
    for lock in ("/tmp/claude-1000/tfbuild.lock", "/tmp/claude-1000/tfbuild.1.lock"):
        r = subprocess.run(["lsof", "-t", lock], capture_output=True, text=True)
        pids = sorted(int(x) for x in r.stdout.split())
        if not pids:
            continue
        p = pids[0]
        try:
            cmd = open(f"/proc/{p}/cmdline", "rb").read().replace(b"\0", b" ").decode(errors="replace").strip()
            cwd = os.readlink(f"/proc/{p}/cwd")
            age = time.time() - os.stat(f"/proc/{p}").st_mtime
        except OSError:
            continue
        br = subprocess.run(["git", "-C", cwd, "branch", "--show-current"], capture_output=True, text=True).stdout.strip()
        out.append({"pid": p, "cmd": cmd[:300], "cwd": cwd, "min": int(age // 60), "branch": br})
    return out if not mine or True else out


def iso(t):
    return t.isoformat() if isinstance(t, datetime) else t


def state():
    now = datetime.now(); evs = events(); T = tasks(); ts = T.get("tasks", [])
    ob = outside()
    rows, last = simulate(load("run"), load("q"), evs, now, len(ob))
    fin = finished(evs)
    keep = ("id", "owner", "lane", "prio", "mem_gb", "cwd", "cmd", "ready", "deadline_min")

    def job(r, extra):
        t = task_of(r, ts)
        d = {k: r.get(k) for k in keep}
        d["task"] = ts.index(t) if t else None
        d.update({k: iso(v) for k, v in extra.items()})
        return d
    jobs = [job(r, {"state": r["_state"], "start": r["_start"], "end": r["_end"], "est": r["_est"], "hist": r["_hist"],
                    "deps": r["_deps"]}) for r in rows]
    done = [job(r, {"state": r["_state"], "ended": r["_ended"], "took": r["_took"], "why": r["_why"]}) for r in fin]
    refs = {}
    for n, it in gh["refs"].items():
        refs[n] = {"title": it["title"], "kind": kind_of(it), "pr": "pull_request" in it, "url": it["html_url"],
                   "comments": it.get("comments", 0), "updated": it["updated_at"], "closed": it.get("closed_at"),
                   "labels": [l["name"] for l in it.get("labels", [])]}
    cut = datetime.now(timezone.utc) - timedelta(days=14)
    prs = [p["number"] for p in gh["prs"] if p["state"] == "open" or
           datetime.fromisoformat(p["closed_at"].replace("Z", "+00:00")) > cut]
    return {"now": iso(now), "empty": iso(last), "jobs": jobs, "finished": done, "groups": T.get("groups", []),
            "tasks": ts, "goals": T.get("goals", []), "updated": T.get("updated", ""), "usage": dict(usage), "prs": prs, "refs": refs, "gh_at": iso(gh["at"]),
            "gh_err": gh["err"], "repo": REPO, "outside": ob,
            "events": [{"t": t, "kind": k, "id": j, "rest": r.strip()[:240]} for t, k, j, r in evs[-60:]][::-1]}


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        p = urllib.parse.unquote(self.path.split("?")[0])
        if p.startswith("/log/"):
            jid = os.path.basename(p[5:])
            try:
                b = open(os.path.join(J, "done", jid + ".log"), "rb").read()[-60000:].decode("utf-8", "replace")
                b = "\n".join(b.splitlines()[-300:])
            except OSError:
                b = "(no log yet)"
            out, ct = b.encode(), "text/plain; charset=utf-8"
        elif p == "/logo.png":
            out, ct = open(os.path.join(D, "logo-128.png"), "rb").read(), "image/png"
        elif p.startswith("/api/state") or p.startswith("/json"):
            out, ct = json.dumps(state()).encode(), "application/json"
        else:
            out, ct = open(os.path.join(D, "index.html"), "rb").read(), "text/html; charset=utf-8"
        self.send_response(200); self.send_header("Content-Type", ct); self.send_header("Content-Length", str(len(out)))
        self.send_header("Cache-Control", "no-store"); self.end_headers(); self.wfile.write(out)

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    threading.Thread(target=gh_loop, daemon=True).start()
    threading.Thread(target=usage_loop, daemon=True).start()
    ThreadingHTTPServer(("0.0.0.0", int(os.environ.get("DASH_PORT", "8090"))), H).serve_forever()
