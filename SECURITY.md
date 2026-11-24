# Security Policy

## Reporting a vulnerability

Please report security issues via [GitHub Security Advisories](../../security/advisories) ("Report a vulnerability") — do not open a public issue.

## Scope notes

- The HTTP API binds to `127.0.0.1` only and POST endpoints are protected by a CSRF Origin check plus a Host allowlist (`127.0.0.1`/`localhost`). **Do not expose it to a LAN or the internet** — it can start and stop processes.
- Env secrets configured for services are masked in API responses unless explicitly requested with `?reveal=1`.
- `state.db` and config files live in the per-user data directory; keep them out of shared/synced folders if they contain sensitive paths or tokens.
