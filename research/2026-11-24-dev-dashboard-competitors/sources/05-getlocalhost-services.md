# Source 05 — docs/services (service model, states, deps, stop)

- URL: https://www.getlocalhost.app/docs/services
- Title: "Services and states"
- Publisher: getlocalhost.app docs — fetched via r.jina.ai, 2026-11-24
- Tier: L1 | source_class: vendor-authored | cluster: C1

## Key quotes

- Command: "one command line, run in your login shell (`$SHELL -l -c "…"`), so your `PATH`, version managers and profile apply. Pipes, `&&` and `$VARIABLES` work as in a terminal. On Windows itself it runs in `cmd.exe`."
- "Run before": "a command line run first, in the same shell as the command… If it fails, or ends the shell with `exit`, the command doesn't run."
- Python env: "a virtualenv the Service runs in… `bin` folder (`Scripts` on Windows) goes first on `PATH` and `VIRTUAL_ENV` is set… localhost fills it in with the nearest `.venv`, `venv` or `virtualenv` in the working directory or a folder above it, up to the Project's, and says so in the editor: 'Using detected .venv'."
- Six states: "Stopped | Starting | Running | Stopping | Exited | Failed" — Running = "its Port accepts connections (or it has been alive ~1.5 s)".
- Dependencies: "Starting a Service starts its Dependencies first. **Start All** goes in dependency order, **Stop All** in reverse. Stopping or restarting one Service leaves the Services that depend on it alone. If a Dependency fails, the Services waiting for it don't start."
- Stop semantics: "Stopping sends Ctrl-C (SIGINT) to the Service's whole process group, then SIGTERM after 5 seconds, then SIGKILL… On Windows itself it sends Ctrl-Break, then ends every process the Service started."
- Crash recovery: "If localhost's background core ever crashes, the next launch finds the Services still running from it and asks whether to stop them."
- No auto-restart: "A running Service whose configuration changed shows 'Restart to apply'; nothing restarts on its own."
- "Manual": "Start All skips it, unless something being started depends on it."
