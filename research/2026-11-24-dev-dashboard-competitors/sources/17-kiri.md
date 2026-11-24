# Kiri — https://github.com/GaoSSR/kiri
- Title: "GaoSSR/kiri" README + repo metadata
- Publisher: GitHub / GaoSSR
- Tier: L1 (project's own docs)
- Fetched: 2026-11-24 (GitHub REST API)
- source_class: independent-primary
- Repo meta: Rust, 445 stars, Apache-2.0, pushed 2026-08-14; topics include windows, macos, linux, port-management.

## Key quotes (README)
- "High-performance local development port management CLI, powered by Rust… helps you quickly see which local services are running, which ports they use, and handle the process behind a port when needed."
- "`ports` to see a focused local development service overview: port, process, PID, memory usage, project name, detected framework, uptime, and health status."
- Commands: `ports`, `ports --all`, `ports <port>` details, "`ports ps` shows development-related processes that may not listen on a port, such as MCP Server processes started by Codex, Claude Code, or other AI coding tools", `ports logs <port|pid> -f`, "`ports clean` — ask before cleaning orphaned/zombie dev processes", "`ports watch` — stream port start/stop events", "`ports kill 3000-3010` — terminate listeners across a range", "`ports kill --force`".
- Status labels: "`healthy` … `orphaned`: the process is still alive… but the parent process that started it has already exited… `zombie`". Orphan = "closing a terminal, IDE task, script runner, Codex session, or Claude Code session while a child server process keeps running."
- Platform table: "MacOS arm64/x64 Supported; Linux x64 Supported; Windows x64 Supported; Linux arm64 / Windows arm64 Planned."
- Windows mechanics: "Windows uses PowerShell/CIM and `Get-NetTCPConnection`; process working directories are best-effort from executable paths." macOS uses `lsof`, `ps`, `tail`, `log`; Linux `ss`, `ps`, `/proc`; "optional Docker metadata" on all.
- Install: `npm install -g @gaossr/kiri@latest`, `brew install gaossr/tap/kiri`, or Windows PowerShell `irm …/install.ps1 | iex`. Free, Apache-2.0.
