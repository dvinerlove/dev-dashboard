# Dev Dashboard MCP server

A lightweight stdio MCP server on top of the local HTTP API (`127.0.0.1:4850`).
No external dependencies — Python stdlib only.

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
| `get_service_logs(name, lines=100)` | Last N log lines |
| `get_issues` | Active issues (crash, port, deps_timeout, crash_loop, log_error) |
| `get_runs(name)` | Run history |
| `start_service(name)` / `stop_service(name)` / `restart_service(name)` | Service control |

## Smoke test

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | python mcp_server.py
```
