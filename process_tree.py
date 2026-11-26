"""Killing a process tree: Windows Job Objects / POSIX process groups.

Windows — a Job with KILL_ON_JOB_CLOSE: while the dashboard holds the
handle open, TerminateJobObject() kills the whole tree instantly. On an
abrupt dashboard shutdown the handles drop — the trees die too (no
orphans). On clean exit we call disarm() before close(), otherwise the
services die together with the dashboard.

POSIX — start_new_session + killpg(SIGKILL): the spawned process is the
group leader, children inherit the pgid. disarm() is a no-op: on POSIX
children outlive the parent anyway.
shortcut: on POSIX an abrupt dashboard crash does NOT kill the tree —
macOS has no kernel equivalent of KILL_ON_JOB_CLOSE (Linux would have
cgroups). Orphans are picked up on next start via pids_on_port/kill_proc_tree.
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
    CREATE_SUSPENDED = 0x00000004  # winbase.h; subprocess has no constant


    class _BasicLimit(ctypes.Structure):
        # LARGE_INTEGER = int64; SIZE_T/ULONG_PTR are machine-word (ctypes
        # aligns to 8 bytes on x64 and 4 on x86).
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
        """One Job Object per service/project launch."""

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
            """Assign a Popen to the job via its process handle. False on refusal
            (ERROR_ACCESS_DENIED — dashboard itself is in a foreign Job without BREAKAWAY)."""
            if not self.h:
                return False
            return bool(_k32.AssignProcessToJobObject(
                self.h, int(proc._handle)))

        def terminate(self, code=1):
            if self.h:
                _k32.TerminateJobObject(self.h, code)

        def disarm(self):
            """Clear KILL_ON_JOB_CLOSE: a clean dashboard exit leaves
            the processes running."""
            if self.h:
                _set_limit(self.h, 0)

        def close(self):
            if self.h:
                _k32.CloseHandle(self.h)
                self.h = None


    def popen_in_job(args, *, job=None, **kw):
        """Popen under a Job Object without a race: CREATE_SUSPENDED → assign → resume.
        Returns (proc, job|None). If job is not given a new one is created;
        on assignment refusal returns None instead of job."""
        kw["creationflags"] = kw.get("creationflags", 0) | CREATE_SUSPENDED
        try:
            proc = subprocess.Popen(args, **kw)
        except Exception:
            if job:  # foreign job — close it so the handle does not leak
                job.disarm()
                job.close()
            raise
        try:
            if job is None:
                job = Job()
            ok = job.assign(proc)
        except Exception:
            ok = False
        try:  # the process may die before resume — do not crash the call
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
        """POSIX analog: holds the pgid of the process group leader.

        Same contract as the Win32 Job: assign/terminate/disarm/close.
        A process spawned with start_new_session is the group leader (pid==pgid),
        children inherit the group → killpg finishes the tree."""

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

        def disarm(self):  # POSIX children outlive the parent anyway
            pass

        def close(self):
            self.pgid = None


    def popen_in_job(args, *, job=None, **kw):
        """Popen in its own session → killpg finishes the whole tree.
        Same (proc, job) signature as the Windows version."""
        kw.pop("creationflags", None)  # Windows-only arg, ignored on POSIX
        kw["start_new_session"] = True  # but remove it explicitly for clarity
        proc = subprocess.Popen(args, **kw)
        if job is None:
            job = Job()
        job.assign(proc)
        return proc, job
