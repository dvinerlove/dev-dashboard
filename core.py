"""Qt-free dashboard core: probe loop, state, actions, HTTP API + static.
Replaces bridge.py: same logic, direct calls under a lock instead of
QMetaObject, subprocess/threading instead of QProcess/QTimer."""
import json
import mimetypes
import os
import re
import subprocess
import sys
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

RESTART_BACKOFF = (2, 5, 10, 20)   # autorestart backoff steps
CIRCUIT_FAILS = 5                  # crashes in the window before circuit opens
CIRCUIT_WINDOW = 60                # crash counting window, sec
STABLE_UPTIME = 60                 # survived this long — crash counter resets
DEP_TIMEOUT = 15                   # dependency readiness wait, sec

STATIC_DIR = os.path.join(be.RESOURCE_DIR, "frontend", "dist")


_LOG_ERR_RE = re.compile(
    r"Traceback \(most recent call last\)|Exception:|\bERROR\b|\bFATAL\b|"
    r"EADDRINUSE|UnhandledPromiseRejection|SyntaxError|ModuleNotFoundError|"
    r"[\w.]*Error:", )
_LOG_WARN_RE = re.compile(r"\bwarn(?:ing)?\b|deprecated", re.I)
_ENV_SECRET_RE = re.compile(
    r"TOKEN|SECRET|KEY|PASSWORD|PASS|AUTH|CREDENTIAL|JWT|SESSION", re.I)
_PID_STATS_RE = re.compile(r"pid\s+(\d+).*?([\d.]+)%.*?(\d+)\s*MB(.*?(\d+)m)?")
_AR_FILE_RE = re.compile(r"[\w.-]+\.(?:py|cmd|bat|exe|ps1|vbs|com)\b", re.I)
_SCRIPT_EXT_RE = re.compile(
    r"\.(?:py|js|ts|mjs|cjs|mts|cts|rb|php|jar|dart)\b", re.I)
_LAUNCHER_EXT_RE = re.compile(r"\.(?:cmd|bat|ps1|sh|vbs)\b", re.I)
_VENV_DIR_RE = re.compile(
    r"[\\/](?:\.?venv|envs?|(?:mini|ana)?conda\d*)[\\/]", re.I)
_SHELL_PROCS = {"cmd", "powershell", "pwsh", "bash", "sh", "zsh", "wsl"}
# run-tools as an ancestor = the real launcher (npm run dev, go run,
# uv run x.py) — the ground truth of "how to start this" on any stack
_RUN_TOOLS = {"go", "cargo", "npm", "yarn", "pnpm", "bun", "deno",
              "make", "dotnet", "uv", "poetry", "gradle", "gradlew",
              "mvn", "flutter", "mix", "composer"}
# declared TS runners for a .ts script without a launcher (node >= 22.6
# runs .ts natively, so no entry = keep plain node)
_NODE_RUNNERS = {"tsx": "npx tsx", "ts-node": "npx ts-node",
                 "vite-node": "npx vite-node", "esno": "npx esno"}

# convention words (data, not vendors): a stem/dir like "index"/"src" says
# nothing about which project it is — smart naming climbs past them
_GENERIC_STEMS = {"index", "server", "main", "app", "bot", "run", "start",
                  "worker", "cli", "service", "daemon", "api", "core", "web",
                  "serve", "dev", "up"}
_GENERIC_DIRS = _GENERIC_STEMS | {"src", "dist", "build", "bin", "lib",
                                  "lib64", "scripts", "node_modules",
                                  "__pycache__", "out", "release", "debug"}


def _smart_name(stem, dpath):
    """Generic stem -> anchor to the nearest meaningful folder, e.g.
    index.ts in my-app\\server -> "my-app index"."""
    if stem.lower() not in _GENERIC_STEMS:
        return stem
    for d in reversed(dpath.replace("/", "\\").strip("\\").split("\\")):
        if d and not d.endswith(":") and d.lower() not in _GENERIC_DIRS:
            return f"{d} {stem}"
    return stem


def _shq(tok):
    """Re-quote a token that contained spaces (cmdline lists keep them)."""
    return f'"{tok}"' if " " in tok else tok


def _find_launcher(p_):
    """Parent chain -> real launcher: a script file run via shell (cmd /c
    x.cmd, pwsh -File x.ps1) or a run-tool cmdline (npm run dev, go run
    ./cmd, uv run x.py). Ground truth of "how to start this" — better than
    any command reconstructed from the child's own argv."""
    a_ = p_
    for _ in range(4):
        try:
            a_ = a_.parent() if a_ else None
            if not a_:
                return None
            an = a_.name().lower().removesuffix(".exe")
            atoks = a_.cmdline() or []
            if an in _RUN_TOOLS:
                return " ".join(_shq(x) for x in atoks), a_.cwd(), ""
            if an not in _SHELL_PROCS:
                return None  # non-shell ancestor: no script launcher above
            for t_ in atoks[1:]:
                if _LAUNCHER_EXT_RE.search(t_):
                    return _shq(t_), (os.path.dirname(t_)
                                     if os.path.isabs(t_) else a_.cwd()), \
                        os.path.splitext(os.path.basename(t_))[0]
        except (psutil.Error, OSError):
            continue  # one dead ancestor must not hide the launcher above
    return None


def _node_runner(sdir):
    """Nearest package.json -> declared TS runner (tsx/ts-node/...)."""
    d = sdir
    for _ in range(6):
        pj = os.path.join(d, "package.json")
        if os.path.isfile(pj):
            try:
                meta = json.load(open(pj, encoding="utf-8"))
                deps = {**meta.get("dependencies", {}),
                        **meta.get("devDependencies", {})}
            except (OSError, ValueError):
                return None
            return next((r for k, r in _NODE_RUNNERS.items()
                         if k in deps), None)
        nd = os.path.dirname(d)
        if nd == d:
            return None
        d = nd
    return None


def classify_log_line(line):
    """Log line level: error / warn / info."""
    if _LOG_ERR_RE.search(line):
        return "error"
    if _LOG_WARN_RE.search(line):
        return "warn"
    return "info"


_AGENTS = ("claude", "codex", "cursor", "windsurf", "aider")
_PREV_PIDS = set()  # live pids at the previous api_ports snapshot


def _agent_of(pid):
    """Name of an agent in the ancestor chain (<=8 levels, as own_owner):
    exe/cmdline of a parent contains a known agent name. None otherwise."""
    try:
        p = psutil.Process(pid)
    except (psutil.Error, OSError):
        return None
    for _ in range(8):
        try:
            p = p.parent()
            if not p:
                return None
            hay = ((p.exe() or "") + " "
                   + " ".join(p.cmdline() or [])).lower()
        except (psutil.Error, OSError):
            continue  # one dead ancestor must not hide the agent above
        for a in _AGENTS:
            if a in hay:
                return a
    return None


def _proc_flags(pid, info, pr, by_pid, age, prev):
    """(zombie, agent) for a ports row: zombie = cwd_missing/parent_dead/aged.
    parent_dead means orphaned on our watch — the parent was alive in the
    previous snapshot. Detached/system processes spawn parentless all the
    time; flagging them would be noise."""
    zombie = None
    try:
        if pr and not os.path.isdir(pr.cwd() or "."):
            zombie = "cwd_missing"
    except (psutil.Error, OSError):
        pass
    if zombie is None:
        try:
            ppid = info["ppid"] if info else (pr.ppid() if pr else 0)
        except (psutil.Error, OSError):
            ppid = 0
        if ppid and ppid in prev and not psutil.pid_exists(ppid):
            zombie = "parent_dead"
    if zombie is None and age >= 86400:
        zombie = "aged"
    return zombie, _agent_of(pid)



def _svc_sel(spec):
    """Typed inspector reference for a service spec (local or remote)."""
    return {"kind": "svc", "name": spec["name"],
            "remote": bool(spec.get("type"))}


def _prj_sel(name):
    """Typed inspector reference for a project."""
    return {"kind": "prj", "name": name}


def _own_owner(pid, own, by_pid):
    """Our service/project name if pid or an ancestor (<=8) is in own."""
    seen, cur = set(), pid
    for _ in range(8):
        if cur in own:
            return own[cur]
        if cur in seen:
            break
        seen.add(cur)
        cur = (by_pid.get(cur) or {}).get("ppid") or 0
    return None


def _timer(sec, fn):
    """Daemon timer: does not keep python.exe alive after tray exit."""
    t = threading.Timer(sec, fn)
    t.daemon = True
    t.start()


