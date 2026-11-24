"""Чистая логика дашборда без UI: конфиги, пробы процессов/портов,
удалённые хелсчеки, автозапуск (реестр), env-helpers.
Переехало из dashboard.py; Qt не импортируется."""
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
# read-only ресурсы (frontend/dist, icon.ico): в onefile-бандле — _MEIPASS
RESOURCE_DIR = getattr(sys, "_MEIPASS", BASE_DIR)
VERSION = "0.9.0"


def _default_data_dir():
    if pi.IS_WIN:
        return os.path.join(
            os.environ.get("LOCALAPPDATA") or BASE_DIR, "DevDashboard")
    if pi.IS_MAC:
        return os.path.expanduser("~/Library/Application Support/DevDashboard")
    return os.path.join(os.environ.get("XDG_CONFIG_HOME")
                        or os.path.expanduser("~/.config"), "dev-dashboard")


# Writable-данные юзера: рядом с кодом, если конфиг уже есть (portable/dev),
# иначе per-OS data dir; DEVDASH_DATA_DIR — принудительный override
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
    """Атомарная запись конфига: tmp + replace, краш не рвёт файл пополам"""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    os.replace(tmp, path)


def _load_json(path, default):
    """json из файла; при битом файле — откладываем его в .corrupt-* и
    возвращаем дефолт, не затирая оригинал"""
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
    "probe_interval": 4,        # период опроса сервисов, сек
    "dep_timeout": 15,          # ожидание готовности depends_on, сек
    "backoff": [2, 5, 10, 20],  # задержки авторестарта, сек
    "scan_roots": [],           # папки поиска проектов; [] = авто (родитель BASE_DIR)
    "port_mine": [],            # имена процессов, помеченные пользователем «моё»
    "port_hidden": [],          # имена процессов, скрытые из списка портов
    "lang": "auto",             # auto = язык ОС (не-ru и сбой определения → en)
    "api_port": 4850,           # порт локального HTTP API; применяется на старте
}

_LANG = "en"  # кэш load_settings — пробы зовут tr() каждый тик


def resolve_lang(v):
    """'auto' → язык ОС; неизвестные значения → 'en'."""
    if v == "auto":
        return pi.system_lang()
    return v if v in LANGS else "en"


def load_settings():
    """settings.json поверх дефолтов; неизвестные ключи игнорируются"""
    global _LANG
    raw = _load_json(SETTINGS_FILE, {})
    out = dict(DEFAULT_SETTINGS)
    for k in out:
        if k in raw:
            out[k] = raw[k]
    # диск — граница доверия: мусорные числа не должны валить дашборд
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
    _LANG = resolve_lang(out["lang"])
    return out


def save_settings(data):
    """Патч известных ключей -> settings.json; вернуть итоговый dict"""
    global _LANG
    s = load_settings()
    for k in s:
        if k in data:
            s[k] = data[k]
    _save_json(SETTINGS_FILE, s)
    _LANG = resolve_lang(s["lang"])
    return s


# --- Локализация -------------------------------------------------------------
# tr(ключ) — семантические SCREAMING_SNAKE_CASE-ключи -> строка языка (RU/EN).
# tr_detail(s) переводит runtime-текст проб (канонический RU = msgid) через
# EN_DETAIL — это gettext-style msgid: строки генерируются probe-функциями
# как данные, поэтому ключом остаётся сам текст.
LANGS = ("auto", "ru", "en")

