# Qt — High DPI
- URL: https://doc.qt.io/qt-6/highdpi.html
- Publisher: Qt (doc.qt.io) — official documentation
- Tier: L1 | Fetched: 2026-11-23 | Worker: pyqt6 (Q3)

Key verbatim quotes:

1. Windows DPI awareness is correct out of the box in Qt 6:
"Windows defines several DPI Awareness levels, which applications set to opt-in to high-DPI features. Qt 6 is Per-Monitor DPI Aware V2 by default." — per-monitor scaling on Windows needs no code in PyQt6.

2. Scale model:
"The application operates in device-independent pixels, which are then mapped to the physical pixels of the display via a scale factor, known as the device pixel ratio."

3. Fractional-scaling caveat (125%/150% displays):
"Integer scale factors (for example, 1.0 or 2.0) are preferred for best results. 'Rounding' the scale factor to 25% increments can also give good results. Setting the scale factor or DPI to the exact physical display DPI may not give good visual results due to the fractional scaling involved. If the application suffers from visual artifacts in this scenario, it can use QGuiApplication::setHighDpiScaleFactorRoundingPolicy() to limit the scale factors it sees."

4. Env controls:
"QT_SCALE_FACTOR_ROUNDING_POLICY | Sets the scale factor rounding policy... Supported values: Round * PassThrough (default)"
"QT_SCALE_FACTOR=2 ./myapp" — global scale for debugging.
