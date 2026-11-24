# Vercel Geist Design System — Colors

- URL: https://vercel.com/geist/colors
- Publisher: Vercel (official design system docs)
- Tier: L1 (official docs)
- Source class: official-docs
- Fetched: 2026-11-23 (full page)

## Key verbatim quotes

- Structure: "There are 10 color scales in the system. P3 colors are used on supported browsers and displays." Scales: Gray, Gray alpha, Blue, Red, Amber, Green, Teal, Purple, Pink.
- Gray vs alpha: "Gray — for text, icons, fills, borders, and dividers by default. Gray-alpha — only when the background should show through, such as in shadows or overlays."
- Border discipline: "Do: Keep the divider inside the border." / "Avoid: Overlapping alpha borders make intersections stand out."
- Shadows: "Do: Transparent shadows blend with the background." / "Avoid: Opaque shadows leave a gray halo."
- Backgrounds: "There are two background colors for pages and UI components... use Background 1—especially when color is being placed on top of the background. Background 2 should be used sparingly."
- Role mapping (Radix-style steps):
  - "Colors 1–3: Component Backgrounds" — 1 default, 2 hover, 3 active. "On smaller UI elements like badges, you can use Color 2 or Color 3 as the background."
  - "Colors 4-6: Borders" — 4 default border, 5 hover border, 6 active border. "Use solid gray by default. Use the matching gray-alpha step only when the edge needs to blend with its surface."
  - "Colors 7-8: High Contrast Backgrounds"
  - "Colors 9-10: Text and Icons" — 9 "Secondary text and icons", 10 "Primary text and icons".
