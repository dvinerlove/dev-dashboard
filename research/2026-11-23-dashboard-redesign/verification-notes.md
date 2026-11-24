# Verification notes — dashboard-redesign

**Checked: 119/119 claims.** All 54 unique cited URLs re-fetched live (r.jina.ai, direct fetch for raw/API hosts, direct MS-docs fetch where jina was auth-walled). Every verbatim/numeric quote was matched against the re-fetched page (markdown-normalized), then claim support was assessed.

## Verdict counts

| verdict | count |
|---|---|
| verified | 118 |
| verified at corrected URL | 1 (F030) |
| misquoted / unsupported / contradicted / outdated / source-blocked | 0 |

No claim needs to be dropped. Corrections and caveats below.

## Corrections

- **F030** — quote not on cited `laragon.org/docs/operations`; found verbatim on canonical `https://laragon.org/docs` → verified, URL corrected in ledger.
- **F009** — page says `"Nothing silent"` (double quotes); stored quote used single quotes. Punctuation-only, content exact.
- **F019** — page renders `Open ↗□ Stop● running 2h`; stored quote inserts spaces between glyphs. Whitespace-only.
- **F041** — all hex values exact; the stored numeric "quote" embeds a `/** */` comment that does not exist in the CSS file. Values unaffected.
- **F115** — quote verified; the claim's parenthetical "windows11 style underneath (Qt 6.12+)" was not in the fetched excerpt — minor unverified elaboration, claim itself stands.

## Tier / source_class audit

Mislabeled `source_class` (independence inflation):
- **F019** portdoc.dev, **F029** laragon.org, **F031** servbay.com — vendor's own sites tagged `independent-secondary` → should be `vendor-authored`.
- **F051–F053** linear.app blog, **F070–F071** raycast.com blog — `unknown` → `vendor-authored`.
- Tiers otherwise honest: doc.qt.io / MS Learn / primer & grafana raw sources correctly L1; buildmvpfast and bitdoze correctly L3.

## Cluster independence

- **Palette/elevation/status numeric claims are multi-origin and solid**: Primer dark.css, Grafana createColors.ts/palette.ts, Radix gray-dark.css, Material spec — 4 independent sources converging (plus Linear teardown L3). Spot-checks vs second sources passed: Primer values confirmed via jsdelivr CDN, Radix via jsdelivr, Grafana via v11.3.0 tagged file (all values identical).
- **Each competitor = one cluster, as expected**: localhost 11 claims (one repo + vendor site), runbay 7 (one README), portdoc 6 (one repo + vendor site), docker 5 (vendor docs). Load-bearing IA patterns are only safe via the synthesis claims F037/F038, which genuinely span 4 origins — sound.
- **qss-* cluster set is single-origin by nature** (doc.qt.io is the authority for Qt capability facts). Only external corroboration of the limits is KDAB (F096). Acceptable, but know the Widgets-vs-QML decision rests almost entirely on Qt's own docs.
- **motion cluster is single-source**: F068/F069 both Carbon. The 70–240ms durations are one design system's values — corroborate (e.g. Apple HIG, Material motion) before baking into the UI.
- **F050 density numbers** (13px / 32–36px rows / 4px grid) rest on ONE L3 blog teardown of Linear — single-source load-bearing.
- **F032/F034** (Uptime Kuma layout/complaints) are one L3 blog relaying reddit — anecdote-grade.
- **F074 synthesis** is an interpretation over 4+ verified clusters — correctly multi-origin.

## Numeric spot-checks performed

1. Primer dark.css `#0d1117`, `#4493f8`, `#f851491a` — confirmed on jsdelivr (independent of unpkg fetch).
2. Radix gray-dark `#111111`/`#3a3a3a`/`#eeeeee` — confirmed on jsdelivr.
3. Grafana `gray05 #111217`, `gray15 #22252b`, `redDarkText #FF5286`, `greenDarkText #6CCF8E` — confirmed on v11.3.0 tag (different release than fetched `main`).
4. Carbon durations 70/110/150/240/400/700ms + 90–120ms band — verbatim on live page.
5. Uptime Kuma issue reaction counts 787/538/383/349 — exact match on live GitHub API.
