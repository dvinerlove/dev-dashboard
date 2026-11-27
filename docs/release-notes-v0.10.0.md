# Dev Dashboard v0.10.0 — Hardening pass

## Highlights

- **Self-update can no longer kill your processes** — the old retry path killed the whole process tree of anything named like the dashboard, and your autostarted projects live in that tree. The updater now kills by exact image name only, verifies the relaunched instance serves the dashboard API (not just any HTTP 200 on the port), keeps a backup of the old exe, and rolls back after three verified failures. Downloads are checked against the SHA256 published with each release.
- **Stopping a service no longer resurrects it** — a manual stop of an auto-restart service used to count as a crash and trigger an immediate restart, making the service impossible to stop without disabling auto-restart first.
- **Witnessed crashes now cover survivors** — a dev server that outlives a dashboard restart counts as witnessed, so when it later dies you get the crash event and the dead pill instead of silence. This closes the hole left in v0.9.2's phantom-crash fix.
- **Events open the affected service or project** — clicking one opens the inspector on the relevant tab (logs for log errors, history for crashes). Events from before this release have no recorded target and stay non-clickable.
- **No more double-starts** — starting a project whose process is already running outside the dashboard adopts that process instead of spawning a second one.
- **Safer process adoption** — npm/pnpm/yarn/bun shims are no longer mistaken for the project itself, nested projects resolve to the deepest matching directory, and evidence is ranked (working directory beats exe path beats a path mention in the command line).
- **Renderer crash recovery** — if the WebView2 renderer stops answering after the window has loaded, the dashboard restarts itself once.
- **Keyboard access** — service, project, autorun, port, and event rows are focusable and open with Enter/Space; selecting a deleted entry shows "This entry no longer exists" instead of a blank panel.
- **Self-update works in `--web` mode** — headless instances now exit cleanly so the updater can replace and relaunch them.

## Other fixes

- **Deleted services stay deleted** — deleting a service while its dependencies are starting no longer restarts it or emits events for it.
- **Background-process kills check pid reuse** — killing a portless dev process from the ports view verifies that its pid was not recycled between listing and clicking.
- **Duplicate names are rejected** — saving a service or project with a name already used in the same list fails instead of making name-based actions ambiguous.
- **Renames preserve runtime state** — renamed services keep restart backoff, circuit-breaker state, and log offsets; renamed projects keep running-process and crash state.
- **Corrupted history databases are rebuilt** — a corrupted `state.db` is quarantined and recreated instead of leaving run and issue history disabled.
- **CSRF protection pins the API port** — POSTs from browser pages on other localhost ports are rejected.
- **Autorun warnings open the right row** — clicking a "Needs attention" row for an autorun entry opens that entry even when a service has the same name.


## Install / upgrade

Download **`DevDashboard-windows-x64.zip`** below, unzip anywhere, run `DevDashboard.exe`. On v0.9.2, click the topbar update icon to self-install this release.

**SmartScreen:** the exe is unsigned, so Windows will warn — click **More info → Run anyway**.

**Checksums:** verify against `DevDashboard-windows-x64.zip.sha256`:

```powershell
Get-FileHash DevDashboard-windows-x64.zip -Algorithm SHA256
```

## Known limitations

- **Windows only, for now.** A POSIX code path exists and passes CI on macOS and Linux, but it has never been run on a real machine.
