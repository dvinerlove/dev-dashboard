# Source 81 — Misc repo/issue evidence (portbook, Portkeeper, localhost, StackOverflow)

- URLs:
  - https://github.com/a-grasso/portbook/issues (list fetched via api.github.com)
  - https://github.com/MarcAparisiTFG/portkeeper (README via search-indexed content — partial; flagged)
  - https://github.com/marcellosso/localhost/issues (list fetched via api.github.com)
  - https://stackoverflow.com/questions/20239232/django-server-error-port-is-already-in-use (search-indexed stats — flagged L4)
- Tier: L4
- Fetch date: 2026-11-24

## a-grasso/portbook issues (full list fetched)

- #4 open: "**Feature Request: Docker Container scanning network and ports**" — a user wants the tool to see inside Docker/container port mappings, not just host listeners.
- #5 closed: "feat(cli): add --port to run a daemon beside an always-on one" — running alongside an existing instance.
- #1 closed: "Please add command line usage" — first issue ever was a user asking for a CLI surface alongside the web UI (multi-surface ask: web + CLI + TUI all shipped).

## marcellosso/localhost issues

- Author-filed Windows work confirms Windows is a supported target with real friction: #24/#28 "Windows: shared core over a named pipe, so the app and localhost mcp share Runs" — Windows needed a different IPC mechanism (named pipe vs unix socket).

## Portkeeper (vendor README, partial fetch — flagged)

- Pain framing: "If you work with several projects at once, and let AI coding agents start servers for you, your machine fills up with `localhost:3000`, `:5173`, `:8080`, Docker containers and forgotten dev servers."
- Feature asks it claims to serve: agent/IDE attribution by walking the process tree ("Claude Code, Codex, Cursor, Gemini CLI, Copilot, Windsurf, VS Code, JetBrains, Zed"), menu bar (macOS) + system tray (Windows), "Lock the ones a client depends on so nobody stops them by mistake" (protect/lock ask).

## StackOverflow #20239232 (stats from search index — flagged, not fully fetched)

- "Django Server Error: port is already in use" — score 297, ~494,623 views — the port-conflict question alone has ~half a million views; the pain predates and outscales every tool.
