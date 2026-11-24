# Source 09 — docs/updates + GitHub repo metadata

- URL: https://www.getlocalhost.app/docs/updates — Title: "How localhost updates on macOS, Windows, Linux"
- URL: https://api.github.com/repos/marcellosso/localhost (+ /releases/latest)
- Publisher: getlocalhost.app docs / GitHub — fetched 2026-11-24
- Tier: L1 | source_class: vendor-authored (docs, repo); independent-secondary (star count) | cluster: C1

## Updates doc — key quotes

- "localhost checks GitHub Releases for a new version at launch and then every 6 hours. It offers a new version; it never installs one without asking."
- "Installing restarts localhost, so… **every running Service stops first**: localhost lists the ones that are running and asks before it goes on."
- "Each update is signed, and localhost checks the signature against a key built into the app before installing it."
- Per-package: macOS app self-updates "also when installed with Homebrew: `brew upgrade` leaves it alone"; Windows self-updates (+ replaces WSL `localhostd`); AppImage self-updates; `.deb`/`.rpm` via package manager.
- "Checking is the only thing localhost asks the network for. Builds you make yourself never check."

## GitHub repo metadata (api.github.com, 2026-11-24)

- description: "Desktop process manager for local dev servers. Start, stop and watch every project's Services from one window. Free and open source for macOS, Windows and Linux."
- language: Rust; license: MIT; created_at: 2026-10-22; pushed_at: 2026-11-19
- stargazers_count: 7; forks: 0; open_issues: 4; homepage: getlocalhost.app
- Latest release v0.6.0, published 2026-11-14; assets: localhost-0.6.0.dmg, localhost_0.6.0_x64-setup.exe, localhost-app_0.6.0_amd64.deb, .rpm, .AppImage, localhostd, appcast.xml/latest.json (+ .sha256 for each)
- Docs pages carry "Edit this page on GitHub" → site sources in-repo (site/src/content/docs/*.md) — docs are vendor-written.