RU = {
    "PILL_RUNNING": "работает",
    "PILL_STOPPED": "остановлен",
    "PILL_DEAD": "упал",
    "PILL_FAILED": "цикл падений",
    "STATE_OFF": "выкл",
    "STATE_ON": "вкл",
    "STATE_DOWN": "не отвечает",
    "AR_RUNNING": "работает",
    "AR_NOT_RUNNING": "не работает",
    "AR_PROBLEM": "в автозапуске, но не работает",
    "AUTORESTART": "авторестарт",
    "ENABLED": "включён",
    "DISABLED": "выключен",
    "CAT_DB": "База данных",
    "CAT_DEV": "Dev",
    "CAT_NET": "Сеть",
    "CAT_SYS": "Система",
    "CAT_OTHER": "Прочее",
    "CAT_PRINT": "Печать",
    "CAT_SEARCH": "Поиск",
    "API_PORT_BUSY": "API НЕ поднят: порт {port} занят (старый экземпляр?)",
    "PORT_BUSY_PID": "порт занят pid {pid} ({pname})",
    "ENV_MISSING": "нет {k}",
    "EXITED": "неожиданно завершился",
    "NAME_EXITED": "{name} — неожиданно завершился",
    "NAME_CRASH_LOOP": "{name} — цикл падений",
    "PROC_FOUND": "Обнаружен запущенный процесс PID: {pid}",
    "N_OK": "● {n} в порядке",
    "CRASHES_HALT": "{n} падений за {w}с — авторестарт остановлен",
    "AR_IN": "авторестарт через {d}с",
    "AR_IN_DEAD": "авторестарт через {d}с: сервис упал",
    "ENV_MONITOR_ONLY": "ENV недоступен для сервисов-мониторов.",
    "ENV_NOT_OBJ": "env должен быть объектом.",
    "DEP_CYCLE_VIA": "цикл зависимостей через {dep}",
    "DEP_CYCLE": "цикл зависимостей: {dep}",
    "DEP_STARTING": "стартую зависимость {dep}",
    "DEP_TIMEOUT": "{dep} не готов за {t}с",
    "DEP_FAIL": "зависимость {dep} не поднялась — старт отменён",
    "DEP_FAIL_NAME": "{name}: зависимость {dep} не поднялась",
    "START_FAIL": "не удалось запустить: {err}",
    "START_FAIL_NAME": "Не удалось запустить {name}: {err}",
    "NO_START_CMD": "{name}: команда запуска не задана в конфиге.",
    "NAME_NOT_FOUND": "«{name}» не найден.",
    "PROJ_NOT_FOUND_OR_RUNNING": "не найден или уже запущен",
    "PROCS_NOT_FOUND": "процессы не найдены",
    "STOPPED_PID": "остановлен (PID: {p})",
    "DEP_CYCLE_IN": "цикл в depends_on",
    "PORTS_NOT_NUMBERS": "Порты должны быть числами.",
    "NAME_REQUIRED": "Имя обязательно.",
    "LOG_NOT_CREATED": "Файл лога ещё не создан — сервис не запускался из дашборда.",
    "NO_ENV_CONF": "У сервиса не заданы env_key/env_file.",
    "EMPTY_VALUE": "Пустое значение не записано.",
    "WRITE_FAIL": "Не удалось записать в {path}: {e}",
    "KEY_WRITTEN": "{key} записан в {path}",
    "PROC_STOPPED": "Процесс PID {pid} остановлен.",
    "ADDED_N": "Добавлено: {n}",
    "TOGGLE_FAIL": "Не удалось переключить «{name}»: {e}",
    "AR_STATE": "«{name}» {s} в автозапуске",
    "NAME_CMD_REQUIRED": "Имя и команда обязательны.",
    "AR_SAVE_FAIL": "Не удалось записать «{name}»: {e}",
    "AR_SAVED": "«{name}» записан в автозапуск",
    "AR_DEL_FAIL": "Не удалось удалить «{name}»: {e}",
    "AR_REMOVED": "«{name}» убран из автозапуска",
    "PROJ_DIR_MISSING": "Папка проекта не существует: {cwd}",
    "NOTHING_TO_OPEN": "Нечего открыть.",
    "PROJ_FOLDER": "Папка проекта",
    "BAD_PID": "Некорректный pid.",
    "CANT_KILL_SELF": "Нельзя убить сам дашборд.",
    "PROTECTED_PROC": "Защищённый процесс (система/база) — убить его можно только вручную.",
    "PID_STOPPED": "PID {pid} остановлен.",
    "PID_STOP_FAIL": "PID {pid}: нет процесса или недостаточно прав.",
    "BAD_PORT": "Порт — число от 1 до 65535.",
    "PORT_PROTECTED": "На :{port} защищённый процесс (система/база) — убивать вручную.",
    "PORT_FREED": "Порт :{port} освобождён.",
    "PORT_FREED_PIDS": "Порт :{port} освобождён (pid {pids})",
    "PORT_NO_LISTENERS": "На порту :{port} нет слушающих процессов или недостаточно прав.",
    "BAD_SETTINGS": "Некорректные значения настроек",
    "TRAY_OPEN": "Открыть",
    "TRAY_QUIT": "Выход",
    "LOG_RUN_MARKER": "запуск: {cmd}",
    "LOG_STARTED": "запущен: {cmd}",
    "PICK_DIR_FAIL": "Диалог выбора папки недоступен: {e}",
}

