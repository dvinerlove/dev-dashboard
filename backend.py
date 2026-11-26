"""Dashboard logic without UI: configs, process/port probes,
remote health checks, autostart (registry), env helpers.
Moved out of dashboard.py; Qt is not imported."""
import json
import os
import re
import socket
import subprocess
import sys
import time
import ssl
import urllib.request
import urllib.error
import psutil
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from urllib.parse import urlparse

import platform_impl as pi

BASE_DIR = os.path.dirname(os.path.abspath(
    sys.executable if getattr(sys, "frozen", False) else __file__))
# read-only resources (frontend/dist, icon.ico): _MEIPASS in a onefile bundle
RESOURCE_DIR = getattr(sys, "_MEIPASS", BASE_DIR)
VERSION = "0.9.1"


def _default_data_dir():
    if pi.IS_WIN:
        return os.path.join(
            os.environ.get("LOCALAPPDATA") or BASE_DIR, "DevDashboard")
    if pi.IS_MAC:
        return os.path.expanduser("~/Library/Application Support/DevDashboard")
    return os.path.join(os.environ.get("XDG_CONFIG_HOME")
                        or os.path.expanduser("~/.config"), "dev-dashboard")


# Writable user data: next to the code if a config already exists (portable/dev),
# otherwise the per-OS data dir; DEVDASH_DATA_DIR — forced override
_DATA_MARKERS = ("services_config.json", "projects_config.json",
                 "settings.json", "state.db")
DATA_DIR = os.environ.get("DEVDASH_DATA_DIR") or (
    BASE_DIR if any(os.path.exists(os.path.join(BASE_DIR, f))
                    for f in _DATA_MARKERS) else _default_data_dir())
