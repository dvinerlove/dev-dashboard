# Source 79 — Raycast guide: "Find and Kill the Process Using a Port on Mac" (Port Manager extension)

- URL: https://www.raycast.com/guides/how-to-kill-a-process-on-a-port-on-mac
- Publisher: Raycast (official guides — L2/L3; extension stats are first-party numbers)
- Tier: L3
- Fetch date: 2026-11-24 (full page via r.jina.ai)

## Key verbatim quotes

- "Port Manager has more than 65,000 installs. It lists every process listening on a TCP port and lets you kill it from the same list. It's free, open source, and **works on Windows too**." — numeric demand proof; a port-killer is among the most-installed Raycast dev extensions, and it ships Windows support.
- Feature asks baked in: "**Named Ports**: give ports a label, like `3000 (Next.js)`" (user labels); "**Open Ports in Menu Bar**"; "It checks the process actually died ... If it ignores the signal, you get a Force Kill button"; "**Kill Parent** (⌥⌘P) stops the process that started the listener. That's the one you want when `nodemon` or a watcher keeps bringing the server back." (kill-the-parent ask — respawn problem)
- Exposure coloring: "Green means only your Mac can reach it, orange means anything on your network can ... a nice way to spot a dev server you accidentally exposed on café Wi-Fi." (LAN-exposure warning again)

## Takeaway

65k installs on one launcher extension alone quantifies "what's on this port / kill it" demand; features repeated: labels, menubar list, verified-kill, kill-parent for watchers, exposure tagging.