EN = {
    "PILL_RUNNING": "running",
    "PILL_STOPPED": "stopped",
    "PILL_DEAD": "dead",
    "PILL_FAILED": "crash loop",
    "STATE_OFF": "off",
    "STATE_ON": "on",
    "STATE_DOWN": "not responding",
    "AR_RUNNING": "running",
    "AR_NOT_RUNNING": "not running",
    "AR_PROBLEM": "in autorun but not running",
    "AUTORESTART": "autorestart",
    "ENABLED": "enabled",
    "DISABLED": "disabled",
    "CAT_DB": "Database",
    "CAT_DEV": "Dev",
    "CAT_NET": "Network",
    "CAT_SYS": "System",
    "CAT_OTHER": "Other",
    "CAT_PRINT": "Printing",
    "CAT_SEARCH": "Search",
    "API_PORT_BUSY": "API failed: port {port} busy (old instance?)",
    "PORT_BUSY_PID": "port busy, pid {pid} ({pname})",
    "ENV_MISSING": "missing {k}",
    "EXITED": "exited unexpectedly",
    "NAME_EXITED": "{name} — exited unexpectedly",
    "NAME_CRASH_LOOP": "{name} — crash loop",
    "PROC_FOUND": "Detected running process PID: {pid}",
    "N_OK": "● {n} OK",
    "CRASHES_HALT": "{n} crashes in {w}s — autorestart stopped",
    "AR_IN": "autorestart in {d}s",
    "AR_IN_DEAD": "autorestart in {d}s: service died",
    "ENV_MONITOR_ONLY": "ENV is unavailable for monitor services.",
    "ENV_NOT_OBJ": "env must be an object.",
    "DEP_CYCLE_VIA": "dependency cycle via {dep}",
    "DEP_CYCLE": "dependency cycle: {dep}",
    "DEP_STARTING": "starting dependency {dep}",
    "DEP_TIMEOUT": "{dep} not ready in {t}s",
    "DEP_FAIL": "dependency {dep} did not come up — start cancelled",
    "DEP_FAIL_NAME": "{name}: dependency {dep} did not come up",
    "START_FAIL": "failed to start: {err}",
    "START_FAIL_NAME": "Failed to start {name}: {err}",
    "NO_START_CMD": "{name}: no start command in config.",
    "NAME_NOT_FOUND": "“{name}” not found.",
    "PROJ_NOT_FOUND_OR_RUNNING": "not found or already running",
    "PROCS_NOT_FOUND": "processes not found",
    "STOPPED_PID": "stopped (PID: {p})",
    "DEP_CYCLE_IN": "cycle in depends_on",
    "PORTS_NOT_NUMBERS": "Ports must be numbers.",
    "NAME_REQUIRED": "Name is required.",
    "LOG_NOT_CREATED": "Log file not created yet — service was never started by the dashboard.",
    "NO_ENV_CONF": "Service has no env_key/env_file configured.",
    "EMPTY_VALUE": "Empty value was not written.",
    "WRITE_FAIL": "Failed to write {path}: {e}",
    "KEY_WRITTEN": "{key} written to {path}",
    "PROC_STOPPED": "PID {pid} stopped.",
    "ADDED_N": "Added: {n}",
    "TOGGLE_FAIL": "Failed to toggle “{name}”: {e}",
    "AR_STATE": "“{name}” {s} in autorun",
    "NAME_CMD_REQUIRED": "Name and command are required.",
    "AR_SAVE_FAIL": "Failed to save “{name}”: {e}",
    "AR_SAVED": "“{name}” saved to autorun",
    "AR_DEL_FAIL": "Failed to delete “{name}”: {e}",
    "AR_REMOVED": "“{name}” removed from autorun",
    "PROJ_DIR_MISSING": "Project folder missing: {cwd}",
    "NOTHING_TO_OPEN": "Nothing to open.",
    "PROJ_FOLDER": "Project folder",
    "BAD_PID": "Bad pid.",
    "CANT_KILL_SELF": "Can't kill the dashboard itself.",
    "PROTECTED_PROC": "Protected process (system/db) — kill it manually.",
    "PID_STOPPED": "PID {pid} stopped.",
    "PID_STOP_FAIL": "PID {pid}: no such process or access denied.",
    "BAD_PORT": "Port must be a number 1–65535.",
    "PORT_PROTECTED": "Port :{port} is held by a protected process (system/db) — kill it manually.",
    "PORT_FREED": "Port :{port} freed.",
    "PORT_FREED_PIDS": "Port :{port} freed (pid {pids})",
    "PORT_NO_LISTENERS": "No listeners on :{port} or access denied.",
    "BAD_SETTINGS": "Invalid settings values",
    "TRAY_OPEN": "Open",
    "TRAY_QUIT": "Quit",
    "LOG_RUN_MARKER": "launch: {cmd}",
    "LOG_STARTED": "started: {cmd}",
    "PICK_DIR_FAIL": "Folder picker unavailable: {e}",
}

