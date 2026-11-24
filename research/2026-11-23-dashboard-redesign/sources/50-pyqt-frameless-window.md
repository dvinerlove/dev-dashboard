# PyQt-Frameless-Window (zhiyiYo) — README
- URL: https://github.com/zhiyiYo/PyQt-Frameless-Window
- Publisher: GitHub repo — library README (vendor-authored docs for own project)
- Tier: L2 | Fetched: 2026-11-23 | Worker: pyqt6 (Q3)

Key verbatim quotes:

1. Proof that the full modern Windows chrome is reachable from PyQt/PySide:
"A cross-platform frameless window based on PyQt5" (PySide2/PySide6/PyQt6 branches exist). Features list: "Moving / Stretching / Window shadow / Window animation / Win11 snap layout / Win10 acrylic blur / Win11 mica blur / Win7 Aero blur / MacOS blur / Disable screen capture".

2. Implementation dependency = raw win32 only:
"| Win32 | pywin32 |" — the Windows effects are done through DWM/win32 calls (DwmSetWindowAttribute family), which can equally be done via ctypes with no dependency at all.

3. API shape:
"To use the frameless window, you only need to inherit `FramelessWindow` or `FramelessMainWindow`" — provides "a default custom title bar" that can be rewritten.

4. Known gotchas (from the README Notes):
"Moving the acrylic window on Win10 may get stuck. At present, there is no good solution. Maybe you can disable the acrylic effect when moving the window."
"Snap layout is not enabled by default."

Relevance: this is the reference implementation behind QFluentWidgets' chrome — demonstrates frameless + custom titlebar + native shadow/snap/Mica/Acrylic are all achievable from Python without any Qt-side support; Qt's own Qt::FramelessWindowHint loses resize/shadow/snap, hence the win32 route.
