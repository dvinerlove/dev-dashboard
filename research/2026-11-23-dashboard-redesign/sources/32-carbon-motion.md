# IBM Carbon Design System — Motion overview

- URL: https://carbondesignsystem.com/elements/motion/overview/ (final: https://www.carbondesignsystem.com/building-blocks/foundations/motion/overview)
- Publisher: IBM Carbon (official design system docs)
- Tier: L1
- Source class: official-docs
- Fetched: 2026-11-23 (full page)

## Key verbatim quotes

- Two modes: "Productive motion creates a sense of efficiency and responsiveness, while remaining subtle and out of the way." — used for "button states, dropdowns, revealing additional information, or rendering data tables". Expressive = rare, significant moments (alerts, notifications).
- Duration tokens (verbatim):
  - `duration-fast-01` — "Micro-interactions such as button and toggle" — 70ms
  - `duration-fast-02` — "Micro-interactions such as fade" — 110ms
  - `duration-moderate-01` — "Micro-interactions, small expansion, short distance movements" — 150ms
  - `duration-moderate-02` — "Expansion, system communication, toast" — 240ms
  - `duration-slow-01` — "Large expansion, important system notifications" — 400ms
  - `duration-slow-02` — "Background dimming" — 700ms
- Micro-interaction target: "Do micro-interactions fall within a static duration ranging from 90–120 ms?"
- Easing (productive): standard cubic-bezier(0.2, 0, 0.38, 0.9); entrance cubic-bezier(0, 0, 0.38, 0.9); exit cubic-bezier(0.2, 0, 1, 0.9). Expressive adds (0.4, 0.14, ...). "Strictly linear movement appears unnatural."
- Duration scales with distance: "the larger the change in distance (traveled) or size (scaling) of the element, the longer the animation takes."
- Restraint: "The best interface motion may go unnoticed... If [your motion is] frequently noticed by average users... consider removing or minimizing it." Always provide reduced-motion/static alternatives.
