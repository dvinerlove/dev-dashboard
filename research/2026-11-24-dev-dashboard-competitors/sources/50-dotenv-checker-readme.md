# 50 — dotenv-checker README

- URL: https://github.com/tanguykonan/dotenv-checker (raw README, main)
- Title: dotenv-checker — Validate and synchronize environment variables across your project
- Publisher: GitHub / tanguykonan (repo author)
- Tier: L1 | Source class: vendor-authored | Fetched: 2026-11-24
- JS CLI, node>=22, 1 dependency, MIT. Repo: 1 star, very new.

## Key quotes
- "CLI to detect missing, extra or inconsistent variables between all .env files" (repo description)
- "It detects missing, empty, and undocumented keys across your environment files and reference templates, with built-in tools to synchronize them safely."
- "Scans projects recursively to find all env files / Validates values against template files (.env.example) / Diffs environments directly (such as staging against production) / Synchronizes missing variables across files safely / Outputs JSON for CI pipelines"
- "dotenv-checker --compare .env.staging .env.production" — env-vs-env diff without a template.
- "# Update all env files and templates\ndotenv-checker --fix\n# Preview changes without writing to disk\ndotenv-checker --fix --dry-run\n# Create a backup before making changes\ndotenv-checker --fix --backup"
- "Existing keys, local values, and custom comments are never overwritten."
- "dotenv-checker returns exit code 0 when all environments are valid, and exit code 1 when discrepancies are found"
