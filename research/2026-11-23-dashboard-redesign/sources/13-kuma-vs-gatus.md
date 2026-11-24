# Source 13 — "Uptime Kuma vs Gatus" comparison (UI anatomy + complaints)

- URL: https://www.bitdoze.com/uptime-kuma-vs-gatus/
- Title: "Uptime Kuma vs Gatus: Which Self-Hosted Monitor Wins?"
- Publisher: bitdoze.com (independent blog/analysis)
- Tier: L3 · source_class: article (independent-secondary)
- Fetched: 2026-11-23 (via r.jina.ai)

## Key verbatim quotes

1. Screenshot caption: "Uptime Kuma dashboard: monitor list on the left, a Google DNS monitor detail with heartbeat bar, ping stats and a response-time graph on the right" — two-pane master-detail layout.
2. "Kuma is UI-first. You click monitors into existence, they live in SQLite, and the dashboard streams live updates over WebSocket." — live push UI, no config file.
3. "The live UI rides a long-lived Socket.IO WebSocket. Proxies that cut idle connections make the dashboard look frozen: the page loads, then nothing updates." — common complaint/fragility.
4. "Heartbeat history makes Kuma's SQLite file grow without bound. Users on r/selfhosted report files of several hundred MB and a sluggish monitor list on old instances." — performance complaint at scale.
5. "v2 removed JSON backup/restore, so copying the `data/` directory is the only supported method."
6. Gatus comparison for contrast: "a grid of endpoint cards with Healthy or Unhealthy badges, heartbeat bars and response times per endpoint" — card-grid alternative layout.
