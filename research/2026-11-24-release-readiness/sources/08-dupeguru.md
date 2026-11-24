# Source 08 — arsenetar/dupeguru (Python/Qt desktop app releases)

- URL: https://api.github.com/repos/arsenetar/dupeguru (+ /releases/latest, /contents/.github/workflows)
- Publisher: arsenetar/dupeguru | Tier: L1 | source_class: vendor-authored
- Fetched: 2026-11-24

## Repo metadata

- "Find duplicate files" | GPL-3.0 | ~8k stars. Workflows: `codeql-analysis.yml`, `default.yml`, `tx-push.yml`.

## Release 4.3.1 (2022-07-09) assets verbatim

- `dupeGuru_win32_4.3.1.exe` (127k downloads) + `dupeGuru_win64_4.3.1.exe` (1.35M downloads) — Inno-style GUI installers
- `dupeguru-win32_4.3.1.zip` / `dupeguru-win64_4.3.1.zip` — portable zips
- `dupeguru_macOS_Qt_4.3.1.zip` (338k)
- `dupeguru_4.3.1_amd64.deb`, `dupeguru-4.3.1-2.x86_64.rpm`, `dupeguru_4.3.1.tar.xz`
- **Every** asset carries a detached `.sig` (GPG signature sidecar, 566 B each).

## Signals

- Long-standing Python/Qt desktop OSS release shape: Windows = installer exe *and* portable zip; Linux = deb + rpm + source tarball; macOS = zip; integrity = GPG `.sig` per file rather than `.sha256` (older convention; SHA-256 sidecars are the 2025-26 norm per localhost/lazygit).