# canonical EN-текст probe-деталей -> RU (см. tr_detail). Русский текст
# живёт только в словарях — канонический формат внутренних строк — EN.
RU_DETAIL = {
    "service stopped": "сервис остановлен",
    "offline": "офлайн",
    "online": "в сети",
    "API unreachable": "API недоступен",
    "port closed": "порт закрыт",
    "not running": "не работает",
    "unreachable": "недоступен",
    "no cli": "cli нет",
    "engine down": "engine выкл",
    "container not found": "контейнер не найден",
    "bad spec": "spec некорректен",
    "stopped": "остановлен",
    "timeout": "таймаут",
    "circuit_open": "авторестарт остановлен",
    "no start command in service config.":
        "Команда запуска не задана в конфиге сервиса.",
}

# шаблонные RU-формы динамических detail и единицы времени (см. tr_detail)
RU_TPL_BUSY_PORT = ":{p} занят · чужой процесс pid {pid}"
RU_TPL_MISSING = "{code} · нет '{kw}'"
RU_TPL_UPTIME = "{h}ч{m}м"
RU_UNIT_MIN, RU_UNIT_DAY = "м", "д"


def lang():
    return _LANG


def tr(key, **kw):
    """Семантический ключ -> строка текущего языка (+{placeholders}).
    Промахнутый ключ отдаётся как есть — видно в UI сразу."""
    s = (EN if _LANG == "en" else RU).get(key, key)
    return s.format(**kw) if kw else s


def tr_detail(s):
    """detail пробы/metrics/issue-text -> текущий язык. Канонический вид —
    EN-строки проб (в коде нет русского); для ru шаблонные формы разбираются
    regex'ами, прочее — через RU_DETAIL; en проходит как есть."""
    if _LANG != "ru" or not s:
        return s
    m = re.fullmatch(r":(\d+) busy · foreign process pid (\d+)", s)
    if m:
        return RU_TPL_BUSY_PORT.format(p=m.group(1), pid=m.group(2))
    m = re.fullmatch(r"(\d+) · missing '(.*)'", s)
    if m:
        return RU_TPL_MISSING.format(code=m.group(1), kw=m.group(2))
    s = RU_DETAIL.get(s, s)
    s = re.sub(r"(\d+)h(\d+)m\b",
               lambda g: RU_TPL_UPTIME.format(h=g.group(1), m=g.group(2)),
               s)                                  # аптайм 7h12m -> 7ч12м
    # граница по началу числа: "0x3d"/IPv6 "::1d"/"item3m" не трогаем
    s = re.sub(r"(?<![\w.:])(\d+)m\b", r"\1" + RU_UNIT_MIN, s)  # 5m -> 5м
    s = re.sub(r"(?<![\w.:])(\d+)d\b", r"\1" + RU_UNIT_DAY, s)  # cert 3d -> 3д
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
    """Завершает процесс и все его дочерние процессы"""
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
    """Завершает процессы, СЛУШАЮЩИЕ указанный порт (только LISTEN —
    иначе убьём процесс с обычным исходящим соединением с этого порта)"""
    killed_pids = []
    for conn in psutil.net_connections(kind='inet'):
        if conn.status == "LISTEN" and conn.laddr and conn.laddr.port == port:
            pid = conn.pid
            # свой PID исключаем — :4850 это наш API
            if pid and pid != os.getpid() and pid not in killed_pids:
                if kill_proc_tree(pid):
                    killed_pids.append(pid)
    return killed_pids


