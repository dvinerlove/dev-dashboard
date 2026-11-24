# Dev Dashboard

A control panel for your local dev environment — services, projects, ports, and monitors in one dark, dense window.

[![Release](https://img.shields.io/github/v/release/OWNER/dev-dashboard)](https://github.com/OWNER/dev-dashboard/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%2FmacOS%20(web)-lightgrey)](#platform-support)

<!-- screenshot: docs/screenshot.png -->

## Features

- **Service lifecycle** — start/stop/restart with process-tree kill via Windows Job Objects (`CREATE_SUSPENDED` → assign → resume), `killpg` on POSIX
- **Auto-restart** — exponential backoff (2→5→10→20s) plus a circuit breaker that flags `crash_loop` after 5 crashes/minute
- **`depends_on` ordering** — wait for a dependency's `health_url` (HTTP), first port (TCP), or a 0.5s alive check before starting
- **Ports inventory** — every TCP listener on the box, attributed to your services, with LAN-exposure flag and "mine/hidden" filtering
- **Env editor** — per-service env overrides in the UI; secrets (`TOKEN|SECRET|KEY|PASSWORD|AUTH`) are masked in the API
- **Remote monitors** — HTTP/TCP/Docker/Supabase probes for services you don't run locally
- **Issues feed** — crashes, port conflicts, dep timeouts, log errors, deduplicated
- **SQLite history** — runs and issues survive restarts (WAL mode)
- **MCP server** — stdio JSON-RPC proxy so AI agents (Cursor/Cline/Codex) can list services, read logs, and restart things — see [README_MCP.md](README_MCP.md)
- **System tray** — close-to-tray, autostart entries manager
- **Themes + RU/EN i18n**
- **`--web` mode** — run headless and use the UI in a browser (`python dashboard.py --web`)

## Install

### Release exe (Windows)

Download `DevDashboard-windows-x64.zip` from [Releases](https://github.com/OWNER/dev-dashboard/releases), unzip, run `DevDashboard.exe`.

> **SmartScreen:** the build is unsigned, so Windows will warn. Click **More info → Run anyway**. Build it yourself from source if you prefer.

### From source

Requirements: Python 3.10+, Node 20+, Microsoft Edge WebView2 (preinstalled on Windows 10/11).

```bash
pip install -r requirements.txt
cd frontend && npm ci && npm run build && cd ..
python dashboard.py
```

Headless / remote:

```bash
python dashboard.py --web   # UI + API at http://127.0.0.1:4850
```

## Configuration

Config files live in the data directory and are plain JSON — edit by hand or via the UI. Deleting a service in the UI removes it from `services_config.json`.

### `services_config.json` — array of service specs

| Field | Type | Meaning |
|---|---|---|
| `name` | string | **Required.** Display name, also the primary key |
| `sub` | string | Secondary label shown under the name |
| `ports` | int[] | Ports the service listens on; `ports[0]` drives the chip and the TCP readiness check |
| `proc` | string | Process name to match when probing (e.g. `syncthing.exe`) |
| `match` | string | Substring match against the process command line |
| `url` | string | "Open" link for the service |
| `start` | string | Command used to start the service |
| `cwd` | string | Working directory for `start` |
| `env` | object | Env var overrides for the started process |
| `env_key` / `env_file` | string | Read a secret from an `.env` file (`env_file`, defaults to `<data dir>/.env`) — used for monitor auth headers and editable via the env editor |
| `autorestart` | bool | Restart on unexpected exit, with backoff + circuit breaker |
| `monitor_only` | bool | Probe the process but never start/stop it |
| `depends_on` | string[] | Service names that must be healthy first (see below) |
| `health_url` | string | HTTP readiness URL for `depends_on` (2xx–3xx = ready); without it falls back to first port, then "alive 0.5s" |
| `type` | `http` \| `tcp` \| `docker` | Remote monitor — no local process; probe a URL, `host`+`port`, or `container` name via `docker ps` |
| `host`, `port` | string, int | For `type: "tcp"` monitors |
| `container` | string | Container name for `type: "docker"` |
| `keyword` | string | For `type: "http"`: body must contain this, else "dead" |
| `interval` | int | Remote probe period in seconds (default: docker 15, supabase 60, other 30) |
| `zerotier` | bool | Vendor probe: ZeroTier via its local API |
| `zt_token` | string | ZeroTier authtoken override (default: read from the service's authtoken file) |
| `supabase` | bool | HTTP probe variant: sends `apikey` + `Authorization: Bearer` from `env_key`/`env_file` |
| `path` | string | Project path — enables the "open folder" affordance |
| `note` | string | Shown when a docker monitor finds no container |

### `projects_config.json` — array of project specs

| Field | Type | Meaning |
|---|---|---|
| `name` | string | **Required.** Display name |
| `cmd` | string | Command run via the shell (e.g. `npm run dev`) |
| `cwd` | string | Working directory |
| `url` | string | Optional "open" link |
| `sub`, `ports`, `env`, `autorestart` | — | Same semantics as services |

### `settings.json`

| Key | Default | Meaning |
|---|---|---|
| `api_port` | `4850` | Local HTTP API port; if busy, the next free port (up to +9) is used |
| `probe_interval` | `4` | Local probe loop period, seconds |
| `dep_timeout` | `15` | How long `depends_on` waits before cancelling a start (`deps_timeout` issue) |
| `backoff` | `[2, 5, 10, 20]` | Auto-restart delays, seconds (reset after 60s uptime) |
| `scan_roots` | `[]` | Folders scanned for projects; `[]` = auto-detect |
| `port_mine` | `[]` | Process names marked as "mine" in the ports view |
| `port_hidden` | `[]` | Process names hidden from the ports view |
| `lang` | `"auto"` | `auto` = OS language (non-Russian falls back to English) |

### Data location

| Case | Path |
|---|---|
| Windows | `%LOCALAPPDATA%\DevDashboard` |
| Linux | `~/.config/dev-dashboard` (or `$XDG_CONFIG_HOME/dev-dashboard`) |
| macOS | `~/Library/Application Support/DevDashboard` |
| Portable | If `services_config.json`/`projects_config.json`/`settings.json`/`state.db` already exists next to the exe/script, that folder is used |
| Override | `DEVDASH_DATA_DIR` env var always wins |

Secrets are never written to `state.db`.

## MCP server

`mcp_server.py` is a zero-dependency stdio MCP server that proxies the local HTTP API — lets AI agents see service state, logs, issues, and start/stop services. Setup: [README_MCP.md](README_MCP.md).

## Development

```bash
cd frontend && npm ci && npm run build   # tsc -b + vite build → dist/
python test_upgrades.py                  # core tests (Job objects, backoff, deps, parser, env)
python _t/i18n_check.py                  # i18n coverage check
cd frontend && npx tsc --noEmit          # frontend typecheck
pyinstaller DevDashboard.spec            # build the exe
```

Backend logic lives in `backend.py` (Qt/web-free), the API + probe loop in `core.py`, platform branches in `platform_impl.py`. See `AGENTS.md` for the architecture notes.

## Platform support

| Platform | Status |
|---|---|
| Windows 10/11 | Full — window, tray, Job Objects, autorun |
| Linux | Experimental — `--web` mode |
| macOS | Experimental — `--web` mode |

## Privacy

No telemetry, no analytics, no network calls except the probes you configure. The API binds to `127.0.0.1` only.

## License

[MIT](LICENSE)
