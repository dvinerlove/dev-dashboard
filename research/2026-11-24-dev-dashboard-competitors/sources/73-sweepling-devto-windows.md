# Source 73 — dev.to: "Finding the processes Claude Code leaves running on Windows" (Sweepling)

- URL: https://dev.to/hazeliscoding/finding-the-processes-claude-code-leaves-running-on-windows-2eg7
- Publisher: DEV Community / Hazel Granados (author of Sweepling)
- Tier: L4 (blog post by tool author — the *observed pain* is primary, the tool is vendor-authored)
- Fetch date: 2026-11-24 (full page via r.jina.ai)

## Key verbatim quotes

- "A scan of my machine, 38 hours after boot, found a `next dev` server that had held port 3001 for 35 hours with nothing connected to it. An `ng serve` had sat idle for 11 hours. Around them were 20 bare `tail.exe`, `grep.exe` and `sh.exe` rows in Task Manager, with nothing to say which project they belonged to."
- "All of them came from my Claude Code sessions ... The sessions had ended and the processes kept running. There's an upstream issue about it, #62659, and a bot closed it as not planned."
- "Why this is a Windows problem: On Linux an orphan is adopted by init or a subreaper ... Windows does neither. When a parent exits, its children keep running and keep the dead parent's PID in their own process record. Windows also reuses PIDs, so a few minutes later that number can belong to something unrelated. Task Manager's tree only nests a process under a parent that's still alive, so an orphan shows up as one more top-level `node.exe`."
- Design asks embedded in the tool: confirmation before closing ("Sweepling never closes anything you haven't confirmed"), never offer in-use processes ("anything in it has an established TCP connection"), protect-list, parent-first close order "so a supervisor can't restart a child it just lost", PID-reuse re-validation by start time, command-line masking in logs "since command lines carry tokens and private paths".
- "cc-reaper does this well on macOS and Linux" — i.e. the orphan-cleanup niche had a mac/Linux tool but nothing on Windows; she built the Windows one.
- Field data: "On its busiest day it found 22 groups on my machine: 9 task output watchers, 9 of their `grep` filters, a Next.js dev server, two Angular dev servers and a shell script."