def pids_on_port(port):
    """pid'ы процессов, слушающих порт (для диалога подтверждения)"""
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
    """pid жив; ctime — create_time на момент присвоения pid, без него
    после ребута чужой процесс может попасть на тот же pid."""
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
          "sh", "bash", "zsh", "fish", "ssh", "npx"}  # POSIX-имена без .exe


def find_project_pid(project):
    """pid процесса проекта: exe или путь в cmdline внутри папки проекта (кроме шеллов/агентов)"""
    if not project.get("cwd"):
        return None  # '' → normpath('.') матчится почти на всё
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
    """Слушающие порты дерева процессов (для авто-URL)"""
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
    """'pid N · 3% · 45MB' — метрики процесса с деревом для проектов"""
    try:
        p = cpu_cache.setdefault(pid, psutil.Process(pid))
        cpu = p.cpu_percent()
        mem = p.memory_info().rss + sum(
            c.memory_info().rss for c in p.children(recursive=True))
        return f"pid {pid:>6} · {cpu:>3.0f}% · {mem // 1048576:>4}MB"
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return f"pid {pid}"


# --- Сервисы и автозапуск -------------------------------------------------

# vendor-проба ZeroTier: путь к authtoken по умолчанию; spec["zt_token"] — override
ZT_AUTHTOKEN = r"C:\ProgramData\ZeroTier\One\authtoken.secret"

DEFAULT_SERVICES = []


def load_services():
    """Сервисы из services_config.json; если файла нет — пишем дефолт"""
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
    """Граница доверия: битая ручная правка конфига не должна ронять дашборд.
    None → пропуск записи"""
    if not isinstance(s, dict) or not isinstance(s.get("name"), str) \
            or not s["name"].strip():
        return None
    if not isinstance(s.get("sub"), str):
        s["sub"] = str(s.get("sub") or "")
    if "ports" in s:  # строки/числа/мусор → int-лист, битые элементы пропускаем
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
    return s


def save_services(services):
    _save_json(SERVICES_FILE, services)


def _port_open(port, host="127.0.0.1", timeout=0.3):
    try:
        with socket.create_connection((host, port), timeout):
            return True
    except OSError:
        return False


def _service_log_path(spec):
    """logs/<имя>.log — безопасное имя файла"""
    name = re.sub(r'[\\/:*?"<>|]', "_", spec["name"])
    return os.path.join(LOGS_DIR, name + ".log")


def _proc_snapshot():
    """(procs, {порт: pid}, {порт: ip} lan-exposed слушателей);
    proc оставлен для ленивого cwd()"""
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
                # 0.0.0.0/:: или конкретный LAN-IP — слушает не только localhost
                if (c.laddr.ip or "") not in ("127.0.0.1", "::1", "localhost",
                                              "::ffff:127.0.0.1"):
                    lan[c.laddr.port] = c.laddr.ip
    except (psutil.AccessDenied, OSError):
        pass
    return out, listeners, lan


# Классификация чужих слушателей портов.
# shortcut: прикидочная база по имени процесса + типовым портам (IANA-полную
# не тянем); расширять по мере жалоб «не опознал».
CATS = {"db": "CAT_DB", "dev": "CAT_DEV", "net": "CAT_NET",
        "sys": "CAT_SYS", "other": "CAT_OTHER"}

PROC_CATS = {  # имя процесса -> (категория, подпись)
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
    "nginx.exe": ("net", "nginx"), "httpd.exe": ("net", "Apache"),
    "caddy.exe": ("net", "Caddy"), "traefik.exe": ("net", "Traefik"),
    "svchost.exe": ("sys", "Windows"), "system": ("sys", "Windows"),
    "services.exe": ("sys", "Windows"), "lsass.exe": ("sys", "Windows"),
    "spoolsv.exe": ("sys", "CAT_PRINT"), "dashost.exe": ("sys", "Windows"),
    "dllhost.exe": ("sys", "Windows"), "searchindexer.exe": ("sys", "CAT_SEARCH"),
}

