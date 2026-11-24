# Heimdall README (GitHub linuxserver/Heimdall)

- url: https://github.com/linuxserver/Heimdall (raw README)
- title: Heimdall — Application Dashboard
- publisher: LinuxServer.io community (MIT)
- tier: L1 (official README), source_class: vendor-authored
- fetched: 2026-11-24

## Key quotes

1. "Heimdall Application Dashboard is a dashboard for all your web applications. It doesn't need to be limited to applications though, you can add links to anything you like." — it's a link/launcher dashboard, not a process manager.

2. "Heimdall is an elegant solution to organise all your web applications. It's dedicated to this purpose so you won't lose your links in a sea of bookmarks. Why not use it as your browser start page?"

3. Enhanced apps = live stats: "Enhanced apps allow you provide details to an apps API, allowing you to view live stats directly on the dashboad. For example, the NZBGet and Sabnzbd Enhanced apps will display the queue size and download speed while something is downloading." — status via each app's API, not health probes.

4. Foundation apps: "will auto fill in the icon for the app and supply a default color for the tile".

5. Runtime: PHP/Laravel app (needs PHP >= 7.2.5, sqlite, php-zip); served by httpd or `php artisan serve`; multi-arch Docker image (x86-64, armhf, arm64). MIT license.

Boundary: read-only presentation layer (links + per-app API stats) — no start/stop, no process supervision, no ports/env/autorun. Our "open service in browser" = their entire product.
