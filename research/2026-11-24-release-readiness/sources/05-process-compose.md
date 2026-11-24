# Source 05 — F1bonacc1/process-compose (repo, README, .goreleaser.yaml, releases)

- URLs:
  - https://api.github.com/repos/F1bonacc1/process-compose (+ /releases/latest, /contents)
  - https://raw.githubusercontent.com/F1bonacc1/process-compose/main/README.md
  - https://raw.githubusercontent.com/F1bonacc1/process-compose/main/.goreleaser.yaml
- Publisher: F1bonacc1/process-compose | Tier: L1 | source_class: vendor-authored
- Fetched: 2026-11-24

## Repo metadata

- description: "Process Compose is a simple and flexible scheduler and orchestrator to manage non-containerized applications." | Apache-2.0 | ~2960 stars | created 2022-04 | Go.

## .goreleaser.yaml — verbatim signals

- `builds: CGO_ENABLED=0` for linux/windows/darwin × 386/amd64/arm64/arm; ldflags inject `config.Version={{.Tag}}`, `config.CheckForUpdates=true`, Commit, Date, `-s -w`.
- `archives` name_template `{{ .ProjectName }}_{{ .Os }}_{{ .Arch }}`, zip override for windows.
- `checksum: name_template: "{{ .ProjectName }}_checksums.txt"`.
- `brews`: homebrew tap `f1bonacc1/homebrew-tap`, `bin.install "process-compose"`.

## Release v1.124.0 (2026-10-26) assets verbatim

`process-compose_checksums.txt` + tarballs for darwin_amd64/arm64, linux_386/amd64/arm/arm64, and zips for windows_amd64/arm64. (No installers — CLI/TUI tool ships raw archives + checksum file, the GoReleaser default shape.)

## README signals

- Badges row (made-with-Go, maintained, PRs-welcome, Go Report, downloads, X), `demo.gif` + `tui.png` screenshots, numbered feature list (~30 items incl. MCP server, health checks, namespaces), "Get Process Compose" → external docs site for install instructions, "How to Contribute" 5-step fork/PR flow, GitHub Sponsors + Bitcoin.

## Signals

- Canonical Go-tool pattern: GoReleaser on tag → archives + checksums + brew tap; README keeps install/docs as links to a docs site rather than inline detail; no CONTRIBUTING.md file (instructions inline in README).
