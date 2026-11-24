"""Ядро дашборда без Qt: probe-loop, состояние, действия, HTTP API + статика.
Заменяет bridge.py: та же логика, вместо QMetaObject — прямые вызовы под локом,
вместо QProcess/QTimer — subprocess/threading."""
import json
import mimetypes
import os
import re
import subprocess
import threading
import time
import zlib
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs, unquote
import urllib.request
import urllib.error

import psutil

import backend as be
import platform_impl as pi
import process_tree as ptree
import storage as st

PILL = {"up": ("PILL_RUNNING", "ok"), "down": ("PILL_STOPPED", "muted"),
        "dead": ("PILL_DEAD", "bad"), "off": ("STATE_OFF", "dim"),
        "failed": ("PILL_FAILED", "bad"), "check": ("…", "check")}

RESTART_BACKOFF = (2, 5, 10, 20)   # экспоненциальный backoff авторестарта
CIRCUIT_FAILS = 5                  # падений за окно до открытия circuit breaker
CIRCUIT_WINDOW = 60                # окно подсчёта падений, сек
STABLE_UPTIME = 60                 # проработал столько — счётчик падений сбрасывается
DEP_TIMEOUT = 15                   # ожидание готовности зависимости, сек

STATIC_DIR = os.path.join(be.RESOURCE_DIR, "frontend", "dist")


_LOG_ERR_RE = re.compile(
    r"Traceback \(most recent call last\)|Exception:|\bERROR\b|\bFATAL\b|"
    r"EADDRINUSE|UnhandledPromiseRejection|SyntaxError|ModuleNotFoundError|"
    r"[\w.]*Error:", )
_LOG_WARN_RE = re.compile(r"\bwarn(?:ing)?\b|deprecated", re.I)
_ENV_SECRET_RE = re.compile(
    r"TOKEN|SECRET|KEY|PASSWORD|PASS|AUTH|CREDENTIAL|JWT|SESSION", re.I)


def classify_log_line(line):
    """Уровень строки лога: error / warn / info."""
    if _LOG_ERR_RE.search(line):
        return "error"
    if _LOG_WARN_RE.search(line):
        return "warn"
    return "info"


def _timer(sec, fn):
    """Daemon-таймер: не держит python.exe после выхода из трея."""
    t = threading.Timer(sec, fn)
    t.daemon = True
    t.start()


class _ApiServer(ThreadingHTTPServer):
    daemon_threads = True
    # на Windows SO_REUSEADDR разрешает ВТОРОЙ bind на занятый порт —
    # fallback на следующий порт тогда не сработает
    allow_reuse_address = not pi.IS_WIN

    def handle_error(self, request, client_address):
        pass  # обрывы keep-alive браузером/webview — шум, не ошибка


class _ApiHandler(BaseHTTPRequestHandler):
    dash = None
    protocol_version = "HTTP/1.1"

    def _send(self, code, obj, ctype="application/json"):
        body = obj if isinstance(obj, bytes) else \
            json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.command == "HEAD":
            return
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def log_message(self, *a):
        pass

    # ---------- GET ----------

    @staticmethod
    def _qint(q, key, default):
        try:
            return int(q.get(key, [""])[0])
        except (TypeError, ValueError):
            return default

    def _host_ok(self):
        """DNS-rebinding guard: только локальный Host, иначе чужой домен,
        указавший на 127.0.0.1, читал бы секреты из GET-эндпоинтов."""
        host = self.headers.get("Host", "")
        return re.match(r"^(127\.0\.0\.1|localhost|::1|\[::1\]):\d+$", host)

    def do_GET(self):
        if not self._host_ok():
            self._send(403, {"error": "forbidden host"})
            return
        u = urlparse(self.path)
        path = unquote(u.path)
        q = parse_qs(u.query)
        d = self.dash
        try:
            env_m = re.match(r"^/api/(services|projects)/(.+)/env$", path)
            if env_m:
                fn = (d.service_env if env_m.group(1) == "services"
                      else d.project_env)
                env = fn(unquote(env_m.group(2)),
                         reveal=q.get("reveal") == ["1"])
                self._send(200 if env is not None else 404,
                           env if env is not None else
                           {"error": "not found"})
            elif path == "/api/state":
                self._send(200, d.api_state())
            elif path == "/api/status":
                self._send(200, d.api_status())
            elif path == "/api/services":
                self._send(200, d.api_services())
            elif path == "/api/projects":
                self._send(200, d.api_projects())
            elif path == "/api/issues":
                self._send(200, d.api_issues())
            elif path == "/api/ports":
                self._send(200, d.api_ports())
            elif path == "/api/settings":
                self._send(200, d.api_settings())
            elif path == "/api/runs":
                self._send(200, d.api_runs(q.get("name", [""])[0]))
            elif path == "/api/log":
                self._send(200, d.api_log(self._qint(q, "tail", 200),
                                          q.get("tag", [""])[0]))
            elif path == "/api/service-log":
                self._send(200, d.api_service_log(
                    q.get("name", [""])[0], self._qint(q, "tail", 300)))
            elif path == "/api/service":
                self._send(200, d.service_spec(q.get("name", [""])[0]) or {})
            elif path == "/api/project":
                self._send(200, d.project_spec(q.get("name", [""])[0]) or {})
            elif path == "/api/service-targets":
                self._send(200, d.service_targets(q.get("name", [""])[0]))
            elif path == "/api/stop-all-targets":
                self._send(200, d.stop_all_targets())
            elif path == "/api/port-targets":
                self._send(200, d.port_targets(self._qint(q, "port", 0)))
            elif path == "/api/port-conflict":
                self._send(200, d.port_conflict(q.get("name", [""])[0]))
            elif path == "/api/service-token":
                self._send(200, {"value": d.get_service_token(
                    q.get("name", [""])[0])})
            elif path.startswith("/api/"):
                self._send(404, {"error": "not found"})
            else:
                self._static(path)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as e:
            self._send(500, {"error": str(e)})

    do_HEAD = do_GET

    def _static(self, path):
        """Отдача собранного фронта; SPA-fallback на index.html."""
        if path in ("", "/"):
            path = "/index.html"
        fs = os.path.normpath(os.path.join(STATIC_DIR, path.lstrip("/")))
        if not fs.startswith(os.path.normpath(STATIC_DIR) + os.sep):
            self._send(403, {"error": "forbidden"})
            return
        if not os.path.isfile(fs):
            fs = os.path.join(STATIC_DIR, "index.html")
            if not os.path.isfile(fs):
                self._send(404, {"error": "frontend not built"})
                return
        ctype = mimetypes.guess_type(fs)[0] or "application/octet-stream"
        if fs.endswith(".js"):
            ctype = "text/javascript"
        try:
            with open(fs, "rb") as f:
                body = f.read()
        except OSError:
            self._send(404, {"error": "not found"})
            return
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    # ---------- POST ----------

    def do_POST(self):
        # CSRF: разрешаем только локальные Origin (или его отсутствие — curl и т.п.)
        origin = self.headers.get("Origin")
        if origin and not re.match(
                r"^https?://(127\.0\.0\.1|localhost)(:\d+)?$", origin):
            self._send(403, {"error": "forbidden origin"})
            return
        if not self._host_ok():
            self._send(403, {"error": "forbidden host"})
            return
        path = unquote(urlparse(self.path).path)
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            n = -1
        if not 0 <= n <= 1 << 20:  # больше 1 МБ дашборду не нужно
            self._send(400, {"error": "bad content-length"})
            return
        try:
            body = json.loads(self.rfile.read(n) or b"{}") if n else {}
        except Exception:
            self._send(400, {"error": "bad json"})
            return
        if not isinstance(body, dict):
            self._send(400, {"error": "bad json"})
            return
        d = self.dash
        try:
            env_m = re.match(r"^/api/(services|projects)/(.+)/env$", path)
            if env_m:  # PUT (и POST для простоты): полная замена env
                fn = (d.save_env if env_m.group(1) == "services"
                      else d.save_project_env)
                res = fn(unquote(env_m.group(2)), body)
                if res is None:
                    self._send(404, {"error": "not found"})
                elif res is False or isinstance(res, tuple):
                    self._send(400, {"error": res[1] if res
                                     else "bad env"})
                else:
                    self._send(200, res)
                return
            m = re.match(r"^/api/(projects|services)/(.+)/(start|stop|restart)$",
                         path)
            if m:  # совместимость со старым API
                ok = d.api_action(m.group(2), m.group(3), m.group(1))
                self._send(200 if ok else 404, {"ok": bool(ok)})
                return
            m = re.match(r"^/api/projects/(.+)/(open-folder|open-ide)$", path)
            if m:
                res = d.open_project(unquote(m.group(1)), m.group(2))
                self._send(200, {"ok": bool(res[0]), "msg": res[1] or ""})
                return
            routes = {
                "/api/services/save":
                    lambda: d.save_service(body.get("old_name", ""),
                                           body.get("data") or {}),
                "/api/services/delete":
                    lambda: d.delete_service(body.get("name", "")),
                "/api/services/autorestart":
                    lambda: d.set_autorestart(body.get("name", ""),
                                              bool(body.get("enabled"))),
                "/api/services/token":
                    lambda: d.set_service_token(body.get("name", ""),
                                                str(body.get("value", ""))),
                "/api/services/open-log":
                    lambda: d.open_service_log(body.get("name", "")),
                "/api/services/clear-log":
                    lambda: d.clear_service_log(body.get("name", "")),
                "/api/projects/save":
                    lambda: d.save_project(body.get("old_name", ""),
                                           body.get("data") or {}),
                "/api/projects/delete":
                    lambda: d.delete_project(body.get("name", "")),
                "/api/projects/add":
                    lambda: d.add_projects(body.get("items") or []),
                "/api/actions/start-all": d.start_all,
                "/api/actions/stop-all": d.stop_all,
                "/api/autorun/toggle":
                    lambda: d.toggle_autorun(body.get("name", ""),
                                             bool(body.get("enabled"))),
                "/api/autorun/save":
                    lambda: d.write_autorun(body.get("name", ""),
                                            body.get("cmd", ""),
                                            body.get("old_name", "")),
                "/api/autorun/delete":
                    lambda: d.delete_autorun(body.get("name", "")),
                "/api/kill-port":
                    lambda: d.kill_port(body.get("port")),
                "/api/kill-pid":
                    lambda: d.kill_pid(body.get("pid")),
                "/api/issues/clear": d.clear_issues,
                "/api/settings": lambda: d.save_settings(body),
                "/api/scan": d.scan_projects,
                "/api/log": lambda: d.log_line(str(body.get("text", ""))),
                "/api/open":
                    lambda: d.open_target(body.get("url"), body.get("path"),
                                          bool(body.get("editor"))),
                "/api/pick-dir":
                    lambda: d.pick_dir(body.get("start", "")),
                "/api/show-window": d.show_window,
            }
            fn = routes.get(path)
            if not fn:
                self._send(404, {"error": "not found"})
                return
            res = fn()
            if isinstance(res, dict):
                res.setdefault("ok", True)
                self._send(200, res)
            elif isinstance(res, tuple):  # (ok, msg)
                self._send(200, {"ok": bool(res[0]), "msg": res[1] or ""})
            else:
                self._send(200, {"ok": res is not False})
        except Exception as e:
            self._send(500, {"error": str(e)})

    do_PUT = do_POST


