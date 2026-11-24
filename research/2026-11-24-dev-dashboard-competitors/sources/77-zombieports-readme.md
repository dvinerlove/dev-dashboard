# Source 77 — ArkaKhorchidian/zombieports README

- URL: https://github.com/ArkaKhorchidian/zombieports
- Publisher: GitHub (repo README — vendor-authored; cited because it codifies the "forgotten server" heuristics users want)
- Tier: L4
- Fetch date: 2026-11-24 (raw README, full)

## Key verbatim quotes

- "You know the drill: `Error: listen EADDRINUSE :::3000`, then `lsof -i :3000`, then squinting at a PID, then `kill -9`. Or the Vite server from last Tuesday that's still holding 5173."
- Zombie heuristics (a dev server is flagged when): "**its terminal is gone**: the shell that started it exited and it got re-parented to `init`/`launchd`; **its folder was deleted**: it's serving a project that no longer exists; **a newer copy is running**: two `next dev` servers for the same project, the older one is almost certainly forgotten; **it's been up for more than a day**."
- "Databases, Docker, and apps the OS launched are never flagged." — protect-list ask (same as Sweepling's protect list, Portkeeper's lock).
- "`z` | Kill every zombie (asks first)" — bulk cleanup with confirmation.
- Status column: "`open to your network` when a dev server or database listens on all interfaces" — LAN-exposure warning.
- Project detection: "package.json's name, or the folder holding pyproject.toml, Cargo.toml, go.mod, .git" — cwd→project attribution again.

## Takeaway

The "forgotten/zombie server" concept now has a de-facto heuristic spec shared across tools (orphaned, dead-folder, duplicated, >24h), plus never-flag protect classes (databases, OS services).
