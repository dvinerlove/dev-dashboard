# Homeport — https://gethomeport.app/
- Title: "Homeport: every local app, one home"
- Publisher: Hapi Creative (gethomeport.app)
- Tier: L2 (vendor-authored product site)
- Fetched: 2026-11-24
- source_class: vendor-authored

## Key quotes
- "The local dev server manager for Mac — Every local app. One home. Run open-source apps from GitHub and your own projects, with every dev server, worker and database in one window." "Free for 1 app · macOS 26 or later"
- Works with "Node.js, Python, Ruby on Rails, Go, Rust, Java, Kotlin, Laravel, Phoenix, .NET, Docker Compose, Procfile".
- "Apps run in Homeport's sandbox… Apps that run in Docker, and tools installed with Homebrew, are outside it." GitHub-app installs reviewed before running: "Homeport runs a project's commands only after you review and approve its config, and asks again when the config changes."
- Health/logs: "A terminal per service: search, timestamps, typed input and ⌃C; HTTP, TCP and command health checks; Automatic restarts, waiting longer between tries; Crash alerts, once per incident."
- Local HTTPS: "https://shop.test, not localhost:3000… Setup trusts a local certificate that can only sign .test names, on this Mac only." Domains served on port 7443.
- Env/doctor: "Checks Node, Python and Ruby versions and missing .env keys before a start, and on request finds outdated packages and known vulnerabilities. Also from the terminal: `homeport doctor`."
- Config: "`homeport.yaml` describes how your app runs… services with `command`, `ports`, `health` (http/tcp/shell with interval + start_period), `depends_on`, `restart` policy with `max_retries` and `backoff { initial, max }`, `stop { signal, timeout }`. Personal overrides in `homeport.local.yaml`. Or let Homeport detect your stack, Compose files included, and write the config for you."
- Extras: "Port conflicts — warns before a start when another process already holds a declared port"; AI assistant (Apple on-device or own Claude/OpenAI key, "Environment values in your config are always hidden, and likely secrets in logs are masked"); "git worktrees… on its own ports and domain"; "Open in Cursor, VS Code, Zed or Xcode"; menu bar control.
- Price/update: "Free — $0 Forever, not a trial — 1 app… Every feature; Updates." "Pro — $9.99 one-time Early-bird price · final price $19.99, 1 Mac per license… every update, for life." "Homeport checks for updates and offers to install them. Each update is verified with Homeport's signing key."
- Closed source (license key, paid Pro; no OSS claim on page).
