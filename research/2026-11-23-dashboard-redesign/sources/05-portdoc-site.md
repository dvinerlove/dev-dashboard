# Source 05 — PortDoc landing page

- URL: https://portdoc.dev/
- Title: "PortDoc | Your local dev servers, under control"
- Publisher: portdoc.dev (vendor, Brad Traversy / Traversy Media)
- Tier: L2 · source_class: vendor-authored
- Fetched: 2026-11-23 (via r.jina.ai)

## Key verbatim quotes

1. "PortDoc shows what is running, which project owns each port, and what you can safely stop. No more digging through old terminal tabs or guessing what took port 3000."
2. "Look up any port and see the process, PID, project, command, age, and exposure in one place." — row data model.
3. "Vite, Next.js, Express, Docker, databases, and background services are grouped under the repo that owns them." — project-grouped cards, e.g. "startdev 4 running".
4. Sample row: "Next.js localhost:3000 / node · PID 18422 · next dev / Open ↗ □ Stop ● running 2h" — primary actions Open + Stop with running state + age on the same line.
5. "Local, LAN-visible, Docker, and unknown services are clearly labeled so you never mistake a public bind for localhost." — exposure labeling as a safety feature.
6. "Stop stale services with confirmation and process checks. PortDoc protects itself and verifies that the port was released."
7. "open a live view of the services on your machine … The server binds `127.0.0.1` only" (from site + README); background mode uses "systemd user service / LaunchAgent / Task Scheduler" per platform — autostart via native OS manager.
