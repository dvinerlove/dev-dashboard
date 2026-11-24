# Source 02 — localhost README.md (raw)

- URL: https://raw.githubusercontent.com/marcellosso/localhost/main/README.md
- Publisher: marcellosso/localhost (project's own repo)
- Tier: L1 | source_class: vendor-authored
- Fetched: 2026-11-24

## Structure (449 lines)

Centered wordmark `<picture>` (dark/light), tagline "Every local project, one place to run it. For macOS, Linux and Windows.", one-paragraph pitch, links row (site·Docs·agents·Changelog), badges row (GitHub release version, ci.yml badge, license badge), full-width hero GIF (`.github/assets/start-all.gif` 1200×720), feature bullet list.

Sections in order: `## Why` → `## Install` (+`### Homebrew`, `### Updates`) → `## Getting started` (8 numbered how-to subsections) → `## Keyboard shortcuts` → `## First launch` (`### macOS: a build that isn't notarized`, `### Windows: SmartScreen`) → `## Platform notes` → `## Data` → `## The command line` → `## Coding agents (MCP)` → `## FAQ` → `## How it compares` → `## Contributing` → `## License`.

## Key verbatim quotes

- Install: "Download the latest release from [GitHub Releases](https://github.com/marcellosso/localhost/releases/latest)." followed by a table mapping each OS to its artifact + minimum requirements (DMG / .deb / .rpm / AppImage / `localhost_<version>_x64-setup.exe`, "It installs for your user only, no administrator rights").
- "Releases aren't notarized or code-signed by a known publisher yet, so the first launch needs one extra step on macOS and Windows; see [First launch](#first-launch). There are no Flatpak or Snap packages: their sandboxes can't run your project's commands."
- SmartScreen: "Unsigned releases make SmartScreen say 'Windows protected your PC'. Click **More info**, check that the file name is what you downloaded from this project's releases, then click **Run anyway**. Each new version asks once again." (with two annotated screenshots of the dialog)
- macOS: "**Remove the quarantine flag** the browser added, from Terminal… `xattr -dr com.apple.quarantine /Applications/localhost.app`" plus "Download from Terminal. macOS only checks files marked as downloaded from the internet, and `curl` doesn't mark them."
- "How it compares" table: per-tool "Where it wins / Where localhost fits better" — explicitly non-defensive comparison vs pm2, foreman/overmind/honcho, tmux, Docker Compose, concurrently, devglow/DevWebUI.
- License section: "MIT, see [LICENSE](LICENSE)."

## Signals

- README doubles as full user manual (install → first launch → config → FAQ) because docs site exists separately.
- First-launch/SmartScreen mitigation is documented *in the README with screenshots*, not left to issues.
