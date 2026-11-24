# Microsoft Learn — DWMWINDOWATTRIBUTE enumeration (dwmapi.h)
- URL: https://learn.microsoft.com/en-us/windows/win32/api/dwmapi/ne-dwmapi-dwmwindowattribute
- Publisher: Microsoft Learn — official Win32 API reference
- Tier: L1 | Fetched: 2026-11-23 | Worker: pyqt6 (Q3)

Key verbatim quotes:

1. Dark title bar from a single call — the #1 "dark control panel" trick on Windows:
"DWMWA_USE_IMMERSIVE_DARK_MODE — Use with DwmSetWindowAttribute. Allows the window frame for this window to be drawn in dark mode colors when the dark mode system setting is enabled. For compatibility reasons, all windows default to light mode regardless of the system setting. The pvAttribute parameter points to a value of type BOOL. TRUE to honor dark mode for the window, FALSE to always use light mode."

2. Rounded window corners:
"DWMWA_WINDOW_CORNER_PREFERENCE — Use with DwmSetWindowAttribute. Specifies the rounded corner preference for a window. The pvAttribute parameter points to a value of type DWM_WINDOW_CORNER_PREFERENCE."

3. Backdrop material hook:
"DWMWA_SYSTEMBACKDROP_TYPE — Use with DwmGetWindowAttribute or DwmSetWindowAttribute. Retrieves or specifies the system-drawn backdrop material of a window, including behind the non-client area. The pvAttribute parameter points to a value of type DWM_SYSTEMBACKDROP_TYPE."

All three are plain `DwmSetWindowAttribute(hwnd, attr, &value, sizeof(value))` calls on dwmapi.dll — callable from PyQt6 via `ctypes.windll.dwmapi` (no pywin32 needed), using `int(widget.winId())` as HWND.
