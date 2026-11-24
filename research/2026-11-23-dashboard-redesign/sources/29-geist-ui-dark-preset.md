# geist-ui dark theme preset (components/themes/presets/dark.ts)

- URL: https://raw.githubusercontent.com/geist-org/geist-ui/master/components/themes/presets/dark.ts
- Publisher: geist-org/geist-ui (open-source component library carrying forward the original Vercel/Zeit design language)
- Tier: L3 (community repo — Vercel-derived tokens, real shipped values)
- Source class: repo / independent-secondary
- Fetched: 2026-11-23 (full file)

## Key verbatim token values

- Surface ladder (accents are inverted dark→light): `accents_1: '#111', accents_2: '#333', accents_3: '#444', accents_4: '#666', accents_5: '#888', accents_6: '#999', accents_7: '#eaeaea', accents_8: '#fafafa'`
- Canvas/text: `background: '#000', foreground: '#fff', secondary: '#888', border: '#333'`
- Status: `error: '#e00', errorLight: '#ff1a1a', success: '#0070f3' (Vercel blue doubles as success link color), successLight: '#3291ff', warning: '#f5a623', warningLight: '#f7b955', link: '#3291ff', violet: '#7928ca', violetLight: '#8a63d2', alert: '#ff0080'`
- The signature Vercel elevation pattern — borders instead of shadows, verbatim:
  - `dropdownBoxShadow: '0 0 0 1px #333'`
  - `shadowSmall: '0 0 0 1px #333'`
  - `shadowMedium: '0 0 0 1px #333'`
  - `shadowLarge: '0 0 0 1px #333'`
  - `portalOpacity: 0.75`
- Note: `success`/`error` names in this file follow the original Zeit mapping where blue = positive action; modern Geist site uses distinct green/red scales.
