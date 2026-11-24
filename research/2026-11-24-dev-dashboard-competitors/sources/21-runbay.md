# RunBay — https://github.com/Tharana/runbay
- Title: "Tharana/runbay" README + repo metadata
- Publisher: GitHub / Tharana
- Tier: L1 (project's own docs)
- Fetched: 2026-11-24 (GitHub REST API)
- source_class: independent-primary
- Repo meta: JavaScript (Electron-style Node app; `npm start`/`npm run dist` builds installer), 1 star, MIT, pushed 2026-11-02.

## Key quotes (README)
- "A free, open-source **local dev server manager for Windows**. Start, stop and monitor your frontend, backend, database and ngrok tunnel with one click, with live logs, health checks and auto-restart."
- "Auto-detect — Next.js, NestJS, Node, Vite, PHP/Laravel, Django, FastAPI, Flask, Go, .NET, Spring Boot, Docker Compose and monorepos."
- "One-click start — Run all / Stop all / Restart, ordered start with 'wait until ready', auto-start on launch." "Self-healing — Auto-restart on crash, one-click fix for 'port already in use'."
- "Health and stats — Responding badge, CPU and memory sparklines, uptime"; "Live logs — Search, copy, export, and a separate Errors tab with a count badge."
- Env: "Env profiles — Switch between dev and staging variables per app"; ".env editor — Edit and compare .env files with secrets masked, and warnings for keys missing from .env.example."
- Dependencies/order: "Start order — Say which service waits for which, drawn as a diagram."
- "Language versions — Each app runs with the Node / Python / PHP version its `.nvmrc`, `.python-version` or `composer.json` asks for, without switching anything globally."
- "Port map — Every port in use on the PC, who owns it, which of your apps it blocks, and a kill button." "Local domains — Open apps at `https://myshop.test` with an auto-generated trusted certificate."
- "ngrok built in — Installs itself, shows your public URL, request inspector, QR code for your phone, webhook URL copier (Stripe, Dodo, GitHub)."
- AI: "'Explain this error' — Click an error… Claude explains the likely cause and fix (you review the redacted text first; bring your own API key)."
- "Git and packages — Branch and status per app, Pull button, Install / Build buttons, warning when package.json changed"; "Workspaces — Save a set of apps as a stack"; "Quick launcher — Global hotkey (Ctrl+Alt+R)"; "Alerts and history — Notifications for high CPU / memory or silent services, plus a crash and downtime timeline."
- CLI: "`runbay start myshop --wait`… exit codes… In CI: `runbay start myshop --wait --timeout 180 && npm test`."
- Install: `RunBay-Setup-x.y.z.exe` or portable exe; "The installer is not code-signed yet." Platform: "Windows 10 and 11 today. Contributions for macOS and Linux are welcome." Update: manual "Check for updates" button fetching a version file from the repo.
