# Localhost Killer — https://github.com/system-conf/localhostkiller
- Title: "system-conf/localhostkiller" README + repo metadata
- Publisher: GitHub / system-conf
- Tier: L1 (project's own docs)
- Fetched: 2026-11-24 (GitHub REST API)
- source_class: independent-primary
- Repo meta: TypeScript (Electron 31 desktop + VS Code extension from same codebase), 1 star, MIT, pushed 2026-05-28.

## Key quotes (README)
- "Find and kill any process listening on a localhost port… lists every TCP port bound to `127.0.0.1`, `0.0.0.0`, `::1`, or `::` on your Windows machine, shows you which process owns each port (PID, executable name, command line), and lets you terminate them — individually or all at once." "works without admin rights."
- "Ships in two flavors from the same codebase: 1. VS Code Extension — a sidebar view and status bar indicator inside your editor. 2. Windows Desktop App (Electron) — a standalone window with a system-tray icon."
- Detection: "Scans every TCP listener on `127.0.0.1`, `0.0.0.0`, `::1`, `::` via `netstat -ano` and `Get-CimInstance Win32_Process` — no external dependencies."
- "System-process protection: PID 0/4 and `svchost.exe`, `lsass.exe`, `services.exe`, `wininit.exe`, `csrss.exe`, `smss.exe`, `winlogon.exe`, `spoolsv.exe`, `dwm.exe` are flagged as protected and require explicit confirmation."
- "Process-tree kill (`taskkill /F /T`) properly cleans up child workers, not just the parent." "Auto-refresh every 5 seconds"; "VS Code status bar indicator shows the current count of listening localhost ports."
- Ships table of default dev ports per stack (CRA/Next 3000, Vite 5173, Spring 8080, ASP.NET 5000/5001, Storybook 6006, Metro 8081…). Windows 10/11 only. Free, MIT.
