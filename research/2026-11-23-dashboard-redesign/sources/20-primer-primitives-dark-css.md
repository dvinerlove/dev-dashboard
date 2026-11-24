# Primer Primitives — dark.css (GitHub design tokens, dark theme)

- URL: https://unpkg.com/@primer/primitives@latest/dist/css/functional/themes/dark.css
- Publisher: GitHub (primer/primitives, official design-token build output)
- Tier: L1 (official token source; the shipped CSS GitHub itself uses)
- Source class: official-docs / repo
- Fetched: 2026-11-23 (full file, 1929 lines)

## Key verbatim token values (copied verbatim from the CSS)

Surfaces:
- `--bgColor-default: #0d1117; /** Default background color for pages and main content areas */`
- `--bgColor-muted: #151b23; /** Muted background for secondary content areas and subtle grouping */`
- `--bgColor-disabled: #212830;` / `--bgColor-emphasis: #3d444d; /** High-emphasis dark background */`
- `--overlay-backdrop-bgColor: #21283066;`

Text:
- `--fgColor-default: #f0f6fc; /** Default text color for primary content and headings */`
- `--fgColor-muted: #9198a1; /** Muted text for secondary content */`
- `--fgColor-disabled: #656c76;`
- `--fgColor-accent: #4493f8;` (link = accent)

Status text:
- `--fgColor-success: #3fb950;` `--fgColor-danger: #f85149;` `--fgColor-attention: #d29922;` `--fgColor-severe: #db6d28;` `--fgColor-done: #ab7df8;`

Borders (hairline-first; shadows mostly `0 0 0 0` for buttons):
- `--borderColor-default: #3d444d;`
- `--borderColor-translucent: #ffffff26; /** Semi-transparent border for overlays... no bgColor-translucent counterpart exists by design. */`
- `--borderColor-success-emphasis: #238636;` `--borderColor-danger-emphasis: #da3633;` `--borderColor-accent-muted: #388bfd66;`

Muted-status bg pattern (status pill anatomy = dark tinted bg + bright fg):
- `--bgColor-danger-muted: #f851491a;` `--bgColor-attention-muted: #bb800926;` `--bgColor-success`-family labels: `--label-green-bgColor-rest: #122117;` `--label-green-fgColor-rest: #41b445;` `--label-red-bgColor-rest: #3c0614`-family

Controls:
- `--control-bgColor-rest: #212830; --control-bgColor-hover: #262c36; --control-bgColor-active: #2a313c;`
- `--control-transparent-bgColor-hover: #656c7633; --control-transparent-bgColor-selected: #656c7633;`
- `--header-bgColor: #151b23f2;` (translucent header over content)

ANSI/terminal palette (useful for console widgets): `--ansi-green: #3fb950`, `--ansi-red: #ff7b72`, `--ansi-yellow: #d29922`, `--ansi-blue: #58a6ff`.
