# Qt — QFont (font features, since Qt 6.7)
- URL: https://doc.qt.io/qt-6/qfont.html
- Publisher: Qt (doc.qt.io) — official documentation
- Tier: L1 | Fetched: 2026-11-23 | Worker: pyqt6 (Q3)

Key verbatim quotes:

1. OpenType feature access exists — tabular numbers (`tnum`), stylistic sets, etc. are reachable from PyQt6 when Qt ≥ 6.7:
"[since 6.7] void QFont::setFeature(QFont::Tag tag, quint32 value)"
"Applies an integer value to the typographical feature specified by tag when shaping the text. This provides advanced access to the font shaping process, and can be used to support font features that are otherwise not covered in the API."
"The feature is specified by a tag, which is typically encoded from the four-character feature name in the font feature map." → `f.setFeature(QFont.Tag.fromString("tnum"), 1)` enables tabular figures in fonts that have them.

2. Semantics:
"A zero value means the feature is disabled, and a non-zero value means it is enabled. For certain font features, however, it may have other interpretations. For example, when applied to the `salt` feature, the value is an index that specifies the stylistic alternative to use."

3. Interplay with defaults:
"By default, Qt will enable and disable certain font features based on other font properties. In particular, the `kern` feature will be enabled/disabled depending on the kerning() property... all ligature features (liga, clig, dlig, hlig) will be disabled if a letterSpacing() is applied" — setFeature overrides these defaults.

4. Related API (all since 6.7): unsetFeature(), featureTags(), featureValue(), isFeatureSet(), clearFeatures().
