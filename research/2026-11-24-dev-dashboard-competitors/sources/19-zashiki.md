# Zashiki Warashi — https://zashiki.anireco.app/ + github.com/khushal-sahni/zashiki-warashi
- Title: "Zashiki Warashi — localhost control plane for macOS"
- Publisher: Khushal Sahni (zashiki.anireco.app; GitHub)
- Tier: L2 (site) / L1 (repo README)
- Fetched: 2026-11-24
- source_class: vendor-authored (site) / independent-primary (README)
- Repo meta: Rust backend + Tauri 2/React/TS UI, 0 stars, MIT, pushed 2026-10-07.

## Key quotes (site)
- "A machine-local catalog of your projects, one-button start/stop via your login shell, Compose/DB peek, and deep-links into Cursor, Finder, and Compass. Glue for tools you already have — not a Docker GUI, not Portainer, not a folder bookmark."
- "Scheduled jobs too: scripts run on launchd with the app closed, wait for Wi-Fi after wake, and keep logs and run history."
- "macOS. Docker Desktop or OrbStack for Compose stacks. Builds are unsigned for now."
- Philosophy: "Observe existing repos. Keep overrides in app data. Do not require per-repo YAML."

## Key quotes (README)
- "A macOS control plane for the localhost pile — especially AI-generated repos. It remembers projects, one-button start/stop, peeks Compose/DB endpoints, and deep-links into Cursor / Finder / Compass."
- "If Compose is present, the Stack panel peeks DB services, Up/Stop, copy URI, and open Compass for Mongo. Port conflicts offer stop-occupant or remap (stored in app data by default)."
- Stack: "Tauri 2 + React + Vite + TypeScript; Rust (FS, processes, Docker, SQLite); SQLite in the app data directory (machine-local catalog; no cloud sync)."
- Install: unsigned `.dmg` from Releases; MIT license; macOS primary target.
