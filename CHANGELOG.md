# Changelog

## [0.9.0] — 2026-11-24

Initial public release.

- React 19 + Tailwind v4 UI on pywebview (Edge WebView2), `--web` headless mode
- Service lifecycle with Windows Job Objects process-tree kill (POSIX `killpg` fallback)
- Auto-restart with 2→5→10→20s backoff and crash-loop circuit breaker
- `depends_on` startup ordering with health_url/TCP readiness and 15s timeout
- Ports inventory with service attribution and LAN-exposure flag
- Per-service env editor with secret masking
- Remote monitors: HTTP/TCP/Docker/Supabase probes, ZeroTier vendor probe
- Issues feed, run/issue history persisted in SQLite (WAL)
- Autorun manager, system tray, themes, RU/EN i18n
- MCP stdio server for AI agents (7 tools)
- Windows exe build via PyInstaller
