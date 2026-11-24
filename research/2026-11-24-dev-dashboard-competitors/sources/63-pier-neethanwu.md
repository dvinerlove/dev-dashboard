# 63 — pier (neethanwu) README — alternate implementation

- URL: https://github.com/neethanwu/pier (raw README, main)
- Title: Pier — macOS menu bar app that keeps track of every dev server
- Publisher: GitHub / neethanwu (repo author). Swift, macOS 14+, MIT, ~7 stars
- Tier: L1 | Source class: vendor-authored | Fetched: 2026-11-24

## Key quotes
- "Pier uses `lsof` to detect listening TCP ports, then resolves each to a process → working directory → project name → git branch. It polls every 2 seconds and uses no background daemons or privileged helpers."
- "Detected servers: node, next, vite, nuxt, ruby, rails, puma, python, uvicorn, flask, django, go, cargo, deno, bun, php, java, and more." — process-name/argv based detection (Sources/Pier/Services: PortScanner.swift = lsof, ProcessResolver.swift = PID → cwd, GitBranchReader.swift = .git/HEAD parsing).
