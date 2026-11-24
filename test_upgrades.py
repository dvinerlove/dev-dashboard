"""Self-verification для апгрейда ядра: Job Objects, backoff/circuit,
deps health-check, log parser. Запуск: python test_upgrades.py
"""
import os
import subprocess
import sys
import tempfile
import time

import psutil

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# изолированная DATA_DIR до импорта backend/core — тесты не трогают
# реальные конфиги и state.db пользователя
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
    """Job Object: родитель + порождённый им ребёнок умирают вместе.
    POSIX-ветка — start_new_session + killpg, тот же контракт."""
    args = (["cmd.exe", "/c",
             "ping -n 30 127.0.0.1 > nul & timeout /t 60 > nul"]
            if os.name == "nt" else
            ["sh", "-c", "sleep 60 & sleep 60"])
    proc, job = ptree.popen_in_job(
        args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if job is None:
        # hosted-раннеры сами внутри Job Object — assign запрещён (by design)
        print("  skip: job=None (процесс уже во внешнем Job)")
        proc.kill()
        proc.wait()
        return
    time.sleep(1.5)
    kids = [c.pid for c in psutil.Process(proc.pid).children(recursive=True)]
    assert kids, "дочерние процессы не найдены до убийства"
    job.terminate()
    job.close()
    time.sleep(0.5)
    dead = [p for p in [proc.pid] + kids if not alive(p)]
    assert len(dead) == 1 + len(kids), \
        f"не все процессы мертвы: {dead} из {[proc.pid]+kids}"
    print(f"  ok: parent {proc.pid} + {len(kids)} children terminated")


def test2_backoff_circuit():
    """Backoff + circuit breaker: 5 падений/60с -> stop, статус failed."""
    d = core.Dashboard.__new__(core.Dashboard)
    d.__init__()  # конфиги из изолированной DATA_DIR; API/пробы не стартуют
    d._backoff = (0.02, 0.02, 0.02, 0.02)
    d._last_services = {}
    starts = []
    d._start_service = lambda spec=None, *a, **k: starts.append(
        spec["name"] if isinstance(spec, dict) else a[0])
    spec = {"name": "fake-svc", "autorestart": True,
            "start": "python -c \"import sys;sys.exit(1)\""}
    d.services_data.append(spec)  # _autorestart_fire отбрасывает чужие spec
    # 5 падений подряд: сервис «работал» <60с каждый раз
    for _ in range(5):
        d._svc_up_since["fake-svc"] = time.time() - 1
        d._svc_autorestart(spec)
        time.sleep(0.1)  # таймер 0.02с должен успеть до след. падения
    time.sleep(0.3)
    assert "fake-svc" in d._cb_open, "circuit breaker не открылся"
    kinds = [i["kind"] for i in d._issues]
    assert "crash_loop" in kinds, "нет события crash_loop в issues"
    assert len(starts) == 4, f"рестартов {len(starts)}, ожидалось 4 " \
                             "(5-е падение открывает circuit)"
    # failed-статус в row
    row = d._svc_row(spec)
    assert row["state"] == "failed" \
        and row["reason"] == be.tr_detail("circuit_open"), row
    # ручной старт сбрасывает CB
    d.services_data.append(spec)
    d._start_service = lambda s, *a, **k: True
    d.start_service("fake-svc")
    assert "fake-svc" not in d._cb_open
    d.services_data.remove(spec)
    print("  ok: 5 падений -> circuit_open, crash_loop issue, "
          "failed state, ручной старт сбрасывает")


def test3_deps_healthcheck():
    """depends_on: B ждёт реальной готовности A (TCP), таймаут ->
    deps_timeout без старта."""
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
    assert d._start_service(svc_b)   # сразу вернёт True, B — в фоне
    time.sleep(2.5)
    assert "t-b" in t_start, "B так и не стартовал"
    assert t_start["t-b"] - t_start["t-a"] >= 0.9, \
        f"B стартовал слишком рано: {t_start}"
    assert be._port_open(port), "порт A не открыт"
    # timeout-ветка: A2 не открывает порт
    svc_a2 = {"name": "t-a2", "ports": [port + 1],
              "start": 'python -c "import time;time.sleep(30)"'}
    svc_b2 = {"name": "t-b2", "depends_on": ["t-a2"],
              "start": 'python -c "pass"'}
    d.services_data = [svc_a, svc_b, svc_a2, svc_b2]
    d._last_services = {}
    d._dep_timeout = 1.2
    # _force_probe после _do_start может пометить t-a2 "up" (процесс жив —
    # легальный fallback готовности) → гонка с окном ожидания; стаб дела
    # timeout-ветку детерминированной, реальную готовность проверяет ветка A/B.
    d._wait_ready = lambda spec, timeout: False
    d._start_service(svc_b2)
    # ждём issue поллингом — спавн процесса на Windows может быть медленным
    deadline = time.time() + d._dep_timeout + 3
    while time.time() < deadline and not any(
            i["kind"] == "deps_timeout" for i in d._issues):
        time.sleep(0.2)
    kinds = [i["kind"] for i in d._issues]
    assert "deps_timeout" in kinds, f"нет deps_timeout: {kinds}"
    assert "t-b2" not in t_start, "B2 стартовал несмотря на таймаут A2"
    # добить тестовые процессы — только Job'ы, созданные этим тестом
    for job in d._jobs.values():
        job.terminate()
        job.close()
    print("  ok: B стартовал после готовности A; timeout -> deps_timeout")


def test4_log_parser():
    """Парсер: Traceback/EADDRINUSE -> error, дедуп issue в окне 60с."""
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
    t0 = time.time()  # issues из state.db переживают запуск — считаем только свежие
    for _ in range(3):
        d._issue_log_error("svc", "EADDRINUSE :::3000")
    d._issue_log_error("svc", "Другая ошибка")
    iss = [i for i in d._issues
           if i["kind"] == "log_error" and i["t"] >= t0]
    assert len(iss) == 2 and iss[0]["count"] == 3, iss
    print("  ok: уровни строк верные, дедуп x3 за окно 60с")


def test5_env_api():
    """ENV: маскирование секретов, сохранение, restart_required."""
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
    # save_env пишет в конфиг DATA_DIR (изолирован) — проверяем запись
    res = d.save_env("env-svc", {"K": "v"})
    assert res == {"restart_required": False}, res
    assert spec["env"] == {"K": "v"}
    print("  ok: секреты маскируются, reveal и save_env работают")


def test6_storage_rotation():
    """Ротация state.db: <=50 runs на сервис, <=200 issues; старые режутся."""
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
        assert runs["svc-x"][0]["t0"] == 10   # 10 самых старых срезаны
        assert issues[0]["t"] == 50           # 50 самых старых срезаны
        # update-ветка (повторный save_run по _rid) не ломает ротацию
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
    print("  ok: 60 runs -> 50, 250 issues -> 200, update по _rid жив")


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
    print("ALL PASS")