CONFIG_FILE = os.path.join(DATA_DIR, "projects_config.json")
SERVICES_FILE = os.path.join(DATA_DIR, "services_config.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
ICON_FILE = os.path.join(RESOURCE_DIR, "icon.ico")
LOGS_DIR = os.path.join(DATA_DIR, "logs")

TAG_COLORS = ["#7aa2f7", "#9ece6a", "#e0af68", "#bb9af7", "#7dcfff", "#ff9e64"]

DEFAULT_PROJECTS = []


def _save_json(path, data):
    """Atomic config write: tmp + replace, a crash does not tear the file in half."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    os.replace(tmp, path)


def _load_json(path, default):
    """json from file; on a broken file we shelve it as .corrupt-* and
    return the default without clobbering the original."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        try:
            os.replace(path, f"{path}.corrupt-{int(time.time())}")
        except OSError:
            pass
        return default


DEFAULT_SETTINGS = {
    "probe_interval": 4,        # service poll interval, sec
    "dep_timeout": 15,          # depends_on readiness wait, sec
    "backoff": [2, 5, 10, 20],  # autorestart delays, sec
    "scan_roots": [],           # project search folders; [] = auto (BASE_DIR parent)
    "port_mine": [],            # process names marked "mine" by the user
    "port_hidden": [],          # process names hidden from the ports list
    "svc_deleted": [],          # specs of recently deleted services — "New
                              # service" restores them by proc/match/port
    "prj_deleted": [],          # same for projects — scan restores by cwd
    "lang": "auto",             # auto = OS language (non-ru and detection failure → en)
    "api_port": 4850,           # local HTTP API port; applied at startup
}

_LANG = "en"  # load_settings cache — probes call tr() every tick


def resolve_lang(v):
    """'auto' → OS language; unknown values → 'en'."""
    if v == "auto":
        return pi.system_lang()
    return v if v in LANGS else "en"


def load_settings():
    """settings.json over the defaults; unknown keys are ignored."""
    global _LANG
    raw = _load_json(SETTINGS_FILE, {})
    out = dict(DEFAULT_SETTINGS)
    for k in out:
        if k in raw:
            out[k] = raw[k]
    # disk is a trust boundary: garbage numbers must not crash the dashboard
    try:
        out["api_port"] = int(out["api_port"])
        if not 1024 <= out["api_port"] <= 65535:
            out["api_port"] = DEFAULT_SETTINGS["api_port"]
    except (TypeError, ValueError):
        out["api_port"] = DEFAULT_SETTINGS["api_port"]
    try:
        out["probe_interval"] = float(out["probe_interval"])
        if out["probe_interval"] <= 0:
            out["probe_interval"] = DEFAULT_SETTINGS["probe_interval"]
    except (TypeError, ValueError):
        out["probe_interval"] = DEFAULT_SETTINGS["probe_interval"]
    try:
        b = [float(x) for x in out["backoff"]]
        out["backoff"] = b or DEFAULT_SETTINGS["backoff"]
    except (TypeError, ValueError):
        out["backoff"] = DEFAULT_SETTINGS["backoff"]
    for k in ("svc_deleted", "prj_deleted"):
        if not isinstance(out[k], list):  # hand-edited garbage → reset
            out[k] = []
    _LANG = resolve_lang(out["lang"])
    return out


def save_settings(data):
    """Patch of known keys -> settings.json; returns the resulting dict."""
    global _LANG
    s = load_settings()
    for k in s:
        if k in data:
            s[k] = data[k]
    _save_json(SETTINGS_FILE, s)
    _LANG = resolve_lang(s["lang"])
    return s


def _note_deleted(key, spec):
    """Deleted spec -> settings[key] (up to 10, newest first): candidates
    and project scan restore fields from it."""
    st = load_settings()
    lst = [s for s in st[key] if s.get("name") != spec.get("name")]
    lst.insert(0, spec)
    st[key] = lst[:10]
    save_settings(st)


def _drop_deleted(key, name, cwd=None):
    """Re-added — forget the remembered spec (by name or by cwd —
    a renamed re-add must not leave a stale memory entry)."""
    st = load_settings()
    nc = os.path.normcase(os.path.normpath(cwd)) if cwd else None
    lst = [s for s in st[key]
           if s.get("name") != name
           and (not nc or os.path.normcase(os.path.normpath(
                s.get("cwd") or "")) != nc)]
    if len(lst) != len(st[key]):
        st[key] = lst
        save_settings(st)


def note_deleted_service(spec):
    _note_deleted("svc_deleted", spec)


def drop_deleted_service(name):
    _drop_deleted("svc_deleted", name)


def note_deleted_project(spec):
    _note_deleted("prj_deleted", spec)


def drop_deleted_project(name, cwd=None):
    _drop_deleted("prj_deleted", name, cwd)


# --- Localization ------------------------------------------------------------
# Translations — locales/<lang>.json at the root, one file per language (auto-discovery:
# adding a language = dropping a file). Flat keys are frontend UI strings, the
# "server" section is API strings (tr), "detail"/"tpl" translate probe runtime
# text (tr_detail; canonical format is EN, en.json has no such sections).
LOCALES_DIR = os.path.join(RESOURCE_DIR, "locales")


def _load_locales():
    out = {}
    if os.path.isdir(LOCALES_DIR):
        for fn in sorted(os.listdir(LOCALES_DIR)):
            if fn.endswith(".json"):
                out[fn[:-5]] = _load_json(os.path.join(LOCALES_DIR, fn), {})
    return out


LOCALES = _load_locales()
LANGS = ("auto",) + tuple(LOCALES)
EN = LOCALES.get("en", {}).get("server", {})  # tr() fallback on a missing key


def lang():
    return _LANG


def tr(key, **kw):
    """Semantic key -> string of the current language (+{placeholders}).
    Miss — fall back to EN, then to the key itself: visible in the UI at once."""
    s = LOCALES.get(_LANG, {}).get("server", {}).get(key, EN.get(key, key))
    return s.format(**kw) if kw else s


def tr_detail(s):
    """Probe detail/metrics/issue-text -> current language. Canonical form —
    EN probe strings (no Russian in the code); templated forms are parsed
    by regexes, the rest via "detail"; a locale without sections — as is."""
    loc = LOCALES.get(_LANG)
    if not loc or not s:
        return s
    tpl = loc.get("tpl", {})
    m = re.fullmatch(r":(\d+) busy · foreign process pid (\d+)", s)
    if m and tpl.get("busy_port"):
        return tpl["busy_port"].format(p=m.group(1), pid=m.group(2))
    m = re.fullmatch(r"(\d+) · missing '(.*)'", s)
    if m and tpl.get("missing"):
        return tpl["missing"].format(code=m.group(1), kw=m.group(2))
    s = loc.get("detail", {}).get(s, s)
    s = re.sub(r"(\d+)h(\d+)m\b",
               lambda g: tpl.get("uptime", "{h}h{m}m").format(
                   h=g.group(1), m=g.group(2)),
               s)                                  # uptime 7h12m -> localized tpl
    # number-start boundary: leave "0x3d"/IPv6 "::1d"/"item3m" alone
    s = re.sub(r"(?<![\w.:])(\d+)m\b", r"\1" + tpl.get("unit_min", "m"), s)
    s = re.sub(r"(?<![\w.:])(\d+)d\b", r"\1" + tpl.get("unit_day", "d"), s)
    return s


def load_projects():
    if os.path.exists(CONFIG_FILE):
        data = _load_json(CONFIG_FILE, DEFAULT_PROJECTS)
        if not isinstance(data, list):
            return DEFAULT_PROJECTS
        out = []
        for p in data:
            if not isinstance(p, dict) or not isinstance(p.get("name"), str) \
                    or not isinstance(p.get("cmd"), str):
                continue
            if not isinstance(p.get("cwd"), str):
                p["cwd"] = ""
            p.setdefault("pid", None)
            out.append(p)
        return out
    return DEFAULT_PROJECTS


def save_projects(projects):
    _save_json(CONFIG_FILE, projects)


def kill_proc_tree(pid):
    """Terminate a process and all its child processes."""
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        for child in children:
            child.kill()
        parent.kill()
        return True
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False


def kill_process_by_port(port):
    """Terminate processes LISTENING on the given port (LISTEN only —
    otherwise we would kill a process with an ordinary outbound connection)"""
    killed_pids = []
    for conn in psutil.net_connections(kind='inet'):
        if conn.status == "LISTEN" and conn.laddr and conn.laddr.port == port:
            pid = conn.pid
            # own PID is excluded — :4850 is our API
            if pid and pid != os.getpid() and pid not in killed_pids:
                if kill_proc_tree(pid):
                    killed_pids.append(pid)
    return killed_pids


def pids_on_port(port):
    """Pids of processes listening on the port (for the confirm dialog)."""
    pids = []
    try:
        for c in psutil.net_connections(kind="inet"):
            if c.status == "LISTEN" and c.laddr and c.laddr.port == port \
                    and c.pid and c.pid not in pids:
                pids.append(c.pid)
    except (psutil.AccessDenied, OSError):
        pass
    return pids


def is_pid_running(pid, ctime=None):
    """pid is alive; ctime — create_time at pid adoption, without it
    a foreign process may land on the same pid after a reboot."""
    if not pid or not psutil.pid_exists(pid):
        return False
    if ctime is None:
        return True
    try:
        return psutil.Process(pid).create_time() == ctime
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False


def pid_ctime(pid):
    try:
        return psutil.Process(pid).create_time()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None


SHELLS = {"cmd.exe", "powershell.exe", "pwsh.exe", "bash.exe", "sh.exe", "zsh.exe",
          "windowsterminal.exe", "wt.exe", "conhost.exe", "explorer.exe", "code.exe",
          "devin.exe", "codex.exe", "studiomcp.exe", "git.exe", "ssh.exe", "npx.exe",
          "sh", "bash", "zsh", "fish", "ssh", "npx"}  # POSIX names without .exe


def find_project_pid(project):
    """pid of the project process: exe or a cmdline path inside the project folder (minus shells/agents)."""
    if not project.get("cwd"):
        return None  # '' → normpath('.') matches almost everything
    target = os.path.normcase(os.path.normpath(project["cwd"])) + os.sep
    best = None
    for p in psutil.process_iter(["pid", "exe", "cmdline", "name"]):
        try:
            info = p.info
            if (info["name"] or "").lower() in SHELLS:
                continue
            cl = os.path.normcase(" ".join(info["cmdline"] or [])
                                  .replace("/", os.sep))
            exe = os.path.normcase((info["exe"] or "")
                                   .replace("/", os.sep))
            if exe.startswith(target) or target in cl:
                if best is None or info["pid"] < best:
                    best = info["pid"]
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return best


def find_project_ports(pid):
    """Listening ports of the process tree (for auto-URL)."""
    try:
        pids = {pid} | {c.pid for c in psutil.Process(pid).children(recursive=True)}
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pids = {pid}
    ports = set()
    for conn in psutil.net_connections(kind="inet"):
        if conn.status == "LISTEN" and conn.pid in pids:
            ports.add(conn.laddr.port)
    return sorted(ports)


def proc_stats(pid, cpu_cache):
    """'pid N · 3% · 45MB' — process metrics with tree for projects."""
    try:
        p = cpu_cache.setdefault(pid, psutil.Process(pid))
        cpu = p.cpu_percent()
        mem = p.memory_info().rss + sum(
            c.memory_info().rss for c in p.children(recursive=True))
        return f"pid {pid:>6} · {cpu:>3.0f}% · {mem // 1048576:>4}MB"
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return f"pid {pid}"


# --- Services and autostart --------------------------------------------------

DEFAULT_SERVICES = []


def load_services():
    """Services from services_config.json; if missing — write the default."""
    if not os.path.exists(SERVICES_FILE):
        try:
            save_services(DEFAULT_SERVICES)
        except OSError:
            pass
        return [dict(s) for s in DEFAULT_SERVICES]
    data = _load_json(SERVICES_FILE, [dict(s) for s in DEFAULT_SERVICES])
    return [_norm_service(s) for s in data if _norm_service(s)] \
        if isinstance(data, list) else [dict(s) for s in DEFAULT_SERVICES]


def _norm_service(s):
    """Trust boundary: a broken manual config edit must not crash the dashboard.
    None → skip the entry."""
    if not isinstance(s, dict) or not isinstance(s.get("name"), str) \
            or not s["name"].strip():
        return None
    if not isinstance(s.get("sub"), str):
        s["sub"] = str(s.get("sub") or "")
    if "ports" in s:  # strings/numbers/garbage → int list, broken items skipped
        ports = []
        for p in s["ports"] if isinstance(s["ports"], list) else ():
            try:
                if 0 < int(p) <= 65535:
                    ports.append(int(p))
            except (TypeError, ValueError):
                pass
        if ports:
            s["ports"] = ports
        else:
            del s["ports"]
    try:  # memory watchdog: positive int MB or drop the key
        lim = s.get("mem_limit_mb")
        lim = 0 if isinstance(lim, bool) else int(lim or 0)
        if lim > 0:
            s["mem_limit_mb"] = lim
        else:
            s.pop("mem_limit_mb", None)
    except (TypeError, ValueError):
        s.pop("mem_limit_mb", None)
    try:  # periodic restart, minutes: positive int or drop
        every = s.get("restart_every_min")
        every = 0 if isinstance(every, bool) else int(every or 0)
        if every > 0:
            s["restart_every_min"] = every
        else:
            s.pop("restart_every_min", None)
    except (TypeError, ValueError):
        s.pop("restart_every_min", None)
    w = s.pop("watch", None)  # watch-restart flag: explicit truthy → real bool
    if w == 1 or str(w).strip().lower() in ("1", "true"):
        s["watch"] = True
    if "env" in s:  # KEY=value overrides → str dict or drop
        e = {str(k): str(v) for k, v in s["env"].items()} \
            if isinstance(s["env"], dict) else {}
        if e:
            s["env"] = e
        else:
            del s["env"]
    if "env_profiles" in s:  # profile name -> {KEY: value}; dict entries only
        ep = {str(k): {str(ek): str(ev) for ek, ev in v.items()}
              for k, v in s["env_profiles"].items()
              if isinstance(v, dict)} \
            if isinstance(s["env_profiles"], dict) else {}
        if ep:
            s["env_profiles"] = ep
        else:
            del s["env_profiles"]
    # chosen profile name: non-empty str; core validates it against
    # env_profiles on apply (the profiles key may arrive later)
    if "env_profile" in s and (not isinstance(s["env_profile"], str)
                               or not s["env_profile"].strip()):
        del s["env_profile"]
    return s


def save_services(services):
    _save_json(SERVICES_FILE, services)


def _port_open(port, host="127.0.0.1", timeout=0.3):
    try:
        with socket.create_connection((host, port), timeout):
            return True
    except OSError:
        return False


def _port_open_confirmed(port, host="127.0.0.1"):
    """Second opinion before declaring an up-service's port dead: a single
    300ms connect can fail under ephemeral-port pressure (TIME_WAIT flood),
    which used to flap up→dead and spawn phantom crash+restart cycles."""
    if _port_open(port, host):
        return True
    time.sleep(0.25)
    return _port_open(port, host, timeout=1.0)


def append_dashboard_log(text):
    """Dashboard's own event log on disk — the in-memory deque dies with the
    process and the packaged exe sends stdout to devnull, so crashes were
    invisible. Single-generation rotation keeps it bounded."""
    try:
        os.makedirs(LOGS_DIR, exist_ok=True)
        p = os.path.join(LOGS_DIR, "dashboard.log")
        if os.path.exists(p) and os.path.getsize(p) > 512 * 1024:
            try:
                os.replace(p, p + ".1")
            except OSError:
                pass
        with open(p, "a", encoding="utf-8", errors="replace") as f:
            f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} {text}\n")
    except OSError:
        pass


