# PyQt-Fluent-Widgets — button.py source (how polished PyQt widgets actually work)
- URL: https://raw.githubusercontent.com/zhiyiYo/PyQt-Fluent-Widgets/master/qfluentwidgets/components/widgets/button.py
- Publisher: GitHub — library source code (the de-facto benchmark for "modern polished" Qt Widgets UI)
- Tier: L2 | Fetched: 2026-11-23 | Worker: pyqt6 (Q3)

What the code shows (verbatim snippets):

1. Hybrid approach — QSS for base, custom painting for the polished parts:
`FluentStyleSheet.BUTTON.apply(self)` in __init__ (theme QSS files applied per-widget), then state details drawn manually in paintEvent with QPainter antialiasing.

2. Hover tracked manually + repaint, not QSS :hover for the fancy parts:
```python
def enterEvent(self, e):
    self.isHover = True
    self.update()

def leaveEvent(self, e):
    self.isHover = False
    self.update()
```

3. paintEvent does the visual states with per-pixel alpha control:
```python
painter = QPainter(self)
painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
if not self.isEnabled():
    painter.setOpacity(0.3628)
elif self.isPressed:
    painter.setOpacity(0.786)
```
and per-state colors computed in code, e.g.
`if self.isHover: filledColor = tintColor(QColor(255, 255, 255, 11) if isDarkTheme() else QColor(0, 0, 0, 15))`

4. Animatable QColor properties — the smooth-hover mechanism:
`lightTextColor = pyqtProperty(QColor, getLightTextColor, setLightTextColor)`
`darkTextColor = pyqtProperty(QColor, getDarkTextColor, setDarkTextColor)`
— pyqtProperty(QColor) makes the color a Qt property targetable by QPropertyAnimation; the library also imports its own animation helpers (`from ...common.animation import TranslateYAnimation`) for press translation effects.

Takeaway: the most-polished open-source PyQt widget set does NOT get its look from QSS alone — QSS supplies base theming while state layering, icon tinting, hover/press visuals and animations are done in Python paintEvent + pyqtProperty + Qt animation classes.
