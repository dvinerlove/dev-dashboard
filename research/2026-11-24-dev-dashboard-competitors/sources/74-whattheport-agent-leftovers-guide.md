# Source 74 — whattheport.dev: "Claude Code left a dev server running? Find and clean up agent-started servers"

- URL: https://whattheport.dev/guides/claude-code-dev-server-left-running
- Publisher: whattheport.dev (guide site adjacent to a localhost-tooling product; treat tool framing as vendor-adjacent, pain description as user-facing observation)
- Tier: L4 → useful mainly as corroboration of the orphan pain + attribution techniques
- Fetch date: 2026-11-24 (full page via r.jina.ai)

## Key verbatim quotes

- "Coding agents are good at starting dev servers. They're less good at stopping them. Ask Claude Code, Codex or Cursor to 'check it in the browser' and it will run `npm run dev` in a background shell. The session ends, you close the window, and the server keeps running. Do that across a few projects and a few days and you have a handful of `node` processes holding ports and gigabytes of memory, none of them attached to a terminal you can find."
- "The other symptom is the reverse: the agent doesn't notice a server is already running, starts another, and gets `localhost:3001`. Then `3002`. You keep typing new port numbers into the browser." (port-drift complaint — agents silently increment ports)
- Attribution table (env vars agents inject): Claude Code `CLAUDECODE=1`, `CLAUDE_CODE_SESSION_ID`; Conductor `CONDUCTOR_WORKSPACE_NAME`, `CONDUCTOR_PORT`; Pane `PANE_SESSION_ID`; Codex matched via `~/.codex/sessions`.
- Process-group gotcha: "Agent-started servers are usually a chain: a shell, `npm`, the framework CLI, then the server itself. Stopping the process on the port can leave the rest. Stop the whole process group." (`kill -- -$(ps -o pgid= -p <PID>)`)
- "Some servers rename themselves once they start (Next.js shows up as `next-server`), which hides their environment from `ps`."
- Companion evidence of genre: sibling guides exist on ramback.app, iknowmymac.com, orrel.app, claudecodereview.ai — an entire SEO genre of "find servers your AI agent left running" appeared in 2026, indicating real search volume for the pain.
