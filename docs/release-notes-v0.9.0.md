# Dev Dashboard v0.9.0 — Initial public release

First public release of Dev Dashboard, a local control panel for dev services on Windows. It shows which of your services are up, restarts the ones that crash, tells you which process owns which port, and gives AI agents the same view through MCP. No telemetry, no account — everything stays on your machine.

## Highlights

- **Service lifecycle** — start/stop/restart arbitrary processes; stop kills the whole process tree via Windows Job Objects (`killpg` on POSIX)
- **Crash recovery that backs off** — auto-restart with 2→5→10→20 s delays plus a circuit breaker that flags a `crash_loop` after 5 crashes per minute
- **Ordered startup** — `depends_on` waits for a health URL, a TCP port, or a stable process before starting dependents
- **Ports inventory** — every TCP listener attributed to your services, with LAN-exposure flags
- **Remote monitors** — HTTP, TCP, and Docker probes
- **Env editor** — per-service env overrides; secrets masked in API responses
- **Issues feed + SQLite history** — crashes, port conflicts, dep timeouts, and log errors, deduplicated and persisted
- **MCP server** — zero-dependency stdio server (7 tools) so AI agents can list services, read logs, and restart things
- **Desktop integration** — system tray, launch-at-login, single instance, RU/EN UI, six themes
- **`--web` mode** — run headless, use the same UI in a browser
- **Portable mode** — put the config files next to the exe and it becomes self-contained

## Install

Download **`DevDashboard-windows-x64.zip`** below, unzip anywhere, run `DevDashboard.exe`. On first launch an onboarding dialog helps you add your first projects.

**SmartScreen:** the exe is unsigned, so Windows will warn — click **More info → Run anyway**. If you'd rather not trust the binary, building from source takes a few minutes (Python 3.10+, Node 20+; see the README).

**Checksums:** verify the download against `DevDashboard-windows-x64.zip.sha256`:

```powershell
Get-FileHash DevDashboard-windows-x64.zip -Algorithm SHA256
```

## Known limitations

- **Windows only, for now.** A POSIX code path exists and passes CI on macOS and Linux, but it has never been run on a real machine. `--web` mode should work there — please report what breaks.
- **Unsigned exe** — SmartScreen warning on first run is expected (see above).
- **No auto-update** — check Releases for new versions. winget and scoop manifests are prepared in `packaging/`, ready for submission.
- **English and Russian UI only.**

Full changelog: [CHANGELOG.md](../CHANGELOG.md). Report issues at [github.com/dvinerlove/dev-dashboard/issues](https://github.com/dvinerlove/dev-dashboard/issues).
