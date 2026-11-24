# Qt — Qt Style Sheets Reference
- URL: https://doc.qt.io/qt-6/stylesheet-reference.html
- Publisher: Qt (doc.qt.io) — official documentation
- Tier: L1 | Fetched: 2026-11-23 | Worker: pyqt6 (Q3)

Key verbatim quotes:

1. The property set is a closed list (no transition/transform/box-shadow/filter/animation properties exist in it):
"This section lists all the properties supported by Qt Style Sheets." — supported set covers box model, colors, fonts, borders, images, positions, Qt-specific extras (image*, opacity*, spacing*, selection-color*, widget-animation-duration*, etc.).

2. border-radius — supported on nearly all interactive widgets, per-corner variants exist:
"The border-radius clips the element's background."
"This property is supported by QAbstractItemView subclasses, QAbstractSpinBox subclasses, QCheckBox, QComboBox, QFrame, QGroupBox, QLabel, QLineEdit, QMenu, QMenuBar, QPushButton, QRadioButton, QSplitter, QTextEdit, and QToolTip." (plus border-top-left-radius etc.)
(NOT in list: QScrollBar/QSlider handles are styled via sub-controls which do accept border/border-radius per box model.)

3. Pseudo-state list (all supported): :hover, :pressed, :disabled, :enabled, :checked, :unchecked, :indeterminate, :focus, :selected, :read-only, :editable, :default, :flat, :on, :off, :open, :closed, :active, :window, plus positional (:first/:last/:middle/:only-one/:next-selected/:previous-selected) and orientation (:horizontal/:vertical).

4. QLabel limitation:
"Supports the box model. Does not support the :hover pseudo-state."

5. Plain QWidget limitation — the famous custom-widget gotcha:
"[QWidget] Supports only the background, background-clip and background-origin properties. If you subclass from QWidget, you need to provide a paintEvent for your custom QWidget as below: void CustomWidget::paintEvent(QPaintEvent *) { QStyleOption opt; opt.initFrom(this); QPainter p(this); style()->drawPrimitive(QStyle::PE_Widget, &opt, &p, this); }"
(For Python/PyQt: `opt.initFrom(self)` + `self.style().drawPrimitive(QStyle.PE_Widget, opt, p, self)` — same mechanism.)

6. opacity* property — tooltips only:
"The opacity for a widget. Possible values are from 0 (transparent) to 255 (opaque). For the moment, this is only supported for tooltips."

7. widget-animation-duration* (since Qt 5.10) — only controls style-hint animations, not state transitions:
"How much an animation should last (in milliseconds). A value equal to zero means that the animations will be disabled. If this property is not specified, it defaults to the value specified by the current style for the SH_Widget_Animation_Duration style hint."

8. Palette-role colors inside QSS:
"QPushButton { color: palette(dark); }" — PaletteRole values: alternate-base, accent, base, bright-text, button, button-text, dark, highlight, highlighted-text, light, link, link-visited, mid, midlight, placeholder-text, shadow, text, tooltip-base, tooltip-text, window, window-text.

9. Sub-control inventory relevant to control-panel UI: ::handle, ::add-line, ::sub-line, ::add-page, ::sub-page (QScrollBar); ::item (QMenu/QComboBox/QListView); ::indicator (QCheckBox/QRadioButton/QMenu); ::separator (QMenu/QToolBar); ::drop-down/::down-arrow (QComboBox); ::section (QHeaderView); ::tab/::pane/::tab-bar (QTabWidget); ::groove/::
