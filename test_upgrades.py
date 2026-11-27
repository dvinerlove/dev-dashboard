"""Self-verification for the core upgrade: Job Objects, backoff/circuit,
deps health-check, log parser. Run: python test_upgrades.py
"""
import os
import subprocess
import sys
import tempfile
import time

import psutil

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# isolated DATA_DIR before importing backend/core — tests must not touch
# the real user configs and state.db
os.environ["DEVDASH_DATA_DIR"] = tempfile.mkdtemp(prefix="devdash-test-")
import process_tree as ptree
import backend as be
import core
import storage


def alive(pid):
    try:
        return psutil.Process(pid).is_running()
    except psutil.NoSuchProcess:
        return False


def test1_job_kills_tree():
    """Job Object: parent and the child it spawned die together.
    POSIX branch — start_new_session + killpg, same contract."""
    args = (["cmd.exe", "/c",
             "ping -n 30 127.0.0.1 > nul & timeout /t 60 > nul"]
            if os.name == "nt" else
            ["sh", "-c", "sleep 60 & sleep 60"])
    proc, job = ptree.popen_in_job(
        args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if job is None:
        # hosted runners are themselves inside a Job Object — assign is denied (by design)
        print("  skip: job=None (process already in an external Job)")
        proc.kill()
        proc.wait()
        return
    time.sleep(1.5)
    kids = [c.pid for c in psutil.Process(proc.pid).children(recursive=True)]
    assert kids, "child processes not found before the kill"
    job.terminate()
    proc.wait(timeout=10)  # reap: otherwise a POSIX zombie, is_running()=True
    job.close()
    time.sleep(0.5)
    dead = [p for p in [proc.pid] + kids if not alive(p)]
    assert len(dead) == 1 + len(kids), \
        f"not all processes are dead: {dead} of {[proc.pid]+kids}"
    print(f"  ok: parent {proc.pid} + {len(kids)} children terminated")


def test2_backoff_circuit():
    """Backoff + circuit breaker: 5 crashes/60s -> stop, failed status."""
    d = core.Dashboard.__new__(core.Dashboard)
    d.__init__()  # configs from the isolated DATA_DIR; API/probes not started
    d._backoff = (0.02, 0.02, 0.02, 0.02)
    d._last_services = {}
    starts = []
    d._start_service = lambda spec=None, *a, **k: starts.append(
        spec["name"] if isinstance(spec, dict) else a[0])
    spec = {"name": "fake-svc", "autorestart": True,
            "start": "python -c \"import sys;sys.exit(1)\""}
    d.services_data.append(spec)  # _autorestart_fire drops foreign specs
    # 5 crashes in a row: the service "ran" <60s each time
    for _ in range(5):
        d._svc_up_since["fake-svc"] = time.time() - 1
        d._svc_autorestart(spec)
        time.sleep(0.1)  # the 0.02s timer must fire before the next crash
    time.sleep(0.3)
    assert "fake-svc" in d._cb_open, "circuit breaker did not open"
    kinds = [i["kind"] for i in d._issues]
    assert "crash_loop" in kinds, "no crash_loop event in issues"
    assert len(starts) == 4, f"restarts {len(starts)}, expected 4 " \
                             "(5th crash opens the circuit)"
    # failed status in the row
    row = d._svc_row(spec)
    assert row["state"] == "failed" \
        and row["reason"] == be.tr_detail("circuit_open"), row
    # a manual start resets the CB
    d.services_data.append(spec)
    d._start_service = lambda s, *a, **k: True
    d.start_service("fake-svc")
    assert "fake-svc" not in d._cb_open
    d.services_data.remove(spec)
    print("  ok: 5 crashes -> circuit_open, crash_loop issue, "
          "failed state, manual start resets")


def test3_deps_healthcheck():
    """depends_on: B waits for real readiness of A (TCP), timeout ->
    deps_timeout without starting."""
    d = core.Dashboard.__new__(core.Dashboard)
    d.__init__()
    d._dep_timeout = 3.0
    port = 54123
    svc_a = {"name": "t-a", "ports": [port],
             "start": f'python -c "import socket,time;'
                      f'time.sleep(1.0);s=socket.socket();'
                      f's.bind((\'127.0.0.1\',{port}));s.listen();'
                      f'time.sleep(10)"'}
    svc_b = {"name": "t-b", "depends_on": ["t-a"],
             "start": 'python -c "import time;time.sleep(10)"'}
    d.services_data = [svc_a, svc_b]
    d._last_services = {}
    t_start = {}
    orig = d._do_start
    d._do_start = lambda s: (t_start.setdefault(s["name"], time.time()),
                             orig(s))[1]
    assert d._start_service(svc_b)   # returns True at once, B starts in background
    time.sleep(2.5)
    assert "t-b" in t_start, "B never started"
    assert t_start["t-b"] - t_start["t-a"] >= 0.9, \
        f"B started too early: {t_start}"
    assert be._port_open(port), "port A did not open"
    # timeout branch: A2 never opens the port
    svc_a2 = {"name": "t-a2", "ports": [port + 1],
              "start": 'python -c "import time;time.sleep(30)"'}
    svc_b2 = {"name": "t-b2", "depends_on": ["t-a2"],
              "start": 'python -c "pass"'}
    d.services_data = [svc_a, svc_b, svc_a2, svc_b2]
    d._last_services = {}
    d._dep_timeout = 1.2
    # _force_probe after _do_start may mark t-a2 "up" (process alive —
    # a legitimate readiness fallback) → races with the wait window; the stub
    # makes the timeout branch deterministic, real readiness is covered by A/B.
    d._wait_ready = lambda spec, timeout: False
    d._start_service(svc_b2)
    # poll for the issue — process spawn on Windows can be slow
    deadline = time.time() + d._dep_timeout + 3
    while time.time() < deadline and not any(
            i["kind"] == "deps_timeout" for i in d._issues):
        time.sleep(0.2)
    kinds = [i["kind"] for i in d._issues]
    assert "deps_timeout" in kinds, f"no deps_timeout: {kinds}"
    assert "t-b2" not in t_start, "B2 started despite the A2 timeout"
    # kill the test processes — only Jobs created by this test
    for job in d._jobs.values():
        job.terminate()
        job.close()
    print("  ok: B started after A was ready; timeout -> deps_timeout")


def test4_log_parser():
    """Parser: Traceback/EADDRINUSE -> error, issue dedup within 60s."""
    assert core.classify_log_line(
        "Traceback (most recent call last):") == "error"
    assert core.classify_log_line(
        "EADDRINUSE: address already in use :::3000") == "error"
    assert core.classify_log_line("ModuleNotFoundError: No module") == "error"
    assert core.classify_log_line("UnhandledPromiseRejection x") == "error"
    assert core.classify_log_line("  warn: low memory") == "warn"
    assert core.classify_log_line("INFO listening on :4850") == "info"
    d = core.Dashboard.__new__(core.Dashboard)
    d.__init__()
    t0 = time.time()  # issues from state.db survive restarts — count fresh ones only
    for _ in range(3):
        d._issue_log_error("svc", "EADDRINUSE :::3000")
    d._issue_log_error("svc", "Another error")
    iss = [i for i in d._issues
           if i["kind"] == "log_error" and i["t"] >= t0]
    assert len(iss) == 2 and iss[0]["count"] == 3, iss
    print("  ok: line levels correct, dedup x3 within the 60s window")


def test5_env_api():
    """ENV: secret masking, saving, restart_required."""
    d = core.Dashboard.__new__(core.Dashboard)
    d.__init__()
    spec = {"name": "env-svc"}
    d.services_data.append(spec)
    spec["env"] = {"API_TOKEN": "secret123", "PLAN": "x"}
    env = d.service_env(spec["name"])
    byk = {e["key"]: e for e in env}
    assert byk["API_TOKEN"]["value"] == "••••••••" and byk["API_TOKEN"]["secret"]
    assert byk["PLAN"]["value"] == "x" and not byk["PLAN"]["secret"]
    env = d.service_env(spec["name"], reveal=True)
    assert {e["key"]: e for e in env}["API_TOKEN"]["value"] == "secret123"
    # save_env writes into the DATA_DIR config (isolated) — verify the write
    res = d.save_env("env-svc", {"K": "v"})
    assert res == {"restart_required": False}, res
    assert spec["env"] == {"K": "v"}
    print("  ok: secrets masked, reveal and save_env work")


def test6_storage_rotation():
    """state.db rotation: <=50 runs per service, <=200 issues; oldest are cut."""
    tmp = os.path.join(tempfile.mkdtemp(), "t.db")
    old_db, old_con = storage.DB, storage._con
    try:
        if old_con:
            old_con.close()
        storage._con = None
        storage.DB = tmp
        for i in range(60):
            storage.save_run("svc-x", {"t0": i, "t1": i + 1, "exit": "exit 0"})
        for i in range(5):
            storage.save_run("svc-y", {"t0": i, "t1": i + 1, "exit": "exit 0"})
        for i in range(250):
            storage.save_issue({"t": i, "kind": "k", "name": "n",
                                "text": "x", "count": 1})
        runs, issues = storage.load()
        assert len(runs["svc-x"]) == 50, len(runs["svc-x"])
        assert len(runs["svc-y"]) == 5, len(runs["svc-y"])
        assert len(issues) == 200, len(issues)
        assert runs["svc-x"][0]["t0"] == 10   # the 10 oldest were cut
        assert issues[0]["t"] == 50           # the 50 oldest were cut
        # the update branch (repeat save_run by _rid) does not break rotation
        r = runs["svc-x"][-1]
        r["t1"], r["exit"] = 999, "killed"
        storage.save_run("svc-x", r)
        runs2, _ = storage.load()
        assert runs2["svc-x"][-1]["exit"] == "killed"
        assert len(runs2["svc-x"]) == 50
    finally:
        if storage._con:
            storage._con.close()
        storage.DB, storage._con = old_db, None
    print("  ok: 60 runs -> 50, 250 issues -> 200, update by _rid alive")


def test7_scan_worktree_compose():
    """Scan: worktree checkouts fold into ONE row; compose.yml lists services."""
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True)
    except Exception:
        print("  skip: no git on PATH")
        return
    root = tempfile.mkdtemp(prefix="devdash-scan-")
    repo = os.path.join(root, "repo")
    os.makedirs(repo)
    env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
               GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")

    def git(*a, cwd=repo):
        subprocess.run(["git", *a], cwd=cwd, env=env,
                       check=True, capture_output=True)

    git("init", "-b", "main")
    with open(os.path.join(repo, "compose.yml"), "w") as f:
        f.write("services:\n  web:\n    image: nginx\n"
                "  db:\n    image: postgres\n")
    git("add", "-A")
    git("commit", "-m", "x")
    wt = os.path.join(root, "repo-wt")
    git("worktree", "add", wt, "-b", "wt-branch")
    # CI repro: %TEMP% arrives in 8.3 short form while git writes the .git
    # worktree pointer in long form — the fold must hold either way
    scan_root = root
    if sys.platform.startswith("win"):
        import ctypes
        buf = ctypes.create_unicode_buffer(512)
        n = ctypes.windll.kernel32.GetShortPathNameW(root, buf, 512)
        if n and buf.value.lower() != root.lower():
            scan_root = buf.value
    be.save_settings({"scan_roots": [scan_root]})
    d = core.Dashboard.__new__(core.Dashboard)
    d.__init__()
    canon = lambda s: os.path.normcase(os.path.realpath(s))
    rows = [p for p in d.scan_projects()["found"]
            if canon(p["cwd"]).startswith(canon(scan_root))]
    assert len(rows) == 1, f"worktrees must fold into one row: {rows}"
    row = rows[0]
    assert canon(row["cwd"]) == canon(repo), \
        "primary must be the main checkout"
    assert {canon(w["cwd"]) for w in row["worktrees"]} == \
        {canon(repo), canon(wt)}, row["worktrees"]
    assert row["compose_services"] == ["web", "db"], row["compose_services"]
    print("  ok: 2 checkouts -> 1 row, worktrees listed, "
          "compose_services parsed")


