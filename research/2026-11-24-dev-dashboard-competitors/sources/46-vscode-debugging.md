# VS Code — Debugging doc (run configs)

- url: https://code.visualstudio.com/docs/editor/debugging (→ /docs/debugtest/debugging)
- title: Debugging — VS Code docs
- publisher: Microsoft (code.visualstudio.com)
- tier: L1 (official docs), source_class: vendor-authored
- fetched: 2026-11-24

## Key quotes

1. "For a simple application, VS Code tries to run the active file. If your application requires a specific entry point, command-line arguments, environment variables, or another custom setup, create a launch.json configuration." — env/args per launch config = partial overlap with our per-service env, but editor- and debugger-bound.

2. "For a repeatable setup that starts multiple debug configurations together, create a compound launch configuration." — multi-service start exists but as debug sessions, not supervised services.

3. "Use Run > Start Debugging, not Run Without Debugging." — run configs are debugging sessions; no restart policy, health check, autorun-at-login, or port inventory.
