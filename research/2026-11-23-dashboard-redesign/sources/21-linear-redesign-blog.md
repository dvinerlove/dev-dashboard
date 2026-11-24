# Linear — "How we redesigned the Linear UI (part II)"

- URL: https://linear.app/blog/how-we-redesigned-the-linear-ui (final: https://linear.app/now/how-we-redesigned-the-linear-ui)
- Publisher: Linear (official engineering/design blog, March 2024)
- Tier: L2 (vendor-authored but primary account of their own system)
- Source class: vendor-authored
- Fetched: 2026-11-23 (full page via r.jina.ai)

## Key verbatim quotes

- Goal: "We've adjusted the sidebar, tabs, headers, and panels to reduce visual noise, maintain visual alignment, and increase the hierarchy and density of navigation elements."
- Elevation method: "Karri mostly worked with opacities of black and white during his explorations, which really helped him get results quickly and helped me understand the relationship he had in mind between the elements and their respective elevation and hierarchy."
- Color space: "we rebuilt the system for generating custom themes in Linear, using the LCH color space instead of HSL. LCH has the benefit that it's perpetually uniform, meaning a red and a yellow color with lightness 50 will appear roughly equally light to the human eye."
- Theme model: "instead of having to define 98 specific variables for each theme, we defined three: base color, accent color, and contrast."
- Contrast-as-input: "the theme generation system also supports a contrast variable which defines how contrasty a theme should be. This allows us to automatically include super high-contrast themes for users who need it for accessibility reasons."
- Neutral chrome: "limiting how much chrome (blue in our case) was used in the calculations applied to our color system. The contrast of the content has also been improved by making our text and neutral icons darker in light mode and lighter in dark mode."
- Type: "We started using Inter Display to add more expression to our headings while maintaining their readability and kept using regular Inter for the rest of the text elements."
- Process: 3 designers, ~6 weeks, feature flag → private beta → staged rollout. Electron app + browser, so "previous/next navigation buttons, history, and tabs needed to be easily removable."
