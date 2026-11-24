# portman — https://github.com/al-nemirov/portman
- Title: "al-nemirov/portman" README + repo metadata
- Publisher: GitHub / al-nemirov
- Tier: L1 (project's own docs)
- Fetched: 2026-11-24 (GitHub REST API)
- source_class: independent-primary
- Repo meta: JavaScript (Node ≥18; single .exe build), 0 stars, MIT, pushed 2026-07-20. UI in EN/KO/DE/ES.

## Key quotes (README)
- "Retro CRT-styled Windows dispatcher for localhost dev servers. See what's listening, what's idle, kill duplicates, auto-clean stale dev servers."
- "Standalone Windows .exe with 80s synthwave UI for managing localhost dev servers. Live RAM/CPU per process, clickable URLs, filter/search/sort, auto-kill idle servers. Self-protected, system whitelist, one-click desktop launcher." (repo description)
- "One screen shows every TCP LISTEN process on your machine, grouped and color-coded. Tells you which ones are actually being used (open connections) and which are idle (listening but no one is talking to them)."
- "An optional auto-mode sweeps idle dev servers older than N minutes"; "`portman run -- npm run dev` registers your dev server with a label, and automatically kills the previous instance of the same project when you start a new one."
- Status model: `●` registered through `portman run`; `◆` unknown but inside dev-port range (3000–9999); `◈` system process — locked, kill button hidden. "System processes are physically unclickable."
- Requires Windows 10/11; Option A single `portman.exe` from releases (no Node needed, SmartScreen warning expected — unsigned), Option B `node bin/portman.js ui`. Free, MIT.