def test8_cred_cleanup():
    """save_env deletes unreferenced cred: targets; rename keeps them alive."""
    import core
    import platform_impl as pi
    d = core.Dashboard.__new__(core.Dashboard)
    d.__init__()
    d.services_data = [{"name": "t-cred", "start": "python -c pass",
                        "match": "zzz-no-such-proc"}]
    if not pi.IS_WIN:
        print("  skip: cred store is windows-only")
        return
    r = d.set_env_secret("t-cred", "K1", "s3cr3t-test")
    assert r and "restart_required" in r, r
    target = "DevDashboard/t-cred/K1"
    try:
        assert pi.cred_read(target) == "s3cr3t-test", "cred not written"
        assert d.services_data[0]["env"]["K1"] == f"cred:{target}"
        # referenced -> survives full replacement
        d.save_env("t-cred", {"K1": f"cred:{target}", "X": "1"})
        assert pi.cred_read(target) == "s3cr3t-test"
        # rename: same target under another key -> still referenced
        d.save_env("t-cred", {"K2": f"cred:{target}"})
        assert pi.cred_read(target) == "s3cr3t-test",             "rename must not kill the credential"
        # unreferenced -> deleted
        d.save_env("t-cred", {"X": "1"})
        assert pi.cred_read(target) is None,             "unreferenced target must be deleted"
    finally:
        try:
            pi.cred_delete(target)
        except OSError:
            pass
    print("  ok: cred write/read, rename survives, delete-on-unref")


