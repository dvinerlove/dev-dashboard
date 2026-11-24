# Portlivo — https://portlivo.com/
- Title: "Portlivo — Mac menu bar app for local dev servers and ports"
- Publisher: Portlivo (indie, portlivo.com)
- Tier: L2 (vendor-authored product site)
- Fetched: 2026-11-24
- source_class: vendor-authored

## Key quotes
- "Portlivo lives in your menu bar and shows every local port — Vite, Laravel, Next.js, Docker, Postgres — with the project it belongs to."
- "Free for 7 days · macOS 14+" … "Try everything free for 7 days. After that it's a one-time license with free updates: $8.99 for one Mac right now, rising to $19.99 as early-bird spots sell out, or $39.99 for 3 Macs and $59.99 for 5 Macs."
- Detection: "Portlivo scans every two seconds and turns a wall of `lsof` output into named, grouped, live servers you can act on." "Every port shows its project folder, command, PID and uptime."
- Safety: "Portlivo re-checks the PID right before stopping anything, so a recycled PID can't take down the wrong app. It sends a polite SIGTERM first… Root-owned processes are left alone."
- Restarts: "Restart keeps the original arguments and environment, quotes and PORT=4000 included."
- "Docker aware — Shows container names instead of docker-proxy, and restarts or stops the container itself." "Homebrew & launchd — Postgres, Redis, MySQL… stop or restart them without brew services."
- "Watch ports — Get a banner when a watched server stops… and a red dot on the menu bar icon." "Network-exposed badge — Servers listening on your LAN are marked."
- "Live usage per server with a trend line" (CPU & memory).
- Comparison table claims vs lsof, Raycast Dev Servers, LocalhostBar, PortKiller — Portlivo uniquely lists "Live logs", "Fixes 'address already in use'… One click from the notification".
- Windows: "Want it on Windows or Linux? Join the waitlist… If enough people want it, I'll build it" — Mac-only today.
- Update model: "The only outbound connections are update checks, the license check with Dodo Payments… and, when you choose to share a server, the cloudflared or ngrok tunnel."
