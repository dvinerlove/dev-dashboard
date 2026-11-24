# Roulette — https://github.com/Nexvyn/Roulette (site roulette.nexvyn.dev)
- Title: "Nexvyn/Roulette" README + repo metadata
- Publisher: GitHub / Nexvyn
- Tier: L1 (project's own docs)
- Fetched: 2026-11-24 (GitHub REST API)
- source_class: independent-primary
- Repo meta: TypeScript (Tauri 2 + Rust + React), 6 stars, MIT, pushed 2026-10-26. Electron version abandoned ("Electron app stays… gets no new features").

## Key quotes (README)
- "Roulette lives in your menu bar (the system tray on Windows) and finds every development server running on your machine. Each one shows its project, git branch, port and uptime, and you can open it, kill it, rename it, pin it or share it with a public link."
- Detection: "Finds running dev servers on macOS (`lsof`), Windows (`netstat`) and Linux (`ss`)"; "Shows the project folder, git branch, port, uptime and memory, with the framework's logo on each row."
- "Stop ends the whole server, including the package manager that started it." "Details for each server: folder, command, branch, processes, and 10 minutes of memory and CPU."
- "Warns when a server uses too much memory or keeps growing: amber memory, a dot on the tray icon and one notification (limit in Settings, snooze for an hour)."
- "Clean up: tick the servers to stop, with idle ones and ones whose folder is gone ticked for you. Databases are never ticked for you. Forgotten servers can also be reported or stopped on their own."
- Agent links: "Links a server to the Claude Code or Codex session, Conductor workspace or Pane terminal that started it, and (optional) to the branch's pull request through the GitHub CLI."
- "Picks up Docker containers that publish a port… Stop runs `docker stop` on that container only."
- Sharing: "Share any server through a Cloudflare Quick Tunnel: a public `trycloudflare.com` link… Links can expire on their own after 1 or 4 hours."
- "Rename and pin servers… A name belongs to its port and project." Global shortcut "Ctrl Alt P, or ⌥⌘P on macOS". CLI: "`roulette list` and `roulette list --json`".
- Update model: "Updates itself: when a new version is out, the panel offers **Restart to update**"; "Installed copies check `latest.json` on the newest published release, 20 seconds after launch and then once a day. Updates are signed." Free, MIT.
