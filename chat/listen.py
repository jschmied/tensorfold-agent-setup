"""Print one line per new chat message (all rooms, not my own) since the saved cursor; poll every 10 s. Stdlib only.

Usage: python3 -u listen.py [<your-sender-name>] [--room NAME ...]   (a background monitor: each stdout line is one message)
--room: print only those rooms' messages (by name, repeatable); the others still advance the cursor.
"""
import json, os, sys, time, urllib.request
BASE = "http://<chat-host>:3006/api/v1"
args = sys.argv[1:]
ROOMS = {args[i + 1] for i, a in enumerate(args) if a == "--room" and i + 1 < len(args)}
pos = [a for i, a in enumerate(args) if a != "--room" and (i == 0 or args[i - 1] != "--room")]
ME = pos[0] if pos else "spark-agent"
CUR = os.path.expanduser(f"~/.config/local-agent-chat/cursor-{ME}" if ME != "spark-agent" else "~/.config/local-agent-chat/cursor")

def get(path):
    with urllib.request.urlopen(BASE + path, timeout=10) as r:
        return json.load(r)

def main():
    os.makedirs(os.path.dirname(CUR), exist_ok=True)
    try:
        after = int(open(CUR).read().strip())
    except Exception:  # first run: start at the newest message, read the history by hand if needed
        ev = get("/activity?limit=1")
        ev = ev.get("events", ev) if isinstance(ev, dict) else ev
        after = max([m["seq"] for m in ev], default=0)
    rooms = {}
    while True:
        try:
            if not rooms:
                rooms = {r["id"]: r["name"] for r in get("/rooms")}
            ev = get(f"/activity?after={after}&limit=50&exclude_sender={ME}")
            ev = ev.get("events", ev) if isinstance(ev, dict) else ev
            for m in sorted(ev, key=lambda m: m["seq"]):
                if m["room_id"] not in rooms:  # a new room: fetch the names now, so --room can match it
                    rooms = {r["id"]: r["name"] for r in get("/rooms")}
                room = rooms.get(m["room_id"], m["room_id"][:8])
                text = m["content"].replace("\n", " ")
                if not ROOMS or room in ROOMS:
                    print(f"[{room}] {m['sender']} #{m['seq']}: {text[:400]}", flush=True)
                after = max(after, m["seq"])
                with open(CUR, "w") as f:
                    f.write(str(after))
        except Exception as e:
            print(f"listen error: {e}", file=sys.stderr, flush=True)
        time.sleep(10)

if __name__ == "__main__":
    main()
