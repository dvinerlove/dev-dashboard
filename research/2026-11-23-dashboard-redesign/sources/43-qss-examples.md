# Qt — Qt Style Sheets Examples
- URL: https://doc.qt.io/qt-6/stylesheet-examples.html
- Publisher: Qt (doc.qt.io) — official documentation
- Tier: L1 | Fetched: 2026-11-23 | Worker: pyqt6 (Q3)

Key verbatim quotes:

1. The scrollbar all-or-nothing rule (THE scroll-area styling pitfall):
"The QScrollBar can be styled using its subcontrols like handle, add-line, sub-line, and so on. Note that if one property or sub-control is customized, all the other properties or sub-controls must be customized as well."
(Same sentence repeated on stylesheet-customizing page for "complex widgets such as QComboBox and QScrollBar".)

2. Slim modern scrollbar is achievable in pure QSS — example sets `QScrollBar:horizontal { height: 15px; margin: 0px 20px 0 20px; }` with `::handle { min-width: 20px; }`, buttons repositioned/hidden via ::add-line/::sub-line width + subcontrol-position/subcontrol-origin + `position: absolute`; `add-page/sub-page { background: none; }` makes the groove transparent. Arrows can be removed or replaced with images.

3. Partial-rule trap on QPushButton:
"We have made a request that cannot be satisfied using the native styles alone (for example, the native Windows theme engine doesn't let us specify the background color of a button). Therefore, the button is rendered using style sheets. We haven't specified any values for border-width and border-style, so by default we obtain a 0-pixel wide border of style none." → flat, borderless button unless you specify the complete look yourself.

4. Dynamic properties = the recommended state-flag mechanism:
"*[mandatoryField="true"] { background-color: yellow }"
"This means that every widget whose `mandatoryField` Qt property is set to true would have a yellow background."
(PyQt6 equivalent: `w.setProperty("mandatoryField", True)` — but selector re-evaluation requires repolish; see KDAB note 44.)

5. QMenu full styling demonstrated:
"QMenu::item { padding: 2px 25px 2px 20px; border: 1px solid transparent; } QMenu::item:selected { border-color: darkblue; background: rgba(100, 100, 100, 150); } QMenu::separator { height: 2px; background: lightblue; margin-left: 10px; margin-right: 5px; }" — rgba() with alpha works in QSS colors; ::indicator, ::icon:checked, ::right-arrow all styleable.

6. QAbstractScrollArea: `background-attachment: scroll|fixed` controls whether a background image scrolls with content or stays fixed to viewport.
