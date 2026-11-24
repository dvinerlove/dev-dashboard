# Portmaster (n-f.pro) — https://n-f.pro/tools/portmaster/
- Title: "Portmaster – Kill a Process on a Port in Windows – n-f.pro"
- Publisher: Sebastian Glabutschnig / n-f.pro (repo github.com/niobiumface/portmaster)
- Tier: L2 (vendor-authored product page)
- Fetched: 2026-11-24
- source_class: vendor-authored

## Key quotes
- "Portmaster is a Windows Local Dev Server & Port Manager… Lightweight Windows tool to see, stop and restart your local development servers – as a GUI, from the command line or from the system tray."
- "It lists only the listeners that matter: local TCP ports of your own user, without Windows system services, with dev servers highlighted."
- "Start a server through Portmaster (`portmaster run --name web npm run dev`) and it becomes restartable: kill the whole process tree and start the same command in the same folder again with one click."
- Tech: "Written in Go with a WebView2 interface." "System Windows; Tech stack Go · WebView2 · HTML/JS; Price & license $0 / €0 (Free / Open Source)"; version 0.1 (released 21/08/2026).
- Detection/features list: "Marks typical dev ports (3000–3999, 4321, 5173 …) and runtimes (node, deno, bun …)"; "Filters: dev only, today / mine, tracked only – with a warning when several PIDs share a port"; "Kill by port or PID, or all dev servers at once (`portmaster kill --all-dev`)"; "Open in browser, open folder, process tree, HTTPS/TLS detection, history side panel"; "Optional on-kill hook (webhook URL or local command)"; hotkeys.
- Requirements: "Windows 10/11 with the WebView2 Runtime (usually preinstalled); Go 1.24+ to build portmaster.exe" — distributed as source only ("No checksum – this tool is distributed as source code on GitHub"). Data in `%LOCALAPPDATA%\portmaster`.
