# Source 72 — anthropics/claude-code issues: agent-spawned orphan processes

- URL: https://github.com/anthropics/claude-code/issues (bodies fetched via api.github.com)
- Publisher: GitHub / Anthropic repo (user-filed bug reports = independent-primary user evidence)
- Tier: L4 platform-wise but independent-primary source_class
- Fetch date: 2026-11-24

## Issue #16198 — "Background dev servers not cleaned up when session transitions to new tasks" (jmhunter83, macOS, closed)

- "This results in orphaned processes consuming significant resources (in my case, 89% CPU and 2.5GB RAM over 2 days)."
- Expected: "Claude kills the background dev server before moving to the new task or ending the session" — Actual: "The `workerd` process continues running indefinitely"
- Suggested fixes: "Prompt/train model to kill dev servers before transitioning to unrelated tasks", "Add automatic cleanup of background tasks when session ends"

## Issue #27959 — "Background bash commands become orphan processes after session close or task interruption" (Disentinel, closed)

- "These orphaned processes persist indefinitely, consuming RAM and CPU. There is no mechanism to track or clean them up in subsequent sessions."
- "With multiple Claude Code sessions (worktree workflow), orphans accumulate fast. On a 16GB machine running 4-6 Claude Code instances, this contributes to memory pressure and swap thrashing"
- "No visibility in Claude Code UI — the status bar doesn't show these processes in the next session"

## Issue #77593 — "Windows: background Bash tool processes orphaned across sessions (block Git installer, leak resources)" (1Map, Windows, closed)

- "Because Windows has no cascading process-tree kill, the children keep running indefinitely after their parent `bash.exe`/`node` dies."
- "**11 orphaned Git-Bash processes** (`bash.exe`/`tail.exe`/`grep.exe`) + **7 orphaned `node` processes** accumulated. The Git for Windows installer refused to proceed because these leftovers hold `C:\\Program Files\\Git\\usr\\bin\\{bash,tail,grep}.exe` open. They also silently leak memory/ports (e.g. a leftover `node serve.js` still bound to a dev port)."
- Suggested fix: "assigning spawned processes to a **Job Object** with `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE` gives cascading termination" — note: this is exactly what Dev Dashboard's process_tree.py already does.
- A confirming comment extends blast radius to "Claude Code CLI 2.1.220 (not just the VS Code extension)".

## Issue #41742 — "Critical: Node.js and bash processes are never released during Next.js development on Windows" (vlastimilvajnorak, closed)

- "**25+ orphaned 'Node.js JavaScript Runtime' processes** (ranging from 0.7 MB to 87 MB each); **14+ orphaned 'bash.exe'** ... Combined impact: **85% CPU, 73% Memory**"

## Issue #43944 — "Background processes started by Bash tool are not cleaned up on session exit" (macOS, closed)

- "orphaned `next dev` servers can grow to 8+ GB"
- "Hooks can't inject env vars into Bash tool calls, so there's no way to tag Claude-spawned processes for selective cleanup." (attribution problem)
- Desired: "clean them up (SIGTERM → SIGKILL) when the session exits. This should include the full process tree, not just the top-level PID."

## Issue #62659 — referenced by Sweepling's author: "an upstream issue about it, #62659, and a bot closed it as not planned" (user demand dismissed upstream → third-party tools fill the gap)