def decode_log(data):
    """Log bytes → text. Run markers are UTF-8, child stdout arrives raw —
    on Windows that's the ANSI codepage (cp1251 here). Decode per line:
    strict UTF-8, ANSI fallback — a mixed file keeps both halves readable."""
    fb = "mbcs" if pi.IS_WIN else "utf-8"
    out = []
    for b in data.splitlines():
        try:
            out.append(b.decode("utf-8"))
        except UnicodeDecodeError:
            out.append(b.decode(fb, errors="replace"))
    return "\n".join(out)


def _service_log_path(spec):
    """logs/<name>.log — safe file name."""
    name = re.sub(r'[\\/:*?"<>|]', "_", spec["name"])
    return os.path.join(LOGS_DIR, name + ".log")


def _proc_snapshot():
    """(procs, {port: pid}, {port: ip} of LAN-exposed listeners);
    proc is kept for lazy cwd()."""
    out = []
    for p in psutil.process_iter(["pid", "name", "exe", "cmdline", "ppid"]):
        try:
            i = p.info
            if (i["name"] or "").lower() in SHELLS:
                continue
            out.append({"pid": i["pid"], "proc": p, "ppid": i["ppid"],
                        "name": (i["name"] or "").lower(),
                        "exe": os.path.normcase(i["exe"] or "")
                            .replace("/", os.sep),
                        "cmd": " ".join(i["cmdline"] or []),
                        "cl": os.path.normcase(" ".join(i["cmdline"] or []))
                            .replace("/", os.sep)})
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    listeners, lan = {}, {}
    try:
        for c in psutil.net_connections(kind="tcp"):
            if c.status == "LISTEN" and c.pid and c.laddr:
                listeners.setdefault(c.laddr.port, c.pid)
                # 0.0.0.0/:: or a concrete LAN IP — listens beyond localhost
                if (c.laddr.ip or "") not in ("127.0.0.1", "::1", "localhost",
                                              "::ffff:127.0.0.1"):
                    lan[c.laddr.port] = c.laddr.ip
    except (psutil.AccessDenied, OSError):
        pass
    return out, listeners, lan


# Classification of foreign port listeners.
# shortcut: rough base by process name + typical ports (not pulling the full
# IANA table); extend as "not recognized" complaints come in.
CATS = {"db": "CAT_DB", "dev": "CAT_DEV", "net": "CAT_NET",
        "sys": "CAT_SYS", "other": "CAT_OTHER"}

PROC_CATS = {  # process name -> (category, label)
    "postgres.exe": ("db", "PostgreSQL"), "pg_ctl.exe": ("db", "PostgreSQL"),
    "mysqld.exe": ("db", "MySQL"), "mariadbd.exe": ("db", "MariaDB"),
    "redis-server.exe": ("db", "Redis"), "memurai.exe": ("db", "Memurai"),
    "mongod.exe": ("db", "MongoDB"), "sqlservr.exe": ("db", "MS SQL"),
    "epmd.exe": ("db", "RabbitMQ"),
    "node.exe": ("dev", "Node.js"), "bun.exe": ("dev", "Bun"),
    "deno.exe": ("dev", "Deno"), "python.exe": ("dev", "Python"),
    "pythonw.exe": ("dev", "Python"), "java.exe": ("dev", "JVM"),
    "javaw.exe": ("dev", "JVM"), "dotnet.exe": ("dev", ".NET"),
    "php.exe": ("dev", "PHP"), "ruby.exe": ("dev", "Ruby"),
    "esbuild.exe": ("dev", "esbuild"),
    "zerotier-one_x64.exe": ("net", "ZeroTier"),
    "zerotier-one": ("net", "ZeroTier"),
    "nginx.exe": ("net", "nginx"), "httpd.exe": ("net", "Apache"),
    "caddy.exe": ("net", "Caddy"), "traefik.exe": ("net", "Traefik"),
    "svchost.exe": ("sys", "Windows"), "system": ("sys", "Windows"),
    "services.exe": ("sys", "Windows"), "lsass.exe": ("sys", "Windows"),
    "spoolsv.exe": ("sys", "CAT_PRINT"), "dashost.exe": ("sys", "Windows"),
    "dllhost.exe": ("sys", "Windows"), "searchindexer.exe": ("sys", "CAT_SEARCH"),
}

# interpreters: candidate name/match taken from the script arg, not the exe
INTERPRETERS = ("python", "pythonw", "node", "bun", "deno",
                "php", "ruby", "java", "javaw", "dotnet", "dart")

# "open in editor": name of a candidate IDE exe, first one found in PATH
EDITORS = ("cursor", "code", "codium", "code-insiders", "sublime_text")


def find_editor():
    """Editor exe from PATH or None."""
    import shutil
    return next((e for e in EDITORS if shutil.which(e)), None)


_vinfo_cache = {}
_vinfo_lib = None


def _vinfo():
    """version.dll with declared argtypes (pointers truncate without them
    on 64-bit); None off Windows."""
    global _vinfo_lib
    if _vinfo_lib is None and pi.IS_WIN:
        import ctypes
        from ctypes import wintypes as w
        v = ctypes.windll.version
        v.GetFileVersionInfoSizeW.argtypes = w.LPCWSTR, w.LPDWORD
        v.GetFileVersionInfoSizeW.restype = w.DWORD
        v.GetFileVersionInfoW.argtypes = w.LPCWSTR, w.DWORD, w.DWORD, w.LPVOID
        v.GetFileVersionInfoW.restype = w.BOOL
        v.VerQueryValueW.argtypes = w.LPCVOID, w.LPCWSTR, \
            ctypes.POINTER(w.LPVOID), ctypes.POINTER(w.UINT)
        v.VerQueryValueW.restype = w.BOOL
        _vinfo_lib = v
    return _vinfo_lib


def exe_label(path):
    """FileDescription/ProductName from the exe version resource —
    the binary describes itself, no vendor table needed. '' on
    POSIX/failure. Cached: called per candidate tick."""
    if not path or not pi.IS_WIN:
        return ""
    path = os.path.normpath(path)
    if path in _vinfo_cache:
        return _vinfo_cache[path]
    out = ""
    try:
        import ctypes
        from ctypes import wintypes as w
        ver = _vinfo()
        size = ver.GetFileVersionInfoSizeW(path, None)
        buf = ctypes.create_string_buffer(size) if size else None
        if buf and ver.GetFileVersionInfoW(path, 0, size, buf):
            pv, ln = w.LPVOID(), w.UINT()
            if ver.VerQueryValueW(buf, r"\VarFileInfo\Translation",
                                  ctypes.byref(pv), ctypes.byref(ln)) \
                    and ln.value:
                lang, cp = (w.WORD * 2).from_address(pv.value)
                for field in ("FileDescription", "ProductName"):
                    sub = rf"\StringFileInfo\{lang:04x}{cp:04x}\{field}"
                    if ver.VerQueryValueW(buf, sub, ctypes.byref(pv),
                                          ctypes.byref(ln)) and ln.value:
                        out = ctypes.wstring_at(pv.value).strip()
                        if out:
                            break
    except Exception:
        pass
    _vinfo_cache[path] = out
    return out


WELL_KNOWN = {  # port -> (category, label) when the process is unknown —
    # the name of the service itself by its typical port, not just a category
    1433: ("db", "MS SQL"), 1521: ("db", "Oracle"), 3306: ("db", "MySQL"),
    5432: ("db", "PostgreSQL"), 5433: ("db", "PostgreSQL"),
    6379: ("db", "Redis"), 27017: ("db", "MongoDB"),
    9200: ("db", "Elasticsearch"), 11211: ("db", "Memcached"),
    5672: ("db", "RabbitMQ"), 15672: ("db", "RabbitMQ"),
    4222: ("db", "NATS"), 9092: ("db", "Kafka"),
    2375: ("net", "Docker"), 2376: ("net", "Docker"),
    3000: ("dev", CATS["dev"]), 3001: ("dev", CATS["dev"]),
    4200: ("dev", CATS["dev"]), 5173: ("dev", CATS["dev"]),
    5174: ("dev", CATS["dev"]), 8000: ("dev", CATS["dev"]),
    8080: ("dev", CATS["dev"]), 8081: ("dev", CATS["dev"]),
    8888: ("dev", CATS["dev"]), 9229: ("dev", CATS["dev"]),
    80: ("net", "HTTP"), 443: ("net", "HTTPS"), 53: ("net", "DNS"),
    9993: ("net", "ZeroTier"),
}


