# Source 06 — pvolok/dekit (formerly mprocs) repo, README, release workflow, releases

- URLs:
  - https://api.github.com/repos/pvolok/dekit (redirected from pvolok/mprocs) (+ /releases, /contents)
  - https://raw.githubusercontent.com/pvolok/dekit/master/README.md
  - https://raw.githubusercontent.com/pvolok/dekit/master/.github/workflows/release.yml
- Publisher: pvolok/dekit | Tier: L1 | source_class: vendor-authored
- Fetched: 2026-11-24

## Repo metadata

- "Process manager for dev and prod" | MIT | ~2820 stars | created 2021-08-30 | Rust. (Repo was renamed mprocs → dekit; `README-mprocs.md` kept beside `README.md`; `CHANGELOG.md` at root.)

## README structure

Centered title+tagline "Process manager for dev and prod", docs/X badges, feature bullets ("Define your project's tasks in a config file / dekit handles dependencies, crashes and restarts / …TUI / A full CLI for humans and agents / Built-in JavaScript"), screenshot `img/dekit-tui.png`.

Install block verbatim:
- macOS/Linux: `curl -fsSL https://dekit.run/install.sh | sh`
- Windows: `irm https://dekit.run/install.ps1 | iex`
- `npm install -g @dekit/cli`, `pip install dekit-cli`

Quick start = `dekit.yaml` example (tasks with cmd/ready/deps/autostart).

## release.yml — verbatim signals

- `on: push: tags: ["v[0-9]+.[0-9]+.[0-9]+*"]` — tag pattern filters pre-releases too (`*-*` → `prerelease=true`, `npm_tag=next`).
- Verifies tag matches code version: `version="${GITHUB_REF_NAME#v}"` vs `cargo metadata … select(.name == "dekit") | .version` — "tag version $version does not match dekit Cargo version" → exit 1.
- `packaging/release-notes.sh <version>` must succeed before publish; `check-crate` job runs `cargo publish --dry-run` pre-build.

## Release assets (v0.10.3, 2026-10-25) verbatim

`dekit-{aarch64-apple-darwin, aarch64-unknown-linux-musl, x86_64-apple-darwin, x86_64-pc-windows-msvc, x86_64-unknown-linux-musl}.{tar.gz,zip}` + `install.sh` + `install.ps1` + `SHA256SUMS`. A rolling `canary` prerelease reuses the same asset set.

## Signals

- curl|sh installer scripts shipped as release assets (install.sh/install.ps1), multi-ecosystem distribution (crates.io + npm + PyPI + GitHub Releases), version-source-of-truth = manifest, tag must match.