class Dashboard:
    """Состояние + действия дашборда. tray_cb/info_cb — колбэки оболочки."""

    def __init__(self):
        self.projects_data = be.load_projects()
        self.services_data = be.load_services()
        self.tray_cb = None      # (title, msg) — уведомление из трея
        self.info_cb = None      # (msg) — тост в UI (сейчас через ответы API)

        self._lock = threading.RLock()
        self._procs = {}          # name -> Popen (запущенные из дашборда)
        self._svc_spawn = {}      # name -> (pid, ctime) shell-обёртки сервиса
        self._proj_dead = {}      # name -> был краш (пилюля «упал»)
        self._detected_url = {}   # name -> url
        self._fw_cache = {}      # cwd -> framework label
        self._envinfo = {}       # cwd -> (ts, env+branch поля), TTL 30с —
        self._envval = {}        # (env_file,key) -> (ts, значение), TTL 30с
        self._last_services = {}
        self._svc_prev = {}
        self._jobs = {}           # name -> process_tree.Job
        self._crash_ts = {}       # name -> [ts] падений (скользящее окно)
        self._quick_fails = {}    # name -> подряд быстрых падений (backoff)
        self._cb_open = set()     # circuit breaker: авторестарт отключён
        self._svc_up_since = {}   # name -> ts перехода в up
        st_cfg = be.load_settings()
        self._backoff = tuple(st_cfg["backoff"]) or RESTART_BACKOFF
        self._dep_timeout = st_cfg["dep_timeout"] or DEP_TIMEOUT
        self._probe_interval = st_cfg["probe_interval"] or 4
        self.api_port = st_cfg["api_port"]   # обновится реальным при bind
        self._err_issues = {}     # (name) -> последний log_error issue (дедуп)
        self._svc_cpu = {}
        self._proj_cpu = {}
        self._remote_next = {}
        self._remote_last = {}
        self._probing = False
        self._probe_t0 = 0.0
        self._issues = deque(maxlen=120)   # дедуплицированные события
        self._runs = {}                    # name -> deque последних запусков
        self.show_cb = None     # () — поднять окно (single-instance)
        try:  # история из state.db
            pruns, piss = st.load()
            for n, lst in pruns.items():
                self._runs[n] = deque(lst[-10:], maxlen=10)
            self._issues.extend(piss[-120:])
        except Exception:
            pass
        self._ar_mine, self._ar_other = [], []
        self._proj_info = {}
        self._status = "● …"
        self._problems = []
        self._log_entries = deque(maxlen=2000)  # событийный лог (in-memory)
        self._stop = threading.Event()
        self.api = None

    # ---------- жизненный цикл ----------

    def start(self):
        self._start_api()
        if self.api:
            self._log("[SYSTEM] API: http://127.0.0.1:%d" % self.api_port)
        else:
            self._log("[SYSTEM] " + be.tr(
                "API_PORT_BUSY",
                port=self.api_port))
        self.refresh_probe()
        threading.Thread(target=self._probe_loop, daemon=True).start()
        # автостарт проектов, помеченных autostart
        for p in list(self.projects_data):
            if p.get("autostart") and not be.is_pid_running(p.get("pid"), p.get("pid_ctime")):
                self.start_project(p["name"])

    def stop(self):
        self._stop.set()
        # штатный выход: снять KILL_ON_JOB_CLOSE — сервисы переживают
        # выход дашборда; при краше дашборда деревья умрут сами
        with self._lock:
            jobs = list(self._jobs.values())
            self._jobs.clear()
        for job in jobs:
            job.disarm()
            job.close()
        if self.api:
            threading.Thread(target=self.api.shutdown, daemon=True).start()

    def _probe_loop(self):
        while not self._stop.wait(
                min(max(float(self._probe_interval), 0.5), 60)):
            self.refresh_probe()

    # ---------- лог ----------

    def _log(self, text):
        m = re.match(r"^\[([^\]]+)\](.*)$", text, re.S)
        tag = m.group(1) if m else ""
        with self._lock:
            self._log_entries.append({
            "tag": tag, "raw": text,
            "text": (m.group(2).strip() if m else text),
            "err": " ERR]" in text or tag.endswith(" ERR"),
            "time": f"{datetime.now():%H:%M:%S}",
            "tagColor": be.TAG_COLORS[
                zlib.crc32(tag.encode()) % len(be.TAG_COLORS)] if tag else ""})

    def log_line(self, text):
        self._log(text)

    # ---------- пробы ----------

    def refresh_probe(self):
        if self._probing:
            if time.time() - self._probe_t0 < 90:  # зависший worker → сброс флага
                return
        self._probing = True
        self._probe_t0 = time.time()
        threading.Thread(target=self._probe_worker, daemon=True).start()

    def _force_probe(self, delay=0):
        def go():
            self._probing = False
            self.refresh_probe()
        if delay:
            _timer(delay / 1000, go)
        else:
            go()

    def _probe_worker(self):
        try:
            procs, listeners, _lan = be._proc_snapshot()
            services = {}
            remotes = []
            for s in list(self.services_data):
                if s.get("type"):
                    remotes.append(s)
                else:
                    try:  # битый spec в конфиге не должен губить все пробы
                        res = be._probe_service(
                            s, procs, listeners, self._svc_cpu)
                        # сервис запущен нами без proc/match: проба его не
                        # видит — «жив» по pid обёртки (своей или из spec)
                        if res[0] == "down" and not s.get("monitor_only"):
                            with self._lock:  # _svc_spawn пишется под _lock
                                ent = self._svc_spawn.get(s["name"])
                                if ent is None and not s.get("proc") \
                                        and not s.get("match"):
                                    ent = (s.get("pid"), s.get("pid_ctime"))
                                if ent and be.is_pid_running(*ent):
                                    res = ("up", f"pid {ent[0]}")
                                elif s["name"] in self._svc_spawn:
                                    del self._svc_spawn[s["name"]]  # обёртка ушла
                        services[s["name"]] = res
                    except Exception:
                        services[s["name"]] = ("dead", "bad spec")
            for pid in list(self._svc_cpu):
                if not psutil.pid_exists(pid):
                    del self._svc_cpu[pid]
            now = time.time()
            due = [s for s in remotes
                   if now >= self._remote_next.get(s["name"], 0)]
            if due:  # remote-пробы параллельно, каждая со своим интервалом
                def _safe(s):
                    try:
                        return be._probe_remote(s)
                    except Exception:
                        return "dead", "bad spec"
                with ThreadPoolExecutor(4) as ex:
                    for s, res in zip(due, ex.map(_safe, due)):
                        services[s["name"]] = res
                        self._remote_last[s["name"]] = res
                        self._remote_next[s["name"]] = \
                            now + be._remote_interval(s)
            for s in remotes:  # не дозрели — показываем прошлый результат
                services.setdefault(
                    s["name"], self._remote_last.get(s["name"], ("check", "…")))

            # проекты: pid + метрики + порты — тяжёлый скан здесь, не в GUI-тике
            projects = {}
            for p in list(self.projects_data):
                pid = p.get("pid")
                if not be.is_pid_running(pid, p.get("pid_ctime")):
                    pid = be.find_project_pid(p)
                entry = {"pid": pid, "running": bool(pid)}
                if pid:
                    entry["stats"] = be.proc_stats(pid, self._proj_cpu)
                    if not p.get("url"):
                        entry["ports"] = be.find_project_ports(pid)
                projects[p["name"]] = entry
            for pid in list(self._proj_cpu):
                if not psutil.pid_exists(pid):
                    del self._proj_cpu[pid]

            dirs = [os.path.normcase(os.path.normpath(p["cwd"])) + os.sep
                    for p in self.projects_data]
            for s_ in self.services_data:
                for f_ in ("cwd", "path"):
                    if s_.get(f_):
                        dirs.append(os.path.normcase(
                            os.path.normpath(s_[f_])) + os.sep)
            disabled = be._autorun_disabled()
            autorun = [(n, c, be._autorun_running(c, procs),
                        be._autorun_is_mine(n, c, dirs,
                                          self._mine_tokens()),
                        n not in disabled)
                       for n, c in be._read_autorun()]
            self._apply_probe((services, projects, autorun))
        except Exception:
            import traceback
            traceback.print_exc()
            self._probing = False

    def _svc_row(self, spec, res=None):
        state, detail = res if res else self._last_services.get(
            spec["name"], (None, ""))
        if state != "up" and spec["name"] in self._cb_open:
            state, detail = "failed", "circuit_open"
        word, tone = PILL.get(state or "check", PILL["check"])
        monitor = bool(spec.get("monitor_only") or spec.get("type"))
        url = spec.get("url")
        if url:
            chip, chip_url = re.sub(r"^https?://", "", url), url
        elif spec.get("host") and spec.get("port"):
            chip, chip_url = f"{spec['host']}:{spec['port']}", "copy"
        elif spec.get("container"):
            chip, chip_url = spec["container"], "copy"
        elif spec.get("ports"):
            chip, chip_url = f":{spec['ports'][0]}", "copy"
        else:
            chip, chip_url = "", ""
        reason, squatter = "", -1
        if state == "dead":
            m = re.search(r":(\d+) busy.*?pid (\d+)", detail or "")
            if m:
                squatter = int(m.group(1))
                try:
                    pname = psutil.Process(int(m.group(2))).name()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pname = "?"
                reason = be.tr("PORT_BUSY_PID",
                               pid=m.group(2), pname=pname)
            else:
                reason = be.tr_detail(detail) or be.tr("STATE_DOWN")
        elif state == "failed":
            reason = be.tr_detail("circuit_open")
        sub = spec.get("sub", "")
        for pt in spec.get("ports", ()):  # порт живёт в чипе — из подписи убрать
            sub = re.sub(rf"\s*·?\s*:{pt}\b", "", sub, count=1)
        if spec.get("autorestart"):
            ar = be.tr("AUTORESTART")
            sub = (sub + " · " + ar) if sub else ar
        metrics = be.tr_detail(detail) if state in ("up", "off") else ""
        metrics = re.sub(r"^:\d+(\s*·\s*)?", "", metrics)  # порт уже в чипе
        if spec.get("zerotier") and re.fullmatch(r"[0-9.]+", metrics or ""):
            chip, chip_url, metrics = metrics, "copy", ""  # IP — это адрес-чип
        chip = re.sub(r"^(127\.0\.0\.1|localhost|0\.0\.0\.0):", ":", chip)
        row = {"name": spec["name"], "sub": sub,
               "state": state or "check", "pillText": be.tr(word), "tone": tone,
               "failed": state in ("dead", "failed"),
               "metrics": metrics, "warn": state == "off" and bool(detail),
               "chip": chip, "chipUrl": chip_url, "monitor": monitor,
               "reason": reason, "squatterPort": squatter,
               "autorestart": bool(spec.get("autorestart")),
               "hasToken": bool(spec.get("env_key") and spec.get("env_file")),
               "hasUrl": bool(url), "hasPath": bool(spec.get("path")),
               "remote": bool(spec.get("type"))}
        # структурные метрики для UI: 'pid 19676 · 0% · 352MB · 7ч12м'
        m = re.search(r"pid\s+(\d+).*?([\d.]+)%.*?(\d+)\s*MB(.*?(\d+)m)?",
                      detail or "")
        if state == "up" and m:
            row["m"] = {"pid": int(m.group(1)),
                        "cpu": float(m.group(2)),
                        "mb": int(m.group(3)),
                        "up": be.tr_detail(
                            (m.group(4) or "").strip(" ·"))}
        # динамическая проверка: ключа env_key реально нет в env_file;
        # кэш 30с — файл не перечитываем на каждом state-полле
        ek, ef = spec.get("env_key"), spec.get("env_file")
        if ek and ef:
            ck = (ef, ek)
            ent = self._envval.get(ck)
            if ent is None or time.time() - ent[0] > 30:
                ent = (time.time(), be._env_get(ef, ek))
                self._envval[ck] = ent
            if not ent[1]:
                row["envWarn"] = be.tr("ENV_MISSING", k=ek)
                row["warn"] = True
        return row

    def _env_info(self, cwd):
        """env-diff + gitignore-cover + ветка проекта; кэш 30с, чтобы
        /api/state не открывал ~7 файлов на проект каждый полл."""
        ent = self._envinfo.get(cwd)
        if ent and time.time() - ent[0] < 30:
            return ent[1]
        d = be.env_diff(cwd) or {}
        info = {"envMissing": d.get("missing", []),
                "envExtra": d.get("extra", []),
                "envEmpty": d.get("empty", []),
                "envOpen": be.env_gitignore_open(cwd),
                "branch": be.git_branch(cwd)}
        self._envinfo[cwd] = (time.time(), info)
        return info

    def _proj_row(self, p, info=None):
        info = info or {}
        running = info.get("running", be.is_pid_running(p.get("pid"), p.get("pid_ctime")))
        dead = self._proj_dead.get(p["name"], False) and not running
        state = "up" if running else ("dead" if dead else "down")
        word, tone = PILL[state]
        url = p.get("url") or self._detected_url.get(p["name"]) or ""
        row = {"name": p["name"], "sub": p["cmd"], "state": state,
               "pillText": be.tr(word), "tone": tone, "failed": dead,
               "metrics": be.tr_detail(info.get("stats", "")) if running else "",
               "chip": re.sub(r"^(https?://)?(localhost|127\.0\.0\.1):", ":",
                              url), "chipUrl": url,
               "running": running, "pid": p.get("pid") or 0,
               "cwd": p.get("cwd", "")}
        cwd = p.get("cwd", "")
        fw = p.get("framework")
        if not fw and cwd:
            fw = self._fw_cache.get(cwd)
            if fw is None:
                fw = be.project_framework(cwd)
                self._fw_cache[cwd] = fw
        row["framework"] = fw or ""
        # diff .env vs .env.example + gitignore-cover + ветка (кэш 30с)
        if cwd:
            row.update(self._env_info(cwd))
        m = re.search(r"pid\s+(\d+).*?([\d.]+)%.*?(\d+)\s*MB",
                      info.get("stats") or "")
        if running and m:
            row["m"] = {"pid": int(m.group(1)), "cpu": float(m.group(2)),
                        "mb": int(m.group(3)), "up": ""}
        return row

    def _ar_row(self, n, c, running, mine, enabled):
        if not enabled:
            # выкл видно по тумблеру — в метриках дублировать не надо
            pill, tone, metrics = be.tr("STATE_OFF"), "dim", "—"
            failed = False
        else:
            pill, tone = be.tr("STATE_ON"), "accent"
            metrics = "…" if running is None else \
                be.tr("AR_RUNNING" if running else "AR_NOT_RUNNING")
            failed = running is False and mine
        return {"name": n, "sub": c, "pillText": pill, "tone": tone,
                "failed": failed, "metrics": metrics, "arEnabled": enabled,
                "mine": mine, "state": "up" if running else "down"}

    def _mine_tokens(self):
        """Токены «своих» автозапусков: варианты имён сервисов и стемы
        файлов из их start — те же иглы, что у _ar_match."""
        toks = set()
        for spec in self.services_data:
            n = spec["name"].lower()
            toks.update((n, n.replace(" ", "-"), n.replace(" ", "_")))
            for t in re.findall(r"[\w.-]+\.(?:py|cmd|bat|exe|ps1|vbs|com)\b",
                                spec.get("start") or "", re.I):
                toks.add(os.path.splitext(os.path.basename(t))[0].lower())
        return toks

    def _ar_match(self, name, spec, entries):
        """Имя записи автозапуска, относящейся к сервису (или None).
        Иглы: имя сервиса, варианты с -/_ и stem исполняемого файла из start
        («pythonw shot2note.py serve» → «shot2note», имя «shot2note serve» →
        «shot2note-serve», что матчит запись shot2note-serve.cmd)."""
        needles = {name.lower(),
                   name.lower().replace(" ", "-"),
                   name.lower().replace(" ", "_")}
        for tok in re.findall(r"[\w.-]+\.(?:py|cmd|bat|exe|ps1|vbs|com)\b",
                              spec.get("start") or "", re.I):
            needles.add(os.path.splitext(os.path.basename(tok))[0].lower())
        for e in entries:
            s = (e["name"] + " " + e["sub"]).lower()
            if any(len(n) >= 4 and n in s for n in needles):
                return e["name"]
        return None

    def _apply_probe(self, res):
        services, projects, autorun = res
        with self._lock:
            self._probing = False
            self._last_services = services

            specs = {s["name"]: s for s in self.services_data}
            for spec in list(self.services_data):
                name = spec["name"]
                st = services.get(name, (None,))[0]
                prev = self._svc_prev.get(name)
                if prev != "up" and st == "up":
                    self._svc_up_since[name] = time.time()
                    self._run_start(name)      # внешний или наш старт — фиксируем
                if prev == "up" and st in ("down", "dead"):
                    self._run_end(name, st)
                if prev == "up" and st == "dead":
                    detail = services.get(name, ("", ""))[1]
                    kind = "port" if " busy" in detail else "crash"
                    self._issue(kind, name, be.tr_detail(detail)
                                or be.tr("EXITED"))
                    self._tray("Dev Dashboard",
                               be.tr("NAME_EXITED",
                                     name=name))
                # watchdog: backoff + circuit breaker на падение up -> down/dead
                if spec.get("autorestart") and not spec.get("monitor_only") \
                        and not spec.get("type") and spec.get("start") \
                        and st in ("down", "dead") and prev == "up":
                    self._svc_autorestart(spec)
                self._svc_prev[name] = st

            ok = sum(1 for st, _ in services.values() if st == "up")
            problems = [n for n, (st, _) in services.items()
                        if st in ("down", "dead")
                        and not specs.get(n, {}).get("note")]
            self._proj_info = projects
            for p in self.projects_data:
                info = projects.get(p["name"], {})
                pid = info.get("pid")
                if pid != p.get("pid"):
                    was = bool(p.get("pid"))
                    p["pid"] = pid
                    p["pid_ctime"] = be.pid_ctime(pid) if pid else None
                    be.save_projects(self.projects_data)
                    if pid:
                        self._proj_dead[p["name"]] = False
                        self._run_start(p["name"])
                        self._log(f"[{p['name']}] " + be.tr(
                            "PROC_FOUND", pid=pid))
                    elif was:
                        self._run_end(p["name"], "dead")
                        if p["name"] not in self._procs:
                            # умер вне дашборда — помечаем «упал»
                            self._proj_dead[p["name"]] = True
                            self._issue("crash", p["name"],
                                        be.tr("EXITED"))
                            self._tray("Dev Dashboard", be.tr(
                                "NAME_EXITED",
                                name=p["name"]))
                if not p.get("url"):
                    ports = info.get("ports") or []
                    self._detected_url[p["name"]] = \
                        f"http://localhost:{ports[0]}" if ports else ""
                if info.get("running"):
                    ok += 1

            mine, other = [], []
            for n, c, r, mn, e in autorun:
                (mine if mn else other).append(self._ar_row(n, c, r, mn, e))
            self._ar_mine, self._ar_other = mine, other
            ok += sum(1 for _, _, r, mn, e in autorun if r and e)
            problems += [n for n, _, r, mn, e in autorun if not r and mn and e]

            self._problems = problems
            status = be.tr("N_OK", n=ok)
            if problems:
                status += f"  ·  ⚠ {len(problems)}: " \
                          + ", ".join(problems[:3]) \
                          + ("…" if len(problems) > 3 else "")
            self._status = status

    def _tray(self, title, msg):
        if self.tray_cb:
            try:
                self.tray_cb(title, msg)
            except Exception:
                pass

    def _info(self, msg):
        if self.info_cb:
            try:
                self.info_cb(msg)
            except Exception:
                pass

    def _svc_autorestart(self, spec):
        """Падение сервиса с autorestart: backoff 2→5→10→20с, circuit
        breaker после 5 падений за 60с."""
        name = spec["name"]
        if name in self._cb_open:
            return
        now = time.time()
        up = self._svc_up_since.pop(name, 0)  # consume: серия инста-крашей
        if up and now - up > STABLE_UPTIME:   # без up не должна сбрасывать счёт
            self._quick_fails[name] = 0      # долго работал — счёт с нуля
            self._crash_ts.pop(name, None)
        ts = self._crash_ts.setdefault(name, [])
        ts.append(now)
        ts[:] = [t for t in ts if now - t < CIRCUIT_WINDOW]
        if len(ts) >= CIRCUIT_FAILS:
            self._cb_open.add(name)
            self._issue("crash_loop", name,
                        be.tr("CRASHES_HALT",
                              n=CIRCUIT_FAILS, w=CIRCUIT_WINDOW))
            self._tray("Dev Dashboard", be.tr("NAME_CRASH_LOOP", name=name))
            return
        self._quick_fails[name] = self._quick_fails.get(name, 0) + 1
        delay = self._backoff[
            min(self._quick_fails[name] - 1, len(self._backoff) - 1)]
        self._issue("restart", name,
                    be.tr("AR_IN", d=delay))
        self._log(f"[{name}] " + be.tr(
            "AR_IN_DEAD", d=delay))
        _timer(delay, lambda s=spec: self._autorestart_fire(s))

    def _autorestart_fire(self, spec):
        """Отложенный авторестарт: не воскрешать удалённый, уже поднятый
        или закрытый circuit'ом сервис."""
        if spec not in self.services_data:
            return
        name = spec["name"]
        if name in self._cb_open:
            return
        if self._last_services.get(name, (None,))[0] == "up":
            return
        self._start_service(spec)

    def _issue(self, kind, name, text):
        """Событие в issues-ленту; повтор подряд того же вида — только счётчик."""
        with self._lock:
            it = self._issues[-1] if self._issues else None
            if it and it["kind"] == kind and it["name"] == name:
                it["count"] += 1
                it["t"] = time.time()
            else:
                it = {"t": time.time(), "kind": kind,
                      "name": name, "text": text, "count": 1}
                self._issues.append(it)
        try:
            st.save_issue(it)
        except Exception:
            pass

    def _issue_log_error(self, name, text):
        """Ошибка из лога сервиса/проекта: дедуп по тексту в окне 60с (×N)."""
        text = text.strip()[:300]
        now = time.time()
        it = self._err_issues.get(name)
        if it and it["text"] == text and now - it["t"] < 60:
            it["count"] += 1
            it["t"] = now
        else:
            it = {"t": now, "kind": "log_error", "name": name,
                  "text": text, "count": 1}
            self._err_issues[name] = it
            self._issues.append(it)
        try:
            st.save_issue(it)
        except Exception:
            pass

    def _run_start(self, name):
        dq = self._runs.setdefault(name, deque(maxlen=10))
        if not dq or dq[-1]["t1"] is not None:
            dq.append({"t0": time.time(), "t1": None, "exit": None})
            try:
                st.save_run(name, dq[-1])
            except Exception:
                pass

    def _run_end(self, name, exit_info=""):
        dq = self._runs.get(name)
        if dq and dq[-1]["t1"] is None:
            dq[-1]["t1"] = time.time()
            dq[-1]["exit"] = exit_info
            try:
                st.save_run(name, dq[-1])
            except Exception:
                pass

    # ---------- сервисы ----------

    def _service(self, name):
        return next((s for s in self.services_data if s["name"] == name), None)

    def service_spec(self, name):
        return dict(self._service(name) or {})

    def service_env(self, name, reveal=False):
        """ENV-оверрайды сервиса; секретные ключи маскируются без reveal."""
        spec = self._service(name)
        if not spec:
            return None
        env = spec.get("env") or {}
        return [{"key": k,
                 "value": str(v)
                 if reveal or not _ENV_SECRET_RE.search(k)
                 else "••••••••",
                 "secret": bool(_ENV_SECRET_RE.search(k))}
                for k, v in env.items()]

    def save_env(self, name, env):
        """PUT: полная замена env-оверрайдов. Не логировать значения!"""
        spec = self._service(name)
        if not spec:
            return None
        if spec.get("type") or spec.get("monitor_only"):
            return False, be.tr("ENV_MONITOR_ONLY")
        if not isinstance(env, dict):
            return False, be.tr("ENV_NOT_OBJ")
        env = {str(k).strip(): str(v) for k, v in env.items()
               if str(k).strip()}
        with self._lock:
            if env:
                spec["env"] = env
            else:
                spec.pop("env", None)
            be.save_services(self.services_data)
        st = self._last_services.get(name, (None,))[0]
        return {"restart_required": st == "up"}

    # ---------- проекты ----------

    def _project(self, name):
        return next((p for p in self.projects_data if p["name"] == name),
                    None)

    def project_env(self, name, reveal=False):
        """ENV проекта = его .env + missing-ключи из .env.example;
        секреты маскируются без reveal."""
        p = self._project(name)
        if not p:
            return None
        cwd = p["cwd"]
        env = be._env_kv(os.path.join(cwd, ".env"))
        d = be.env_diff(cwd) or {}
        mask = lambda k, v: (str(v)
                             if reveal or not _ENV_SECRET_RE.search(k)
                             else "••••••••")
        return {"env": [{"key": k, "value": mask(k, v),
                         "secret": bool(_ENV_SECRET_RE.search(k))}
                        for k, v in env.items()],
                "missing": [{"key": k,
                             "secret": bool(_ENV_SECRET_RE.search(k))}
                            for k in d.get("missing", [])]}

    def save_project_env(self, name, env):
        """PUT: перезапись .env проекта ключами из payload — комментарии
        и пустые строки файла сохраняются, удалённые ключи пропадают."""
        p = self._project(name)
        if not p:
            return None
        if not isinstance(env, dict):
            return False, be.tr("ENV_NOT_OBJ")
        env = {str(k).strip(): str(v) for k, v in env.items()
               if str(k).strip()}
        path = os.path.join(p["cwd"], ".env")
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                lines = f.read().splitlines()
        except OSError:
            lines = []
        out, written = [], set()
        for line in lines:
            s = line.strip()
            if s and not s.startswith("#") and "=" in s:
                k = s.split("=", 1)[0].strip()
                if k in env:
                    out.append(f"{k}={env[k]}")
                    written.add(k)
                continue
            out.append(line)
        out += [f"{k}={v}" for k, v in env.items() if k not in written]
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(out) + ("\n" if out else ""))
        except OSError as e:
            return False, str(e)
        self._envinfo.pop(p["cwd"], None)
        return {"ok": True}

    def _start_service(self, spec, _depth=0, _seen=None):
        # depends_on: дозапустить неработающие зависимости и дождаться
        # их готовности (health_url → HTTP, порт → TCP, иначе «жив 0.5с»)
        if _seen is None:
            _seen = {spec["name"]}
        waiting = []
        for dep in spec.get("depends_on", ()):
            if dep in _seen:
                self._issue("dep_cycle", spec["name"],
                            be.tr("DEP_CYCLE_VIA", dep=dep))
                self._log(f"[{spec['name']} ERR] " + be.tr(
                    "DEP_CYCLE", dep=dep))
                continue
            ds = self._service(dep)
            if not ds:
                continue
            if self._last_services.get(dep, (None,))[0] != "up":
                self._log(f"[{spec['name']}] " + be.tr(
                    "DEP_STARTING", dep=dep))
                self._start_service(ds, _depth + 1, _seen | {dep})
                waiting.append(ds)
        if waiting:
            threading.Thread(target=self._start_after_deps,
                             args=(spec, waiting), daemon=True).start()
            return True
        return self._do_start(spec)

    def _start_after_deps(self, spec, deps):
        for dep in deps:
            if not self._wait_ready(dep, self._dep_timeout):
                self._issue("deps_timeout", spec["name"],
                            be.tr("DEP_TIMEOUT",
                                  dep=dep["name"], t=self._dep_timeout))
                self._log(f"[{spec['name']} ERR] " + be.tr(
                    "DEP_FAIL",
                    dep=dep["name"]))
                self._info(be.tr("DEP_FAIL_NAME",
                                 name=spec["name"], dep=dep["name"]))
                return False
        self._do_start(spec)
        return True

    def _wait_ready(self, spec, timeout):
        """Готов ли сервис: health_url → HTTP 200-399; порт → TCP; иначе
        процесс жив и не упал за 0.5с. Поллинг 250мс, таймаут — сек."""
        name, url = spec["name"], spec.get("health_url")
        ports = spec.get("ports") or []
        alive_since, deadline = None, time.time() + timeout
        while time.time() < deadline and not self._stop.is_set():
            if self._last_services.get(name, (None,))[0] == "up":
                return True
            if url:
                try:
                    code = urllib.request.urlopen(url, timeout=1).status
                    if 200 <= code < 400:
                        return True
                except urllib.error.HTTPError as e:
                    if 200 <= e.code < 400:
                        return True
                except Exception:
                    pass
            elif ports:
                if be._port_open(ports[0]):
                    return True
            else:
                alive = any(
                    (spec.get("proc") and p["name"] == spec["proc"])
                    or (spec.get("match")
                        and spec["match"].lower() in p["cl"])
                    for p in be._proc_snapshot()[0])
                now = time.time()
                alive_since = alive_since if alive else None
                if alive and alive_since is None:
                    alive_since = now
                if alive_since and now - alive_since >= 0.5:
                    return True
            time.sleep(0.25)
        return False

    def _do_start(self, spec):
        job = None
        try:
            job = ptree.Job()
        except OSError:
            pass
        try:
            ok, err, proc = be.start_service_process(spec, self._log, job=job)
        except Exception:
            if job:
                job.disarm()
                job.close()
            raise
        if ok and job:
            with self._lock:
                old = self._jobs.pop(spec["name"], None)
                if old:
                    old.terminate()      # старые процессы — добить дерево
                    old.close()
                self._jobs[spec["name"]] = job
        elif job:
            job.disarm()
            job.close()
        if ok:
            with self._lock:
                # pid обёртки — сигнал «жив» для проб без proc/match/ports;
                # в spec — чтобы проба приняла его и после рестарта дашборда
                self._svc_spawn[spec["name"]] = (proc.pid,
                                                 be.pid_ctime(proc.pid))
                spec["pid"], spec["pid_ctime"] = \
                    self._svc_spawn[spec["name"]]
                be.save_services(self.services_data)
            self._run_start(spec["name"])
            if spec.get("autorestart"):
                # insta-crash <4с проба не увидит — проверим через 8с
                _timer(8, lambda s=spec: self._start_verify(s))
        else:
            self._log(f"[{spec['name']} ERR] " + be.tr(
                "START_FAIL", err=be.tr_detail(str(err))))
            self._info(be.tr("START_FAIL_NAME",
                             name=spec["name"], err=be.tr_detail(str(err))))
        self._force_probe(1500)
        return ok

    def _start_verify(self, spec):
        """Если через 8с сервис всё ещё не up и процесса нет — insta-crash:
        засчитываем падение, чтобы circuit breaker сработал."""
        if self._last_services.get(spec["name"], (None,))[0] == "up":
            return
        if any((spec.get("proc") and p["name"] == spec["proc"])
               or (spec.get("match") and spec["match"].lower() in p["cl"])
               for p in be._proc_snapshot()[0]):
            return  # процесс жив — просто медленный старт
        self._svc_autorestart(spec)

    def port_conflict(self, name):
        """{} или {port,pid,pname}: порт занят чужим процессом — для диалога."""
        spec = self._service(name)
        if not spec:
            return {}
        procs, listeners, _lan = be._proc_snapshot()
        own = {p["pid"] for p in procs
               if (spec.get("proc") and p["name"] == spec["proc"])
               or (spec.get("match") and spec["match"].lower() in p["cl"])}
        for pt in spec.get("ports", ()):
            owner = listeners.get(pt)
            if owner and owner not in own and owner != os.getpid():
                try:
                    pname = psutil.Process(owner).name()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pname = "?"
                return {"port": pt, "pid": owner, "pname": pname,
                        "suggest": be.next_free_port(pt)}
        return {}

    def service_targets(self, name):
        """Кого убьёт stop — имена процессов для диалога подтверждения."""
        spec = self._service(name)
        if not spec:
            return []
        matched = [p for p in be._proc_snapshot()[0]
                   if (spec.get("proc") and p["name"] == spec["proc"])
                   or (spec.get("match") and spec["match"].lower() in p["cl"])]
        return [{"name": p["name"], "pid": p["pid"]} for p in matched]

    def start_service(self, name):
        spec = self._service(name)
        # ручной старт — сброс circuit breaker и счётчиков падений
        self._cb_open.discard(name)
        self._crash_ts.pop(name, None)
        self._quick_fails.pop(name, None)
        if spec and spec.get("start"):
            return self._start_service(spec)
        if spec:
            return False, be.tr(
                "NO_START_CMD", name=name)
        return False, be.tr("NAME_NOT_FOUND", name=name)

    def _stop_service(self, spec):
        with self._lock:
            job = self._jobs.pop(spec["name"], None)
            spawn = self._svc_spawn.pop(spec["name"], None)
            spid, sctime = spec.pop("pid", None), spec.pop("pid_ctime", None)
            if spid:  # принятый пробой pid — снять до убийства
                be.save_services(self.services_data)
        if job:  # Job Object: мгновенное убийство всего дерева
            job.terminate()
            job.close()
        # adopted/spawned pid вне Job (перезапуск дашборда, Job() упал) —
        # без этого stop «успешен», а процесс продолжает жить
        killed = [pid for pid, ct in ((spawn or (None, None)), (spid, sctime))
                  if pid and be.is_pid_running(pid, ct)
                  and be.kill_proc_tree(pid)]
        matched = [p for p in be._proc_snapshot()[0]
                   if (spec.get("proc") and p["name"] == spec["proc"])
                   or (spec.get("match") and spec["match"].lower() in p["cl"])]
        killed += [p["pid"] for p in matched if p["pid"] not in killed
                   and be.kill_proc_tree(p["pid"])]
        self._log(f"[{spec['name']}] " + (be.tr(
            "STOPPED_PID", p=", ".join(map(str, killed))) if killed
            else be.tr("PROCS_NOT_FOUND")))
        self._force_probe(800)
        return True

    def stop_service(self, name):
        spec = self._service(name)
        return (self._stop_service(spec), "") if spec \
            else (False, be.tr("NAME_NOT_FOUND", name=name))

    def restart_service(self, name):
        spec = self._service(name)
        if not spec:
            return False, be.tr("NAME_NOT_FOUND", name=name)
        if self._stop_service(spec):
            _timer(1.5, lambda: self._start_service(spec))
        return True, ""

    def stop_all_targets(self):
        return [s["name"] for s in self.services_data
                if not s.get("monitor_only") and not s.get("type")
                and (s.get("proc") or s.get("match")
                     or s["name"] in self._svc_spawn or s.get("pid"))]

    def start_all(self):
        specs = self._dep_order([s for s in self.services_data
                                 if not s.get("monitor_only")
                                 and not s.get("type") and s.get("start")])
        for i, s in enumerate(specs):  # стаггер — не душить систему разом
            _timer(i * 0.8, lambda s=s: self._start_service(s))

    def stop_all(self):
        specs = [s for s in self.services_data
                 if not s.get("monitor_only") and not s.get("type")
                 and (s.get("proc") or s.get("match")
                      or s["name"] in self._svc_spawn or s.get("pid"))]
        for i, s in enumerate(specs):
            _timer(i * 0.5, lambda s=s: self._stop_service(s))

    def _dep_order(self, specs):
        """Топосорт по depends_on: зависимости стартуют раньше зависимых.
        Циклы/неизвестные имена не блокируют — докидываются в конец."""
        by_name = {s["name"]: s for s in specs}
        done, out = set(), []

        def visit(s, stack):
            if s["name"] in done:
                return
            if s["name"] in stack:
                self._issue("deps", s["name"], be.tr("DEP_CYCLE_IN"))
                return
            stack = stack | {s["name"]}
            for dep in s.get("depends_on", ()):
                if dep in by_name:
                    visit(by_name[dep], stack)
            done.add(s["name"])
            out.append(s)

        for s in specs:
            visit(s, set())
        return out

    def set_autorestart(self, name, enabled):
        spec = self._service(name)
        if not spec:
            return False, be.tr("NAME_NOT_FOUND", name=name)
        with self._lock:
            spec["autorestart"] = enabled
            be.save_services(self.services_data)
        self._force_probe()
        return True, ""

    def delete_service(self, name):
        spec = self._service(name)
        if not spec:
            return False, be.tr("NAME_NOT_FOUND", name=name)
        self._stop_service(spec)  # иначе запущенный процесс станет сиротой
        with self._lock:
            if spec in self.services_data:
                self.services_data.remove(spec)
            be.save_services(self.services_data)
        self._force_probe()
        return True, ""

    def save_service(self, old_name, data):
        """old_name='' — добавить; форма шлёт только известные ключи,
        неизвестные в spec сохраняются."""
        try:
            if isinstance(data.get("ports"), str):
                data["ports"] = [int(x) for x in
                                 re.split(r"[,\s]+", data["ports"]) if x]
        except ValueError:
            return False, be.tr("PORTS_NOT_NUMBERS")
        if not data.get("type"):
            data.pop("type", None)
        if not isinstance(data.get("name"), str) or not data["name"].strip():
            return False, be.tr("NAME_REQUIRED")
        be._norm_service(data)  # ports → валидный int-лист либо удалить
        with self._lock:
            if old_name:
                spec = self._service(old_name)
                if spec is None:
                    return False, be.tr("NAME_NOT_FOUND", name=old_name)
                # ключи формы, отсутствующие в data — удалить (снятый чек/
                # пустое поле); неизвестные ключи spec сохранить
                known = {"name", "sub", "type", "ports", "proc", "match", "url",
                         "host", "port", "keyword", "container", "interval",
                         "start", "cwd", "path", "note", "env_key", "env_file",
                         "autorestart", "monitor_only", "zerotier", "supabase",
                         "depends_on"}
                for k in known - set(data):
                    spec.pop(k, None)
                spec.update(data)
            else:
                self.services_data.append(data)
            be.save_services(self.services_data)
        self._force_probe()
        return True, ""

    def _log_path(self, spec):
        return be._service_log_path(spec)

    def open_service_log(self, name):
        spec = self._service(name)
        if not spec:
            return False, be.tr("NAME_NOT_FOUND", name=name)
        path = self._log_path(spec)
        if os.path.exists(path):
            pi.open_path(path)
            return True, ""
        return False, be.tr(
            "LOG_NOT_CREATED")

    def clear_service_log(self, name):
        spec = self._service(name)
        if not spec:
            return False, be.tr("NAME_NOT_FOUND", name=name)
        try:
            open(self._log_path(spec), "w").close()
        except OSError:
            pass
        return True, ""

    def set_service_token(self, name, value):
        spec = self._service(name)
        if not spec:
            return False, be.tr("NAME_NOT_FOUND", name=name)
        key, path = spec.get("env_key"), spec.get("env_file")
        if not key or not path:
            return False, be.tr("NO_ENV_CONF")
        if not value.strip():
            return False, be.tr("EMPTY_VALUE")
        try:
            be._env_set(path, key, value.strip())
        except OSError as e:
            return False, be.tr("WRITE_FAIL",
                                path=path, e=e)
        self._log("[SYSTEM] " + be.tr("KEY_WRITTEN",
                                      key=key, path=path))
        self._force_probe()
        return True, ""

    def get_service_token(self, name):
        spec = self._service(name)
        if not spec:
            return ""
        return be._env_get(spec.get("env_file", ""), spec.get("env_key", ""))

    # ---------- проекты ----------

    def _proj(self, name):
        return next((p for p in self.projects_data if p["name"] == name), None)

    def project_spec(self, name):
        return dict(self._proj(name) or {})

    def start_project(self, name):
        p = self._proj(name)
        if not p or be.is_pid_running(p.get("pid"), p.get("pid_ctime")):
            return False, be.tr("PROJ_NOT_FOUND_OR_RUNNING")
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        job = None
        try:
            job = ptree.Job()
        except OSError:
            pass
        try:
            proc, job = ptree.popen_in_job(
                pi.shell_argv(p["cmd"]), cwd=p["cwd"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                creationflags=flags, job=job)
        except OSError as e:
            self._log(f"[{name} ERR] " + be.tr(
                "START_FAIL", err=be.tr_detail(str(e))))
            return False, be.tr_detail(str(e))
        with self._lock:
            if job:
                old = self._jobs.pop(name, None)
                if old:  # job прошлого запуска: добить дерево, закрыть хендл
                    old.terminate()
                    old.close()
                self._jobs[name] = job
            self._procs[name] = proc
            p["pid"] = proc.pid
            p["pid_ctime"] = be.pid_ctime(proc.pid)
            self._proj_dead[name] = False
            be.save_projects(self.projects_data)
        threading.Thread(target=self._pump, daemon=True,
                         args=(proc.stdout, name, False)).start()
        threading.Thread(target=self._pump, daemon=True,
                         args=(proc.stderr, name, True)).start()
        threading.Thread(target=self._wait_proc, daemon=True,
                         args=(proc, name)).start()
        self._run_start(name)
        return True, ""

    def _pump(self, stream, name, err):
        try:
            for raw in iter(stream.readline, b""):
                line = raw.decode("utf-8", errors="replace").rstrip()
                if line:
                    self._log(f"[{name}{' ERR' if err else ''}] {line}")
                    if classify_log_line(line) == "error":
                        self._issue_log_error(name, line)
        except (OSError, ValueError):
            pass

    def _wait_proc(self, proc, name):
        rc = proc.wait()
        with self._lock:
            if self._procs.get(name) is proc:
                self._procs.pop(name, None)
            self._run_end(name, f"exit {rc}")
            p = self._proj(name)
            if p:
                was = bool(p.get("pid"))
                p["pid"] = None
                p["pid_ctime"] = None
                if was:
                    self._proj_dead[name] = True
                    self._issue("crash", name, f"exit {rc}")
                    self._tray("Dev Dashboard", be.tr(
                        "NAME_EXITED", name=name))
                be.save_projects(self.projects_data)

    def stop_project(self, name):
        p = self._proj(name)
        if not p:
            return False, be.tr("NAME_NOT_FOUND", name=name)
        proc = self._procs.get(name)
        with self._lock:
            job = self._jobs.pop(name, None)
        pid = p.get("pid")
        with self._lock:
            # pid=None до убийства: _wait_proc не примет остановку за краш
            p["pid"] = None
            p["pid_ctime"] = None
            self._proj_dead[name] = False
            be.save_projects(self.projects_data)
        if proc and proc.poll() is None:
            try:  # мягкое завершение, 3с на выход
                proc.terminate()
                proc.wait(timeout=3)
            except Exception:
                pass
        if job:
            job.terminate()          # добить всё дерево гарантированно
            job.close()
        if pid:
            # всегда: при job=None (отказ в назначении) без этого дети
            # процесса остаются сиротами; повторное убийство безопасно
            be.kill_proc_tree(pid)
        self._log(f"[{name}] " + be.tr("PROC_STOPPED",
                                       pid=pid))
        return True, ""

    def restart_project(self, name):
        self.stop_project(name)
        _timer(0.3, lambda: self.start_project(name))
        return True, ""

    def save_project(self, old_name, data):
        if not isinstance(data.get("name"), str) or not data["name"].strip():
            return False, be.tr("NAME_REQUIRED")
        with self._lock:
            if old_name:
                p = self._proj(old_name)
                if p is None:
                    return False, be.tr("NAME_NOT_FOUND", name=old_name)
                known = {"name", "cmd", "cwd", "url", "autostart"}
                for k in known - set(data):
                    p.pop(k, None)
                # cmd/cwd обязательны для probe/ports-путей — частичный
                # save без них ломал бы p["cwd"]-индексы
                data.setdefault("cmd", "")
                data.setdefault("cwd", "")
                data.setdefault("pid", p.get("pid"))
                p.update(data)  # неизвестные ключи + pid сохраняются
            else:
                data.setdefault("pid", None)
                self.projects_data.append(data)
            be.save_projects(self.projects_data)
        return True, ""

    def delete_project(self, name):
        p = self._proj(name)
        if not p:
            return False, be.tr("NAME_NOT_FOUND", name=name)
        with self._lock:
            self.projects_data.remove(p)
            be.save_projects(self.projects_data)
        return True, ""

    def add_projects(self, items):
        # whitelist: env_*/branch из скана — временные поля, их место не
        # в projects_config.json (пересчитываются живьём в _proj_row)
        KEEP = ("name", "cmd", "cwd", "url", "framework", "autostart")
        new = [{k: v for k, v in i.items() if k in KEEP}
               for i in items
               if isinstance(i, dict) and i.get("name") and i.get("cmd")]
        for i in new:
            i.setdefault("pid", None)
            i.setdefault("cwd", "")
        if new:
            with self._lock:
                self.projects_data.extend(new)
                be.save_projects(self.projects_data)
        return True, be.tr("ADDED_N", n=len(new))

    def scan_projects(self):
        known = {os.path.normcase(os.path.normpath(p["cwd"]))
                 for p in list(self.projects_data)}
        found, seen = [], set()
        for root in be.scan_roots():
            if not os.path.isdir(root):
                continue
            for p in be.scan_project_dirs(root, known):
                key = os.path.normcase(os.path.normpath(p["cwd"]))
                if key not in seen:
                    seen.add(key)
                    found.append(p)
        return {"found": found}

    # ---------- автозапуск ----------

    def toggle_autorun(self, name, enabled):
        try:
            be._autorun_set_enabled(name, enabled)
        except OSError as e:
            return False, be.tr("TOGGLE_FAIL",
                                name=name, e=e)
        self._log("[SYSTEM] " + be.tr(
            "AR_STATE", name=name,
            s=be.tr("ENABLED" if enabled else "DISABLED")))
        self._force_probe()
        return True, ""

    def write_autorun(self, name, cmd, old_name):
        if not name.strip() or not cmd.strip():
            return False, be.tr("NAME_CMD_REQUIRED")
        try:
            if old_name and old_name != name:
                pi.autorun_delete(old_name)
            pi.autorun_write(name, cmd)
        except OSError as e:
            return False, be.tr("AR_SAVE_FAIL",
                                name=name, e=e)
        self._log("[SYSTEM] " + be.tr("AR_SAVED",
                                      name=name))
        self._force_probe()
        return True, ""

    def delete_autorun(self, name):
        try:
            pi.autorun_delete(name)
        except OSError as e:
            return False, be.tr("AR_DEL_FAIL",
                                name=name, e=e)
        self._log("[SYSTEM] " + be.tr("AR_REMOVED",
                                      name=name))
        self._force_probe()
        return True, ""

    # ---------- общее ----------

    def open_project(self, name, what):
        """Открыть папку проекта в Проводнике или в IDE (cursor → code)."""
        p = self._proj(name)
        cwd = (p or {}).get("cwd") or ""
        if not p:
            return False, be.tr("NAME_NOT_FOUND", name=name)
        if not cwd or not os.path.isdir(cwd):
            return False, be.tr("PROJ_DIR_MISSING",
                                cwd=cwd or "—")
        if what == "open-ide":
            import shutil
            for exe in ("cursor", "code"):
                if shutil.which(exe):
                    subprocess.Popen(pi.shell_argv(f'{exe} "{cwd}"'),
                                     **pi.popen_kwargs())
                    return True, ""
            pi.open_path(cwd)  # нет IDE — хотя бы файловый менеджер
            return True, ""
        pi.open_path(cwd)
        return True, ""

    def open_target(self, url=None, path=None, editor=False):
        try:
            if url:
                pi.open_url(url)
                return True, ""
            if path and os.path.exists(path):
                if editor:
                    try:  # «Открыть в редакторе»: code → иначе ассоциация
                        subprocess.Popen(pi.shell_argv(f'code "{path}"'),
                                         **pi.popen_kwargs())
                        return True, ""
                    except OSError:
                        pass
                pi.open_path(path)
                return True, ""
        except OSError as e:
            return False, str(e)
        return False, be.tr("NOTHING_TO_OPEN")

    def pick_dir(self, start):
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            d = filedialog.askdirectory(parent=root, initialdir=start or None,
                                       title=be.tr("PROJ_FOLDER"))
            root.destroy()
            return {"dir": d or ""}
        except Exception as e:  # headless/нет tkinter — чистая ошибка, не 500
            return False, be.tr("PICK_DIR_FAIL", e=e)

    def port_targets(self, port):
        out = []
        for pid in be.pids_on_port(int(port)):
            try:
                out.append({"name": psutil.Process(pid).name(), "pid": pid})
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                out.append({"name": "?", "pid": pid})
        return out

    def _protected_pid(self, pid):
        """Системный/db-процесс, НЕ принадлежащий нашим сервисам и
        проектам — защита от случайного kill postgres/svchost."""
        try:
            name = psutil.Process(pid).name().lower()
        except (psutil.Error, OSError):
            return False
        cat, _ = be.port_class(name, 0)
        if cat not in ("sys", "db"):
            return False
        for spec in self.services_data:
            if spec.get("proc") and spec["proc"].lower() == name:
                return False
        for prj in self.projects_data:
            if prj.get("pid") == pid:
                return False
        return True

    def kill_pid(self, pid):
        """Убить процесс по pid (фоновые dev-процессы без портов)."""
        try:
            pid = int(pid)
        except (TypeError, ValueError):
            return False, be.tr("BAD_PID")
        if pid == os.getpid():
            return False, be.tr("CANT_KILL_SELF")
        if self._protected_pid(pid):
            return False, be.tr("PROTECTED_PROC")
        if be.kill_proc_tree(pid):
            self._log("[SYSTEM] " + be.tr("PROC_STOPPED",
                                          pid=pid))
            self._force_probe(800)
            return True, be.tr("PID_STOPPED", pid=pid)
        return False, be.tr("PID_STOP_FAIL",
                            pid=pid)

    def kill_port(self, port):
        try:
            port = int(port)
            if not 0 < port <= 65535:
                raise ValueError
        except (TypeError, ValueError):
            return False, be.tr("BAD_PORT")
        if port == self.api_port:
            return False, be.tr("CANT_KILL_SELF")
        if any(self._protected_pid(p) for p in be.pids_on_port(port)):
            return False, be.tr("PORT_PROTECTED", port=port)
        killed = be.kill_process_by_port(port)
        if killed:
            self._log("[SYSTEM] " + be.tr(
                "PORT_FREED_PIDS", port=port,
                pids=", ".join(map(str, killed))))
            self._force_probe(800)
            return True, be.tr("PORT_FREED", port=port)
        return False, be.tr("PORT_NO_LISTENERS", port=port)

    # ---------- API ----------

    def show_window(self):
        if self.show_cb:
            try:
                self.show_cb()
            except Exception:
                pass
        return True, ""

    def api_settings(self):
        """Текущие настройки ядра + мета (порт помечен restart-only)."""
        with self._lock:
            return {
                "probe_interval": self._probe_interval,
                "dep_timeout": self._dep_timeout,
                "backoff": list(self._backoff),
                "api_port": be.load_settings()["api_port"],
                "config_dir": be.DATA_DIR,
                "scan_roots": be.scan_roots(),
                "port_mine": be.load_settings()["port_mine"],
                "port_hidden": be.load_settings()["port_hidden"],
                "lang": be.load_settings()["lang"],
                "lang_resolved": be.lang(),
            }

    def save_settings(self, body):
        """Патч настроек из UI: валидация -> settings.json -> применить
        живьём. api_port не меняется без перезапуска — в ответ не входит."""
        with self._lock:
            patch = {}
            try:
                if "probe_interval" in body:
                    patch["probe_interval"] = min(
                        max(float(body["probe_interval"]), 0.5), 60.0)
                if "dep_timeout" in body:
                    patch["dep_timeout"] = min(
                        max(float(body["dep_timeout"]), 1.0), 120.0)
                if "backoff" in body:
                    bo = [min(max(float(x), 0.5), 300.0)
                          for x in body["backoff"]][:8]
                    if bo:
                        patch["backoff"] = bo
                if "scan_roots" in body:
                    roots, seen = [], set()
                    for r in body["scan_roots"][:20]:
                        r = str(r).strip()
                        if not r:
                            continue
                        r = os.path.normpath(r)
                        if os.path.normcase(r) not in seen:
                            seen.add(os.path.normcase(r))
                            roots.append(r)
                    patch["scan_roots"] = roots
                for key in ("port_mine", "port_hidden"):
                    if key in body:
                        lst, seen2 = [], set()
                        for x in body[key][:50]:
                            x = str(x).strip().lower()
                            if x and x not in seen2:
                                seen2.add(x)
                                lst.append(x)
                        patch[key] = lst
                if "lang" in body and str(body["lang"]) in be.LANGS:
                    patch["lang"] = str(body["lang"])
                if "api_port" in body:  # применится на следующем старте
                    p = int(body["api_port"])
                    if not 1024 <= p <= 65535:
                        raise ValueError
                    patch["api_port"] = p
            except (TypeError, ValueError):
                return False, be.tr("BAD_SETTINGS")
            saved = be.save_settings(patch)
            self._probe_interval = saved["probe_interval"]
            self._dep_timeout = saved["dep_timeout"]
            self._backoff = tuple(saved["backoff"])
            res = self.api_settings()
            res["restart_required"] = saved["api_port"] != self.api_port
            return res

    def api_ports(self):
        """TCP-слушатели + владелец (сервис/проект, в т.ч. через родителей
        и cwd в cmdline) + категория чужих и пользовательские метки."""
        procs, listeners, lan = be._proc_snapshot()
        by_pid = {p["pid"]: p for p in procs}
        with self._lock:  # снапшот shared-списков — записи идут под _lock
            svcs, prjs = list(self.services_data), list(self.projects_data)
        own = {}
        for spec in svcs:
            for p in procs:
                if (spec.get("proc") and p["name"] == spec["proc"].lower()) \
                        or (spec.get("match")
                            and spec["match"].lower() in p["cl"]):
                    own[p["pid"]] = spec["name"]
            # spawned/adopted pid сервиса без proc/match — тоже «наш»
            for pid in (spec.get("pid"),
                        (self._svc_spawn.get(spec["name"]) or (0,))[0]):
                if pid:
                    own[pid] = spec["name"]
        for prj in prjs:
            if prj.get("pid"):
                own[prj["pid"]] = prj["name"]
        st = be.load_settings()
        mine = {x.lower() for x in st["port_mine"]}
        hidden = {x.lower() for x in st["port_hidden"]}
        # процесс «наш», если его предок в own (npm -> node и т.п.)
        def own_owner(pid):
            seen, cur = set(), pid
            for _ in range(8):
                if cur in own:
                    return own[cur]
                if cur in seen:
                    break
                seen.add(cur)
                info = by_pid.get(cur)
                cur = info["ppid"] if info else 0
            return None

        def own_by_cwd(pid):
            cl = (by_pid.get(pid) or {}).get("cl", "")
            if not cl:
                return None
            for prj in prjs:
                raw = prj.get("cwd") or ""
                if not raw:
                    continue  # '' → normpath('.') матчил бы всё подряд
                cwd = os.path.normcase(os.path.normpath(raw))
                if cwd + os.sep in cl or cl.endswith(cwd):
                    return prj["name"]
            return None

        out = []
        for port, pid in sorted(listeners.items()):
            info = by_pid.get(pid)
            try:
                if info:
                    proc, cmd = info["name"], info["cmd"]
                    age = time.time() - info["proc"].create_time()
                else:
                    pp = psutil.Process(pid)
                    proc, cmd = pp.name(), " ".join(pp.cmdline() or [])
                    age = time.time() - pp.create_time()
            except (psutil.Error, OSError):
                proc, cmd, age = (info or {}).get("name", "?"), "", 0
            owner = own_owner(pid) or own_by_cwd(pid)
            cat, label = be.port_class(proc, port)
            out.append({"port": port, "pid": pid,
                        "proc": proc or "?", "cmd": cmd[:140],
                        "owner": owner, "self": pid == os.getpid(),
                        "cat": cat, "label": be.tr(label),
                        "lan": lan.get(port), "age": int(age),
                        "mine": (proc or "").lower() in mine,
                        "hidden": (proc or "").lower() in hidden})
        # page-title только на своих портах — чужие не дёргаем
        own_ports = [r["port"] for r in out
                     if r["owner"] or r["self"] or r["mine"]]
        if own_ports:
            with ThreadPoolExecutor(6) as ex:
                titles = dict(zip(own_ports,
                                  ex.map(be.page_title, own_ports)))
            for r in out:
                r["title"] = titles.get(r["port"], "")
        # фоновые dev-процессы без портов (как `ports ps` у kiri):
        # node/python/bun…, которые ничего не слушают — «idle-сервера»
        busy = set(listeners.values())
        # предки слушателей тоже заняты (npm -> node-обёртка):
        # иначе родительский dev-процесс ложно попадает в «без портов»
        for pid in list(busy):
            cur = by_pid.get(pid)
            for _ in range(8):
                ppid = (cur or {}).get("ppid")
                if not ppid:
                    break
                busy.add(ppid)
                cur = by_pid.get(ppid)
        bg = []
        for p in procs:
            if p["pid"] in busy or p["pid"] == os.getpid():
                continue
            cat, _ = be.port_class(p["name"], 0)
            if cat != "dev":
                continue
            try:
                mb = int(p["proc"].memory_info().rss / 1048576)
            except (psutil.Error, OSError):
                mb = 0
            bg.append({"name": p["name"], "pid": p["pid"], "mb": mb,
                       "owner": own_owner(p["pid"]) or own_by_cwd(p["pid"])})
        return {"ports": out, "bg": bg}

    def api_state(self):
        """Всё, что нужно UI одним запросом."""
        with self._lock:
            locals_ = [self._svc_row(s) for s in self.services_data
                       if not s.get("type")]
            remotes = [self._svc_row(s) for s in self.services_data
                       if s.get("type")]
            pinfo = getattr(self, "_proj_info", {})
            projects = [self._proj_row(p, pinfo.get(p["name"], {}))
                        for p in self.projects_data]
            mem = sum(r.get("m", {}).get("mb", 0)
                      for r in locals_ + remotes + projects)
            # сервис «в автозапуске»: имя записи Run, относящейся к нему
            entries = self._ar_mine + self._ar_other
            for r in locals_ + remotes:
                spec = self._service(r["name"]) or {}
                r["arName"] = self._ar_match(r["name"], spec, entries)
                r["inAutorun"] = bool(r["arName"])
            up_infra = sum(1 for r in locals_ + remotes if r["state"] == "up")
            return {"services": locals_, "remotes": remotes,
                    "projects": projects,
                    "autorunMine": self._ar_mine,
                    "autorunOther": self._ar_other,
                    "status": self._status, "problems": self._problems,
                    "issues": len(self._issues),
                    "infraUp": up_infra, "infraTotal": len(locals_) + len(remotes),
                    "platform": pi.PLATFORM,
                    "version": be.VERSION,
                    "lang": be.lang(),
                    "api_port": self.api_port,
                    "memMb": mem, "ts": time.time()}

    def api_projects(self):
        out = []
        for p in self.projects_data:
            out.append({"name": p["name"], "cmd": p["cmd"], "cwd": p["cwd"],
                        "url": p.get("url")
                        or self._detected_url.get(p["name"]) or None,
                        "running": be.is_pid_running(p.get("pid"), p.get("pid_ctime")),
                        "pid": p.get("pid")})
        return out

    def api_log(self, n, tag=""):
        n = int(n)
        with self._lock:
            entries = [e for e in self._log_entries
                       if not tag or e["tag"] == tag or e["tag"] == tag + " ERR"]
        return [e["raw"] for e in (entries[-n:] if n > 0 else [])]

    def api_service_log(self, name, n):
        """Логи сервиса: файл logs/<name>.log, иначе — событийный лог по тегу."""
        spec = self._service(name)
        path = self._log_path(spec) if spec else ""
        if path and os.path.exists(path):
            try:
                with open(path, "rb") as f:
                    f.seek(0, 2)
                    size = f.tell()
                    f.seek(max(0, size - 262144))
                    tail = f.read().decode("utf-8", errors="replace")
                lines = tail.splitlines()
                lines = lines[-int(n):] if int(n) > 0 else []
                return {"kind": "file",
                        "lines": [{"t": l, "l": classify_log_line(l)}
                                  for l in lines],
                        "path": path}
            except OSError:
                pass
        return {"kind": "events",
                "lines": [{"t": l, "l": classify_log_line(l)}
                          for l in self.api_log(n, tag=name)],
                "path": path}

    def api_services(self):
        """Сервисы для агентов: то же состояние, что видит UI."""
        out = []
        for s in self.services_data:
            st, detail = self._last_services.get(s["name"], ("check", ""))
            out.append({"name": s["name"], "sub": s.get("sub", ""),
                        "state": st, "detail": detail,
                        "remote": bool(s.get("type")),
                        "monitor_only": bool(s.get("monitor_only")),
                        "ports": s.get("ports", []),
                        "autorestart": bool(s.get("autorestart"))})
        return out

    def api_status(self):
        up = sum(1 for st, _ in self._last_services.values() if st == "up")
        return {"status": self._status,
                "problems": self._problems,
                "services_up": up,
                "services_total": len(self.services_data),
                "projects_running":
                    sum(1 for p in self.projects_data
                        if be.is_pid_running(p.get("pid"), p.get("pid_ctime"))),
                "ts": time.time()}

    def api_issues(self):
        with self._lock:
            return [{k: v for k, v in i.items() if k != "_rid"}
                    for i in list(self._issues)[-50:]]

    def clear_issues(self):
        self._issues.clear()
        return True, ""

    def api_runs(self, name):
        def strip(r):
            return {k: v for k, v in r.items() if k != "_rid"}
        if name:
            return [strip(r) for r in self._runs.get(name, ())]
        return {n: [strip(r) for r in dq] for n, dq in self._runs.items()}

    def api_action(self, name, action, kind="projects"):
        """Совместимость со старым API: /api/(projects|services)/X/start|stop|restart"""
        if kind == "services":
            spec = self._service(name)
            if not spec or spec.get("monitor_only") or spec.get("type"):
                return False
            st = self._last_services.get(name, (None,))[0]
            if action == "start" and st != "up":
                self._start_service(spec)
            elif action == "stop" and st == "up":
                self._stop_service(spec)
            elif action == "restart":
                if self._stop_service(spec):
                    _timer(1.5, lambda s=spec: self._start_service(s))
            return True
        p = self._proj(name)
        if not p:
            return False
        running = be.is_pid_running(p.get("pid"), p.get("pid_ctime"))
        if action == "start" and not running:
            self.start_project(name)
        elif action == "stop" and running:
            self.stop_project(name)
        elif action == "restart" and running:
            self.restart_project(name)
        return True

    # ---------- сервер ----------

    def _start_api(self):
        _ApiHandler.dash = self
        want = be.load_settings()["api_port"]
        self.api = None
        for cand in range(want, want + 10):  # порт занят → следующие 9
            try:
                self.api = _ApiServer(("127.0.0.1", cand), _ApiHandler)
                self.api_port = cand
                break
            except (OSError, OverflowError):  # OSError=занят, Overflow=мусор
                pass
        if self.api:
            # дочерние процессы (mcp_server и т.п.) узнают реальный порт
            os.environ["DEVDASH_PORT"] = str(self.api_port)
            try:  # маркер bound-порта: второй инстанс/MCP пингуют его
                with open(os.path.join(be.DATA_DIR, "api.port"), "w",
                          encoding="ascii") as f:
                    f.write(str(self.api_port))
            except OSError:
                pass
            threading.Thread(target=self.api.serve_forever,
                             daemon=True).start()