class _ApiServer(ThreadingHTTPServer):
    daemon_threads = True
    # on Windows SO_REUSEADDR allows a SECOND bind on a busy port —
    # the next-port fallback would not work then
    allow_reuse_address = not pi.IS_WIN

    def handle_error(self, request, client_address):
        pass  # keep-alive aborts by browser/webview — noise, not an error


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
        """DNS-rebinding guard: local Host only, otherwise a foreign domain
        pointing at 127.0.0.1 could read secrets from GET endpoints."""
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
            elif path == "/api/service-candidates":
                self._send(200, d.api_service_candidates())
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
            elif path == "/api/free-port":
                self._send(200, d.free_port(self._qint(q, "from", 8000)))
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
        """Serve the built frontend; SPA fallback to index.html."""
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
        # CSRF: allow only local Origins (or none — curl etc.)
        origin = self.headers.get("Origin")
        port = self.server.server_address[1]
        if origin and not re.match(
                r"^https?://(127\.0\.0\.1|localhost):%d$" % port, origin):
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
        if not 0 <= n <= 1 << 20:  # dashboard never needs more than 1 MB
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
            if env_m:  # PUT (and POST for simplicity): full env replacement
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
            ep_m = re.match(
                r"^/api/services/(.+)/env-(profiles|profile|secret)$", path)
            if ep_m:
                name, kind = unquote(ep_m.group(1)), ep_m.group(2)
                res = (d.save_env_profiles(name, body.get("profiles"))
                       if kind == "profiles"
                       else d.set_env_profile(name, body.get("profile", ""))
                       if kind == "profile"
                       else d.set_env_secret(name, body.get("key"),
                                             body.get("value", "")))
                if res is None:
                    self._send(404, {"error": "not found"})
                elif res is False or isinstance(res, tuple):
                    self._send(400, {"error": res[1] if res
                                     else "bad profiles"})
                else:
                    self._send(200, res)
                return
            m = re.match(r"^/api/(projects|services)/(.+)/(start|stop|restart)$",
                         path)
            if m:  # compat with the old API
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
                "/api/self-update": d.self_update,
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
    """Dashboard state + actions. tray_cb/info_cb are shell callbacks."""

    def __init__(self):
        self.projects_data = be.load_projects()
        self.services_data = be.load_services()
        self.tray_cb = None      # (title, msg) — tray notification
        self.info_cb = None      # (msg) — UI toast (currently via API responses)

        self._lock = threading.RLock()
        self._procs = {}          # name -> Popen (started by the dashboard)
        self._svc_spawn = {}      # name -> (pid, ctime) of the service shell wrapper
        self._svc_stop_gen = {}   # name -> intentional-stop generation
        self._proj_dead = {}      # name -> had a crash ("dead" pill)
        self._proj_seen = set()   # names witnessed alive this session —
        # a persisted pid that vanished while we were down is "not
        # running", not a crash; only witnessed deaths get the dead pill
        self._detected_url = {}   # name -> url
        self._fw_cache = {}      # cwd -> framework label
        self._envinfo = {}       # cwd -> (ts, env+branch fields), TTL 30s
        self._envval = {}        # (env_file,key) -> (ts, value), TTL 30s
        self._last_services = {}
        self._svc_prev = {}
        self._jobs = {}           # name -> process_tree.Job
        self._crash_ts = {}       # name -> [ts] of crashes (sliding window)
        self._quick_fails = {}    # name -> consecutive quick crashes (backoff)
        self._cb_open = set()     # circuit breaker: autorestart disabled
        self._svc_up_since = {}   # name -> ts of the transition to up
        self._watch_mtime = {}    # name -> last seen cwd mtime (watch mode)
        self._uptime = {}         # remote name -> (ts, uptime%), TTL 30s
        st_cfg = be.load_settings()
        self._backoff = tuple(st_cfg["backoff"]) or RESTART_BACKOFF
        self._dep_timeout = st_cfg["dep_timeout"] or DEP_TIMEOUT
        self._probe_interval = st_cfg["probe_interval"] or 4
        self.api_port = st_cfg["api_port"]   # updated to the real one on bind
        self._err_issues = {}     # (name) -> last log_error issue (dedup)
        self._svc_cpu = {}
        self._proj_cpu = {}
        self._remote_next = {}
        self._remote_last = {}
        self._remote_hist = {}    # name -> deque of the last 30 ms values
        self._log_off = {}        # service name -> read offset of logs/<name>.log
        self._last_listeners = None  # port -> pid of the previous probe tick
        self._probing = False
        self._probe_t0 = 0.0
        self._sniff = {}          # port -> (ts, (title, favicon)) — 60s
        self._sniff_busy = False
        self._issues = deque(maxlen=120)   # deduplicated events
        self._runs = {}                    # name -> deque of recent runs
        self.show_cb = None     # () — raise the window (single-instance)
        try:  # history from state.db
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
        self._log_entries = deque(maxlen=2000)  # event log (in-memory)
        self._stop = threading.Event()
        self.api = None

    # ---------- lifecycle ----------

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
        # autostart projects marked autostart
        for p in list(self.projects_data):
            if p.get("autostart") and not be.is_pid_running(p.get("pid"), p.get("pid_ctime")):
                self.start_project(p["name"])

    def stop(self):
        self._stop.set()
        # clean exit: clear KILL_ON_JOB_CLOSE — services survive
        # dashboard exit; if the dashboard crashes, trees die on their own
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

    # ---------- log ----------

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
        be.append_dashboard_log(text)

    def log_line(self, text):
        self._log(text)

    # ---------- probes ----------

    def refresh_probe(self):
        if self._probing:
            if time.time() - self._probe_t0 < 90:  # stuck worker → reset flag
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
            self._watch_ports(procs, listeners)
            self._scan_service_logs()
            services = {}
            remotes = []
            mem_over = {}
            watch_chg = set()     # names whose watched cwd mtime grew
            for s in list(self.services_data):
                if s.get("type"):
                    remotes.append(s)
                else:
                    try:  # a broken spec in config must not kill all probes
                        res = be._probe_service(
                            s, procs, listeners, self._svc_cpu,
                            confirm_dead=self._svc_prev.get(s["name"]) == "up")
                        # service started by us without proc/match: the probe
                        # cannot see it — "alive" via wrapper pid (ours or spec's)
                        if res[0] == "down" and not s.get("monitor_only"):
                            with self._lock:  # _svc_spawn is written under _lock
                                ent = self._svc_spawn.get(s["name"])
                                if ent is None and not s.get("proc") \
                                        and not s.get("match"):
                                    ent = (s.get("pid"), s.get("pid_ctime"))
                                if ent and be.is_pid_running(*ent):
                                    res = ("up", f"pid {ent[0]}")
                                elif s["name"] in self._svc_spawn:
                                    del self._svc_spawn[s["name"]]  # wrapper gone
                        services[s["name"]] = res
                        lim = s.get("mem_limit_mb")
                        if res[0] == "up" and lim \
                                and not s.get("monitor_only"):
                            mb = self._svc_tree_mb(s, procs)
                            if mb > lim:
                                mem_over[s["name"]] = (int(mb), lim)
                    except Exception:
                        services[s["name"]] = ("dead", "bad spec")
                    try:  # watch: fs walk must never break the probe;
                        # down/dead re-baselines — changes while stopped
                        # must not fire on the next start
                        if s.get("watch") and s.get("cwd") \
                                and not s.get("monitor_only"):
                            mt = be.latest_mtime(s["cwd"])
                            if res[0] != "up" or not mt:
                                self._watch_mtime.pop(s["name"], None)
                            else:
                                prev_mt = self._watch_mtime.get(s["name"])
                                if prev_mt and mt > prev_mt \
                                        and s.get("start"):
                                    watch_chg.add(s["name"])
                                self._watch_mtime[s["name"]] = mt
                    except Exception:
                        pass
            for pid in list(self._svc_cpu):
                if not psutil.pid_exists(pid):
                    del self._svc_cpu[pid]
            now = time.time()
            due = [s for s in remotes
                   if now >= self._remote_next.get(s["name"], 0)]
            if due:  # remote probes in parallel, each on its own interval
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
                        try:  # uptime sampling — non-critical
                            st.remote_probe(s["name"], res[0] == "up")
                        except Exception:
                            pass
                        if s.get("type") in ("http", "tcp"):
                            m = re.search(r"(\d+)\s*ms\b", res[1] or "")
                            if m:
                                self._remote_hist.setdefault(
                                    s["name"], deque(maxlen=30)
                                ).append(int(m.group(1)))
            for s in remotes:  # not due yet — show the previous result
                services.setdefault(
                    s["name"], self._remote_last.get(s["name"], ("check", "…")))

            # projects: pid + metrics + ports — heavy scan here, not the GUI tick
            # one cwd sweep per tick: a dev server started outside the
            # dashboard (cmd/npm/IDE) often carries no project path in
            # exe/cmdline, but its working dir sits inside the project tree
            proc_cwds = {}
            pidless = any(
                not be.is_pid_running(p.get("pid"), p.get("pid_ctime"))
                for p in list(self.projects_data))
            if pidless:  # the sweep exists for adoption — idle otherwise
                for pr_ in psutil.process_iter():
                    try:
                        c = pr_.cwd()
                        if c:
                            proc_cwds[pr_.pid] = os.path.normcase(
                                os.path.normpath(c))
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            projects = {}
            claims = {}  # pid -> (project, cwd depth) — one pid, one owner
            cand = {}
            for p in list(self.projects_data):
                pid = p.get("pid")
                if not be.is_pid_running(pid, p.get("pid_ctime")):
                    pid = be.find_project_pid(p, proc_cwds)
                cand[p["name"]] = (p, pid)
                if pid:
                    depth = len(os.path.normpath(
                        p.get("cwd") or "").split(os.sep))
                    cur = claims.get(pid)
                    if cur is None or depth > cur[1]:
                        claims[pid] = (p, depth)
            for p, pid in cand.values():
                if pid and claims.get(pid, (None,))[0] is not p:
                    pid = None  # contested — the longest-cwd project owns it
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
            self._apply_probe(
                (services, projects, autorun, mem_over, watch_chg))
        except Exception:
            import traceback
            self._log("[SYSTEM] probe worker crashed: "
                      + traceback.format_exc())
            self._probing = False

    def _svc_tree_mb(self, spec, procs):
        """Total RSS of the service tree in MB: matched pids or, for a
        proc/match-less spec, the spawned/adopted wrapper pid."""
        pids = [p["pid"] for p in procs
                if (spec.get("proc") and p["name"] == spec["proc"])
                or (spec.get("match") and spec["match"].lower() in p["cl"])]
        if not pids:
            ent = self._svc_spawn.get(spec["name"]) \
                or (spec.get("pid"), spec.get("pid_ctime"))
            if ent[0]:
                pids = [ent[0]]
        total = 0
        for pid in pids:
            try:
                pr = psutil.Process(pid)
                total += pr.memory_info().rss + sum(
                    c.memory_info().rss for c in pr.children(recursive=True))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return total / 1048576

    def _watch_ports(self, procs, listeners):
        """New foreign LISTEN port or an owner-pid change -> tray notice.
        The first snapshot after start is quiet; ours/mine are skipped."""
        prev = self._last_listeners
        self._last_listeners = dict(listeners)
        if prev is None:
            return
        mine = {x.lower() for x in be.load_settings()["port_mine"]}
        by_pid = {p["pid"]: p for p in procs}
        own = self._own_pids(procs, list(self.services_data),
                             list(self.projects_data))
        for port, pid in listeners.items():
            proc = (by_pid.get(pid) or {}).get("name", "?")
            if pid == os.getpid() or proc in mine \
                    or _own_owner(pid, own, by_pid):
                continue
            if port not in prev:
                self._tray("Dev Dashboard",
                           be.tr("PORT_NEW", port=port, proc=proc))
            elif prev[port] != pid:
                self._tray("Dev Dashboard",
                           be.tr("PORT_OWNER", port=port, proc=proc))

    def _scan_service_logs(self):
        """New lines of logs/<name>.log since the last read -> error lines
        -> log_error issues. The first read positions at EOF — history
        is not parsed; a truncated file (clear log) restarts from 0."""
        for spec in list(self.services_data):
            if spec.get("type"):
                continue
            path = be._service_log_path(spec)
            try:
                size = os.path.getsize(path)
            except OSError:
                continue
            off = self._log_off.get(spec["name"])
            if off is None or off > size:
                self._log_off[spec["name"]] = size
                continue
            try:
                with open(path, "rb") as f:
                    f.seek(off)
                    data = f.read()
                    self._log_off[spec["name"]] = f.tell()
            except OSError:
                continue
            for line in be.decode_log(data).splitlines():
                if line and classify_log_line(line) == "error":
                    self._issue_log_error(spec["name"], line, sel=_svc_sel(spec))

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
        for pt in spec.get("ports", ()):  # port lives in the chip — drop from subtitle
            sub = re.sub(rf"\s*·?\s*:{pt}\b", "", sub, count=1)
        if spec.get("autorestart"):
            ar = be.tr("AUTORESTART")
            sub = (sub + " · " + ar) if sub else ar
        metrics = be.tr_detail(detail) if state in ("up", "off") else ""
        metrics = re.sub(r"^:\d+(\s*·\s*)?", "", metrics)  # port already in the chip
        chip = re.sub(r"^(127\.0\.0\.1|localhost|0\.0\.0\.0):", ":", chip)
        row = {"name": spec["name"], "sub": sub,
               "state": state or "check", "pillText": be.tr(word), "tone": tone,
               "failed": state in ("dead", "failed"),
               "metrics": metrics, "warn": state == "off" and bool(detail),
               "chip": chip, "chipUrl": chip_url, "monitor": monitor,
               "reason": reason, "squatterPort": squatter,
               # raw (untranslated) reason kind for frontend checks —
               # `reason` itself is localized, comparing it to keys is locale-brittle
               "reasonKey": "circuit_open" if state == "failed" else "",
               "autorestart": bool(spec.get("autorestart")),
               "hasToken": bool(spec.get("env_key") and spec.get("env_file")),
               "hasUrl": bool(url), "hasPath": bool(spec.get("path")),
               "remote": bool(spec.get("type")),
               "deps": spec.get("depends_on") or [],
               "env_profiles": sorted(spec.get("env_profiles") or {}),
               "env_profile": spec.get("env_profile") or ""}
        # structured metrics for the UI: 'pid 19676 · 0% · 352MB · 7h12m'
        m = _PID_STATS_RE.search(detail or "")
        if state == "up" and m:
            row["m"] = {"pid": int(m.group(1)),
                        "cpu": float(m.group(2)),
                        "mb": int(m.group(3)),
                        "up": be.tr_detail(
                            (m.group(4) or "").strip(" ·"))}
        # dynamic check: env_key is really missing from env_file;
        # 30s cache — do not re-read the file on every state poll
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
        if spec.get("type"):  # remote latency history (last 30 probes)
            row["ms_hist"] = list(self._remote_hist.get(spec["name"], ()))
            ent = self._uptime.get(spec["name"])  # 30s cache — 1 SELECT/remote
            if ent is None or time.time() - ent[0] > 30:
                try:
                    ent = (time.time(), st.uptime_pct(spec["name"]))
                except Exception:
                    ent = (time.time(), None)
                self._uptime[spec["name"]] = ent
            row["uptime"] = ent[1]
        return row

    def _env_info(self, cwd):
        """env-diff + gitignore-cover + project branch; 30s cache so
        /api/state does not open ~7 files per project on each poll."""
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
        # .env vs .env.example diff + gitignore-cover + branch (30s cache)
        if cwd:
            row.update(self._env_info(cwd))
        m = _PID_STATS_RE.search(info.get("stats") or "")
        if running and m:
            row["m"] = {"pid": int(m.group(1)), "cpu": float(m.group(2)),
                        "mb": int(m.group(3)), "up": ""}
        return row

    def _ar_row(self, n, c, running, mine, enabled):
        if not enabled:
            # off is visible on the toggle — no need to duplicate in metrics
            pill, tone, metrics = be.tr("STATE_OFF"), "dim", ""
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
        """Tokens of "own" autorun entries: service name variants and file
        stems from their start — the same needles as _ar_match."""
        toks = set()
        for spec in self.services_data:
            n = spec["name"].lower()
            toks.update((n, n.replace(" ", "-"), n.replace(" ", "_")))
            for t in _AR_FILE_RE.findall(spec.get("start") or ""):
                toks.add(os.path.splitext(os.path.basename(t))[0].lower())
        return toks

    def _ar_match(self, name, spec, entries):
        """Name of the autorun entry belonging to the service (or None).
        Needles: service name, -/_ variants and exe stem from start
        ("pythonw my_app.py serve" → "my_app", name "my app serve" →
        "my-app-serve", matching the my-app-serve.cmd entry)."""
        needles = {name.lower(),
                   name.lower().replace(" ", "-"),
                   name.lower().replace(" ", "_")}
        for tok in _AR_FILE_RE.findall(spec.get("start") or ""):
            needles.add(os.path.splitext(os.path.basename(tok))[0].lower())
        for e in entries:
            s = (e["name"] + " " + e["sub"]).lower()
            if any(len(n) >= 4 and n in s for n in needles):
                return e["name"]
        return None

    def _apply_probe(self, res):
        services, projects, autorun, mem_over, watch_chg = res
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
                    self._run_start(name)      # external or our start — record it
                if prev == "up" and st in ("down", "dead"):
                    self._run_end(name, st)
                if prev == "up" and st == "dead":
                    detail = services.get(name, ("", ""))[1]
                    kind = "port" if " busy" in detail else "crash"
                    self._issue(kind, name, be.tr_detail(detail)
                                or be.tr("EXITED"), sel=_svc_sel(spec))
                    self._tray("Dev Dashboard",
                               be.tr("NAME_EXITED",
                                     name=name))
                # watchdog: backoff + circuit breaker on up -> down/dead transition
                if spec.get("autorestart") and not spec.get("monitor_only") \
                        and not spec.get("type") and spec.get("start") \
                        and st in ("down", "dead") and prev == "up":
                    self._svc_autorestart(spec)
                self._svc_prev[name] = st
                # planned restarts (mem limit / file watch / interval):
                # stop + relaunch through the crash budget — a trigger
                # firing every probe tick trips the circuit instead of
                # looping. _svc_autorestart does not consult the
                # autorestart flag: the trigger itself opts the service in
                if st == "up" and spec.get("start") \
                        and not spec.get("type") and not spec.get("monitor_only"):
                    mo = mem_over.get(name)
                    every = spec.get("restart_every_min") or 0
                    if mo:
                        why, detail = be.tr("MEM_LIMIT", mb=mo[0],
                                            lim=mo[1]), "memory limit"
                    elif name in watch_chg:
                        why, detail = be.tr("WATCH_RESTART"), "files changed"
                    elif every and time.time() - \
                            self._svc_up_since.get(name, 0) > every * 60:
                        why, detail = be.tr("CRON_RESTART",
                                            min=every), "scheduled restart"
                    else:
                        why = None
                    if why:
                        self._issue("restart", name, why, sel=_svc_sel(spec))
                        self._log(f"[{name}] {why}")
                        self._stop_service(spec)
                        # mark the planned stop: not a crash on the next tick,
                        # and _autorestart_fire must not see a stale "up"
                        self._last_services[name] = ("down", detail)
                        self._svc_prev[name] = "down"
                        self._svc_autorestart(spec)

            ok = sum(1 for st, _ in services.values() if st == "up")
            problems = [{"name": n, "why": be.tr_detail(detail)}
                        for n, (st, detail) in services.items()
                        if st in ("down", "dead")
                        and not specs.get(n, {}).get("note")]
            self._proj_info = projects
            for p in self.projects_data:
                info = projects.get(p["name"], {})
                pid = info.get("pid")
                if not pid and p["name"] in self._procs:
                    continue  # dashboard-started: _wait_proc owns its death
                if pid:
                    # witnessed alive this session — also when the pid simply
                    # persists (no transition): a dev server that survived our
                    # own restart is as witnessed as a freshly adopted one,
                    # its later death must not go silent
                    self._proj_seen.add(p["name"])
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
                        if p["name"] in self._proj_seen \
                                and p["name"] not in self._procs:
                            # died outside the dashboard — mark "dead"
                            self._proj_dead[p["name"]] = True
                            self._issue("crash", p["name"],
                                        be.tr("EXITED"), sel=_prj_sel(p["name"]))
                            self._tray("Dev Dashboard", be.tr(
                                "NAME_EXITED",
                                name=p["name"]))
                if not p.get("url"):
                    ports = info.get("ports") or []
                    self._detected_url[p["name"]] = \
                        f"http://127.0.0.1:{ports[0]}" if ports else ""
                if info.get("running"):
                    ok += 1

            mine, other = [], []
            for n, c, r, mn, e in autorun:
                own = be.self_autorun_is(n, c)  # наша запись — всегда «своя»
                row = self._ar_row(n, c, r, mn or own, e)
                if own:
                    row["self"] = True
                (mine if mn or own else other).append(row)
            self._ar_mine, self._ar_other = mine, other
            ok += sum(1 for _, _, r, mn, e in autorun if r and e)
            known = {p["name"] for p in problems}
            problems += [{"name": n, "why": be.tr("AR_PROBLEM")}
                         for n, _, r, mn, e in autorun
                         if not r and mn and e and n not in known]

            self._problems = problems
            status = be.tr("N_OK", n=ok)
            if problems:
                status += f"  ·  ⚠ {len(problems)}: " \
                          + ", ".join(p["name"] for p in problems[:3]) \
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
        """Crash of an autorestart service: backoff 2→5→10→20s, circuit
        breaker after 5 crashes in 60s."""
        name = spec["name"]
        if name in self._cb_open:
            return
        now = time.time()
        up = self._svc_up_since.pop(name, 0)  # consume: a run of insta-crashes
        if up and now - up > STABLE_UPTIME:   # without up it must not reset the count
            self._quick_fails[name] = 0      # ran long — count from scratch
            self._crash_ts.pop(name, None)
        ts = self._crash_ts.setdefault(name, [])
        ts.append(now)
        ts[:] = [t for t in ts if now - t < CIRCUIT_WINDOW]
        if len(ts) >= CIRCUIT_FAILS:
            self._cb_open.add(name)
            self._issue("crash_loop", name,
                        be.tr("CRASHES_HALT",
                              n=CIRCUIT_FAILS, w=CIRCUIT_WINDOW),
                        sel=_svc_sel(spec))
            self._tray("Dev Dashboard", be.tr("NAME_CRASH_LOOP", name=name))
            return
        self._quick_fails[name] = self._quick_fails.get(name, 0) + 1
        delay = self._backoff[
            min(self._quick_fails[name] - 1, len(self._backoff) - 1)]
        self._issue("restart", name,
                    be.tr("AR_IN", d=delay), sel=_svc_sel(spec))
        self._log(f"[{name}] " + be.tr(
            "AR_IN_DEAD", d=delay))
        gen = self._svc_stop_gen.get(name, 0)
        _timer(delay, lambda s=spec, g=gen: self._autorestart_fire(s, g))

    def _autorestart_fire(self, spec, gen=None):
        """Deferred autorestart: do not resurrect a service that was deleted,
        already brought up, cut off by the circuit, or stopped by the user
        after the restart was scheduled (stop-generation moved on)."""
        if spec not in self.services_data:
            return
        if gen is not None \
                and self._svc_stop_gen.get(spec["name"], 0) != gen:
            return
        name = spec["name"]
        if name in self._cb_open:
            return
        if self._last_services.get(name, (None,))[0] == "up":
            return
        self._start_service(spec)

    def _issue(self, kind, name, text, sel=None):
        """Event into the issues feed; a repeat of the same kind only bumps the count.
        `sel` — typed entity reference {kind,name,remote?}: the emitter always
        knows statically whether the event is about a service or a project,
        and the frontend jumps straight to it without re-resolving by name."""
        with self._lock:
            it = self._issues[-1] if self._issues else None
            if it and it["kind"] == kind and it["name"] == name \
                    and it.get("sel") == sel:
                it["count"] += 1
                it["t"] = time.time()
                if sel and "sel" not in it:
                    it["sel"] = sel  # legacy linkless row — adopt the type
            else:
                it = {"t": time.time(), "kind": kind,
                      "name": name, "text": text, "count": 1}
                if sel:
                    it["sel"] = sel
                self._issues.append(it)
        try:
            st.save_issue(it)
        except Exception:
            pass

    def _issue_log_error(self, name, text, sel=None):
        """Error from a service/project log: text dedup within a 60s window (×N)."""
        text = text.strip()[:300]
        now = time.time()
        key = (name, (sel or {}).get("kind"), (sel or {}).get("remote"))
        with self._lock:
            it = self._err_issues.get(key)
            if it and it["text"] == text and now - it["t"] < 60:
                it["count"] += 1
                it["t"] = now
            else:
                it = {"t": now, "kind": "log_error", "name": name,
                      "text": text, "count": 1}
                if sel:
                    it["sel"] = sel
                self._err_issues[key] = it
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

    # ---------- services ----------

    def _service(self, name):
        return next((s for s in self.services_data if s["name"] == name), None)

    def service_spec(self, name):
        return dict(self._service(name) or {})

    def service_env(self, name, reveal=False):
        """Service ENV overrides; secret keys and cred: refs are masked
        without reveal. reveal resolves cred: via the OS keystore —
        an unsupported platform or a missing entry shows the literal
        "cred:<target>" ref."""
        spec = self._service(name)
        if not spec:
            return None
        env = spec.get("env") or {}

        def value(k, v):
            v = str(v)
            if v.startswith("cred:"):
                return (pi.cred_read(v[5:]) or v) if reveal \
                    else "••••••••"
            return v if reveal or not _ENV_SECRET_RE.search(k) \
                else "••••••••"

        return [{"key": k, "value": value(k, v),
                 "secret": bool(_ENV_SECRET_RE.search(k))
                 or str(v).startswith("cred:")}
                for k, v in env.items()]

    def save_env(self, name, env):
        """PUT: full replacement of env overrides. Never log values!"""
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
            old_targets = {v[5:] for v in (spec.get("env") or {}).values()
                           if isinstance(v, str) and
                           v.startswith("cred:DevDashboard/")}
            new_targets = {v[5:] for v in env.values()
                           if v.startswith("cred:DevDashboard/")}
            if env:
                spec["env"] = env
            else:
                spec.pop("env", None)
            be.save_services(self.services_data)
        # unreferenced cred: targets are deleted — a rename keeps the same
        # target referenced, a true row deletion drops it
        for target in old_targets - new_targets:
            try:
                pi.cred_delete(target)
            except OSError:
                pass
        st = self._last_services.get(name, (None,))[0]
        res = {"restart_required": st == "up"}
        w = be.validate_env(env)
        if w:
            res["warnings"] = w
        return res

    def save_env_profiles(self, name, profiles):
        """PUT: full replacement of named env_profiles (never log values!)."""
        spec = self._service(name)
        if not spec:
            return None
        if spec.get("type") or spec.get("monitor_only"):
            return False, be.tr("ENV_MONITOR_ONLY")
        if profiles is None:
            profiles = {}
        if not isinstance(profiles, dict) or not all(
                isinstance(v, dict) for v in profiles.values()):
            return False, be.tr("PROFILES_NOT_OBJ")
        profiles = {str(k).strip(): {str(kk): str(vv)
                                     for kk, vv in v.items()
                                     if str(kk).strip()}
                    for k, v in profiles.items() if str(k).strip()}
        with self._lock:
            if profiles:
                spec["env_profiles"] = profiles
            else:
                spec.pop("env_profiles", None)
            be.save_services(self.services_data)
        st = self._last_services.get(name, (None,))[0]
        res = {"restart_required": st == "up"}
        w = [x for pname, p in profiles.items()
             for x in be.validate_env(p, prefix=f"{pname}.")]
        if w:
            res["warnings"] = w
        return res

    def set_env_profile(self, name, profile):
        """POST: select the active env_profile ("" = none)."""
        spec = self._service(name)
        if not spec:
            return None
        if spec.get("type") or spec.get("monitor_only"):
            return False, be.tr("ENV_MONITOR_ONLY")
        profile = str(profile or "").strip()
        if profile and profile not in (spec.get("env_profiles") or {}):
            return False, be.tr("PROFILE_NOT_FOUND", name=profile)
        with self._lock:
            if profile:
                spec["env_profile"] = profile
            else:
                spec.pop("env_profile", None)
            be.save_services(self.services_data)
        st = self._last_services.get(name, (None,))[0]
        return {"restart_required": st == "up"}

    def set_env_secret(self, name, key, value):
        """POST: store a secret in the OS credential store; spec.env keeps
        only "cred:DevDashboard/<name>/<key>". save_env deletes the
        credential once no env value references its target anymore."""
        spec = self._service(name)
        if not spec:
            return None
        if spec.get("type") or spec.get("monitor_only"):
            return False, be.tr("ENV_MONITOR_ONLY")
        if not pi.IS_WIN:
            return False, be.tr("CRED_UNSUPPORTED")
        key = str(key or "").strip()
        if not key:
            return False, be.tr("NAME_REQUIRED")
        target = f"DevDashboard/{name}/{key}"
        try:
            ok = pi.cred_write(target, str(value))
        except OSError:
            ok = False
        if not ok:
            return False, be.tr("CRED_WRITE_FAIL", target=target)
        with self._lock:
            spec.setdefault("env", {})[key] = f"cred:{target}"
            be.save_services(self.services_data)
        st = self._last_services.get(name, (None,))[0]
        return {"restart_required": st == "up"}

    def self_update(self):
        """POST: upgrade to the latest release and restart. Channel decides
        the mechanism: winget/scoop defer to their package manager, git
        swaps the exe directly. A detached .bat does the swap after this
        process exits — a running exe cannot overwrite itself."""
        import tempfile
        if getattr(self, "_update_in_progress", False):
            return False, be.tr("UPDATE_IN_PROGRESS")
        self._update_in_progress = True
        import tempfile
        ch = be.update_channel()
        if ch == "dev":
            self._update_in_progress = False
            return False, be.tr("UPDATE_DEV_MODE")
        rel = None
        if ch == "git":
            rel = be.fetch_latest_release()
            if not rel or not rel["zip_url"]:
                return False, be.tr("UPDATE_CHECK_FAILED")
            if be.semver_key(rel["tag"]) <= be.semver_key(be.VERSION):
                return False, be.tr("UPDATE_NONE")
        target, pid = sys.executable, os.getpid()
        tmp = os.path.join(tempfile.gettempdir(), "devdash-update")
        os.makedirs(tmp, exist_ok=True)
        try:
            if ch == "git":
                action = ("copy", be.download_update_zip(rel["zip_url"], tmp))
            elif ch == "winget":
                action = ("cmd",
                          f"winget upgrade --id {be.WINGET_ID} -e --silent"
                          " --accept-source-agreements"
                          " --accept-package-agreements")
            else:  # scoop — shim target stays valid through the re-junction
                action = ("cmd", "scoop update dev-dashboard")
            ps1 = be.write_update_helper(target, pid, action,
                                         os.path.join(tmp,
                                                      "apply-update.ps1"),
                                         port=self.api_port,
                                         port_file=os.path.join(
                                             be.DATA_DIR, "api.port"))
        except (OSError, ValueError, urllib.error.URLError) as e:
            self._update_in_progress = False
            return False, str(e)[:200]
        # CREATE_NO_WINDOW only: DETACHED_PROCESS leaves powershell.exe
        # (a console app) without a console and it never runs; windows
        # children outlive the parent anyway
        subprocess.Popen(["powershell", "-NoProfile", "-ExecutionPolicy",
                          "Bypass", "-File", ps1],
                         creationflags=getattr(subprocess,
                                               "CREATE_NO_WINDOW", 0),
                         close_fds=True)

        def _quit_later():  # let the HTTP response flush first
            time.sleep(1.0)
            cb = getattr(self, "quit_cb", None)
            if cb:
                cb()
        threading.Thread(target=_quit_later, daemon=True).start()
        return {"channel": ch, "version": rel["tag"] if rel else "",
                "restart_required": True}

    # ---------- projects ----------

    def _project(self, name):
        return next((p for p in self.projects_data if p["name"] == name),
                    None)

    def project_env(self, name, reveal=False):
        """Project ENV = its .env + missing keys from .env.example;
        secrets are masked without reveal."""
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
        """PUT: rewrite project .env with payload keys — file comments
        and blank lines are preserved, removed keys are dropped."""
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
        res = {"ok": True}
        w = be.validate_env(env)
        if w:
            res["warnings"] = w
        return res

    def _start_service(self, spec, _depth=0, _seen=None):
        # depends_on: start up dead dependencies and wait for their
        # readiness (health_url → HTTP, port → TCP, else "alive 0.5s")
        if _seen is None:
            _seen = {spec["name"]}
        waiting = []
        for dep in spec.get("depends_on", ()):
            if dep in _seen:
                self._issue("dep_cycle", spec["name"],
                            be.tr("DEP_CYCLE_VIA", dep=dep),
                            sel=_svc_sel(spec))
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
                                  dep=dep["name"], t=self._dep_timeout),
                            sel=_svc_sel(spec))
                self._log(f"[{spec['name']} ERR] " + be.tr(
                    "DEP_FAIL",
                    dep=dep["name"]))
                self._info(be.tr("DEP_FAIL_NAME",
                                 name=spec["name"], dep=dep["name"]))
                return False
        self._do_start(spec)
        return True

    def _wait_ready(self, spec, timeout):
        """Is the service ready: health_url → HTTP 200-399; port → TCP; else
        process alive and not crashed within 0.5s. 250ms poll, sec timeout."""
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

    def _remap_port(self, spec):
        """ports[0] held by another process at launch -> the next free port
        (scan +20) or None. The spec is not mutated — the override reaches
        the process only via the PORT/DEVDASH_PORT env vars."""
        ports = spec.get("ports") or ()
        if not ports or not be._port_open(ports[0]):
            return None  # free — the common case costs one TCP connect
        port = ports[0]
        holders = set(be.pids_on_port(port))
        if not holders:
            return None
        own = {p["pid"] for p in be._proc_snapshot()[0]
               if (spec.get("proc") and p["name"] == spec["proc"].lower())
               or (spec.get("match") and spec["match"].lower() in p["cl"])}
        own.update(x for x in
                   (spec.get("pid"),
                    (self._svc_spawn.get(spec["name"]) or (0,))[0]) if x)
        if holders <= own:
            return None  # bound by our own still-running process — as before
        for p in range(port + 1, min(port + 21, 65536)):
            if not be._port_open(p):
                return p
        return None  # no free port nearby — the probe reports the busy port

    def _do_start(self, spec):
        # alive matched procs → already running; a restart fired on a
        # probe flap must not spawn a duplicate (SO_REUSEADDR lets two
        # instances share the port → split-brain listeners)
        if spec.get("proc") or spec.get("match"):
            matched = [p for p in be._proc_snapshot()[0]
                       if (spec.get("proc") and p["name"] == spec["proc"])
                       or (spec.get("match")
                           and spec["match"].lower() in p["cl"])]
            if matched:
                self._log(f"[{spec['name']}] " + be.tr(
                    "SKIP_ALIVE",
                    pids=", ".join(str(p["pid"]) for p in matched[:5])))
                self._force_probe()
                return False
        job = None
        try:
            job = ptree.Job()
        except OSError:
            pass
        try:
            lspec = spec
            free = self._remap_port(spec)
            if free:
                # remap rides on a throwaway spec copy: profile merged and
                # expanded now, env_profile cleared so the remapped PORT
                # stays authoritative over a profile-defined PORT
                lspec = dict(spec, env_profile="",
                             env=dict(be.env_profile_env(spec),
                                      PORT=str(free),
                                      DEVDASH_PORT=str(free)))
                msg = be.tr("PORT_REMAPPED",
                            old=spec["ports"][0], new=free)
                self._issue("port", spec["name"], msg, sel=_svc_sel(spec))
                self._log(f"[{spec['name']}] {msg}")
            ok, err, proc = be.start_service_process(
                lspec, self._log, job=job)
        except Exception:
            if job:
                job.disarm()
                job.close()
            raise
        if ok and job:
            with self._lock:
                old = self._jobs.pop(spec["name"], None)
                if old:
                    old.terminate()      # stale processes — finish the tree
                    old.close()
                self._jobs[spec["name"]] = job
        elif job:
            job.disarm()
            job.close()
        if ok:
            with self._lock:
                # wrapper pid is the "alive" signal for probes without proc/match/ports;
                # kept in spec so the probe accepts it after a dashboard restart
                self._svc_spawn[spec["name"]] = (proc.pid,
                                                 be.pid_ctime(proc.pid))
                spec["pid"], spec["pid_ctime"] = \
                    self._svc_spawn[spec["name"]]
                be.save_services(self.services_data)
            self._run_start(spec["name"])
            if spec.get("autorestart"):
                # insta-crash <4s is invisible to the probe — verify after 8s
                _timer(8, lambda s=spec: self._start_verify(s))
        else:
            self._log(f"[{spec['name']} ERR] " + be.tr(
                "START_FAIL", err=be.tr_detail(str(err))))
            self._info(be.tr("START_FAIL_NAME",
                             name=spec["name"], err=be.tr_detail(str(err))))
        self._force_probe(1500)
        return ok

    def _start_verify(self, spec):
        """If after 8s the service is still not up and no process — insta-crash:
        count it as a crash so the circuit breaker kicks in."""
        if self._last_services.get(spec["name"], (None,))[0] == "up":
            return
        if any((spec.get("proc") and p["name"] == spec["proc"])
               or (spec.get("match") and spec["match"].lower() in p["cl"])
               for p in be._proc_snapshot()[0]):
            return  # process alive — just a slow start
        self._svc_autorestart(spec)

    def port_conflict(self, name):
        """{} or {port,pid,pname}: port held by a foreign process — for the dialog."""
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
        """What stop would kill — process names for the confirm dialog."""
        spec = self._service(name)
        if not spec:
            return []
        matched = [p for p in be._proc_snapshot()[0]
                   if (spec.get("proc") and p["name"] == spec["proc"])
                   or (spec.get("match") and spec["match"].lower() in p["cl"])]
        return [{"name": p["name"], "pid": p["pid"]} for p in matched]

    def start_service(self, name):
        spec = self._service(name)
        # manual start — reset circuit breaker and crash counters
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
            if spid:  # probe-adopted pid — clear it before killing
                be.save_services(self.services_data)
        if job:  # Job Object: instant kill of the whole tree
            job.terminate()
            job.close()
        # adopted/spawned pid outside the Job (dashboard restart, Job() failed) —
        # without this stop "succeeds" while the process keeps living
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
        self._svc_prev[spec["name"]] = "down"  # intentional — not a crash,
        # not an autorestart trigger on the next probe tick
        self._svc_stop_gen[spec["name"]] = (
            self._svc_stop_gen.get(spec["name"], 0) + 1)
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
        for i, s in enumerate(specs):  # stagger — do not choke the system at once
            _timer(i * 0.8, lambda s=s: self._start_service(s))

    def stop_all(self):
        specs = [s for s in self.services_data
                 if not s.get("monitor_only") and not s.get("type")
                 and (s.get("proc") or s.get("match")
                      or s["name"] in self._svc_spawn or s.get("pid"))]
        for i, s in enumerate(specs):
            _timer(i * 0.5, lambda s=s: self._stop_service(s))

    def _dep_order(self, specs):
        """Toposort by depends_on: dependencies start before dependents.
        Cycles/unknown names do not block — appended at the end."""
        by_name = {s["name"]: s for s in specs}
        done, out = set(), []

        def visit(s, stack):
            if s["name"] in done:
                return
            if s["name"] in stack:
                self._issue("deps", s["name"], be.tr("DEP_CYCLE_IN"),
                            sel=_svc_sel(s))
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
        self._stop_service(spec)  # otherwise the started process becomes an orphan
        with self._lock:
            if spec in self.services_data:
                self.services_data.remove(spec)
            be.save_services(self.services_data)
        be.note_deleted_service(spec)  # "Discovered" restores fields via proc/match
        self._force_probe()
        return True, ""

    def save_service(self, old_name, data):
        """old_name='' — add; the form sends only known keys,
        unknown keys in spec are preserved."""
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
        be._norm_service(data)  # ports → valid int list or drop
        with self._lock:
            if old_name:
                spec = self._service(old_name)
                if spec is None:
                    return False, be.tr("NAME_NOT_FOUND", name=old_name)
                # form keys absent from data — delete (unchecked box/
                # empty field); keep unknown spec keys
                known = {"name", "sub", "type", "ports", "proc", "match", "url",
                         "host", "port", "keyword", "container", "interval",
                         "start", "cwd", "path", "note", "env_key", "env_file",
                         "autorestart", "monitor_only", "depends_on",
                         "health_url", "mem_limit_mb", "watch",
                         "restart_every_min", "env_profiles", "env_profile"}
                if data["name"].strip() != old_name \
                        and self._service(data["name"].strip()):
                    return False, be.tr("NAME_TAKEN", name=data["name"])
                for k in known - set(data):
                    spec.pop(k, None)
                spec.update(data)
            else:
                if self._service(data["name"].strip()):
                    return False, be.tr("NAME_TAKEN", name=data["name"])
                self.services_data.append(data)
            be.save_services(self.services_data)
        be.drop_deleted_service(data["name"])  # re-added — forget the remembered one
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

    # ---------- projects ----------

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
                if old:  # job from the previous run: finish the tree, close the handle
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
                line = be.decode_log(raw).rstrip()
                if line:
                    self._log(f"[{name}{' ERR' if err else ''}] {line}")
                    if classify_log_line(line) == "error":
                        self._issue_log_error(name, line, sel=_prj_sel(name))
        except (OSError, ValueError):
            pass

    def _wait_proc(self, proc, name):
        rc = proc.wait()
        with self._lock:
            if self._procs.get(name) is proc:
                self._procs.pop(name, None)
            self._run_end(name, f"exit {rc}")
            p = self._proj(name)
            if p and p.get("pid") == proc.pid:
                p["pid"] = None
                p["pid_ctime"] = None
                self._proj_dead[name] = True
                self._issue("crash", name, f"exit {rc}", sel=_prj_sel(name))
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
            # pid=None before kill: _wait_proc will not take the stop for a crash
            p["pid"] = None
            p["pid_ctime"] = None
            self._proj_dead[name] = False
            be.save_projects(self.projects_data)
        if proc and proc.poll() is None:
            try:  # graceful shutdown, 3s to exit
                proc.terminate()
                proc.wait(timeout=3)
            except Exception:
                pass
        if job:
            job.terminate()          # finish the whole tree for sure
            job.close()
        if pid:
            # always: with job=None (assign failed) without this the children
            # of the process stay orphaned; killing again is safe
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
                # cmd/cwd are required for the probe/ports paths — a partial
                # save without them would break the p["cwd"] indexes
                data.setdefault("cmd", "")
                data.setdefault("cwd", "")
                if data["name"].strip() != old_name:
                    if self._proj(data["name"].strip()):
                        return False, be.tr("NAME_TAKEN", name=data["name"])
                    # runtime state is keyed by name — it must move with the
                    # rename or witnessed deaths of the renamed project
                    # silently lose their crash report
                    if old_name in self._proj_seen:
                        self._proj_seen.discard(old_name)
                        self._proj_seen.add(data["name"].strip())
                    for m in (self._proj_dead, self._procs, self._jobs,
                              self._detected_url):
                        if old_name in m:
                            m[data["name"].strip()] = m.pop(old_name)
                data.setdefault("pid", p.get("pid"))
                if (data.get("cwd") or "") != (p.get("cwd") or ""):
                    data["pid"], data["pid_ctime"] = None, None
                p.update(data)  # unknown keys + pid are preserved
            else:
                if self._proj(data["name"].strip()):
                    return False, be.tr("NAME_TAKEN", name=data["name"])
                data["pid"] = None  # client-sent pid must never be trusted
                self.projects_data.append(data)
            be.save_projects(self.projects_data)
        be.drop_deleted_project(data["name"],
                                data.get("cwd"))  # re-added — forget it
        return True, ""

    def delete_project(self, name):
        p = self._proj(name)
        if not p:
            return False, be.tr("NAME_NOT_FOUND", name=name)
        # untrack, don't kill — unlike services, a deleted project's
        # process keeps running (it may not be ours)
        be.note_deleted_project(p)  # scan restores cmd/url by cwd match
        with self._lock:
            self.projects_data.remove(p)
            self._proj_seen.discard(name)
            self._proj_dead.pop(name, None)
            be.save_projects(self.projects_data)
        return True, ""

    def add_projects(self, items):
        # whitelist: env_*/branch from the scan are transient fields, they
        # do not belong in projects_config.json (recomputed live in _proj_row)
        KEEP = ("name", "cmd", "cwd", "url", "framework", "autostart")
        with self._lock:
            have = {(p["name"], os.path.normcase(os.path.normpath(
                p.get("cwd") or ""))) for p in self.projects_data}
            names = {p["name"] for p in self.projects_data}
            new, seen = [], set()
            for i in items:
                if not (isinstance(i, dict) and i.get("name")
                        and i.get("cmd")):
                    continue
                nc = os.path.normcase(os.path.normpath(i.get("cwd") or ""))
                # no dup by name or cwd — a stale strip row must not clone
                if i["name"] in names or (i["name"], nc) in have \
                        or nc in seen:
                    continue
                seen.add(nc)
                new.append({k: v for k, v in i.items() if k in KEEP})
            for i in new:
                i["pid"] = None
                i.setdefault("cwd", "")
                be.drop_deleted_project(i["name"], i["cwd"])
            if new:
                self.projects_data.extend(new)
                be.save_projects(self.projects_data)
        return True, be.tr("ADDED_N", n=len(new))

    def scan_projects(self):
        # the walk is the slow part — a short cache is enough for the
        # strip's mount+expand fetches and repeated visits
        now = time.time()
        if getattr(self, "_scan_cache", None) \
                and now - self._scan_cache[0] < 30:
            return {"found": self._scan_cache[1]}
        with self._lock:
            known = {os.path.normcase(os.path.normpath(p["cwd"]))
                     for p in list(self.projects_data)}
        # cwds of running processes — a "project already running" signal
        # for scoring; its LISTEN port prefills the project url
        run_dirs, run_ports = set(), {}
        me = os.getpid()
        try:
            conns = psutil.net_connections("tcp")
        except (psutil.Error, OSError):
            conns = []
        for p in be._proc_snapshot()[0]:
            if p["proc"].pid == me:
                continue  # our own :4850 is not a project
            try:
                nc = os.path.normcase(os.path.normpath(p["proc"].cwd()))
            except (psutil.Error, OSError):
                continue
            run_dirs.add(nc)
            for c in conns:
                if c.status == "LISTEN" and c.pid == p["proc"].pid \
                        and c.laddr:
                    run_ports.setdefault(nc, c.laddr.port)
        deleted = {os.path.normcase(os.path.normpath(s["cwd"])): s
                   for s in be.load_settings()["prj_deleted"]
                   if s.get("cwd")}
        groups, order, seen = {}, [], set()
        for root in be.scan_roots():
            if not os.path.isdir(root):
                continue
            for p in be.scan_project_dirs(root, known, run_dirs, run_ports):
                key = os.path.normcase(os.path.normpath(p["cwd"]))
                if key not in seen:
                    seen.add(key)
                    repo = p.get("repo") or key
                    if repo not in groups:
                        groups[repo] = []
                        order.append(repo)
                    groups[repo].append(p)
        # worktrees of one repo fold into a single primary row (the main
        # checkout, else the best score) carrying {cwd, branch} per checkout
        found = []
        for repo in order:
            rows = groups[repo]
            pri = rows[0] if len(rows) == 1 else next(
                (r for r in rows
                 if os.path.normcase(os.path.normpath(r["cwd"])) == repo),
                max(rows, key=lambda r: r["score"]))
            if len(rows) > 1:
                pri["worktrees"] = [{"cwd": r["cwd"], "branch": r["branch"]}
                                    for r in rows]
            found.append(pri)
        for p in found:  # deleted spec resurrects user's cmd/url/autostart
            old = deleted.get(os.path.normcase(os.path.normpath(p["cwd"])))
            if old:
                p["restored"] = True
                for k in ("name", "cmd", "url", "autostart"):
                    if old.get(k) is not None:
                        p[k] = old[k]
        # same basename under different parents (multi-root scans) —
        # qualify with the nearest ancestor dir until the name is unique
        counts = {}
        for p in found:
            counts[p["name"]] = counts.get(p["name"], 0) + 1
        taken = set(counts)
        for p in found:
            if counts[p["name"]] <= 1:
                continue
            base, d = p["name"], p["cwd"]
            for _ in range(4):
                d = os.path.dirname(d)
                par = os.path.basename(d).upper()
                if not par:
                    break
                q = f"{base} · {par}"
                if q not in taken:
                    taken.add(q)
                    p["name"] = q
                    break
        self._scan_cache = (now, found)
        return {"found": found}

    # ---------- autorun ----------

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
        if old_name and old_name.lower() == be.SELF_AUTORUN_NAME.lower():
            return False, be.tr("AR_SELF_MANAGED")  # Settings toggle owns it
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

    # ---------- misc ----------

    def open_project(self, name, what):
        """Open the project folder in Explorer or in an IDE (cursor → code)."""
        p = self._proj(name)
        cwd = (p or {}).get("cwd") or ""
        if not p:
            return False, be.tr("NAME_NOT_FOUND", name=name)
        if not cwd or not os.path.isdir(cwd):
            return False, be.tr("PROJ_DIR_MISSING",
                                cwd=cwd or "—")
        if what == "open-ide":
            exe = be.find_editor()
            if exe:
                subprocess.Popen(pi.shell_argv(f'{exe} "{cwd}"'),
                                 **pi.popen_kwargs())
                return True, ""
            pi.open_path(cwd)  # no IDE — at least a file manager
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
                    exe = be.find_editor()
                    if exe:
                        try:  # "Open in editor" → otherwise file association
                            subprocess.Popen(pi.shell_argv(f'{exe} "{path}"'),
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
        except Exception as e:  # headless/no tkinter — clean error, not a 500
            return False, be.tr("PICK_DIR_FAIL", e=e)

    def port_targets(self, port):
        out = []
        for pid in be.pids_on_port(int(port)):
            try:
                out.append({"name": psutil.Process(pid).name(), "pid": pid})
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                out.append({"name": "?", "pid": pid})
        return out

    def free_port(self, start):
        """First free TCP port >= start ('from' itself counts)."""
        try:
            start = int(start)
        except (TypeError, ValueError):
            start = 8000
        start = max(1, min(start, 65535))
        p = start if not be._port_open(start) else be.next_free_port(start)
        return {"port": p, "from": start}

    def _protected_pid(self, pid):
        """System/db process NOT belonging to our services and
        projects — protection against accidentally killing postgres/svchost."""
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
        """Kill a process by pid (background dev processes without ports)."""
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
        """Current core settings + meta (port marked restart-only)."""
        with self._lock:
            return {
                "probe_interval": self._probe_interval,
                "dep_timeout": self._dep_timeout,
                "backoff": list(self._backoff),
                "api_port": be.load_settings()["api_port"],
                "config_dir": be.DATA_DIR,
                "scan_roots": be.load_settings()["scan_roots"],
                "scan_roots_auto": be.scan_roots(),
                "port_mine": be.load_settings()["port_mine"],
                "port_hidden": be.load_settings()["port_hidden"],
                "lang": be.load_settings()["lang"],
                "lang_resolved": be.lang(),
                "autostart": be.self_autorun_enabled(),
            }

    def save_settings(self, body):
        """Settings patch from the UI: validate -> settings.json -> apply
        live. api_port cannot change without a restart — absent from the reply."""
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
                if "autostart" in body:
                    want = bool(body["autostart"])
                    if want != be.self_autorun_enabled():
                        try:  # registry write — applies instantly, not stored
                            be.self_autorun_set(want)
                        except OSError:
                            return False, be.tr("SAVE_FAILED")
                if "api_port" in body:  # applies on next start
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

    def _own_pids(self, procs, svcs, prjs):
        """pid -> our service/project name: proc/match hits, spawned or
        adopted service pids, project pids. Port attribution + port-watch."""
        own = {}
        for spec in svcs:
            for p in procs:
                if (spec.get("proc") and p["name"] == spec["proc"].lower()) \
                        or (spec.get("match")
                            and spec["match"].lower() in p["cl"]):
                    own[p["pid"]] = (spec["name"], "svc")
            # spawned/adopted pid of a service without proc/match — also "ours"
            for pid in (spec.get("pid"),
                        (self._svc_spawn.get(spec["name"]) or (0,))[0]):
                if pid:
                    own[pid] = (spec["name"], "svc")
        for prj in prjs:
            if prj.get("pid"):
                own[prj["pid"]] = (prj["name"], "prj")
        return own

    def api_ports(self):
        """TCP listeners + owner (service/project, incl. via parents
        and cwd in cmdline) + category of foreign ones and user marks."""
        global _PREV_PIDS
        procs, listeners, lan = be._proc_snapshot()
        by_pid = {p["pid"]: p for p in procs}
        prev, _PREV_PIDS = _PREV_PIDS, set(by_pid)
        with self._lock:  # snapshot shared lists — writes go under _lock
            svcs, prjs = list(self.services_data), list(self.projects_data)
        own = self._own_pids(procs, svcs, prjs)
        st = be.load_settings()
        mine = {x.lower() for x in st["port_mine"]}
        hidden = {x.lower() for x in st["port_hidden"]}

        def own_by_cwd(pid):
            cl = (by_pid.get(pid) or {}).get("cl", "")
            if not cl:
                return None
            for prj in prjs:
                raw = prj.get("cwd") or ""
                if not raw:
                    continue  # '' → normpath('.') would match anything
                cwd = os.path.normcase(os.path.normpath(raw))
                if cwd + os.sep in cl or cl.endswith(cwd):
                    return prj["name"]
            return None

        out = []
        for port, pid in sorted(listeners.items()):
            info = by_pid.get(pid)
            pr = info["proc"] if info else None
            try:
                if info:
                    proc, cmd = info["name"], info["cmd"]
                else:
                    pr = psutil.Process(pid)
                    proc, cmd = pr.name(), " ".join(pr.cmdline() or [])
                age = time.time() - pr.create_time()
            except (psutil.Error, OSError):
                proc, cmd, age = (info or {}).get("name", "?"), "", 0
            ot = _own_owner(pid, own, by_pid)
            if ot:
                owner, okind = ot
            else:
                owner, okind = own_by_cwd(pid), "prj"
            if not owner:
                okind = None
            zombie, agent = _proc_flags(pid, info, pr, by_pid, age, prev)
            if pid == os.getpid():
                zombie = None  # the dashboard itself is detached, not a zombie
            cat, label = be.port_class(proc, port)
            out.append({"port": port, "pid": pid,
                        "proc": proc or "?", "cmd": cmd[:140],
                        "owner": owner, "ownerKind": okind,
                        "self": pid == os.getpid(),
                        "cat": cat, "label": be.tr(label),
                        "lan": lan.get(port), "age": int(age),
                        "mine": (proc or "").lower() in mine,
                        "hidden": (proc or "").lower() in hidden,
                        "zombie": zombie, "agent": agent})
        # title+favicon: serve the cache, never block on probes — under
        # ephemeral-port pressure each connect stalls for seconds and the
        # whole endpoint used to hang. Misses refresh in the background
        # and surface on the next poll; sys holders / LAN-only not poked.
        now = time.time()
        fresh = {p: v for p, (ts, v) in self._sniff.items()
                 if now - ts < 60}
        for r in out:
            r["title"], r["favicon"] = fresh.get(r["port"], ("", ""))
        miss = [r["port"] for r in out if r["cat"] != "sys"
                and r["lan"] in (None, "0.0.0.0", "::")
                and r["port"] not in fresh]
        if miss and not self._sniff_busy:
            self._sniff_busy = True
            threading.Thread(target=self._sniff_ports,
                             args=(miss,), daemon=True).start()
        # scoring sort: own on top, then "interesting" foreign ones
        # (db/dev, LAN-exposed, long-lived, marked), sys at the bottom
        catw = {"db": 3, "dev": 2, "net": 2, "other": 0, "sys": -50}
        for r in out:
            r["score"] = (100 if r["owner"] or r["self"] else 0) \
                + catw.get(r["cat"], 0) \
                + (3 if r["mine"] else 0) + (2 if r["lan"] else 0) \
                + (1 if r.get("title") else 0) \
                + (1 if r["age"] >= 300 else 0) + (1 if r["age"] >= 3600 else 0)
        out.sort(key=lambda r: (-r["score"], r["port"]))
        # background dev processes without ports (like kiri's `ports ps`):
        # node/python/bun… that listen on nothing — "idle servers"
        busy = set(listeners.values())
        # listener ancestors are busy too (npm -> node wrapper):
        # otherwise the parent dev process falsely lands in "no ports"
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
                age = time.time() - p["proc"].create_time()
            except (psutil.Error, OSError):
                mb, age = 0, 0
            zombie, agent = _proc_flags(p["pid"], p, p["proc"], by_pid,
                                        age, prev)
            ot = _own_owner(p["pid"], own, by_pid)
            bg.append({"name": p["name"], "pid": p["pid"], "mb": mb,
                       "owner": (ot[0] if ot else None)
                       or own_by_cwd(p["pid"]),
                       "zombie": zombie, "agent": agent})
        bg.sort(key=lambda p: -p["mb"])  # hungriest idle processes on top
        return {"ports": out, "bg": bg}

    def _sniff_ports(self, ports):
        """Fill the title/favicon cache off the request path."""
        try:
            vals = list(ThreadPoolExecutor(4).map(
                lambda pt: (be.page_title(pt), be.port_favicon(pt)), ports))
            now = time.time()
            for pt, v in zip(ports, vals):
                self._sniff[pt] = (now, v)
        finally:
            self._sniff_busy = False

    def api_service_candidates(self):
        """Running foreign processes → service candidates for the "New
        service" dialog. Scoring: port > category > mark > own path > age."""
        data = self.api_ports()
        with self._lock:
            prjs, svcs = list(self.projects_data), list(self.services_data)
        dirs = [os.path.normcase(os.path.normpath(p["cwd"])) + os.sep
                for p in prjs if p.get("cwd")]
        for s_ in svcs:
            for f_ in ("cwd", "path"):
                if s_.get(f_):
                    dirs.append(os.path.normcase(
                        os.path.normpath(s_[f_])) + os.sep)
        deleted = be.load_settings()["svc_deleted"]
        # autorun entries: needle per entry for matching live candidates,
        # plus the rows themselves as a source of dormant candidates
        ar_rows = self._ar_mine + self._ar_other
        ar_used = set()

        def _ar_for(name, cmd):
            """Autorun entry for this process: registry name or the
            target basename inside the process name/cmdline."""
            s = (name + " " + (cmd or "")).lower()
            for a in ar_rows:
                tgt = be._autorun_target(a["sub"] or "")
                needles = (a["name"].lower(),
                           os.path.basename(tgt).lower() if tgt else "")
                if any(n and n in s for n in needles):
                    return a
            return None

        by_pid = {}
        for r in data["ports"]:
            if r["owner"] or r["self"] or r["hidden"] or r["cat"] == "sys":
                continue
            c = by_pid.setdefault(
                r["pid"], {"pid": r["pid"], "name": r["proc"],
                           "cmd": r["cmd"], "ports": [], "cat": r["cat"],
                           "label": r["label"], "mine": r["mine"],
                           "age": r["age"], "mb": 0,
                           "zombie": r["zombie"], "agent": r["agent"]})
            c["ports"].append(r["port"])
        for r in data["bg"]:  # portless dev processes — bots/watchers
            if not r["owner"]:
                by_pid.setdefault(
                    r["pid"], {"pid": r["pid"], "name": r["name"], "cmd": "",
                               "ports": [], "cat": "dev", "label": "",
                               "mine": False, "age": 0, "mb": r["mb"],
                               "zombie": r["zombie"], "agent": r["agent"]})
        out, used_deleted = [], set()
        for c in by_pid.values():
            try:
                p_ = psutil.Process(c["pid"])
            except (psutil.Error, OSError):
                p_ = None
            argv = []
            if p_:
                try:  # arg list, not joined string — quoted args stay whole
                    argv = p_.cmdline() or []
                except (psutil.Error, OSError):
                    pass  # SYSTEM gives no cmdline — proc alone suffices
            cmd = c["cmd"] or " ".join(_shq(x) for x in argv)
            proc = (c["name"] or "").lower()
            interp = proc.removesuffix(".exe") in be.INTERPRETERS
            toks = argv or cmd.split()
            frag, script, si = "", "", -1
            for i, t_ in enumerate(toks):
                if _SCRIPT_EXT_RE.search(t_):
                    script, si = t_, i
                    frag = os.path.basename(t_)
                    nxt = toks[i + 1] if i + 1 < len(toks) else ""
                    if nxt and not nxt.startswith("-") \
                            and "\\" not in nxt and "/" not in nxt:
                        frag += " " + nxt
                    break
            try:
                cwd = p_.cwd() if p_ else ""
            except (psutil.Error, OSError):
                cwd = ""
            try:
                exe_p = p_.exe() if p_ else ""
            except (psutil.Error, OSError):
                exe_p = ""
            # launcher in the parent chain (npm run / go run / x.cmd) is the
            # real start recipe; else interpreter + absolute script anchors
            # to the script file; else the live snapshot
            lstart, lcwd, lstem = _find_launcher(p_) or ("", "", "")
            if lstart:
                start, cwd = lstart, lcwd or cwd
            elif interp and si >= 0 and os.path.isabs(script):
                cwd = os.path.dirname(script) or cwd
                exe_b = _shq(exe_p) if _VENV_DIR_RE.search(exe_p) \
                    else (os.path.basename(toks[0]) if toks else "")
                if re.search(r"\.tsx?$", script, re.I) \
                        and exe_b.lower().startswith("node"):
                    exe_b = _node_runner(cwd) or exe_b
                start = " ".join(_shq(x) for x in
                                 [exe_b, os.path.basename(script),
                                  *toks[si + 1:]] if x)
            else:
                start = cmd
            # name/match from the launcher or script — interpreters only;
            # for a plain exe an arg like server-ws.mjs is no script sign
            stem = lstem or (frag if interp else "") \
                or os.path.splitext(c["name"] or "?")[0]
            in_dirs = any(d in cmd.lower().replace("/", "\\") for d in dirs) \
                or any(d in (cwd.lower().replace("/", "\\") + os.sep)
                       for d in dirs)
            score, why = 0, []
            if c["ports"]:
                score += 3
            if c["cat"] in ("dev", "db", "net"):
                score += 2
            if c["mine"]:
                score += 2; why.append("WHY_MINE")
            if in_dirs:
                score += 2; why.append("WHY_OWN_DIR")
            if c["age"] >= 300:
                score += 1; why.append("WHY_AGED")
            ar = _ar_for(c["name"], cmd)
            if ar:  # the machine already starts it = strongest infra sign
                score += 4; why.append("WHY_AUTORUN")
                ar_used.add(id(ar))
            name = _SCRIPT_EXT_RE.sub("", stem)
            name = re.sub(r"[_-](?:x64|x86|amd64|win64)$", "", name)
            if interp and frag:  # for scripts "my_bot.py serve" → "my bot serve"
                name = name.replace("_", " ")
                base = name.split()[0]
                if base.lower() in _GENERIC_STEMS:
                    sdir = os.path.dirname(lstart.strip('"')) if lstart \
                        else (os.path.dirname(script)
                              if os.path.isabs(script) else cwd)
                    name = _smart_name(base, sdir) + name[len(base):]
            elif name.lower() in _GENERIC_STEMS:
                sdir = os.path.dirname(lstart.strip('"')) if lstart \
                    else os.path.dirname(exe_p)
                name = _smart_name(name, sdir)  # exe's folder names it
            # "index.js" matches every node process — anchor generic match
            # fragments to their folder: agent\server.mjs is still a
            # cmdline substring, but unique
            match = ""
            if interp and frag:
                match = frag
                if os.path.splitext(frag.split()[0])[0].lower() \
                        in _GENERIC_STEMS:
                    parts = script.replace("/", "\\").split("\\")
                    if len(parts) > 1:
                        tail = "\\".join(parts[-2:])
                        if tail.lower() in cmd.lower():
                            match = tail
            # deleted-service spec restored via proc / match fragment;
            # if it had neither — via port intersection
            def _is_old(s):
                if s.get("proc") and s["proc"].lower() == proc:
                    return True
                if s.get("match") and s["match"].lower() in cmd.lower():
                    return True
                return not s.get("proc") and not s.get("match") and \
                    bool(set(s.get("ports") or ()) & set(c["ports"]))
            old = next((s for s in deleted if _is_old(s)), None)
            if old:
                score += 3; why.append("WHY_DELETED")
                used_deleted.add(id(old))
            label = c["label"]
            if c["cat"] == "other" and exe_p:
                try:  # unknown proc — let the exe describe itself
                    label = be.exe_label(exe_p) or label
                except (psutil.Error, OSError):
                    pass
            out.append({"name": name, "pid": c["pid"],
                        "proc": c["name"], "match": match,
                        "ports": sorted(c["ports"]), "start": start,
                        "cwd": cwd, "cat": c["cat"], "label": label,
                        "hint": dict(old) if old else None,
                        "alive": True, "why": why, "score": score,
                        "zombie": c["zombie"], "agent": c["agent"]})
        # dormant candidates: deleted specs no live process matched (delete
        # stops the service — it stays discoverable for one-click restore)
        for s in deleted:
            if id(s) in used_deleted:
                continue
            out.append({"name": s.get("name", "?"), "pid": 0,
                        "proc": s.get("proc", ""), "match": s.get("match", ""),
                        "ports": [int(p) for p in (s.get("ports") or [])],
                        "start": s.get("start", ""), "cwd": s.get("cwd", ""),
                        "cat": "other", "label": "", "hint": dict(s),
                        "alive": False, "why": ["WHY_DELETED"], "score": 9,
                        "zombie": None, "agent": None})
        # unbound autorun entries — dormant infra the machine starts itself;
        # bound ones (live service / project dir / live candidate) skipped
        svc_names = {s["name"].lower() for s in svcs}
        for a in ar_rows:
            if id(a) in ar_used:
                continue
            an, cmd = a["name"].lower(), a["sub"] or ""
            s_cmd = an + " " + cmd.lower()
            if an in svc_names \
                    or any((s.get("proc") and s["proc"].lower() in s_cmd) or
                           (s.get("match") and s["match"].lower() in s_cmd) or
                           s["name"].lower() in s_cmd for s in svcs) \
                    or any(d in s_cmd for d in dirs) \
                    or any(  # the deleted-spec row is the richer twin
                        (s.get("proc") and s["proc"].lower() in s_cmd) or
                        (s.get("match") and s["match"].lower() in s_cmd) or
                        s["name"].lower() in s_cmd for s in deleted):
                continue
            tgt = be._autorun_target(cmd) or ""
            stem = os.path.splitext(os.path.basename(tgt))[0] if tgt else ""
            out.append({"name": a["name"], "pid": 0,
                        "proc": os.path.basename(tgt)
                        if tgt.lower().endswith(".exe") else "",
                        "match": stem,
                        "ports": [int(p) for p in
                                  re.findall(r":(\d{2,5})\b", cmd)],
                        "start": cmd,
                        "cwd": os.path.dirname(tgt) if tgt else "",
                        "cat": "other", "label": be.exe_label(tgt),
                        "hint": None, "alive": a["state"] == "up",
                        "why": ["WHY_AUTORUN"]
                        + ([] if a["state"] == "up" else ["WHY_STOPPED"]),
                        "score": 7, "zombie": None, "agent": None})
        out.sort(key=lambda c: -c["score"])
        return out[:15]

    def api_state(self):
        """Everything the UI needs in one request."""
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
            # service "in autorun": name of the Run entry belonging to it
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
                    "updChannel": be.update_channel(),
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
        """Service logs: logs/<name>.log file, otherwise the event log by tag."""
        spec = self._service(name)
        path = self._log_path(spec) if spec else ""
        if path and os.path.exists(path):
            try:
                with open(path, "rb") as f:
                    f.seek(0, 2)
                    size = f.tell()
                    f.seek(max(0, size - 262144))
                    tail = be.decode_log(f.read())
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
        """Services for agents: the same state the UI sees."""
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
        self._err_issues.clear()
        st.clear_issues()
        return True, ""

    def api_runs(self, name):
        def strip(r):
            return {k: v for k, v in r.items() if k != "_rid"}
        if name:
            return [strip(r) for r in self._runs.get(name, ())]
        return {n: [strip(r) for r in dq] for n, dq in self._runs.items()}

    def api_action(self, name, action, kind="projects"):
        """Old-API compat: /api/(projects|services)/X/start|stop|restart"""
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

    # ---------- server ----------

    def _start_api(self):
        _ApiHandler.dash = self
        want = be.load_settings()["api_port"]
        self.api = None
        for cand in range(want, want + 10):  # port busy → try the next 9
            try:
                self.api = _ApiServer(("127.0.0.1", cand), _ApiHandler)
                self.api_port = cand
                break
            except (OSError, OverflowError):  # OSError=busy, Overflow=garbage
                pass
        if self.api:
            # child processes (mcp_server etc.) learn the real port
            os.environ["DEVDASH_PORT"] = str(self.api_port)
            try:  # bound-port marker: second instance/MCP ping it
                with open(os.path.join(be.DATA_DIR, "api.port"), "w",
                          encoding="ascii") as f:
                    f.write(str(self.api_port))
            except OSError:
                pass
            threading.Thread(target=self.api.serve_forever,
                             daemon=True).start()
