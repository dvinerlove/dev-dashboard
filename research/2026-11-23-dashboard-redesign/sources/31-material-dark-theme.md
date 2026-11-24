# Material Design 2 — Dark theme guideline

- URL: https://m2.material.io/design/color/dark-theme.html
- Publisher: Google / Material Design (official guideline)
- Tier: L1
- Source class: official-docs
- Fetched: 2026-11-23 (full page)
- Note: M3 dark-theme page is JS/shadow-DOM walled (blocked); M2 page is canonical for elevation-overlay math and remains authoritative.

## Key verbatim quotes

- "A dark theme displays dark surfaces across the majority of a UI."
- "Use dark grey – rather than black – to express elevation and space in an environment with a wider range of depth."
- "The recommended dark theme surface color is #121212."
- "At higher levels of elevation, components express depth by displaying lighter surface colors" — via semi-transparent white overlay; "Elevation overlay transparencies range from 0% for the lowest level to 16% for the highest level."
- Overlay table (verbatim): 00dp 0% | 01dp 5% | 02dp 7% | 03dp 8% | 04dp 9% | 06dp 11% | 08dp 12% | 12dp 14% | 16dp 15% | 24dp 16%.
- Contrast: "Dark surfaces and 100% white body text have a contrast level of at least 15.8:1"; "Dark theme surfaces must be dark enough to display white text... This ensures that body text passes WCAG's AA standard of at least 4.5:1 when applied to surfaces at the highest (and lightest) elevation."
- Saturation: "A dark theme should avoid using saturated colors, as they don't pass WCAG's accessibility standard of at least 4.5:1... Saturated colors also produce optical vibrations against a dark background, which can induce eye strain."
- Accent restraint: "Apply limited color accents in dark theme UIs, so the majority of space is dedicated to dark surfaces."
- "Don't use light glows in place of dark shadows to express elevation."
- Branded surfaces: overlay the brand color at low opacity over #121212 (e.g. #1F1B24 = #121212 + 8% primary).
- "Dark grey surfaces also reduce eye strain, as light text on a dark grey surface has less contrast than light text on a black surface."
