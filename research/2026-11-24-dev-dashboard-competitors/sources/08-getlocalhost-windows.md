# Source 08 — docs/windows (Windows + WSL specifics)

- URL: https://www.getlocalhost.app/docs/windows
- Title: "Windows and WSL"
- Publisher: getlocalhost.app docs — fetched via r.jina.ai, 2026-11-24
- Tier: L1 | source_class: vendor-authored | cluster: C1

## Key quotes

- "localhost on Windows installs for your user only, on Windows 10 or 11 (x64)… A Project runs on its **Execution Target**: Windows itself (the default), or a WSL distro such as Ubuntu."
- "Commands run in `cmd.exe` with your user environment read fresh at every start, so a toolchain you just installed is found without restarting localhost. Version managers that only work through a PowerShell profile (fnm or mise in `activate` mode) aren't seen; their shim modes, nvm-windows and Volta are."
- WSL: "localhost copies a small helper, `localhostd`, into `~/.local/share/localhost/windows/` there; it is replaced when localhost updates, and stops every Service it started when localhost quits."
- MCP on Windows: "the app and the agent share one background core, reached through a named pipe (`\\.\pipe\localhostd-<number>`) that only your user can open."
- Updates: "The app installed by `localhost_<version>_x64-setup.exe` updates itself: **Restart to Update** stops your running Services, after asking, then installs the new version."
- Tray: "Left-click it to open the window, right-click it for the menu"; icon lands in overflow by default.
- Integrations: "Open in Terminal uses Windows Terminal… VS Code, Cursor, VSCodium and Windsurf open WSL folders through their WSL remote."
- Uninstall leaves `~/.local/share/localhost/windows` copies in each distro to remove manually.
