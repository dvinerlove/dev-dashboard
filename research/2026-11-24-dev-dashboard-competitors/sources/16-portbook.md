# Portbook — https://github.com/a-grasso/portbook
- Title: "a-grasso/portbook" README + repo metadata
- Publisher: GitHub / a-grasso
- Tier: L1 (project's own docs)
- Fetched: 2026-11-24 (GitHub REST API)
- source_class: independent-primary
- Repo meta: Rust, 24 stars, MIT, pushed 2026-09-14.

## Key quotes (README)
- "Local Rust web dashboard that auto-discovers and labels HTTP dev services running on localhost ports — with live SSE updates, project-root detection, and live/error/dead classification." (repo description)
- "Auto-discovers HTTP servers on every non-standard localhost port"; "Labels each card with project name (detected from process `cwd` markers) and page title"; "Classifies ports as **live** / **error** / **dead** with visible reasons" — "a crashed `next dev` shows up red instead of disappearing."
- Surfaces: "Web UI at `http://localhost:7777` with live updates via SSE; `portbook ls` — grouped, colored terminal list; `portbook tui` — interactive terminal app: live updates, filter, expand row to see diagnostics, Enter to open in browser; `portbook watch [--json]` — streaming snapshots for agents and scripts."
- "Stable JSON schema (`/api/ports`, `ls --json`, `watch --json`) — same shape everywhere"; "Cmdline secret redaction at the API boundary (tokens, passwords, URLs with userinfo)"; "`portbook explain <port>` — paste-ready diagnostic block (probe URL, elapsed time, error class, attempts)".
- Probe diagnostics in schema: `probed_url`, `elapsed_ms`, `error_class` ("timeout | connect | decode | body | other"), `attempts`, `status` — project_root "detected from process cwd".
- Platform: "macOS and Linux (x86_64 and arm64). Requires `lsof` (macOS) or `ss` (Linux) on `$PATH`" — NO Windows. Install: `brew install a-grasso/tap/portbook` or shell installer.
- "Single static binary, ~5 MB, no runtime dependencies beyond `lsof` (macOS) or `ss` (Linux)."