WELL_KNOWN = {  # порт -> категория, когда процесс не опознан
    1433: "db", 1521: "db", 3306: "db", 5432: "db", 5433: "db",
    6379: "db", 27017: "db", 9200: "db", 11211: "db",
    5672: "db", 15672: "db",
    3000: "dev", 3001: "dev", 4200: "dev", 5173: "dev", 5174: "dev",
    8000: "dev", 8080: "dev", 8081: "dev", 8888: "dev", 9229: "dev",
    80: "net", 443: "net", 53: "net",
}


def port_class(proc_name, port):
    """(категория, подпись) слушателя: сначала по имени процесса, потом по порту.
    POSIX-имена не имеют .exe → пробуем и с суффиксом."""
    n = (proc_name or "").lower()
    c = PROC_CATS.get(n) or PROC_CATS.get(n + ".exe") \
        or PROC_CATS.get(n.rstrip("0123456789") + ".exe")  # python3 → python
    if c:
        return c
    cat = WELL_KNOWN.get(port)
    return (cat, CATS[cat]) if cat else ("other", CATS["other"])


def _proc_stats(matched, cpu_cache=None):
    """' · 3% · 45MB · 1ч 30м' по первому совпавшему процессу; '' если недоступен.
    cpu_cache: {pid: Process} — иначе cpu_percent() каждый раз на новом объекте = 0"""
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
        # фиксированная ширина полей — колонки метрик выравниваются по строкам
        return f" · {cpu:>3.0f}% · {mb:>4}MB · {up:>6}"
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return ""


def _probe_zerotier(procs, spec=None):
    if not any(p["name"] == "zerotier-one_x64.exe" for p in procs):
        return "down", "service stopped"
    try:  # локальный API ZeroTier вместо subprocess zerotier-cli
        hdr = {"X-ZT1-Auth": open(
            (spec or {}).get("zt_token") or ZT_AUTHTOKEN,
            encoding="utf-8").read().strip()}
        get = lambda path: json.load(urllib.request.urlopen(
            urllib.request.Request("http://127.0.0.1:9993" + path, headers=hdr),
            timeout=1))
        if not get("/status").get("online"):
            return "dead", "offline"
        ips = [a.split("/")[0] for n in get("/network")
               for a in n.get("assignedAddresses", [])]
        return "up", " ".join(ips) if ips else "online"
    except Exception:
        return "dead", "API unreachable"


def _probe_service(spec, procs, listeners, cpu_cache=None):
    """(state, detail): up=зелёный, down=серый, dead=красный, off=штатно выкл"""
    if spec.get("zerotier"):
        return _probe_zerotier(procs, spec)
    matched = [p for p in procs
               if (spec.get("proc") and p["name"] == spec["proc"])
               or (spec.get("match") and spec["match"].lower() in p["cl"])]
    pids = [p["pid"] for p in matched]
    ports = spec.get("ports", ())
    if ports:
        pt = next((pt for pt in ports if _port_open(pt)), None)
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


# --- Удалённые мониторы (spec type: http|tcp|docker) ------------------------

def _remote_interval(spec):
    """Период пробы в секундах: interval из spec, иначе docker=15, supabase=60, прочие=30"""
    try:
        v = int(spec.get("interval") or 0)
        if v > 0:
            return v
    except (TypeError, ValueError):
        pass
    if spec.get("supabase"):
        return 60
    return {"docker": 15}.get(spec.get("type"), 30)


def _cert_days(url):
    """Дней до конца TLS-сертификата хоста; None если не https или ошибка"""
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
    """(state, detail) для удалённого spec; те же коды состояний, что у локальных"""
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
    # http (+ supabase = http с токеном из .env)
    req = urllib.request.Request(spec["url"])
    if spec.get("env_key"):
        tok = _env_get(spec.get("env_file") or os.path.join(DATA_DIR, ".env"),
                       spec["env_key"])
        if tok:
            req.add_header("Authorization", f"Bearer {tok}")
            if spec.get("supabase"):
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
    """Записи автозагрузки -> [(имя, команда)]: реестр Run / LaunchAgents."""
    return pi.autorun_entries()


def _autorun_disabled():
    """Имена записей, выключенных юзером без удаления (StartupApproved)."""
    return pi.autorun_disabled_names()


