# 54 — dotenv-sentinel README

- URL: https://github.com/MrLouisWright/dotenv-sentinel (raw README, main); site mrlouiswright.github.io/dotenv-sentinel
- Title: dotenv-sentinel
- Publisher: GitHub / MrLouisWright (repo author). npm package, Node 18+, GitHub Action @v1
- Tier: L1 | Source class: vendor-authored | Fetched: 2026-11-24

## Key quotes
- "`dotenv-sentinel` finds every `.env`, `.env.*` and `*.env` file in a project and checks three things: **completeness** ... **secret hygiene** ... and **git exposure** ... **Values are never printed**: every secret is masked."
- completeness: "variables missing compared with `.env.example` or a JSON schema, empty required values, wrong types"
- secret hygiene: "`changeme`, `<your-key>`, short secrets, debug mode in production files, real credentials left in example files"
- git exposure: "env files that are tracked, not covered by `.gitignore`, or present anywhere in history"
- example alternates: "(or `.env.sample`, `.env.template`, `.env.dist`, `<file>.example`, or `--example`)"
- schema types: "`string`, `number`, `integer`, `boolean`, `url`, `email`, `port`, `json`, `enum`), `pattern`, `enum`, `minLength`, `secret`"
- Rules table (severity): committed-env critical; example-contains-secret critical; known-secret/env-in-history/env-not-ignored/weak-secret/missing-var high; empty-required/type-mismatch/short-secret/debug-in-production/duplicate-key/invalid-line medium; insecure-url/unquoted-space/undefined-reference/extra-var low; missing-example info.
- config `.dotenv-sentinel.json`: "`severity` changes the severity of any rule, or turns it `off`. `allow` suppresses findings. Each entry needs a `rule` ... and a `reason` ... When `expires` (YYYY-MM-DD) has passed, the finding comes back together with an `allow-expired` finding"
- output: "--format text|json|sarif|markdown"; "--fail-on critical|high
