# Source 07 — /agents (MCP server for coding agents)

- URL: https://www.getlocalhost.app/agents
- Title: "localhost app's MCP server for Claude Code, Cursor and Codex"
- Publisher: getlocalhost.app — fetched via r.jina.ai, 2026-11-24
- Tier: L2 (vendor marketing/docs page) | source_class: vendor-authored | cluster: C1

## Key quotes

- "The app and `localhost mcp` drive one localhost core in the background. A Service the agent starts is Running in the app… `status` says who started each one (`"startedBy": "app"` or `"agent"`)."
- "Fifteen tools: nine to run and inspect, six to add, edit and remove." Tools: list_projects, list_services, status, start_service, stop_service, start_project, stop_project, logs, ports, create_project, update_project, delete_project, create_service, update_service, delete_service.
- "A Service that is already running isn't started again… the agent neither starts a second copy nor stops it."
- "Stopping ends the whole process tree. When the agent disconnects, the Services it started stop, unless the app is open."
- "Results are JSON, failures carry a `kind` such as `portConflict` or `commandNotFound`… logs are bounded (200 lines by default, at most 2,000)."
- Safety: "It removes only with `confirm: true`, never touches a Project's folder, sets no Secrets… `localhost mcp --read-only` leaves the editing tools out."
- Install: "click **Connect** next to Claude Code, Cursor or Codex… writes a server named `localhost` in `~/.claude.json`, `~/.cursor/mcp.json` or `~/.codex/config.toml`" or `npx @getlocalhost/cli mcp install`.
