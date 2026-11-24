# PortDoc repo — https://github.com/bradtraversy/portdoc
- Title: "bradtraversy/portdoc" README + repo metadata
- Publisher: GitHub / Brad Traversy
- Tier: L1 (project's own docs)
- Fetched: 2026-11-24 (via GitHub REST API; r.jina.ai github.com blocked)
- source_class: independent-primary
- Repo meta: Rust, 12 stars, license field: none detected on repo, pushed 2026-07-27. NOTE: website claims "open source" but GitHub license API field is empty.

## Key quotes (README)
- "A local dev server control panel. One binary serves a web dashboard showing what dev apps are running, which project owns each port, what URL to open, and what can be stopped safely."
- "Project-grouped dashboard — services grouped by the repo that owns them, with framework labels (Next.js, Vite, Express, Redis, Postgres, and more), git branch, and package manager"
- "Exposure labels — know what is local-only, LAN-visible, or Docker-bound"; "Stale hints — find the dev server you forgot about last week"; "Safe stop — graceful stop first, with force only behind a second explicit yes"; "Docker and Advanced tabs — container hints, raw sockets, JSON export"
- Windows install: "`irm https://portdoc.dev/install.ps1 | iex`"; "The server binds `127.0.0.1` only; nothing is reachable from the network."
- Background mode: "Linux uses a systemd user service named `portdoc.service`. macOS uses a LaunchAgent named `com.traversymedia.portdoc`. Windows uses a Task Scheduler task named `PortDoc`." — no admin required.
- "Windows binaries are Authenticode-signed (as 'Brad Traversy') since v0.1.1, so Smart App Control and SmartScreen accept them. macOS binaries are unsigned."
- Stack: "`src/` - Rust binary: clap CLI entry, axum server, platform probes; `web/` - React + TypeScript + Vite frontend"; default port `127.0.0.1:7788`.
- Releases via cargo-dist → GitHub Releases + Homebrew tap.
