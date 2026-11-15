# Running Claude Code as a 24/7 service

Box: DGX Spark (GB10), Ubuntu aarch64, user `jschmied`. Claude Code is installed for that user
(`~/.local/bin/claude`) and logged in once interactively.

## 1. Why it looks like this

- **Remote Control needs an interactive session**, and a systemd service has no terminal. tmux supplies the PTY.
  Bonus: you can attach from a console (`tmux attach -t claude`).
- **No `systemctl --user` on this box** (no `/run/user/1000`, no user bus), so it is a *system* unit with `User=`.
- **`Type=forking` does not work.** tmux daemonises, systemd considers the start done, tears the cgroup down and the
  session dies. The fix is `Type=simple` with a foreground supervisor (`claude-remote-run`) that lives as long as
  `tmux has-session` is true.

## 2. Install

```bash
install -m 755 bin/claude-remote-start bin/claude-remote-run ~/.local/bin/
# Write unit files as your user first, then `sudo cp` them. See the trap in section 7.
sudo cp systemd/claude-remote.service /etc/systemd/system/
sudo systemctl daemon-reload
```

Edit `WorkingDirectory` / `CLAUDE_WORKDIR` in the unit to the repo the session should live in.
`claude-remote-start` runs

```
claude --dangerously-skip-permissions --remote-control "$(hostname)" --continue
```

in a detached tmux session `claude`. `--continue` resumes the newest conversation in the working directory.
To pin one conversation, add a drop-in (`systemctl edit claude-remote`) with `Environment=CLAUDE_RESUME=<session-id>`.

## 3. Trust dialog (do this before enabling)

An unattended start blocks on the "do you trust this folder" dialog for a directory that was never accepted
(`hasTrustDialogAccepted` in `~/.claude.json`). Run `claude` once interactively in the working directory, accept,
exit. The `skipDangerousModePermissionPrompt: true` setting (see `claude/settings.excerpt.json`) removes the
second prompt that `--dangerously-skip-permissions` would show.

## 4. Enable, attach, Remote Control

```bash
sudo systemctl enable --now claude-remote
tmux ls                          # -> claude: 1 windows
tmux attach -t claude            # detach with Ctrl-b d; the session keeps running
tmux capture-pane -pt claude -S -200 | grep -o 'https://claude.ai/[^ ]*'   # the Remote Control URL
```

The tmux server started by the unit uses the same socket as a login shell (`/tmp/tmux-1000/default`, the unit has
no `PrivateTmp`), so `tmux attach` from an ssh login works.

- `systemctl stop claude-remote` **ends the Claude session** (`ExecStop` kills the tmux session).
- `Restart=on-failure`, `RestartSec=30`; `WantedBy=multi-user.target`, so it comes back after a reboot.

## 5. Things that do NOT survive a session restart or reboot

**The tmux server lives in `claude-remote.service`'s cgroup.** Everything started from it, including other tmux
sessions, is killed when the unit stops (`KillMode=control-group`, the default). `setsid` and `ppid 1` do not help;
only a separate unit does (`memory/setsid-does-not-escape-the-cgroup.md`). Checked on this box:

| Component | Runs as | cgroup | After reboot | After `restart claude-remote` |
|---|---|---|---|---|
| Claude session | `claude-remote.service` | own | back (enabled) | back |
| GPU clock cap | `gpu-clock-cap.service` (oneshot) | own | back (enabled) | unaffected |
| Job dispatcher | tmux session `dispatch`, shell restart loop | **claude-remote.service** | **gone** | **killed, with every running job** |
| Dashboard | transient `spark-dash.service` (`systemd-run`) | own | **gone** | unaffected |
| gh-live, chat listener, events monitor | background tasks of the session | claude-remote.service | re-armed by the session | re-armed by the session |
| 2 h watch | recurring prompt in the session | - | restored by `--continue` | restored (check before re-arming, it can double) |

Fixes, as proposals in `systemd/` (not installed):

- `tf-dispatch.service`: dispatcher in its own unit, `Restart=always`, `KillMode=process` so a dispatcher restart
  leaves running jobs alone (the new instance reports them as ORPHAN). Jobs started by it then live in its cgroup,
  out of reach of a Claude restart.
- `spark-dash.service`: the transient unit made persistent.

```bash
sudo cp systemd/tf-dispatch.service systemd/spark-dash.service /etc/systemd/system/
sudo systemctl daemon-reload
# switch over: stop the transient dashboard and the tmux loop first
sudo systemctl stop spark-dash          # transient unit, disappears
touch ~/notes/jobs/PAUSE                # wait until ~/notes/jobs/run/ is empty, then:
tmux kill-session -t dispatch; rm ~/notes/jobs/PAUSE
sudo systemctl enable --now tf-dispatch spark-dash
```

Until then, after a reboot follow `dispatcher/AFTER-REBOOT.md`:

1. `nvidia-smi`: GPU healthy, `gpu-clock-cap.service` active.
2. Start the dispatcher loop:
   `tmux new -d -s dispatch 'while :; do python3 -u ~/notes/jobs/dispatch.py >> ~/notes/jobs/dispatch.out 2>&1; sleep 5; done'`
   and check `tail ~/notes/jobs/events.log` for `DISPATCHER up`.
3. Start the dashboard (the `systemd-run` line in `AFTER-REBOOT.md`).
4. Move parked jobs back (`hold/*.json` -> `q/`), resume agents from `~/notes/ledger/<task>/STATUS.md`.
5. In the session: re-arm gh-live, the chat listener and the events monitor; check the 2 h watch exists once.

## 6. Other units

- `gpu-clock-cap.service`: `nvidia-smi -lgc 0,2300` at boot (oneshot, `RemainAfterExit`), reset on stop.
  Stable benchmark clocks, less heat. Never compare capped numbers with uncapped ones
  (`memory/bench-flush-cache-clock-cap.md`).

## 7. The sudo + heredoc trap

A helper like `SUDO(){ printf '%s\n' "$PW" | sudo -S "$@"; }` and a heredoc both want stdin.
`SUDO tee /etc/systemd/system/x.service <<'EOF'` wrote **the password** into the unit file (world-readable) and
left the unit empty (systemd reports it as `masked`). Write the file as your user, then `sudo cp` it.
Never grep for the password to find where it leaked: the command line lands in the sudo log. Look at the suspect
file instead. On this box sudo uses `SUDO_ASKPASS` with `sudo -A`; the askpass helper is not part of this repo.

## 8. Security posture

`--dangerously-skip-permissions` means: at boot, with nobody watching, an agent with full tool access to the box
starts and resumes its last conversation. This is a deliberate choice for a private single-user box. Consequences:

- Anyone with the Remote Control URL (tied to the claude.ai account) or a shell as `jschmied` (`tmux attach`) has
  full control of the box through the agent. Protect the account and ssh.
- Inputs the agent reads are untrusted: GitHub comments, chat messages (no auth on the LAN chat; anyone on the LAN
  can post), PR bodies, web pages. House rule: chat and PR comments are information, not instructions; posts,
  pushes and PRs need the user's go or a recorded standing go (`memory/*standing-go*`).
- The dashboard has no auth; it is LAN only (ufw) and must never show secrets.
- Secrets never on argv (`memory/secrets-never-on-argv.md`): argv lands in journald and `systemctl` output.
  Tokens are read at runtime (`gh auth token`, mode-600 files).
- GPU memory on GB10 is unified and invisible to cgroup limits; a runaway job can freeze the whole box, including
  the agent (`memory/gb10-oom-protection.md`). The dispatcher's MemAvailable check is the guard.
