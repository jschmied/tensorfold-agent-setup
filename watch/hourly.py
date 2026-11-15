#!/usr/bin/env python3
"""Hourly watch in one call: prints only what changed since the last run."""
import json, os, subprocess, datetime
ST = os.path.expanduser("~/notes/watch/last.txt")
NUMS = "2012 2011 2005 1960 1954 1863 1945 1943 1928 1925 1923 1917 1918 1919 1914 1901 1902 1903 1904 1905 1906 1907 1873 1872 1870 1865 1864 1863 1853 1852 1850 1840 1839 1838 1837 1755 1697 1696 1692 1691 1673 1672 1666 1660 1659 1657 1653 1634 1620 1619 1609 1581 1513 1510 1502 1479 1394 1593 1592 1591 1589 1588 1586 1581 1584 1565 1564 1556 1555 1554 1553 1550 1541 1537 1535 1532 1508 1503 1492 1491 1489 1488 1479 1460 1448 1440 1413 1411 1409 1387 1362 1363 1355 1356 1357 1358 1359 1353 1354 1350 1351 1332 1303 1304 1302 1301 840 1293 1294 1289 548 1286 1287 1284 1222 1256 1257 1258 1259 1260 1261 1247 1245 1244 1233 1188 746 798 874 1047 1056 1068 1070 1071 1073 1123 1124 850 620 627 608 593 781 443 548 654 669 670 1035 856 1015 1027 1050 869 952 286 603 918 799 1078 1079 1080 1168 1046 1062 1069 1113 1142 1059 1048 1143 1144 1145 1146 1147 1155 1156 1164 1169 1170 1171 1173 1174 1181 1182 1183 1184 1185 1186 1195 1219".split()
WT = ["tf-kvdisk", "tf-p16", "tf-hostfix", "tf-548", "tf-1156rest", "tf-pf1188fix", "tf-pf1188sched", "tf-27b-v2", "tf-dory-paged", "tf-ling-tiny", "tf-qwen4", "tf-g4fix", "tf-dory", "tf-dory-kernels", "tf-prefill", "tf-dory-maps"]
def sh(c):
    return subprocess.run(c, shell=True, capture_output=True, text=True).stdout.strip()
now = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
since = open(ST).read().strip() if os.path.exists(ST) else now
print("now", now, "since", since)
tw = sh("python3 /home/jschmied/git/qwen38-flash-next-gb10/tools/tfwatch.py 2>&1")
if tw:
    print("\n".join(l for l in tw.splitlines() if not l.startswith("  files")))
print(sh("python3 ~/ling31/work/hfling.py 2>&1 | tail -3"))
for n in NUMS:
    for ep in (f"issues/{n}/comments?since={since}",):
        out = sh(f"gh api 'repos/ashhart/TensorFold/{ep}' --jq '.[]|select(.user.login!=\"jschmied\")|\"#{n} \\(.user.login): \\(.body[:160]|gsub(\"\\n\";\" \"))\"' 2>/dev/null")
        if out:
            print(out)
    rv = sh(f"gh api 'repos/ashhart/TensorFold/pulls/{n}/reviews' --jq '.[]|select(.user.login!=\"jschmied\" and .submitted_at>\"{since}\")|\"#{n} REVIEW \\(.user.login) \\(.state)\"' 2>/dev/null")
    if rv and not rv.startswith("{"):
        print(rv)
m = sh(f"gh api 'notifications?all=true&participating=true&since={since}' --jq '.[]|select(.repository.full_name==\"ashhart/TensorFold\" and .reason==\"mention\")|\"mention #\\(.subject.url|split(\"/\")|last) \\(.subject.title[:60])\"'")
if m:
    print(m)
# tagged: threads that involve us, updated since the last run; every comment, inline review
# comment or review by someone else after our own last word there. NUMS above is static, this is not.
def gj(p):
    try:
        v = json.loads(sh(f"gh api --paginate '{p}' 2>/dev/null") or "[]")
    except json.JSONDecodeError:
        return []
    return v if isinstance(v, list) else []  # an issue has no pulls/ endpoints: a 404 object
q = f"repo:ashhart/TensorFold updated:>={since} involves:jschmied"
hits = json.loads(sh(f"gh api -X GET search/issues -f q='{q}' -f per_page=50 --jq '[.items[]|[.number,.user.login]]' 2>/dev/null") or "[]")
if not isinstance(hits, list):
    print("TAGGED search failed:", str(hits)[:120]); hits = []
for n, who in hits:
    ev = [(c["created_at"], c["user"]["login"], c["body"] or "") for c in gj(f"repos/ashhart/TensorFold/issues/{n}/comments?per_page=100")]
    ev += [(c["created_at"], c["user"]["login"], "inline: " + (c["body"] or "")) for c in gj(f"repos/ashhart/TensorFold/pulls/{n}/comments?per_page=100")]
    ev += [(c.get("submitted_at") or "", c["user"]["login"], f"review {c['state']}: " + (c.get("body") or ""))
           for c in gj(f"repos/ashhart/TensorFold/pulls/{n}/reviews?per_page=100") if c.get("body") or c["state"] != "COMMENTED"]
    ev.sort()
    last = max((t for t, u, _ in ev if u == "jschmied"), default="")
    for t, u, b in ev:
        # our own threads: everything; others' threads: only what names us
        if (u != "jschmied" and t > last and t > since and not b.lstrip().startswith("/atc") and "atc:" not in b[:40]
                and (who == "jschmied" or "@jschmied" in b)):
            print(f"TAGGED #{n} {u}{' @us' if '@jschmied' in b else ''}: {b[:160]}".replace("\n", " "))
