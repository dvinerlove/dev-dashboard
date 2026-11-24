# 60 — pier IdentifyProject.swift (detection source)

- URL: https://github.com/StepanBlaha/pier/blob/main/Sources/PierCore/Identify/IdentifyProject.swift (raw)
- Title: IdentifyProject.swift — project root, git branch, framework detection
- Publisher: GitHub / Štěpán Bláha (official source code)
- Tier: L1 | Source class: vendor-authored | Fetched: 2026-11-24

## Key quotes
- Project markers (walk up from cwd): ["package.json", ".git", "pyproject.toml", "requirements.txt", "Gemfile", "go.mod", "Cargo.toml", "composer.json", "deno.json", "deno.jsonc", "bun.lockb", "mix.exs"] — "Nearest ancestor of `cwd` (inclusive) containing a project marker. Ignores nil, \"/\" and $HOME."
- Git branch: parses `.git/HEAD`; handles worktrees where `.git` is a file ("gitdir: ..."); detached -> 7-char sha.
- packageDependencies: "dependencies + devDependencies keys of `<dir>/package.json`"
- argvRules: "Ordered: meta-frameworks before their bundlers, runtimes last. First match wins." — words = argv/name basename tokens (script ext stripped); phrases = substrings of space-joined lowercased argv. e.g. next (words: next, next-server, next-router-worker), django (phrases: manage.py runserver, django-admin runserver, runserver), laravel (words: artisan), fastapi (words: uvicorn, fastapi), phoenix (phrases: phx.server).
- depRules priority: next, nuxt, @sveltejs/kit, astro, `@remix-run/` (prefix match), gatsby, @angular/core, react-scripts, @docusaurus/core, vitepress, vite, @nestjs/core, fastify, express.
- Vite upgrade: "When argv says plain Vite but package.json reveals a meta-framework built on it" — viteHosts = ["sveltekit", "remix", "nuxt", "astro"].
