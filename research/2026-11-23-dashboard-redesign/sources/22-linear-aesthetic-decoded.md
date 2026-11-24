# The Linear Aesthetic, Decoded: Tokens, Density, and Keyboard-First UX

- URL: https://www.buildmvpfast.com/blog/linear-aesthetic-tokens-density-keyboard-first-ux-2026
- Publisher: buildmvpfast.com (independent analysis, published 2026-07-03)
- Tier: L3 (third-party teardown; values marked "approximate" but concrete)
- Source class: independent-secondary
- Fetched: 2026-11-23 (full page)

## Key verbatim quotes (concrete values)

- Canvas: "Linear's canvas is not pure black. It sits at roughly `#010102`, a near-black with a faint blue cast, and surfaces step up from there in tiny lightness increments: about `#0f1011`, `#141516`, then `#18191a`. Depth comes from those background shifts, not from drop shadows."
- Accent: "a lavender-blue around `#5E6AD2`, internally nicknamed Magic Blue. It shows up on the brand mark, the focus ring, and the primary button. Nowhere else."
- Text/borders: "Text runs through four steps from near-white `#f7f8f8` down through a muted `#8a8f98` to a faint `#62666d`, and borders are hairlines near `#23252a`."
- Contrast warning: "The faintest tone, `#62666d`, sits around 3.6:1 on the near-black canvas, under the WCAG AA minimum of 4.5:1 for body text. It works for a timestamp or a decorative label."
- Density: "Linear's list rows are built around 13px body text with a line height near 1.4, laid out on a 4px spacing grid, which yields compact rows in the 32 to 36 pixel range."
- Density prescription: `body { font-size: 13px; line-height: 1.45; } .row-compact { padding-block: 6px; padding-inline: 12px; }`
- Keyboard: Cmd+K palette built on cmdk; "never hide an action behind a hover state. Hover is a bonus, not a requirement."
- A11y: "WebAIM's 2024 audit found contrast failures on 83.6% of home pages"; "Roughly 47% of people have some astigmatism, and light text on dark backgrounds is genuinely harder for them to focus."
- Trend note: "roughly half of [recent SaaS products] wear the same outfit: a near-black sidebar, a single purple accent, tight rows of small text, and a command palette that pops open on Cmd+K."