def _autorun_set_enabled(name, enabled):
    """Вкл/выкл запись автозагрузки без удаления (как Диспетчер задач)"""
    pi.autorun_set_enabled(name, enabled)


def _env_get(path, key):
    """Значение ключа из .env; '' при отсутствии."""
    return _env_kv(path).get(key, "")


def _env_set(path, key, value):
    """Пишет KEY=value в .env: заменяет строку или дописывает в конец"""
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


def _autorun_is_mine(name, cmd, project_dirs, mine_tokens=()):
    """Свои = команда/имя матчит cwd проекта, папку сервиса или
    имя/stem start-файла из спека сервисов."""
    s = (name + " " + cmd).lower().replace("/", "\\")
    return any(d in s for d in project_dirs) \
        or any(t and t in s for t in mine_tokens)


def _autorun_target(cmd):
    """Путь-жертва команды: кавычки, путь с диска до расширения, иначе None"""
    if not pi.IS_WIN:
        for t in cmd.split():  # plist-команда: первый абсолютный путь
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
    return t if ("\\" in t or "." in t) else None  # голое 'pythonw' — не путь


def _autorun_running(cmd, procs):
    """Запущена ли команда из автозагрузки: по exe, по имени скрипта/папке в cmdline,
    а для .cmd-обёрток (родитель уже умер) — по cwd процесса в папке лаунчера"""
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
    """Popen команды запуска сервиса с записью в logs/<name>.log.
    job (process_tree.Job) — если передан, процесс стартует suspended и
    назначается в Job до пробуждения (без гонки дочерних процессов).
    Возвращает (ok, err_str|None, Popen|None) — proc это shell-обёртка,
    живёт пока живо дерево сервиса (probe-фолбэк для spec без proc/match)."""
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
    env.update({k: str(v) for k, v in (spec.get("env") or {}).items()})
    proc = None
    try:
        pk = pi.popen_kwargs()
        if job and pi.IS_WIN:
            pk["creationflags"] = pk.get("creationflags", 0) | 0x00000004
            # CREATE_SUSPENDED: назначить в Job до пробуждения, без гонки

        def spawn(args):
            nonlocal job, proc
            p = subprocess.Popen(
                args, cwd=cwd, env=env, stdout=log,
                stderr=subprocess.STDOUT, **pk)
            if job:
                try:
                    ok = job.assign(p)
                finally:
                    if pi.IS_WIN:  # старт был suspended — разбудить
                        try:
                            psutil.Process(p.pid).resume()
                        except psutil.Error:
                            pass
                if not ok:  # отказ (чужой Job): хендл закрыть, без него живём
                    job.disarm()
                    job.close()
                    job = None
            proc = p
            return p

        try:
            if pi.IS_WIN and not cmd.lower().endswith((".cmd", ".bat")):
                spawn(cmd)
            else:
                # POSIX: строку команды всегда через login shell —
                # PATH/version-managers, args и shebang разрешает sh
                spawn(pi.shell_argv(cmd))
        except FileNotFoundError:
            # голый 'pythonw' и т.п. — пусть shell разрешит PATH/PATHEXT
            spawn(pi.shell_argv(cmd))
    except OSError as e:
        return False, str(e), None
    finally:
        if log is not subprocess.DEVNULL:
            log.close()
    log_append(f"[{spec['name']}] " + tr("LOG_STARTED", cmd=cmd))
    return True, None, proc


def scan_roots():
    """Папки поиска проектов из настроек; пусто — домашняя (frozen) или
    родитель BASE_DIR (запуск из исходников — проекты обычно рядом)."""
    roots = load_settings()["scan_roots"] or (
        [os.path.expanduser("~")] if getattr(sys, "frozen", False)
        else [os.path.dirname(BASE_DIR)])
    return [os.path.normpath(r) for r in roots]


_EXAMPLE_NAMES = (".env.example", ".env.sample", ".env.template",
                  ".env.dist", ".env.defaults")


def _env_kv(path):
    """KEY -> value из .env; {} при отсутствии/ошибке."""
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
    """Diff .env vs .env.example: missing — нет в .env (error),
    extra — недокументированные в example (warn), empty — пустые
    значения в .env (warn). Паттерн envaudit/dotenv-checker.
    None — example-файла нет, сравнивать не с чем."""
    env = _env_kv(os.path.join(directory, ".env"))
    for name in _EXAMPLE_NAMES:
        want = set(_env_kv(os.path.join(directory, name)))
        if want:
            return {"missing": sorted(want - set(env)),
                    "extra": sorted(set(env) - want),
                    "empty": sorted(k for k, v in env.items() if not v)}
    return None


