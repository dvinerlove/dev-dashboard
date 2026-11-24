# 64 — Portlivo features/projects page

- URL: https://portlivo.com/features/projects (via r.jina.ai)
- Title: Projects: start a whole project in one click
- Publisher: portlivo.com (official vendor site). Published 2026-10-21
- Tier: L1 | Source class: vendor-authored | Fetched: 2026-11-24

## Key quotes — convention→command detection table
- "It reads the project's own files and suggests the commands they imply. Nothing runs until you press Create Project."
- "`Procfile.dev` or `Procfile` | Every line, as written"
- "`composer.json` with a `dev` script | `composer run dev` (Laravel 11 and later: server, queue and Vite together)"
- "`artisan` | `php artisan serve` and `php artisan queue:work`"
- "`package.json` | Its `dev`, `start`, `serve` or `watch` script, run with npm, pnpm, yarn or bun to match the lockfile"
- "`bin/dev` or `bin/rails` | `bin/dev`, or `bin/rails server`"
- "`manage.py` | `python3 manage.py runserver`"
- "`go.mod` | `go run .`"
- "`docker-compose.yml` or `compose.yaml` | `docker compose up`, left unticked"
- Priority: "A Procfile wins: when there is one, it's what gets ticked, because it lists exactly what the project runs."
- Also: "Save as Project" captures commands already running from that folder "with its exact arguments"; "Each command runs in a login shell from the project folder, so the PATH from your shell profile (nvm, Herd, Homebrew) applies."
