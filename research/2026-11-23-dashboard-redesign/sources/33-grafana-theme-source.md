# Grafana — palette.ts + createColors.ts (dark theme source)

- URLs:
  - https://raw.githubusercontent.com/grafana/grafana/main/packages/grafana-data/src/themes/palette.ts
  - https://raw.githubusercontent.com/grafana/grafana/main/packages/grafana-data/src/themes/createColors.ts
- Publisher: Grafana Labs (grafana/grafana, main branch)
- Tier: L1 (shipped monitoring-UI theme source)
- Source class: repo
- Fetched: 2026-11-23 (full files)

## Verbatim palette values (palette.ts)

Gray ramp: `gray05: '#111217', gray10: '#181b1f', gray15: '#22252b', gray20: '#2c2f35', gray25: '#383b42', gray30: '#44474e' ... gray95: '#f4f5f5'`
Dark-mode accents: `blueDarkMain: '#3d71d9', blueDarkText: '#6e9fff', redDarkMain: '#d10e5c', redDarkText: '#ff5286', greenDarkMain: '#1a7f4b', greenDarkText: '#6ccf8e', orangeDarkMain: '#ff9900', orangeDarkText: '#fbad37', purpleDarkMain: '#C27AFF', purpleDarkText: '#D4A0FF'`

## Verbatim dark theme construction (createColors.ts, class DarkColors)

- Base: `whiteBase = '204, 204, 220'` — all neutrals derived from ONE slightly-blue off-white via alpha.
- Borders are alpha, not hex: `weak: rgba(...,0.12), medium: rgba(...,0.2), strong: rgba(...,0.30)`.
- Text: `primary: rgb(204,204,220), secondary: rgba(...,0.65), disabled: rgba(...,0.61), link: blueDarkText`.
- Backgrounds: `canvas: gray05 (#111217), page: gray10 (#181b1f), primary: gray10, secondary: gray15 (#22252b), elevated: gray15` — comment: "in dark themes [elevated] has a brighter shade to help give it contrast against the primary background."
- Action states (alpha fills): `hover: rgba(...,0.16), selected: rgba(...,0.12), focus: rgba(...,0.16), disabledBackground: rgba(...,0.04), disabledOpacity: 0.38, hoverOpacity: 0.08`.
- Status roles: `error.main redDarkMain / error.text redDarkText`, `success.main greenDarkMain / text greenDarkText`, `warning.main orangeDarkMain / text orangeDarkText` — i.e. darker "main" for fills, brighter "text" variant for text-on-dark.
- `contrastThreshold = 3`, `hoverFactor = 0.03`, `tonalOffset = 0.15`.
