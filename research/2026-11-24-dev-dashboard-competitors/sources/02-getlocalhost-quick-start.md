# Source 02 — docs/quick-start (project/service detection + onboarding)

- URL: https://www.getlocalhost.app/docs/quick-start
- Title: "Quick start"
- Publisher: getlocalhost.app docs — fetched via r.jina.ai, 2026-11-24
- Tier: L1 | source_class: vendor-authored | cluster: C1

## Key quotes

- Detection sources: "**Node**: `package.json` scripts, run with your package manager (`pnpm run dev`, …). Known dev servers get their default port, passed as `$PORT`. **Docker Compose**: one `Infra` Service running the whole file (`docker compose up`, in the foreground), or one per Compose service… **Python**: Django, FastAPI and Flask apps, with uv, Poetry, Pipenv or a virtualenv… **Cargo**: `cargo run` for each binary."
- "The likely Services are checked… the rest… folded under 'N more found'. Select several and click **Merge…** to make them one Service, or set what a Suggestion **Starts after**."
- "Nothing found…? Add the Project anyway and add Services yourself with **⇧⌘N**. **Detect Services…** scans again later."
- "On Windows, Add Project also asks where the Project runs: on Windows itself, or in one of your WSL distros."
- Onboarding: "a short welcome explains the three words… a **Project** is a folder, a **Service** is a long-running command… and its **Port** is how localhost knows it is Running." + "a **Get started** checklist at the foot of the sidebar ticks off adding a Project, adding a Service and starting your first one, plus connecting your coding agents".
- Tray/close behavior: "Closing the window doesn't stop anything: your Services keep running, and the menu bar icon (the tray icon on Linux and Windows) shows them, with a red dot while one has Failed. Quitting asks first, then stops everything."
- Logs: "Select **All services** to see every Service's output in one stream, each line prefixed with its Key."
