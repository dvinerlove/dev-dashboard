# Source 06 — PortDoc repo README

- URL: https://github.com/bradtraversy/portdoc (raw README.md)
- Title: PortDoc — "A local dev server control panel"
- Publisher: GitHub repo (vendor-authored)
- Tier: L1 · source_class: repo
- Fetched: 2026-11-23

## Key verbatim quotes

1. "One binary serves a web dashboard showing what dev apps are running, which project owns each port, what URL to open, and what can be stopped safely."
2. "**Project-grouped dashboard** - services grouped by the repo that owns them, with framework labels (Next.js, Vite, Express, Redis, Postgres, and more), git branch, and package manager"
3. "**Exposure labels** - know what is local-only, LAN-visible, or Docker-bound"
4. "**Stale hints** - find the dev server you forgot about last week"
5. "**Safe stop** - graceful stop first, with force only behind a second explicit yes"
6. "**Docker and Advanced tabs** - container hints, raw sockets, JSON export"
7. "Background mode uses the current user's native process manager and does not require administrator privileges: Linux uses a systemd user service … macOS uses a LaunchAgent … Windows uses a Task Scheduler task."
8. "`background start` … refuses to replace a foreground PortDoc or another application already using the requested port."
9. Stack: "`src/` - Rust binary: clap CLI entry, axum server … `web/` - React + TypeScript + Vite frontend"; dashboard served on `127.0.0.1:7788`.
