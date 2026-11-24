# A Technical Deep Dive Into the New Raycast (v2)

- URL: https://www.raycast.com/blog/a-technical-deep-dive-into-the-new-raycast
- Publisher: Raycast official blog, 2026-05-14
- Tier: L2 (vendor-authored engineering post)
- Source class: vendor-authored
- Fetched: 2026-11-23 (full page)

## Key verbatim quotes (desktop-feel conventions — most relevant to PyQt)

- Native bar: "we're not a web app with some native hooks sprinkled on top. We're a native app that uses web for its UI."
- "No `cursor: pointer` on interactive controls. Desktop apps don't do this. It's small, but it immediately signals 'this is a website.'"
- "No hover highlights on most controls. On macOS, buttons and list items don't highlight on hover the way they do on the web."
- "Settings open in a separate native window, not a modal or a side panel."
- "Popovers and tooltips render as native windows, not as DOM elements inside the WebView. They can extend beyond the window bounds, just like native popovers do."
- Custom controls rationale: "We almost never reached for standard UI components. They weren't built for the kind of keyboard-first, power-user workflows we cared about, so we built our own. Every list row, every shortcut, every default behavior was handled by us."
- Perf craft: prewarm emoji font; keep WebView frame at expanded size so content is already rendered when window expands; trigger render in requestAnimationFrame before showing window to avoid flicker; unlock 60 FPS cap.
