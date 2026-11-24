# 52 — dotenv-linter README

- URL: https://github.com/dotenv-linter/dotenv-linter (raw README, master)
- Title: dotenv-linter — Lightning-fast linter for .env files. Written in Rust
- Publisher: GitHub / dotenv-linter org (maintained by Evrone). Docs: dotenv-linter.github.io
- Tier: L1 | Source class: vendor-authored | Fetched: 2026-11-24
- ~2.1k stars, Rust binary, language-agnostic. Commands: check / fix / diff.

## Key quotes
- "can **check** / **fix** / **diff** `.env` files for problems that may cause the application to malfunction."
- Available checks (14): "Duplicated key, Ending blank line, Extra blank line, Incorrect delimiter, Key without value, Leading character, Lowercase key, Quote character, Schema violation, Space character, Substitution key, Trailing whitespace, Unordered key, Value without quotes"
- "Can be used on any project regardless of the programming language"
- fix output: "Original file was backed up to: \".env_1601378896\"" — auto-backup before writing.
- diff: "`dotenv-linter diff .env .env.example` ... `.env is missing keys: BAR` / `.env.example is missing keys: FOO`" — key-set diff only, no values.
- Integrations: reviewdog, GitHub Action (action-dotenv-linter), super-linter, pre-commit.
