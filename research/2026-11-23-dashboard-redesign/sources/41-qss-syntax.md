# Qt — The Style Sheet Syntax
- URL: https://doc.qt.io/qt-6/stylesheet-syntax.html
- Publisher: Qt (doc.qt.io) — official documentation
- Tier: L1 | Fetched: 2026-11-23 | Worker: pyqt6 (Q3)

Key verbatim quotes:

1. Selector support = full CSS2 + Qt extensions:
"Qt Style Sheets support all the selectors defined in CSS2." — plus sub-controls (`::drop-down`) and pseudo-states (`:hover`), dynamic-property selectors (`*[mandatoryField="true"]` equivalent via property selectors).

2. Pseudo-states are instant, chainable, negatable:
"Pseudo-states can be negated using the exclamation operator."
"Pseudo-states can be chained, in which case a logical AND is implied."
Example: `QComboBox::drop-down:hover { image: url(dropdown_bright.png) }` — pseudo-states combine with sub-controls.

3. No `!important`:
"Be aware that Qt currently doesn't implement `!important`."

4. No CSS-style inheritance:
"By default, when using Qt Style Sheets, a widget does **not** automatically inherit its font and color setting from its parent widget."
(The QPushButton inside a styled QGroupBox keeps "the system color" unless `QGroupBox, QGroupBox *` selector used.)

5. `qproperty-*` is polish-once — cannot drive state changes/animations:
"**Note:**Use the qproperty syntax with care, as it modifies the widget that is being painted. Also, the qproperty syntax is evaluated only once, which is when the widget is polished by the style. This means that any attempt to use them in pseudo-states such as QPushButton:hover, will not work."
