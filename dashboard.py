"""Dev Dashboard — pywebview (WebView2) + local HTTP API.
UI: built React frontend from frontend/dist, served by the local API (port
from the api_port setting, default 4850).
Run: python dashboard.py  (old QtQuick core — bridge.py + ui/Main.qml)"""
import os
import subprocess
import sys
import threading

# windowed exe (PyInstaller --noconsole): sys.stdout/stderr = None, and
# pythonnet/clr_loader crashes on print at startup — WebView2 never
# initializes and the window stays blank. Substitute devnull.
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

import json
import urllib.error
import urllib.parse
import urllib.request

import backend as be
import platform_impl as pi
from core import Dashboard

_WIN = dict(width=1240, height=780, min_size=(920, 600))
# --minimized: autostart entry uses it — open to taskbar, not in the face
if "--minimized" in sys.argv:
    _WIN["minimized"] = True
_BG = "#0B0D11"  # --bg-base: form background until the WebView repaints


def _tray_image():
    from PIL import Image
    for f in (be.TRAY_ICON_FILE, be.ICON_FILE):
        if os.path.exists(f):
            return Image.open(f)
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    from PIL import ImageDraw
    d = ImageDraw.Draw(img)
    d.ellipse((8, 8, 56, 56), fill="#5E81F4")
    return img


# ---------- CLI companion (no window — talks to the running instance) ----------

_CLI_CMDS = ("status", "services", "projects", "ports",
             "start", "stop", "restart", "kill-port", "scan")


def _api_port():
    """Port of the running dashboard — same chain as the single-instance
    check: the api.port marker → DEVDASH_PORT → configured (4850)."""
    try:
        return int(open(os.path.join(be.DATA_DIR, "api.port"),
                        encoding="ascii").read())
    except (OSError, ValueError):
        pass
    try:
        return int(os.environ.get("DEVDASH_PORT", ""))
    except ValueError:
        pass
    return be.load_settings()["api_port"]


def _api_get(port, path):
    with urllib.request.urlopen(
            f"http://127.0.0.1:{port}{path}", timeout=30) as r:
        return json.loads(r.read() or b"{}")


def _api_post(port, path, body=None):
    """POST JSON -> (http_code, parsed body); HTTPError keeps its code."""
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}{path}",
        data=json.dumps(body or {}).encode(),
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read() or b"{}")
        except Exception:
            return e.code, {}


def _cli(argv):
    """Runs a CLI command against the live API and returns the exit code."""
    try:
        sys.stdout.reconfigure(errors="replace")
    except Exception:
        pass
    port, cmd = _api_port(), argv[0]
    try:
        if cmd == "status":
            r = _api_get(port, "/api/status")
            print(f"services {r['services_up']}/{r['services_total']} up, "
                  f"{r['projects_running']} projects running, "
                  f"{len(r['problems'])} problems")
        elif cmd == "services":
            for r in _api_get(port, "/api/services"):
                print(f"{r['name']:<28} {r['state']}")
        elif cmd == "projects":
            for r in _api_get(port, "/api/projects"):
                print(f"{r['name']:<28} "
                      f"{'running' if r['running'] else 'stopped'}")
        elif cmd == "ports":
            for r in _api_get(port, "/api/ports")["ports"]:
                print(f":{r['port']:<6} {r['proc']:<24} {r['owner'] or '-'}")
        elif cmd in ("start", "stop", "restart"):
            if not argv[1:]:
                print(f"usage: {cmd} NAME", file=sys.stderr)
                return 1
            name = urllib.parse.quote(argv[1], safe="")
            code, r = _api_post(port, f"/api/services/{name}/{cmd}")
            if code == 404:  # not a service — try the same-named project
                code, r = _api_post(port, f"/api/projects/{name}/{cmd}")
            if code != 200:
                print(f"{cmd} {argv[1]}: not found", file=sys.stderr)
                return 1
            print(f"{cmd} {argv[1]}: ok")
        elif cmd == "kill-port":
            try:
                n = int(argv[1])
            except (IndexError, ValueError):
                print("usage: kill-port PORT", file=sys.stderr)
                return 1
            code, r = _api_post(port, "/api/kill-port", {"port": n})
            print(r.get("msg") or ("ok" if r.get("ok") else "failed"))
            return 0 if r.get("ok") else 1
        elif cmd == "scan":
            code, r = _api_post(port, "/api/scan")
            found = r.get("found") or []
            print(f"{len(found)} found")
            for p in found:
                print(f"  {p.get('name')}")
        return 0
    except (urllib.error.URLError, OSError, ValueError) as e:
        print(f"dashboard api unavailable: {e}", file=sys.stderr)
        return 1