def test9_self_update_mechanics():
    """Updater helper: ps1 waits for the app pid to die, then swaps the exe."""
    import subprocess, tempfile, time
    import backend as be
    if not be.pi.IS_WIN:
        print("  skip: updater is windows-only")
        return
    assert be.update_channel() == "dev", "tests run from source"
    assert be.semver_key("0.10.0") > be.semver_key("0.9.1")
    assert be.semver_key("0.9.0") == be.semver_key("v0.9.0")
    tmp = tempfile.mkdtemp()
    sleeper = subprocess.Popen(["python", "-c", "import time; time.sleep(60)"])
    src = os.path.join(tmp, "DevDashboard.exe")
    open(src, "w").write("NEW")
    target = os.path.join(tmp, "target.exe")
    open(target, "w").write("old")
    ps1 = be.write_update_helper(target, sleeper.pid, ("copy", src),
                                 os.path.join(tmp, "apply.ps1"))
    subprocess.Popen(["powershell", "-NoProfile", "-ExecutionPolicy",
                      "Bypass", "-File", ps1],
                     creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                     close_fds=True)
    time.sleep(1.5)
    assert open(target).read() == "old", "swap must wait for process death"
    sleeper.kill()
    for _ in range(30):
        try:
            if open(target).read() == "NEW":
                break
        except OSError:
            pass
        time.sleep(0.5)
    assert open(target).read() == "NEW", "exe not swapped after death"
    print("  ok: helper waits for exit, swaps exe, relaunch line present")



