# Portarium — https://github.com/y-tretyakov/portarium
- Title: "y-tretyakov/portarium" README + repo metadata
- Publisher: GitHub / y-tretyakov
- Tier: L1 (project's own docs)
- Fetched: 2026-11-24 (GitHub REST API)
- source_class: independent-primary
- Repo meta: Rust (Tauri 2 desktop + Ratatui/OpenTUI TUI + CLI), 5 stars, MIT, pushed 2026-07-23.

## Key quotes (README)
- "A blazing-fast, native developer port manager… Portarium watches your ports, tracks traffic, and visualizes network topology — in your terminal, CLI, or desktop." Windows + macOS + Linux (incl. arm64 where available).
- "Real-Time Port Dashboard — Every listening port at a glance — process name, PID, connections, framework detection, and project identification."
- "One-Click Control — Kill any process instantly. If the start command is known, restart it directly in a new terminal. Dead processes show a stopped badge with a persistent restart button."
- "Interactive Port Map (Desktop) — A D3.js-powered network topology visualization showing how your services communicate." "System Tray… traffic light icon alerts you to conflicts."
- "Smart Detection Engine — Framework Detection: Recognizes React, Vite, Angular, Django, Node, and more via default ports. Project Context: Crawls for `package.json`, `Cargo.tomr`, or `go.mod` to name your running servers."
- TUI pages: Ports / Dashboard / Services (grouped by project or framework) / Logs (event log of port starts/stops); keys incl. `k` kill, `K` kill all filtered, `r` restart.
- Platform mechanics: "Linux/macOS `lsof -iTCP -sTCP:LISTEN -n -P`, kill SIGTERM→2s→SIGKILL; Windows `netstat -ano`, `taskkill /PID <pid> /F`, restart `cmd /C start cmd /K <cmd>`." "Windows: Built-in `netstat` / `taskkill`."
- "All data is collected in-process via system commands (`lsof`/`ss`/`netstat`) and `/proc`. No external services, daemons, or network connections required." MIT license, free.
