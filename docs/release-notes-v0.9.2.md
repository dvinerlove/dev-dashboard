# Dev Dashboard v0.9.2 — Passive update notifications

## Highlights

- **Update notifications** — the app now checks for new releases at startup and shows a download icon in the topbar when one is available; one click confirms and self-installs. No more manual polling in Settings (the manual check is still there).
- **No more phantom crashes after reboot** — projects no longer show "crashed" at every boot: only a process death the dashboard actually witnessed counts as a crash. A pid persisted from a previous session that is simply gone is just "not running".
- **Externally started dev servers are adopted** — a process whose working directory sits inside the project tree now counts as the project's process, even when its exe/cmdline carry no project path (`node src\index.ts` started by hand from a terminal). No configuration needed.
- **Inspector opens on row click** — every service/project/autorun row opens the detail inspector directly.
- **WebView2 self-healing** — a silent renderer init failure is detected by a watchdog and recovered instead of showing a dead window.
- **Self-update hardening** — relaunch waits past the WebView2 lock window, copy retries, start verification.

## Install / upgrade

Download **`DevDashboard-windows-x64.zip`** below, unzip anywhere, run `DevDashboard.exe`. Already on v0.9.1? This is the first release your app will *notify* you about — watch the topbar.

**SmartScreen:** the exe is unsigned, so Windows will warn — click **More info → Run anyway**.

**Checksums:** verify against `DevDashboard-windows-x64.zip.sha256`:

```powershell
Get-FileHash DevDashboard-windows-x64.zip -Algorithm SHA256
```

## Known limitations

- **Windows only, for now.** A POSIX code path exists and passes CI on macOS and Linux, but it has never been run on a real machine.
- **Unsigned exe** — SmartScreen warning on first run is expected.
