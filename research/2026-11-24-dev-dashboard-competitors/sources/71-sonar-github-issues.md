# Source 71 — RasKrebs/sonar GitHub issue tracker (feature requests)

- URL: https://github.com/RasKrebs/sonar/issues (fetched via api.github.com issues list + per-issue bodies)
- Publisher: GitHub / RasKrebs
- Tier: L4 — real user requests on the most-engaged tool in the category
- Fetch date: 2026-11-24
- Note: sonar grew from "list+kill ports" CLI into a project/daemon/worktree manager; its tracker is the best public record of what users actually ask for.

## User-filed feature requests (verbatim titles; author in parens)

- #17 "Add Windows support" — closed/merged, author nthomsencph (a *contributor PR*, i.e. demand strong enough that someone ported it themselves). Body: "This PR extends that pattern to Windows by finding the native equivalent for each capability" — netstat -ano, Get-CimInstance, taskkill.
- #25 "[Feature] Add Windows Support" (author raskrebs, tracking issue)
- #15 "[Feature] Create a MacOS app for this" — josegonzalez: "It would be great to have a MacOS app for this, as it'll be slightly more intuitive than trying to remember the `sonar` cli arguments."
- #21 "[Feature] Add tray to linux" (open)
- #5 "[Feature] sonar next: find the next available port" — 0xheartcode: "EADDRINUSE is a common problem. The typical workflow is: try to start a service, it fails, manually hunt for a free port, update your config, try again. There's no standard, fast CLI command to just answer 'what port can I use?' ... especially painful when spinning up multiple instances of the same service"
- #6/#13 "sonar wait: Block until a port is ready" — blocks until ports accept connections, `--http` readiness, `--timeout` (health-gating ask — same as dashboard depends_on)
- #18 "[Feature] kill inline" (open, mustafa0x — interactive multiselect kill)
- #12 "sonar next command", #7 "Self-update and version checking", #10 "go install", #33/#38 Homebrew, #34 "list command with more info", #32 "-4/-6 flags to filter on the IP family", #26 "--bind argument", #35 "support for CentOS 7/8"
- #84 "ports per worktree (worktree_ports in .sonar.yaml)" — worktree-aware port allocation
- #91 (open) "[Feature] Stop or kill a project together with all its checkouts" — project-level lifecycle incl. worktrees
- #109 "claims.ttl sets how long a port claim lives", #108 "sonar down --only", #107 "sonar env" — port *claims*/reservations emerged as a feature
- Bug class worth noting: #95/#97/#98 stale Docker container list misdirecting kills; #97 explicitly "Windows: a stale Docker container list can still misdirect ports.kill" — kill-the-right-thing correctness is hard on Windows too.

## Takeaway

Asked-for, in order of recurrence: Windows support, tray/GUI surface, free-port finder, port-readiness wait, inline/interactive kill, worktree-aware grouping, port claims/reservations, brew/go-install distribution.
