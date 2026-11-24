# Source 70 — HN: "Show HN: Sonar – A tiny CLI to see and kill whatever's running on localhost"

- URL: https://news.ycombinator.com/item?id=47452515
- Publisher: Hacker News (comments) | fetched via https://hn.algolia.com/api/v1/items/47452515
- Tier: L4 (community sentiment + feature asks)
- Fetch date: 2026-11-24
- Stats: 204 points, 77 comments — the highest-engagement thread found in this space.

## Key verbatim quotes (author = HN username)

- raskrebs (author): "A big pain of mine was constantly running into port: Redis from one project blocking another, orphaned dev servers from old worktrees, Docker containers I forgot about. The usual fix is lsof -iTCP | grep ..., then figuring out what the PID actually is, then killing it. But I always forget the command"
- raskrebs: "I've already been approached by a few agent orchestration tools that have been struggling with the same thing. It's really useful when you have multiple agents running"
- raskrebs (planned features): "next available port; wait (wait for a host to return a successful health check before proceeding - good for migrations"
- Bradd3rs: "love this, i get tired of spamming lsof -i tcp:xxxx"
- mfkrause: "I always find myself going through my zsh history for `lsof`."
- maciejj: "I always forget the lsof flags and end up googling them every time. Would be cool if it could run in the system tray and show what's running on your ports at a glance."
- klaushardt: "Would be nice to have a flag to customize the URL displayed for Docker containers. I connect to my host via Tailscale, but I can't open links with localhost."
- mustafa0x: "Nice util. It should be possible to kill inline. I like clack/prompts. See its multiselect API." (→ became issue #18)
- Barbing: "That monitor sounds interesting; I manually set something up in Keyboard Maestro to notify me that something quit and potentially re-launch it." (crash-notify/auto-restart demand)
- rtpg (on orphan mechanics): "it's _very easy_ to accidentally spawn children that won't get killed ... the distinction between processes and process groups [is] papered over by the fact that shells will be nice enough to kill via process group."
- quotemstr: "I hate our industry practice of binding to some inscrutable port number on localhost. Unix domain sockets aren't that hard!"
- Skeptics (counter-signal): Doublon "I just needed a simple `alias local-tcp-listeners='lsof -iTCP -sTCP:LISTEN'`"; deadbabe "not sure why a whole cli app is needed"; RonanSoleste "It looks to me like a convenience tool. Which is fine, but i see no need for it myself"
- raskrebs (on niche): "i felt that there was a big gap in managing multiple services running on localhost."
