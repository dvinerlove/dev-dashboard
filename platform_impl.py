"""Platform layer: Win32 vs POSIX (macOS/Linux).

Everything OS-dependent lives here; callers branch through functions,
not via if sys.platform scattered across files.
"""
import os
import subprocess
import sys

IS_WIN = sys.platform == "win32"
IS_MAC = sys.platform == "darwin"
PLATFORM = "windows" if IS_WIN else ("macos" if IS_MAC else "linux")


def shell_argv(cmd):
    """argv for launching a user command.
    POSIX — login shell: picks up PATH/version-managers from the profile
    (same trick as getlocalhost.app). `/bin/sh -l` does not work:
    on Debian/Ubuntu sh=dash without -l → every start would fail."""
    if IS_WIN:
        return ["cmd.exe", "/c", cmd]
    sh = os.environ.get("SHELL") or "/bin/sh"
    return [sh, "-lc", cmd] if os.path.basename(sh) in ("bash", "zsh") \
        else [sh, "-c", cmd]


def popen_kwargs():
    """kwargs for subprocess.Popen when starting a service.
    POSIX — own session → killpg finishes the tree (Job Objects analog)."""
    if IS_WIN:
        return {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0)}
    return {"start_new_session": True}


def open_path(path):
    """Open a folder/file with the system-associated application."""
    if IS_WIN:
        os.startfile(path)  # noqa: attr-defined — Windows only
    else:
        subprocess.Popen(["open" if IS_MAC else "xdg-open", path])


def open_url(url):
    open_path(url)


def system_lang():
    """OS UI language -> 'ru'|'en'. Any non-ru locale or a detection
    failure yields 'en' — English as the default."""
    try:
        if IS_WIN:
            import ctypes
            lid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            return "ru" if (lid & 0x3FF) == 0x19 else "en"
        loc = os.environ.get("LC_ALL") or os.environ.get("LANG") or ""
        return "ru" if loc.lower().startswith("ru") else "en"
    except Exception:
        return "en"


# --- autostart: HKCU\...\Run registry vs ~/Library/LaunchAgents --------

def _plist_path(label):
    from pathlib import Path
    return Path.home() / "Library" / "LaunchAgents" / f"{label}.plist"


def autorun_entries():
    """[(name, cmd)] — autostart entries of the current user."""
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
    """Names of entries the user disabled without deleting.
    Windows — StartupApproved; macOS does not keep "disabled but present"
    in a user-visible form → empty (disable for us = delete)."""
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
    """Create/overwrite an autostart entry."""
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
    """Enable/disable without deleting (Task Manager style).
    macOS: no user-visible disabled state — noop."""
    if not IS_WIN:
        return
    import winreg
    with winreg.CreateKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer"
            r"\StartupApproved\Run") as k:
        winreg.SetValueEx(k, name, 0, winreg.REG_BINARY,
                          (b"\x02" if enabled else b"\x03") + b"\x00" * 11)


# --- single instance -----------------------------------------------------

def acquire_single_instance(name="devdashboard"):
    """Lock handle or None if already held (second instance).
    Windows — mutex; POSIX — flock on a lockfile in tmp."""
    if IS_WIN:
        import ctypes
        ctypes.windll.kernel32.CreateMutexW(None, False, f"{name}Mutex")
        if ctypes.windll.kernel32.GetLastError() == 183:  # ALREADY_EXISTS
            return None
        return True  # the OS holds the handle until process exit
    import fcntl
    import tempfile
    lock = open(os.path.join(tempfile.gettempdir(), f"{name}.lock"), "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        lock.close()
        return None
    return lock  # keep the file open — the OS releases it on exit


# --- OS credential store: Windows Credential Manager via advapi32 --------
# Secrets live outside the configs; spec.env keeps only "cred:<target>".
# POSIX: no stdlib keystore — read returns None, writes raise OSError.

if IS_WIN:
    import ctypes
    from ctypes import wintypes

    _CRED_TYPE_GENERIC = 1
    _CRED_PERSIST_LOCAL_MACHINE = 2

    class _CREDENTIAL(ctypes.Structure):
        _fields_ = [("Flags", wintypes.DWORD),
                    ("Type", wintypes.DWORD),
                    ("TargetName", wintypes.LPWSTR),
                    ("Comment", wintypes.LPWSTR),
                    ("LastWritten", wintypes.FILETIME),
                    ("CredentialBlobSize", wintypes.DWORD),
                    ("CredentialBlob", ctypes.c_void_p),
                    ("Persist", wintypes.DWORD),
                    ("AttributeCount", wintypes.DWORD),
                    ("Attributes", ctypes.c_void_p),
                    ("TargetAlias", wintypes.LPWSTR),
                    ("UserName", wintypes.LPWSTR)]

    _advapi = ctypes.windll.advapi32
    _advapi.CredReadW.argtypes = [
        wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
        ctypes.POINTER(ctypes.POINTER(_CREDENTIAL))]
    _advapi.CredReadW.restype = wintypes.BOOL
    _advapi.CredWriteW.argtypes = [ctypes.POINTER(_CREDENTIAL),
                                   wintypes.DWORD]
    _advapi.CredWriteW.restype = wintypes.BOOL
    _advapi.CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD,
                                    wintypes.DWORD]
    _advapi.CredDeleteW.restype = wintypes.BOOL
    _advapi.CredFree.argtypes = [ctypes.c_void_p]
    _advapi.CredFree.restype = None


def cred_read(target):
    """Secret text for `target` (e.g. "DevDashboard/svc/KEY") or None —
    also None on POSIX, where no stdlib keystore exists."""
    if not IS_WIN:
        return None
    p = ctypes.POINTER(_CREDENTIAL)()
    if not _advapi.CredReadW(str(target), _CRED_TYPE_GENERIC, 0,
                             ctypes.byref(p)):
        return None
    try:
        size = p.contents.CredentialBlobSize
        blob = ctypes.string_at(p.contents.CredentialBlob, size) \
            if size else b""
        # errors=replace: a foreign cred target with a non-UTF16 blob
        # must not crash env resolution
        return blob.decode("utf-16-le", errors="replace")
    finally:
        _advapi.CredFree(p)


def cred_write(target, secret):
    """Write/update a generic credential -> True/False. POSIX: OSError."""
    if not IS_WIN:
        raise OSError("credential store is supported on Windows only")
    blob = str(secret).encode("utf-16-le")
    buf = ctypes.create_string_buffer(blob, len(blob))
    cred = _CREDENTIAL(Type=_CRED_TYPE_GENERIC, TargetName=str(target),
                       LastWritten=wintypes.FILETIME(0, 0),
                       CredentialBlobSize=len(blob),
                       CredentialBlob=ctypes.addressof(buf),
                       Persist=_CRED_PERSIST_LOCAL_MACHINE)
    return bool(_advapi.CredWriteW(ctypes.byref(cred), 0))


def cred_delete(target):
    """Delete a generic credential -> True/False. POSIX: OSError."""
    if not IS_WIN:
        raise OSError("credential store is supported on Windows only")
    return bool(_advapi.CredDeleteW(str(target), _CRED_TYPE_GENERIC, 0))
