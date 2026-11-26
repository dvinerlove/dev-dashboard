# Changelog

## [0.9.1] — 2026-11-26

- Self-update: one-click upgrade from Settings (git/zip channel; winget/scoop defer to their package managers)
- Service candidates: detect unmanaged running processes that look like dev services
- Free-port finder and kill-port moved into the Ports view header
- localStorage-backed cache for strips/views: instant render after restart, loading shimmer fixed on cold scans
- UI rework: decluttered topbar with theme-adaptive app icon, clean sidebar meta-zone, contextual add-buttons
- Themes reordered (paper family first) and renamed; new hexagonal app icon
- Codebase comments/docstrings fully in English; remote probe history in SQLite
- Tests: self-update mechanics, scan compose, credential cleanup, autorun

## [0.9.0] — 2026-11-24

Initial public release.

- React 19 + Tailwind v4 UI on pywebview (Edge WebView2), `--web` headless mode
- Service lifecycle with Windows Job Objects process-tree kill (POSIX `killpg` fallback)
- Auto-restart with 2→5→10→20s backoff and crash-loop circuit breaker
- `depends_on` startup ordering with health_url/TCP readiness and 15s timeout
- Ports inventory with service attribution and LAN-exposure flag
- Per-service env editor with secret masking
- Remote monitors: HTTP/TCP probes with keyword/token auth, TCP, Docker
- Issues feed, run/issue history persisted in SQLite (WAL)
- Autorun manager, system tray, themes, RU/EN i18n
- MCP stdio server for AI agents (7 tools)
- Windows exe build via PyInstaller
