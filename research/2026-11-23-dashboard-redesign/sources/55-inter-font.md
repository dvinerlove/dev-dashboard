# Inter — official site (rsms.me/inter)
- URL: https://rsms.me/inter/
- Publisher: Rasmus Andersson (font author site — vendor-authored)
- Tier: L2 | Fetched: 2026-11-23 | Worker: pyqt6 (Q3)

Key verbatim quotes:

1. Coverage incl. Cyrillic:
"The Inter typeface family features over 2000 glyphs covering 147 languages." — the site's glyph listing includes the full Cyrillic block (U+0400–U+04FF: Ё U+0401, Й U+0419, all Russian letters, plus extended Cyrillic like U+049A, U+04A2).
"Weights range from a delicate thin 100 all the way up to a heavy 900... Optical size ranges from 'text' to 'display' and there is a true italic variant."
Variable axes: "Variable axis opsz [14–32]" and "Variable axis wght [100–900]".

2. Tabular numbers — the dashboard-metric feature:
"Many OpenType features are provided as well, including contextual alternates..., slashed zero..., tabular numbers, and much more."
"tnum Tabular numbers — Fixed-width numbers are useful for tabular data, where comparing columns across rows is desired."
"Tabular figures are excellent for tables of numeric data. `tnum` enables an entire set of dedicated glyphs that have the same width across all weights."

3. Full feature list (usable via QFont::setFeature on Qt ≥6.7): calt, case, cpsp, dlig, frac, numr, ordn, pnum, salt, sinf, ss01–ssxx, subs, sups, tnum, zero, cv01–cv13.

Caveat for the project: Inter is not bundled with Windows — must be installed or shipped (Inter is OFL-licensed → embeddable via QFontDatabase.addApplicationFont).
