# copy-critic (anti-slop pass) — verdicts

Method: writing-guidelines + copy-editing skills, banned-word grep (zero hits
outside explicit "avoid" lists), AI-cliché patterns, emoji/claim audit.
All concrete claims cross-checked against code.

## Verdicts (before parent fixes)
| File | Verdict |
|---|---|
| README.md | FIX — 1 defect |
| docs/release-notes-v0.9.0.md | SHIP |
| .agents/product-marketing.md | SHIP |
| README_MCP.md | SHIP |
| packaging/README.md | SHIP |
| packaging/winget/*.yaml | SHIP |
| packaging/scoop/dev-dashboard.json | SHIP |

## Fixed by parent
- README:20 env-mask regex understated (listed 5 of 9 patterns; a user could
  conclude AWS_SESSION_TOKEN stays visible) → now lists full key-name pattern
- "store submission is pending" → "submission PRs are pending" (README+notes)
- "never had a live run" → "never been run on a real machine" (×3)
- "Microsoft Edge WebView2" → "WebView2 Runtime"
- Portable-mode row: "If any of ... already exists"
- "lightweight" MCP description left as-is (backed by stdlib-only line)

## Noted, kept
- Tagline "One window for everything running on your dev machine" — accepted
  tagline license; body copy is precise.
- Em-dashes follow the consistent "lead — detail" bullet convention.
