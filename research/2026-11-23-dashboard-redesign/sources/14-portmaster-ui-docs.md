# Source 14 — Portmaster User Interface docs

- URL: https://docs.safing.io/portmaster/architecture/user-interface
  (requested https://docs.safing.io/portmaster/app/user-interface → 404, redirected)
- Title: "User Interface - Safing Docs"
- Publisher: Safing docs
- Tier: L1 · source_class: official-docs
- Fetched: 2026-11-23 (via r.jina.ai)

## Key verbatim quotes

1. "The Portmaster UI is the main way you interact with the Portmaster Application. It connects to the Portmaster Core Service, which is running in the background." — app = thin GUI over always-on daemon (same core pattern as localhost/PortDoc).
2. "The Portmaster UI has no background activity. Instead, background interaction is being take care of the Notifier." — tray/notifier owns background presence.
3. "we chose to go with Electron. We are not happy about Electron and only see it as a mid-term solution" — vendor's own regret re: Electron UI; a native toolkit (PyQt6) is fine.

Note: page is thin ("Extended documentation of the Portmaster UI are yet to be written") — limited anatomy detail available.
