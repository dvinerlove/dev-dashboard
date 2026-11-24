# Laravel Herd (official site, Windows page)

- url: https://herd.laravel.com/ (redirects to /windows)
- title: Laravel Herd — The Laravel development environment
- publisher: Beyond Code (in partnership with Laravel)
- tier: L2 (official product page), source_class: vendor-authored
- fetched: 2026-11-24

## Key quotes

1. "Herd gives you a fast, native PHP and Laravel stack for every project on your machine. Install it once and manage everything in one place without external dependencies." — native GUI app, macOS + Windows ("Is there a Linux version available? Not… yet.").

2. Services panel (closest desktop-GUI analog to our dashboard): "Services — Run and manage local databases, caches, and other services alongside your sites." Service rows show e.g. "Redis ... v7.4.11 · Port 6379 [Stop]", config fields "Name / Port 6379 / Start Automatically / Version / Data Directory", actions "Documentation Open / Logs Open / Environment Variables".

3. Service creation form offers "Automatically start with Herd" and "Default port in use" detection — per-service autorun + port conflict awareness, overlapping our autorun + ports.

4. App-level autorun/tray: "Launch Herd at login — Start Herd automatically when you sign in to Windows." + "Start minimized as system tray application — Launch in the background, tucked into the system tray." — identical tray pattern to ours.

5. Env delivery: "Add MySQL, PostgreSQL, Redis, and more in a click. Run versions side by side, with the .env values ready to copy." — env vars are generated per-service and copied into the app's .env, e.g. REDIS_HOST/REDIS_PORT.

6. Per-project config: "Secure sites, switch PHP versions, share a herd.yml, and keep every project configured the way it needs to be." + parallel workspaces (branch = own domain + DB copy).

7. Pricing: "Herd ... Free — No license needed"; "Herd Pro ... $69 $99 Per year"; "Herd for Teams ... $199 $299 Per year · 10 licenses"; "Lifetime license now available. Pay once, keep Herd Pro forever." Pro adds "managed services, deeper debugging, and a direct line to the team".

8. Herd Studio + CLI: "Open any Herd site with its live preview, console, logs, terminal, and code context in one place"; agents "can also control Herd directly via the CLI"; Laravel Boost lets agents "analyze dumps and queries, test emails, and enable HTTPS".

Boundary: PHP/Laravel-scoped — services are bundled DBs/caches, not arbitrary user processes; no generic process supervisor, no port conflict/issues model beyond its own services.
