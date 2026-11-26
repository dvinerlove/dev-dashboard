# Dev Dashboard v0.9.1 — Self-update and discovery

## Highlights

- **Self-update** — the app can now upgrade itself: Settings → check for updates → one click downloads the latest release, swaps the exe, and restarts. winget/scoop installs defer to their package manager. *(Note: update checks are manual — there is no passive notification yet.)*
- **Service candidates** — the dashboard detects running processes that look like dev services but are not managed yet, and offers to adopt them
- **Free-port finder and kill-port** — pick an unused port or free an occupied one, right from the Ports view header
- **Instant project/service strips** — scan results are cached in localStorage, so strips render immediately after an app restart and refresh in the background; loading shimmer actually shows during cold scans
- **UI rework** — decluttered topbar (app icon, no duplicate buttons), clean sidebar meta-zone, contextual add-buttons, six themes reordered with the paper family first, new hexagonal app icon that adapts to the theme
- **Codebase fully in English** — comments and docstrings translated; Russian lives only in `locales/ru.json`
- **Remote probe history** persisted in SQLite; expanded test coverage (self-update mechanics, scan compose, credential cleanup, autorun)

## Install / upgrade

Download **`DevDashboard-windows-x64.zip`** below, unzip anywhere, run `DevDashboard.exe`. Already on v0.9.0? Settings → check for updates — this release is the first one the self-updater can actually deliver.

**SmartScreen:** the exe is unsigned, so Windows will warn — click **More info → Run anyway**.

**Checksums:** verify against `DevDashboard-windows-x64.zip.sha256`:

```powershell
Get-FileHash DevDashboard-windows-x64.zip -Algorithm SHA256
```

## Known limitations

- **Windows only, for now.** A POSIX code path exists and passes CI on macOS and Linux, but it has never been run on a real machine.
- **Unsigned exe** — SmartScreen warning on first run is expected.
- **Update checks are manual** — no background notification when a new release appears.
- **English and Russian UI only.**

Full changelog: [CHANGELOG.md](../CHANGELOG.md). Report issues at [github.com/dvinerlove/dev-dashboard/issues](https://github.com/dvinerlove/dev-dashboard/issues).