def git_branch(directory):
    """Ветка из .git/HEAD без subprocess (pier/Portlivo фича).
    '' — не репо; короткий sha при detached HEAD.
    Worktree: .git — файл «gitdir: <путь>», HEAD лежит там."""
    git = os.path.join(directory, ".git")
    try:
        if os.path.isfile(git):
            ptr = open(git, encoding="utf-8").read().strip()
            if ptr.startswith("gitdir:"):
                git = ptr[7:].strip()
                if not os.path.isabs(git):
                    git = os.path.normpath(os.path.join(directory, git))
            else:
                return ""
        head = open(os.path.join(git, "HEAD"),
                    encoding="utf-8").read().strip()
    except OSError:
        return ""
    if head.startswith("ref: refs/heads/"):
        return head[16:]
    return head[:7] if head else ""


def env_gitignore_open(directory):
    """True, если .env существует и .gitignore его не покрывает —
    секреты уедут в коммит (dotenv-sentinel фича).
    ponytail: матчим базовые паттерны, не полный gitignore-DSL —
    экзотику вида `dir/**/.env` не считаем покрытием."""
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
            continue  # комментарий, негация `!.env`, dir-only паттерн — не покрытие
        if p.lstrip("/") in (".env", "*.env", ".env*", "*", "**/.env",
                             "**/*.env"):
            return False
    return True


# мета-фреймворки раньше базовых библиотек (next > react, nuxt > vue)
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
    """Django/Flask/FastAPI по pyproject.toml + requirements*.txt."""
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
    """Лейбл фреймворка папки проекта (для уже добавленных проектов,
    добавленных до скана или вручную). '' — не опознано."""
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


def scan_project_dirs(root, known_cwds):
    """Папки-проекты вне known_cwds. Приоритет манифестов — по таблице
    Portlivo: Procfile > composer > package.json > bin/dev > manage.py >
    artisan > go.mod > Cargo.toml > pyproject/requirements + entry >
    compose.
    -> [{name, cmd, cwd, framework, branch, env_missing, env_extra,
         env_empty, env_open}]"""
    SKIP = ("node_modules", ".git", "dist", "build", "__pycache__",
            ".venv", "venv", "target", "vendor", ".next", ".nuxt")
    COMPOSE = {"docker-compose.yml", "docker-compose.yaml",
               "compose.yml", "compose.yaml"}
    SKIP += (".svn", ".hg", ".idea", ".vs", ".cache")
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP]
        # глубина до 4 уровней — junction-циклы и гигантские деревья не вешают скан
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
            cmd = "npm run dev" if "dev" in scripts else \
                ("npm start" if "start" in scripts else "")
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
                item = (f"python {entry}", _py_framework(dirpath))
        elif COMPOSE & fs:
            item = ("docker compose up", "Docker")
        if item and os.path.normcase(os.path.normpath(dirpath)) \
                not in known_cwds:
            d = env_diff(dirpath)
            found.append({"name": os.path.basename(dirpath).upper(),
                          "cmd": item[0], "cwd": dirpath, "pid": None,
                          "framework": item[1],
                          "branch": git_branch(dirpath),
                          "env_missing": d["missing"] if d else [],
                          "env_open": env_gitignore_open(dirpath)})
        if item or "package.json" in fs:
            dirnames[:] = []  # корень проекта — внутрь не лезем
    return sorted(found, key=lambda p: p["cwd"])


_TITLE_CACHE = {}  # порт -> (title, ts)


def page_title(port):
    """<title> первой страницы на 127.0.0.1:port (как у pier/Portbook).
    Кэш TTL 60с; '' — не-HTTP или недоступно."""
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


def next_free_port(start):
    """Первый свободный TCP-порт после start (connect refused = свободен)."""
    for p in range(start + 1, min(start + 60, 65536)):
        s = socket.socket()
        try:
            if s.connect_ex(("127.0.0.1", p)) != 0:
                return p
        finally:
            s.close()
    return None
