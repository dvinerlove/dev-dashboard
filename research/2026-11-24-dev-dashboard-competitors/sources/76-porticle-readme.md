# Source 76 — AmoonPod/porticle README

- URL: https://github.com/AmoonPod/porticle
- Publisher: GitHub (repo README — vendor-authored; cited for feature-set convergence + Windows support)
- Tier: L4
- Fetch date: 2026-11-24 (raw README, full)

## Key verbatim quotes

- "A fast, open-source menu bar and system tray app for seeing—and stopping—what is using your local ports. macOS 13+ · Windows 10+ · TCP + UDP · IPv4 + IPv6"
- "Porticle answers one question immediately: **what owns this port?**"
- Feature list (what this category converged on): "Stops a process tree gracefully, then force-stops it after a configurable delay if needed. Revalidates process identity before termination to avoid PID-reuse races. Detects ports that reopen under a supervisor or a replacement process."
- "Watches ports even while they are free and notifies when their owner changes." — watch-for-takeover notification ask.
- "Recognizes common local tools and services such as Next.js, Vite, Astro, Django, Rails, PostgreSQL, Redis, MySQL, MongoDB, Docker, LocalStack, Storybook, Jupyter, and Ollama."
- "Signed and notarized macOS builds and signed Windows installers" — signing on both OSes.

## Takeaway

Cross-platform (mac+Windows) tray tool whose hard problems are exactly ours: PID-reuse races, supervisor respawn detection, safe tree-kill.
