# Source 01 — localhost app README

- URL: https://github.com/marcellosso/localhost (raw README.md, main branch)
- Title: marcellosso/localhost — "Every local project, one place to run it"
- Publisher: GitHub repo (vendor-authored, official)
- Tier: L1 · source_class: repo
- Fetched: 2026-11-23

## Key verbatim quotes

1. "localhost app (getlocalhost.app) is a free, open-source desktop process manager for local development: it starts, stops and watches all your dev servers, workers and databases from one window instead of terminal tabs."
2. "A **Project** is a folder. A **Service** is one long-running command in it: `pnpm dev`, `uv run fastapi dev`, `docker compose up postgres`, `cargo run`."
3. "One place for every project: Start All / Stop All, Dependencies between Services (the API waits for the database), one merged log of every Service."
4. "a Service counts as Running once its Port accepts connections. If the Port is taken, localhost says by whom and can start the Service on the next free one. The **Ports** view lists everything listening on your machine, whoever started it."
5. Six-state table: "Stopped | Not running… Starting | Waiting for its Dependencies… Running | Up: its Port accepts connections (or it has been alive ~1.5 s)… Stopping | Asked to stop… Exited | Ended on its own with exit code 0. Failed | Ended on its own with an error, or couldn't start. The reason and the last lines of output are shown."
6. "Select a Service and press **⌘R** to start (or restart) it, **⌘.** to stop it. **⇧⌘R** starts every Service of the Project in dependency order, **⇧⌘.** stops them all."
7. "Closing the window doesn't stop anything: your Services keep running, and the menu bar icon (the tray icon on Linux and Windows) shows them, with a red dot while one has Failed."
8. "**All services** shows every Service of the Project in one stream, each line prefixed with its Key. **⌘F** filters, **⌃L** (Ctrl+L) clears the view; log files are kept. URLs in the output are clickable."
9. "The **Ports** view (**⌘0**) lists every process listening on a TCP port and whom it belongs to… Select one and press ⌘. to stop it; localhost asks first for anything it didn't start."
10. "a notice at the bottom of the sidebar says 'localhost X.Y.Z is available'" — alerts/updates live in the sidebar footer.
11. Screenshot alt text: "the Acme Shop Project with its Services (Migrations exited, API, Web and Worker running, Storybook manual) and their merged log" — confirms sidebar+list+log layout and per-service state words.
12. "Keyboard first: a command palette, a shortcut for every action, arrow keys across the window. Screen readers, light and dark, reduced motion."
