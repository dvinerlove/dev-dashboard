# 53 — envguard README

- URL: https://github.com/BLemine/envguard (raw README, main)
- Title: envguard — Keep your .env files honest.
- Publisher: GitHub / BLemine (repo author). Go CLI, v1.0.0, brew + go install + prebuilt binaries (win amd64 too)
- Tier: L1 | Source class: vendor-authored | Fetched: 2026-11-24

## Key quotes
- "checks missing, undocumented, and empty environment variables, syncs local files from examples, scans YAML and properties config for env placeholders, audits git history for leaked secrets, and encrypts/decrypts env files for safer team sharing"
- check output legend: "✗ STRIPE_SECRET_KEY missing from .env / ⚠ DEBUG_MODE in .env but not in .env.example"; "`check` exits with code `1` for missing or empty keys. Undocumented keys produce warnings only and do not fail the check."
- sync: "Adds missing keys from `.env.example` into your `.env` with empty values. **Existing keys are never overwritten.**"
- validate: "Perfect for CI pipelines. Exits with code 1 if any required key is missing or empty." — `envguard validate --required=DATABASE_URL,API_KEY,JWT_SECRET`
- audit: "Walks history reachable from all local refs, including merge commits, and flags committed `.env` files plus lines matching common secret patterns such as API keys, tokens, passwords, private keys, Slack tokens, GitHub tokens, and Stripe keys."
- audit limits: "Template filenames ending in `.example`, `.sample`, or `.template` are excluded from the env-file check, but their contents still undergo pattern matching."
- scan-config: "Extracts `${VAR}` and `${VAR:default}` placeholders from YAML and `.properties` config files" (Spring Boot application.yml / Quarkus application.properties); `--strict` fails if required vars missing from supplied env file. "a placeholder scanner, not a complete Spring Boot or Quarkus configuration resolver".
- encrypt/decrypt: "AES-256-GCM with a key derived from your passphrase via Argon2id"; decrypted output chmod 0600.
