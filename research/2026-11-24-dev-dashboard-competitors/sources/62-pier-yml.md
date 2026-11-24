# 62 — pier docs/pier-yml.md (stack-file convention)

- URL: https://github.com/StepanBlaha/pier/blob/main/docs/pier-yml.md (raw)
- Title: pier.yml: stack files
- Publisher: GitHub / Štěpán Bláha (official docs)
- Tier: L1 | Source class: vendor-authored | Fetched: 2026-11-24

## Key quotes
- "A `pier.yml` describes a set of local services (web app, database, worker, ...). `pier up` starts all of them as managed services, in dependency order, waiting until each one is ready."
- Discovery: "`pier up` / `pier down` look for `pier.yml`, `pier.yaml`, `.pier.yml` or `.pier.yaml` in the current directory and then in each parent directory, stopping at `$HOME`."
- Service keys: run (required, string|array), cwd, port, env, depends_on, ready ("http | port | none | \"log:<regex>\""), ready_timeout.
- ready semantics: "`port` something accepts TCP connections ... `http` `port` answers HTTP with a status below 500 ... `log:<regex>` the service's managed log output matches"
- Start logic: "if `<stack>/<service>` is already running it is left alone; if its `port` is taken by something else it fails and tells you who holds the port" — port-conflict pre-check.
