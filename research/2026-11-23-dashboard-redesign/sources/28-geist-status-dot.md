# Vercel Geist Design System — Status Dot component

- URL: https://vercel.com/geist/status-dot
- Publisher: Vercel (official design system docs)
- Tier: L1
- Source class: official-docs
- Fetched: 2026-11-23 (full page)

## Key verbatim quotes

- States: "`state` accepts `QUEUED | BUILDING | READY | ERROR | CANCELED | DELETED`" — labels rendered sentence-cased: Queued / Building / Error / Ready / Canceled.
- Animation rule: "The dot animates while `BUILDING` or `QUEUED` and goes static once the deployment reaches a terminal state. Don't add a separate spinner alongside it."
- Polling rule: "Don't flash the color through every transitional state on a polling tick; only update when the readyState changes."
- Timing context: "Pair with RelativeTimeCard when timing matters (`Building · 12s ago`); the dot alone doesn't convey duration."
- Label discipline: "Don't wrap the dot in extra prose like `Status: Ready`. The label already names the state."
- Accessibility: "Color is not the only signal: every state ships with a distinct title and label so colorblind users get the same information." Also: mark dot `aria-hidden` when adjacent text already names the state.
- For non-deployment statuses "use a Badge with the canonical state vocabulary instead of repurposing the dot"; for health with a number use Gauge; in-flight work with knowable total → Progress.
