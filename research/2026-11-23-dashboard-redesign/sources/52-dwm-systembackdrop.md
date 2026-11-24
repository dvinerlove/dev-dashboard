# Microsoft Learn — DWM_SYSTEMBACKDROP_TYPE enumeration (dwmapi.h)
- URL: https://learn.microsoft.com/en-us/windows/win32/api/dwmapi/ne-dwmapi-dwm_systembackdrop_type
- Publisher: Microsoft Learn — official Win32 API reference
- Tier: L1 | Fetched: 2026-11-23 | Worker: pyqt6 (Q3)

Key verbatim quotes:

1. What it does:
"Flags for specifying the system-drawn backdrop material of a window, including behind the non-client area." — set via DwmSetWindowAttribute (attribute DWMWA_SYSTEMBACKDROP_TYPE, see note 53).

2. Mica via one enum value:
"DWMSBT_MAINWINDOW — Draw the backdrop material effect corresponding to a long-lived window behind the entire window bounds. For Windows 11, this corresponds to Mica in its default variant."

3. Acrylic:
"DWMSBT_TRANSIENTWINDOW — ... For Windows 11, this corresponds to Desktop Acrylic, also known as Background Acrylic, in its brightest variant."

4. Mica Alt:
"DWMSBT_TABBEDWINDOW — ... For Windows 11, this corresponds to Mica in its alternate variant (Mica Alt)."

5. OS requirement:
"Minimum supported client | Windows 11 Build 22621" — no Mica/Acrylic-backdrop on Windows 10 via this API (Win10 acrylic requires the undocumented SetWindowCompositionAttribute or Win32 blur-behind; this is what PyQt-Frameless-Window's "Win10 acrylic" does).
