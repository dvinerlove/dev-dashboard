# Switchboard — https://destucr.github.io/Switchboard/
- Title: "Switchboard: Mac menu bar port manager for localhost"
- Publisher: destucr (GitHub Pages)
- Tier: L2 (vendor-authored product site)
- Fetched: 2026-11-24
- source_class: vendor-authored

## Key quotes
- "Switchboard sits in your Mac menu bar and shows everything running on localhost, grouped by project. Open it, restart it, read its logs or stop it without going back to the terminal."
- "Free and open source. Needs macOS 14 or later."
- Dependency map: "A map shows which servers talk to each other. Stop the database and it tells you the API and the web app are still using it, before you pull the plug." (web:3000 → api:8000 → postgres:5432)
- Port conflicts: "If you start something whose port is taken, Switchboard says who is using it and offers the next free one. You can also move a running server to another port, and undo it."
- Restart/project resume: "Stopped servers stay on the list. One click starts the whole project again, in the order its servers depend on each other. Save a `switchboard.json` in your repo and a teammate gets the same stack." (switchboard.json has services + dependsOn)
- "Undo after Stop — Undo starts it again, in the same folder with the same command."
- "Logs right here — Output follows live inside the popover… send it to Terminal, iTerm, Ghostty, Warp, tmux and more."
- "Why did it stop? Crash, closed terminal, or another process took the port. It tells you which, with the last lines of output."
- "The Homebrew install adds a `switchboard` command for status, start and stop."
- Signing: "Switchboard is not notarized yet, so macOS asks you to confirm the first launch."