def main():
    # first line, before anything can hang — tells bootloader/OS stalls
    # (no line at all) from python-level deaths in the incident log
    be.append_dashboard_log(f"[SYSTEM] start pid={os.getpid()}")
    if pi.IS_WIN:
        # own AppUserModelID — otherwise Windows groups the window with
        # other python processes and ignores the taskbar icon
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "DevDashboard.App")
        except Exception:
            pass

    # single-instance: a second copy raises the first window and exits.
    # Keep the reference: on POSIX flock lives on the file object — GC would drop it
    _SINGLETON = pi.acquire_single_instance("DevDashboard")
    if not _SINGLETON:
        try:  # bound port from the marker; config may not match (fallback)
            port = int(open(os.path.join(be.DATA_DIR, "api.port"),
                            encoding="ascii").read())
        except (OSError, ValueError):
            port = be.load_settings()["api_port"]
        try:
            urllib.request.urlopen(urllib.request.Request(
                f"http://127.0.0.1:{port}/api/show-window",
                data=b"{}"), timeout=3)
        except Exception:
            pass
        be.append_dashboard_log("[SYSTEM] second instance, exiting")
        return

    dash = Dashboard()
    dash.start()

    # --web: HTTP API + frontend only, no window/pywebview/tray —
    # the dashboard lives in the browser (and on macOS/Linux without pywebview)
    if "--web" in sys.argv:
        print(f"Dev Dashboard -> http://127.0.0.1:{dash.api_port}/")
        try:
            threading.Event().wait()
        except KeyboardInterrupt:
            pass
        dash.stop()
        return

    import webview

    # bridge for the window buttons in the custom topbar: × = to tray,
    # same as the system close button — services keep running.
    # WARNING: the Window reference must live only in a _-attribute,
    # else pywebview walks its graph recursively (winforms Form) and hangs.
    class _WinCtl:
        _win = None
        _maximized = False

        def window_drag_start(self):
            """Native topbar drag: ReleaseCapture +
            WM_NCLBUTTONDOWN/HTCAPTION on the form UI thread (Invoke) —
            WebView2 holds mouse capture, ReleaseCapture from another
            thread is a no-op. One call per mousedown, then Windows itself
            moves the window — no JS→Python per mousemove."""
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
            """Form and WebView2 background matching the theme — the stripe
            during resize/load blends into the app background."""
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
        # background_color=app bg (--bg-base): otherwise a white stripe
        # shows on resize — default form/WebView2 background before repaint
        win = webview.create_window(
            "Dev Dashboard", f"http://127.0.0.1:{dash.api_port}/",
            **_WIN, easy_drag=False, js_api=ctl,
            background_color=_BG)
        ctl._win = win

        # resize zone inside the window: hit tests above the webview go to its
        # child (a foreign process, cannot be subclassed), so the webview is
        # sunk by RING px via form Padding — the ring is a real form surface
        # in theme color, and our WM_NCHITTEST returns HT codes from there
        RING = 4

        def _set_pad(l, t, rr, b):
            """BeginInvoke — padding inside the maximize/restore event
            deadlocks the layout with WebView2; applied asynchronously after."""
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
            _set_pad(0, 0, 0, 0)                    # maximized — content flush to edges

        def _on_res(*_):
            ctl._maximized = False
            _set_pad(RING, RING, RING, RING)
        win.events.maximized += _on_max
        win.events.restored += _on_res

        # Canonical DWM frameless (Chrome/VS Code): standard window styles
        # (Sizable) — shadow, rounded corners, Aero Snap and the invisible
        # size border are provided by DWM itself. WM_NCCALCSIZE→0: client = whole
        # window rect → title bar and border are not drawn at all (no NC area,
        # nothing for WM_NCPAINT to paint — hence no white frame).
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
                            # maximized: the window hangs past the screen edges by
                            # the border thickness — pull the client into the
                            # visible area, otherwise content is clipped at edges
                            p = ctypes.cast(lp, ctypes.POINTER(_NCP))
                            fx = u.GetSystemMetrics(32) + u.GetSystemMetrics(92)
                            fy = u.GetSystemMetrics(33) + u.GetSystemMetrics(92)
                            r0 = p.contents.rgrc[0]
                            r0.left += fx; r0.top += fy
                            r0.right -= fx; r0.bottom -= fy
                        return 0                    # client = whole window rect
                    if msg == 0x0084:               # WM_NCHITTEST
                        if u.IsZoomed(h):
                            return 1                # HTCLIENT
                        x = ctypes.c_short(lp & 0xFFFF).value
                        y = ctypes.c_short((lp >> 16) & 0xFFFF).value
                        r = wt.RECT()
                        u.GetWindowRect(h, ctypes.byref(r))
                        l, t = x - r.left, y - r.top
                        rr, b = r.right - x, r.bottom - y
                        # invisible system border + RING px of form ring
                        fx = u.GetSystemMetrics(32) + u.GetSystemMetrics(92) \
                            + RING
                        fy = u.GetSystemMetrics(33) + u.GetSystemMetrics(92) \
                            + RING
                        C = fx + 10                 # corners — wider for diagonal drags
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
                    # NC area already recalculated through our proc — the window
                    # opens straight in final geometry, without a jump on
                    # the first WM_NCACTIVATE
                    u.SetWindowPos(hwnd, 0, 0, 0, 0, 0,
                                   0x0001 | 0x0002 | 0x0004 | 0x0020)
                try:
                    win.native.Invoke(_install)
                except Exception:
                    _install()
                ctl._nc_proc = _proc              # keep the reference — GC would kill it

                # 1px of glass on top → DWM keeps drawing the native
                # shadow around the custom frame
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
                ctl.window_set_bg(_BG)
            except Exception:
                pass
        win.events.shown += _custom_frame

        # initial padding: during shown the webview layout deadlocks
        # with initialization; by loaded the control is alive.
        win.events.loaded += lambda *_: _set_pad(RING, RING, RING, RING)
    else:
        # macOS/Linux: native chrome, no Win32 hooks;
        # window-* js_api absent → frontend calls are a quiet no-op
        win = webview.create_window(
            "Dev Dashboard", f"http://127.0.0.1:{dash.api_port}/",
            **_WIN, easy_drag=False, background_color=_BG)

    # --- tray ---
    import pystray
    quitting = {"v": False}
    quit_evt = threading.Event()

    def show(*_):
        win.restore()
        win.show()
    dash.show_cb = show

    def quit_app(*_):
        quitting["v"] = True
        quit_evt.set()
        win.destroy()
    dash.quit_cb = quit_app  # self-update exits through the same clean path

    def build_menu():
        def svc_items():
            for r in dash.api_services():
                up = r["state"] == "up"
                yield pystray.MenuItem(
                    f"{'▶' if up else '■'} {r['name']}",
                    lambda n=r["name"], up=up:
                        (dash.stop_service if up else dash.start_service)(n),
                    # monitor-only/remote services are shown but not toggled
                    enabled=not (r["monitor_only"] or r["remote"]))

        def prj_items():
            for r in dash.api_projects():
                yield pystray.MenuItem(
                    f"{'▶' if r['running'] else '■'} {r['name']}",
                    lambda n=r["name"], run=r["running"]:
                        (dash.stop_project if run
                         else dash.start_project)(n))

        return pystray.Menu(
            pystray.MenuItem(be.tr("TRAY_OPEN"), show, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(be.tr("TRAY_SERVICES"), pystray.Menu(svc_items)),
            pystray.MenuItem(be.tr("TRAY_PROJECTS"), pystray.Menu(prj_items)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(be.tr("TRAY_QUIT"), quit_app))

    icon = pystray.Icon(
        "devdashboard", _tray_image(), "Dev Dashboard", build_menu())
    dash.tray_cb = lambda t, m: icon.notify(m, t)
    threading.Thread(target=icon.run, daemon=True).start()

    # the win32 backend builds the native menu once at update_menu() — rebuild
    # from the live dashboard state on the probe cadence (~4s)
    def _menu_loop():
        while not quit_evt.wait(4):
            try:
                icon.menu = build_menu()
            except Exception:
                pass
    threading.Thread(target=_menu_loop, daemon=True).start()

    # Ctrl+Alt+D → raise the window (Windows only; skipped if taken)
    hk = {"tid": None}
    if pi.IS_WIN:
        def _hotkey():
            try:
                from ctypes import wintypes
                u = ctypes.windll.user32
                hk["tid"] = ctypes.windll.kernel32.GetCurrentThreadId()
                if not u.RegisterHotKey(None, 1, 0x0001 | 0x0002, ord("D")):
                    return                      # combo already taken
                try:
                    msg = wintypes.MSG()
                    while u.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                        if msg.message == 0x0312:       # WM_HOTKEY
                            show()
                finally:
                    u.UnregisterHotKey(None, 1)
            except Exception:
                pass
        threading.Thread(target=_hotkey, daemon=True).start()

    # closing the window = minimize to tray, not exit
    def on_closing():
        if quitting["v"]:
            return True
        win.hide()
        return False
    win.events.closing += on_closing

    # watchdog: WebView2 init can fail silently (its own renderer processes
    # of the previous instance still holding the user-data lock, pythonnet
    # print crash — both seen in the wild): the form stays dark forever
    # while the API answers fine, so the port-based relaunch verification
    # cannot see it. `loaded` never fires in that state. Self-heal once
    # through the same relaunch helper as self-update; the marker file
    # breaks restart loops and is cleared by the first successful load.
    loaded_ok = threading.Event()
    win.events.loaded += lambda *_: loaded_ok.set()
    wv_marker = os.path.join(be.DATA_DIR, "wv-restart.once")

    def _clear_marker(*_):
        # whenever a load DOES succeed — even after the 40s deadline — the
        # anti-loop marker is stale and must go, otherwise it disables
        # self-healing for all future incidents
        try:
            os.remove(wv_marker)
        except OSError:
            pass
    win.events.loaded += _clear_marker

    def _webview_watchdog():
        if loaded_ok.wait(40):
            return
        if quitting["v"] or quit_evt.is_set():
            return                # user is exiting — never restart behind them
        be.append_dashboard_log("[SYSTEM] webview never loaded in 40s")
        if os.path.exists(wv_marker) or not getattr(sys, "frozen", False):
            return                # already restarted once, or dev mode
        if loaded_ok.wait(2):
            return                # slow load raced past the deadline
        try:
            ps1 = be.write_update_helper(
                sys.executable, os.getpid(), ("cmd", ""),
                os.path.join(be.DATA_DIR, "wv-restart.ps1"), dash.api_port,
                port_file=os.path.join(be.DATA_DIR, "api.port"))
            subprocess.Popen(["powershell", "-NoProfile", "-ExecutionPolicy",
                              "Bypass", "-File", ps1],
                             creationflags=getattr(subprocess,
                                                   "CREATE_NO_WINDOW", 0),
                             close_fds=True)
        except Exception as e:
            be.append_dashboard_log(f"[SYSTEM] watchdog restart failed: {e}")
            return                # no marker — the next incident may retry
        # marker only after the helper is actually running: a failed launch
        # must not permanently disable self-healing
        open(wv_marker, "w").close()
        be.append_dashboard_log("[SYSTEM] restarting once to recover")
        quit_app()
    threading.Thread(target=_webview_watchdog, daemon=True).start()

    try:
        # private_mode — pywebview default True: profile in temp and localStorage
        # (theme, onboarding, dd-ui-*) wiped on every launch
        webview.start(icon=be.ICON_FILE, private_mode=False,
                      storage_path=os.path.join(be.DATA_DIR, "webview"))
    finally:
        dash.stop()
        icon.stop()
        if hk["tid"]:   # release Ctrl+Alt+D → the hotkey loop exits
            ctypes.windll.user32.PostThreadMessageW(hk["tid"], 0x0012, 0, 0)


if __name__ == "__main__":
    # CLI companion: a known command talks to the running instance
    # over the API and exits — no window, no single-instance claim
    if len(sys.argv) > 1 and sys.argv[1] in _CLI_CMDS:
        sys.exit(_cli(sys.argv[1:]))
    main()