def port_class(proc_name, port):
    """(category, label) of a listener: by process name first, then by port.
    POSIX names have no .exe → also try with the suffix."""
    n = (proc_name or "").lower()
    c = PROC_CATS.get(n) or PROC_CATS.get(n + ".exe") \
        or PROC_CATS.get(n.rstrip("0123456789") + ".exe")  # python3 → python
    return c or WELL_KNOWN.get(port) or ("other", CATS["other"])


def _proc_stats(matched, cpu_cache=None):
    """' · 3% · 45MB · 1h 30m' from the first matching process; '' if unavailable.
    cpu_cache: {pid: Process} — else cpu_percent() on a fresh object is always 0."""
    if not matched:
        return ""
    try:
        p = matched[0]["proc"]
        if cpu_cache is not None:
            p = cpu_cache.setdefault(p.pid, p)
        cpu = p.cpu_percent()
        mb = p.memory_info().rss // 1048576
        mins = max(0, int((time.time() - p.create_time()) // 60))
        up = f"{mins // 60}h{mins % 60:02d}m" if mins >= 60 else f"{mins}m"
        # fixed field widths — metric columns align across rows
        return f" · {cpu:>3.0f}% · {mb:>4}MB · {up:>6}"
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return ""


def _probe_service(spec, procs, listeners, cpu_cache=None,
                   confirm_dead=False):
    """(state, detail): up=green, down=gray, dead=red, off=cleanly off."""
    matched = [p for p in procs
               if (spec.get("proc") and p["name"] == spec["proc"])
               or (spec.get("match") and spec["match"].lower() in p["cl"])]
    pids = [p["pid"] for p in matched]
    ports = spec.get("ports", ())
    if ports:
        pt = next((pt for pt in ports if _port_open(pt)), None)
        if pt is None and confirm_dead:
            # was "up" a tick ago — confirm the miss before "dead"/"down"
            pt = next((pt for pt in ports if _port_open_confirmed(pt)), None)
        if pt is not None:
            owner = listeners.get(pt)
            if owner and owner not in pids \
                    and (spec.get("proc") or spec.get("match")):
                return "dead", f":{pt} busy · foreign process pid {owner}"
            return "up", f":{pt}" + (f" · pid {pids[0]:>6}" if pids else "") \
                         + _proc_stats(matched, cpu_cache)
        return ("dead", "port closed") if pids else ("down", "stopped")
    if pids:
        return "up", f"pid {pids[0]:>6}" + _proc_stats(matched, cpu_cache)
    return ("off", spec["note"]) if spec.get("note") else ("down", "not running")


# --- Remote monitors (spec type: http|tcp|docker) ----------------------------

def _remote_interval(spec):
    """Probe interval in seconds: spec interval, else docker=15, others=30."""
    try:
        v = int(spec.get("interval") or 0)
        if v > 0:
            return v
    except (TypeError, ValueError):
        pass
    return {"docker": 15}.get(spec.get("type"), 30)


def _cert_days(url):
    """Days until the host TLS certificate expires; None if not https or on error."""
    u = urlparse(url)
    if u.scheme != "https" or not u.hostname:
        return None
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((u.hostname, u.port or 443), timeout=3) as sock:
            with ctx.wrap_socket(sock, server_hostname=u.hostname) as s:
                exp = datetime.strptime(
                    s.getpeercert()["notAfter"], "%b %d %H:%M:%S %Y %Z")
        return (exp - datetime.utcnow()).days
    except Exception:
        return None


def _probe_remote(spec):
    """(state, detail) for a remote spec; same state codes as local ones."""
    t = spec.get("type")
    if t == "tcp":
        t0 = time.time()
        try:
            socket.create_connection(
                (spec["host"], int(spec["port"])), timeout=3).close()
            return "up", f"{int((time.time() - t0) * 1000)}ms"
        except (OSError, KeyError, ValueError):
            return "dead", "unreachable"
    if t == "docker":
        try:
            out = subprocess.run(
                ["docker", "ps", "--format", "{{json .}}"],
                capture_output=True, text=True, timeout=3,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except FileNotFoundError:
            return "off", "no cli"
        except subprocess.TimeoutExpired:
            return "dead", "engine down"
        if out.returncode != 0:
            return "dead", "engine down"
        for line in out.stdout.splitlines():
            try:
                c = json.loads(line)
            except ValueError:
                continue
            if spec.get("container") and spec["container"] in (c.get("Names") or ""):
                return ("up" if c.get("State") == "running" else "down",
                        c.get("Status", ""))
        return ("off", spec["note"]) if spec.get("note") \
            else ("down", "container not found")
    # http: env_key — Bearer from .env + an apikey duplicate (common
    # Bearer+apikey convention: servers ignore the extra header)
    req = urllib.request.Request(spec["url"])
    if spec.get("env_key"):
        tok = _env_get(spec.get("env_file") or os.path.join(DATA_DIR, ".env"),
                       spec["env_key"])
        if tok:
            req.add_header("Authorization", f"Bearer {tok}")
            req.add_header("apikey", tok)
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            code = r.status
            body = r.read(65536) if spec.get("keyword") else b""
        ms = int((time.time() - t0) * 1000)
        detail = f"{code} · {ms}ms"
        if spec.get("keyword") and spec["keyword"].encode() not in body:
            return "dead", f"{code} · missing '{spec['keyword']}'"
        days = _cert_days(spec["url"])
        if days is not None and days < 14:
            detail += f" · cert {days}d"
        return "up", detail
    except urllib.error.HTTPError as e:
        return "dead", f"HTTP {e.code} · {int((time.time() - t0) * 1000)}ms"
    except (socket.timeout, TimeoutError):
        return "dead", "timeout"
    except Exception as e:
        return "dead", str(getattr(e, "reason", e))[:40]


def _read_autorun():
    """Autostart entries -> [(name, cmd)]: Run registry / LaunchAgents."""
    return pi.autorun_entries()


def _autorun_disabled():
    """Names of entries the user disabled without deleting (StartupApproved)."""
    return pi.autorun_disabled_names()


SELF_AUTORUN_NAME = "DevDashboard"


def self_autorun_cmd():
    """Command line for our own Run entry: the frozen exe, or
    pythonw + dashboard.py in dev mode (no console window at login)."""
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}" --minimized'
    exe = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    if not os.path.exists(exe):
        exe = sys.executable
    return f'"{exe}" "{os.path.join(BASE_DIR, "dashboard.py")}" --minimized'


def self_autorun_is(name, cmd):
    """Our entry = right name AND a command that launches this app —
    a foreign same-named Run value does not count. Covers both layouts:
    exe-written (…\\dist\\DevDashboard.exe) and dev-written
    (pythonw …\\dashboard.py) — dev and frozen see each other's entries."""
    if name.lower() != SELF_AUTORUN_NAME.lower():
        return False
    c = os.path.normcase(cmd)
    dirs = (os.path.normcase(BASE_DIR),
            os.path.normcase(os.path.dirname(BASE_DIR)))
    return "devdashboard.exe" in c or (
        "dashboard.py" in c and any(d in c for d in dirs if d))


def self_autorun_enabled():
    """True when our Run entry exists and is not StartupApproved-disabled."""
    return any(self_autorun_is(n, c) for n, c in _read_autorun()) \
        and SELF_AUTORUN_NAME not in _autorun_disabled()


def self_autorun_set(enabled):
    if enabled:
        pi.autorun_write(SELF_AUTORUN_NAME, self_autorun_cmd())
        pi.autorun_set_enabled(SELF_AUTORUN_NAME, True)
    else:
        try:
            pi.autorun_delete(SELF_AUTORUN_NAME)
        except OSError:
            pass  # entry already absent


def _autorun_set_enabled(name, enabled):
    """Enable/disable an autostart entry without deleting (Task Manager style)."""
    pi.autorun_set_enabled(name, enabled)


def _env_get(path, key):
    """Value of a key from .env; '' when absent."""
    return _env_kv(path).get(key, "")


def _env_set(path, key, value):
    """Write KEY=value into .env: replace the line or append at the end."""
    try:
        lines = open(path, encoding="utf-8").read().splitlines()
    except OSError:
        lines = []
    for i, line in enumerate(lines):
        if line.split("=", 1)[0].strip() == key:
            lines[i] = f"{key}={value}"
            break
    else:
        lines.append(f"{key}={value}")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


_ENV_REF_RE = re.compile(r"\$\{(\w+)\}|\$(\w+)|%(\w+)%")


def expand_env(env):
    """${VAR}, $VAR and %VAR% refs in values -> os.environ (configs come
    from users of any shell/OS); unknown refs stay as-is. New dict."""
    def sub(m):
        return os.environ.get(next(g for g in m.groups() if g), m.group(0))
    return {k: _ENV_REF_RE.sub(sub, str(v)) for k, v in (env or {}).items()}


_ENV_PORT_K = re.compile(r"(?:^|_)PORT$", re.I)
_ENV_URL_K = re.compile(r"(?:^|_)(?:URL|URI|ENDPOINT)$", re.I)


def validate_env(env, prefix=""):
    """Env sanity warnings -> [{key, code, msg}]. Advisory only —
    callers attach the list to the save response, never reject."""
    out = []
    for k, v in (env or {}).items():
        if not v:
            continue
        v = str(v)
        kk = f"{prefix}{k}"
        if _ENV_PORT_K.search(k):
            try:
                n = int(v)
                if not 1 <= n <= 65535:
                    raise ValueError
            except ValueError:
                out.append({"key": kk, "code": "port",
                            "msg": tr("ENV_WARN_PORT", name=kk, value=v)})
        elif _ENV_URL_K.search(k) and not re.match(r"https?://", v):
            out.append({"key": kk, "code": "url",
                        "msg": tr("ENV_WARN_URL", name=kk)})
    return out


def env_profile_env(spec):
    """Env for launch: spec env overlaid by the chosen env_profile
    (profile values win), var refs expanded, cred: refs resolved from
    the OS credential store.
    shortcut: a missing/unreadable credential degrades to "" — upgrade
    = raise an issue on resolution failure."""
    env = dict(spec.get("env") or {})
    prof = (spec.get("env_profiles") or {}).get(spec.get("env_profile"))
    if isinstance(prof, dict):
        env.update(prof)
    return {k: (pi.cred_read(v[5:]) or "") if v.startswith("cred:") else v
            for k, v in expand_env(env).items()}


def _autorun_is_mine(name, cmd, project_dirs, mine_tokens=()):
    """Own = command/name matches a project cwd, a service folder, or
    the name/stem of a start file from the services spec."""
    s = (name + " " + cmd).lower().replace("/", "\\")
    return any(d in s for d in project_dirs) \
        or any(t and t in s for t in mine_tokens)


def _autorun_target(cmd):
    """Target path of a command: quotes, drive-rooted path to an extension, else None."""
    if not pi.IS_WIN:
        for t in cmd.split():  # plist command: first absolute path
            if t.startswith("/"):
                return t
        return None
    m = re.search(r'"([a-zA-Z]:[^"]+)"', cmd)
    if m:
        return m.group(1)
    m = re.search(r"[a-zA-Z]:[\\/].+?\.(?:exe|cmd|bat|py|com|ps1|vbs)\b",
                  cmd, re.IGNORECASE)
    if m:
        return m.group(0)
    m = re.search(r"\S+", cmd)
    t = m.group(0) if m else ""
    return t if ("\\" in t or "." in t) else None  # bare 'pythonw' is not a path


def _autorun_running(cmd, procs):
    """Is an autostart command running: by exe, by script/folder name in cmdline,
    and for .cmd wrappers (parent already dead) — by process cwd in the launcher folder."""
    target = _autorun_target(cmd)
    if not target:
        return False
    tnorm = os.path.normcase(os.path.normpath(target))
    base, tdir = os.path.basename(tnorm), os.path.dirname(tnorm)
    if tnorm.endswith(".exe"):
        return any(p["exe"] == tnorm or p["name"] == base for p in procs)
    if any(base in p["cl"] or tdir + os.sep in p["cl"] for p in procs):
        return True
    for p in procs:
        try:
            cwd = os.path.normcase(p["proc"].cwd())
            if cwd == tdir or cwd.startswith(tdir + os.sep):
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, OSError):
            continue
    return False


def start_service_process(spec, log_append, job=None):
    """Popen for a service start command writing to logs/<name>.log.
    job (process_tree.Job) — if given, the process starts suspended and
    is assigned to the Job before resuming (no child-process race).
    Returns (ok, err_str|None, Popen|None) — proc is the shell wrapper,
    alive while the service tree lives (probe fallback for spec without proc/match)."""
    cmd, cwd = spec.get("start"), spec.get("cwd") or None
    if not cmd:
        return False, "no start command in service config.", None
    try:
        os.makedirs(LOGS_DIR, exist_ok=True)
        log = open(_service_log_path(spec), "a", encoding="utf-8",
                   errors="replace")
        log.write(f"\n--- {datetime.now():%Y-%m-%d %H:%M:%S} "
                  + tr("LOG_RUN_MARKER", cmd=cmd) + " ---\n")
        log.flush()
    except OSError:
        log = subprocess.DEVNULL
    env = dict(os.environ)
    env.update(env_profile_env(spec))  # spec env + chosen profile, $VAR expanded
    proc = None
    try:
        pk = pi.popen_kwargs()
        if job and pi.IS_WIN:
            pk["creationflags"] = pk.get("creationflags", 0) | 0x00000004
            # CREATE_SUSPENDED: assign to the Job before resuming, no race

        def spawn(args):
            nonlocal job, proc
            p = subprocess.Popen(
                args, cwd=cwd, env=env, stdout=log,
                stderr=subprocess.STDOUT, **pk)
            if job:
                try:
                    ok = job.assign(p)
                finally:
                    if pi.IS_WIN:  # start was suspended — wake it up
                        try:
                            psutil.Process(p.pid).resume()
                        except psutil.Error:
                            pass
                if not ok:  # refusal (foreign Job): close the handle, live on without it
                    job.disarm()
                    job.close()
                    job = None
            proc = p
            return p

        try:
            if pi.IS_WIN and not cmd.lower().endswith((".cmd", ".bat")):
                spawn(cmd)
            else:
                # POSIX: the command string always goes through a login shell —
                # sh resolves PATH/version-managers, args and shebang
                spawn(pi.shell_argv(cmd))
        except FileNotFoundError:
            # bare 'pythonw' etc. — let the shell resolve PATH/PATHEXT
            spawn(pi.shell_argv(cmd))
    except OSError as e:
        return False, str(e), None
    finally:
        if log is not subprocess.DEVNULL:
            log.close()
    log_append(f"[{spec['name']}] " + tr("LOG_STARTED", cmd=cmd))
    return True, None, proc


def scan_roots():
    """Project search folders from settings; empty — home dir (frozen) or
    the BASE_DIR parent (running from source — projects are usually nearby)."""
    roots = load_settings()["scan_roots"] or (
        [os.path.expanduser("~")] if getattr(sys, "frozen", False)
        else [os.path.dirname(BASE_DIR)])
    return [os.path.normpath(r) for r in roots]


_EXAMPLE_NAMES = (".env.example", ".env.sample", ".env.template",
                  ".env.dist", ".env.defaults")


def _env_kv(path):
    """KEY -> value from .env; {} on absence/error."""
    out = {}
    try:
        for line in open(path, encoding="utf-8", errors="replace"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                if k.strip():
                    out[k.strip()] = v.strip().strip("\"'")
    except OSError:
        pass
    return out


def env_diff(directory):
    """Diff .env vs .env.example: missing — absent from .env (error),
    extra — undocumented in example (warn), empty — empty values
    in .env (warn). The envaudit/dotenv-checker pattern.
    None — no example file, nothing to compare against."""
    env = _env_kv(os.path.join(directory, ".env"))
    for name in _EXAMPLE_NAMES:
        want = set(_env_kv(os.path.join(directory, name)))
        if want:
            return {"missing": sorted(want - set(env)),
                    "extra": sorted(set(env) - want),
                    "empty": sorted(k for k, v in env.items() if not v)}
    return None


def canon_path(p):
    """Path key for cross-source comparison: realpath expands 8.3 short
    names and symlinks, so a scan root in one form and a git-reported
    path in another still compare equal."""
    return os.path.normcase(os.path.realpath(p))


def git_dir_of(directory):
    """Real git dir for a checkout: the .git dir as-is, or the
    "gitdir: <path>" pointer target of a worktree/submodule .git file.
    '' — no usable .git."""
    git = os.path.join(directory, ".git")
    if not os.path.isfile(git):
        return git if os.path.isdir(git) else ""
    try:
        ptr = open(git, encoding="utf-8").read().strip()
    except OSError:
        return ""
    if not ptr.startswith("gitdir:"):
        return ""
    git = ptr[7:].strip()
    if not os.path.isabs(git):
        git = os.path.normpath(os.path.join(directory, git))
    return git


def git_branch(directory):
    """Branch from .git/HEAD without subprocess (pier/Portlivo feature).
    '' — not a repo; short sha on detached HEAD.
    Worktree: .git is a "gitdir: <path>" file, HEAD lives there."""
    git = git_dir_of(directory)
    if not git:
        return ""
    try:
        head = open(os.path.join(git, "HEAD"),
                    encoding="utf-8").read().strip()
    except OSError:
        return ""
    if head.startswith("ref: refs/heads/"):
        return head[16:]
    return head[:7] if head else ""


def env_committed(directory):
    """.env is tracked by git — secrets live in history (worse than an
    unignored working file). False without .git/.env or on any error."""
    if not os.path.isfile(os.path.join(directory, ".env")) \
            or not os.path.exists(os.path.join(directory, ".git")):
        return False
    try:
        return subprocess.run(
            ["git", "-C", directory, "ls-files", "--error-unmatch", ".env"],
            capture_output=True, timeout=3,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
        ).returncode == 0
    except Exception:
        return False


def env_gitignore_open(directory):
    """True if .env exists and .gitignore does not cover it —
    secrets would leak into a commit (dotenv-sentinel feature).
    shortcut: match basic patterns, not the full gitignore DSL —
    exotic forms like `dir/**/.env` do not count as coverage."""
    if not os.path.isfile(os.path.join(directory, ".env")) \
            or not os.path.exists(os.path.join(directory, ".git")):
        return False
    try:
        lines = open(os.path.join(directory, ".gitignore"),
                     encoding="utf-8", errors="replace").read().splitlines()
    except OSError:
        return True
    for ln in lines:
        p = ln.strip()
        if not p or p.startswith(("#", "!")) or p.endswith("/"):
            continue  # comment, `!.env` negation, dir-only pattern — not coverage
        if p.lstrip("/") in (".env", "*.env", ".env*", "*", "**/.env",
                             "**/*.env"):
            return False
    return True


# meta-frameworks before the base libraries (next > react, nuxt > vue)
_JS_FRAMEWORKS = (
    ("next", "Next.js"), ("nuxt", "Nuxt"), ("@angular/core", "Angular"),
    ("@sveltejs/kit", "SvelteKit"), ("astro", "Astro"), ("remix", "Remix"),
    ("@nestjs/core", "Nest"), ("expo", "Expo"), ("react-scripts", "CRA"),
    ("gatsby", "Gatsby"), ("vite", "Vite"), ("express", "Express"),
    ("fastify", "Fastify"), ("vue", "Vue"), ("svelte", "Svelte"),
    ("react", "React"),
)


def _js_framework(pkg):
    deps = {**(pkg.get("dependencies") or {}),
            **(pkg.get("devDependencies") or {})}
    for key, label in _JS_FRAMEWORKS:
        if key in deps:
            return label
    return ""


def _py_framework(directory):
    """Django/Flask/FastAPI from pyproject.toml + requirements*.txt."""
    blob = ""
    try:
        import tomllib
        with open(os.path.join(directory, "pyproject.toml"), "rb") as f:
            data = tomllib.load(f)
        blob = str(data.get("project", {}).get("dependencies", "")) + str(
            data.get("tool", {}).get("poetry", {}).get("dependencies", ""))
    except Exception:
        pass
    for fname in ("requirements.txt", "requirements-dev.txt"):
        try:
            blob += open(os.path.join(directory, fname),
                         encoding="utf-8", errors="replace").read()
        except OSError:
            pass
    blob = blob.lower()
    for key, label in (("django", "Django"), ("fastapi", "FastAPI"),
                       ("flask", "Flask"), ("starlette", "Starlette")):
        if key in blob:
            return label
    return "Python"


def project_framework(directory):
    """Framework label of a project folder (for projects added
    before the scan or manually). '' — unrecognized."""
    pj = os.path.join(directory, "package.json")
    if os.path.isfile(pj):
        try:
            return _js_framework(json.load(open(pj, encoding="utf-8")))
        except Exception:
            return ""
    if os.path.isfile(os.path.join(directory, "manage.py")):
        return "Django"
    if os.path.isfile(os.path.join(directory, "go.mod")):
        return "Go"
    if os.path.isfile(os.path.join(directory, "Cargo.toml")):
        return "Rust"
    if os.path.isfile(os.path.join(directory, "pyproject.toml")) \
            or os.path.isfile(os.path.join(directory, "requirements.txt")):
        return _py_framework(directory)
    return ""


_PY_ENTRIES = ("manage.py", "app.py", "main.py", "server.py", "wsgi.py",
               "run.py", "__main__.py")

_PORT_ARG_RE = re.compile(r"--port[=\s](\d+)|PORT=(\d{2,5})")
_ENV_PORT_RE = re.compile(r"\s*(?:[A-Z][\w]*_)?PORT\s*=\s*(\d{2,5})")


def _pm_for(dirpath, fs, pkg):
    """Node package manager: packageManager field > lockfile > npm."""
    pm = (pkg.get("packageManager") or "").split("@")[0]
    if pm in ("npm", "pnpm", "yarn", "bun"):
        return pm
    for lock, pm_ in (("pnpm-lock.yaml", "pnpm"), ("bun.lockb", "bun"),
                      ("bun.lock", "bun"), ("yarn.lock", "yarn")):
        if lock in fs:
            return pm_
    return "npm"


def _env_port(directory):
    """PORT-ish var from .env/.env.local -> http url guess."""
    for ef in (".env", ".env.local"):
        try:
            for ln in open(os.path.join(directory, ef),
                           encoding="utf-8", errors="replace"):
                m = _ENV_PORT_RE.match(ln)
                if m and int(m.group(1)) <= 65535:
                    return f"http://127.0.0.1:{m.group(1)}"
        except OSError:
            pass
    return ""


# last-resort url guess: the framework's conventional dev-server port
_FW_PORTS = {
    "Vite": 5173, "SvelteKit": 5173, "Astro": 4321, "Next.js": 3000,
    "Nuxt": 3000, "Remix": 3000, "Nest": 3000, "CRA": 3000,
    "Express": 3000, "Fastify": 3000, "Angular": 4200, "Gatsby": 8000,
    "Expo": 8081, "Django": 8000, "Flask": 5000, "FastAPI": 8000,
    "Starlette": 8000,
}
_VITE_CFG_RE = re.compile(r"port\s*:\s*(\d{2,5})")


def _fw_port(dirpath, framework, fs):
    """Framework-conventional dev port -> http url guess. A vite.config
    server.port wins over the default — the dev server reads the same
    file."""
    port = _FW_PORTS.get(framework)
    if not port:
        return ""
    cfg = next((f for f in fs if f.startswith("vite.config.")), None)
    if cfg:
        try:
            m = _VITE_CFG_RE.search(open(os.path.join(dirpath, cfg),
                                         encoding="utf-8",
                                         errors="replace").read())
            if m and int(m.group(1)) <= 65535:
                port = int(m.group(1))
        except OSError:
            pass
    return f"http://127.0.0.1:{port}"


def _dotnet_port(dirpath):
    """launchSettings.json applicationUrl — the port `dotnet run` binds."""
    try:
        data = json.load(open(os.path.join(
            dirpath, "Properties", "launchSettings.json"), encoding="utf-8"))
    except Exception:
        return ""
    for prof in (data.get("profiles") or {}).values():
        for u in str(prof.get("applicationUrl") or "").split(";"):
            m = re.match(r"https?://[\w.\*]+:(\d+)$", u.strip())
            if m and int(m.group(1)) <= 65535:
                return f"http://127.0.0.1:{m.group(1)}"
    return ""


def _make_target(dirpath, fs):
    """Makefile -> first conventional target (dev/run/serve/up/start)."""
    path = next((os.path.join(dirpath, m)
                 for m in ("Makefile", "makefile") if m in fs), None)
    if not path:
        return ""
    try:
        tgts = set(re.findall(r"^([A-Za-z][\w-]*)\s*:",
                              open(path, encoding="utf-8",
                                   errors="replace").read(), re.M))
    except OSError:
        return ""
    return next((t for t in ("dev", "run", "serve", "up", "start")
                 if t in tgts), "")


_COMPOSE_FILES = ("docker-compose.yml", "docker-compose.yaml",
                  "compose.yml", "compose.yaml")


def _compose_services(dirpath, fs):
    """Service names from compose.yml. shortcut: 2-space indent parse of
    the services: block — covers stock files; exotic anchors/profiles
    slip through, upgrade = a real yaml dep."""
    f = next((x for x in _COMPOSE_FILES if x in fs), None)
    if not f:
        return []
    try:
        lines = open(os.path.join(dirpath, f), encoding="utf-8",
                     errors="replace").read().splitlines()
    except OSError:
        return []
    out, in_svc = [], False
    for ln in lines:
        if re.match(r"^services\s*:", ln):
            in_svc = True
            continue
        if in_svc:
            if re.match(r"^\S", ln):
                break
            m = re.match(r"^  ([A-Za-z][\w.-]*)\s*:", ln)
            if m:
                out.append(m.group(1))
    return out


def scan_project_dirs(root, known_cwds, run_dirs=None, run_ports=None):
    """Project folders outside known_cwds. Manifest priority — per the
    Portlivo: Procfile > composer > package.json > bin/dev > manage.py >
    artisan > go.mod > Cargo.toml > pyproject/requirements + entry >
    compose.
    run_dirs — normalized cwds of running processes (score boost).
    run_ports — {normalized cwd: listen port} for url prefill.
    -> [{name, cmd, cwd, framework, branch, env_missing, env_open,
         score, root, repo, worktree, compose_services, running, url}]"""
    SKIP = ("node_modules", "dist", "build", "__pycache__", "venv",
            "target", "vendor", "obj", "bin", "out", "coverage",
            "DerivedData", "Pods", "AppData")
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        # dotdirs pruned wholesale — .git/.idea/etc plus tools' caches;
        # a real project nested inside a dot-dir is rare enough to accept
        dirnames[:] = [d for d in dirnames
                       if d not in SKIP and not d.startswith(".")]
        # depth up to 4 levels — junction loops and giant trees do not hang the scan
        if dirpath[len(root):].count(os.sep) >= 4:
            dirnames[:] = []
        fs = set(filenames)
        item = None
        if "Procfile" in fs:
            cmd = ""
            try:
                for ln in open(os.path.join(dirpath, "Procfile"),
                               encoding="utf-8", errors="replace"):
                    if ":" in ln and not ln.lstrip().startswith("#"):
                        cmd = ln.split(":", 1)[1].strip()
                        break
            except OSError:
                pass
            if cmd:
                item = (cmd, "Procfile")
        elif "composer.json" in fs:
            try:
                comp = json.load(open(os.path.join(
                    dirpath, "composer.json"), encoding="utf-8"))
            except Exception:
                comp = {}
            scripts = comp.get("scripts", {})
            cmd = "composer run dev" if "dev" in scripts else \
                ("composer start" if "start" in scripts else "")
            if cmd:
                item = (cmd, "Composer")
        elif "package.json" in fs:
            try:
                pkg = json.load(open(os.path.join(dirpath, "package.json"),
                                     encoding="utf-8"))
            except Exception:
                pkg = {}
            scripts = pkg.get("scripts", {})
            pm = _pm_for(dirpath, fs, pkg)
            cmd = f"{pm} run dev" if "dev" in scripts else \
                (f"{pm} start" if "start" in scripts else "")
            if cmd:
                item = (cmd, _js_framework(pkg))
        elif not pi.IS_WIN and os.path.isfile(
                os.path.join(dirpath, "bin", "dev")):
            item = ("bin/dev", "")
        elif "manage.py" in fs:
            item = ("python manage.py runserver", "Django")
        elif "artisan" in fs:
            item = ("php artisan serve", "Laravel")
        elif "go.mod" in fs:
            item = ("go run .", "Go")
        elif "Cargo.toml" in fs:
            item = ("cargo run", "Rust")
        elif {"pyproject.toml", "requirements.txt"} & fs:
            entry = next((e for e in _PY_ENTRIES if e in fs), None)
            if entry:
                if "uv.lock" in fs:
                    item = (f"uv run {entry}", _py_framework(dirpath))
                elif "poetry.lock" in fs:
                    item = (f"poetry run python {entry}",
                            _py_framework(dirpath))
                elif "Pipfile" in fs:
                    item = (f"pipenv run python {entry}",
                            _py_framework(dirpath))
                else:  # project-local venv beats the system python
                    vpy = os.path.join(".venv",
                                       "Scripts" if pi.IS_WIN else "bin",
                                       "python.exe" if pi.IS_WIN else "python")
                    v = vpy if os.path.isfile(
                        os.path.join(dirpath, vpy)) else "python"
                    item = (f"{v} {entry}", _py_framework(dirpath))
        elif any(f.endswith(".csproj") for f in fs):
            # a sln root descends here: only EXECUTABLE projects are
            # runnable — class libs / test assemblies are not
            cs = next(f for f in fs if f.endswith(".csproj"))
            try:
                low = open(os.path.join(dirpath, cs), encoding="utf-8",
                           errors="replace").read().lower()
            except OSError:
                low = ""
            runnable = ("microsoft.net.sdk.web" in low
                        or "microsoft.net.sdk.worker" in low
                        or re.search(r"<outputtype>\s*(?:exe|winexe)",
                                     low))
            is_test = ("microsoft.net.test" in low or "xunit" in low
                       or "nunit" in low or "mstest" in low
                       or cs.lower().endswith(
                           (".tests.csproj", ".test.csproj",
                            "integrationtests.csproj")))
            if runnable and not is_test:
                item = ("dotnet run", "dotnet")
        elif "pubspec.yaml" in fs:
            item = ("flutter run", "Flutter")
        elif "mix.exs" in fs:
            phx = False
            try:
                phx = "phoenix" in open(
                    os.path.join(dirpath, "mix.exs"),
                    encoding="utf-8", errors="replace").read()
            except OSError:
                pass
            item = ("mix phx.server" if phx else "mix run", "Elixir")
        elif "pom.xml" in fs:
            psrc = ""
            try:
                psrc = open(os.path.join(dirpath, "pom.xml"),
                            encoding="utf-8", errors="replace").read()
            except OSError:
                pass
            if "spring-boot" in psrc:  # plain lib / pom parent — no run cmd
                w = "mvnw.cmd" if pi.IS_WIN else "./mvnw"
                item = ((w if os.path.isfile(os.path.join(dirpath, w))
                         else "mvn") + " spring-boot:run", "Java")
        elif {"build.gradle", "build.gradle.kts"} & fs:
            gsrc = ""
            # shortcut: root build.gradle may be bare while plugins live in
            # settings.gradle — reading both covers most multi-module repos;
            # deeper catalog setups still slip through
            for gf in ("build.gradle.kts", "build.gradle",
                       "settings.gradle.kts", "settings.gradle"):
                if gf in fs:
                    try:
                        gsrc += open(os.path.join(dirpath, gf),
                                     encoding="utf-8",
                                     errors="replace").read()
                    except OSError:
                        pass
            if "com.android" not in gsrc:  # android app — no service cmd
                w = "gradlew.bat" if pi.IS_WIN else "./gradlew"
                exe = w if os.path.isfile(os.path.join(dirpath, w)) \
                    else "gradle"
                item = (f"{exe} "
                        f"{'bootRun' if 'spring' in gsrc else 'run'}",
                        "Gradle")
        elif "Gemfile" in fs:
            item = (("bin/rails s" if os.path.isfile(
                os.path.join(dirpath, "config", "application.rb"))
                else "bundle exec rackup"), "Ruby")
        elif "justfile" in fs or "Justfile" in fs:
            item = ("just", "")
        elif "Taskfile.yml" in fs:
            item = ("task", "")
        elif "Makefile" in fs or "makefile" in fs:
            tgt = _make_target(dirpath, fs)
            if tgt:
                item = (f"make {tgt}", "")
        elif any(f in fs for f in _COMPOSE_FILES):
            item = ("docker compose up", "Docker")
        if item:
            nc = os.path.normcase(os.path.normpath(dirpath))
            if nc not in known_cwds:
                d = env_diff(dirpath)
                gitdir = os.path.join(dirpath, ".git")
                has_git = os.path.exists(gitdir)  # worktree .git is a file
                # worktree checkouts of one repo share repo_key — the main
                # repo root — so core can fold them into a single row
                repo_key, worktree = canon_path(dirpath), False
                gdir = git_dir_of(dirpath) if has_git else ""
                if os.path.basename(os.path.dirname(gdir)) == "worktrees":
                    # <main>/.git/worktrees/<w> → repo root is 3 levels up
                    repo_key = canon_path(os.path.dirname(
                        os.path.dirname(os.path.dirname(gdir))))
                    worktree = True
                branch = git_branch(dirpath)
                # score without hardcoding — only observable signals:
                # git repo, live branch, fresh mtime, recognized
                # framework, env template present, process running inside
                # a process INSIDE the project dir is evidence it runs;
                # one in a parent dir is ambiguous (e.g. this dashboard
                # serving :4850 from the repo root) — do not attribute
                running = bool(run_dirs) and any(
                    rd == nc or rd.startswith(nc + os.sep)
                    for rd in run_dirs)
                score = (3 if has_git else 0) + (1 if branch else 0) \
                    + (1 if item[1] else 0) + (1 if d is not None else 0) \
                    + (3 if running else 0)
                try:
                    mt = max(os.path.getmtime(dirpath),
                             os.path.getmtime(gitdir) if has_git else 0)
                    days = (time.time() - mt) / 86400
                    score += 2 if days < 30 else (1 if days < 180 else 0)
                except OSError:
                    pass
                url = ""
                if running and run_ports:
                    rp = next((run_ports[rd] for rd in run_ports
                               if rd == nc or rd.startswith(nc + os.sep)),
                              None)
                    if rp:
                        url = f"http://127.0.0.1:{rp}"
                if not url:
                    m = _PORT_ARG_RE.search(item[0])
                    if m and int(m.group(1) or m.group(2)) <= 65535:
                        url = f"http://127.0.0.1:{m.group(1) or m.group(2)}"
                if not url:
                    url = _env_port(dirpath)
                if not url:
                    url = _fw_port(dirpath, item[1], fs)
                if not url and item[1] == "dotnet":
                    url = _dotnet_port(dirpath)
                found.append({"name": os.path.basename(dirpath).upper(),
                              "cmd": item[0], "cwd": dirpath,
                              "framework": item[1],
                              "branch": branch,
                              "env_missing": d["missing"] if d else [],
                              "env_open": env_gitignore_open(dirpath),
                              "env_committed": env_committed(dirpath)
                              if has_git else False,
                              "score": score, "root": root,
                              "repo": repo_key, "worktree": worktree,
                              "compose_services": _compose_services(
                                  dirpath, fs) if item[1] == "Docker" else [],
                              "running": running, "url": url})
        if item or "package.json" in fs:
            dirnames[:] = []  # project root — do not descend further
    return sorted(found, key=lambda p: (-p["score"], p["cwd"]))


_TITLE_CACHE = {}  # port -> (title, ts)


def page_title(port):
    """<title> of the first page on 127.0.0.1:port (like pier/Portbook).
    60s cache TTL; '' — non-HTTP or unreachable."""
    ent = _TITLE_CACHE.get(port)
    if ent and time.time() - ent[1] < 60:
        return ent[0]
    title = ""
    try:
        with urllib.request.urlopen(
                f"http://127.0.0.1:{port}/", timeout=1) as r:
            html = r.read(65536)
        m = re.search(rb"<title[^>]*>([^<]{1,140})", html, re.IGNORECASE)
        if m:
            title = m.group(1).decode("utf-8", errors="replace").strip()
    except Exception:
        pass
    _TITLE_CACHE[port] = (title, time.time())
    return title


_FAVICON_CACHE = {}  # port -> (favicon url or "", ts)


def port_favicon(port, host="127.0.0.1"):
    """favicon.ico URL if the port's service serves one, else ''.
    Same 60s per-port cache as page_title; never raises."""
    ent = _FAVICON_CACHE.get(port)
    if ent and time.time() - ent[1] < 60:
        return ent[0]
    url = f"http://{host}:{port}/favicon.ico"
    ok = False
    try:
        with urllib.request.urlopen(url, timeout=0.5) as r:
            ct = r.headers.get("Content-Type", "")
            head = r.read(16)
            # SPA fallback serves 200 text/html — require a real image
            magic = head.startswith((b"\x89PNG", b"GIF8", b"\xff\xd8",
                                     b"\x00\x00\x01\x00", b"RIFF")) \
                or b"<svg" in head.lower()
            ok = 200 <= r.status < 300 \
                and ("image" in ct or "icon" in ct or magic)
    except Exception:
        pass
    _FAVICON_CACHE[port] = (url if ok else "", time.time())
    return url if ok else ""


def next_free_port(start):
    """First free TCP port after start (connect refused = free)."""
    for p in range(start + 1, min(start + 60, 65536)):
        s = socket.socket()
        try:
            if s.connect_ex(("127.0.0.1", p)) != 0:
                return p
        finally:
            s.close()
    return None


_MTIME_SKIP = frozenset((".git", "node_modules", "bin", "obj", "dist",
                        "build", "__pycache__", ".venv", "venv",
                        ".next", ".turbo", "target"))


def latest_mtime(root, max_depth=4, max_files=8000):
    """Newest file mtime under root for watch-restart; 0.0 on error/missing.
    Runs every probe tick — iterative scandir, stat-only, no file reads."""
    newest, seen = 0.0, 0
    stack = [(root, 0)]
    while stack:
        d, depth = stack.pop()
        try:
            entries = os.scandir(d)
        except OSError:
            continue
        with entries:
            for e in entries:
                try:
                    if e.is_dir(follow_symlinks=False):
                        if depth < max_depth and e.name not in _MTIME_SKIP:
                            stack.append((e.path, depth + 1))
                    else:
                        seen += 1
                        if seen > max_files:
                            return newest
                        newest = max(newest, e.stat(
                            follow_symlinks=False).st_mtime)
                except OSError:
                    continue
    return newest


# --- self-update -----------------------------------------------------------

REPO = "dvinerlove/dev-dashboard"
WINGET_ID = "Dvinerlove.DevDashboard"


def update_channel():
    """How this build was installed: dev (source) / winget / scoop / git zip."""
    if not getattr(sys, "frozen", False):
        return "dev"
    exe = os.path.normcase(sys.executable)
    if os.sep + "microsoft" + os.sep + "winget" + os.sep in exe:
        return "winget"
    if os.sep + "scoop" + os.sep in exe:
        return "scoop"
    return "git"


def semver_key(v):
    return tuple(int(x) if x.isdigit() else 0
                 for x in str(v).lstrip("v").split("."))


def fetch_latest_release(timeout=15):
    """Latest GitHub release: {tag, url, zip_url} or None."""
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/releases/latest",
        headers={"User-Agent": "dev-dashboard-updater"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            j = json.loads(r.read().decode())
    except (OSError, ValueError):
        return None
    zip_url = next((a["browser_download_url"]
                    for a in j.get("assets", [])
                    if a.get("name", "").endswith(".zip")), None)
    return {"tag": str(j.get("tag_name", "")).lstrip("v"),
            "url": j.get("html_url", ""), "zip_url": zip_url}


def download_update_zip(zip_url, dest_dir, timeout=180):
    """Download the release zip and extract DevDashboard.exe next to it.
    Returns the extracted exe path."""
    import zipfile
    os.makedirs(dest_dir, exist_ok=True)
    zpath = os.path.join(dest_dir, "update.zip")
    req = urllib.request.Request(
        zip_url, headers={"User-Agent": "dev-dashboard-updater"})
    with urllib.request.urlopen(req, timeout=timeout) as r, \
            open(zpath, "wb") as f:
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)
    with zipfile.ZipFile(zpath) as z:
        z.extract("DevDashboard.exe", dest_dir)
    return os.path.join(dest_dir, "DevDashboard.exe")


def write_update_helper(target_exe, pid, action, ps1_path):
    """Detached helper: wait for the app to die, apply the update, relaunch.
    `action` is either ("copy", src_exe) or ("cmd", shell_command).
    PowerShell, not .bat — cmd's `find`/`timeout` get shadowed by Git/MSYS
    binaries on dev machines and the wait loop silently breaks."""
    if action[0] == "copy":
        do = ("Copy-Item -LiteralPath '{}' -Destination '{}' -Force"
              .format(action[1], target_exe))
    else:
        do = action[1]
    lines = [
        f"while (Get-Process -Id {pid} -ErrorAction SilentlyContinue)"
        " { Start-Sleep 1 }",
        "Start-Sleep 1",
        do,
        # the dying instance's WebView2 children release the user-data
        # folder lock a beat after the host exits — relaunching into the
        # lock window can hang the new instance silently
        "Start-Sleep 4",
        f"Start-Process -FilePath '{target_exe}'",
        "Remove-Item -LiteralPath $MyInvocation.MyCommand.Path -Force"
        " -ErrorAction SilentlyContinue",
    ]
    with open(ps1_path, "w", encoding="utf-8-sig") as f:
        f.write("\r\n".join(lines) + "\r\n")
    return ps1_path
