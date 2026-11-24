# Qt — Styling Approaches for Qt Widgets
- URL: https://doc.qt.io/qt-6/qtwidgets-styling-approaches.html
- Publisher: Qt (doc.qt.io) — official documentation
- Tier: L1 | Fetched: 2026-11-23 | Worker: pyqt6 (Q3)

Key verbatim quotes:

1. Official positioning of QSS:
"Style sheets override individual visual properties with CSS-like rules. They are a tool for prototyping and for small, local adjustments, not for the production look of an application."

2. Performance cost — every widget through the wrapper engine:
"**Every affected widget is drawn through the style sheet engine.** When a style sheet is set, QWidget::style() returns a style sheet style that wraps the underlying style. For each widget it matches the selectors against the widget's class, object name, properties, and state, computes the rendering rules, and caches them per widget. The memory and processing cost grows with the number of widgets and rules."

3. Theme switching via setStyleSheet is explicitly discouraged:
"**Changing a style sheet repolishes everything it applies to.** Each call to QApplication::setStyleSheet() discards the caches and repolishes every widget in the application, which recomputes fonts, palettes, geometry, and size hints and can visibly flicker. Don't build theme switching on style sheets."

4. Partial styling kills native look:
"**A partial rule discards the native look.** When a rule requests something the native style cannot honor, such as a background color for a QPushButton, the style sheet engine draws the whole element itself, without the native decoration. You then have to specify borders, padding, and every state yourself."

5. Selector fragility + precedence:
"**Selectors couple the design to implementation details.** Rules match class names, object names, and property values. Renaming an object or replacing a widget class silently stops the rule from matching."
"**Style sheets win over programmatic settings.** A style sheet overrides fonts, palettes, and item colors set with functions such as QWidget::setFont() or QTreeWidgetItem::setBackground()."

6. Per-widget setStyleSheet is a perf trap; recommended pattern:
"**Don't assemble style sheets from C++ strings.** A style sheet set on a widget is parsed once for every widget it's set on... each call to QWidget::setStyleSheet() repolishes the widget and all its children, even when the string didn't change... Instead, express the difference with a selector on an object name or a Qt property in the one style sheet."

7. Theme-safe colors + scalable units:
"**Don't hard-code colors.** ... Use `palette(window)`, `palette(text)`, and the other palette roles so that the style sheet follows the application palette, including a dark color scheme."
"**Don't size everything in pixels.** ... Use `em` and `ex` lengths for paddings, margins, and sizes that should follow the font, and `pt` for font sizes."

8. Production alternative named:
"StyleKit is a declarative styling system... QStyleKitStyle is available since Qt 6.12. StyleKit is a Qt Labs module, and its API may change between Qt releases." — QStyle/QProxyStyle/QCommonStyle subclass is the recommended production mechanism.