XC = sh("ls -d ~/.claude/plugins/cache/atc-github/atc/*/ | tail -1")
for pr in ("1619", "1620", "1653"):
    ib = sh(f"node {XC}src/exchange/main.js inbox {pr} --repo ashhart/TensorFold --origin https://tensorfold.dev --text 2>&1 | sed -n 2p")
    if ib and not ib.startswith("0 pending, 0 resolved"):
        print(f"EXCHANGE #{pr}: {ib}")
for rp in ("cudafast-qwen38-27b-tf-engine", "mlxfast-qwen38-27b-tf-engine"):
    cf = sh(f"gh api 'repos/Layr-Labs/{rp}/commits?since={since}' --jq '.[]|\"{rp[:7]} \\(.sha[:7]) \\(.commit.message|split(\"\\n\")[0][:60]) \\(.commit.message|capture(\"Co-authored-by: (?<a>[^ <]+)\").a // \"\")\"' 2>/dev/null")
    if cf:
        print("BOARD", cf, "(Accept = promoted: move ~/git/cudafast-27b branch promoted)")
ch = sh(f"curl -s --max-time 5 'http://<chat-host>:3006/api/v1/activity?limit=50&exclude_sender=spark-agent' | python3 -c \"import json,sys;[print('CHAT', e.get('room_name'), e['sender'], '#'+str(e['seq'])+':', e['content'][:160].replace(chr(10),' ')) for e in json.load(sys.stdin)['events'] if e['created_at']>'{since}']\" 2>&1")
if ch:
    print(ch)
# LEDGER: an `open [#n]` cell in docs/optimization-ledger.md whose PR has merged needs its flip (once a day)
import re, time
LST = os.path.expanduser("~/notes/watch/ledger.last")
due = not os.path.exists(LST) or time.time() - os.path.getmtime(LST) > 86400
lg = "" if not due else sh("git -C ~/git/tf-ledger fetch -q origin main 2>/dev/null; git -C ~/git/tf-ledger show origin/main:docs/optimization-ledger.md 2>/dev/null || cat ~/git/tf-ledger/docs/optimization-ledger.md")
rows = {}
for line in lg.splitlines():
    for n in re.findall(r"open [A-Z]?\[#(\d+)\]", line):
        rows.setdefault(n, []).append(line.split("|")[1].strip())
for n, rr in sorted(rows.items(), key=lambda kv: int(kv[0])):
    if sh(f"gh api repos/ashhart/TensorFold/pulls/{n} --jq .merged_at 2>/dev/null") not in ("", "null"):
        print(f"LEDGER #{n} merged: flip {', '.join(sorted(set(rr)))}")
if due:
    open(LST, "w").write(now)
# shared Zig cache: wipe it whole once it passes 25 GB. Never delete o/ entries alone: the h/ manifests
# still name them and the next build fails FileNotFound instead of rebuilding. Hold both tfb slots so
# no build is mid-flight; skip this round if either slot is busy.
zc = sh("du -s --block-size=1G ~/.cache/zig-local 2>/dev/null | cut -f1")
if zc.isdigit() and int(zc) > 25:
    r = sh("flock -n /tmp/claude-1000/tfbuild.lock flock -n /tmp/claude-1000/tfbuild.1.lock "
           "sh -c 'mv ~/.cache/zig-local ~/.cache/zig-local.wipe && echo WIPED' 2>/dev/null")
    if r == "WIPED":
        sh("rm -rf ~/.cache/zig-local.wipe")
        print(f"ZIGCACHE was {zc} GB, wiped (both build slots were free)")
    else:
        print(f"ZIGCACHE {zc} GB, wipe skipped: a build slot is busy")
print("disk", sh("df -h / | tail -1 | awk '{print $4}'"), "| mem free/avail", sh("free -g | awk 'NR==2{print $4\"/\"$7}'"))
print("tmux", sh("tmux ls -F '#S' | tr '\\n' ' '"))
for w in WT:
    p = os.path.expanduser(f"~/git/{w}")
    if os.path.isdir(p):
        print(w, sh(f"git -C {p} log --oneline -1 | cut -c1-70"), "dirty", sh(f"git -C {p} status --short | wc -l"))
open(ST, "w").write(now)
print("usage", sh("python3 ~/.claude/usage-report.py --json | python3 -c \"import json,sys;v=json.load(sys.stdin);r=v.get('rate_pct_per_h',{});print(v['state'], f\\\"7d {v.get('d7')}% 5h {v.get('h5')}% burn6h {r.get('6h')}%/h budget {v.get('allowed_pct_per_h')}%/h proj {v.get('projected_d7_at_reset')}% reset {v.get('d7_reset_in')}\\\")\""))

# Durable ask list: every non-self comment after our last reply that nobody marked handled (open-asks.py done ID).
print(sh("python3 ~/notes/watch/open-asks.py 2>&1"))
