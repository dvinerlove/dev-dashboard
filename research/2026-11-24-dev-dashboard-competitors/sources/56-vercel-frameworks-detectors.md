# 56 — Vercel @vercel/frameworks frameworks.ts (detector examples)

- URL: https://github.com/vercel/vercel/blob/main/packages/frameworks/src/frameworks.ts (raw, 137KB)
- Title: packages/frameworks/src/frameworks.ts — framework preset definitions
- Publisher: GitHub / Vercel (official source code)
- Tier: L1 | Source class: vendor-authored | Fetched: 2026-11-24
- ~75 framework presets (grep count of `slug:`).

## Key quotes
- Design note: "the `dependency` property needs to reference a CLI. ... you can't look for the `preact` dependency. Instead, you need to look for `preact-cli`"
- Container preset: "`Dockerfile.vercel`/`Containerfile.vercel`" eager; "`Dockerfile`, `Containerfile`" with `fallback: true` "so they do not override a project's actual framework preset."
- Next.js: "detectors: { every: [ { matchPackage: 'next' } ] }"; devCommand value "`next dev --port $PORT`"; buildCommand "`next build`"; envPrefix NEXT_PUBLIC_; sort: 1.
- Remix/React-Router: `matchPackage: '@remix-run/dev'`; `matchContent: '@react-router/dev/vite'`; `supersedes: ['hydrogen', 'vite', 'node']`.
- Django: detectors.some = `requirements.txt` matchContent `[Dd]jango`; `pyproject.toml` `[Dd]jango`; `Pipfile` `[Dd]jango`; `manage.py` matchContent `DJANGO_SETTINGS_MODULE` ("a default django project will create a manage.py which sets DJANGO_SETTINGS_MODULE"); supersedes ['python']; useRuntime @vercel/python.
- FastAPI/Flask same pattern: requirements.txt/pyproject.toml + app-file content matches (`fastapi`, `[Ff]lask`), installCommand placeholder "`pip install -r requirements.txt`".
- Example path+content detector: `every: [ { path: 'package.json', matchContent: '"(dev)?(d|D)ependencies":\\s*{[^}]*"experimental-ash":\\s*".+?"[^}]*}' } ]`.
