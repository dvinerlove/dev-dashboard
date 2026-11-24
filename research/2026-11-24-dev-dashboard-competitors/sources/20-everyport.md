# Everyport — https://github.com/greenfield-inc/everyport (site everyport.dev)
- Title: "greenfield-inc/everyport" README + repo metadata
- Publisher: GitHub / Greenfield Inc (makers of Pane)
- Tier: L1 (project's own docs)
- Fetched: 2026-11-24 (GitHub REST API)
- source_class: independent-primary
- Repo meta: Rust (Tauri app + CLI), 2 stars, MIT, pushed 2026-09-30. Also on npm/crates.io/PyPI.

## Key quotes (README)
- "See every dev server on your machine, or on any box you can reach, from your menu bar. What it is, which branch it's on, which coding agent started it, and what it costs you."
- "It runs on macOS, Windows and Linux. It also watches remote machines over SSH, Docker, Kubernetes, WSL, or any command that can run a program there." "Free and open source. No account. No telemetry."
- Detection: "Every listening dev server with its port, project, git branch or worktree, framework and uptime; Memory and CPU for the whole process tree behind each port, with a 10-minute history chart."
- Cleanup: "Spike alerts when a server's memory crosses your threshold or keeps climbing; Clean up: servers whose worktree was deleted, or that are idle, long-running or leaking memory; Auto-kill… set to ask first or act on its own. Clean up and auto-kill skip protected processes, such as databases."
- Agent integration: "See the Claude Code or Codex session that started a server, and resume it in your terminal (on this computer and in WSL)"; "See the Conductor workspace, Pane worktree or git worktree each server runs in."
- Remote: "On Windows, every WSL distro shows up on its own, with the real Linux process behind each port. Add machines from `~/.ssh/config`… Connect over `ssh`, `docker exec`, `kubectl exec`, `wsl`… Opening a remote server's URL forwards its port to your machine."
- "Opens instantly from the menu bar, the tray, or a global shortcut… 40 color themes." CLI/TUI: "`everyport` opens the same server list as a terminal UI; `everyport list --json` and `everyport watch --jsonl`."
- Windows install: `irm https://everyport.dev/install.ps1 | iex` (per-user, no admin); "`.msi` or `-setup.exe` from Releases… Windows builds are not signed yet, so SmartScreen asks you to confirm when you install the .msi by hand." macOS 13+, Linux x86_64 (AppImage/.deb/.rpm); Linux arm64 = CLI only.
