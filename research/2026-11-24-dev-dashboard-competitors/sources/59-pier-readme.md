# 59 — pier (StepanBlaha) README

- URL: https://github.com/StepanBlaha/pier (raw README, main); site stepanblaha.github.io/pier
- Title: pier — See what's running on localhost and which project it belongs to
- Publisher: GitHub / Štěpán Bláha (repo author). macOS menu bar app + CLI, Swift 6, brew
- Tier: L1 | Source class: vendor-authored | Fetched: 2026-11-24

## Key quotes
- "For each one, it tells you **which project** it belongs to (from the process's working directory), the **framework** ..., the **page title and favicon**, the **git branch**, whether it's **healthy**, whether it's **reachable from your LAN**, and **what started it** (VS Code, iTerm, tmux, Claude Code)."
- How it works: "**Discovery** uses native `libproc` calls (no shelling out to `lsof`) and scans every port in about 0.1s."
- "**Identification** combines the process's working directory, its arguments, `package.json`, `.git/HEAD`, well-known infrastructure ports, the Docker Engine API and a quick HTTP probe for the page title and favicon."
- "`pier run` | Runs your `package.json` `dev` script under pier."
- "Stacks from `pier.yml` start and stop with one button" — multi-service definition convention.
- "`pier stale` | Finds forgotten dev servers: long uptime, idle, no open connections"
