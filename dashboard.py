"""Dev Dashboard — pywebview (WebView2) + локальный HTTP API.
UI: собранный React-фронт из frontend/dist, отдаётся локальным API (порт
из настроек api_port, default 4850).
Запуск: python dashboard.py  (старое QtQuick-ядро — bridge.py + ui/Main.qml)"""
import os
import sys
import threading

# windowed-exe (PyInstaller --noconsole): sys.stdout/stderr = None, а
# pythonnet/clr_loader падает на print при старте — WebView2 не инициализируется
# и окно остаётся пустым. Подменяем на devnull.
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

import urllib.request

import backend as be
import platform_impl as pi
from core import Dashboard


def _tray_image():
    from PIL import Image
    if os.path.exists(be.ICON_FILE):
        return Image.open(be.ICON_FILE)
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    from PIL import ImageDraw
    d = ImageDraw.Draw(img)
    d.ellipse((8, 8, 56, 56), fill="#5E81F4")
    return img


def main():
    if pi.IS_WIN:
        # свой AppUserModelID — иначе Windows группирует окно с другими
        # python-процессами и игнорирует иконку в панели задач
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "DevDashboard.App")
        except Exception:
            pass

    # single-instance: вторая копия поднимает окно первой и выходит
    if not pi.acquire_single_instance("DevDashboard"):
        try:
            urllib.request.urlopen(urllib.request.Request(
                "http://127.0.0.1:%d/api/show-window"
                % be.load_settings()["api_port"],
                data=b"{}"), timeout=3)
        except Exception:
            pass
        return

    dash = Dashboard()
    dash.start()

    # --web: только HTTP API + фронт, без окна/pywebview/трея —
    # дашборд живёт в браузере (и на macOS/Linux без pywebview)
    if "--web" in sys.argv:
        print(f"Dev Dashboard -> http://127.0.0.1:{dash.api_port}/")
        try:
            threading.Event().wait()
        except KeyboardInterrupt:
            pass
        dash.stop()
        return

    import webview

    # мост для кнопок окна в кастомном топбаре: × = в трей,
    # как и системный крестик — сервисы живут дальше.
    # ВНИМАНИЕ: ссылка на Window — только в _-атрибуте, иначе pywebview
    # рекурсивно обходит её граф (winforms Form) и вешает весь процесс.
    class _WinCtl:
        _win = None
        _maximized = False

        def window_drag_start(self):
            """Нативный drag за топбар: ReleaseCapture +
            WM_NCLBUTTONDOWN/HTCAPTION на UI-потоке формы (Invoke) —
            WebView2 держит mouse-capture, ReleaseCapture из другого
            потока no-op. Один вызов на mousedown, дальше окно таскает
            сама Windows — без JS→Python на каждый mousemove."""
            try:
                from System import Func, Type
                from ctypes import wintypes as wt

                def go():
                    u = ctypes.windll.user32
                    u.ReleaseCapture()
                    sm = u.SendMessageW
                    sm.argtypes = (wt.HANDLE, wt.UINT,
                                   wt.WPARAM, wt.LPARAM)
                    sm(self._win.native.Handle.ToInt32(), 0x00A1, 0x0002, 6)

                self._win.native.Invoke(Func[Type](go))
            except Exception:
                pass

        def window_set_bg(self, color):
            """Фон формы и WebView2 под текущую тему — полоса при
            ресайзе/загрузке сливается с фоном приложения."""
            try:
                import re
                if not re.fullmatch(r"#[0-9A-Fa-f]{6}", str(color)):
                    return
                from System import Action
                from System.Drawing import ColorTranslator

                def go():
                    c = ColorTranslator.FromHtml(color)
                    self._win.native.BackColor = c
                    wv = getattr(self._win.native, "webview", None)
                    if wv is not None:
                        wv.DefaultBackgroundColor = c
                self._win.native.Invoke(Action(go))
            except Exception:
                pass

        def window_minimize(self):
            self._win.minimize()

        def window_toggle_maximize(self):
            (self._win.restore if self._maximized else self._win.maximize)()

        def window_close(self):
            self._win.hide()

    if pi.IS_WIN:
        ctl = _WinCtl()
        # background_color=bg приложения (--bg-base): иначе при ресайзе
        # видна белая полоса — дефолтный фон формы/WebView2 до перерисовки
        win = webview.create_window(
            "Dev Dashboard", f"http://127.0.0.1:{dash.api_port}/",
            width=1240, height=780, min_size=(920, 600),
            easy_drag=False, js_api=ctl,
            background_color="#0B0D11")
        ctl._win = win

        # зона ресайза внутри окна: хит-тесты над webview уходят в его чайлд
        # (чужой процесс, не сабклассится), поэтому webview утапливается на
        # RING px через Padding формы — кольцо это реальная поверхность
        # формы в цвет темы, и наш WM_NCHITTEST отдаёт оттуда HT-коды
        RING = 4

        def _set_pad(l, t, rr, b):
            """BeginInvoke — padding внутри события maximize/restore
            дедлокит layout с WebView2, асинхронно применяется после."""
            try:
                from System import Func, Type
                from System.Windows.Forms import Padding

                def go():
                    win.native.Padding = Padding(l, t, rr, b)
                win.native.BeginInvoke(Func[Type](go))
            except Exception:
                pass

        def _on_max(*_):
            ctl._maximized = True
            _set_pad(0, 0, 0, 0)                    # maximized — контент вплотную

        def _on_res(*_):
            ctl._maximized = False
            _set_pad(RING, RING, RING, RING)
        win.events.maximized += _on_max
        win.events.restored += _on_res

        # Канонный DWM frameless (Chrome/VS Code): стили окна стандартные
        # (Sizable) — тень, скруглённые углы, Aero Snap и невидимый
        # size-бордер даёт сам DWM. WM_NCCALCSIZE→0: клиент = весь рект
        # окна → заголовок и рамка не рисуются совсем (NC-области нет,
        # WM_NCPAINT нечего красить — отсюда и нет белой рамки).
        def _custom_frame(*_):
            try:
                from ctypes import wintypes as wt
                u = ctypes.windll.user32
                hwnd = win.native.Handle.ToInt32()
                if not hwnd:
                    return

                class _NCP(ctypes.Structure):
                    _fields_ = [("rgrc", wt.RECT * 3),
                                ("_lppos", ctypes.c_void_p)]

                u.SetWindowLongPtrW.argtypes = (wt.HWND, ctypes.c_int,
                                                ctypes.c_void_p)
                u.SetWindowLongPtrW.restype = ctypes.c_void_p
                u.CallWindowProcW.argtypes = (ctypes.c_void_p, wt.HWND,
                                              wt.UINT, wt.WPARAM, wt.LPARAM)
                u.CallWindowProcW.restype = ctypes.c_ssize_t
                WNDPROC = ctypes.WINFUNCTYPE(
                    ctypes.c_ssize_t, wt.HWND, wt.UINT,
                    wt.WPARAM, wt.LPARAM)
                state = {"old": None}

                @WNDPROC
                def _proc(h, msg, wp, lp):
                    if msg == 0x0083 and wp:       # WM_NCCALCSIZE
                        if u.IsZoomed(h):
                            # maximized: окно свешено за края экрана на
                            # толщину рамки — втягиваем клиент в видимую
                            # область, иначе контент обрезан по краям
                            p = ctypes.cast(lp, ctypes.POINTER(_NCP))
                            fx = u.GetSystemMetrics(32) + u.GetSystemMetrics(92)
                            fy = u.GetSystemMetrics(33) + u.GetSystemMetrics(92)
                            r0 = p.contents.rgrc[0]
                            r0.left += fx; r0.top += fy
                            r0.right -= fx; r0.bottom -= fy
                        return 0                    # клиент = весь рект окна
                    if msg == 0x0084:               # WM_NCHITTEST
                        if u.IsZoomed(h):
                            return 1                # HTCLIENT
                        x = ctypes.c_short(lp & 0xFFFF).value
                        y = ctypes.c_short((lp >> 16) & 0xFFFF).value
                        r = wt.RECT()
                        u.GetWindowRect(h, ctypes.byref(r))
                        l, t = x - r.left, y - r.top
                        rr, b = r.right - x, r.bottom - y
                        # невидимый системный бордер + RING px кольца формы
                        fx = u.GetSystemMetrics(32) + u.GetSystemMetrics(92) \
                            + RING
                        fy = u.GetSystemMetrics(33) + u.GetSystemMetrics(92) \
                            + RING
                        C = fx + 10                 # углы — пошире для диагонали
                        el, et = l < fx, t < fy
                        er, eb = rr < fx, b < fy
                        code = 1                    # HTCLIENT
                        if el and t < C:
                            code = 13               # HTTOPLEFT
                        elif er and t < C:
                            code = 14               # HTTOPRIGHT
                        elif el and b < C:
                            code = 16               # HTBOTTOMLEFT
                        elif er and b < C:
                            code = 17               # HTBOTTOMRIGHT
                        elif el:
                            code = 10               # HTLEFT
                        elif er:
                            code = 11               # HTRIGHT
                        elif et:
                            code = 12               # HTTOP
                        elif eb:
                            code = 15               # HTBOTTOM
                        return code
                    return u.CallWindowProcW(state["old"], h, msg, wp, lp)

                def _install():
                    state["old"] = u.SetWindowLongPtrW(hwnd, -4, _proc)
                    # пересчёт NC-области уже через наш proc — окно сразу
                    # открывается в финальной геометрии, без сдвига на
                    # первом WM_NCACTIVATE
                    u.SetWindowPos(hwnd, 0, 0, 0, 0, 0,
                                   0x0001 | 0x0002 | 0x0004 | 0x0020)
                try:
                    win.native.Invoke(_install)
                except Exception:
                    _install()
                ctl._nc_proc = _proc              # держим ссылку — GC иначе убьёт

                # 1px стекла сверху → DWM продолжает рисовать нативную
                # тень вокруг кастомного кадра
                class _MARGINS(ctypes.Structure):
                    _fields_ = [("cxLeft", ctypes.c_int),
                                ("cxRight", ctypes.c_int),
                                ("cyTop", ctypes.c_int),
                                ("cyBottom", ctypes.c_int)]
                ctypes.windll.dwmapi.DwmExtendFrameIntoClientArea(
                    hwnd, ctypes.byref(_MARGINS(0, 0, 1, 0)))
                corner = ctypes.c_int(2)          # DWMWCP_ROUND
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, 33, ctypes.byref(corner), 4)  # CORNER_PREFERENCE
                ctl.window_set_bg("#0B0D11")
            except Exception:
                pass
        win.events.shown += _custom_frame

        # стартовый padding: во время shown layout webview дедлокится
        # с инициализацией; к моменту loaded контрол живой.
        win.events.loaded += lambda *_: _set_pad(RING, RING, RING, RING)
    else:
        # macOS/Linux: нативный chrome, без Win32-хуков;
        # window-* js_api отсутствует → вызовы фронта тихий no-op
        win = webview.create_window(
            "Dev Dashboard", f"http://127.0.0.1:{dash.api_port}/",
            width=1240, height=780, min_size=(920, 600),
            easy_drag=False, background_color="#0B0D11")

    # --- трей ---
    import pystray
    quitting = {"v": False}

    def show(*_):
        win.restore()
        win.show()
    dash.show_cb = show

    def quit_app(*_):
        quitting["v"] = True
        win.destroy()

    icon = pystray.Icon(
        "devdashboard", _tray_image(), "Dev Dashboard",
        pystray.Menu(
            pystray.MenuItem(be.tr("TRAY_OPEN"), show, default=True),
            pystray.MenuItem(be.tr("TRAY_QUIT"), quit_app)))
    dash.tray_cb = lambda t, m: icon.notify(m, t)
    threading.Thread(target=icon.run, daemon=True).start()

    # закрытие окна — сворачивание в трей, не выход
    def on_closing():
        if quitting["v"]:
            return True
        win.hide()
        return False
    win.events.closing += on_closing

    try:
        webview.start(icon=be.ICON_FILE)
    finally:
        dash.stop()
        icon.stop()


if __name__ == "__main__":
    main()
