"""Убийство дерева процессов: Windows Job Objects / POSIX process groups.

Windows — Job с KILL_ON_JOB_CLOSE: пока дашборд держит хендл открытым, можно
TerminateJobObject() (мгновенное убийство всего дерева). При аварийном
закрытии процесса дашборда хендлы падают — деревья тоже умирают (нет
сирот). При штатном выходе перед close() зовём disarm(), иначе сервисы
погибнут вместе с дашбордом.

POSIX — start_new_session + killpg(SIGKILL): порождённый процесс — лидер
группы, дети наследуют pgid. disarm() — no-op: на POSIX дети и так
переживают родителя.
shortcut: на POSIX при аварийном падении дашборда дерево НЕ умирает —
на macOS нет ядерного аналога KILL_ON_JOB_CLOSE (на Linux был бы cgroup).
Сироты добираются на следующем старте через pids_on_port/kill_proc_tree.
"""
import subprocess
import sys

import platform_impl as pi

if pi.IS_WIN:
    import ctypes
    import ctypes.wintypes as wt

    import psutil

    _k32 = ctypes.windll.kernel32
    _k32.CreateJobObjectW.restype = wt.HANDLE
    _k32.CreateJobObjectW.argtypes = (wt.LPVOID, wt.LPCWSTR)
    _k32.SetInformationJobObject.argtypes = (wt.HANDLE, ctypes.c_int,
                                             wt.LPVOID, wt.DWORD)
    _k32.SetInformationJobObject.restype = wt.BOOL
    _k32.AssignProcessToJobObject.argtypes = (wt.HANDLE, wt.HANDLE)
    _k32.AssignProcessToJobObject.restype = wt.BOOL
    _k32.TerminateJobObject.argtypes = (wt.HANDLE, wt.UINT)
    _k32.TerminateJobObject.restype = wt.BOOL
    _k32.CloseHandle.argtypes = (wt.HANDLE,)
    _k32.CloseHandle.restype = wt.BOOL

    JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000
    _JobObjectExtendedLimitInformation = 9
    CREATE_SUSPENDED = 0x00000004  # winbase.h; в subprocess константы нет


    class _BasicLimit(ctypes.Structure):
        # LARGE_INTEGER = int64; SIZE_T/ULONG_PTR — machine-word (ctypes сам
        # выровняет под 8 байт на x64 и 4 на x86).
        _fields_ = [
            ("PerProcessUserTimeLimit", ctypes.c_int64),
            ("PerJobUserTimeLimit", ctypes.c_int64),
            ("LimitFlags", wt.DWORD),
            ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t),
            ("ActiveProcessLimit", wt.DWORD),
            ("Affinity", ctypes.c_size_t),
            ("PriorityClass", wt.DWORD),
            ("SchedulingClass", wt.DWORD),
        ]


    class _IOCounters(ctypes.Structure):
        _fields_ = [(n, ctypes.c_uint64) for n in (
            "ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
            "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]


    class _ExtLimit(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", _BasicLimit),
            ("IoInfo", _IOCounters),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]


    def _set_limit(h, flags):
        info = _ExtLimit()
        info.BasicLimitInformation.LimitFlags = flags
        return bool(_k32.SetInformationJobObject(
            h, _JobObjectExtendedLimitInformation,
            ctypes.byref(info), ctypes.sizeof(info)))


    class Job:
        """Один Job Object на один запуск сервиса/проекта."""

        def __init__(self):
            self.h = _k32.CreateJobObjectW(None, None)
            if not self.h:
                raise ctypes.WinError()
            try:
                if not _set_limit(self.h, JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE):
                    raise ctypes.WinError()
            except Exception:
                _k32.CloseHandle(self.h)
                self.h = None
                raise

        def assign(self, proc):
            """Назначить Popen в job по его process-handle. False при отказе
            (ERROR_ACCESS_DENIED — дашборд сам в чужом Job без BREAKAWAY)."""
            if not self.h:
                return False
            return bool(_k32.AssignProcessToJobObject(
                self.h, int(proc._handle)))

        def terminate(self, code=1):
            if self.h:
                _k32.TerminateJobObject(self.h, code)

        def disarm(self):
            """Снять KILL_ON_JOB_CLOSE: штатный выход дашборда оставляет
            процессы жить."""
            if self.h:
                _set_limit(self.h, 0)

        def close(self):
            if self.h:
                _k32.CloseHandle(self.h)
                self.h = None


    def popen_in_job(args, *, job=None, **kw):
        """Popen под Job Object без гонки: CREATE_SUSPENDED → assign → resume.
        Возвращает (proc, job|None). Если job не передан — создаётся новый;
        при отказе назначения возвращает None вместо job."""
        kw["creationflags"] = kw.get("creationflags", 0) | CREATE_SUSPENDED
        try:
            proc = subprocess.Popen(args, **kw)
        except Exception:
            if job:  # чужой job — закрыть, чтоб не утёк хендл
                job.disarm()
                job.close()
            raise
        try:
            if job is None:
                job = Job()
            ok = job.assign(proc)
        except Exception:
            ok = False
        try:  # процесс может умереть до resume — не роняем вызов
            psutil.Process(proc.pid).resume()
        except psutil.Error:
            pass
        if not ok:
            if job:
                job.disarm()
                job.close()
            return proc, None
        return proc, job
else:
    import os
    import signal


    class Job:
        """POSIX-аналог: держит pgid лидера группы процессов.

        Тот же контракт, что у Win32-Job: assign/terminate/disarm/close.
        Порождённый с start_new_session процесс — лидер группы (pid==pgid),
        дети наследуют группу → killpg добивает дерево."""

        def __init__(self):
            self.pgid = None

        def assign(self, proc):
            self.pgid = proc.pid
            return True

        def terminate(self, code=1):
            if self.pgid:
                try:
                    os.killpg(self.pgid, signal.SIGKILL)
                except (ProcessLookupError, PermissionError, OSError):
                    pass

        def disarm(self):  # дети POSIX и без того переживают родителя
            pass

        def close(self):
            self.pgid = None


    def popen_in_job(args, *, job=None, **kw):
        """Popen в своей сессии → killpg добивает всё дерево.
        Та же сигнатура (proc, job), что и Windows-версия."""
        kw.pop("creationflags", None)  # аргумент Windows-only, на POSIX игнор,
        kw["start_new_session"] = True  # но убираем явно ради ясности
        proc = subprocess.Popen(args, **kw)
        if job is None:
            job = Job()
        job.assign(proc)
        return proc, job
