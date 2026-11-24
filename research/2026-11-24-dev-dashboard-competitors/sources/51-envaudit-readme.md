# 51 — envaudit README

- URL: https://github.com/albertoarena/envaudit (raw README, main)
- Title: envaudit — Zero-dependency Node.js CLI tool that audits .env files
- Publisher: GitHub / albertoarena (repo author). Docs: albertoarena.github.io/envaudit
- Tier: L1 | Source class: vendor-authored | Fetched: 2026-11-24
- Node>=18, zero npm deps, npm: @albertoarena/envaudit. Has a GitHub Action @v1.

## Key quotes
- "Compares `.env` against `.env.example`, detects missing variables, undocumented variables, empty values, and possible secrets leaked into `.env.example`."
- "Output categories: **Errors (✗):** Missing variables, possible secrets in `.env.example`, unquoted values with spaces. **Warnings (⚠):** Undocumented variables, empty values"
- "`envaudit check --ci` ... exits with code 1 if errors found"; `--ignore-empty` "secrets injected at runtime".
- diff: "Shows keys only in each file and keys with different values. Secret-looking values are masked."
- sync: "Add missing keys between `.env` and `.env.example`" with `--dry-run` preview.
- doc: "Generate markdown documentation of all env variables ... Outputs a table grouped by prefix (DB_, APP_, AWS_, etc.) with columns: Variable, Required, Default, Group."
- CI note: ".env is usually gitignored, so on a fresh checkout only .env.example exists and check has nothing to compare against" — workaround `cp .env.example .env`.