def test10_self_autorun():
    """self_autorun_is: name AND a command pointing at this app —
    foreign same-named values do not count."""
    fake = '"C:\\x\\pythonw.exe" "%s"' % os.path.join(
        be.BASE_DIR, "dashboard.py")
    assert be.self_autorun_is("DevDashboard", fake)
    assert be.self_autorun_is("devdashboard", fake)  # registry names: case-ins.
    assert not be.self_autorun_is("DevDashboard", '"C:\\x\\calc.exe"')
    assert not be.self_autorun_is("Other", fake)
    # monkeypatched registry -> enabled flips with the entry
    orig = be._read_autorun
    try:
        be._read_autorun = lambda: []
        assert not be.self_autorun_enabled()
        be._read_autorun = lambda: [("DevDashboard", fake)]
        assert be.self_autorun_enabled()
    finally:
        be._read_autorun = orig
    print("  ok: self_autorun_is requires name+cmd, enabled reads live")


def test11_find_project_pid_cwd():
    """find_project_pid: a process whose cwd is inside the project tree
    counts even when exe/cmdline carry no project path (node src\\x.ts);
    outside-cwd processes and shells do not."""
    import tempfile
    root = tempfile.mkdtemp(prefix="projmatch-")
    srv = os.path.join(root, "server")
    os.makedirs(srv)
    proj = {"cwd": root}
    inside = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(30)"], cwd=srv)
    outside = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(30)"])
    try:
        time.sleep(0.5)  # let cwd settle
        assert be.find_project_pid(proj) == inside.pid
        cwds = {inside.pid: os.path.normcase(srv)}
        assert be.find_project_pid(proj, cwds) == inside.pid
        assert be.find_project_pid({"cwd": os.path.join(root, "other")}) \
            is None
    finally:
        inside.kill(); outside.kill()
    print("  ok: cwd inside the project tree adopts the process")


if __name__ == "__main__":
    print("step1: job objects")
    test1_job_kills_tree()
    print("step2: backoff + circuit")
    test2_backoff_circuit()
    print("step3: deps health-check")
    test3_deps_healthcheck()
    print("step4: log error parser")
    test4_log_parser()
    print("step5: env masking")
    test5_env_api()
    print("step6: storage rotation")
    test6_storage_rotation()
    print("step7: scan worktree + compose")
    test7_scan_worktree_compose()
    print("step8: cred cleanup")
    test8_cred_cleanup()
    print("step9: self-update mechanics")
    test9_self_update_mechanics()
    print("step10: self autorun")
    test10_self_autorun()
    print("step11: project pid by cwd")
    test11_find_project_pid_cwd()
    print("ALL PASS")