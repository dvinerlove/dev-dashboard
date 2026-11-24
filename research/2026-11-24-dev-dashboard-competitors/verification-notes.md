# Verification notes — 2026-11-24 dev-dashboard-competitors

Scope: 131 load-bearing claims verified (all of Q1, env-pattern set, Windows
competitors, SmartScreen/signing, update mechanisms, pricing, user-request
evidence, pier/Portlivo detection, PM2/Herd/ServBay overlap). Each cited URL
re-fetched live (curl; r.jina.ai fallback not needed; GitHub API via `gh` for
repo metadata). Quote matching: HTML/markdown artifacts stripped, whitespace
collapsed; punctuation-only drift (ol/li numbering, ' vs ", trailing period)
treated as faithful. Numbers checked character-exact.

## Verdict counts
- verified: 128 | misquoted: 3 | unsupported/contradicted/outdated/blocked: 0

## Misquoted (salvageable)
- **F041** (PortDoc detection): README supports project grouping, framework
  labels, exposure labels, stale hints, safe-stop, raw sockets/JSON export —
  but "verifies that the port was released" and "self-protection" do not
  appear anywhere. Drop or re-source those two sub-details.
- **F076** (PM2 restart surface): recorded quote stitches a comment line
  ("# Set memory threshold for app reload") that is not on the page between
  the option rows. Every option itself (--max-memory-restart 200M,
  --restart-delay, --cron, --no-autorestart) is present and exact.
- **F096** (Herd pricing): page shows **€69/€99 per year**, not $69/$99.
  Numbers match; currency differs (site geo-localizes). Report should not
  state "$" without noting the localization.

## Corrected URLs (content verified at canonical location)
- F138–F142 (pier detection rules): cited repo root; quotes verified
  character-exact in raw file `Sources/PierCore/Identify/IdentifyProject.swift`
  and `IdentifyInfra.swift` on main.
- F149 (pier.yml): verified in raw `docs/pier-yml.md`.

## Tier / cluster audit
- F016/F017 (getlocalhost MCP pages): tier corrected L2→L1 — vendor docs are
  primary for own-product facts.
- Cluster independence: no vendor-curated content mislabeled as independent.
  Product-feature claims are inherently single-cluster (each tool's own site);
  numeric facts corroborated via second source where required.
- **Single-source load-bearing**: F183 (EV bypass removal) rests solely on one
  Microsoft Learn doc — it is L1-primary so acceptable, flagged. F161
  (AI-agent orphan pain as demand) is vendor marketing but corroborated by
  independent primary sources F162–F164 (claude-code issues).

## Numeric spot-checks (second source)
- F025: GitHub API — 7★/0 forks/created 2026-10-22/MIT/Rust/v0.6.0 2026-11-14: exact.
- F043: GitHub API — portdoc license null, 12★, pushed 2026-07-27: exact.
- F155: HN page — "204 points by raskrebs | 77 comments": exact.
- F186: MS Learn table — $9.99/mo, $150–300/yr, $400+/yr: exact.
- F204/F205: Portlivo $8.99→$19.99/$39.99/$59.99, Rungeist $14.99: exact.

## Env-pattern synthesis (F129/F151)
Key-diff pattern (.env vs .env.example → missing=error / undocumented=warning /
empty=warning, non-destructive sync, JSON/exit codes for CI) confirmed verbatim
in all five tools' READMEs — the "standard pattern" claim is load-bearing sound.
