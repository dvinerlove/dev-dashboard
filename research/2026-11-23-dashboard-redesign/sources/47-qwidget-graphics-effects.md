# Qt — QWidget::setGraphicsEffect + QGraphicsDropShadowEffect
- URLs:
  - https://doc.qt.io/qt-6/qwidget.html (setGraphicsEffect section)
  - https://doc.qt.io/qt-6/qgraphicseffect.html
  - https://doc.qt.io/qt-6/qgraphicsdropshadoweffect.html
- Publisher: Qt (doc.qt.io) — official documentation
- Tier: L1 | Fetched: 2026-11-23 | Worker: pyqt6 (Q3)

Key verbatim quotes:

1. The box-shadow workaround — QGraphicsDropShadowEffect properties:
"The QGraphicsDropShadowEffect class provides a drop shadow effect." Properties: "blurRadius : qreal", "color : QColor", "offset : QPointF", "xOffset/yOffset : qreal".
"By default, the drop shadow is a semi-transparent dark gray (QColor(63, 63, 63, 180)) shadow, blurred with a radius of 1 at an offset of 8 pixels towards the lower right."
NOTE: blurRadius/offset are Qt properties → animatable with QPropertyAnimation (e.g. shadow grows on hover).

2. One effect per widget, hard limit:
"Sets effect as the widget's effect. If there already is an effect installed on this widget, QWidget will delete the existing effect before installing the new effect." → cannot stack shadow + opacity + blur.

3. Applies to whole subtree:
"**Note:**This function will apply the effect on itself and all its children." → a shadow on a card re-renders every child through the effect pipeline each repaint; keep effects on small leaf containers.

4. OpenGL widgets excluded:
"**Note:**Graphics effects are not supported for OpenGL-based widgets, such as QGLWidget, QOpenGLWidget and QQuickWidget."

5. Rendering is pixmap-based (explains the cost):
Effects "operate between the source... and the destination device"; custom effects call "sourcePixmap() to get a pixmap of the graphics effect source" — i.e. the widget is rendered offscreen then composited every repaint. Four standard effects: QGraphicsBlurEffect, QGraphicsDropShadowEffect, QGraphicsColorizeEffect, QGraphicsOpacityEffect (the QWidget-opacity workaround; QWidget has windowOpacity only for top-level windows).
