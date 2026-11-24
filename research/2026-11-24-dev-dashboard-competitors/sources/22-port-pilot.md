# Port Pilot — https://github.com/Nimba-Solutions/Port-Pilot
- Title: "Nimba-Solutions/Port-Pilot" README + repo metadata
- Publisher: GitHub / Nimba Solutions (Cloud Nimbus LLC)
- Tier: L1 (project's own docs)
- Fetched: 2026-11-24 (GitHub REST API)
- source_class: independent-primary
- Repo meta: JavaScript, 0 stars, license BSL 1.1 (repo shows NOASSERTION), pushed 2026-03-13.

## Key quotes (README)
- "**Free & open-source visual localhost port manager for Windows.** See every listening port, what process owns it, and kill it with one click."
- Features: "Live port table — all listening TCP ports with process name, PID, and address; One-click kill; Open in browser; Smart hints — Auto-detects common dev stacks (React, Vite, Django, PostgreSQL, etc.); Pin ports; Notes — Label ports with custom notes; Search & filter; Dev filter — Show only common development ports; Auto-refresh — Configurable refresh interval (default 3s); System tray; Copy URL."
- Distribution: "Grab the latest portable `.exe` from Releases. No installation required — just run it." Requires Windows 10/11. Build: `npm install && npm run build` → portable exe in `dist/` (Electron-style JS app).
- Detection method: "Port Pilot queries Windows `Get-NetTCPConnection` via PowerShell to enumerate listening TCP connections, then resolves owning process info via `Get-Process`. Everything runs locally — no network calls, no telemetry."
- License: "BSL 1.1 — Converts to Apache 2.0 after four years per release. Author: Cloud Nimbus LLC."
