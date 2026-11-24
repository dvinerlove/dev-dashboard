# Qt — QPropertyAnimation Class
- URL: https://doc.qt.io/qt-6/qpropertyanimation.html
- Publisher: Qt (doc.qt.io) — official documentation
- Tier: L1 | Fetched: 2026-11-23 | Worker: pyqt6 (Q3)

Key verbatim quotes:

1. What it animates:
"QPropertyAnimation interpolates over Qt properties. As property values are stored in QVariants, the class inherits QVariantAnimation, and supports animation of the same meta types as its super class."

2. Works on widget properties directly — official example animates a button's `pos`:
"To make it possible to animate a property, it must provide a setter (so that QPropertyAnimation can set the property's value). Note that this makes it possible to animate many of Qt's widgets."
Example code: `QPropertyAnimation *anim = new QPropertyAnimation(button, "pos", this);` — applies equally to geometry, windowOpacity, size, pos, and custom pyqtProperty declarations.

3. Default duration:
"The animation changes the property propertyName on target. The default duration is 250ms."

4. Missing start value = animates from current:
"if a start value is not set, the property will start at the value it had when the QPropertyAnimation instance was created" — convenient for reversible hover in/out animations.

5. Groups:
"For complex animations that, for instance, contain several objects, QAnimationGroup is provided... QParallelAnimationGroup."
