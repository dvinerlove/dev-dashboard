# PM2 Quick Start (official docs)

- url: https://pm2.keymetrics.io/docs/usage/quick-start/
- title: PM2 - Quick Start
- publisher: Keymetrics / PM2 docs (pm2.keymetrics.io)
- tier: L1 (official docs), source_class: vendor-authored
- fetched: 2026-11-24

## Key quotes

1. "PM2 is a daemon process manager that will help you manage and keep your application online. ... it is offered as a simple and intuitive CLI, installable via NPM." — PM2 is CLI-first, Node/npm ecosystem.

2. CLI options list includes: "--watch ... Watch and Restart app when files change", "--max-memory-restart 200M ... Set memory threshold for app reload", "--restart-delay <delay in ms> ... Delay between automatic restarts", "--no-autorestart ... Do not auto restart app", "--cron <cron_pattern> ... Specify cron for forced restart". — restart policy surface is broad (watch, memory cap, delay, cron).

3. Process control: "$ pm2 restart app_name / $ pm2 reload app_name / $ pm2 stop app_name / $ pm2 delete app_name" with "all" and "id" selectors.

4. Terminal dashboard: "$ pm2 monit" — "a realtime dashboard that fits directly into your terminal"; web dashboard via "$ pm2 plus" — "Web based dashboard, cross servers with diagnostic system" (pm2.io).

5. Ecosystem file per-app env: `module.exports = { apps : [{ name: "app", script: "./app.js", env: { NODE_ENV: "development" }, env_production: { NODE_ENV: "production" } }] }` — env declared in JS config, not .env files.

6. Boot persistence: "$ pm2 startup" — "generate an active startup script" for server boot; "$ pm2 save" — "to freeze a process list for automatic respawn".

7. Cluster mode: "PM2 includes an automatic load balancer ... $ pm2 start app.js -i max" — Node.js-oriented scaling.

8. Logs: "$ pm2 logs [--raw] ... Display all processes logs in streaming"; "pm2 flush ... Empty all log files".
