# Dev Dashboard MCP server

A stdio MCP server on top of the local HTTP API (`127.0.0.1:4850`).
Capabilities: tools, resources, prompts.
The server itself is Python stdlib only — no pip install needed; the `api.port`
auto-detect additionally needs the repo checkout with its deps installed.

The dashboard must be running (`python dashboard.py` or `DevDashboard.exe`).

## Setup

**Cursor** (`~/.cursor/mcp.json` or `.cursor/mcp.json` in a project):

```json
{
  "mcpServers": {
    "dev-dashboard": {
      "command": "python",
      "args": ["C:\\path\\to\\dev-dashboard\\mcp_server.py"]
    }
  }
}
```

**Cline** — same: `command=python`, `args=["C:\\path\\to\\dev-dashboard\\mcp_server.py"]`,
stdio transport. **Codex** uses TOML (`[mcp_servers.*]`) instead of the JSON above.

> The API port defaults to `4850`. If the dashboard fell back to another port,
> the server picks it up from the `api.port` marker automatically; otherwise
> set `DEVDASH_PORT` in the connection's `env`:
> `"env": {"DEVDASH_PORT": "4851"}`.

## Tools

| Tool | What it does |
|---|---|
| `list_services` | Services and projects: state, port/IP, metrics |
| `list_projects` | Registered projects: cmd, cwd, url, running/pid |
| `list_ports` | TCP listeners with service/project attribution |
| `get_service_logs(name, lines=100)` | Last N log lines |
| `get_service_env(name)` | Env overrides of a service (secrets masked) |
| `get_issues` | Active issues (crash, port, deps_timeout, crash_loop, log_error) |
| `get_runs(name)` | Run history |
| `get_settings` | Dashboard settings (ports, scan roots, autorun, lang) |
| `start_service(name)` / `stop_service(name)` / `restart_service(name)` | Service control |
| `start_project(name)` / `stop_project(name)` / `restart_project(name)` | Project control (launches/kills the real process) |
| `kill_port(port)` | Free a TCP port by killing its listener(s) |
| `scan_projects` | Scan configured roots for new project dirs (`found` candidates) |
| `add_service(name, …)` | Register a service: `start`/`cmd`, `cwd`, `ports` (list or CSV), `sub`, `autorestart`, `monitor_only`, `depends_on`, `health_url`, `mem_limit_mb`, `watch`, `restart_every_min`, `env`, `env_profiles` |
| `update_service(name, …)` | Patch a service — current spec is fetched, fields merged, full spec re-saved (the save endpoint wipes known keys missing from the payload) |
| `delete_service(name)` | Delete a service (stops it first if running) |
| `set_settings(settings)` | Update settings — merged with current, saved under lock server-side |
| `set_env_profile(name, profile="")` | Set active env profile (empty string clears) |
| `set_env_profiles(name, profiles)` | Replace the env profiles map of a service |

## Resources

| URI | Content |
|---|---|
| `dashboard://state` | Full `/api/state` JSON snapshot |
| `dashboard://issues` | `/api/issues` JSON |
| `dashboard://services/{name}/log` | Service log text (resource template) |

## Prompts

`prompts/list` exposes three ready-made briefs; `prompts/get` assembles a
single `user` message from live API data (state, spec, logs, issues) that
the client then sends to the model.

| Prompt | Args | Message content |
|---|---|---|
| `debug_service` | `name` | Service/project state + spec + last 80 log lines + runs + related issues, ending in a diagnose-and-fix request. Unknown name → list of valid names. |
| `health_summary` | — | Dashboard status, up/down counts, problem list, recent issues. |
| `free_port_restart` | `port` | Who holds the port (pid, cmd, dashboard owner if any), a suggested free port when `/api/free-port` exists, and a kill/restart plan. |

Example frame:

```json
{"jsonrpc":"2.0","id":3,"method":"prompts/get",
 "params":{"name":"debug_service","arguments":{"name":"OmniRoute"}}}
```

## Smoke test

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | python mcp_server.py
```
