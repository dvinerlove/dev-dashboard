# Source 75 — gabriel0139/windows-devbar README (DevBar for Windows)

- URL: https://github.com/gabriel0139/windows-devbar
- Publisher: GitHub (repo README — vendor-authored tool, cited as *evidence of Windows demand*)
- Tier: L4
- Fetch date: 2026-11-24 (raw README, full)

## Key verbatim quotes

- "The system tray, built for developers. System vitals, listening ports, Docker, WSL, winget, network diagnostics, automations — one click or one hotkey from anywhere."
- "**A Windows counterpart to [backquant/mac-devbar](https://github.com/backquant/mac-devbar), rebuilt natively in C#/WPF with the Windows-specific tools a dev box actually needs.**" — direct evidence someone saw a macOS-only tool and rebuilt it for Windows.
- "Most Windows monitors show you a graph and stop there. DevBar is built around *doing something about it*: the port list has a Kill button, the Docker row has restart, the hosts file has a toggle, and everything is reachable four ways — tray click, global hotkey (Ctrl+Alt+D), `devbar://` deep links, and the bundled CLI."
- Ports feature: "Every listening TCP and UDP socket — IPv4 **and** IPv6, so dev servers that bind `::` don't hide — with the owning process and PID. Dev-stack processes (node, vite, python, dotnet, docker, postgres…) rank above system listeners."
- Windows-specific scope that no mac tool covers: WSL integration, winget upgrades, Windows hosts-file toggle.

## Takeaway

Windows-side demand expressed as *building*: a mac-first category spawned a native Windows port with extra Windows-only surface (WSL, winget).
