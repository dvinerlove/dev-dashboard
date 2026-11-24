# Source 01 — marcellosso/localhost repo metadata + tree (GitHub API)

- URL: https://api.github.com/repos/marcellosso/localhost (repo of https://github.com/marcellosso/localhost, site https://www.getlocalhost.app)
- Publisher: GitHub API / repo owner
- Tier: L1 | source_class: vendor-authored (project's own repo)
- Fetched: 2026-11-24

## Repo metadata (verbatim fields)

- `description`: "Desktop process manager for local dev servers. Start, stop and watch every project's Services from one window. Free and open source for macOS, Windows and Linux."
- `license`: MIT (`spdx_id: MIT`)
- `created_at`: 2026-10-22T19:43:17Z · `pushed_at`: 2026-11-19 · `stargazers_count`: 7 · `default_branch`: main · `language`: Rust · `homepage`: https://www.getlocalhost.app
- `topics`: desktop-app, dev-server, developer-tools, linux, local-development, macos, mcp, mcp-server, model-context-protocol, pm2-alternative, process-manager, procfile, rust, swiftui, tauri, windows, wsl

## Root tree (verbatim listing, api.github.com/contents)

Files: `.dockerignore .gitignore .mcp.json AGENTS.md CLAUDE.md CODE_OF_CONDUCT.md CONTRIBUTING.md Dockerfile LICENSE PRODUCT.md README.md RELEASING.md SECURITY.md glama.json server.json`
Dirs: `.github .impeccable apps assets core docs packages packaging scripts site skills`

`.github/`: `CODEOWNERS`, `ISSUE_TEMPLATE/` (bug_report.yml, feature_request.yml, config.yml), `assets/` (README images/GIF), `dependabot.yml`, `pull_request_template.md`, `release.yml` (auto-notes config), `workflows/` (ci.yml, log-perf.yml, packages.yml, publish-cli.yml, release.yml, site.yml)

## Key signals

- Full "community health file" set present: LICENSE, CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, issue templates, PR template, CODEOWNERS, dependabot.
- `RELEASING.md` — a maintainer-facing release runbook at root (see source 03).
- AGENTS.md + CLAUDE.md — agent-instructions files committed at root.
