---
name: claude-autostart-remote-control
description: Claude Code startet nach Reboot per systemd in tmux, mit Remote Control und übersprungenen Berechtigungen (Unit claude-remote.service)
metadata:
  type: project
---

**Eingerichtet 2026-08-24.** `claude-remote.service` (System-Unit, `User=jschmied`) startet beim
Hochfahren `claude --dangerously-skip-permissions --remote-control <hostname> --continue` in einer
losgelösten tmux-Sitzung namens `claude`, Arbeitsverzeichnis `~/git/dgx-spark-setup-guide`.

- **Anhängen von der Konsole: `tmux attach -t claude`** — geprüft: der Dienst-tmux nutzt denselben
  Socket `/tmp/tmux-1000/default` wie eine Login-Shell (`PrivateTmp=no`), läuft als `jschmied` und
  im Repo-Verzeichnis. Lösen mit `Ctrl-b d`, die Sitzung läuft weiter.
- ⚠️ `systemctl stop claude-remote` **beendet die Claude-Sitzung** (ExecStop killt die tmux-Sitzung)
- Fernsteuerung: die claude.ai-URL, die die Sitzung ausgibt
- Andere Unterhaltung anheften: Drop-in mit `Environment=CLAUDE_RESUME=<session-id>` statt `--continue`
- Skripte: `~/.local/bin/claude-remote-start` (startet tmux) und `claude-remote-run` (bleibt im
  Vordergrund, solange die tmux-Sitzung lebt)

**Warum tmux:** Remote Control verlangt eine *interaktive* Sitzung, ein systemd-Dienst hat kein
Terminal. Und **`systemctl --user` gibt es auf dieser Box nicht** (kein `/run/user/1000`, kein
User-Bus) → System-Unit mit `User=`.

⚠️ **`Type=forking` funktioniert NICHT.** tmux daemonisiert, systemd räumt danach die Cgroup ab und
die Sitzung stirbt. Lösung: `Type=simple` plus ein Vordergrund-Supervisor, der lebt, solange
`tmux has-session` zutrifft.

⚠️ **Vertrauens-Dialog blockiert unbeaufsichtigte Starts** in Verzeichnissen, die noch nicht
freigegeben sind (`hasTrustDialogAccepted` in `~/.claude.json`). Unser Arbeitsverzeichnis ist es.

⚠️ **Sicherheitslage:** Beim Hochfahren läuft ein Agent mit umgangenen Berechtigungen, ohne dass
jemand davorsitzt. Bewusste Entscheidung des Nutzers; wer Zugriff auf die Remote-Control-URL oder
auf `tmux attach` hat, hat vollen Werkzeugzugriff auf die Box.

## Die Falle, die mich das gekostet hat
`SUDO(){ printf '%s\n' "$PW" | sudo -S ...; }` **verträgt sich nicht mit Heredocs** — beide wollen
stdin. `SUDO tee datei <<'EOS'` schrieb **das Passwort** in die Datei statt des Inhalts, weltweit
lesbar, und die Unit blieb leer (systemd meldet das als `masked`).
**Richtig:** Datei als Nutzer ins Scratchpad schreiben, dann `sudo cp` — `cp` braucht kein stdin.
**Und niemals nach dem Passwort greppen**: `sudo grep -rl <pw> /etc` schreibt es in die
sudo-Protokolle. Stattdessen die verdächtige Datei ansehen.
