# KDAB — Say No to Qt Style Sheets
- URL: https://www.kdab.com/say-no-to-qt-style-sheets/
- Publisher: KDAB (David Faure) — Qt consultancy blog; explicitly linked from official Qt docs as the QStyle-side comparison
- Tier: L3 | Fetched: 2026-11-23 | Worker: pyqt6 (Q3)

Key verbatim quotes (comparison table, QSS column):

1. QSS ignores programmatic styling:
"Calling setFont/setPalette: No effect (rather unexpected), even if the style sheet has nothing to do with colors."
"Changing the system colors: No effect — the styled widgets don't adapt to the new colors."

2. Hard ceiling:
"Achieving 100% of the styling requirements: Style sheets allow you to do a number of things, but not everything. If there's no support for a specific customization, there's no solution."
"(Note that style sheets are implemented as an internal QStyle subclass.)"

3. Doesn't compose with real styles:
"Stylesheets do not mix well with QProxyStyles or other QStyle subclasses. This makes it even harder to gradually move away from the stylesheet solution. One specific example for proof: a stylesheet that simply sets a background color will lead to many of the style's methods not being called because the style sheet style does many things on its own (ex: CT_SpinBox)."

4. Dynamic-property selectors are NOT reactive:
"Selectors on properties do not get reevaluated when the properties change, forcing hacks such as reset of a style sheet with the associated cost." — i.e., `w.setProperty()` then `style().unpolish(w); style().polish(w)` hack needed.

5. Performance specifics:
"Each call to setStyleSheet triggers parsing, which can be slow if done too often (e.g., when creating 50 buttons, each one calling setStylesheet("…")). The usual solution is a single application-wide stylesheet."
"Each reparenting triggers clearing the stylesheet rules cache and recalculating everything."

6. No modularity:
"Actual management of the stylesheet data does not scale (no include mechanism, etc.), calling for super-complicated selectors."

Community-corroboration in comments (L4, anecdotal, not load-bearing): a game-tooling dev reports QSS "extract a pretty substantial performance cost in instantiating widgets, but also reparenting widgets"; a commenter notes QSS gives up rounding very small rounded rects (e.g. 1% progress bar → square) where QPainter::drawRoundedRect works — illustrating the fixed-behavior ceiling.
