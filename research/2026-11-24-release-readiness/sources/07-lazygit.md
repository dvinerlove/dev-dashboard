# Source 07 — jesseduffield/lazygit (repo metadata, README, releases)

- URLs:
  - https://api.github.com/repos/jesseduffield/lazygit (+ /releases/latest, /contents)
  - https://raw.githubusercontent.com/jesseduffield/lazygit/master/README.md
- Publisher: jesseduffield/lazygit | Tier: L1 | source_class: vendor-authored
- Fetched: 2026-11-24

## Repo metadata

- "simple terminal UI for git commands" | MIT | ~84k stars | created 2018-05 | Go.
- Root: `CODE-OF-CONDUCT.md CONTRIBUTING.md LICENSE Makefile README.md SECURITY.md VISION.md .goreleaser.yml` + workflows `ci.yml release.yml` + AGENTS.md/CLAUDE.md.

## Release v0.66.3 (2026-11-07) assets verbatim

`checksums.txt` + `lazygit_0.66.3_{darwin_arm64, darwin_x86_64, freebsd_*, linux_*, windows_32-bit, windows_arm64, windows_x86_64}.tar.gz/.zip` — raw GoReleaser archives, no installers, checksums file on top. Downloads in the tens of thousands (linux_x86_64 51k, darwin_arm64 42k, windows_x86_64 12k).

## README signals (grep over raw)

- Badges: GitHub Releases total downloads, golangci-lint, latest tag, `homebrew/v/lazygit`.
- Sections: Sponsors → Elevator Pitch → Table of contents → Features (hunk-level, ~15 subsections w/ animated demos) → Tutorials → **Installation** with per-ecosystem subsections: Binary Releases, Dev container feature, Homebrew (`brew install lazygit`), MacPorts, Void Linux, Scoop (`scoop bucket add extras` + `scoop install lazygit`), gah, Arch Linux (pacman/AUR), Fedora/AL2023/CentOS (COPR + Terra), NixOS, Winget (`winget install JesseDuffield.lazygit`), plus Conda/Flo/FreeBSD/openSUSE/Go install/Release binary/Ubuntu PPA-style entries.
- Fun videos, contributing link, donate.

## Signals

- At scale, the README install section = exhaustive package-manager matrix (community-maintained packages listed as first-class), GitHub Releases stays the binary source; version via `.goreleaser.yml` + tag; repo ships all community-health files incl. SECURITY.md and VISION.md.
