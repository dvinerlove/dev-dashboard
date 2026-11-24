# Qt — QVariantAnimation Class
- URL: https://doc.qt.io/qt-6/qvariantanimation.html
- Publisher: Qt (doc.qt.io) — official documentation
- Tier: L1 | Fetched: 2026-11-23 | Worker: pyqt6 (Q3)

Key verbatim quotes:

1. QColor interpolation is built in — this is what makes smooth hover-color transitions possible in code:
"Not all QVariant types are supported. Below is a list of currently supported QVariant types:" — list includes Int, UInt, Double, Float, QLine(F), QPoint(F), QSize(F), QRect(F), and **QColor**.

2. Mechanics — drive anything from valueChanged:
"QVariantAnimation will interpolate the property of the target object and emit valueChanged(). To react to a change in the current value you have to reimplement the updateCurrentValue() virtual function or connect to said signal."
In PyQt6: connect `valueChanged` to a slot that stores the QColor and calls `update()`; paint it in a custom paintEvent — the standard smooth-hover pattern.

3. Custom interpolation possible:
"If you need to interpolate other variant types, including custom types, you have to implement interpolation for these yourself... register an interpolator function" / "reimplement interpolated(), which returns interpolation values for the value being interpolated."

4. Easing:
"setEasingCurve()... default, a linear easing curve is used" — QEasingCurve types (InOutCubic etc.) available.
