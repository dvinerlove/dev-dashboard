"""Платформенный слой: Win32 vs POSIX (macOS/Linux).

Всё, что зависит от ОС — здесь; вызывающий код ветвится через функции,
не через if sys.platform разбросанный по файлам.
"""
import os
import subprocess
import sys

IS_WIN = sys.platform == "win32"
IS_MAC = sys.platform == "darwin"
PLATFORM = "windows" if IS_WIN else ("macos" if IS_MAC else "linux")


def shell_argv(cmd):
    """argv для запуска пользовательской команды.
    POSIX — login shell: подхватывает PATH/version-managers профиля
    (тот же приём, что у getlocalhost.app). `/bin/sh -l` не катит:
    на Debian/Ubuntu sh=dash без -l → каждый старт падал бы."""
    if IS_WIN:
        return ["cmd.exe", "/c", cmd]
    sh = os.environ.get("SHELL") or "/bin/sh"
    return [sh, "-lc", cmd] if os.path.basename(sh) in ("bash", "zsh") \
        else [sh, "-c", cmd]


def popen_kwargs():
    """kwargs для subprocess.Popen при старте сервиса.
    POSIX — своя сессия → killpg добивает дерево (аналог Job Objects)."""
    if IS_WIN:
        return {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0)}
    return {"start_new_session": True}


def open_path(path):
    """Открыть папку/файл системным ассоциированным приложением."""
    if IS_WIN:
        os.startfile(path)  # noqa: attr-defined — только на Windows
    else:
        subprocess.Popen(["open" if IS_MAC else "xdg-open", path])


def open_url(url):
    open_path(url)


def system_lang():
    """UI-язык ОС -> 'ru'|'en'. Любая не-ru локаль или ошибка определения
    дают 'en' — английский как дефолт."""
    try:
        if IS_WIN:
            import ctypes
            lid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            return "ru" if (lid & 0x3FF) == 0x19 else "en"
        loc = os.environ.get("LC_ALL") or os.environ.get("LANG") or ""
        return "ru" if loc.lower().startswith("ru") else "en"
    except Exception:
        return "en"


# --- автозагрузка: реестр HKCU\...\Run vs ~/Library/LaunchAgents --------

def _plist_path(label):
    from pathlib import Path
    return Path.home() / "Library" / "LaunchAgents" / f"{label}.plist"


def autorun_entries():
    """[(name, cmd)] — записи автозагрузки текущего пользователя."""
    out = []
    if IS_WIN:
        import winreg
        try:
            with winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Run") as k:
                i = 0
                while True:
                    try:
                        n, v = winreg.EnumValue(k, i)[:2]
                        out.append((str(n), str(v)))
                        i += 1
                    except OSError:
                        break
        except OSError:
            pass
    else:
        import plistlib
        from pathlib import Path
        agents = Path.home() / "Library" / "LaunchAgents"
        try:
            for f in sorted(agents.glob("*.plist")):
                try:
                    pl = plistlib.loads(f.read_bytes())
                    args = pl.get("ProgramArguments") or ([pl["Program"]]
                                                          if pl.get("Program") else [])
                    out.append((pl.get("Label") or f.stem,
                                " ".join(str(a) for a in args)))
                except Exception:
                    out.append((f.stem, ""))
        except OSError:
            pass
    return out


def autorun_disabled_names():
    """Имена записей, выключенных юзером без удаления.
    Windows — StartupApproved; macOS не хранит «disabled но present»
    в user-visible виде → пусто (disable у нас = delete)."""
    if not IS_WIN:
        return set()
    import winreg
    disabled = set()
    try:
        with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Explorer"
                r"\StartupApproved\Run") as k:
            i = 0
            while True:
                try:
                    n, v = winreg.EnumValue(k, i)[:2]
                    if v and v[0] == 3:
                        disabled.add(str(n))
                    i += 1
                except OSError:
                    break
    except OSError:
        pass
    return disabled


def autorun_write(name, cmd):
    """Создать/перезаписать запись автозагрузки."""
    if IS_WIN:
        import winreg
        with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY) as k:
            winreg.SetValueEx(k, name, 0, winreg.REG_SZ, cmd)
        return
    if not IS_MAC:
        raise OSError("autorun is supported on Windows/macOS")
    import plistlib
    p = _plist_path(name)
    p.parent.mkdir(parents=True, exist_ok=True)
    plistlib.dump(
        {"Label": name, "ProgramArguments": shell_argv(cmd),
         "RunAtLoad": True},
        open(p, "wb"))


def autorun_delete(name):
    if IS_WIN:
        import winreg
        with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY) as k:
            winreg.DeleteValue(k, name)
        return
    p = _plist_path(name)
    if p.exists():
        p.unlink()


def autorun_set_enabled(name, enabled):
    """Вкл/выкл без удаления (аналог Диспетчера задач).
    macOS: user-visible disabled-состояния нет — noop."""
    if not IS_WIN:
        return
    import winreg
    with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer"
            r"\StartupApproved\Run",
            0, winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY) as k:
        winreg.SetValueEx(k, name, 0, winreg.REG_BINARY,
                          (b"\x02" if enabled else b"\x03") + b"\x00" * 11)


# --- single instance -----------------------------------------------------

def acquire_single_instance(name="devdashboard"):
    """Хендл блокировки или None если уже занято (второй инстанс).
    Windows — mutex; POSIX — flock на lockfile в tmp."""
    if IS_WIN:
        import ctypes
        ctypes.windll.kernel32.CreateMutexW(None, False, f"{name}Mutex")
        if ctypes.windll.kernel32.GetLastError() == 183:  # ALREADY_EXISTS
            return None
        return True  # хендл держит ОС до выхода процесса
    import fcntl
    import tempfile
    lock = open(os.path.join(tempfile.gettempdir(), f"{name}.lock"), "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        lock.close()
        return None
    return lock  # файл держим открытым — ОС отпустит на выходе
