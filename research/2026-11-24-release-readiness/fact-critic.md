# fact-critic (docs vs code) — verdicts

Method: every named feature/config-key/command/version/path/URL verified
against core.py, backend.py, dashboard.py, mcp_server.py, platform_impl.py,
storage.py, process_tree.py, test_upgrades.py, spec, workflows, theme.ts,
OnboardingDialog.tsx.

## Verdicts (before parent fixes)
| File | Verdict |
|---|---|
| README.md | FIX — M1 + nits |
| docs/release-notes-v0.9.0.md | FIX — M1 |
| README_MCP.md | SHIP |
| packaging/* | SHIP |
| .agents/product-marketing.md | SHIP |

## Must-fixes found & fixed
- M1: onboarding scanner suggests PROJECTS (projects_config.json via
  /api/projects/add), not services — fixed in README:58 + release-notes:21
- M2: _t/i18n_check.py was NOT git-tracked — `_t/` whole-dir ignore makes
  `!` negation dead. Fixed: `_t/` → `_t/*` + negation; file now tracked.

## Verified clean (sampled)
Probe fields, backoff/circuit constants, depends_on semantics, all
settings.json defaults, env masking + ?reveal=1, 7 MCP tools by name,
tray/autorun/single-instance/--web/portable mode/DEVDASH_DATA_DIR/api.port,
Job Objects vs killpg, LAN flag, SQLite scope, six themes, RU/EN, CSRF+Host
allowlist+127.0.0.1, version 0.9.0 consistency (8 places), asset names vs
release.yml, CI badge→ci.yml, Python 3.10+/Node 20+, winget+scoop schemas.

## Nits fixed
- env-mask doc accuracy, note-key description, pywebview POSIX wording,
  Codex TOML caveat, api.port marker mention in README_MCP,
  scoop `shortcuts` Start-Menu entry added.

## Nits left (documented)
- mcp_server.py serverInfo.version 1.0.0 ≠ product 0.9.0 (legal, own version)
- LOCALAPPDATA-unset Windows fallback → BASE_DIR undocumented (trivial)
- issues kind list in MCP docs is partial (matches mcp_server's own text)
